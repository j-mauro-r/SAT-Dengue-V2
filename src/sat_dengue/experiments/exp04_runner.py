"""EXP04 read-only readiness and generated functional exercise; no real science."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp03 import load_protocol
from sat_dengue.experiments.exp03_preflight import safe_path
from sat_dengue.experiments.exp04 import (
    apply_calibrator,
    calibration_window,
    evaluate_frozen,
    fit_calibrator,
    temporal_roles,
    threshold_policy,
)
from sat_dengue.experiments.exp04_baseline import audit_baseline, paired_support
from sat_dengue.experiments.exp04_contract import BASELINE, ROOT, digest, protocol


def preflight(directory: Path = BASELINE) -> dict[str, Any]:
    """No training/calibration/threshold selection; unavailable arms stay explicit."""
    p = protocol()
    if json.loads((ROOT / "protocol.json").read_text()) != p:
        raise ValueError("EXP04 technical protocol changed")
    if hashlib.sha256((ROOT / "DESING.md").read_bytes()).hexdigest() != p["design_sha256"]:
        raise ValueError("EXP04 authority design changed")
    baseline = audit_baseline(directory)
    return {
        "schema": "exp04-readiness-v1",
        "experiment_id": "EXP04",
        "status": "BLOCKED_BASELINE",
        "baseline": baseline,
        "scientific_protocol": "BLOCKED_DESIGN",
        "unresolved_scientific_inputs": p["unresolved_scientific_inputs"],
        "arms": {
            name: {"status": "NOT_EVALUABLE", "reason": "baseline_and_temporal_support_unverified"}
            for name in p["arms"]
        },
        "cuts": {str(year): "NOT_EVALUABLE" for year in (2020, 2021, 2022, 2024, 2025)},
        "protocol_sha256": digest(p),
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "private_source_reads": 0,
        "model_fits": 0,
        "calibrator_fits": 0,
        "threshold_selections": 0,
        "mlflow_writes": 0,
    }


def generated_scores(start: str, end: str, horizon: int) -> pd.DataFrame:
    """Deterministic probability fixture, never an M00 or native-family prediction."""
    rows = []
    for i, month in enumerate(pd.period_range(start, end, freq="M")):
        for j, code in enumerate(("50001", "50002", "73001", "73002")):
            truth = int((i + j) % 3 == 0)
            rows.append(
                {
                    "municipality_code": code,
                    "target_month": str(month),
                    "forecast_issue_date": str((month - horizon).start_time.date()),
                    "target_date": str(month.start_time.date()),
                    "label_available_date": str((month.start_time + pd.Timedelta(days=14)).date()),
                    "training_cutoff": "2014-01-01",
                    "horizon": horizon,
                    "family": "generated_fixed_probability_fixture",
                    "raw_score": float(((i * 3 + j * 7) % 19 + 1) / 21),
                    "truth": truth,
                    "error_class": "onset"
                    if truth
                    else ("continuation" if (i + j) % 5 == 0 else "no_excess"),
                    "selection_block": str(month.year) + ("a" if month.month < 7 else "b"),
                }
            )
    return pd.DataFrame(rows)


def compare_policies(
    reference: pd.DataFrame,
    candidate: pd.DataFrame,
    ref_metrics: dict[str, Any],
    cand_metrics: dict[str, Any],
) -> dict[str, Any]:
    support = paired_support(reference, candidate)
    if support["status"] != "evaluable":
        return support
    if (
        ref_metrics["objective"] != cand_metrics["objective"]
        or ref_metrics["common_exposure"] != cand_metrics["common_exposure"]
        or ref_metrics["common_exposure"] != support["common_exposure"]
    ):
        return {"status": "NOT_EVALUABLE", "reason": "objective_or_exposure_differs"}
    keys = (
        "sensitivity",
        "false_alerts",
        "alerts_emitted",
        "precision",
        "common_FA_rate",
        "brier",
        "ece",
        "average_precision",
    )
    return {
        **support,
        "candidate_minus_reference": {
            key: None
            if ref_metrics[key] is None or cand_metrics[key] is None
            else cand_metrics[key] - ref_metrics[key]
            for key in keys
        },
        "uncertainty": "UNAVAILABLE",
        "classification": "FUNCTIONAL_ONLY",
    }


def _provenance() -> dict[str, Any]:
    sources = [
        *Path("src/sat_dengue/experiments").glob("exp04*.py"),
        Path("src/sat_dengue/experiments/exp03_1_evaluation.py"),
        Path("src/sat_dengue/experiments/exp03_persistence.py"),
        Path("src/sat_dengue/model_evaluation/calibration.py"),
        Path("src/sat_dengue/configuration.py"),
        Path("src/sat_dengue/hooks.py"),
        Path("src/sat_dengue/pipeline_registry.py"),
        Path("src/sat_dengue/pipelines/exp04/pipeline.py"),
    ]
    return {
        "code_sha256": digest(
            {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)}
        ),
        "protocol_sha256": digest(protocol()),
        "parent_protocol_sha256": digest(load_protocol()),
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ("numpy", "pandas", "scikit-learn")},
        "predictor": "generated_probability_formula_no_fit_not_M00",
        "seed": load_protocol()["design"]["seed"],
        "functional_fixture_only": {
            "isotonic_minimum_per_class": 2,
            "ECE_bins": 10,
            "maturity": "target_month_start_plus_14_days",
        },
    }


def functional_run() -> dict[str, Any]:
    """Exercise isolated factors on generated input; never select a real policy."""
    provenance = _provenance()
    output: dict[str, Any] = {
        "schema": "exp04-functional-bundle-v1",
        "experiment_id": "EXP04",
        "evidence_type": "generated_functional_only",
        "reference_is_M00": False,
        "provenance": provenance,
        "predictions": [],
        "input_sha256_by_horizon": {},
        "metrics": [],
        "thresholds": [],
        "calibrators": [],
        "strata": [],
        "contrasts": [],
        "temporal_roles": [],
        "D": {"status": "NOT_EVALUABLE", "reason": "no_independent_nested_development_selection"},
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "scientific_hypotheses": {h: "NOT_EVALUATED" for h in ("H1", "H1a", "H1b", "H1c")},
        "execution_counters": {
            "real_private_reads": 0,
            "real_model_fits": 0,
            "real_calibrator_fits": 0,
            "mlflow_writes": 0,
        },
    }
    for horizon in (1, 2):
        cal = generated_scores("2016-01", "2018-12", horizon)
        selection = generated_scores("2019-04", "2019-12", horizon)
        evaluation = generated_scores("2020-03", "2020-12", horizon)
        output["input_sha256_by_horizon"][str(horizon)] = digest(
            {
                "calibration": cal.to_dict(orient="records"),
                "selection": selection.to_dict(orient="records"),
                "evaluation": evaluation.to_dict(orient="records"),
            }
        )
        dates: dict[str, Any] = {
            "horizon": horizon,
            "calibration_cutoff": "2019-01-15",
            "decision_date": "2019-12-31",
        }
        output["temporal_roles"].append(temporal_roles(cal, selection, evaluation, **dates))
        windows = {
            name: calibration_window(
                cal, months=months, last_mature_month="2018-12", cutoff="2019-01-15"
            )[0]
            for name, months in (("A1", 12), ("A2", 24), ("A3", 36), ("A4", None))
        }
        windows["A0"] = cal.loc[cal.target_month.ge("2018-07")].copy()
        window12 = windows["A1"]
        rows_by_arm, metrics_by_arm = {}, {}
        for arm in ("A0", "A1", "A2", "A3", "A4", "B0", "B1", "B2", "C0", "C1", "C2"):
            method = "isotonic" if arm == "B2" else "sigmoid"
            fit_rows = windows[arm] if arm.startswith("A") else window12
            state = fit_calibrator(
                fit_rows, method=method, seed=provenance["seed"], minimum_class_support=2
            )
            chosen = selection.copy()
            chosen["score"] = apply_calibrator(chosen, state)
            decision = threshold_policy(chosen, policy=arm if arm.startswith("C") else "C0")
            predicted, metric = evaluate_frozen(
                evaluation,
                state,
                decision["threshold"],
                bins=10,
                objective="onset",
                historical_exposure=4.0,
            )
            metric.update(
                arm=arm,
                horizon=horizon,
                family="generated_fixed_probability_fixture",
                cut="development_2020_fixture",
            )
            metric["selection_common_FA_rate"] = decision["false_alerts"] / (len(selection) / 12)
            metric["selection_evaluation_drift"] = (
                metric["common_FA_rate"] - metric["selection_common_FA_rate"]
            )
            metric["interannual_dispersion"] = {
                "status": "UNAVAILABLE",
                "reason": "one_functional_evaluation_year",
            }
            predicted["arm"] = arm
            predicted["objective"] = "onset"
            predicted["calibration_cutoff"] = dates["calibration_cutoff"]
            predicted["decision_date"] = dates["decision_date"]
            output["predictions"].extend(predicted.to_dict(orient="records"))
            output["metrics"].append(metric)
            output["thresholds"].append(
                {"arm": arm, "horizon": horizon, **decision, "frozen_at": dates["decision_date"]}
            )
            output["calibrators"].append(
                {
                    "arm": arm,
                    "horizon": horizon,
                    "frozen_at": dates["calibration_cutoff"],
                    "fit_rows": len(fit_rows),
                    "state": state,
                }
            )
            rows_by_arm[arm], metrics_by_arm[arm] = predicted, metric
            for (year, department), group in evaluation.groupby(
                [evaluation.target_month.str[:4], evaluation.municipality_code.str[:2]]
            ):
                _, group_metrics = evaluate_frozen(
                    group, state, decision["threshold"], bins=10, objective="onset"
                )
                output["strata"].append(
                    {
                        "arm": arm,
                        "horizon": horizon,
                        "year": str(year),
                        "department": str(department),
                        "metrics": group_metrics,
                    }
                )
        for question, contrasts in protocol()["contrasts"].items():
            if question == "H1":
                continue
            for candidate, reference in contrasts:
                output["contrasts"].append(
                    {
                        "question": question,
                        "horizon": horizon,
                        "candidate": candidate,
                        "reference": reference,
                        **compare_policies(
                            rows_by_arm[reference],
                            rows_by_arm[candidate],
                            metrics_by_arm[reference],
                            metrics_by_arm[candidate],
                        ),
                    }
                )
        # Identity/no recalibration is meaningful for this generated probability fixture.
        _, diagnostic = evaluate_frozen(
            evaluation, {"method": "identity"}, 0.7, bins=10, objective="onset"
        )
        output.setdefault("fixed_uncalibrated_diagnostics", []).append(
            {"horizon": horizon, "fixture_threshold": 0.7, "metrics": diagnostic}
        )
        if horizon == 2:
            # Separate control structure only; no onset-budget threshold is selected.
            excess = evaluation.copy()
            excess.loc[excess.error_class.eq("continuation"), "truth"] = 1
            _, control = evaluate_frozen(
                excess, {"method": "identity"}, 0.7, bins=10, objective="excess_control"
            )
            output["excess_control"] = {
                "horizon": 2,
                "diagnostic_only": True,
                "fixture_threshold": 0.7,
                "metrics": control,
            }
    output["fixture_sha256"] = digest(
        {
            "formula": "((i*3+j*7)%19+1)/21",
            "calibration": ["2016-01", "2018-12"],
            "selection": ["2019-04", "2019-12"],
            "evaluation": ["2020-03", "2020-12"],
        }
    )
    output["bundle_id"] = digest(output)
    return output


def write_result(result: dict[str, Any], destination: Path) -> None:
    """New ignored output directory only; never overwrite historical artifacts."""
    path = safe_path(str(destination))
    if not path.is_relative_to(Path.cwd().resolve() / "tmp") or not path.name.startswith("exp04-"):
        raise ValueError("EXP04 outputs require a new tmp/exp04-* directory")
    path.mkdir(parents=True, exist_ok=False)
    (path / "result.json").write_bytes(canonical_bytes(result))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--functional", action="store_true")
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = preflight(args.baseline) if args.dry_run else functional_run()
    if args.output:
        write_result(result, args.output)
    print(
        json.dumps(
            {
                "experiment_id": "EXP04",
                "status": result.get("status", "FUNCTIONAL_ONLY"),
                "bundle_id": result.get("bundle_id"),
                "output": str(args.output) if args.output else None,
                "G5": "NOT_APPROVED",
                "champion": "not_selected",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
