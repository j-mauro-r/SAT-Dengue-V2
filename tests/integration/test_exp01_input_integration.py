"""Generated admission-to-publication connection probe; never invoke real EXP01."""

from __future__ import annotations

import builtins
import copy
from pathlib import Path
from typing import Any

import pytest
from exp01_inputs_fixture import ROOT, generated_panel, write_sources
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.pipeline import node, pipeline
from kedro.runner import SequentialRunner

from sat_dengue.datasets import exp01 as datasets
from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.experiments import exp01
from sat_dengue.experiments import exp01_preflight as checks
from sat_dengue.experiments import exp01_runner as runner
from sat_dengue.tracking.exp01 import Exp01Tracking, verified_result


def test_generated_manifest_to_real_catalog_publication_and_tracking(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = write_sources(repo_tmp_path / "sources", generated_panel())
    manifest = str(config.resolve(config.manifest_path).relative_to(ROOT))
    source_paths = tuple(
        str(path.relative_to(ROOT))
        for path in (repo_tmp_path / "sources/data").rglob("*")
        if path.is_file()
    )
    monkeypatch.setattr(checks, "SOURCE_PATHS", source_paths)
    monkeypatch.setattr(runner, "NATIVE_MANIFEST", manifest)
    monkeypatch.setattr(runner, "NATIVE_IDENTITIES", {manifest: fingerprint(ROOT / manifest)})
    monkeypatch.setattr(runner, "PreparationConfig", lambda root: config)
    original_protocol = exp01.load_protocol()
    fixture_protocol = copy.deepcopy(original_protocol)
    fixture_protocol["population"]["municipalities"] = 2
    monkeypatch.setattr(runner, "load_protocol", lambda: fixture_protocol)
    tracking = str((repo_tmp_path / "tracking").relative_to(ROOT))
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", tracking)
    monkeypatch.delenv("SAT_DENGUE_EXP01_APPROVAL", raising=False)
    events: list[str] = []
    receipt: dict[str, Any] = {
        "sources": checks.source_metadata(),
        "tracking": {"root": tracking},
        "protocol_sha256": exp01.digest(original_protocol),
        "git_revision": "a" * 40,
        "data_version": fingerprint(ROOT / manifest)["sha256"],
        "configuration_sha256": "b" * 64,
        "code": {"generated_fixture.py": "c" * 64},
        "runtime": {"fixture": "controlled_substitutes"},
    }
    receipt["code_sha256"] = exp01.digest(receipt["code"])
    receipt["environment_sha256"] = exp01.digest(receipt["runtime"])
    original_open, original_path_open = builtins.open, Path.open

    def guard(path: Any) -> None:
        if isinstance(path, (str, Path)):
            resolved = Path(path).resolve()
            if resolved.is_relative_to(ROOT / "data"):
                raise AssertionError("Private content is forbidden")
            if resolved.is_relative_to(config.root / "data"):
                assert "authorized_fixture" in events

    def guarded_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        guard(file)
        return original_open(file, *args, **kwargs)

    def guarded_path_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        guard(path)
        return original_path_open(path, *args, **kwargs)

    def authorize_fixture(value: dict[str, Any]) -> dict[str, str]:
        assert value == receipt
        events.append("authorized_fixture")
        return {"fixture": "in-memory test boundary; not an execution approval"}

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Real adjustment/reservation route reached")

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    # Prove the real denial boundary is upstream of any generated/private content read.
    with pytest.raises(PermissionError):
        runner.load_authorized_sources(receipt)
    assert events == [] and not Path(tracking).exists()
    monkeypatch.setattr(runner, "authorize", authorize_fixture)
    monkeypatch.setattr(runner, "reserve_execution", forbidden)
    monkeypatch.setattr(runner, "native_fit", forbidden)
    monkeypatch.setattr(runner, "native_calibration", forbidden)
    monkeypatch.setattr(exp01, "native_fit", forbidden)
    monkeypatch.setattr(exp01, "native_calibration", forbidden)
    calls: list[tuple[str, Any]] = []
    calibrations: list[int] = []
    trackers: list[Exp01Tracking] = []

    def fit(family: Any, X: Any, y: Any, parameters: Any, seed: Any) -> Any:
        assert X.index.equals(y.index)
        calls.append((family, X.copy(deep=True)))
        return exp01.synthetic_fit(family, X, y, parameters, seed)

    def calibrate(scores: Any, truth: Any, seed: Any) -> Any:
        assert len(scores) == len(truth)
        calibrations.append(len(truth))
        return lambda values: values

    def generated_receipt(descriptor: dict[str, Any]) -> dict[str, Any]:
        assert descriptor == receipt["sources"]
        return receipt

    def generated_computation(sources: dict[str, Any]) -> dict[str, Any]:
        assert events == ["authorized_fixture"]
        assert sources["panel"].year_month.max() == "2024-12"
        assert "y_t1" not in sources["panel"] and "zona_canal_t" not in sources["panel"]
        provenance = {k: v for k, v in receipt.items() if k not in ("sources", "tracking")}
        provenance["data_sha256"] = exp01.digest(sources["input_fingerprints"])
        tracker = Exp01Tracking(
            "exp01_synthetic",
            "generated-raw-admission",
            receipt["tracking"]["root"],
            experiment_id="EXP01",
        )
        trackers.append(tracker)
        tracker.initialize_paired(provenance, synthetic=True)
        result = exp01.execute_paired(
            sources["panel"],
            sources["contract"],
            original_protocol["design"],
            fit=fit,
            calibrate=calibrate,
            synthetic=True,
        )
        return {"result": result, "provenance": provenance, "tracker": tracker}

    bootstrap_project(ROOT)
    session = KedroSession.create(project_path=ROOT, save_on_close=False)
    with session:
        catalog = session.load_context().catalog
        bundle = catalog.get("exp01_bundle")
        assert isinstance(bundle, datasets.Exp01BundleDataset)
        assert bundle._describe()["filepath"] == checks.OUTPUT_ROOT
        # Construction exercises Kedro's canonical absolute path. Only test writes are redirected.
        bundle._root = (repo_tmp_path / "publication").relative_to(ROOT)
        graph = pipeline(
            [
                node(generated_receipt, "exp01_sources", "fixture_receipt"),
                node(runner.load_authorized_sources, "fixture_receipt", "fixture_sources"),
                node(generated_computation, "fixture_sources", "exp01_bundle"),
            ]
        )
        SequentialRunner().run(graph, catalog)
        publication = catalog.load("exp01_bundle")
    assert len(calls) == len(calibrations) == 36
    for left, right in zip(calls[::2], calls[1::2], strict=True):
        assert left[0] == right[0] and left[1].equals(right[1])
    result = verified_result(publication)["result"]
    assert (
        result["real_model_fits"]
        == result["real_preparer_refits"]
        == result["calibrator_fits"]
        == 0
    )
    assert result["G5"] == "NOT_APPROVED" and result["champion"] == "not_selected"
    tracker = trackers[0]
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 37 and all(run.info.status == "FINISHED" for run in runs)
    assert (
        len([run for run in runs if run.data.tags.get("mlflow.parentRunId") == tracker.parent])
        == 36
    )
    assert all(run.data.params["kind"] == "synthetic" for run in runs)
    assert not list(repo_tmp_path.rglob("*.reservation"))
