"""Observe real local MLflow lifecycle and privacy against complete synthetic Kedro runs."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
import yaml  # type: ignore[import-untyped]
from kedro.framework.hooks.manager import _create_hook_manager
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue.datasets import ConfigurationInputsDataset
from sat_dengue.datasets.evaluation import EvaluationBundleDataset
from sat_dengue.datasets.stage2 import PublishedConfigurationDataset
from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.tracking.artifacts import register_local_artifacts
from sat_dengue.tracking.lineage import verified_lineage
from sat_dengue.tracking.local import LocalTracking, allowed_parameters

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    "name", ["literal space", "encoded%2Fstore", "query?ignored=1", "fragment#tag", "unicode-ñ"]
)
def test_tracking_uri_preserves_literal_store_and_receipt_paths(
    repo_tmp_path: Path, name: str
) -> None:
    store = repo_tmp_path / name
    # Keep the pre-fix decoded alias writable so a misplaced database fails
    # promptly instead of invoking the SDK's lengthy connection retries.
    if name == "encoded%2Fstore":
        (repo_tmp_path / "encoded" / "store").mkdir(parents=True)
    tracker = LocalTracking("foundation", "literal-path", str(store.relative_to(ROOT)))
    receipt = repo_tmp_path / (uuid4().hex + ".json")
    payload = {
        "schema": "bounded-mlflow-lineage-v1",
        "parameters": {"observability_profile": "standard"},
        "real_adjustments": 0,
    }
    receipt.write_text(json.dumps(payload))
    tracker.client.log_artifact(tracker.parent, str(receipt))
    tracker.fail(aborted=True)

    assert (store / "tracking.sqlite").is_file()
    copies = list((store / "artifacts").rglob(receipt.name))
    assert len(copies) == 1 and copies[0].read_bytes() == receipt.read_bytes()
    assert tracker.client.get_run(tracker.parent).info.status == "KILLED"
    assert all(
        path == receipt or path.is_relative_to(store)
        for path in repo_tmp_path.rglob("*")
        if path.is_file()
    )


@pytest.mark.parametrize(
    "relative", ["tmp/%2e%2e/.dwp/uri-escape", "tmp/nested%2F..%2F../.dwp/uri-escape"]
)
def test_artifact_uri_rejects_decoded_parent_traversal(relative: str) -> None:
    from mlflow.store.artifact.artifact_repository_registry import get_artifact_repository

    register_local_artifacts()
    with pytest.raises(ValueError, match="Artifact URI"):
        get_artifact_repository("satlocal:/" + relative)


def test_artifact_uri_rejects_encoded_symlink(repo_tmp_path: Path) -> None:
    from mlflow.store.artifact.artifact_repository_registry import get_artifact_repository

    target = repo_tmp_path / "outside-store"
    target.mkdir()
    link = repo_tmp_path / "linked store"
    link.symlink_to(target, target_is_directory=True)
    encoded = str(link.relative_to(ROOT)).replace(" ", "%20")
    register_local_artifacts()
    with pytest.raises(ValueError, match="Artifact URI"):
        get_artifact_repository("satlocal:/" + encoded)
    assert list(target.iterdir()) == []


@pytest.mark.parametrize("preimport", [False, True])
def test_local_tracking_disables_sdk_telemetry_outside_pytest(
    repo_tmp_path: Path, preimport: bool
) -> None:
    """CI's implicit SDK opt-out must not conceal telemetry in an ordinary process."""
    config = repo_tmp_path / "sdk-config"
    store = repo_tmp_path / "tracking"
    script = """
import json
import socket
import sys
from pathlib import Path

attempts = []
def audit(event, args):
    if event in {"socket.getaddrinfo", "socket.connect"}:
        attempts.append(event)
        raise RuntimeError("Network egress is forbidden in this local tracking test")
sys.addaudithook(audit)
preimport = sys.argv[1] == "True"
if preimport:
    import mlflow
from sat_dengue.tracking.local import LocalTracking
tracker = LocalTracking("foundation", "telemetry-regression", root=sys.argv[2])
tracker.fail(aborted=True)
from mlflow.telemetry.client import get_telemetry_client
from mlflow.telemetry.utils import is_telemetry_disabled
assert is_telemetry_disabled()
assert not attempts, attempts
client = get_telemetry_client()
if preimport:
    assert client is not None and not client._is_config_fetched
    assert client._queue.empty() and not client._pending_records
else:
    assert client is None
    assert not (Path(sys.argv[3]) / "mlflow" / "telemetry.json").exists()
assert tracker.client.get_run(tracker.parent).info.status == "KILLED"
print(json.dumps({"telemetry_disabled": True, "network_attempts": attempts}))
"""
    # A deliberately minimal child environment excludes pytest/CI opt-outs and
    # confines any pre-import SDK installation identifier to the repository.
    env = {
        "PATH": os.environ["PATH"],
        "PYTHONDONTWRITEBYTECODE": "1",
        "XDG_CONFIG_HOME": str(config),
        "MLFLOW_DISABLE_TELEMETRY": "false",
    }
    result = subprocess.run(
        [sys.executable, "-c", script, str(preimport), str(store.relative_to(ROOT)), str(config)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout.splitlines()[-1]) == {
        "telemetry_disabled": True,
        "network_attempts": [],
    }


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
 def load(self,n): return {'profile':'foundation','tracking':'disabled'}
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


@pytest.fixture
def synthetic_experiments(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the real resolver with an isolated registered synthetic protocol."""
    import hashlib

    from sat_dengue.configuration import canonical_bytes
    from sat_dengue.tracking import experiments

    registry = yaml.safe_load(experiments.REGISTRY.read_text())
    original = registry["experiments"][0]
    protocol = json.loads(Path(original["protocol"]).read_text())
    entries = []
    base = (repo_tmp_path / "docs/product/experiments").relative_to(ROOT)
    for identifier in ("EXP91", "EXP92", "EXP93"):
        entry = dict(original)
        document = json.loads(json.dumps(protocol))
        for target in (entry, document, document["mlflow"]["required_conceptual_tags"]):
            target.update(
                experiment_id=identifier,
                hypothesis_id=identifier + "-H0",
                experiment_slug="synthetic_tracking_fixture",
            )
        document["execution"]["kedro_pipeline"] = (
            "replay_synthetic" if identifier == "EXP93" else "evaluation_synthetic"
        )
        entry["pipeline"] = document["execution"]["kedro_pipeline"]
        path = base / identifier / "protocol.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(canonical_bytes(document))
        entry["protocol"] = str(path)
        entry["conclusions"] = str(path.with_name("CONCLUSIONS.md"))
        entry["protocol_sha256"] = hashlib.sha256(canonical_bytes(document)).hexdigest()
        entries.append(entry)
    registry["experiments"] = entries
    path = base / "experiment-registry.yml"
    path.write_text(yaml.safe_dump(registry))
    monkeypatch.setattr(experiments, "REGISTRY", path)


def test_registered_parent_children_names_counters_and_duplicate_isolation(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_experiments: None
) -> None:
    from sat_dengue.tracking.experiments import resolve_experiment
    from sat_dengue.tracking.lineage import COUNTERS

    _, publication = execute(repo_tmp_path / "native", monkeypatch, enabled=False)
    store = str((repo_tmp_path / "registered").relative_to(ROOT))
    first = LocalTracking("evaluation_synthetic", "first", store, experiment_id="EXP91")
    first.finish(publication)
    tags = resolve_experiment("EXP91")
    runs = first.client.search_runs([first.experiment])
    assert len(runs) == 7
    for run in runs:
        assert all(run.data.tags[k] == v for k, v in tags.items())
        assert run.info.status == "FINISHED"
        if run.info.run_id == first.parent:
            assert run.data.tags["mlflow.runName"].startswith("EXP91:synthetic_tracking_fixture:")
            assert all(run.data.metrics[k] == 0 for k in COUNTERS)
            assert run.data.params["G5"] == "NOT_APPROVED"
            assert run.data.params["champion"] == "not_selected"
        else:
            assert run.data.tags["mlflow.runName"].startswith(
                "EXP91:" + run.data.params["family"] + ":t" + run.data.params["horizon"] + ":"
            )
    retry = LocalTracking("evaluation_synthetic", "retry", store, experiment_id="EXP91")
    assert retry.finish(publication) == first.parent
    assert retry.client.get_run(retry.parent).data.tags["duplicate_of"] == first.parent
    other = LocalTracking("evaluation_synthetic", "other", store, experiment_id="EXP92")
    assert other.finish(publication) == other.parent
    assert other.parent != first.parent
    assert (
        len(
            first.client.search_runs(
                [first.experiment], filter_string="attributes.status = 'FINISHED'"
            )
        )
        == 14
    )


def test_store_rejects_rewritten_protocol_even_if_registry_hash_updated(
    repo_tmp_path: Path, synthetic_experiments: None
) -> None:
    import hashlib

    from sat_dengue.configuration import canonical_bytes
    from sat_dengue.tracking.experiments import REGISTRY

    store = str((repo_tmp_path / "frozen").relative_to(ROOT))
    first = LocalTracking("evaluation_synthetic", "first", store, experiment_id="EXP91")
    first.fail()
    registry = yaml.safe_load(REGISTRY.read_text())
    entry = registry["experiments"][0]
    path = Path(entry["protocol"])
    document = json.loads(path.read_text())
    document["objective"] = "Modified protocol content"
    path.write_bytes(canonical_bytes(document))
    entry["protocol_sha256"] = hashlib.sha256(canonical_bytes(document)).hexdigest()
    REGISTRY.write_text(yaml.safe_dump(registry))
    with pytest.raises(ValueError, match="already frozen"):
        LocalTracking("evaluation_synthetic", "changed", store, experiment_id="EXP91")
    assert len(first.client.search_runs([first.experiment])) == 1


def test_real_hook_requires_id_before_creating_store(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", str(repo_tmp_path.relative_to(ROOT)))
    catalog = DataCatalog(
        {"parameters": MemoryDataset({"profile": "foundation", "tracking": "enabled"})}
    )
    with pytest.raises(ValueError, match="requires experiment_id"):
        TrackingHooks().before_pipeline_run({"pipeline_name": "replay"}, catalog)
    assert not (repo_tmp_path / "tracking.sqlite").exists()
    with pytest.raises(ValueError, match="pipeline mismatch"):
        LocalTracking(
            "evaluation_synthetic",
            "mismatch",
            str(repo_tmp_path.relative_to(ROOT)),
            experiment_id="EXP00",
        )


def test_registered_synthetic_composition_propagates_identity(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_experiments: None
) -> None:
    from test_kedro_e2e import execute as composed

    from sat_dengue.datasets import replay_identity

    def forbidden() -> None:
        raise AssertionError("Real replay inputs are forbidden")

    monkeypatch.setattr(replay_identity, "native_inputs", forbidden)
    tracker, record, _ = composed(
        repo_tmp_path / "composed", monkeypatch, enabled=True, experiment_id="EXP93"
    )
    assert tracker.client.get_run(tracker.parent).data.tags["experiment_id"] == "EXP93"
    audit = json.loads((ROOT / record["path"] / "audit.json").read_text())
    assert all(
        audit.get(k, 0) == 0
        for k in (
            "real_model_fits",
            "real_preparer_refits",
            "calibrator_fits",
            "threshold_selection",
        )
    )
    snapshots = list((repo_tmp_path / "composed").glob("*/configuration/*/*/resolved.json"))
    assert len(snapshots) >= 4
    for snapshot in snapshots:
        provenance = json.loads(snapshot.read_text())
        assert provenance["operational"]["experiment_id"] == "EXP93"


def test_concurrent_retries_publish_one_verified_success(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, synthetic_experiments: None
) -> None:
    from concurrent.futures import ThreadPoolExecutor

    _, publication = execute(repo_tmp_path / "native", monkeypatch, enabled=False)
    store = str((repo_tmp_path / "concurrent").relative_to(ROOT))
    trackers = [
        LocalTracking("evaluation_synthetic", str(i), store, experiment_id="EXP91")
        for i in range(2)
    ]
    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda tracker: tracker.finish(publication), trackers))
    assert results[0] == results[1]
    assert sorted(t.client.get_run(t.parent).info.status for t in trackers) == [
        "FINISHED",
        "KILLED",
    ]


def test_scientific_registration_rejects_synthetic_payload(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, publication = execute(repo_tmp_path / "native", monkeypatch, enabled=False)
    tracker = LocalTracking(
        "replay",
        "synthetic-mismatch",
        str((repo_tmp_path / "store").relative_to(ROOT)),
        experiment_id="EXP00",
    )
    with pytest.raises(ValueError, match="cannot register a synthetic"):
        tracker.finish(publication)
    assert tracker.client.get_run(tracker.parent).info.status == "FAILED"


def test_duplicate_rejects_corrupted_existing_metrics(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, publication = execute(repo_tmp_path / "native", monkeypatch)
    first.client.log_metric(first.children[0], "brier", 999)
    second = LocalTracking(
        "evaluation_synthetic", "retry", str((repo_tmp_path / "native/tracking").relative_to(ROOT))
    )
    with pytest.raises(ValueError, match="scientific lineage changed"):
        second.finish(publication)
    assert second.client.get_run(second.parent).info.status == "FAILED"


def test_private_child_name_is_rejected_before_mlflow_write(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.tracking import local

    _, publication = execute(repo_tmp_path / "native", monkeypatch, enabled=False)
    params, candidates = verified_lineage(publication)
    candidates[0]["window"] = "/Users/private/secret"
    monkeypatch.setattr(local, "verified_lineage", lambda publication: (params, candidates))
    tracker = LocalTracking(
        "evaluation_synthetic", "private-child", str((repo_tmp_path / "store").relative_to(ROOT))
    )
    with pytest.raises(ValueError, match="Tracking value rejected"):
        tracker.finish(publication)
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 1
    assert "/Users/private" not in json.dumps(runs[0].data.tags)
