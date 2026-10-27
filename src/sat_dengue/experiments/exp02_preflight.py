"""Metadata-only EXP02 checks and explicit, identity-bound future authorization."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, NATIVE_MANIFEST
from sat_dengue.experiments import exp01_preflight as shared
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp01_preflight import (
    execution_metadata,
    git_identity,
    runtime_versions,
    safe_path,
)
from sat_dengue.tracking.experiments import resolve_experiment, unique_object

PROTOCOL_PATH = "docs/product/experiments/EXP02_label_stability/protocol.json"
OUTPUT_ROOT = "tmp/kedro-migration/exp02-runs"
BINDINGS = (
    "git_revision",
    "protocol_sha256",
    "data_version",
    "configuration_sha256",
    "code_sha256",
    "environment_sha256",
    "tracking_root",
    "output_root",
)


def load_protocol() -> dict[str, Any]:
    protocol: dict[str, Any] = json.loads(
        safe_path(PROTOCOL_PATH).read_text(), object_pairs_hook=unique_object
    )
    if resolve_experiment("EXP02")["protocol_sha256"] != digest(protocol):
        raise ValueError("EXP02 registry/protocol identity mismatch")
    for relative, expected in protocol["reproducibility"]["authority_sha256"].items():
        if hashlib.sha256(safe_path(relative).read_bytes()).hexdigest() != expected:
            raise ValueError("EXP02 frozen authority changed")
    return protocol


def source_metadata() -> dict[str, Any]:
    descriptor = shared.source_metadata()
    files = {}
    for relative, record in descriptor["files"].items():
        stat = safe_path(relative).stat()
        files[relative] = {
            **record,
            "mtime_ns": stat.st_mtime_ns,
            "ctime_ns": stat.st_ctime_ns,
            "inode": stat.st_ino,
        }
    return {"schema": "exp02-source-metadata-v1", "files": files}


def storage_preflight(root: str) -> dict[str, Any]:
    output = safe_path(OUTPUT_ROOT, temporary=True)
    path = safe_path(root, temporary=True)
    if path.resolve().is_relative_to(output.resolve()) or output.resolve().is_relative_to(
        path.resolve()
    ):
        raise ValueError("EXP02 publication and tracking roots must be separate")
    if output.exists() and not output.is_dir():
        raise ValueError("EXP02 publication root must be a directory")
    parent = next(p for p in (output, *output.parents) if p.exists())
    if (
        not os.access(parent, os.W_OK)
        or subprocess.run(
            ["git", "check-ignore", "-q", "--", str(output / ".publish.lock")], check=False
        ).returncode
    ):
        raise ValueError("EXP02 publication root must be writable and ignored")
    storage = shared.storage_preflight(
        root, experiment_id="EXP02", protocol_sha256=digest(load_protocol())
    )
    if any(p.is_symlink() for p in output.rglob("*")):
        raise ValueError("EXP02 publication contains symlinks")
    return storage


def configuration_identity(
    protocol: dict[str, Any],
    metadata: dict[str, Any],
    versions: dict[str, str],
    sources: dict[str, Any],
    root: str,
) -> str:
    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipeline_registry import register_pipelines

    catalog = ValidatedConfigLoader("conf", base_env="base", default_run_env="base")["catalog"]
    graph = register_pipelines()["exp02"]
    if graph.inputs() != {"parameters", "exp02_sources"} or graph.outputs() != {"exp02_bundle"}:
        raise ValueError("EXP02 graph binding differs")
    nodes = [
        {
            "name": n.name,
            "inputs": n.inputs,
            "outputs": n.outputs,
            "function": n.func.__module__ + "." + n.func.__qualname__,
        }
        for n in graph.nodes
    ]
    return digest(
        {
            "protocol": protocol,
            "catalog": catalog,
            "graph": nodes,
            "versions": versions,
            "metadata": metadata,
            "sources": sources,
            "tracking_root": root,
            "output_root": OUTPUT_ROOT,
        }
    )


def materialize_publication_dataset() -> None:
    from kedro.framework.session import KedroSession
    from kedro.framework.startup import bootstrap_project

    from sat_dengue.datasets.exp02 import Exp02BundleDataset

    bootstrap_project(Path.cwd())
    session = KedroSession.create(project_path=Path.cwd(), save_on_close=False)
    with session:
        if not isinstance(session.load_context().catalog.get("exp02_bundle"), Exp02BundleDataset):
            raise ValueError("EXP02 publication dataset is incompatible")


def preflight(parameters: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    operational = validate_parameters(parameters)
    if operational not in [
        {"profile": p, "tracking": "enabled", "experiment_id": "EXP02"}
        for p in ("exp02", "exp02_preflight")
    ]:
        raise ValueError("EXP02 requires its exact profile and enabled tracking")
    git = git_identity()
    if git["git_dirty"]:
        raise ValueError("EXP02 requires a clean committed checkout")
    protocol = load_protocol()
    if sources != source_metadata():
        raise ValueError("EXP02 source metadata changed")
    metadata, versions = execution_metadata(), runtime_versions()
    root = os.environ.get("SAT_DENGUE_TRACKING_ROOT", "")
    storage = storage_preflight(root)
    configuration = configuration_identity(protocol, metadata, versions, sources, root)
    materialize_publication_dataset()
    return {
        "schema": "exp02-preflight-v1",
        "status": "structural_pass",
        "execution_ready": False,
        **git,
        **metadata,
        "versions": versions,
        "sources": sources,
        "protocol_sha256": digest(protocol),
        "data_version": NATIVE_IDENTITIES[NATIVE_MANIFEST]["sha256"],
        "data_identity_mode": "pinned_manifest_and_metadata_content_verified_after_authorization",
        "configuration_sha256": configuration,
        "tracking_root": root,
        "tracking": storage,
        "output_root": OUTPUT_ROOT,
        "real_model_fits": 0,
        "calibrator_fits": 0,
        "mlflow_writes": 0,
        "real_execution_started": False,
        "pending": [
            "explicit_human_and_independent_execution_approval",
            "private_content_admission_after_authorization",
        ],
    }


def authorize(receipt: dict[str, Any]) -> dict[str, Any]:
    """Validate a human-created record; never generate one or open private contents."""
    relative = os.environ.get("SAT_DENGUE_EXP02_APPROVAL", "")
    if not relative:
        raise PermissionError(
            "EXP02 requires separate human authorization via SAT_DENGUE_EXP02_APPROVAL"
        )
    approval = json.loads(
        safe_path(relative, temporary=True).read_text(), object_pairs_hook=unique_object
    )
    booleans = (
        "real_execution_authorized",
        "independent_reviewer_approved",
        "retrospective_availability_acknowledged",
        "refits_authorized",
    )
    required = {
        "schema",
        "experiment_id",
        "authority",
        "independent_reviewer",
        "max_model_fits",
        "max_calibrator_fits",
        *booleans,
        *BINDINGS,
    }
    if not isinstance(approval, dict) or set(approval) != required:
        raise PermissionError("Invalid EXP02 approval schema")
    reviewer = approval["independent_reviewer"]
    if (
        approval["schema"] != "exp02-execution-approval-v1"
        or approval["experiment_id"] != "EXP02"
        or approval["authority"] != "Mauricio"
        or not isinstance(reviewer, str)
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,79}", reviewer) is None
        or reviewer == "Mauricio"
        or any(approval[k] is not True for k in booleans)
        or any(
            type(approval[k]) is not int or approval[k] != 54
            for k in ("max_model_fits", "max_calibrator_fits")
        )
        or any(approval[k] != receipt.get(k) for k in BINDINGS)
        or receipt.get("schema") != "exp02-preflight-v1"
        or receipt.get("status") != "structural_pass"
        or receipt.get("execution_ready") is not False
        or receipt.get("git_dirty") is not False
    ):
        raise PermissionError("EXP02 approval is incomplete or differs from preflight")
    protocol, metadata, versions = load_protocol(), execution_metadata(), runtime_versions()
    sources, root = source_metadata(), os.environ.get("SAT_DENGUE_TRACKING_ROOT", "")
    safe_path(root, temporary=True)
    safe_path(OUTPUT_ROOT, temporary=True)
    if (
        git_identity() != {"git_revision": receipt["git_revision"], "git_dirty": False}
        or digest(protocol) != receipt["protocol_sha256"]
        or receipt["data_version"] != NATIVE_IDENTITIES[NATIVE_MANIFEST]["sha256"]
        or root != receipt["tracking_root"]
        or receipt["output_root"] != OUTPUT_ROOT
        or sources != receipt["sources"]
        or versions != receipt["versions"]
        or any(metadata[k] != receipt[k] for k in metadata)
        or configuration_identity(protocol, metadata, versions, sources, root)
        != receipt["configuration_sha256"]
    ):
        raise PermissionError(
            "EXP02 authorization is stale: commit, inputs, configuration, "
            "code, runtime or roots changed"
        )
    return approval


def main() -> None:
    print(
        canonical_bytes(
            preflight(
                {"profile": "exp02_preflight", "tracking": "enabled", "experiment_id": "EXP02"},
                source_metadata(),
            )
        ).decode(),
        end="",
    )


if __name__ == "__main__":
    main()
