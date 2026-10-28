"""Aggregate-only EXP03.1 tracking projection with no MLflow side effects."""

from __future__ import annotations

from typing import Any


def aggregate_projection(bundle: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_1_reporting import validate_bundle

    validate_bundle(bundle)
    aggregate = {
        "schema": "exp03-1-aggregate-tracking-v1",
        "experiment_id": bundle["experiment_id"],
        "scientific_id": bundle["scientific_id"],
        "protocol_sha256": bundle["protocol_sha256"],
        "reuse_decision": bundle["reuse_decision"]["decision"],
        "execution_counts": bundle["execution_plan"]["counts"],
        "metrics": bundle["metrics"],
        "diagnostics": bundle["diagnostics"],
        "G5": bundle["G5"],
        "champion": bundle["champion"],
        "evidence_type": "synthetic_generated_data",
    }
    text = repr(aggregate).lower()
    if "municipality_code" in text or "/users/" in text or "private" in text:
        raise ValueError("Municipal rows or private paths cannot enter EXP03.1 tracking")
    return aggregate
