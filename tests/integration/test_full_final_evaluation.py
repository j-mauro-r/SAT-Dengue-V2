"""Critical final-route regressions using synthetic inputs only; no reserved reads."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from evaluation_test_fixtures import frozen_graph_fixture as frozen_graph_fixture
from evaluation_test_fixtures import synthetic as synthetic

from sat_dengue.datasets.legacy_evaluation.final_evaluation import pipeline

ROOT = Path(__file__).resolve().parents[2]


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
