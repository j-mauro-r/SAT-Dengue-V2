"""Two frozen-score alert policies; the sole intervention is P1 threshold selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.datasets.canonical import verify_records
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle, verify_bundle
from sat_dengue.experiments.exp_beta01 import KEYS, metric_row
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table


def counts(frame: pd.DataFrame, alert_column: str = "alert") -> dict[str, Any]:
    """Separate excess false alerts from onset false alerts; preserve zero denominators."""
    truth, excess, alert = (
        frame.truth.eq(1),
        frame.target_excess.eq(1),
        frame[alert_column].astype(bool),
    )
    n, onsets, alerts = len(frame), int(truth.sum()), int(alert.sum())
    tp = int((alert & truth).sum())
    false_excess, false_onset = int((alert & ~excess).sum()), int((alert & ~truth).sum())
    return {
        "rows": n,
        "onsets": onsets,
        "detected": tp,
        "missed": onsets - tp,
        "sensitivity": tp / onsets if onsets else None,
        "alerts": alerts,
        "false_alerts_excess": false_excess,
        "far_excess": false_excess / alerts if alerts else None,
        "false_alerts_onset": false_onset,
        "precision_onset": tp / alerts if alerts else None,
        "false_alerts_per_eligible_municipality_year": false_onset / (n / 12),
        "exposure_municipality_years": n / 12,
        "target_excesses": int(excess.sum()),
        "continuation_alerts": false_onset - false_excess,
    }


def within_margin(false: int, alerts: int, channel_false: int, channel_alerts: int) -> bool:
    return (
        alerts > 0
        and channel_alerts > 0
        and (20 * (false * channel_alerts - channel_false * alerts) <= alerts * channel_alerts)
    )


def choose(frame: pd.DataFrame) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Enumerate whole ties; maximize onset TP subject to development excess FAR + 5 pp."""
    channel = counts(frame, "channel_alert")
    support = (
        frame.truth.nunique() == 2
        and frame.target_excess.nunique() == 2
        and channel["far_excess"] is not None
    )
    # No-alert is audited but never feasible: its FAR is undefined.
    frontier: list[dict[str, Any]] = [
        {
            "threshold": None,
            "detected": 0,
            "false_alerts_excess": 0,
            "alerts": 0,
            "far_excess": None,
            "feasible": False,
        }
    ]
    ordered = frame.sort_values("score", ascending=False, kind="stable")
    scores = ordered.score.to_numpy()
    ends = np.r_[np.flatnonzero(scores[:-1] != scores[1:]), len(scores) - 1]
    tp = np.cumsum(ordered.truth.to_numpy(dtype=int))
    fp = np.cumsum(1 - ordered.target_excess.to_numpy(dtype=int))
    for i in ends:
        alerts, false, detected = int(i + 1), int(fp[i]), int(tp[i])
        frontier.append(
            {
                "threshold": float(scores[i]),
                "detected": detected,
                "false_alerts_excess": false,
                "alerts": alerts,
                "far_excess": false / alerts,
                "feasible": bool(
                    support
                    and detected > 0
                    and within_margin(
                        false, alerts, channel["false_alerts_excess"], channel["alerts"]
                    )
                ),
            }
        )
    feasible = [r for r in frontier if r["feasible"]]
    best = (
        max(
            feasible,
            key=lambda r: (r["detected"], -r["false_alerts_excess"], -r["alerts"], r["threshold"]),
        )
        if feasible
        else None
    )
    policy = {
        "status": "EVALUABLE" if best else "NO_EVALUABLE",
        "reason": None
        if best
        else "insufficient_support"
        if not support
        else "no_feasible_threshold",
        "threshold": best["threshold"] if best else None,
        "development_CHANNEL": channel,
        "development_P1": best,
        "support": {
            "rows": len(frame),
            "onsets": int(frame.truth.sum()),
            "target_excesses": int(frame.target_excess.sum()),
        },
        "selection_rows_sha256": bytes_record(
            serialize_table(
                frame[[*KEYS, "target_month", "truth", "target_excess", "score", "channel_alert"]]
            )
        )["sha256"],
    }
    return policy, frontier


def prepare(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    if validate_parameters(parameters) != {"profile": "exp_delta01", "tracking": "disabled"}:
        raise ValueError("DELTA requires its own disabled-tracking profile")
    protocol, cells = sources["protocol"], sources["cells"]
    expected = {
        (h, y)
        for h in protocol["cohort"]["horizons"]
        for y in protocol["cohort"]["evaluation_target_years"]
    }
    if len(cells) != len(expected) or {(c["horizon"], c["year"]) for c in cells} != expected:
        raise ValueError("Incomplete DELTA cells")
    for c in cells:
        select, evaluate = c["selection"], c["evaluation"]
        for f in (select, evaluate):
            if (
                f.empty
                or f.duplicated(KEYS).any()
                or f[[*KEYS, "target_month", "truth", "target_excess", "score"]].isna().any().any()
                or not f.truth.isin([0, 1]).all()
                or not f.target_excess.isin([0, 1]).all()
                or not np.isfinite(f.score).all()
                or not f.score.between(0, 1).all()
                or not f.department_code.isin(["50", "73"]).all()
            ):
                raise ValueError("Invalid DELTA keys/labels/probabilities")
        if (
            not select.target_month.str[:4].eq(str(c["year"] - 1)).all()
            or not evaluate.target_month.str[:4].eq(str(c["year"])).all()
            # Original BETA embargo allows equality: labels through the origin month.
            or select.target_month.max() > evaluate.year_month.min()
        ):
            raise ValueError("Selection/evaluation chronological leakage")
    for h in protocol["cohort"]["horizons"]:
        frames = [c["evaluation"] for c in cells if c["horizon"] == h]
        expected_counts = protocol["cohort"]["expected"][str(h)]
        if (
            sum(len(f) for f in frames) != expected_counts["rows"]
            or sum(int(f.truth.sum()) for f in frames) != expected_counts["onsets"]
        ):
            raise ValueError("Full primary evaluation cohort changed")
    return sources


def select(prepared: dict[str, Any]) -> dict[str, Any]:
    """Persist development choices before applying any evaluation policy."""
    policies: list[dict[str, Any]] = []
    frontier: list[dict[str, Any]] = []
    for cell in sorted(prepared["cells"], key=lambda c: (c["horizon"], c["year"])):
        policy, candidates = choose(cell["selection"])
        label = {"horizon": cell["horizon"], "year": cell["year"]}
        policies.append(
            {
                **label,
                **policy,
                "model_identity": cell["model_identity"],
                "calibrator_sha256": cell["calibrator_sha256"],
            }
        )
        frontier.extend({**label, **r} for r in candidates)
    payloads = {
        "policies.json": canonical_bytes({"policies": policies}),
        "frontier.csv": serialize_table(pd.DataFrame(frontier)),
    }
    body = {
        "schema": "exp-delta01-selection-freeze-v1",
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": prepared["provenance"]["sources"],
        "code": prepared["provenance"]["execution"]["code"],
    }
    bundle_id = bytes_record(canonical_bytes(body))["sha256"]
    payloads["manifest.json"] = canonical_bytes({**body, "bundle_id": bundle_id})
    verify_records(prepared["provenance"]["sources"])
    verify_records(prepared["provenance"]["execution"]["code"])
    path = publish_bundle(Path(prepared["freeze_root"]), bundle_id, payloads)
    verify_bundle(path, payloads)
    return {
        **prepared,
        "freeze": {
            "path": str(path),
            "payloads": payloads,
            "manifest_sha256": bytes_record(payloads["manifest.json"])["sha256"],
        },
    }


def apply(selected: dict[str, Any]) -> dict[str, Any]:
    """Copy P0 probabilities/alerts and apply only the already frozen P1 threshold."""
    freeze = selected["freeze"]
    verify_bundle(Path(freeze["path"]), freeze["payloads"])
    policies = json.loads(freeze["payloads"]["policies.json"])["policies"]
    frames: list[pd.DataFrame] = []
    for cell in selected["cells"]:
        policy = next(
            p for p in policies if (p["horizon"], p["year"]) == (cell["horizon"], cell["year"])
        )
        evaluation = cell["evaluation"].copy()
        evaluation["horizon"], evaluation["year"] = cell["horizon"], cell["year"]
        p0 = evaluation.assign(arm="P0", available=True)
        p1 = evaluation.assign(
            arm="P1", available=policy["status"] == "EVALUABLE", threshold=policy["threshold"]
        )
        p1["alert"] = (
            pd.Series(pd.NA, index=p1.index, dtype="boolean")
            if policy["status"] != "EVALUABLE"
            else p1.score.ge(policy["threshold"])
        )
        if p0.score.tolist() != p1.score.tolist() or p0.truth.tolist() != p1.truth.tolist():
            raise ValueError("P0/P1 probability/label mismatch")
        frames.extend((p0, p1))
    return {**selected, "details": pd.concat(frames, ignore_index=True)}


def evaluate(applied: dict[str, Any]) -> dict[str, Any]:
    """Full primary cohorts, pooled/annual x territorial strata, and paired changes."""
    details, metric_rows, paired = applied["details"], [], []
    policies = json.loads(applied["freeze"]["payloads"]["policies.json"])["policies"]
    for h, horizon in details.groupby("horizon", sort=True):
        for year in ["all", *sorted(horizon.year.unique())]:
            for dept in ("all", "50", "73"):
                mask = pd.Series(True, index=horizon.index)
                if year != "all":
                    mask &= horizon.year.eq(year)
                if dept != "all":
                    mask &= horizon.department_code.eq(dept)
                group = horizon.loc[mask]
                p0, p1 = (group.loc[group.arm.eq(arm)].sort_values(KEYS) for arm in ("P0", "P1"))
                if p0.empty or len(p0) != len(p1):
                    raise ValueError("Missing required full stratum")
                label = {"horizon": int(h), "year": str(year), "department": dept}
                channel, persistence = counts(p0, "channel_alert"), counts(p0, "persistence_alert")
                probability = metric_row(p0, 1.0)  # Exactly once per shared cohort.
                common = {
                    "average_precision": probability["average_precision"],
                    "brier": probability["brier"],
                }
                complete = all(
                    p["status"] == "EVALUABLE"
                    for p in policies
                    if p["horizon"] == h and (year == "all" or p["year"] == year)
                )
                for arm, frame in (("P0", p0), ("P1", p1)):
                    available = arm == "P0" or complete
                    m: dict[str, Any] = (
                        counts(frame) if available else {k: None for k in counts(p0)}
                    )
                    if not available:
                        m.update(rows=len(p0), onsets=int(p0.truth.sum()))
                    a = m["detected"] > channel["detected"] if available else None
                    b = m["detected"] > persistence["detected"] if available else None
                    c = (
                        within_margin(
                            m["false_alerts_excess"],
                            m["alerts"],
                            channel["false_alerts_excess"],
                            channel["alerts"],
                        )
                        if available
                        and m["far_excess"] is not None
                        and channel["far_excess"] is not None
                        else None
                    )
                    metric_rows.append(
                        {
                            **label,
                            "arm": arm,
                            **m,
                            **common,
                            "channel_detected": channel["detected"],
                            "persistence_detected": persistence["detected"],
                            "channel_far_excess": channel["far_excess"],
                            "far_difference_CHANNEL": m["far_excess"] - channel["far_excess"]
                            if available
                            and m["far_excess"] is not None
                            and channel["far_excess"] is not None
                            else None,
                            "condition_A": a,
                            "condition_B": b,
                            "condition_C": c,
                            "academic_status": "NO_EVALUABLE"
                            if not available or c is None
                            else "MEETS"
                            if a and b and c
                            else "DOES_NOT_MEET",
                        }
                    )
                diff: dict[str, Any] = {
                    **label,
                    "status": "EVALUABLE" if complete else "NO_EVALUABLE",
                }
                if complete:
                    a0, a1 = p0.alert.to_numpy(dtype=bool), p1.alert.to_numpy(dtype=bool)
                    y, excess = p0.truth.to_numpy(dtype=int), p0.target_excess.to_numpy(dtype=int)
                    for name, mask in (
                        ("onset_detections", y == 1),
                        ("false_excess_alerts", excess == 0),
                        ("false_onset_alerts", y == 0),
                        ("alerts", np.ones(len(y), dtype=bool)),
                    ):
                        gains, losses = int((~a0 & a1 & mask).sum()), int((a0 & ~a1 & mask).sum())
                        diff.update(
                            {
                                f"gained_{name}": gains,
                                f"lost_{name}": losses,
                                f"difference_{name}": gains - losses,
                            }
                        )
                paired.append(diff)
    metrics = pd.DataFrame(metric_rows)
    transport = []
    for p in policies:
        row = metrics.loc[
            metrics.horizon.eq(p["horizon"])
            & metrics.year.eq(str(p["year"]))
            & metrics.department.eq("all")
            & metrics.arm.eq("P1")
        ].iloc[0]
        transport.append(
            {
                "horizon": p["horizon"],
                "year": p["year"],
                "status": p["status"],
                "threshold": p["threshold"],
                "development_channel_far": p["development_CHANNEL"]["far_excess"],
                "development_P1_far": p["development_P1"]["far_excess"]
                if p["development_P1"]
                else None,
                "evaluation_P1_far": row.far_excess,
                "evaluation_channel_far": row.channel_far_excess,
                "evaluation_condition_C": row.condition_C,
            }
        )
    primary = metrics.loc[
        metrics.year.eq("all") & metrics.department.eq("all") & metrics.arm.eq("P1")
    ]
    disposition = (
        "NO_EVALUABLE"
        if primary.academic_status.eq("NO_EVALUABLE").any()
        else (
            "RESPALDADA_DESCRIPTIVAMENTE"
            if primary.academic_status.eq("MEETS").all()
            else "NO_RESPALDADA"
        )
    )
    conclusions = {
        "hypothesis": disposition,
        "primary": primary.astype(object).where(pd.notna(primary), None).to_dict("records"),
        "interpretation": "Retrospective descriptive comparison; no independent confirmation.",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads = {
        "predictions.csv": serialize_table(details.sort_values(["horizon", "year", "arm", *KEYS])),
        "metrics.csv": serialize_table(metrics),
        "paired_changes.csv": serialize_table(pd.DataFrame(paired)),
        "transport.csv": serialize_table(pd.DataFrame(transport)),
        "policies.json": applied["freeze"]["payloads"]["policies.json"],
        "selection_frontier.csv": applied["freeze"]["payloads"]["frontier.csv"],
        "protocol.json": canonical_bytes(applied["protocol"]),
        "conclusions.json": canonical_bytes(conclusions),
        "provenance.json": canonical_bytes(applied["provenance"]),
    }
    body = {
        "schema": "exp-delta01-publication-v1",
        "evidence_type": applied["evidence_type"],
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": applied["provenance"]["sources"],
        "selection_freeze": {
            "path": applied["freeze"]["path"],
            "manifest_sha256": applied["freeze"]["manifest_sha256"],
        },
        "model_fits": 0,
        "calibrations": 0,
        "inference_calls": 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    )
    verify_records(applied["provenance"]["sources"])
    return {"payloads": payloads, "provenance": applied["provenance"]}
