"""Critical final-route regressions using synthetic inputs only; no reserved reads."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.final_evaluation import pipeline
from scripts.final_evaluation.cohorts import build_cohorts, validate_cohort
from scripts.final_evaluation.evaluation import circular_draws, evaluate_horizon, research_result
from scripts.final_evaluation.protocol import require_authorization
from scripts.model_assessment.policy import proposed_calendar
from scripts.model_training.references import persistence_reference
from scripts.training_preparation.features import DERIVED_COLUMNS

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def synthetic() -> tuple[dict[str, Any], dict[int, Any], pd.DataFrame, dict[str, Any]]:
    """Two synthetic municipalities with complete history, actual calendars and both classes."""
    contract = json.loads(
        (ROOT / "docs/product/stage-3/training_preparation_contract_v1.json").read_text()
    )
    settings = json.loads(
        (ROOT / "docs/product/stage-5/model_evaluation_contract_v1.json").read_text()
    )["proposed_final"]["uncertainty"]
    population = ["50001", "73001"]
    periods = pd.period_range("2011-01", "2025-12", freq="M")
    rows = []
    for m, code in enumerate(population):
        for i, month in enumerate(periods):
            row: dict[str, Any] = {
                c: float(10 + (i * (m + 1)) % 7) for c in contract["roles"]["predictors"]
            }
            row.update(
                municipality_code=code,
                year_month=str(month),
                zona_canal_t="EXCESO" if (i + m) % 4 in [1, 2] else "SEGURIDAD",
            )
            for h in [1, 2]:
                row[f"target_period_t{h}"] = str(month + h)
                row[f"y_t{h}"] = int((i + h + m) % 4 in [1, 2])
                row[f"y_evaluable_t{h}"] = True
            rows.append(row)
    panel = pd.DataFrame(rows)
    columns = ["municipality_code", *contract["roles"]["predictors"], *DERIVED_COLUMNS]
    configs = {
        "xgboost": dict(
            n_estimators=3,
            max_depth=2,
            eta=0.1,
            reg_lambda=1,
            reg_alpha=0,
            max_bin=16,
            min_child_weight=1,
        ),
        "lightgbm": dict(
            n_estimators=3,
            max_depth=2,
            num_leaves=3,
            learning_rate=0.1,
            lambda_l1=0,
            lambda_l2=1,
            max_bin=16,
            min_data_in_leaf=3,
        ),
        "gam": dict(n_knots=3, C=1.0),
    }
    procedures = []
    for h in [1, 2]:
        for family, parameters in configs.items():
            procedures.append(
                dict(
                    proposed_calendar(h),
                    candidate=family,
                    retained_internal_components=dict(selected_parameters=parameters),
                    future_preparer=dict(
                        input_columns=columns,
                        spec=dict(
                            encoding="onehot",
                            numeric_missing="error",
                            numeric_scaling="none",
                            unknown_municipality="explicit",
                        ),
                    ),
                    retained_calibrator=dict(calibration_choice="original", available=False),
                    retained_threshold=dict(selected_threshold=0.5, calibration_choice="original"),
                    retained_component_availability_checks=[
                        dict(producer_role="threshold_selection", effective_availability="2024-03")
                    ],
                )
            )
    proposal = dict(
        procedures=procedures,
        common_population=population,
        rules=dict(proposed_final=dict(uncertainty=settings)),
    )
    return proposal, build_cohorts(panel, contract, proposal), panel, contract


def test_authorization_precedes_scientific_reads_and_fits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither direct production execution nor verify can load final values without consent."""

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Scientific access before human authority")

    monkeypatch.setattr(pipeline, "load_cohorts", forbidden)
    monkeypatch.setattr(pipeline, "load_proposal", forbidden)
    monkeypatch.setattr(pipeline, "fit_model", forbidden)
    for verify in [False, True]:
        with pytest.raises(PermissionError, match="human"):
            pipeline.run_final(tmp_path, verify_only=verify)
    with pytest.raises(PermissionError):
        require_authorization(tmp_path)


def test_readiness_reports_post_freeze_dependency_drift_without_authorizing_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Readiness remains usable after closure while scientific execution stays blocked."""

    archived = pipeline.load_archived_proposal(ROOT)
    monkeypatch.setattr(pipeline, "load_archived_proposal", lambda root: archived)

    def changed(root: Path) -> dict[str, Any]:
        raise ValueError("Frozen scientific contract changed")

    monkeypatch.setattr(pipeline, "load_proposal", changed)
    result = pipeline.readiness(ROOT)
    assert result["status"] == "human_authorization_recorded"
    assert result["live_frozen_dependencies"] == "changed_after_freeze"
    assert result["live_dependency_error"] == "Frozen scientific contract changed"
    assert result["scientific_execution_allowed"] is False
    assert result["new_fits"] == 0


def test_t2_calendar_all_cohorts_before_fit_and_future_invariance(
    synthetic: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject T2 December training and cohort/feature defects before any model call."""
    proposal, cohorts, panel, contract = synthetic
    assert cohorts[2].index.year_month.min() == "2024-11"
    assert cohorts[2].train_index.target_period.max() == "2024-11"
    original = cohorts[2].X.loc[cohorts[2].index.year_month.eq("2024-11")]
    changed = panel.copy()
    changed.loc[changed.year_month > "2024-11", "rain_mm_month_sum"] = 99999
    revised = build_cohorts(changed, contract, proposal)
    pd.testing.assert_frame_equal(
        original, revised[2].X.loc[revised[2].index.year_month.eq("2024-11")]
    )

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Fit before complete six-procedure preflight")

    monkeypatch.setattr(pipeline, "fit_model", forbidden)
    for defect in ["date", "cohort", "future_control", "last_threshold"]:
        broken = copy.deepcopy(cohorts)
        frozen = copy.deepcopy(proposal)
        if defect == "date":
            broken[2].train_index.loc[0, "target_period"] = "2024-12"
        elif defect == "cohort":
            broken[2].index = broken[2].index.iloc[:-1]
        elif defect == "future_control":
            broken[2].X["actual_onset"] = True
        else:
            frozen["procedures"][-1]["retained_threshold"]["selected_threshold"] = None
        with pytest.raises(ValueError):
            pipeline.execute_bundle(tmp_path, frozen, broken, {"fixture": "synthetic"})


def test_shared_blocks_preserve_original_states_and_annual_metrics(synthetic: Any) -> None:
    """Pairing is by whole months; never reconstruct onset transitions at artificial joins."""
    proposal, cohorts, _, _ = synthetic
    cohort = cohorts[1]
    prediction = persistence_reference(cohort.X, horizon=1)
    predictions = {
        name: prediction.copy() for name in ["persistence", "xgboost", "lightgbm", "gam"]
    }
    table, metrics, intervals, draws = evaluate_horizon(
        cohort, predictions, proposal["rules"]["proposed_final"]["uncertainty"]
    )
    np.testing.assert_array_equal(draws, circular_draws(12))
    assert draws.shape == (2000, 12)
    assert (draws[:, 1::3] == (draws[:, ::3] + 1) % 12).all()
    assert table.real_onsets.eq(int(cohort.context.actual_onset.sum())).all()
    monthly = metrics[
        (metrics.candidate == "persistence")
        & (metrics.scope == "period")
        & (metrics.metric == "onset_sensitivity")
    ]
    assert monthly.numerator.sum() == table.iloc[0].detected_onsets
    assert monthly.denominator.sum() == table.iloc[0].real_onsets
    assert intervals.lower.dropna().eq(0).all()
    # Exact duplicate original rows keep S/S-1 and onset; the concatenation order
    # is irrelevant, unlike shifting/rebuilding context at block joins.
    months = sorted(cohort.index.target_period.unique())
    selected = np.concatenate(
        [np.flatnonzero(cohort.index.target_period.eq(months[i])) for i in draws[0]]
    )
    expected = sum(
        int(cohort.context.loc[cohort.index.target_period.eq(months[i]), "actual_onset"].sum())
        for i in draws[0]
    )
    assert int(cohort.context.iloc[selected].actual_onset.sum()) == expected


def test_missing_evidence_cannot_pass_or_disappear(synthetic: Any) -> None:
    """Unknown Y/context and absent denominators cannot qualify a candidate."""
    assert research_result(False, 0.4, -0.4, 0.3, -0.3) == "insufficient_evidence"
    assert research_result(True, np.nan, 0, 0.2, 0.01) == "insufficient_evidence"
    assert research_result(True, 0.2, 0, np.nan, 0.01) == "insufficient_evidence"
    assert research_result(True, 0.09, 0, 0.2, 0.01) == "does_not_meet"
    proposal, cohorts, _, _ = synthetic
    cohort = cohorts[1]
    cohort.y.iloc[0] = pd.NA
    validate_cohort(cohort, proposal)
    prediction = persistence_reference(cohort.X, horizon=1)
    predictions = {
        name: prediction.copy() for name in ["persistence", "xgboost", "lightgbm", "gam"]
    }
    table, _, intervals, _ = evaluate_horizon(
        cohort, predictions, proposal["rules"]["proposed_final"]["uncertainty"]
    )
    assert len(table) == 4 and table.examples.eq(24).all()
    assert table[table.candidate.ne("persistence")].result.eq("insufficient_evidence").all()
    assert intervals.valid_resamples.eq(0).all() and intervals.lower.isna().all()


def test_native_roundtrip_reuse_verify_no_fallback_and_budget(
    synthetic: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise all three real adapters on synthetic rows and restore every saved model."""
    proposal, cohorts, _, _ = synthetic
    identity = {"fixture": "synthetic-only", "version": 1}
    fitted = pipeline.execute_bundle(tmp_path, proposal, cohorts, identity)
    assert (fitted["new_model_fits"], fitted["new_preparer_fits"]) == (6, 6)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("Replay attempted fitting")

    monkeypatch.setattr(pipeline, "fit_model", forbidden)
    from scripts.model_training.candidate_families import ADAPTERS

    for adapter in ADAPTERS.values():
        monkeypatch.setattr(adapter, "fit_candidate", forbidden)
        monkeypatch.setattr(adapter, "fit_representation", forbidden)
    for verify in [True, False]:
        replay = pipeline.execute_bundle(tmp_path, proposal, cohorts, identity, verify_only=verify)
        assert replay["summary"] == fitted["summary"] and replay["new_model_fits"] == 0
    with pytest.raises(FileNotFoundError):
        pipeline.execute_bundle(
            tmp_path, proposal, cohorts, {"fixture": "changed"}, verify_only=True
        )
    with pytest.raises(FileExistsError):
        pipeline.execute_bundle(tmp_path, proposal, cohorts, {"fixture": "changed"})
    bundle = tmp_path / fitted["summary"]["bundle"]
    model_path = bundle / "gam_t2_model.json"
    model_path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="Corrupt"):
        pipeline.execute_bundle(tmp_path, proposal, cohorts, identity, verify_only=True)
    assert model_path.read_bytes() == b"corrupt"
