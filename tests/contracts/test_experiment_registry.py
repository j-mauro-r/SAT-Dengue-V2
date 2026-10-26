"""Registered experiment identities are frozen, private and reusable."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.tracking.experiments import REGISTRY, conceptual_tags, resolve_experiment

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def registry(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    shutil.copytree(ROOT / REGISTRY.parent, repo_tmp_path / REGISTRY.parent)
    monkeypatch.chdir(repo_tmp_path)
    return yaml.safe_load(REGISTRY.read_text())


def save(registry: dict[str, Any]) -> None:
    REGISTRY.write_text(yaml.safe_dump(registry))


def test_valid_baseline_and_disabled_configuration() -> None:
    tags = resolve_experiment("EXP00")
    assert tags["experiment_type"] == "baseline_replay"
    assert tags["objective_slug"] == "register_pre_kedro_baseline"
    assert len(tags["protocol_sha256"]) == 64
    assert validate_parameters({"profile": "replay", "tracking": "disabled"}) == {
        "profile": "replay",
        "tracking": "disabled",
    }
    assert (
        validate_parameters({"profile": "replay", "tracking": "enabled", "experiment_id": "EXP00"})[
            "experiment_id"
        ]
        == "EXP00"
    )


@pytest.mark.parametrize("profile", ["replay", "training_replay", "evaluation_replay"])
def test_enabled_real_requires_identity(profile: str) -> None:
    with pytest.raises(ValueError, match="requires experiment_id"):
        validate_parameters({"profile": profile, "tracking": "enabled"})


def test_unknown_experiment_and_configuration_keys() -> None:
    with pytest.raises(ValueError, match="Unregistered"):
        resolve_experiment("EXP99")
    with pytest.raises(ValueError):
        validate_parameters({"profile": "foundation", "tracking": "disabled", "secret": "x"})


@pytest.mark.parametrize("mutation", ["duplicate", "unknown_key", "hash", "mismatch", "schema"])
def test_invalid_registry(registry: dict[str, Any], mutation: str) -> None:
    entry = registry["experiments"][0]
    if mutation == "duplicate":
        registry["experiments"].append(copy.deepcopy(entry))
    elif mutation == "unknown_key":
        entry["unexpected"] = "value"
    elif mutation == "hash":
        entry["protocol_sha256"] = "0" * 64
    elif mutation == "mismatch":
        entry["experiment_slug"] = "different"
    else:
        registry["schema"] = "unknown"
    save(registry)
    with pytest.raises(ValueError):
        resolve_experiment("EXP00")


@pytest.mark.parametrize(
    "path",
    ["/private/protocol.json", "docs/product/experiments/../protocol.json", "tmp/protocol.json"],
)
def test_unsafe_path(registry: dict[str, Any], path: str) -> None:
    registry["experiments"][0]["protocol"] = path
    save(registry)
    with pytest.raises(ValueError, match="Unsafe"):
        resolve_experiment("EXP00")


@pytest.mark.parametrize("kind", ["file", "directory", "registry"])
def test_symlinks(registry: dict[str, Any], kind: str) -> None:
    protocol = Path(registry["experiments"][0]["protocol"])
    path = REGISTRY if kind == "registry" else protocol.parent if kind == "directory" else protocol
    target = path.with_name(path.name + "-original")
    path.rename(target)
    path.symlink_to(target.name, target_is_directory=kind == "directory")
    with pytest.raises(ValueError, match="Unsafe"):
        resolve_experiment("EXP00")


@pytest.mark.parametrize(
    "value",
    [
        "/Users/private/data",
        "free text",
        "ghp_secret",
        "AKIA1234567890",
        "password",
        {"token": "hidden"},
    ],
)
def test_conceptual_privacy(value: Any) -> None:
    tags = {
        k: v
        for k, v in resolve_experiment("EXP00").items()
        if k not in {"pipeline", "protocol_sha256"}
    }
    tags["objective_slug"] = value
    with pytest.raises(ValueError):
        conceptual_tags(tags)


def test_future_registered_experiment(registry: dict[str, Any]) -> None:
    entry = copy.deepcopy(registry["experiments"][0])
    protocol = json.loads(Path(entry["protocol"]).read_text())
    for doc in (entry, protocol, protocol["mlflow"]["required_conceptual_tags"]):
        doc.update(
            experiment_id="EXP89", experiment_slug="future_comparison", hypothesis_id="EXP89-H1"
        )
    path = REGISTRY.parent / "EXP89_future/protocol.json"
    path.parent.mkdir()
    path.write_bytes(canonical_bytes(protocol))
    entry["protocol"] = str(path)
    entry["protocol_sha256"] = hashlib.sha256(canonical_bytes(protocol)).hexdigest()
    registry["experiments"].append(entry)
    save(registry)
    assert resolve_experiment("EXP89")["experiment_slug"] == "future_comparison"
    protocol["objective"] = "changed after freezing"
    path.write_bytes(canonical_bytes(protocol))
    with pytest.raises(ValueError, match="hash"):
        resolve_experiment("EXP89")


def test_duplicate_document_keys(registry: dict[str, Any]) -> None:
    REGISTRY.write_text(REGISTRY.read_text() + '\nversion: "1.0.0"\n')
    with pytest.raises(ValueError, match="Duplicate"):
        resolve_experiment("EXP00")


@pytest.mark.parametrize(
    "mutation",
    [
        "different_name",
        "missing_name",
        "missing_tags",
        "extra_key",
        "registration_status",
        "implementation_note",
    ],
)
def test_protocol_mlflow_schema_and_container_are_closed(
    registry: dict[str, Any], mutation: str
) -> None:
    entry = registry["experiments"][0]
    path = Path(entry["protocol"])
    protocol = json.loads(path.read_text())
    mlflow = protocol["mlflow"]
    if mutation == "different_name":
        mlflow["experiment_name"] = "another-container"
    elif mutation == "missing_name":
        del mlflow["experiment_name"]
    elif mutation == "missing_tags":
        del mlflow["required_conceptual_tags"]
    else:
        mlflow[mutation] = "unapproved"
    path.write_bytes(canonical_bytes(protocol))
    entry["protocol_sha256"] = hashlib.sha256(canonical_bytes(protocol)).hexdigest()
    save(registry)
    with pytest.raises(ValueError, match="MLflow"):
        resolve_experiment("EXP00")


def test_baseline_protocol_keeps_only_stable_mlflow_fields_and_tags() -> None:
    from sat_dengue.tracking.experiments import MLFLOW_EXPERIMENT_NAME

    registry = yaml.safe_load(REGISTRY.read_text())
    entry = registry["experiments"][0]
    protocol = json.loads(Path(entry["protocol"]).read_text())
    assert set(protocol["mlflow"]) == {"experiment_name", "required_conceptual_tags"}
    assert protocol["mlflow"]["experiment_name"] == MLFLOW_EXPERIMENT_NAME
    assert entry["mlflow_registration"] == "pending"
    expected = {
        "experiment_id": "EXP00",
        "experiment_slug": "historical_pre_kedro_baseline",
        "hypothesis_id": "EXP00-H0",
        "objective_slug": "register_pre_kedro_baseline",
        "experiment_type": "baseline_replay",
        "target_definition": "excess_with_onset_evaluation",
    }
    assert protocol["mlflow"]["required_conceptual_tags"] == expected
    assert resolve_experiment("EXP00") == {
        **expected,
        "pipeline": "replay",
        "protocol_sha256": entry["protocol_sha256"],
    }
    with pytest.raises(ValueError, match="Only operational"):
        validate_parameters(
            {
                "profile": "foundation",
                "tracking": "disabled",
                "experiment_name": MLFLOW_EXPERIMENT_NAME,
            }
        )


def test_yaml_is_a_direct_pinned_base_dependency() -> None:
    import importlib.metadata
    import tomllib

    from packaging.requirements import Requirement

    dependencies = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["dependencies"]
    yaml_requirements = [
        Requirement(value) for value in dependencies if Requirement(value).name.lower() == "pyyaml"
    ]
    assert len(yaml_requirements) == 1
    assert str(yaml_requirements[0].specifier) == "==6.0.3"
    assert importlib.metadata.version("PyYAML") == "6.0.3"
