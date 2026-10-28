"""Safe native EXP03.1 bundle validation and repository-local publication."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes


def validate_bundle(bundle: dict[str, Any]) -> None:
    from sat_dengue.experiments.exp03_1_contract import counts, digest, protocol
    from sat_dengue.experiments.exp03_1_engine import execution_plan

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
    if bundle["protocol_sha256"] != digest(protocol()):
        raise ValueError("EXP03.1 protocol identity changed")
    if bundle["G5"] != "NOT_APPROVED" or bundle["champion"] != "not_selected":
        raise ValueError("EXP03.1 cannot approve G5 or select champion")
    if bundle["synthetic"] is not True:
        raise PermissionError("Real EXP03.1 publication is not authorized")
    decision = bundle["reuse_decision"].get("decision")
    expected_counts = counts()
    expected_execution = (
        {
            "total": expected_counts["maximum_refit_cells"],
            "reused": expected_counts["maximum_reused_m00_cells"],
            "new_fits": expected_counts["maximum_new_fit_cells_with_complete_reuse"],
        }
        if decision == "reused"
        else {
            "total": expected_counts["maximum_refit_cells"],
            "reused": 0,
            "new_fits": expected_counts["maximum_refit_cells"],
        }
        if decision == "refitted"
        else None
    )
    execution = bundle["execution_plan"]
    if (
        expected_execution is None
        or execution.get("counts") != expected_execution
        or execution.get("searches") != 0
        or len(execution.get("cells", ())) != expected_execution["total"]
        or execution != execution_plan(bundle["reuse_decision"])
    ):
        raise ValueError("Invalid EXP03.1 execution plan")
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
    prediction_keys = []
    cell_ids = set()
    for row in bundle["predictions"]:
        if not {"cell_id", "municipality_code", "target_month", "score", "alert"} <= set(row):
            raise ValueError("Invalid native prediction row")
        try:
            year, month = (int(value) for value in row["target_month"].split("-"))
            score = float(row["score"])
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError("Invalid native prediction values") from error
        if (
            year > 2024
            or month not in range(1, 13)
            or not math.isfinite(score)
            or not 0 <= score <= 1
        ):
            raise ValueError("EXP03.1 predictions reject post-2024 or invalid values")
        if not isinstance(row["alert"], bool):
            raise ValueError("EXP03.1 alerts must be boolean")
        key = (row["cell_id"], row["municipality_code"], row["target_month"])
        prediction_keys.append(key)
        cell_ids.add(row["cell_id"])
    if len(prediction_keys) != len(set(prediction_keys)):
        raise ValueError("Duplicate native EXP03.1 prediction key")
    threshold_cells = []
    for row in bundle["thresholds"]:
        if not {"cell_id", "threshold", "budget"} <= set(row) or row["cell_id"] not in cell_ids:
            raise ValueError("Invalid EXP03.1 threshold row")
        if row["budget"] != protocol()["budget"]["B_primary"]:
            raise ValueError("EXP03.1 threshold budget differs from the frozen protocol")
        threshold = row["threshold"]
        if threshold is not None and (
            not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1
        ):
            raise ValueError("Invalid EXP03.1 threshold")
        threshold_cells.append(row["cell_id"])
    if len(threshold_cells) != len(set(threshold_cells)):
        raise ValueError("Duplicate EXP03.1 threshold cell")


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
