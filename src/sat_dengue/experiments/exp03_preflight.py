"""Read-only EXP03 graph/runtime checks and separately bound human authorization."""

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
from sat_dengue.experiments.exp03 import load_protocol
from sat_dengue.tracking.experiments import unique_object

OUTPUT_ROOT = "tmp/kedro-migration/exp03-runs"
TRACKING_ROOT = "tmp/kedro-migration/replay-mlflow"  # Documented choice, not an implicit access.


def tracking_root() -> str:
    root = os.environ.get("SAT_DENGUE_TRACKING_ROOT", "")
    if not root:
        raise ValueError("EXP03 requires explicit SAT_DENGUE_TRACKING_ROOT")
    resolved = safe_path(root)
    output = safe_path(OUTPUT_ROOT, OUTPUT_ROOT)
    if resolved.is_relative_to(output) or output.is_relative_to(resolved):
        raise ValueError("EXP03 result and tracking roots must be separate")
    return root


def safe_path(value: str, canonical: str | None = None) -> Path:
    """Accept Kedro absolute resolution only when equivalent to canonical local path."""
    if not value or "://" in value or ".." in Path(value).parts:
        raise ValueError("Unsafe EXP03 path")
    path = Path(value)
    absolute = path if path.is_absolute() else Path.cwd() / path
    if any(p.is_symlink() for p in (absolute, *absolute.parents)):
        raise ValueError("Symlink EXP03 path")
    resolved = absolute.resolve()
    root = Path.cwd().resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("External EXP03 path")
    if canonical is not None and resolved != root / canonical:
        raise ValueError("Noncanonical EXP03 path")
    return resolved


def descriptor() -> dict[str, Any]:
    # Declared inventory, not private file existence/content. Missing sources are
    # checked only AFTER authorization. No stat/hash of private inputs here.
    return {
        "schema": "exp03-source-descriptor-v1",
        "declared_paths": list(SOURCE_PATHS),
        "private_reads": 0,
    }


def preflight(parameters: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipeline_registry import register_pipelines

    p = load_protocol()
    from sat_dengue.experiments.exp03_features import validate_design

    expected = validate_design(p["design"])
    operational = validate_parameters(parameters)
    if operational not in (
        {"profile": profile, "tracking": "enabled", "experiment_id": "EXP03"}
        for profile in ("exp03", "exp03_preflight")
    ):
        raise ValueError("EXP03 profile and tracking binding required")
    if sources != descriptor():
        raise ValueError("Source descriptor mismatch")
    for relative, sha in p["reproducibility"]["authority_sha256"].items():
        if hashlib.sha256(safe_path(relative).read_bytes()).hexdigest() != sha:
            raise ValueError("Scientific authority changed")
    catalog = ValidatedConfigLoader("conf", base_env="base", default_run_env="base")["catalog"]
    from kedro.io import DataCatalog

    materialized = DataCatalog.from_config(catalog)
    # Force real Kedro absolute-path construction without loading private data.
    materialized.get("exp03_sources")
    materialized.get("exp03_bundle")
    graph = register_pipelines()["exp03"]
    if graph.inputs() != {"parameters", "exp03_sources"}:
        raise ValueError("Unexpected EXP03 graph input")
    versions = runtime_versions()
    metadata = execution_metadata()
    safe_path(OUTPUT_ROOT, OUTPUT_ROOT)
    root = tracking_root()
    storage = storage_preflight(root)
    database = safe_path(root) / "tracking.sqlite"
    if database.exists():
        uri = "file:" + quote(str(database), safe="/") + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as connection:
            pins = connection.execute(
                "SELECT t.value FROM experiment_tags t JOIN experiments e "
                "ON t.experiment_id = e.experiment_id WHERE e.name = ? AND t.key = ?",
                ("sat-dengue-bounded-v1", "protocol.EXP03"),
            ).fetchall()
            if any(value != digest(p) for (value,) in pins):
                raise ValueError("Stored EXP03 protocol changed")
    return {
        "schema": "exp03-preflight-v2",
        "revision": p["design"]["revision"],
        "B_primary": p["design"]["B_primary"],
        "budget_status": "pending" if p["design"]["B_primary"] is None else "specified",
        "execution_ready": False,
        "experiment_id": "EXP03",
        "protocol_sha256": digest(p),
        "configuration_sha256": digest(
            {
                "design": p["design"],
                "catalog": catalog,
                "versions": versions,
                "tracking_root": root,
                **metadata,
            }
        ),
        "data_version": NATIVE_IDENTITIES[NATIVE_MANIFEST]["sha256"],
        "sources": sources,
        "versions": versions,
        **metadata,
        **git_identity(),
        "tracking": storage,
        "output_root": OUTPUT_ROOT,
        "expected_children": expected,
        "expected_model_fits": expected,
        "expected_calibrator_fits": expected,
        "real_model_fits": 0,
        "calibrator_fits": 0,
        "private_reads": 0,
        "reservations": 0,
        "mlflow_writes": 0,
        "writes": 0,
    }


def authorize(receipt: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_engine import require_budget

    protocol = load_protocol()
    require_budget(protocol["design"])
    if receipt.get("protocol_sha256") != digest(protocol):
        raise PermissionError("EXP03 authorization protocol mismatch")
    value = os.environ.get("SAT_DENGUE_EXP03_APPROVAL", "")
    if not value:
        raise PermissionError("EXP03 requires independent SAT_DENGUE_EXP03_APPROVAL")
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
        or approval["schema"] != "exp03-execution-approval-v2"
        or approval["experiment_id"] != "EXP03"
        or approval["authority"] != "Mauricio"
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,79}", str(approval["independent_reviewer"]))
        or approval["independent_reviewer"] == "Mauricio"
        or any(approval[k] is not True for k in flags)
        or any(approval[k] != receipt[k] for k in bound)
    ):
        raise PermissionError("Invalid EXP03 authorization")
    fresh = preflight(
        {"profile": "exp03", "tracking": "enabled", "experiment_id": "EXP03"}, descriptor()
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
        raise PermissionError("Stale EXP03 authorization or dirty commit")
    return approval


def main() -> None:
    print(
        canonical_bytes(
            preflight(
                {"profile": "exp03_preflight", "tracking": "enabled", "experiment_id": "EXP03"},
                descriptor(),
            )
        ).decode(),
        end="",
    )


if __name__ == "__main__":
    main()
