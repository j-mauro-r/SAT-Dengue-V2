"""Public-only EXP01 wiring, no-fit preflight and fail-closed execution boundaries."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue.configuration import validate_parameters
from sat_dengue.experiments import exp01_preflight as checks
from sat_dengue.experiments.exp01 import digest, load_protocol
from sat_dengue.experiments.exp01_runner import load_authorized_sources
from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS = {"profile": "exp01_preflight", "tracking": "enabled", "experiment_id": "EXP01"}


@pytest.fixture
def descriptor(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    value = {"schema": "exp01-source-descriptor-v1", "files": {"generated_fixture": {"bytes": 1}}}
    monkeypatch.setattr(checks, "source_metadata", lambda: copy.deepcopy(value))
    # Generated graph checks are independent of a host's optional dev packages.
    # Real installed-runtime checks run separately and in the no-fit CLI gate.
    monkeypatch.setattr(checks, "runtime_versions", lambda: {"generated_runtime": "1.0"})
    return value


def test_registered_graph_and_catalog_are_bound() -> None:
    from sat_dengue.config_loader import ValidatedConfigLoader

    graphs = register_pipelines()
    assert {"exp01", "exp01_preflight", "exp01_synthetic"} <= graphs.keys()
    assert [n.name for n in graphs["exp01"].nodes] == [
        "exp01_preflight",
        "exp01_authorize_and_load",
        "exp01_execute_paired",
    ]
    loader = ValidatedConfigLoader("conf", base_env="base", default_run_env="base")
    catalog = DataCatalog.from_config(loader["catalog"])
    assert catalog.get("exp01_sources").__class__.__name__ == "Exp01SourcesDataset"
    assert catalog.get("exp01_bundle").__class__.__name__ == "Exp01BundleDataset"
    assert graphs["exp01"].inputs() == {"parameters", "exp01_sources"}


def test_preflight_graph_performs_no_fits_or_private_content_reads_or_mlflow_writes(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, descriptor: dict[str, Any]
) -> None:
    import builtins

    from sat_dengue.experiments import exp01, exp01_runner
    from sat_dengue.tracking.local import LocalTracking

    root = str((repo_tmp_path / "tracking").relative_to(ROOT))
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", root)
    actual_open = builtins.open
    actual_path_open = Path.open
    private_reads = []

    def guarded_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(file, (str, Path)) and Path(file).resolve().is_relative_to(ROOT / "data"):
            private_reads.append(str(file))
            raise AssertionError("Private content read")
        mode = args[0] if args else kwargs.get("mode", "r")
        assert not any(c in str(mode) for c in "wax+"), "Preflight write"
        return actual_open(file, *args, **kwargs)

    def guarded_path_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.resolve().is_relative_to(ROOT / "data"):
            private_reads.append(str(path))
            raise AssertionError("Private content read")
        mode = args[0] if args else kwargs.get("mode", "r")
        assert not any(c in str(mode) for c in "wax+"), "Preflight write"
        return actual_path_open(path, *args, **kwargs)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Real fitter, calibration or MLflow writer reached")

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(exp01, "native_fit", forbidden)
    monkeypatch.setattr(exp01, "native_calibration", forbidden)
    monkeypatch.setattr(LocalTracking, "__init__", forbidden)
    monkeypatch.setattr(exp01_runner, "prepare_exp01_inputs", forbidden)
    monkeypatch.setattr(exp01_runner, "reserve_execution", forbidden)
    monkeypatch.setattr(exp01_runner, "native_fit", forbidden)
    monkeypatch.setattr(exp01_runner, "native_calibration", forbidden)
    # These deliberately invalid accesses prove both hooks catch canonical paths.
    for private in (Path("data/never-read.csv"), ROOT / "data/never-read.csv"):
        with pytest.raises(AssertionError, match="Private content"):
            private.open()
        with pytest.raises(AssertionError, match="Private content"):
            builtins.open(private)
    for opening in (
        lambda: Path("tmp/never-written").open("w"),
        lambda: builtins.open("tmp/never-written", "w"),
    ):
        with pytest.raises(AssertionError, match="Preflight write"):
            opening()
    private_reads.clear()
    actual_load = DataCatalog.load

    def guarded_catalog_load(self: Any, name: str, *args: Any, **kwargs: Any) -> Any:
        assert name in {"parameters", "exp01_sources", "exp01_preflight_receipt"}, (
            "Private catalog load"
        )
        return actual_load(self, name, *args, **kwargs)

    monkeypatch.setattr(DataCatalog, "load", guarded_catalog_load)
    catalog = DataCatalog(
        {
            "parameters": MemoryDataset(PARAMETERS),
            "exp01_sources": MemoryDataset(descriptor),
            "exp01_preflight_receipt": MemoryDataset(),
        }
    )
    hooks = TrackingHooks()
    hooks.before_pipeline_run({"pipeline_name": "exp01_preflight"}, catalog)
    SequentialRunner().run(register_pipelines()["exp01_preflight"], catalog)
    receipt = catalog.load("exp01_preflight_receipt")
    hooks.after_pipeline_run(catalog)
    assert hooks.tracker is None
    assert receipt["status"] == "structural_pass"
    assert receipt["execution_ready"] is False
    assert receipt["real_model_fits"] == receipt["calibrator_fits"] == receipt["mlflow_writes"] == 0
    assert receipt["real_execution_started"] is False
    assert receipt["protocol_sha256"] == digest(load_protocol())
    assert private_reads == []
    assert not Path(root).exists()


def test_metadata_descriptor_only_stats_generated_files(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = repo_tmp_path / "source.csv"
    source.write_text("generated fixture,not private\n")
    relative = str(source.relative_to(ROOT))
    monkeypatch.setattr(checks, "SOURCE_PATHS", (relative,))
    descriptor = checks.source_metadata()
    assert descriptor["files"] == {relative: {"bytes": source.stat().st_size}}
    source.unlink()
    with pytest.raises(ValueError, match="Missing or empty"):
        checks.source_metadata()


@pytest.mark.parametrize("root", ["", "/tmp/external", "tmp/../outside", "data/tracking"])
def test_invalid_tracking_paths_fail_closed(root: str) -> None:
    with pytest.raises(ValueError):
        checks.storage_preflight(root)


def test_symlink_and_corrupt_database_fail_closed(repo_tmp_path: Path) -> None:
    relative = str(repo_tmp_path.relative_to(ROOT))
    (repo_tmp_path / "artifacts").symlink_to(ROOT)
    with pytest.raises(ValueError, match="symlink"):
        checks.storage_preflight(relative)
    (repo_tmp_path / "artifacts").unlink()
    (repo_tmp_path / "tracking.sqlite").write_text("corrupt database")
    with pytest.raises(Exception, match="database"):
        checks.storage_preflight(relative)


@pytest.mark.parametrize("mutation", ["profile", "tracking", "experiment_id"])
def test_real_parameters_cannot_disable_or_rebind_protections(mutation: str) -> None:
    parameters = {**PARAMETERS, "profile": "exp01"}
    parameters[mutation] = {"profile": "unknown", "tracking": "disabled", "experiment_id": "EXP00"}[
        mutation
    ]
    with pytest.raises(ValueError):
        validate_parameters(parameters)


def test_profile_cannot_be_used_on_another_graph() -> None:
    catalog = DataCatalog({"parameters": MemoryDataset(PARAMETERS)})
    with pytest.raises(ValueError, match="exact pipeline"):
        TrackingHooks().before_pipeline_run({"pipeline_name": "foundation"}, catalog)


def test_authorization_denial_precedes_private_reads_and_mlflow_creation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sat_dengue.experiments import exp01_runner
    from sat_dengue.tracking.local import LocalTracking

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Authorization denial reached scientific side effect")

    for name in ("prepare_exp01_inputs", "native_fit", "native_calibration", "reserve_execution"):
        monkeypatch.setattr(exp01_runner, name, forbidden)
    monkeypatch.setattr(LocalTracking, "__init__", forbidden)
    monkeypatch.delenv("SAT_DENGUE_EXP01_APPROVAL", raising=False)
    with pytest.raises(PermissionError, match="separate human authorization"):
        load_authorized_sources({})


@pytest.mark.parametrize(
    "mutation",
    [
        "protocol_sha256",
        "git_revision",
        "data_version",
        "configuration_sha256",
        "real_execution_authorized",
        "retrospective_availability_acknowledged",
        "comparator_refit_authorized",
        "authority",
        "independent_reviewer",
        "unknown",
        "dirty",
    ],
)
def test_approval_requires_all_boundaries(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    receipt = {
        "protocol_sha256": digest(load_protocol()),
        "git_revision": "a" * 40,
        "data_version": "b" * 64,
        "configuration_sha256": "c" * 64,
        "git_dirty": False,
    }
    approval = {
        "schema": "exp01-execution-approval-v1",
        "experiment_id": "EXP01",
        **{k: v for k, v in receipt.items() if k != "git_dirty"},
        "authority": "Mauricio",
        "independent_reviewer": "FixtureReviewer",
        "real_execution_authorized": True,
        "retrospective_availability_acknowledged": True,
        "comparator_refit_authorized": True,
    }
    monkeypatch.setattr(
        checks, "git_identity", lambda: {"git_revision": "a" * 40, "git_dirty": False}
    )
    if mutation == "independent_reviewer":
        approval[mutation] = "Mauricio"
    elif mutation == "dirty":
        receipt["git_dirty"] = True
    else:
        approval[mutation] = False if isinstance(approval.get(mutation), bool) else "invalid"
    path = repo_tmp_path / "fixture-approval.json"
    path.write_text(json.dumps(approval))
    monkeypatch.setenv("SAT_DENGUE_EXP01_APPROVAL", str(path.relative_to(ROOT)))
    with pytest.raises(PermissionError):
        checks.authorize(receipt)


def test_2025_never_acquires_a_role_and_pairing_cannot_silently_drop_keys() -> None:
    from sat_dengue.experiments.onset import partitions
    from sat_dengue.experiments.onset_evaluation import assert_paired

    cohort = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2024-12"],
            "target_month": ["2025-01"],
            "eligible_at_t": [True],
            "x": [1.0],
        }
    )
    for original in load_protocol()["design"]["windows"]:
        assert all(frame.empty for frame in partitions(cohort, original).values())
        for role in ("train", "calibration", "selection", "evaluation"):
            window = copy.deepcopy(original)
            window[role][1] = "2025-12"
            with pytest.raises(ValueError):
                partitions(cohort, window)
    with pytest.raises(ValueError, match="differ"):
        assert_paired(cohort, cohort.iloc[:0], ["x"])


def test_protocol_and_canonical_hash_are_mandatory(
    monkeypatch: pytest.MonkeyPatch, repo_tmp_path: Path
) -> None:
    import sat_dengue.experiments.exp01 as experiment

    missing = repo_tmp_path / "missing.json"
    monkeypatch.setattr(experiment, "PROTOCOL", missing)
    with pytest.raises(FileNotFoundError):
        experiment.load_protocol()
    missing.write_text(json.dumps({"modified": True}))
    with pytest.raises(ValueError, match="changed"):
        experiment.load_protocol()


def test_new_approval_cannot_bypass_scientific_duplicate_reservation(repo_tmp_path: Path) -> None:
    from sat_dengue.experiments.exp01_runner import reserve_execution

    provenance = {
        "protocol_sha256": "a" * 64,
        "data_version": "b" * 64,
        "approval_sha256": "c" * 64,
    }
    root = str(repo_tmp_path.relative_to(ROOT))
    reserve_execution(provenance, root)
    provenance["approval_sha256"] = "d" * 64
    with pytest.raises(ValueError, match="duplicate or interrupted"):
        reserve_execution(provenance, root)


def test_valid_generated_approval_is_checked_without_executing_anything(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt = {
        "protocol_sha256": digest(load_protocol()),
        "git_revision": "a" * 40,
        "data_version": "b" * 64,
        "configuration_sha256": "c" * 64,
        "code_sha256": "d" * 64,
        "environment_sha256": "e" * 64,
        "git_dirty": False,
    }
    approval = {
        "schema": "exp01-execution-approval-v1",
        "experiment_id": "EXP01",
        **{
            k: receipt[k]
            for k in ("protocol_sha256", "git_revision", "data_version", "configuration_sha256")
        },
        "authority": "Mauricio",
        "independent_reviewer": "GeneratedFixtureReviewer",
        "real_execution_authorized": True,
        "retrospective_availability_acknowledged": True,
        "comparator_refit_authorized": True,
    }
    path = repo_tmp_path / "generated-approval.json"
    path.write_text(json.dumps(approval))
    monkeypatch.setenv("SAT_DENGUE_EXP01_APPROVAL", str(path.relative_to(ROOT)))
    monkeypatch.setattr(
        checks, "git_identity", lambda: {"git_revision": "a" * 40, "git_dirty": False}
    )
    monkeypatch.setattr(
        checks,
        "execution_metadata",
        lambda: {"code_sha256": "d" * 64, "environment_sha256": "e" * 64},
    )
    assert checks.authorize(receipt) == approval
    assert sorted(p.name for p in repo_tmp_path.iterdir()) == ["generated-approval.json"]


def test_dependency_drift_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    actual = checks.importlib.metadata.version
    monkeypatch.setattr(
        checks.importlib.metadata,
        "version",
        lambda name: "0.0.0" if name == "numpy" else actual(name),
    )
    with pytest.raises(ValueError, match="frozen pin: numpy"):
        checks.runtime_versions()


def test_horizon_boundary_embargo_is_explicit_in_coverage() -> None:
    from sat_dengue.experiments.onset import partitions

    window = load_protocol()["design"]["windows"][0]
    for horizon, origin, expected in ((1, "2018-12", 0), (2, "2018-11", 1)):
        cohort = pd.DataFrame(
            {
                "municipality_code": ["50001"],
                "year_month": [origin],
                "target_month": [str(pd.Period(origin, freq="M") + horizon)],
                "eligible_at_t": [True],
            }
        )
        role = partitions(cohort, window)["calibration"]
        assert role.attrs["coverage"]["target_role_rows"] == 1
        assert role.attrs["coverage"]["embargo_excluded_rows"] == expected
        assert len(role) == 1 - expected
