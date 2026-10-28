"""Safe native EXP03.1 bundle validation and repository-local publication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes


def validate_bundle(bundle: dict[str, Any]) -> None:
    required = {
        "schema",
        "experiment_id",
        "scientific_id",
        "protocol_sha256",
        "reuse_decision",
        "execution_plan",
        "predictions",
        "thresholds",
        "metrics",
        "diagnostics",
        "execution_counters",
        "G5",
        "champion",
        "synthetic",
    }
    if set(bundle) != required or bundle["schema"] != "exp03-1-scientific-bundle-v1":
        raise ValueError("Invalid EXP03.1 bundle schema")
    if bundle["experiment_id"] != "EXP031" or bundle["scientific_id"] != "EXP03.1":
        raise ValueError("Invalid EXP03.1 identity")
    if bundle["G5"] != "NOT_APPROVED" or bundle["champion"] != "not_selected":
        raise ValueError("EXP03.1 cannot approve G5 or select champion")
    if not bundle["synthetic"]:
        raise PermissionError("Real EXP03.1 publication is not authorized")
    counters = bundle["execution_counters"]
    forbidden = (
        "real_private_reads",
        "real_reservations",
        "real_fits",
        "real_calibrations",
        "real_searches",
        "permanent_mlflow_writes",
    )
    if set(counters) != set(forbidden) or any(counters[name] != 0 for name in forbidden):
        raise ValueError("Real-science counters must remain zero")
    for row in bundle["predictions"]:
        if not {"cell_id", "municipality_code", "target_month", "score", "alert"} <= set(row):
            raise ValueError("Invalid native prediction row")


def write_bundle(bundle: dict[str, Any], path: Path) -> str:
    validate_bundle(bundle)
    root = (Path.cwd() / "tmp").resolve()
    resolved = path.resolve()
    if (
        not resolved.is_relative_to(root)
        or path.exists()
        or any(parent.is_symlink() for parent in [path, *path.parents])
    ):
        raise ValueError("EXP03.1 bundles require a new repository-local tmp path")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(bundle)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def read_bundle(path: Path, expected_sha256: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("EXP03.1 bundle changed")
    value: dict[str, Any] = json.loads(raw)
    validate_bundle(value)
    return value
