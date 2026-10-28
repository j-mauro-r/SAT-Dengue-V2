"""Read-only EXP03.1 preflight; real science is deliberately blocked."""

from __future__ import annotations

from typing import Any

from sat_dengue.experiments.exp03_1_contract import counts, digest, protocol


def preflight(parameters: dict[str, Any]) -> dict[str, Any]:
    required = {"profile", "tracking", "experiment_id"}
    if set(parameters) != required:
        raise ValueError("EXP03.1 preflight requires the exact guarded parameter set")
    if (
        parameters["profile"] not in {"exp03_1", "exp03_1_preflight"}
        or parameters["tracking"] != "disabled"
        or parameters["experiment_id"] != "EXP031"
    ):
        raise PermissionError("EXP03.1 real execution and tracking remain unauthorized")
    p = protocol()
    return {
        "schema": "exp03-1-preflight-v1",
        "status": "blocked_pending_separate_scientific_authorization",
        "execution_ready": False,
        "protocol_sha256": digest(p),
        "counts": counts(p),
        "effects": {
            "private_reads": 0,
            "reservations": 0,
            "fits": 0,
            "calibrations": 0,
            "searches": 0,
            "permanent_mlflow_writes": 0,
        },
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
