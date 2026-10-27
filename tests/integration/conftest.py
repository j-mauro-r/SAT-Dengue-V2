"""Shared isolated fixtures for public synthetic integration tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def synthetic_experiments(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise the real resolver with isolated registered synthetic protocols."""
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


@pytest.fixture
def exp02_receipt(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from sat_dengue.experiments import exp02_preflight as checks
    from sat_dengue.experiments.exp01 import digest

    descriptor = {"schema": "exp02-source-metadata-v1", "files": {"generated": {"bytes": 1}}}
    metadata: dict[str, Any] = {
        "code": {"generated.py": "b" * 64},
        "runtime": {"generated": "only"},
    }
    metadata.update(
        code_sha256=digest(metadata["code"]), environment_sha256=digest(metadata["runtime"])
    )
    monkeypatch.setattr(checks, "source_metadata", lambda: descriptor)
    monkeypatch.setattr(checks, "execution_metadata", lambda: metadata)
    monkeypatch.setattr(checks, "runtime_versions", lambda: {"generated": "1"})
    monkeypatch.setattr(
        checks, "git_identity", lambda: {"git_revision": "a" * 40, "git_dirty": False}
    )
    monkeypatch.setenv(
        "SAT_DENGUE_TRACKING_ROOT", str((repo_tmp_path / "tracking").relative_to(ROOT))
    )
    monkeypatch.delenv("SAT_DENGUE_EXP02_APPROVAL", raising=False)
    return checks.preflight(
        {"profile": "exp02_preflight", "tracking": "enabled", "experiment_id": "EXP02"}, descriptor
    )


@pytest.fixture(scope="session")
def exp02_generated_result():
    from sat_dengue.experiments.exp02_runner import synthetic_run

    return synthetic_run(
        {"profile": "exp02_synthetic", "tracking": "disabled", "experiment_id": "EXP02"}
    )


@pytest.fixture
def exp02_generated_bundle(exp02_generated_result):
    from sat_dengue.experiments.exp01 import digest
    from sat_dengue.experiments.exp02_preflight import load_protocol

    code, runtime = {"generated.py": "b" * 64}, {"generated": "only"}
    provenance = {
        "protocol_sha256": digest(load_protocol()),
        "git_revision": "a" * 40,
        "data_sha256": "c" * 64,
        "configuration_sha256": "d" * 64,
        "code": code,
        "runtime": runtime,
        "code_sha256": digest(code),
        "environment_sha256": digest(runtime),
    }
    return {"result": exp02_generated_result, "provenance": provenance}


@pytest.fixture(autouse=True)
def prohibit_exp02_test_access_to_permanent_store(request, monkeypatch):
    if "exp02" not in str(request.fspath) and "test_exp01_catalog" not in str(request.fspath):
        return
    import builtins
    import sqlite3

    real_open, real_path_open, real_connect = builtins.open, Path.open, sqlite3.connect
    protected = ROOT / "tmp/kedro-migration/replay-mlflow"

    def guard(path):
        if isinstance(path, (str, Path)):
            assert "replay-mlflow" not in str(path), "Permanent MLflow access is forbidden"
            assert not Path(path).absolute().is_relative_to(protected)

    def guarded_open(path, *args, **kwargs):
        guard(path)
        return real_open(path, *args, **kwargs)

    def guarded_path_open(path, *args, **kwargs):
        guard(path)
        return real_path_open(path, *args, **kwargs)

    def guarded_connect(database, *args, **kwargs):
        guard(database)
        return real_connect(database, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    monkeypatch.setattr(sqlite3, "connect", guarded_connect)
