"""Resolve reviewed experiment identities without exposing protocol prose to tracking."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes

MLFLOW_EXPERIMENT_NAME = "sat-dengue-bounded-v1"

REGISTRY = Path("docs/product/experiments/experiment-registry.yml")
TAG_PATTERNS = {
    "experiment_id": r"EXP[0-9]{2,6}",
    "experiment_slug": r"[a-z][a-z0-9_]{0,79}",
    "hypothesis_id": r"EXP[0-9]{2,6}-H[0-9]{1,4}",
    "objective_slug": r"[a-z][a-z0-9_]{0,79}",
    "experiment_type": r"[a-z][a-z0-9_]{0,79}",
    "target_definition": r"[a-z][a-z0-9_]{0,79}",
}
ENTRY_FIELDS = {
    "experiment_id",
    "experiment_slug",
    "hypothesis_id",
    "title",
    "objective",
    "experiment_type",
    "pipeline",
    "protocol",
    "protocol_sha256",
    "conclusions",
    "scientific_result",
    "scientific_gate",
    "champion",
    "mlflow_registration",
    "lifecycle_status",
}


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate document key")
        result[key] = value
    return result


class RegistryLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently overwriting them."""


def _mapping(loader: RegistryLoader, node: Any) -> dict[str, Any]:
    return unique_object(
        [(loader.construct_object(k), loader.construct_object(v)) for k, v in node.value]
    )


RegistryLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def safe_document(relative: str) -> Path:
    path = Path(relative)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.is_relative_to(REGISTRY.parent)
        or any(p.is_symlink() for p in (path, *path.parents))
        or not path.resolve().is_relative_to((Path.cwd() / REGISTRY.parent).resolve())
    ):
        raise ValueError("Unsafe experiment document path")
    return path


def conceptual_tags(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != set(TAG_PATTERNS):
        raise ValueError("Conceptual tags require the exact allowlist")
    for name, pattern in TAG_PATTERNS.items():
        text = value[name]
        if (
            not isinstance(text, str)
            or re.fullmatch(pattern, text) is None
            or re.search(r"(?i)(gh[pousr]_|akia|aiza|secret|token|password|private_key)", text)
        ):
            raise ValueError("Unapproved conceptual tag value")
    if not value["hypothesis_id"].startswith(value["experiment_id"] + "-H"):
        raise ValueError("Hypothesis identity mismatch")
    return dict(value)


def resolve_experiment(experiment_id: str) -> dict[str, str]:
    """Validate the whole registry and return only a registered, hash-bound projection."""
    if (
        not isinstance(experiment_id, str)
        or re.fullmatch(TAG_PATTERNS["experiment_id"], experiment_id) is None
    ):
        raise ValueError("Invalid experiment_id")
    registry = yaml.load(safe_document(str(REGISTRY)).read_text(), Loader=RegistryLoader)
    if (
        not isinstance(registry, dict)
        or set(registry) != {"schema", "version", "experiments"}
        or registry["schema"] != "sat-dengue-experiment-registry-v1"
        or registry["version"] != "1.0.0"
        or not isinstance(registry["experiments"], list)
        or not registry["experiments"]
    ):
        raise ValueError("Invalid experiment registry schema")
    seen: set[str] = set()
    paths: set[str] = set()
    selected = None
    for entry in registry["experiments"]:
        if (
            not isinstance(entry, dict)
            or set(entry) != ENTRY_FIELDS
            or any(not isinstance(v, str) or not v for v in entry.values())
        ):
            raise ValueError("Invalid experiment registry entry")
        identifier = entry["experiment_id"]
        if identifier in seen or entry["protocol"] in paths:
            raise ValueError("Duplicate experiment identity or protocol")
        seen.add(identifier)
        paths.add(entry["protocol"])
        path = safe_document(entry["protocol"])
        safe_document(entry["conclusions"])
        if (
            path.name != "protocol.json"
            or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", entry["pipeline"]) is None
        ):
            raise ValueError("Invalid protocol or pipeline")
        protocol = json.loads(path.read_text(), object_pairs_hook=unique_object)
        if (
            not isinstance(protocol, dict)
            or protocol.get("schema") != "sat-dengue-experiment-protocol-v1"
            or protocol.get("version")
            not in (("1.0.0", "2.0.0") if identifier == "EXP03" else ("1.0.0",))
        ):
            raise ValueError("Invalid experiment protocol schema")
        digest = hashlib.sha256(canonical_bytes(protocol)).hexdigest()
        if digest != entry["protocol_sha256"]:
            raise ValueError("Experiment protocol hash mismatch")
        if not isinstance(protocol.get("mlflow"), dict) or not isinstance(
            protocol.get("execution"), dict
        ):
            raise ValueError("Invalid protocol tracking/execution schema")
        mlflow = protocol["mlflow"]
        if set(mlflow) != {"experiment_name", "required_conceptual_tags"}:
            raise ValueError("Invalid protocol MLflow schema")
        if mlflow["experiment_name"] != MLFLOW_EXPERIMENT_NAME:
            raise ValueError("Unapproved MLflow experiment container")
        tags = conceptual_tags(mlflow["required_conceptual_tags"])
        if (
            any(
                tags[k] != entry[k] or protocol.get(k) != entry[k]
                for k in ("experiment_id", "experiment_slug", "hypothesis_id")
            )
            or tags["experiment_type"] != entry["experiment_type"]
            or protocol.get("execution", {}).get("kedro_pipeline") != entry["pipeline"]
        ):
            raise ValueError("Registry and protocol mismatch")
        if identifier == experiment_id:
            selected = {**tags, "protocol_sha256": digest, "pipeline": entry["pipeline"]}
    if selected is None:
        raise ValueError("Unregistered experiment_id")
    return selected
