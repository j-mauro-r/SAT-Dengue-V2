"""Real Kedro catalog materialization and metadata-only EXP01 preflight."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from sat_dengue.datasets.exp01 import Exp01BundleDataset
from sat_dengue.experiments.exp01_preflight import OUTPUT_ROOT

ROOT = Path(__file__).resolve().parents[2]


def test_real_session_materializes_exp01_bundle_without_creating_output() -> None:
    """Regression: main rejects the absolute filepath emitted by KedroContext."""
    output = ROOT / OUTPUT_ROOT
    before = output.exists()
    bootstrap_project(ROOT)
    session = KedroSession.create(project_path=ROOT, save_on_close=False)
    with session:
        context = session.load_context()
        assert context.config_loader["catalog"]["exp01_bundle"]["filepath"] == OUTPUT_ROOT
        dataset = context.catalog.get("exp01_bundle")
        assert isinstance(dataset, Exp01BundleDataset)
        assert dataset._describe()["filepath"] == OUTPUT_ROOT
    assert output.exists() == before


def test_real_context_preflight_is_structural_and_creates_no_output(
    monkeypatch: pytest.MonkeyPatch,
    repo_tmp_path: Path,
) -> None:
    import builtins

    from sat_dengue.datasets import exp01 as datasets
    from sat_dengue.experiments import exp01
    from sat_dengue.experiments import exp01_preflight as checks
    from sat_dengue.tracking.local import LocalTracking

    # Generated source metadata keeps CI independent of local private inputs.
    # Catalog, context, dataset construction and node execution remain real.
    descriptor = {"schema": "exp01-source-descriptor-v1", "files": {"generated": {"bytes": 1}}}
    monkeypatch.setattr(checks, "source_metadata", lambda: descriptor)
    monkeypatch.setattr(datasets, "source_metadata", lambda: descriptor)
    monkeypatch.setattr(checks, "runtime_versions", lambda: {"generated_runtime": "1.0"})
    original_open = builtins.open
    original_path_open = Path.open

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("Fit, calibration or MLflow writer reached")

    def guarded_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(file, (str, Path)) and Path(file).resolve().is_relative_to(ROOT / "data"):
            raise AssertionError("Private-content read reached")
        return original_open(file, *args, **kwargs)

    def guarded_path_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.resolve().is_relative_to(ROOT / "data"):
            raise AssertionError("Private-content read reached")
        return original_path_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(exp01, "native_fit", forbidden)
    monkeypatch.setattr(exp01, "native_calibration", forbidden)
    monkeypatch.setattr(LocalTracking, "__init__", forbidden)
    monkeypatch.delenv("SAT_DENGUE_EXP01_APPROVAL", raising=False)
    monkeypatch.setenv(
        "SAT_DENGUE_TRACKING_ROOT", str((repo_tmp_path / "tracking").relative_to(ROOT))
    )
    output_existed = (ROOT / OUTPUT_ROOT).exists()
    bootstrap_project(ROOT)
    session = KedroSession.create(
        project_path=ROOT,
        save_on_close=False,
        runtime_params={
            "profile": "exp01_preflight",
            "tracking": "enabled",
            "experiment_id": "EXP01",
        },
    )
    with session:
        result = session.run(pipeline_names=["exp01_preflight"])["exp01_preflight_receipt"].load()
    assert result["status"] == "structural_pass"
    assert result["execution_ready"] is False
    assert result["real_model_fits"] == result["calibrator_fits"] == result["mlflow_writes"] == 0
    assert result["real_execution_started"] is False
    assert (ROOT / OUTPUT_ROOT).exists() == output_existed
