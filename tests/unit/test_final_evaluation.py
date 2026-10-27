"""Critical final-route regressions using synthetic inputs only; no reserved reads."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from evaluation_test_fixtures import synthetic as synthetic

from sat_dengue.datasets.legacy_evaluation.final_evaluation import pipeline
from sat_dengue.datasets.legacy_evaluation.final_evaluation.cohorts import (
    build_cohorts,
    validate_cohort,
)
from sat_dengue.datasets.legacy_evaluation.final_evaluation.evaluation import (
    circular_draws,
    evaluate_horizon,
    research_result,
)
from sat_dengue.datasets.legacy_evaluation.final_evaluation.protocol import require_authorization
from sat_dengue.model_training.references import persistence_reference

ROOT = Path(__file__).resolve().parents[2]


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
    tmp_path: Path,
) -> None:
    """Readiness remains usable after closure while scientific execution stays blocked."""

    archived = {"identity_inputs": {"code": {str(pipeline.NOTEBOOK): {"fixture": "synthetic"}}}}
    bundle = tmp_path / pipeline.PROPOSAL_BUNDLE
    bundle.mkdir(parents=True)
    (bundle / "run_summary.json").write_text(json.dumps({"fixture": "synthetic"}))
    monkeypatch.setattr(pipeline, "load_archived_proposal", lambda root: archived)
    monkeypatch.setattr(pipeline, "require_authorization", lambda root: {"fixture": "synthetic"})
    monkeypatch.setattr(pipeline, "code_fingerprints", lambda root: {"fixture": "synthetic"})

    def changed(root: Path) -> dict[str, Any]:
        raise ValueError("Frozen scientific contract changed")

    monkeypatch.setattr(pipeline, "load_proposal", changed)
    result = pipeline.readiness(tmp_path)
    assert result["status"] == "human_authorization_recorded"
    assert result["live_frozen_dependencies"] == "changed_after_freeze"
    assert result["live_dependency_error"] == "Frozen scientific contract changed"
    assert result["scientific_execution_allowed"] is False
    assert result["new_fits"] == 0
    assert result["reserved_results_read"] is False


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


@pytest.mark.parametrize(
    "name",
    [
        "fit_model",
        "_fit",
        "train",
        "_choose_calibration",
        "_select_threshold_from_grid",
        "_select_configuration_from_hyperparameter_role",
        "freeze_proposal",
    ],
)
def test_evaluation_call_guard_denies_fitting_and_selection_aliases(name: str) -> None:
    from sat_dengue.datasets.evaluation_legacy import no_adjustment

    namespace: dict[str, Any] = {}
    exec("def " + name + "():\n    return 'forbidden'", namespace)
    alias = namespace[name]
    with pytest.raises(AssertionError, match="Forbidden"), no_adjustment():
        alias()


@pytest.mark.parametrize(
    "key", ["threshold", "calibration", "utility", "search", "year", "champion"]
)
def test_evaluation_rejects_scientific_runtime_overrides(key: str) -> None:
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.final_evaluation.workflow import resolve_synthetic_configuration

    with pytest.raises(ValueError, match="Only operational"):
        resolve_synthetic_configuration(
            ConfigurationInputsDataset().load(),
            {"profile": "evaluation_synthetic", "tracking": "disabled", key: 2025},
        )


@pytest.mark.parametrize("entrypoint", ["run_final", "execute_bundle"])
def test_consumed_real_evaluation_routes_refuse_new_scientific_execution(entrypoint: str) -> None:
    with pytest.raises(PermissionError, match="consumed"):
        if entrypoint == "run_final":
            pipeline.run_final(ROOT)
        else:
            pipeline.execute_bundle(ROOT, {}, {}, {})
