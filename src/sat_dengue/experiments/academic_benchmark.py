"""Read-only academic evaluation of frozen BETA predictions; no model execution.

Run from the repository root with --preflight, --publish, or --verify BUNDLE_ID.
Only --publish creates an immutable private bundle. Public exports are aggregates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.data.consolidation import history_periods_for_target, percentile_type7
from sat_dengue.datasets.canonical import CanonicalBundleDataset, verify_records
from sat_dengue.datasets.exp_beta01 import BetaSourcesDataset
from sat_dengue.datasets.exp_beta01_v2 import _bundle
from sat_dengue.datasets.legacy_preparation.persistence import verify_bundle
from sat_dengue.datasets.stage2 import identity, local_path
from sat_dengue.experiments.exp_beta01 import metric_row, prepare, role_parts
from sat_dengue.experiments.exp_beta01_v2 import require_pair
from sat_dengue.experiments.onset import KEYS, labels, validate_keys
from sat_dengue.model_training.references import persistence_reference
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

PROTOCOL = "docs/product/experiments/benchmark/protocol.json"
PROTOCOL_SHA = "6eb69f14ab19c04d844fe0aaac1c298c6f77c8f718ce965329632b2510453e05"
OUTPUT = "data/processed/benchmark"
ARMS = ["CHANNEL", "PERSISTENCE", "R0", "G0_OFF", "G0_ON", "G1_OFF"]
MODELS = ARMS[2:]
STRATA = ["horizon", "year", "department"]


def read_predictions(path: Path) -> pd.DataFrame:
    """Reject malformed boolean tokens rather than casting nonempty strings."""
    frame = pd.read_csv(
        path,
        dtype={"municipality_code": str, "department_code": str, "alert": str},
        float_precision="round_trip",
    )
    boolean = frame.alert.map({"True": True, "False": False, "true": True, "false": False})
    if boolean.isna().any() or not frame.truth.isin([0, 1]).all():
        raise ValueError("Invalid frozen truth/alert tokens")
    frame["alert"] = boolean.astype(bool)
    if not np.isfinite(frame.score).all() or not frame.score.between(0, 1).all():
        raise ValueError("Invalid frozen probabilities")
    return frame


def comparator_inputs(table: pd.DataFrame, cohort: pd.DataFrame, h: int) -> pd.DataFrame:
    """Verify complete H5 history and separate origin-only inputs from outcomes."""
    validate_keys(table)
    validate_keys(cohort)
    states = table[KEYS].copy()
    states["excess"] = table.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[table.zona_canal_t.isna(), "excess"] = pd.NA
    outcome = labels(states, h)
    joined = cohort[KEYS].merge(outcome, on=KEYS, how="left", validate="one_to_one")
    if not joined.eligible_at_t.all() or joined.onset_target.isna().any():
        raise ValueError("Missing or ineligible outcome; no cohort reduction permitted")
    require_pair(
        cohort, joined.rename(columns={"onset_target": "truth"}), [*KEYS, "truth", "target_month"]
    )
    lookup = table.set_index(KEYS)
    counts = lookup.dengue_notifications_count.to_dict()
    rows = []
    for item in joined.itertuples(index=False):
        m, t, target = item.municipality_code, item.year_month, item.target_month
        periods = history_periods_for_target(target, 5)
        if any(p > t for p in periods):
            raise ValueError("Future history in CHANNEL")
        values = [counts.get((m, p)) for p in periods]
        current = counts.get((m, t))
        if any(pd.isna(v) for v in [current, *values]):
            raise ValueError("Missing CHANNEL input; complete contrast unavailable")
        if not np.isfinite(np.asarray([current, *values], dtype=float)).all():
            raise ValueError("Nonfinite CHANNEL input")
        p75 = percentile_type7(values, 0.75)
        if p75 != lookup.loc[(m, t), f"p75_h5_t{h}"]:
            raise ValueError("Published target-month historical P75 mismatch")
        # Verify source states using counts, including future counts ONLY as outcomes.
        for period in {t, target, str(pd.Period(target, freq="M") - 1)}:
            past = history_periods_for_target(period, 5)
            if any(p > t for p in past):
                raise ValueError("Outcome threshold history exceeds origin")
            historical = [counts.get((m, p)) for p in past]
            observed = counts.get((m, period))
            if any(pd.isna(v) for v in [observed, *historical]):
                raise ValueError("Missing H5 state verification input")
            excess = observed > percentile_type7(historical, 0.75)
            if excess != (lookup.loc[(m, period), "zona_canal_t"] == "EXCESO"):
                raise ValueError("Canonical H5 state disagrees with historical counts")
        rows.append(
            {
                "municipality_code": m,
                "year_month": t,
                "origin_count": current,
                "target_p75": p75,
                "history_first": periods[0],
                "history_last": periods[-1],
                "history_count": len(periods),
                "origin_zone": lookup.loc[(m, t), "zona_canal_t"],
                "target_excess": int(item.excess_target),
            }
        )
    return pd.DataFrame(rows)


def deterministic_alerts(inputs: pd.DataFrame, h: int) -> tuple[pd.Series, pd.Series]:
    """Approved strict CHANNEL and historical persistence; no future-state argument."""
    channel = inputs.origin_count.gt(inputs.target_p75)
    persistence = persistence_reference(
        inputs.rename(columns={"origin_zone": "zona_canal_t"}), horizon=h
    ).prediction_label.astype(bool)
    return channel, persistence


def _native_r0(spec: dict[str, Any], records: dict[str, Any]) -> dict[str, Any]:
    path = local_path(spec["path"])
    manifest = json.loads((path / "manifest.json").read_text())
    if identity(path / "manifest.json")["sha256"] != spec["manifest_sha256"]:
        raise ValueError("Native R0 manifest changed")
    records[spec["path"] + "/manifest.json"] = identity(path / "manifest.json")
    for name, fp in manifest["files"].items():
        records[spec["path"] + "/" + name] = fp
    replay_path = spec["path"] + "/replay/manifest.json"
    if identity(local_path(replay_path))["sha256"] != manifest["replay"]["manifest_sha256"]:
        raise ValueError("Native R0 replay identity changed")
    records[replay_path] = identity(local_path(replay_path))
    replay = json.loads(local_path(replay_path).read_text())
    for name, fp in replay["files"].items():
        records[spec["path"] + "/replay/" + name] = fp
    verify_records(records)
    return json.loads((path / "bundle.json").read_text())


def load_preflight() -> dict[str, Any]:
    """Verify identities, exact populations, labels and saved policies before scoring."""
    if identity(local_path(PROTOCOL))["sha256"] != PROTOCOL_SHA:
        raise ValueError("Frozen benchmark protocol changed")
    protocol = json.loads(local_path(PROTOCOL).read_text())
    authority = protocol["authority"]
    records = {PROTOCOL: identity(local_path(PROTOCOL)), authority["path"]: authority["identity"]}
    verify_records(records)
    sources = BetaSourcesDataset().load()
    records.update(sources["provenance"]["sources"])
    regional = prepare(sources, {"profile": "exp_beta01", "tracking": "disabled"})
    manifests, predictions, ledgers = {}, {}, {}
    for name in ("G0", "G1"):
        spec = protocol["sources"][name]
        manifests[name] = _bundle(spec["path"], spec["manifest_sha256"], records)
        predictions[name] = read_predictions(local_path(spec["path"] + "/predictions.csv"))
        ledgers[name] = json.loads(local_path(spec["path"] + "/cells.json").read_text())["cells"]
    native = _native_r0(protocol["sources"]["R0"], records)
    policies = json.loads(
        local_path(protocol["sources"]["G0"]["path"] + "/policies.json").read_text()
    )
    parts, audit = [], []
    for h in protocol["cohort"]["horizons"]:
        expected = pd.concat(
            [
                role_parts(regional["cohorts"][h], y, sources["protocol"])["parts"]["evaluation"]
                for y in protocol["cohort"]["evaluation_target_years"]
            ]
        ).rename(columns={"onset_target": "truth"})
        expected = expected[[*KEYS, "target_month", "department_code", "target_year", "truth"]]
        expected = expected.sort_values(KEYS).reset_index(drop=True)
        ref = protocol["cohort"]["expected"][str(h)]
        if len(expected) != ref["rows"] or int(expected.truth.sum()) != ref["onsets"]:
            raise ValueError("BETA cohort totals differ from frozen academic protocol")
        if set(expected.department_code) != {"50", "73"}:
            raise ValueError("Unexpected evaluation departments")
        inputs = comparator_inputs(sources["table"], expected, h)
        context = expected.merge(inputs, on=KEYS, how="left", validate="one_to_one")
        for arm in MODELS:
            owner = "G1" if arm == "G1_OFF" else "G0"
            family = "R0" if arm == "R0" else owner
            climate = "historical" if arm == "R0" else arm.split("_")[1]
            frame = predictions[owner]
            frame = frame.loc[
                frame.horizon.eq(h) & frame.arm.eq(family) & frame.climate.eq(climate)
            ].copy()
            require_pair(expected, frame, [*KEYS, "target_month", "department_code", "truth"])
            if not frame.year.eq(frame.target_month.str[:4].astype(int)).all():
                raise ValueError("Frozen evaluation year mismatch")
            if arm == "R0":
                original = sources["reference"].rename(columns={"origin_month": "year_month"})
                original = original.loc[original.horizon.eq(h)]
                require_pair(frame, original, [*KEYS, "target_month", "truth", "score", "alert"])
                # Also require the independent copy in the national bundle to match.
                copy = predictions["G1"]
                copy = copy.loc[copy.horizon.eq(h) & copy.arm.eq("R0")]
                require_pair(frame, copy, [*KEYS, "target_month", "truth", "score", "alert"])
            if arm == "G0_OFF":
                copy = predictions["G1"]
                copy = copy.loc[copy.horizon.eq(h) & copy.arm.eq("G0")]
                require_pair(frame, copy, [*KEYS, "target_month", "truth", "score", "alert"])
            for year in protocol["cohort"]["evaluation_target_years"]:
                selection = frame.loc[frame.year.eq(year)].copy()
                if arm == "R0":
                    old = original.loc[original.target_month.str[:4].eq(str(year))]
                    cell_ids = old.cell_id.unique()
                    if len(cell_ids) != 1:
                        raise ValueError("Ambiguous native R0 cell")
                    policy = next(v for v in native["thresholds"] if v["cell_id"] == cell_ids[0])
                    model_id = str(cell_ids[0])
                else:
                    cell = next(
                        v
                        for v in ledgers[owner]
                        if v["horizon"] == h
                        and v["year"] == year
                        and (owner == "G1" or v["climate"] == climate)
                    )
                    policy = (
                        cell["policy"]
                        if owner == "G1"
                        else next(
                            v
                            for v in policies["policies"]
                            if v["horizon"] == h
                            and v["year"] == year
                            and v["arm"] == "G0"
                            and v["climate"] == climate
                        )
                    )
                    model_id = manifests[owner]["files"][cell["model_file"]]["sha256"]
                threshold = policy["threshold"]
                saved_alert = (
                    selection.score.ge(threshold)
                    if threshold is not None
                    else pd.Series(False, index=selection.index)
                )
                if not selection.alert.eq(saved_alert).all():
                    raise ValueError("Frozen alert does not match saved policy")
                selection["model_identity"] = model_id
                selection["policy_identity"] = bytes_record(canonical_bytes(policy))["sha256"]
                selection["threshold"] = threshold
                selection["source_manifest_sha256"] = protocol["sources"][owner]["manifest_sha256"]
                selection["source_predictions_sha256"] = manifests[owner]["files"][
                    "predictions.csv"
                ]["sha256"]
                selection["arm"] = arm
                parts.append(
                    context.merge(
                        selection[
                            [
                                *KEYS,
                                "arm",
                                "score",
                                "alert",
                                "threshold",
                                "model_identity",
                                "policy_identity",
                                "source_manifest_sha256",
                                "source_predictions_sha256",
                            ]
                        ],
                        on=KEYS,
                        how="inner",
                        validate="one_to_one",
                    ).assign(horizon=h)
                )
        channel, persistence = deterministic_alerts(context, h)
        for arm, alerts in (("CHANNEL", channel), ("PERSISTENCE", persistence)):
            parts.append(
                context.assign(
                    arm=arm,
                    score=np.nan,
                    alert=alerts,
                    threshold=np.nan,
                    model_identity="deterministic",
                    policy_identity=PROTOCOL_SHA,
                    source_manifest_sha256=protocol["sources"]["canonical"]["manifest_sha256"],
                    source_predictions_sha256="not_applicable",
                    horizon=h,
                )
            )
        audit.append(
            {
                "horizon": h,
                **ref,
                "ordered_keys_sha256": bytes_record(serialize_table(expected[KEYS]))["sha256"],
                "labels_sha256": bytes_record(serialize_table(expected[[*KEYS, "truth"]]))[
                    "sha256"
                ],
                "exact_model_pairing": "PASS",
                "H5_state_and_history": "PASS",
                "comparator_input_rows": len(inputs),
                "cohort_rows_removed": 0,
            }
        )
    detailed = pd.concat(parts, ignore_index=True)
    detailed["year"] = detailed.target_month.str[:4].astype(int)
    detailed["onset_class"] = np.select(
        [
            detailed.alert & detailed.truth.eq(1),
            detailed.alert & detailed.truth.eq(0),
            ~detailed.alert & detailed.truth.eq(1),
        ],
        ["TP", "FP", "FN"],
        default="TN",
    )
    detailed["excess_class"] = np.select(
        [
            detailed.alert & detailed.target_excess.eq(1),
            detailed.alert & detailed.target_excess.eq(0),
            ~detailed.alert & detailed.target_excess.eq(1),
        ],
        ["TP", "FP", "FN"],
        default="TN",
    )
    detailed = detailed.sort_values(["horizon", "arm", *KEYS]).reset_index(drop=True)
    verify_records(records)
    return {"protocol": protocol, "records": records, "details": detailed, "audit": audit}


def aggregate(frame: pd.DataFrame) -> dict[str, Any]:
    """Preserve onset/excess denominators separately, including undefined FAR."""
    y, alert, excess = (
        frame.truth.astype(int),
        frame.alert.astype(bool),
        frame.target_excess.astype(int),
    )
    probabilistic = frame.score.notna().all()
    # Reuse the established BETA metric implementation; deterministic scores are
    # placeholders only for its shared counts, and never reported as probabilities.
    counted = frame if probabilistic else frame.assign(score=alert.astype(float))
    result = metric_row(counted, 1.0)
    if not probabilistic:
        result.update(average_precision=None, brier=None)
    alerts = int(alert.sum())
    false_excess = int((alert & excess.eq(0)).sum())
    negatives = int(excess.eq(0).sum())
    result.update(
        alerts=alerts,
        missed=result["onsets"] - result["detected"],
        onset_negatives=int(y.eq(0).sum()),
        target_excesses=int(excess.sum()),
        excess_negatives=negatives,
        false_alerts_excess=false_excess,
        continuation_alerts=int((alert & excess.eq(1) & y.eq(0)).sum()),
        far_excess=false_excess / alerts if alerts else None,
        fpr_excess=false_excess / negatives if negatives else None,
        fpr_onset=result["false_alerts"] / int(y.eq(0).sum()) if y.eq(0).any() else None,
    )
    return result


def comparisons(metrics: pd.DataFrame) -> pd.DataFrame:
    """All deltas use the same stratum; undefined denominators cannot pass."""
    rows = []
    for keys, group in metrics.groupby(STRATA, sort=False):
        lookup = group.set_index("arm").to_dict("index")
        for arm in MODELS:
            value = lookup[arm]
            c, p, r = (lookup[n] for n in ("CHANNEL", "PERSISTENCE", "R0"))
            a, b = value["detected"] > c["detected"], value["detected"] > p["detected"]
            far_defined = pd.notna(value["far_excess"]) and pd.notna(c["far_excess"])
            # Integer cross-multiplication avoids floating-point ambiguity at exactly 5 pp.
            condition_c = (
                (
                    20
                    * (
                        value["false_alerts_excess"] * c["alerts"]
                        - c["false_alerts_excess"] * value["alerts"]
                    )
                    <= value["alerts"] * c["alerts"]
                )
                if far_defined
                else None
            )
            status = (
                "NOT_EVALUABLE"
                if not far_defined
                else "MEETS"
                if a and b and condition_c
                else "DOES_NOT_MEET"
            )
            beta = (
                None
                if pd.isna(value["sensitivity"]) or pd.isna(r["sensitivity"])
                else bool(value["budget_met"] and value["sensitivity"] - r["sensitivity"] >= -0.02)
            )
            for reference in ("CHANNEL", "PERSISTENCE", "R0"):
                other = lookup[reference]
                delta = {
                    f"{name}_difference": value[name] - other[name]
                    for name in (
                        "sensitivity",
                        "detected",
                        "false_alerts",
                        "false_alerts_excess",
                        "far_excess",
                        "false_alerts_per_municipality_year",
                    )
                }
                rows.append(
                    {
                        **dict(zip(STRATA, keys, strict=True)),
                        "arm": arm,
                        "reference": reference,
                        "rows": value["rows"],
                        "onsets": value["onsets"],
                        **delta,
                        "condition_A": a,
                        "condition_B": b,
                        "condition_C": condition_c,
                        "academic_status": status,
                        "beta_joint_descriptive": beta,
                    }
                )
    return pd.DataFrame(rows)


def summarize(details: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Report each horizon, pooled/annual and pooled/department cross-stratum."""
    rows = []
    for (h, arm), frame in details.groupby(["horizon", "arm"], sort=True):
        for year in ["all", *sorted(frame.year.unique())]:
            for dept in ["all", "50", "73"]:
                subset = (
                    frame.loc[
                        (True if year == "all" else frame.year.eq(year))
                        & (True if dept == "all" else frame.department_code.eq(dept))
                    ]
                    if not (year == "all" and dept == "all")
                    else frame
                )
                if subset.empty:
                    raise ValueError("Missing required stratum")
                rows.append(
                    {
                        "horizon": int(h),
                        "arm": arm,
                        "year": str(year),
                        "department": dept,
                        **aggregate(subset),
                    }
                )
    metrics = pd.DataFrame(rows)
    return metrics, comparisons(metrics)


def artifacts(preflight: dict[str, Any]) -> dict[str, Any]:
    """Build reproducible private evidence; source checks bracket computation."""
    verify_records(preflight["records"])
    details = preflight["details"]
    metrics, paired = summarize(details)
    code_paths = [
        "src/sat_dengue/experiments/academic_benchmark.py",
        "src/sat_dengue/experiments/exp_beta01.py",
        "src/sat_dengue/experiments/onset.py",
        "src/sat_dengue/experiments/exp_beta01_v2.py",
        "src/sat_dengue/datasets/exp_beta01.py",
        "src/sat_dengue/datasets/exp_beta01_v2.py",
        "src/sat_dengue/datasets/canonical.py",
        "src/sat_dengue/data/consolidation.py",
        "src/sat_dengue/model_training/references.py",
        "src/sat_dengue/training_preparation/serialization.py",
        "src/sat_dengue/datasets/legacy_preparation/persistence.py",
    ]
    code = {p: identity(local_path(p)) for p in code_paths}
    import importlib.metadata

    provenance = {
        "sources": preflight["records"],
        "execution": {
            "code": code,
            "packages": {
                n: importlib.metadata.version(n) for n in ("numpy", "pandas", "scikit-learn")
            },
        },
    }
    payloads = {
        "predictions.csv": serialize_table(details),
        "metrics.csv": serialize_table(metrics),
        "comparisons.csv": serialize_table(paired),
        "protocol.json": local_path(PROTOCOL).read_bytes(),
        "preflight.json": canonical_bytes({"cohorts": preflight["audit"], "status": "PASS"}),
        "provenance.json": canonical_bytes(provenance),
    }
    body = {
        "schema": "academic-benchmark-publication-v1",
        "evidence_type": "authorized_retrospective",
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": preflight["records"],
        "code": code,
        "model_fits": 0,
        "inference_calls": 0,
        "calibrations": 0,
        "threshold_searches": 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    )
    verify_records(preflight["records"])
    return {"payloads": payloads, "provenance": provenance}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--publish", action="store_true")
    action.add_argument("--verify", metavar="BUNDLE_ID")
    args = parser.parse_args()
    checked = load_preflight()
    if args.preflight:
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "cohorts": checked["audit"],
                    "verified_source_files": len(checked["records"]),
                }
            )
        )
        return
    result = artifacts(checked)
    manifest = json.loads(result["payloads"]["manifest.json"])
    if args.verify:
        if args.verify != manifest["bundle_id"]:
            raise ValueError("Recomputed publication identity differs")
        verify_bundle(local_path(OUTPUT + "/" + args.verify), result["payloads"])
        print(json.dumps({"status": "REPRODUCTION_PASS", "bundle_id": args.verify}))
        return
    publisher = CanonicalBundleDataset(OUTPUT)
    publisher.save(result)
    published = publisher.load()
    print(
        json.dumps(
            {
                "status": "PUBLISHED",
                "path": published["path"],
                "manifest_sha256": bytes_record(result["payloads"]["manifest.json"])["sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
