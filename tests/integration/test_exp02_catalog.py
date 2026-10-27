"""Real Kedro catalog and generated metadata-only preflight; no operational run."""

import builtins
from pathlib import Path

import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset

from sat_dengue.datasets.exp02 import Exp02BundleDataset, publication_root
from sat_dengue.experiments import exp02_preflight as checks
from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


def test_fixed_catalog_real_context_and_graph():
    bootstrap_project(ROOT)
    session = KedroSession.create(project_path=ROOT, save_on_close=False)
    with session:
        dataset = session.load_context().catalog.get("exp02_bundle")
        assert isinstance(dataset, Exp02BundleDataset)
        assert dataset._describe()["filepath"] == checks.OUTPUT_ROOT
    graph = register_pipelines()["exp02"]
    assert graph.inputs() == {"parameters", "exp02_sources"}
    assert [n.name for n in graph.nodes] == [
        "exp02_preflight",
        "exp02_authorize_and_load",
        "exp02_construct_labels",
        "exp02_compare_stability",
        "exp02_predictive_comparison",
        "exp02_publish",
    ]
    assert publication_root(str(ROOT / checks.OUTPUT_ROOT)) == Path(checks.OUTPUT_ROOT)
    for path in (
        "tmp/different",
        str(ROOT / "tmp/different"),
        "tmp/../tmp/kedro-migration/exp02-runs",
    ):
        with pytest.raises(ValueError):
            publication_root(path)


def test_kedro_preflight_with_generated_metadata_performs_no_prohibited_io(
    exp02_receipt, monkeypatch
):
    from sat_dengue.datasets import exp02 as datasets
    from sat_dengue.experiments import exp02_runner as runner
    from sat_dengue.tracking.local import LocalTracking

    original_open, original_path_open = builtins.open, Path.open

    def protected(file):
        return isinstance(file, (str, Path)) and Path(file).resolve().is_relative_to(ROOT / "data")

    def guarded_open(file, *args, **kwargs):
        assert not protected(file), "Private content read"
        return original_open(file, *args, **kwargs)

    def guarded_path_open(path, *args, **kwargs):
        assert not protected(path), "Private content read"
        return original_path_open(path, *args, **kwargs)

    def forbidden(*args, **kwargs):
        raise AssertionError(
            "Real model, calibration, private loader, reservation or MLflow reached"
        )

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    for name in ("native_fit", "native_calibration", "prepare_exp01_inputs", "reserve_execution"):
        monkeypatch.setattr(runner, name, forbidden)
    monkeypatch.setattr(LocalTracking, "__init__", forbidden)
    monkeypatch.setattr(datasets, "source_metadata", checks.source_metadata)
    params = {"profile": "exp02_preflight", "tracking": "enabled", "experiment_id": "EXP02"}
    bootstrap_project(ROOT)
    session = KedroSession.create(project_path=ROOT, save_on_close=False, runtime_params=params)
    with session:
        receipt = session.run(pipeline_names=["exp02_preflight"])["exp02_preflight_receipt"].load()
    assert receipt["status"] == "structural_pass" and receipt["execution_ready"] is False
    assert receipt["real_model_fits"] == receipt["calibrator_fits"] == receipt["mlflow_writes"] == 0
    assert not receipt["real_execution_started"]
    assert not Path(receipt["tracking_root"]).exists()


def test_dirty_preflight_rejected(exp02_receipt, monkeypatch):
    monkeypatch.setattr(
        checks, "git_identity", lambda: {"git_revision": "a" * 40, "git_dirty": True}
    )
    with pytest.raises(ValueError, match="clean committed"):
        checks.preflight(
            {"profile": "exp02_preflight", "tracking": "enabled", "experiment_id": "EXP02"},
            exp02_receipt["sources"],
        )


def test_profiles_cannot_bypass_hooks_or_enable_synthetic_tracking():
    from sat_dengue.configuration import validate_parameters

    params = {"profile": "exp02", "tracking": "enabled", "experiment_id": "EXP02"}
    with pytest.raises(ValueError, match="exact pipeline"):
        TrackingHooks().before_pipeline_run(
            {"pipeline_name": "foundation"}, DataCatalog({"parameters": MemoryDataset(params)})
        )
    for override in (
        {"tracking": "disabled"},
        {"experiment_id": "EXP01"},
        {"profile": "exp02_synthetic"},
    ):
        with pytest.raises(ValueError):
            validate_parameters({**params, **override})


def test_generated_pipeline_preserves_full_grid_without_real_fits(exp02_generated_result):
    result = exp02_generated_result
    assert result["evidence_type"] == "synthetic_interface_probe"
    assert result["predictive"]["real_model_fits"] == result["predictive"]["calibrator_fits"] == 0
    assert len(result["stability"]["children"]) == 9
    assert len(result["predictive"]["children"]) == 54
    assert result["G5"] == "NOT_APPROVED" and result["champion"] == "not_selected"
