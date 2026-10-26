"""Read-only EXP02 graph/runtime checks and separately bound human authorization."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, NATIVE_MANIFEST
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp01_preflight import (
    SOURCE_PATHS,
    execution_metadata,
    git_identity,
    runtime_versions,
    storage_preflight,
)
from sat_dengue.experiments.exp02 import load_protocol
from sat_dengue.tracking.experiments import unique_object

OUTPUT_ROOT = "tmp/kedro-migration/exp02-runs"
TRACKING_ROOT = "tmp/kedro-migration/exp02-mlflow"


def safe_path(value: str, canonical: str | None = None) -> Path:
    """Accept Kedro absolute resolution only when equivalent to canonical local path."""
    if not value or "://" in value or ".." in Path(value).parts:
        raise ValueError("Unsafe EXP02 path")
    path = Path(value)
    absolute = path if path.is_absolute() else Path.cwd() / path
    if any(p.is_symlink() for p in (absolute, *absolute.parents)):
        raise ValueError("Symlink EXP02 path")
    resolved = absolute.resolve()
    root = Path.cwd().resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("External EXP02 path")
    if canonical is not None and resolved != root / canonical:
        raise ValueError("Noncanonical EXP02 path")
    return resolved


def descriptor() -> dict[str, Any]:
    # Declared inventory, not private file existence/content. Missing sources are
    # checked only AFTER authorization. No stat/hash of private inputs here.
    return {
        "schema": "exp02-source-descriptor-v1",
        "declared_paths": list(SOURCE_PATHS),
        "private_reads": 0,
    }


def preflight(parameters: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipeline_registry import register_pipelines

    p = load_protocol()
    operational = validate_parameters(parameters)
    if operational not in (
        {"profile": profile, "tracking": "enabled", "experiment_id": "EXP02"}
        for profile in ("exp02", "exp02_preflight")
    ):
        raise ValueError("EXP02 profile and tracking binding required")
    if sources != descriptor():
        raise ValueError("Source descriptor mismatch")
    for relative, sha in p["reproducibility"]["authority_sha256"].items():
        if hashlib.sha256(safe_path(relative).read_bytes()).hexdigest() != sha:
            raise ValueError("Scientific authority changed")
    catalog = ValidatedConfigLoader("conf", base_env="base", default_run_env="base")["catalog"]
    from kedro.io import DataCatalog

    materialized = DataCatalog.from_config(catalog)
    # Force real Kedro absolute-path construction without loading private data.
    materialized.get("exp02_sources")
    materialized.get("exp02_bundle")
    graph = register_pipelines()["exp02"]
    if graph.inputs() != {"parameters", "exp02_sources"}:
        raise ValueError("Unexpected EXP02 graph input")
    versions = runtime_versions()
    metadata = execution_metadata()
    safe_path(OUTPUT_ROOT, OUTPUT_ROOT)
    safe_path(TRACKING_ROOT, TRACKING_ROOT)
    storage = storage_preflight(TRACKING_ROOT)
    database = safe_path(TRACKING_ROOT) / "tracking.sqlite"
    if database.exists():
        uri = "file:" + quote(str(database), safe="/") + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as connection:
            pins = connection.execute(
                "SELECT value FROM experiment_tags WHERE key = ?", ("protocol.EXP02",)
            ).fetchall()
            if any(value != digest(p) for (value,) in pins):
                raise ValueError("Stored EXP02 protocol changed")
    return {
        "schema": "exp02-preflight-v1",
        "execution_ready": False,
        "experiment_id": "EXP02",
        "protocol_sha256": digest(p),
        "configuration_sha256": digest(
            {"design": p["design"], "catalog": catalog, "versions": versions, **metadata}
        ),
        "data_version": NATIVE_IDENTITIES[NATIVE_MANIFEST]["sha256"],
        "sources": sources,
        "versions": versions,
        **metadata,
        **git_identity(),
        "tracking": storage,
        "output_root": OUTPUT_ROOT,
        "expected_children": 108,
        "expected_model_fits": 108,
        "expected_calibrator_fits": 108,
        "real_model_fits": 0,
        "calibrator_fits": 0,
        "private_reads": 0,
        "reservations": 0,
        "mlflow_writes": 0,
        "writes": 0,
    }


def authorize(receipt: dict[str, Any]) -> dict[str, Any]:
    value = os.environ.get("SAT_DENGUE_EXP02_APPROVAL", "")
    if not value:
        raise PermissionError("EXP02 requires independent SAT_DENGUE_EXP02_APPROVAL")
    path = safe_path(value)
    if not path.is_relative_to(Path.cwd().resolve() / "tmp"):
        raise PermissionError("Approval must be repository tmp record")
    approval = json.loads(path.read_text(), object_pairs_hook=unique_object)
    bound = ("protocol_sha256", "git_revision", "data_version", "configuration_sha256")
    flags = (
        "real_execution_authorized",
        "comparator_refit_authorized",
        "variant_refits_authorized",
        "retrospective_availability_acknowledged",
    )
    required = {"schema", "experiment_id", "authority", "independent_reviewer", *bound, *flags}
    if (
        set(approval) != required
        or approval["schema"] != "exp02-execution-approval-v1"
        or approval["experiment_id"] != "EXP02"
        or approval["authority"] != "Mauricio"
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,79}", str(approval["independent_reviewer"]))
        or approval["independent_reviewer"] == "Mauricio"
        or any(approval[k] is not True for k in flags)
        or any(approval[k] != receipt[k] for k in bound)
    ):
        raise PermissionError("Invalid EXP02 authorization")
    fresh = preflight(
        {"profile": "exp02", "tracking": "enabled", "experiment_id": "EXP02"}, descriptor()
    )
    # The dedicated writer may initialize its previously absent SQLite store.
    # All other receipt fields (including exact root) must remain identical.
    if receipt["tracking"]["state"] not in {"not_initialized", "existing_read_only_verified"}:
        raise PermissionError("Invalid tracking preflight state")
    prior_state = receipt["tracking"]["state"]
    current_state = fresh["tracking"]["state"]
    if current_state != prior_state and (prior_state, current_state) != (
        "not_initialized",
        "existing_read_only_verified",
    ):
        raise PermissionError("Tracking store disappeared or changed state")
    normalized = {**fresh, "tracking": {**fresh["tracking"], "state": receipt["tracking"]["state"]}}
    if normalized != receipt or receipt["git_dirty"] or git_identity()["git_dirty"]:
        raise PermissionError("Stale EXP02 authorization or dirty commit")
    return approval


def main() -> None:
    print(
        canonical_bytes(
            preflight(
                {"profile": "exp02_preflight", "tracking": "enabled", "experiment_id": "EXP02"},
                descriptor(),
            )
        ).decode(),
        end="",
    )


if __name__ == "__main__":
    main()
