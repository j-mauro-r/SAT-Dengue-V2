"""EXP03.1 structural preflight and separately bound execution authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import load_protocol as load_exp03_protocol
from sat_dengue.experiments.exp03_preflight import (
    OUTPUT_ROOT as EXP03_OUTPUT_ROOT,
    descriptor as exp03_descriptor,
    safe_path as exp03_safe_path,
    tracking_root as exp03_tracking_root,
)
from sat_dengue.experiments.exp03_1_contract import MATRIX, PROTOCOL, counts, matrix, protocol
from sat_dengue.tracking.experiments import unique_object

OUTPUT_ROOT = "tmp/kedro-migration/exp03-1-runs"
APPROVAL_ENV = "SAT_DENGUE_EXP03_1_APPROVAL"
APPROVAL_SCHEMA = "exp03-1-execution-approval-v1"


def source_descriptor() -> dict[str, Any]:
    """Reuse EXP03's pinned source inventory without inspecting source files."""
    parent = exp03_descriptor()
    return {
        "schema": "exp03-1-source-descriptor-v1",
        "parent_descriptor": parent,
        "coverage_field": "in_epi_coverage",
        "coverage_key": ["municipality_code", "year_month"],
        "coverage_policy": "explicit_boolean_only_unknown_is_unknown",
        "private_reads": 0,
    }


def _tracking_root() -> str:
    root = exp03_tracking_root()
    path = Path(root)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not root.startswith("tmp/")
        or root == OUTPUT_ROOT
        or root.startswith(OUTPUT_ROOT + "/")
    ):
        raise ValueError("EXP03.1 tracking requires a separate repository-local tmp root")
    return root


def _git_identity() -> dict[str, Any]:
    return {
        "git_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
    }


def _source_code_identity() -> dict[str, str]:
    paths = [
        *Path("src/sat_dengue/experiments").glob("exp03_1*.py"),
        Path("src/sat_dengue/experiments/exp03.py"),
        Path("src/sat_dengue/experiments/exp03_admission.py"),
        Path("src/sat_dengue/experiments/exp03_features.py"),
        Path("src/sat_dengue/experiments/exp03_persistence.py"),
        Path("src/sat_dengue/experiments/exp03_revision.py"),
        Path("src/sat_dengue/experiments/exp03_preflight.py"),
        Path("src/sat_dengue/experiments/exp01_preflight.py"),
        Path("src/sat_dengue/experiments/exp01_inputs.py"),
        Path("src/sat_dengue/experiments/onset.py"),
        Path("src/sat_dengue/datasets/exp03_1.py"),
        Path("src/sat_dengue/datasets/stage2.py"),
        Path("src/sat_dengue/datasets/legacy_preparation/pipeline.py"),
        Path("src/sat_dengue/model_training/candidate_families.py"),
        Path("src/sat_dengue/model_training/candidate_preparation.py"),
        Path("src/sat_dengue/model_training/gam_adapter.py"),
        Path("src/sat_dengue/model_training/lightgbm_adapter.py"),
        Path("src/sat_dengue/model_training/xgboost_adapter.py"),
        Path("src/sat_dengue/model_evaluation/calibration.py"),
        Path("src/sat_dengue/training_preparation/preprocessing.py"),
        Path("src/sat_dengue/tracking/exp03_1.py"),
        Path("src/sat_dengue/tracking/local.py"),
        Path("src/sat_dengue/tracking/experiments.py"),
        Path("src/sat_dengue/configuration.py"),
        Path("src/sat_dengue/config_loader.py"),
        Path("src/sat_dengue/settings.py"),
        Path("src/sat_dengue/pipeline_registry.py"),
        Path("conf/base/catalog.yml"),
        Path("docs/product/experiments/experiment-registry.yml"),
    ]
    return {
        path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(set(paths))
        if path.is_file()
    }


def _validate_frozen_documents() -> tuple[dict[str, Any], dict[str, Any]]:
    p = json.loads(PROTOCOL.read_text(), object_pairs_hook=unique_object)
    m = yaml.safe_load(MATRIX.read_text())
    canonical = protocol()
    if p != canonical:
        raise ValueError("EXP03.1 frozen protocol differs from its canonical contract")
    if m != matrix(canonical):
        raise ValueError("EXP03.1 frozen matrix differs from its canonical contract")
    parent = load_exp03_protocol()
    if p["parent_experiment"]["protocol_sha256"] != digest(parent):
        raise ValueError("EXP03 V09 reference protocol identity changed")
    return p, m


def preflight(parameters: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    """Create a read-only receipt; source contents are not read here."""
    if (
        set(parameters) != {"profile", "tracking", "experiment_id"}
        or parameters["profile"] not in {"exp03_1", "exp03_1_preflight"}
        or parameters["tracking"] != "enabled"
        or parameters["experiment_id"] != "EXP031"
    ):
        raise ValueError("EXP03.1 profile, tracking and experiment binding required")
    if sources != source_descriptor():
        raise ValueError("EXP03.1 source descriptor mismatch")
    p, matrix = _validate_frozen_documents()
    safe = exp03_safe_path
    safe(OUTPUT_ROOT, OUTPUT_ROOT)
    output = Path(OUTPUT_ROOT)
    if output.exists() and not output.is_dir():
        raise ValueError("EXP03.1 result root must be a directory")
    root = _tracking_root()
    from sat_dengue.experiments.exp01_preflight import storage_preflight

    tracking = storage_preflight(root, experiment_id="EXP031", protocol_sha256=digest(p))
    pipeline = __import__(
        "sat_dengue.pipeline_registry", fromlist=["register_pipelines"]
    ).register_pipelines()["exp03_1"]
    if pipeline.inputs() != {"parameters", "exp03_1_sources"}:
        raise ValueError("Unexpected EXP03.1 pipeline inputs")
    identity = {
        "protocol_sha256": digest(p),
        "matrix_sha256": digest(matrix),
        "source_descriptor_sha256": digest(sources),
        "parent_protocol_sha256": p["parent_experiment"]["protocol_sha256"],
        "configuration_sha256": digest(
            {
                "protocol": p,
                "matrix": matrix,
                "source_descriptor": sources,
                "tracking_root": root,
                "output_root": OUTPUT_ROOT,
            }
        ),
        "data_version": sources["parent_descriptor"]["expected_source_sha256"],
        "code_sha256": digest(_source_code_identity()),
        **_git_identity(),
    }
    return {
        "schema": "exp03-1-preflight-v1",
        "status": "structural_pass",
        "experiment_id": "EXP031",
        "execution_ready": False,
        "source_identity_status": "pending_authorized_verification",
        "sources": sources["parent_descriptor"],
        **identity,
        "tracking": tracking,
        "tracking_root": root,
        "output_root": OUTPUT_ROOT,
        "expected_cells": counts(p)["maximum_refit_cells"],
        "real_private_reads": 0,
        "real_reservations": 0,
        "real_model_fits": 0,
        "real_calibrator_fits": 0,
        "real_threshold_selections": 0,
        "mlflow_writes": 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }


def authorize(receipt: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Verify explicit human execution approval before any source access."""
    current = preflight(parameters, source_descriptor())
    if receipt != current:
        raise PermissionError("Stale or altered EXP03.1 preflight receipt")
    if receipt["git_dirty"]:
        raise PermissionError("EXP03.1 authorization requires a clean reviewed revision")
    approval_value = os.environ.get(APPROVAL_ENV, "")
    if not approval_value:
        raise PermissionError(f"EXP03.1 requires {APPROVAL_ENV}")
    path = exp03_safe_path(approval_value)
    if not path.is_relative_to(Path.cwd().resolve() / "tmp"):
        raise PermissionError("EXP03.1 approval must be a repository-local tmp record")
    approval = json.loads(path.read_text(), object_pairs_hook=unique_object)
    bound = (
        "protocol_sha256",
        "matrix_sha256",
        "source_descriptor_sha256",
        "configuration_sha256",
        "data_version",
        "git_revision",
    )
    flags = (
        "real_execution_authorized",
        "m00_refit_authorized",
        "variant_refits_authorized",
        "retrospective_availability_acknowledged",
    )
    required = {
        "schema",
        "experiment_id",
        "authority",
        "independent_reviewer",
        "preflight_sha256",
        *bound,
        *flags,
        "G5_approval",
        "champion_selection",
    }
    if (
        not isinstance(approval, dict)
        or set(approval) != required
        or approval["schema"] != APPROVAL_SCHEMA
        or approval["experiment_id"] != "EXP031"
        or approval["authority"] != "Mauricio"
        or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,79}", approval["independent_reviewer"])
        or approval["independent_reviewer"] == "Mauricio"
        or approval["preflight_sha256"] != digest(receipt)
        or any(approval[name] != receipt[name] for name in bound)
        or any(approval[name] is not True for name in flags)
        or approval["G5_approval"] is not False
        or approval["champion_selection"] is not False
    ):
        raise PermissionError("Invalid or altered EXP03.1 execution approval")
    return approval


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    destination = exp03_safe_path(str(args.output))
    if not destination.is_relative_to(Path.cwd().resolve() / "tmp") or destination.exists():
        raise ValueError("EXP03.1 preflight output requires a new repository-local tmp path")
    value = preflight(
        {"profile": "exp03_1_preflight", "tracking": "enabled", "experiment_id": "EXP031"},
        source_descriptor(),
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(canonical_bytes(value))
    print(destination)


if __name__ == "__main__":
    main()
