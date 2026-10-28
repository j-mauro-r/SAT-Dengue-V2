"""Read-only EXP03.1 preflight; real science is deliberately blocked."""

from __future__ import annotations

from typing import Any

from sat_dengue.experiments.exp03_1_contract import counts, digest, protocol


def preflight(parameters: dict[str, Any]) -> dict[str, Any]:
    allowed = {"profile", "tracking", "experiment_id"}
    if set(parameters) - allowed:
        raise ValueError("Unknown EXP03.1 runtime parameter")
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
