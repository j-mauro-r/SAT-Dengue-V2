"""Read-only EXP01 infrastructure checks and future human-approval boundary.

Private input contents and MLflow writers are never opened by preflight.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import re
import sqlite3
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sat_dengue.configuration import AUTHORITIES, canonical_bytes, validate_parameters
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, NATIVE_MANIFEST
from sat_dengue.experiments.exp01 import digest, load_protocol
from sat_dengue.tracking.experiments import MLFLOW_EXPERIMENT_NAME, unique_object

OUTPUT_ROOT = "tmp/kedro-migration/exp01-runs"
SOURCE_PATHS = (
    NATIVE_MANIFEST,
    "data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json",
    "data/processed/panel_mensual_dengue_clima.csv",
    "data/processed/dengue_y_dengue_grave.csv",
    "data/interim/stage2_consolidated_dataset_pipeline/y_label_history_traceability.csv",
    "data/interim/stage2_consolidated_dataset_pipeline/current_endemic_channel_traceability.csv",
    "data/sources/Divipola-municipios.md",
)


def safe_path(relative: str, *, temporary: bool = False) -> Path:
    """Reject absolute, parent-traversal and symlink paths before any I/O."""
    path = Path(relative)
    if (
        not relative
        or path.is_absolute()
        or ".." in path.parts
        or (temporary and (len(path.parts) < 2 or path.parts[0] != "tmp"))
        or any(p.is_symlink() for p in (path, *path.parents))
        or not path.resolve().is_relative_to(Path.cwd().resolve())
    ):
        raise ValueError("EXP01 requires repository-local paths without symlinks")
    return path


def source_metadata() -> dict[str, Any]:
    """Stat the declared sources only; never open a private CSV or manifest."""
    records = {}
    for relative in SOURCE_PATHS:
        path = safe_path(relative)
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("Missing or empty EXP01 source: " + relative)
        size = path.stat().st_size
        if relative in NATIVE_IDENTITIES and size != NATIVE_IDENTITIES[relative]["bytes"]:
            raise ValueError("EXP01 source metadata differs from pinned identity")
        records[relative] = {"bytes": size}
    return {"schema": "exp01-source-descriptor-v1", "files": records}


def git_identity() -> dict[str, Any]:
    return {
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
    }


def storage_preflight(root: str) -> dict[str, Any]:
    """Validate ignored storage and existing experiment metadata without creating it."""
    path = safe_path(root, temporary=True)
    if path.exists() and not path.is_dir():
        raise ValueError("MLflow root must be a directory")
    if any(p.is_symlink() for p in path.rglob("*")):
        raise ValueError("MLflow storage contains a symlink")
    for name in ("tracking.sqlite", "artifacts/probe"):
        if subprocess.run(
            ["git", "check-ignore", "-q", "--", str(path / name)], check=False
        ).returncode:
            raise ValueError("MLflow destination must be ignored by Git")
    # Check the closest existing directory without creating an output directory.
    parent = next(p for p in (path, *path.parents) if p.exists())
    if not os.access(parent, os.W_OK):
        raise ValueError("MLflow destination is not writable")
    database = path / "tracking.sqlite"
    state = "not_initialized"
    if database.exists():
        uri = "file:" + quote(str(database.resolve()), safe="/") + "?mode=ro&immutable=1"
        with sqlite3.connect(uri, uri=True) as connection:
            if connection.execute("PRAGMA quick_check").fetchone() != ("ok",):
                raise ValueError("MLflow SQLite integrity check failed")
            rows = connection.execute(
                "SELECT experiment_id, artifact_location, lifecycle_stage FROM experiments "
                "WHERE name = ?",
                (MLFLOW_EXPERIMENT_NAME,),
            ).fetchall()
            expected = "satlocal:/" + quote(str(path / "artifacts"), safe="/")
            if rows and (len(rows) != 1 or rows[0][1:] != (expected, "active")):
                raise ValueError("MLflow experiment destination is inconsistent")
            if rows:
                pinned = connection.execute(
                    "SELECT value FROM experiment_tags WHERE experiment_id = ? AND key = ?",
                    (rows[0][0], "protocol.EXP01"),
                ).fetchone()
                if pinned and pinned[0] != digest(load_protocol()):
                    raise ValueError("MLflow EXP01 protocol pin differs")
            state = "existing_read_only_verified"
    return {"root": root, "state": state, "writes": 0}


def execution_metadata() -> dict[str, Any]:
    """Reuse the foundation's read-only code and installed-runtime inventory."""
    from sat_dengue.datasets import ConfigurationInputsDataset

    execution = ConfigurationInputsDataset().load()["execution"]
    expected = {
        name.removeprefix("src/sat_dengue/"): value
        for name, value in execution["code"].items()
        if name.startswith("src/sat_dengue/")
    }
    if expected != execution["loaded_package_code"]:
        raise ValueError("Installed EXP01 code differs from the reviewed checkout")
    runtime = {key: execution[key] for key in ("python", "packages", "environment")}
    return {
        "code": execution["code"],
        "runtime": runtime,
        "code_sha256": digest(execution["code"]),
        "environment_sha256": digest(runtime),
    }


def runtime_versions() -> dict[str, str]:
    """Check all required direct pins and installed exported transitive pins."""
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("EXP01 requires the frozen Python 3.12 runtime")
    project = tomllib.loads(safe_path("pyproject.toml").read_text())["project"]
    required = project["dependencies"] + [
        pin for extra in ("modeling", "tracking") for pin in project["optional-dependencies"][extra]
    ]
    versions = {"sat-dengue-v2": importlib.metadata.version("sat-dengue-v2")}
    if versions["sat-dengue-v2"] != project["version"]:
        raise ValueError("Installed EXP01 package version differs from project")
    constraints = safe_path("docs/operations/kedro-foundation-constraints.txt").read_text()
    pins = [line for line in constraints.splitlines() if line and not line.startswith("#")]
    for pin in dict.fromkeys([*required, *pins]):
        name, expected = pin.split("==")
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            if pin in required:
                raise RuntimeError(
                    "Future EXP01 requires sat-dengue-v2[modeling,tracking]"
                ) from error
            continue
        if actual != expected:
            raise ValueError("EXP01 runtime dependency differs from frozen pin: " + name)
        versions[name] = actual
    return versions


def materialize_publication_dataset() -> None:
    """Exercise KedroContext's real absolute-path resolution without running nodes."""
    from kedro.framework.session import KedroSession
    from kedro.framework.startup import bootstrap_project

    from sat_dengue.datasets.exp01 import Exp01BundleDataset

    bootstrap_project(Path.cwd())
    session = KedroSession.create(project_path=Path.cwd(), save_on_close=False)
    with session:
        dataset = session.load_context().catalog.get("exp01_bundle")
        if not isinstance(dataset, Exp01BundleDataset):
            raise ValueError("EXP01 publication dataset is incompatible")


def preflight(parameters: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    operational = validate_parameters(parameters)
    if operational not in (
        {"profile": "exp01", "tracking": "enabled", "experiment_id": "EXP01"},
        {"profile": "exp01_preflight", "tracking": "enabled", "experiment_id": "EXP01"},
    ):
        raise ValueError(
            "EXP01 requires its bound profile, enabled tracking and experiment_id=EXP01"
        )
    protocol = load_protocol()
    for relative, expected in protocol["reproducibility"]["authority_sha256"].items():
        if hashlib.sha256(safe_path(relative).read_bytes()).hexdigest() != expected:
            raise ValueError("EXP01 frozen authority changed: " + relative)
    if sources != source_metadata():
        raise ValueError("EXP01 source descriptor changed")
    preparation = json.loads(
        safe_path(AUTHORITIES["training_preparation_contract_v1"]["path"]).read_text()
    )
    if preparation["panel_path"] != SOURCE_PATHS[2]:
        raise ValueError("EXP01 panel path differs from the preparation contract")
    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipeline_registry import register_pipelines

    loader = ValidatedConfigLoader("conf", base_env="base", default_run_env="base")
    catalog = loader["catalog"]
    graph = register_pipelines()["exp01"]
    if graph.inputs() != {"parameters", "exp01_sources"} or not {
        "exp01_sources",
        "exp01_bundle",
    } <= set(catalog):
        raise ValueError("EXP01 catalog/graph binding is incomplete")
    materialize_publication_dataset()
    versions = runtime_versions()
    metadata = execution_metadata()
    output = safe_path(OUTPUT_ROOT, temporary=True)
    root = os.environ.get("SAT_DENGUE_TRACKING_ROOT", "")
    storage = storage_preflight(root)
    if output.resolve().is_relative_to(Path(root).resolve()) or Path(root).resolve().is_relative_to(
        output.resolve()
    ):
        raise ValueError("EXP01 result and tracking roots must be separate")
    return {
        "schema": "exp01-preflight-v1",
        "status": "structural_pass",
        "execution_ready": False,
        "purpose": "infrastructure_validation_only",
        "protocol_sha256": digest(protocol),
        "data_version": NATIVE_IDENTITIES[NATIVE_MANIFEST]["sha256"],
        "configuration_sha256": digest(
            {"protocol": protocol, "catalog": catalog, "versions": versions, "metadata": metadata}
        ),
        **git_identity(),
        "sources": sources,
        "tracking": storage,
        "output_root": OUTPUT_ROOT,
        "versions": versions,
        **metadata,
        "historical_predictions": "incompatible_refit_required_no_reuse",
        "operational_reference": "fixed_stage4_persistence_same_non_excess_cohort",
        "pending": [
            "protocol_commit_data_bound_human_and_independent_reviewer_approval",
            "private_input_hash_schema_and_cohort_validation_after_authorization",
            "retrospective_predictor_availability_acknowledgement",
            "36_new_paired_model_and_36_calibrator_fits_in_future_authorized_run",
        ],
        "real_model_fits": 0,
        "calibrator_fits": 0,
        "real_execution_started": False,
        "mlflow_writes": 0,
    }


def authorize(receipt: dict[str, Any]) -> dict[str, Any]:
    """A later explicit review record is required before source reads or MLflow writes.

    This is an auditable local approval record, not cryptographic authentication.
    Its creation is a human action; infrastructure never generates an approval.
    """
    relative = os.environ.get("SAT_DENGUE_EXP01_APPROVAL", "")
    if not relative:
        raise PermissionError(
            "EXP01 real execution requires separate human authorization "
            "via SAT_DENGUE_EXP01_APPROVAL"
        )
    path = safe_path(relative, temporary=True)
    approval = json.loads(path.read_text(), object_pairs_hook=unique_object)
    required = {
        "schema",
        "experiment_id",
        "protocol_sha256",
        "git_revision",
        "data_version",
        "configuration_sha256",
        "authority",
        "independent_reviewer",
        "real_execution_authorized",
        "retrospective_availability_acknowledged",
        "comparator_refit_authorized",
    }
    if not isinstance(approval, dict) or set(approval) != required:
        raise PermissionError("Invalid EXP01 approval schema")
    if (
        approval["schema"] != "exp01-execution-approval-v1"
        or approval["experiment_id"] != "EXP01"
        or approval["authority"] != "Mauricio"
        or not isinstance(approval["independent_reviewer"], str)
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,79}", approval["independent_reviewer"]) is None
        or approval["independent_reviewer"] == "Mauricio"
        or any(
            approval[name] is not True
            for name in (
                "real_execution_authorized",
                "retrospective_availability_acknowledged",
                "comparator_refit_authorized",
            )
        )
        or any(
            approval[name] != receipt[name]
            for name in ("protocol_sha256", "git_revision", "data_version", "configuration_sha256")
        )
        or receipt["git_dirty"]
        or git_identity() != {"git_revision": receipt["git_revision"], "git_dirty": False}
        or digest(load_protocol()) != receipt["protocol_sha256"]
        or any(
            execution_metadata()[name] != receipt[name]
            for name in ("code_sha256", "environment_sha256")
        )
    ):
        raise PermissionError(
            "EXP01 approval is stale, incomplete or not bound to a clean reviewed commit"
        )
    return approval


def main() -> None:
    """Print a no-fit preflight receipt; no implicit real execution option."""
    from sat_dengue.config_loader import ValidatedConfigLoader

    loader = ValidatedConfigLoader("conf", base_env="base", default_run_env="base")
    loader["catalog"]
    receipt = preflight(
        {"profile": "exp01_preflight", "tracking": "enabled", "experiment_id": "EXP01"},
        source_metadata(),
    )
    print(canonical_bytes(receipt).decode(), end="")


if __name__ == "__main__":
    main()
