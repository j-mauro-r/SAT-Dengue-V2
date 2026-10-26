"""EXP01 local tracking records structural synthetic probes only."""

from __future__ import annotations

from pathlib import Path

import pytest
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.tracking.local import LocalTracking

ROOT = Path(__file__).resolve().parents[2]


def test_exp01_pipeline_tracks_zero_fit_parent_children_and_duplicate(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = str((repo_tmp_path / "exp01-tracking").relative_to(ROOT))
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", store)
    catalog = DataCatalog(
        {
            "parameters": MemoryDataset(
                {"profile": "exp01_synthetic", "tracking": "enabled", "experiment_id": "EXP01"}
            ),
            "exp01_synthetic_receipt": MemoryDataset(),
        }
    )
    hooks = TrackingHooks()
    hooks.before_pipeline_run(
        {"pipeline_name": "exp01_synthetic", "session_id": "synthetic-exp01"}, catalog
    )
    SequentialRunner().run(register_pipelines()["exp01_synthetic"], catalog)
    receipt = catalog.load("exp01_synthetic_receipt")
    first_id = hooks.tracker.parent
    hooks.after_pipeline_run(catalog)

    tracker = hooks.tracker
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 37
    parent = tracker.client.get_run(first_id)
    assert parent.info.status == "FINISHED"
    assert parent.data.tags["experiment_id"] == "EXP01"
    assert parent.data.tags["hypothesis_id"] == "EXP01-H1"
    assert parent.data.tags["pipeline"] == "exp01_synthetic"
    assert parent.data.params["protocol_version"] == "1.0.0"
    assert parent.data.params["evidence_type"] == "synthetic_interface_probe"
    assert parent.data.params["data_sha256"]
    assert parent.data.params["git_revision"]
    assert parent.data.params["manifest_sha256"]
    assert all(
        parent.data.metrics[name] == 0
        for name in (
            "real_model_fits",
            "real_preparer_refits",
            "calibrator_fits",
            "hyperparameter_search",
            "threshold_selection",
        )
    )
    children = [run for run in runs if run.data.tags.get("mlflow.parentRunId") == first_id]
    assert len(children) == 36
    assert (
        len(
            {
                (
                    run.data.params["objective"],
                    run.data.params["family"],
                    run.data.params["horizon"],
                    run.data.params["window"],
                )
                for run in children
            }
        )
        == 36
    )
    assert all(not child.data.metrics for child in children)
    assert all(
        child.data.params["evidence_type"] == "synthetic_interface_probe" for child in children
    )
    assert "private" not in " ".join(parent.data.params.values()).lower()

    retry = LocalTracking("exp01_synthetic", "synthetic-exp01-retry", store, experiment_id="EXP01")
    assert retry.finish_exp01_synthetic(receipt) == first_id
    retry_parent = retry.client.get_run(retry.parent)
    assert retry_parent.info.status == "KILLED"
    assert retry_parent.data.tags["status"] == "duplicate_verified"
    assert retry_parent.data.tags["duplicate_of"] == first_id
