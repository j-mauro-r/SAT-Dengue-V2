"""Composed native replay and isolated synthetic failure/restart/identity acceptance."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from kedro.framework.startup import bootstrap_project
from kedro.io import DataCatalog, MemoryDataset
from kedro.runner import SequentialRunner

from sat_dengue.config_loader import CATALOG
from sat_dengue.datasets import ConfigurationInputsDataset
from sat_dengue.datasets.replay_identity import STAGES, open_execution, verify_publication
from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


def test_installed_console_runs_without_repository_pythonpath() -> None:
    """Use the actual console entrypoint without the guarded harness's import setup."""
    env = dict(os.environ, KEDRO_DISABLE_TELEMETRY="yes", PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [
            str(Path(sys.executable).with_name("kedro")),
            "run",
            "--pipeline=evaluation_synthetic",
            "--params=profile=evaluation_synthetic",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def execute(
    folder: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    enabled: bool = False,
    fail: bool = False,
    experiment_id: str | None = None,
) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    bootstrap_project(ROOT)
    monkeypatch.setenv("SAT_DENGUE_REPLAY_ROOT", str(folder.relative_to(ROOT)))
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", str((folder / "tracking").relative_to(ROOT)))
    inputs = ConfigurationInputsDataset().load()
    catalog = DataCatalog.from_config(CATALOG)
    catalog["configuration_inputs"] = MemoryDataset(inputs)
    catalog["parameters"] = MemoryDataset(
        {
            "profile": "replay_synthetic",
            "tracking": "enabled" if enabled else "disabled",
            **({"experiment_id": experiment_id} if experiment_id else {}),
        }
    )
    hooks = TrackingHooks()
    hooks.before_pipeline_run(
        {"pipeline_names": ["replay_synthetic"], "session_id": uuid4().hex}, catalog
    )
    output = catalog["replay_bundle"]
    if fail:

        def stop(data: Any) -> None:
            assert set(data["stages"]) == set(STAGES)
            assert len(data["audit"]["decisions"]) == 6
            raise RuntimeError("injected-between-computation-and-final-publication")

        monkeypatch.setattr(output, "save", stop)
    try:
        SequentialRunner().run(register_pipelines()["replay_synthetic"], catalog)
        hooks.after_pipeline_run(catalog)
    except BaseException as error:
        hooks.on_pipeline_error(error)
        if fail:
            assert "injected-between-computation-and-final-publication" in str(error)
            return hooks.tracker, {}, inputs
        raise
    return hooks.tracker, output.load(), inputs


def scientific_payloads(record: dict[str, Any]) -> dict[str, bytes]:
    return {
        stage + "/" + p.name: p.read_bytes()
        for stage, entry in record["stages"].items()
        for p in (ROOT / entry["path"]).glob("*.csv")
    }


def test_two_source_free_deterministic_runs_and_tracking(
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    synthetic_experiments: None,
) -> None:
    from sat_dengue.datasets import replay_identity
    from sat_dengue.datasets.stage2 import Stage2SourcesDataset

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Synthetic E2E attempted a native source read")

    monkeypatch.setattr(replay_identity, "native_inputs", forbidden)
    monkeypatch.setattr(Stage2SourcesDataset, "load", forbidden)
    runs = []
    for label, enabled in (("off", False), ("on", True)):
        tracker, record, _ = execute(
            repo_tmp_path / label,
            monkeypatch,
            enabled=enabled,
            experiment_id="EXP93" if enabled else None,
        )
        runs.append(scientific_payloads(record))
        assert set(record["stages"]) == set(STAGES)
        audit = json.loads((ROOT / record["path"] / "audit.json").read_text())
        assert audit["synthetic_only"]
        assert all(
            audit.get(counter, 0) == 0
            for counter in (
                "real_model_fits",
                "real_preparer_refits",
                "calibrator_fits",
                "threshold_selection",
            )
        )
        assert audit["G5"] == "NOT_APPROVED" and audit["champion"] == "not_selected"
        # The final commit is lineage only; no duplicate native payload bundle.
        assert set(record["manifest"]["files"]) == {"audit.json", "lineage.json", "provenance.json"}
        if enabled:
            observed = tracker.client.search_runs([tracker.experiment])
            assert len(observed) == 7 and all(r.info.status == "FINISHED" for r in observed)
            parent = tracker.client.get_run(tracker.parent)
            assert parent.data.tags["experiment_id"] == "EXP93"
            assert (
                parent.data.params["pipeline_identity_sha256"]
                == record["manifest"]["context_sha256"]
            )
            assert "/Users/" not in json.dumps([r.data.params for r in observed])
            snapshots = list((repo_tmp_path / label).glob("*/configuration/*/*/resolved.json"))
            assert len(snapshots) >= 4
            for snapshot in snapshots:
                provenance = json.loads(snapshot.read_text())
                assert provenance["operational"]["experiment_id"] == "EXP93"
        else:
            assert tracker is None and not (repo_tmp_path / label / "tracking").exists()
    assert runs[0] and runs[0] == runs[1]


def test_failure_restart_reuses_verified_stages_and_never_duplicates_success(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = repo_tmp_path / "restart"
    failed, record, _ = execute(folder, monkeypatch, enabled=True, fail=True)
    assert not record
    assert failed.client.get_run(failed.parent).info.status == "FAILED"
    executions = list(folder.glob("*/execution.json"))
    assert len(executions) == 1
    execution = executions[0].parent
    assert not (execution / "publication").exists()
    assert len(list(execution.glob("checkpoint-*.json"))) == 4
    before = {str(p): p.read_bytes() for p in execution.rglob("manifest.json")}
    from sat_dengue.model_training import workflow as training
    from sat_dengue.training_preparation import workflow as preparation

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Restart attempted a synthetic refit instead of verified reuse")

    monkeypatch.setattr(training, "fit_synthetic", forbidden)
    monkeypatch.setattr(preparation, "fit_training_partition", forbidden)
    restarted, publication, _ = execute(folder, monkeypatch, enabled=True)
    assert restarted.client.get_run(restarted.parent).info.status == "FINISHED"
    assert all(Path(p).read_bytes() == b for p, b in before.items())
    duplicate, same, _ = execute(folder, monkeypatch, enabled=True)
    assert publication == same
    assert duplicate.client.get_run(duplicate.parent).info.status == "KILLED"
    observed = duplicate.client.search_runs([duplicate.experiment])
    assert len([r for r in observed if r.info.status == "FINISHED"]) == 7
    assert len(list(execution.glob("publication/*/manifest.json"))) == 1
    assert not list(execution.rglob(".publish.lock"))
    assert not [p for p in execution.rglob("*") if p.name.startswith((".bundle-", ".publish-"))]


def test_tampered_stale_missing_and_changed_identity_refused(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = repo_tmp_path / "identity"
    _, publication, inputs = execute(folder, monkeypatch)
    parameters = {"profile": "replay_synthetic", "tracking": "disabled"}
    context = open_execution(inputs, parameters, mode="synthetic")
    assert set(context["cache"]) == set(STAGES)
    record = publication["stages"]["data"]
    payload = ROOT / record["path"] / "panel.csv"
    original = payload.read_bytes()
    payload.chmod(0o644)
    try:
        payload.write_bytes(original + b"tampered")
        with pytest.raises(ValueError, match="payload changed"):
            open_execution(inputs, parameters, mode="synthetic")
    finally:
        payload.write_bytes(original)
        payload.chmod(0o444)
    with pytest.raises(ValueError, match="Stale"):
        verify_publication(record, {**context, "identity": "0" * 64})
    checkpoint = ROOT / context["folder"] / "checkpoint-preparation.json"
    held = checkpoint.with_suffix(".held")
    checkpoint.rename(held)
    try:
        with pytest.raises(ValueError, match="missing ancestors"):
            open_execution(inputs, parameters, mode="synthetic")
    finally:
        held.rename(checkpoint)
    altered = copy.deepcopy(inputs)
    altered["authorities"]["model_engineering_contract_v1"]["document"]["schema"] = "altered"
    with pytest.raises(ValueError, match="contract identity"):
        open_execution(altered, parameters, mode="synthetic")
    with pytest.raises(ValueError):
        open_execution(inputs, {**parameters, "tracking": "automatic"}, mode="synthetic")
    # Legitimate operational/code/environment changes may create fresh executions,
    # but can never reuse the old checkpoints or overwrite the old publication.
    for field in ("code", "environment", "loaded_package_code"):
        changed = copy.deepcopy(inputs)
        changed["execution"][field]["changed"] = "new-identity"
        new = open_execution(changed, parameters, mode="synthetic")
        assert new["identity"] != context["identity"] and not new["cache"]
        with pytest.raises(ValueError, match="Stale"):
            verify_publication(record, new)
    new = open_execution(inputs, {**parameters, "tracking": "enabled"}, mode="synthetic")
    assert new["identity"] != context["identity"] and not new["cache"]
    assert payload.read_bytes() == original

    for field, value in (
        ("python", "changed-python"),
        ("git_dirty", not inputs["execution"]["git_dirty"]),
    ):
        changed_input = copy.deepcopy(inputs)
        changed_input["execution"][field] = value
        changed_context = open_execution(changed_input, parameters, mode="synthetic")
        assert changed_context["identity"] != context["identity"] and not changed_context["cache"]

    from sat_dengue.datasets import replay_identity

    fingerprint = replay_identity.identity
    seen = []

    def changed_adapter(path: Path) -> dict[str, Any]:
        result = fingerprint(path)
        if path.is_relative_to(ROOT / "scripts"):
            seen.append(path)
            return {**result, "sha256": "0" * 64}
        return result

    # Fault injection changes only observed identities; original code is never written.
    monkeypatch.setattr(replay_identity, "identity", changed_adapter)
    changed = open_execution(inputs, parameters, mode="synthetic")
    assert seen and changed["identity"] != context["identity"] and not changed["cache"]
    with pytest.raises(ValueError, match="Stale"):
        verify_publication(record, changed)


@pytest.mark.migration_evidence
def test_one_command_full_guarded_replay_and_complete_preservation() -> None:
    from migration_support import (
        BASELINE_SHA256,
        fingerprint,
        new_evidence_directory,
        verify_protected_inventory,
    )

    evidence = new_evidence_directory("e2e")
    evidence.mkdir(parents=True, exist_ok=True)
    baseline_path = ROOT / "tmp/kedro-migration/baseline.json"
    assert fingerprint(baseline_path)["sha256"] == BASELINE_SHA256
    baseline = json.loads(baseline_path.read_text())
    before = verify_protected_inventory(ROOT, baseline)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", KEDRO_DISABLE_TELEMETRY="yes")
    env["PYTHONPATH"] = os.pathsep.join([str(ROOT), str(ROOT / "src")])
    # Persistent private acceptance roots are isolated per invocation; no implicit latest.
    storage = ROOT / "tmp/kedro-migration/e2e-private" / uuid4().hex
    env["SAT_DENGUE_REPLAY_ROOT"] = str(storage.relative_to(ROOT))
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, "tests/integration/replay_cli.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    (evidence / "one-command-no-adjustment.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-4000:]
    publications = list(storage.glob("*/publication/*/manifest.json"))
    assert len(publications) == 1
    manifest = json.loads(publications[0].read_text())
    assert manifest["real_model_fits"] == manifest["real_preparer_refits"] == 0
    assert len(list(storage.glob("*/checkpoint-*.json"))) == 4
    lineage = json.loads((publications[0].parent / "lineage.json").read_text())
    assert set(lineage) == set(STAGES)
    for record in lineage.values():
        verify_publication(record)
    after = verify_protected_inventory(ROOT, baseline)
    assert after == before
    (evidence / "one-command-receipt.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "command": "kedro run --pipeline=replay",
                "guarded": True,
                "wall_seconds": time.monotonic() - start,
                "real_adjustments": 0,
                "publication": str(publications[0].parent.relative_to(ROOT)),
                "before": before,
                "after": after,
                "stages": list(lineage),
            },
            indent=2,
        )
        + "\n"
    )


@pytest.mark.parametrize(
    "root", ["/tmp/replay", "https://remote.example", "data/raw/replay", "tmp/../outside"]
)
def test_replay_storage_rejects_unsafe_locations(
    root: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.datasets.replay_identity import storage

    monkeypatch.setenv("SAT_DENGUE_REPLAY_ROOT", root)
    with pytest.raises(ValueError):
        storage()


def test_changed_pinned_native_input_is_rejected_without_a_write(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sat_dengue.datasets import replay_identity

    monkeypatch.setattr(replay_identity, "identity", lambda path: {"bytes": 0, "sha256": "0" * 64})
    with pytest.raises(ValueError, match="source identity changed"):
        replay_identity.native_inputs()
