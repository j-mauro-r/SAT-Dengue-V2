"""Exercise actual merged configuration, scientific authority and immutable publication."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
from kedro.io import DatasetError
from migration_support import (
    METADATA_ORIGINALS,
    fingerprint,
    verify_preservation_records,
)
from packaging.requirements import Requirement

from sat_dengue.config_loader import ValidatedConfigLoader
from sat_dengue.configuration import AUTHORITIES, canonical_bytes, resolve_configuration
from sat_dengue.datasets import ConfigurationInputsDataset, ImmutableConfigurationDataset

ROOT = Path(__file__).resolve().parents[2]


def test_resolved_snapshot_reads_the_single_scientific_authority(repo_tmp_path: Path) -> None:
    directory = str(repo_tmp_path)
    _check_resolved_snapshot(Path(directory))


def test_snapshot_storage_rejects_external_repository_path() -> None:
    with pytest.raises(ValueError, match="Snapshot storage must remain inside the repository"):
        ImmutableConfigurationDataset(str(ROOT.parent / "external-snapshot"))


def _check_resolved_snapshot(tmp_path: Path) -> None:
    inputs = ConfigurationInputsDataset().load()
    loader = ValidatedConfigLoader(str(ROOT / "conf"), base_env="base", default_run_env="base")
    resolved = resolve_configuration(inputs, loader["parameters"])
    assert loader["catalog"]["configuration_inputs"]["type"].endswith("ConfigurationInputsDataset")
    for name, identity in AUTHORITIES.items():
        assert resolved["authorities"][name]["document"] == json.loads(
            ROOT.joinpath(identity["path"]).read_text()
        )
    policy = resolved["authorities"]["champion_decision_policy_v1"]["document"]
    assert policy["human_disposition"]["G5"] == "NOT_APPROVED"
    assert policy["human_disposition"]["champion"] == "not_selected"
    dataset = ImmutableConfigurationDataset(str(tmp_path))
    dataset.save(resolved)
    path = tmp_path / inputs["execution"]["run_id"] / "resolved.json"
    assert path.read_bytes() == canonical_bytes(resolved)
    assert path.stat().st_mode & 0o222 == 0
    dataset.save(resolved)  # exact retry is safe
    tampered = copy.deepcopy(resolved)
    tampered["operational"]["tracking"] = "enabled"
    with pytest.raises(DatasetError, match="fingerprint mismatch"):
        dataset.save(tampered)
    body = {k: v for k, v in tampered.items() if k != "configuration_sha256"}
    tampered["configuration_sha256"] = hashlib.sha256(canonical_bytes(body)).hexdigest()
    with pytest.raises(DatasetError, match="different bytes"):
        dataset.save(tampered)
    assert path.read_bytes() == canonical_bytes(resolved)
    assert list(path.parent.iterdir()) == [path]


@pytest.mark.parametrize(
    "runtime",
    [
        {"profile": "training"},
        {"profile": 1},
        {"tracking": "autolog"},
        {"seed": 0},
        {"scientific": {"utility": {"seed": 0}}},
        {"utility": {"max_false_alarm_increase_pp": 99}},
    ],
)
def test_runtime_overrides_fail_closed(runtime: dict[str, Any]) -> None:
    loader = ValidatedConfigLoader(
        str(ROOT / "conf"), base_env="base", default_run_env="base", runtime_params=runtime
    )
    with pytest.raises(ValueError, match="Only operational|Unknown profile"):
        loader["parameters"]


@pytest.mark.parametrize(
    "content",
    [
        "profile: unknown\ntracking: disabled\n",
        "profile: foundation\ntracking: 1\n",
        "profile: foundation\ntracking: disabled\nseed: 42\n",
    ],
)
def test_environment_yaml_cannot_add_scientific_settings(tmp_path: Path, content: str) -> None:
    shutil.copytree(ROOT / "conf/base", tmp_path / "base")
    (tmp_path / "override").mkdir()
    (tmp_path / "override/parameters.yml").write_text(content)
    loader = ValidatedConfigLoader(str(tmp_path), env="override", base_env="base")
    with pytest.raises(ValueError):
        loader["parameters"]


def test_catalog_cannot_replace_scientific_authority(tmp_path: Path) -> None:
    shutil.copytree(ROOT / "conf/base", tmp_path / "base")
    (tmp_path / "override").mkdir()
    (tmp_path / "override/catalog.yml").write_text("configuration_inputs:\n  type: MemoryDataset\n")
    loader = ValidatedConfigLoader(str(tmp_path), env="override", base_env="base")
    with pytest.raises(ValueError, match="Catalog overrides"):
        loader["catalog"]


@pytest.mark.parametrize("content", ["[]", '{"schema": "unknown"}', '{"utility": {"seed": 1}}'])
def test_invalid_scientific_json_is_rejected_without_repair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    content: str,
) -> None:
    for identity in AUTHORITIES.values():
        path = tmp_path / identity["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / identity["path"], path)
    path = tmp_path / next(iter(AUTHORITIES.values()))["path"]
    path.write_text(content)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(DatasetError, match="Scientific authority changed"):
        ConfigurationInputsDataset().load()
    assert path.read_text() == content


def test_scientific_inputs_are_read_only_and_runs_are_distinct() -> None:
    dataset = ConfigurationInputsDataset()
    first, second = dataset.load(), dataset.load()
    assert first["authorities"] == second["authorities"]
    assert first["execution"]["run_id"] != second["execution"]["run_id"]
    with pytest.raises(DatasetError, match="read-only"):
        dataset.save(first)


def test_dependency_versions_have_one_authority_and_derived_constraints() -> None:
    raw = (ROOT / "pyproject.toml").read_bytes()
    project = tomllib.loads(raw.decode())["project"]
    lock = (ROOT / "docs/operations/kedro-foundation-constraints.txt").read_text()
    assert hashlib.sha256(raw).hexdigest() in lock
    pins = {
        Requirement(line).name.lower().replace("_", "-"): Requirement(line).specifier
        for line in lock.splitlines()
        if line and not line.startswith("#")
    }
    declared = project["dependencies"] + [
        value for values in project["optional-dependencies"].values() for value in values
    ]
    for value in declared:
        requirement = Requirement(value)
        assert str(requirement.specifier).startswith("==")
        assert pins[requirement.name.lower().replace("_", "-")] == requirement.specifier
    assert ".[modeling]" in (ROOT / "requirements-modeling.txt").read_text()
    assert ".[dev,modeling,notebook,tracking]" in (ROOT / "requirements-dev.txt").read_text()
    assert "==" not in (ROOT / "requirements-modeling.txt").read_text()
    assert "==" not in (ROOT / "requirements-dev.txt").read_text()


@pytest.mark.parametrize("mutation", ["current", "original", "revision", "expanded", "protected"])
def test_metadata_amendment_has_exact_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    ledger = json.loads((ROOT / "docs/operations/kedro-foundation-metadata.json").read_text())
    for name in METADATA_ORIGINALS:
        shutil.copyfile(ROOT / name, tmp_path / name)
    extra = tmp_path / "science.json"
    extra.write_text('{"scientific": "unchanged"}')
    records = {**METADATA_ORIGINALS, "science.json": fingerprint(extra)}
    # Use the actual pinned Git blobs, while keeping mutations inside the fixture.
    original_check_output = subprocess.check_output

    def git_blob(*args: Any, **kwargs: Any) -> bytes:
        kwargs["cwd"] = ROOT
        return original_check_output(*args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", git_blob)
    path = tmp_path / "docs/operations/kedro-foundation-metadata.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(ledger))
    assert verify_preservation_records(tmp_path, records) == 3
    if mutation == "current":
        (tmp_path / "pyproject.toml").write_text("changed")
    elif mutation == "original":
        ledger["files"]["pyproject.toml"]["original"]["sha256"] = "0" * 64
    elif mutation == "revision":
        ledger["original_revision"] = "HEAD"
    elif mutation == "expanded":
        ledger["files"]["science.json"] = ledger["files"]["pyproject.toml"]
    else:
        extra.write_text("changed")
    path.write_text(json.dumps(ledger))
    with pytest.raises(AssertionError):
        verify_preservation_records(tmp_path, records)
