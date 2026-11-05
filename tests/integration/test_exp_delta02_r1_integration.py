"""Generated integration checks for the single EXP-DELTA02-R1 candidate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.canonical.table import CLIMATE, PREDICTORS
from sat_dengue.datasets.legacy_preparation.contract import PreparationError
from sat_dengue.experiments.exp_delta02_r1 import (
    COMPARATORS,
    FEATURE,
    candidate_predictors,
    evaluate_candidate,
    execution_artifacts,
    fit_candidate,
    metric_tables,
    publish_real,
    verified_publication,
    verify_source_spec,
)


def generated_protocol() -> dict[str, Any]:
    return {
        "training_start": "2011-06",
        "evaluation_years": [2020],
        "reserved_target_start": "2025-01",
        "model": {
            "family": "xgboost",
            "n_estimators": 80,
            "max_depth": 2,
            "learning_rate": 0.05,
            "max_bin": 128,
            "min_child_weight": 5,
            "reg_alpha": 0,
            "reg_lambda": 1,
            "subsample": 1.0,
            "colsample_bytree": 1.0,
            "random_state": 1729,
            "n_jobs": 1,
            "tree_method": "hist",
            "objective": "binary:logistic",
        },
        "calibration": {"penalty": 1.0},
        "policy": {"budget_false_alerts_per_municipality_year": 1.0},
    }


def generated_frame() -> pd.DataFrame:
    periods = pd.period_range("2011-06", "2020-11", freq="M")
    rows = []
    for index, period in enumerate(periods):
        row: dict[str, Any] = {
            "municipality_code": "50001" if index % 2 == 0 else "73001",
            "year_month": str(period - 1),
            "target_month": str(period),
            "department_code": "50" if index % 2 == 0 else "73",
            "target_year": period.year,
            "onset_target": index % 3 == 0,
            "earlier_onset_t1": False,
            FEATURE: np.nan if index % 5 == 0 else float(index % 7),
            "neighbor_count": 3,
            "neighbor_values_available": 2 if index % 5 == 0 else 3,
            "neighbor_values_missing": 1 if index % 5 == 0 else 0,
            "neighbor_feature_missing_reason": "unknown_neighbor_count" if index % 5 == 0 else None,
        }
        for offset, name in enumerate(PREDICTORS):
            row[name] = float((index + offset) % 11)
        row["zona_canal_t"] = index % 3
        rows.append(row)
    return pd.DataFrame(rows)


def frozen_details(candidate: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for arm_index, arm in enumerate(COMPARATORS):
        part = candidate[
            [
                "municipality_code",
                "year_month",
                "target_month",
                "department_code",
                "target_year",
                "truth",
                "target_excess",
                "horizon",
                "year",
            ]
        ].copy()
        part["arm"] = arm
        part["alert"] = np.arange(len(part)) % (arm_index + 2) == 0
        part["score"] = np.linspace(0.01, 0.99, len(part)) if arm in {"R0", "G0_OFF"} else np.nan
        rows.append(part)
    return pd.concat(rows, ignore_index=True)


def test_candidate_uses_only_g0_off_plus_spatial_configuration() -> None:
    assert candidate_predictors() == [name for name in PREDICTORS if name not in CLIMATE] + [
        FEATURE
    ]
    protocol = generated_protocol()
    assert protocol["model"]["n_estimators"] == 80
    assert protocol["model"]["max_depth"] == 2
    assert protocol["model"]["learning_rate"] == 0.05


def test_temporal_candidate_ignores_gap_and_evaluation_truth_for_fit_policy() -> None:
    protocol = generated_protocol()
    frame = generated_frame()
    first = fit_candidate(frame, protocol)
    changed = frame.copy()
    changed.loc[changed.target_year.eq(2020), "onset_target"] = ~changed.loc[
        changed.target_year.eq(2020), "onset_target"
    ]
    second = fit_candidate(changed, protocol)
    assert first["model_fits"] == first["calibrations"] == first["policy_selections"] == 1
    assert first["cells"][0]["gap_role"].startswith("adaptation (Y-2) intentionally unused")
    assert first["cells"][0]["model_bytes"] == second["cells"][0]["model_bytes"]
    assert first["cells"][0]["global_offset"] == second["cells"][0]["global_offset"]
    assert first["cells"][0]["policy"] == second["cells"][0]["policy"]
    np.testing.assert_array_equal(first["predictions"].score, second["predictions"].score)
    np.testing.assert_array_equal(first["predictions"].alert, second["predictions"].alert)


def test_metric_candidate_reports_academic_far_and_all_strata() -> None:
    fitted = fit_candidate(generated_frame(), generated_protocol())
    candidate = fitted["predictions"]
    details = pd.concat([candidate, frozen_details(candidate)], ignore_index=True, sort=False)
    metrics, comparisons = metric_tables(details)
    assert len(metrics) == 5 * 6  # pooled + two departments; year + two year-departments.
    assert len(comparisons) == 6 * 4
    pooled = comparisons.loc[
        comparisons.year.eq("all")
        & comparisons.department.eq("all")
        & comparisons.reference.eq("CHANNEL")
    ].iloc[0]
    assert pooled.academic_status in {"MEETS", "DOES_NOT_MEET", "NOT_EVALUABLE"}
    assert pooled.condition_C in {True, False, None}


def test_cohort_comparator_mismatch_is_rejected() -> None:
    fitted = fit_candidate(generated_frame(), generated_protocol())
    candidate = fitted["predictions"]
    frozen = frozen_details(candidate)
    frozen.loc[frozen.arm.eq("G0_OFF").idxmax(), "truth"] ^= 1
    with pytest.raises(ValueError, match="value mismatch"):
        evaluate_candidate({"frozen": frozen}, fitted)


def test_publication_is_deterministic_and_rejects_changed_existing_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fitted = fit_candidate(generated_frame(), generated_protocol())
    candidate = fitted["predictions"]
    result = evaluate_candidate({"frozen": frozen_details(candidate)}, fitted)
    owner = tmp_path / "owner"
    owner.mkdir()
    protocol = {"experiment_id": "EXP-DELTA02-R1"}
    sources = {"experiment_id": "EXP-DELTA02-R1"}
    (owner / "protocol.json").write_text(json.dumps(protocol))
    (owner / "sources.json").write_text(json.dumps(sources))
    import sat_dengue.experiments.exp_delta02_r1 as module

    monkeypatch.setattr(module, "OWNER", owner)
    monkeypatch.setattr(module, "OUTPUT", tmp_path / "published")
    preflight: dict[str, Any] = {"records": {}}
    first = execution_artifacts(preflight, result)
    second = execution_artifacts(preflight, result)
    assert first == second
    target = publish_real(first)
    assert publish_real(second) == target
    (target / "metrics.csv").write_bytes(b"changed")
    with pytest.raises(PreparationError, match="stale or corrupted"):
        publish_real(second)


def test_real_publication_reconciles_exact_private_execution() -> None:
    spec = json.loads(Path("docs/product/experiments/EXP-DELTA02-R1/sources.json").read_bytes())
    private_paths = [
        Path(spec["dependency"]["original_result_path"]),
        *(Path(record["path"]) for record in spec["sources"].values()),
    ]
    if any(not path.exists() for path in private_paths):
        pytest.skip("pinned private sources are unavailable on this host")

    verify_source_spec(spec)
    target, manifest = verified_publication(
        {
            "path": (
                "data/processed/exp_delta02_r1/"
                "1d2665c4a348ddcf9aa270336cb89f27b490d6292c393f8ef88b4c98c84a57d8"
            ),
            "manifest_sha256": ("33a8b2d21cb7b97aa7015a1ffcf419528a327127b648cb3bcaefbc4325f01975"),
        }
    )
    assert manifest["bundle_id"] == (
        "1d2665c4a348ddcf9aa270336cb89f27b490d6292c393f8ef88b4c98c84a57d8"
    )
    conclusions = json.loads((target / "conclusions.json").read_bytes())
    predictions = pd.read_csv(target / "predictions.csv")
    candidate = predictions.loc[predictions.arm.eq("R1_SPATIAL")]
    assert conclusions["scientific_disposition"] == "NOT_SUPPORTED"
    assert len(candidate) == 2653
    assert int(candidate.truth.sum()) == 313
