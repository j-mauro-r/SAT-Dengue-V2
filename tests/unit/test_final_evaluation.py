"""Critical final-route regressions using synthetic inputs only; no reserved reads."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

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
from sat_dengue.datasets.legacy_evaluation.model_assessment.policy import proposed_calendar
from sat_dengue.model_training.references import persistence_reference
from sat_dengue.training_preparation.features import DERIVED_COLUMNS

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
    from sat_dengue.model_training.candidate_families import ADAPTERS

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


@pytest.fixture
def frozen_graph_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """A complete deterministic in-memory fixture, never evidence of real-data parity."""
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.final_evaluation.workflow import (
        generate_synthetic_sources,
        resolve_synthetic_configuration,
    )

    resolved = resolve_synthetic_configuration(
        ConfigurationInputsDataset().load(),
        {"profile": "evaluation_synthetic", "tracking": "disabled"},
    )
    return generate_synthetic_sources(resolved), resolved


def test_evaluation_synthetic_graph_is_source_free_atomic_and_repeatable(
    repo_tmp_path: Path,
) -> None:
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.datasets.evaluation import EvaluationBundleDataset
    from sat_dengue.datasets.stage2 import PublishedConfigurationDataset
    from sat_dengue.pipeline_registry import register_pipelines

    graph = register_pipelines()["evaluation_synthetic"]
    assert graph.inputs() == {"configuration_inputs", "parameters"}
    completed = []
    for repeat in ("first", "second"):
        output = EvaluationBundleDataset(str(repo_tmp_path / repeat / "output"))
        catalog = DataCatalog(
            {
                "configuration_inputs": MemoryDataset(ConfigurationInputsDataset().load()),
                "parameters": MemoryDataset(
                    {"profile": "evaluation_synthetic", "tracking": "disabled"}
                ),
                "resolved_configuration": PublishedConfigurationDataset(
                    str(repo_tmp_path / repeat / "configuration")
                ),
                "evaluation_bundle": output,
            }
        )
        SequentialRunner().run(graph, catalog)
        bundle = ROOT / output.load()["path"]
        audit = json.loads((bundle / "audit.json").read_text())
        assert audit["G5"] == "NOT_APPROVED" and audit["champion"] == "not_selected"
        assert all(
            audit[n] == 0
            for n in (
                "real_model_fits",
                "real_preparer_refits",
                "calibrator_fits",
                "threshold_selection",
                "hyperparameter_search",
            )
        )
        assert len(audit["decisions"]) == 6
        completed.append({f.name: f.read_bytes() for f in bundle.glob("*.csv")})
    assert completed[0] == completed[1]


@pytest.mark.parametrize("defect", ["proposal", "panel", "cohort", "component", "selection"])
def test_evaluation_rejects_foreign_synthetic_inputs_before_inference(
    frozen_graph_fixture: Any,
    defect: str,
) -> None:
    from sat_dengue.final_evaluation.workflow import validate_sources

    sources, resolved = frozen_graph_fixture
    sources = copy.deepcopy(sources)
    if defect == "proposal":
        sources["proposal"]["procedures"][0]["retained_threshold"]["selected_threshold"] = 0.9
    elif defect == "panel":
        sources["panel"].loc[0, "rain_mm_month_sum"] = 99999
    elif defect == "cohort":
        sources["panel"] = sources["panel"].iloc[:-1]
    elif defect == "component":
        sources["components"]["xgboost_t1"] = {"model": b"unapproved"}
    else:
        sources["provenance"]["threshold_selection"] = 1
    with pytest.raises(ValueError, match="Foreign/changed"):
        validate_sources(sources, resolved)


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


def test_evaluation_publication_is_atomic_read_only_and_never_overwrites(
    repo_tmp_path: Path,
    frozen_graph_fixture: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kedro.io import DatasetError

    from sat_dengue.datasets.evaluation import (
        EvaluationBundleDataset,
        FrozenEvaluationSourcesDataset,
        assemble_payloads,
    )
    from sat_dengue.datasets.legacy_preparation import persistence
    from sat_dengue.final_evaluation import workflow

    sources, resolved = frozen_graph_fixture
    cohort_data = workflow.construct_cohorts(sources, resolved)
    raw = workflow.replay_raw_probabilities(sources, cohort_data, resolved)
    calibrated = workflow.apply_calibration(raw, sources)
    alerts = workflow.emit_alerts(raw, calibrated, sources, cohort_data)
    metrics = workflow.compute_final_metrics(alerts, cohort_data, sources, resolved)
    result = workflow.apply_decision_policy(metrics, resolved, sources)
    payload = assemble_payloads(result, {}, sources, resolved)
    output = EvaluationBundleDataset(str(repo_tmp_path / "output"))
    with pytest.raises(DatasetError, match="explicit"):
        output.load()
    with pytest.raises(DatasetError, match="read-only"):
        FrozenEvaluationSourcesDataset().save({})
    rename = persistence.os.rename

    def interrupt(*args: Any, **kwargs: Any) -> None:
        raise OSError("publication interrupted")

    monkeypatch.setattr(persistence.os, "rename", interrupt)
    with pytest.raises(DatasetError, match="interrupted"):
        output.save(payload)
    assert not list((repo_tmp_path / "output").iterdir())
    monkeypatch.setattr(persistence.os, "rename", rename)
    output.save(payload)
    bundle = ROOT / output.load()["path"]
    before = (bundle / "manifest.json").read_bytes()
    with pytest.raises(DatasetError, match="exists"):
        output.save(payload)
    assert (bundle / "manifest.json").read_bytes() == before
    path = bundle / "predictions.csv"
    path.chmod(0o644)
    path.write_bytes(b"corrupt")
    with pytest.raises(DatasetError, match="changed"):
        output.load()


def test_evaluation_rejects_missing_predictions_before_alerting(frozen_graph_fixture: Any) -> None:
    from sat_dengue.final_evaluation import workflow

    sources, resolved = frozen_graph_fixture
    cohort = workflow.construct_cohorts(sources, resolved)
    raw = workflow.replay_raw_probabilities(sources, cohort, resolved)
    raw["xgboost_t1"].iloc[0] = pd.NA
    with pytest.raises(ValueError, match="coverage"):
        workflow.apply_calibration(raw, sources)


@pytest.mark.parametrize(
    "authority", ["champion_decision_policy_v1", "probability_calibration_thresholds_contract_v1"]
)
def test_evaluation_rejects_semantic_snapshot_override_even_with_recomputed_hash(
    frozen_graph_fixture: Any,
    authority: str,
) -> None:
    import hashlib

    from sat_dengue.configuration import canonical_bytes
    from sat_dengue.final_evaluation.workflow import evaluation_contract

    _, resolved = frozen_graph_fixture
    broken = copy.deepcopy(resolved)
    document = broken["authorities"][authority]["document"]
    if authority == "champion_decision_policy_v1":
        document["utility"]["max_false_alarm_increase_pp"] = 50.0
    else:
        document["window_role_calendar"]["2024-06_t2"]["component_available_by_origin"] = "2025-01"
    body = {k: v for k, v in broken.items() if k != "configuration_sha256"}
    broken["configuration_sha256"] = hashlib.sha256(canonical_bytes(body)).hexdigest()
    with pytest.raises(ValueError, match="Scientific values"):
        evaluation_contract(broken, "synthetic")


@pytest.mark.parametrize("defect", ["audit_decision", "comparison_decision", "metric_value"])
def test_evaluation_rejects_decision_metric_policy_inconsistency(
    frozen_graph_fixture: Any,
    defect: str,
) -> None:
    from sat_dengue.datasets.evaluation import assemble_payloads
    from sat_dengue.final_evaluation import workflow

    sources, resolved = frozen_graph_fixture
    cohort = workflow.construct_cohorts(sources, resolved)
    raw = workflow.replay_raw_probabilities(sources, cohort, resolved)
    alerts = workflow.emit_alerts(raw, workflow.apply_calibration(raw, sources), sources, cohort)
    result = workflow.apply_decision_policy(
        workflow.compute_final_metrics(alerts, cohort, sources, resolved), resolved, sources
    )
    if defect == "audit_decision":
        result["decisions"][0]["result"] = "forged"
    elif defect == "comparison_decision":
        frame = result["tables"]["comparison.csv"]
        frame.loc[frame.candidate.eq("xgboost"), "result"] = "forged"
    else:
        frame = result["tables"]["metrics.csv"]
        frame.loc[
            frame.scope.eq("annual")
            & frame.candidate.eq("xgboost")
            & frame.metric.eq("average_precision"),
            "value",
        ] = 0.12345
    with pytest.raises(ValueError, match="inconsistency"):
        assemble_payloads(result, {}, sources, resolved)
