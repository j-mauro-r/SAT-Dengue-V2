"""Observe real local MLflow lifecycle and privacy against complete synthetic Kedro runs."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from kedro.framework.hooks.manager import _create_hook_manager
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue.datasets import ConfigurationInputsDataset
from sat_dengue.datasets.evaluation import EvaluationBundleDataset
from sat_dengue.datasets.stage2 import PublishedConfigurationDataset
from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.tracking.lineage import verified_lineage
from sat_dengue.tracking.local import LocalTracking, allowed_parameters

ROOT = Path(__file__).resolve().parents[2]


def execute(
    folder: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    enabled: bool = True,
    profile: str = "standard",
    failure: str | None = None,
    store: Path | None = None,
) -> tuple[Any, dict[str, Any]]:
    output = EvaluationBundleDataset(str(folder / "evaluation"))
    store = store or folder / "tracking"
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", str(store.relative_to(ROOT)))
    monkeypatch.setenv("SAT_DENGUE_TRACKING_PROFILE", profile)
    graph = register_pipelines()["evaluation_synthetic"]
    catalog = DataCatalog(
        {
            "configuration_inputs": MemoryDataset(ConfigurationInputsDataset().load()),
            "parameters": MemoryDataset(
                {
                    "profile": "evaluation_synthetic",
                    "tracking": "enabled" if enabled else "disabled",
                }
            ),
            "resolved_configuration": PublishedConfigurationDataset(str(folder / "configuration")),
            "evaluation_bundle": output,
        }
    )
    hooks = TrackingHooks()
    manager = _create_hook_manager()
    manager.register(hooks)
    hooks.before_pipeline_run(
        {"pipeline_name": "evaluation_synthetic", "session_id": uuid4().hex}, catalog
    )
    original = output.save
    if failure:

        def fail(data: Any) -> None:
            assert data["payloads"]["comparison.csv"]  # computation completed
            if failure == "after_publication":
                original(data)
                (ROOT / output.load()["path"] / "comparison.csv").chmod(0o644)
                (ROOT / output.load()["path"] / "comparison.csv").write_text("tampered")
                return
            raise RuntimeError("injected-before-publication")

        monkeypatch.setattr(output, "save", fail)
    try:
        SequentialRunner().run(graph, catalog, hook_manager=manager)
        hooks.after_pipeline_run(catalog)
    except BaseException as error:
        hooks.on_pipeline_error(error)
        if failure:
            return hooks.tracker, {}
        raise
    return hooks.tracker, output.load()


def test_isolated_comparable_parent_children_and_scientific_equality(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    records = []
    comparable = []
    for label, profile, enabled in [
        ("one", "standard", True),
        ("two", "diagnostic", True),
        ("off", "standard", False),
    ]:
        tracker, publication = execute(
            repo_tmp_path / label, monkeypatch, enabled=enabled, profile=profile
        )
        folder = ROOT / publication["path"]
        records.append({p.name: p.read_bytes() for p in folder.glob("*.csv")})
        params, children = verified_lineage(publication)
        assert len(children) == 6
        if not enabled:
            assert tracker is None and not (repo_tmp_path / label / "tracking").exists()
            continue
        runs = tracker.client.search_runs([tracker.experiment])
        assert len(runs) == 7 and all(r.info.status == "FINISHED" for r in runs)
        parent = tracker.client.get_run(tracker.parent)
        assert parent.data.params["observability_profile"] == profile
        comparable.append(
            (
                {
                    k: v
                    for k, v in parent.data.params.items()
                    if k.startswith("contract_")
                    or k in {"input_sha256", "code_sha256", "metric_definition_sha256", "seed"}
                },
                {
                    (r.data.params["family"], r.data.params["horizon"]): r.data.metrics
                    for r in runs
                    if r.info.run_id != tracker.parent
                },
            )
        )
        with sqlite3.connect(repo_tmp_path / label / "tracking/tracking.sqlite") as connection:
            dump = "\n".join(connection.iterdump())
        assert str(ROOT) not in dump and "/Users/" not in dump
        assert parent.data.params["kind"] == "synthetic"
        assert parent.data.params["seed"] == "42"
        assert (
            parent.data.params["contract_champion_decision_policy_v1"]
            == params["contract_champion_decision_policy_v1"]
        )
        assert all(
            r.data.tags["mlflow.parentRunId"] == tracker.parent
            for r in runs
            if r.info.run_id != tracker.parent
        )
        serialized = json.dumps(
            [
                {
                    "params": r.data.params,
                    "tags": r.data.tags,
                    "metrics": r.data.metrics,
                    "uri": r.info.artifact_uri,
                }
                for r in runs
            ]
        )
        assert str(ROOT) not in serialized and "/Users/" not in serialized
        assert (
            "municipality_code" not in serialized and "dengue_notifications_count" not in serialized
        )
        assert set(p.name for p in (repo_tmp_path / label / "tracking" / "receipts").iterdir()) == {
            tracker.parent + ".json"
        }
        assert (
            subprocess.run(
                [
                    "git",
                    "check-ignore",
                    "-q",
                    str(repo_tmp_path / label / "tracking/tracking.sqlite"),
                ]
            ).returncode
            == 0
        )
    assert records[0] == records[1] == records[2]
    assert comparable[0] == comparable[1]


@pytest.mark.parametrize("failure", ["before_publication", "after_publication"])
def test_failure_never_finishes_a_run(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    tracker, publication = execute(repo_tmp_path / failure, monkeypatch, failure=failure)
    assert not publication
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 1 and runs[0].info.status == "FAILED"
    if failure == "before_publication":
        assert not list((repo_tmp_path / failure / "evaluation").glob("*/manifest.json"))


def test_error_before_compute_and_abort_are_explicit(repo_tmp_path: Path) -> None:
    for aborted in (False, True):
        tracker = LocalTracking(
            "evaluation_synthetic",
            uuid4().hex,
            str((repo_tmp_path / str(aborted)).relative_to(ROOT)),
        )
        tracker.fail(aborted=aborted)
        tracker.fail()  # terminal actions idempotent
        assert tracker.client.get_run(tracker.parent).info.status == (
            "KILLED" if aborted else "FAILED"
        )


def test_verified_duplicate_does_not_create_second_success(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, publication = execute(repo_tmp_path / "native", monkeypatch)
    store = str((repo_tmp_path / "native/tracking").relative_to(ROOT))
    second = LocalTracking("evaluation_synthetic", "retry", store)
    assert second.finish(publication) == first.parent
    assert second.client.get_run(second.parent).info.status == "KILLED"
    assert (
        len(
            second.client.search_runs(
                [second.experiment], filter_string="attributes.status = 'FINISHED'"
            )
        )
        == 7
    )
    assert len(list((repo_tmp_path / "native/evaluation").glob("*/manifest.json"))) == 1


@pytest.mark.parametrize(
    "values",
    [
        {"raw_rows": [1]},
        {"profile": "/Users/private/data"},
        {"native_pointer": "../../data/raw/private.csv"},
        {"environment_sha256": "secret"},
        {"cohort": "a@private.example"},
        {"profile": {"token": "hidden"}},
    ],
)
def test_allowlist_rejects_private_or_untyped_payloads(values: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        allowed_parameters(values)


@pytest.mark.parametrize(
    "root", ["", "/tmp/tracking", "https://remote.example", "data/raw/tracking", "tmp/../outside"]
)
def test_enabled_requires_valid_ignored_local_configuration(root: str) -> None:
    with pytest.raises(ValueError):
        LocalTracking("evaluation_synthetic", "invalid", root)


@pytest.mark.parametrize(
    "child",
    [
        "tracking.sqlite",
        "tracking.sqlite-wal",
        "tracking.sqlite-shm",
        "receipts",
        "artifacts",
        "artifacts/nested/receipt.json",
    ],
)
def test_tracking_rejects_symlinked_store_children_before_writing(
    repo_tmp_path: Path, child: str
) -> None:
    store = repo_tmp_path / "tracking"
    link = store / child
    link.parent.mkdir(parents=True)
    target = repo_tmp_path / "outside-store"
    directory = child in {"receipts", "artifacts"}
    if directory:
        target.mkdir()
    else:
        target.touch()
    link.symlink_to(target, target_is_directory=directory)

    with pytest.raises(ValueError, match="symlinks"):
        LocalTracking("evaluation_synthetic", "unsafe-child", str(store.relative_to(ROOT)))

    assert list(target.iterdir()) == [] if directory else target.read_bytes() == b""
    assert link.is_symlink()


def test_tracking_rechecks_receipt_storage_before_finishing(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, publication = execute(repo_tmp_path / "publication", monkeypatch, enabled=False)
    store = repo_tmp_path / "tracking"
    tracker = LocalTracking(
        "evaluation_synthetic", "redirected-receipt", str(store.relative_to(ROOT))
    )
    target = repo_tmp_path / "outside-store"
    target.mkdir()
    (store / "receipts").symlink_to(target, target_is_directory=True)

    with pytest.raises(ValueError, match="symlinks"):
        tracker.finish(publication)

    assert list(target.iterdir()) == []
    assert tracker.client.get_run(tracker.parent).info.status == "FAILED"
    assert not tracker.children


def test_disabled_does_not_import_mlflow_and_missing_extra_is_actionable(
    repo_tmp_path: Path,
) -> None:
    code = """
import importlib.abc,sys
class Missing(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0]=='mlflow': raise ModuleNotFoundError('unavailable')
sys.meta_path.insert(0,Missing())
from sat_dengue.hooks import TrackingHooks
class Catalog:
 def load(self,n): return {'tracking':'disabled'}
h=TrackingHooks();h.before_pipeline_run({},Catalog())
assert not any(n.split('.')[0]=='mlflow' for n in sys.modules)
from sat_dengue.tracking.local import LocalTracking
try: LocalTracking('evaluation_synthetic','missing',sys.argv[1])
except RuntimeError as e: assert 'sat-dengue-v2[tracking]' in str(e)
else: raise AssertionError('missing extra silently ignored')
"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(repo_tmp_path.relative_to(ROOT))],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_training_synthetic_tracking_uses_its_own_publication(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.datasets.training import TrainingBundleDataset

    monkeypatch.setenv(
        "SAT_DENGUE_TRACKING_ROOT", str((repo_tmp_path / "tracking").relative_to(ROOT))
    )
    catalog = DataCatalog(
        {
            "configuration_inputs": MemoryDataset(ConfigurationInputsDataset().load()),
            "parameters": MemoryDataset({"profile": "training_synthetic", "tracking": "enabled"}),
            "resolved_configuration": PublishedConfigurationDataset(
                str(repo_tmp_path / "configuration")
            ),
            "training_bundle": TrainingBundleDataset(str(repo_tmp_path / "training")),
            "evaluation_bundle": EvaluationBundleDataset(str(repo_tmp_path / "unused")),
        }
    )
    hooks = TrackingHooks()
    hooks.before_pipeline_run(
        {"pipeline_name": "training_synthetic", "session_id": "training"}, catalog
    )
    SequentialRunner().run(register_pipelines()["training_synthetic"], catalog)
    hooks.after_pipeline_run(catalog)
    runs = hooks.tracker.client.search_runs([hooks.tracker.experiment])
    assert len(runs) == 4 and all(r.info.status == "FINISHED" for r in runs)
    assert not (repo_tmp_path / "unused").exists()
