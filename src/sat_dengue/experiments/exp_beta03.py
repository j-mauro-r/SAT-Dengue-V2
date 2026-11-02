"""Frozen-score policy comparison; selection never consumes evaluation outcomes."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.experiments.exp_beta01 import KEYS, metric_row, thresholds
from sat_dengue.experiments.exp_beta01 import prepare as canonical_cohorts
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table


def _frame(part: pd.DataFrame) -> pd.DataFrame:
    frame = (
        part[[*KEYS, "target_month", "onset_target", "score"]]
        .rename(columns={"onset_target": "truth"})
        .copy()
    )
    frame.attrs = {}
    frame["department_code"] = frame.municipality_code.astype(str).str[:2]
    return frame.sort_values(KEYS).reset_index(drop=True)


def _validate_frame(frame: pd.DataFrame, role: str) -> None:
    if (
        frame.empty
        or frame.duplicated(KEYS).any()
        or frame[[*KEYS, "target_month", "truth", "score"]].isna().any().any()
        or not frame.truth.isin([0, 1]).all()
        or not np.isfinite(frame.score.astype(float)).all()
        or not frame.score.between(0, 1).all()
        or not frame.target_month.lt("2025-01").all()
        or not frame.department_code.isin(["50", "73"]).all()
    ):
        raise ValueError(f"Invalid frozen {role} scores/cohort")


def prepare(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    if validate_parameters(parameters) != {"profile": "exp_beta03", "tracking": "disabled"}:
        raise ValueError("Beta03 requires its own profile and disabled tracking")
    protocol, cells = sources["protocol"], sources["cells"]
    expected = {(h, y) for h in protocol["horizons"] for y in protocol["evaluation_years"]}
    if len(cells) != len(expected) or {(c["horizon"], c["year"]) for c in cells} != expected:
        raise ValueError("Incomplete R0 horizon/year membership")
    canonical = canonical_cohorts(
        {**sources, "protocol": sources["canonical_protocol"]},
        {"profile": "exp_beta01", "tracking": "disabled"},
    )["cohorts"]
    reference = sources["reference"]
    if reference is None:
        raise ValueError("Mandatory paired R0 predictions missing")
    for cell in cells:
        previous, audit = None, {}
        for role in ("train", "calibration", "selection", "evaluation"):
            part = cell["parts"][role]
            start, end = cell["window"][role]
            if (
                part.empty
                or not part.target_month.between(start, end).all()
                or (previous is not None and not part.year_month.ge(previous).all())
                or (role != "evaluation" and not part.target_month.lt("2024-01").all())
            ):
                raise ValueError("Frozen temporal role/embargo violation")
            audit[role] = {
                "rows": len(part),
                "target_start": start,
                "target_end": end,
                "origin_start": str(part.year_month.min()),
                "origin_end": str(part.year_month.max()),
                "keys_sha256": bytes_record(serialize_table(part[KEYS]))["sha256"],
            }
            previous = end
        selection, evaluation = (_frame(cell["parts"][r]) for r in ("selection", "evaluation"))
        for role, frame in (("selection", selection), ("evaluation", evaluation)):
            _validate_frame(frame, role)
            # Independent canonical labels, exact calendar, no intersection rescue.
            expected_role = canonical[cell["horizon"]]
            start, end = cell["window"][role]
            boundary = cell["window"]["calibration" if role == "selection" else "selection"][1]
            expected_role = expected_role.loc[
                expected_role.target_month.between(start, end)
                & expected_role.year_month.ge(boundary)
            ].sort_values(KEYS)
            cols = [*KEYS, "target_month", "truth"]
            expected_role = expected_role.rename(columns={"onset_target": "truth"})
            if (
                frame[cols].to_records(index=False).tolist()
                != expected_role[cols].to_records(index=False).tolist()
            ):
                raise ValueError(f"Canonical {role} pairing mismatch")
        if selection.truth.nunique() != 2:
            raise ValueError("R0 selection lacks two-class development support")
        old = (
            reference.loc[
                reference.horizon.eq(cell["horizon"])
                & reference.target_month.str[:4].eq(str(cell["year"]))
            ]
            .rename(columns={"origin_month": "year_month"})
            .sort_values(KEYS)
        )
        cols = [*KEYS, "target_month", "truth", "score"]
        if (
            evaluation[cols].to_records(index=False).tolist()
            != old[cols].to_records(index=False).tolist()
        ):
            raise ValueError("Exact frozen R0 pairing mismatch")
        evaluation["reference_alert"] = old.alert.astype(bool).to_numpy()
        if not np.array_equal(
            evaluation.reference_alert,
            alerts(evaluation.score, cell["reference_threshold"]),
        ):
            raise ValueError("Frozen reference alerts changed")
        cell.update(selection=selection, evaluation=evaluation, role_audit=audit)
        # Downstream selection cannot access native feature/training payloads.
        del cell["parts"]
    return {**sources, "provenance": {**sources["provenance"], "operational": parameters}}


def alerts(score: pd.Series, threshold: float | None) -> np.ndarray:
    return np.zeros(len(score), dtype=bool) if threshold is None else score.ge(threshold).to_numpy()


def select_policy(selection: pd.DataFrame, protocol: dict[str, Any]) -> dict[str, Any]:
    """Pure development interface: no evaluation argument or global search state."""
    _validate_frame(selection, "selection")
    p = protocol["policy"]
    budget = p["budget_false_alerts_per_municipality_year"]
    global_policy = thresholds(selection.truth, selection.score, len(selection) / 12, budget)
    selected = selection.assign(alert=alerts(selection.score, global_policy["threshold"]))
    rule, department, rates = p["department"], {}, []
    supported = True
    for code in ("50", "73"):
        group = selected.loc[selected.department_code.eq(code)]
        positive, negative = int(group.truth.sum()), int(group.truth.eq(0).sum())
        support = (
            len(group) >= rule["minimum_rows"]
            and min(positive, negative) >= rule["minimum_per_class"]
        )
        supported &= support
        rate = (
            float((group.alert & group.truth.eq(0)).sum() / (len(group) / 12))
            if len(group)
            else None
        )
        if rate is not None:
            rates.append(rate)
        department[code] = {
            "rows": len(group),
            "onsets": positive,
            "supported": support,
            "global_false_alert_rate": rate,
            "threshold": global_policy["threshold"],
            "fallback": True,
        }
    execute = supported and max(rates) - min(rates) >= rule["minimum_false_alert_rate_gap"]
    if execute:
        for code, local in department.items():
            group = selection.loc[selection.department_code.eq(code)]
            estimate = thresholds(group.truth, group.score, len(group) / 12, budget)
            local_t, global_t = estimate["threshold"], global_policy["threshold"]
            weight = len(group) / (len(group) + rule["pseudo_rows"])
            # Null is stricter than every numeric probability (no alerts).
            threshold = (
                None
                if local_t is None or global_t is None
                else max(local_t, weight * local_t + (1 - weight) * global_t)
            )
            local.update(threshold=threshold, fallback=False, weight=weight, constrained=estimate)
    hard = selection.loc[
        selection.truth.eq(0) & selection.score.ge(p["fp_aware"]["high_confidence_score"])
    ]
    repeated = hard.groupby("municipality_code").size()
    return {
        "global": global_policy,
        "department_status": "EVALUATE" if execute else "NO_EVALUABLE",
        "department_reason": "supported development rate heterogeneity"
        if execute
        else "insufficient department support or development rate heterogeneity",
        "departments": department,
        "fp_aware": {
            "status": "CONDICIONAL_NO_JUSTIFICADO",
            "hard_false_positives": len(hard),
            "municipalities": int(hard.municipality_code.nunique()),
            "municipalities_with_repeated_errors": int(repeated.ge(2).sum()),
            "independent_oof_selection_blocks_per_predictor": 1,
            "reason": (
                "one six-month selection block; no independent recurrence plus untouched "
                "policy block; calibration fitted its scores; evaluation excluded"
            ),
        },
    }


def select(prepared: dict[str, Any]) -> dict[str, Any]:
    for cell in prepared["cells"]:
        cell["policies"] = select_policy(cell["selection"], prepared["protocol"])
    return prepared


def apply(selected: dict[str, Any]) -> dict[str, Any]:
    outputs = []
    for cell in selected["cells"]:
        frame, policy = cell["evaluation"], cell["policies"]
        arms = {
            "R0": frame.reference_alert.to_numpy(),
            "GLOBAL": alerts(frame.score, policy["global"]["threshold"]),
        }
        if policy["department_status"] == "EVALUATE":
            territorial = np.zeros(len(frame), dtype=bool)
            for code, local in policy["departments"].items():
                mask = frame.department_code.eq(code)
                territorial[mask] = alerts(frame.loc[mask, "score"], local["threshold"])
            arms["DEPARTMENT"] = territorial
        for name, emitted in arms.items():
            outputs.append(
                frame.drop(columns="reference_alert").assign(
                    arm=name, alert=emitted, horizon=cell["horizon"], year=cell["year"]
                )
            )
    return {**selected, "predictions": pd.concat(outputs, ignore_index=True)}


def evaluate(applied: dict[str, Any]) -> dict[str, Any]:
    protocol, predictions = applied["protocol"], applied["predictions"]
    budget = protocol["policy"]["budget_false_alerts_per_municipality_year"]
    margin = protocol["policy"]["noninferiority_margin"]
    rows, pooled = [], []
    for (arm, horizon, year), group in predictions.groupby(["arm", "horizon", "year"], sort=True):
        for department in ("all", "50", "73"):
            part = group if department == "all" else group.loc[group.department_code.eq(department)]
            if not part.empty:
                rows.append(
                    {
                        "arm": arm,
                        "horizon": int(horizon),
                        "year": int(year),
                        "department": department,
                        **metric_row(part, budget),
                    }
                )
    for (arm, horizon), group in predictions.groupby(["arm", "horizon"], sort=True):
        pooled.append({"arm": arm, "horizon": int(horizon), **metric_row(group, budget)})
    references = {(r["horizon"], r["year"], r["department"]): r for r in rows if r["arm"] == "R0"}
    comparisons = []
    for row in rows:
        if row["arm"] == "R0":
            continue
        old = references[(row["horizon"], row["year"], row["department"])]
        delta = (
            None
            if row["sensitivity"] is None or old["sensitivity"] is None
            else row["sensitivity"] - old["sensitivity"]
        )
        comparisons.append(
            {
                **{k: row[k] for k in ("arm", "horizon", "year", "department")},
                "sensitivity_difference": delta,
                "false_alert_difference": row["false_alerts"] - old["false_alerts"],
                "budget_met": row["budget_met"],
                "joint_descriptive_compliance": None
                if delta is None
                else row["budget_met"] and delta >= margin,
            }
        )
    ledger = [
        {
            **{
                k: c[k]
                for k in (
                    "cell_id",
                    "horizon",
                    "year",
                    "role_audit",
                    "reference_threshold",
                    "reference_selection",
                )
            },
            "policies": c["policies"],
        }
        for c in applied["cells"]
    ]
    payloads = {
        "predictions.csv": serialize_table(
            predictions.sort_values(["arm", "horizon", "year", *KEYS])
        ),
        "metrics.csv": serialize_table(pd.DataFrame(rows)),
        "comparisons_r0.json": canonical_bytes({"comparisons": comparisons}),
        "pooled.json": canonical_bytes(
            {
                "metrics": pooled,
                "warning": (
                    "department arm covers only development-supported cuts; "
                    "do not compare unmatched pooled totals"
                ),
            }
        ),
        "policies.json": canonical_bytes({"cells": ledger}),
        "protocol.json": canonical_bytes(protocol),
        "provenance.json": canonical_bytes(applied["provenance"]),
        "conclusions.json": canonical_bytes(
            {
                "G5": "NOT_APPROVED",
                "champion": "not_selected",
                "statistical_noninferiority": "UNAVAILABLE",
                "superiority": "NOT_ESTABLISHED",
                "fp_aware": "CONDICIONAL_NO_JUSTIFICADO",
                "confirmation": protocol["confirmation"],
                "real_model_fits": 0,
            }
        ),
    }
    body = {
        "schema": "exp-beta03-publication-v1",
        "experiment_id": "EXP-BETA03",
        "evidence_type": applied["evidence_type"],
        "real_model_fits": 0,
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": applied["provenance"]["sources"],
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": hashlib.sha256(canonical_bytes(body)).hexdigest()}
    )
    return {"payloads": payloads, "provenance": applied["provenance"]}
