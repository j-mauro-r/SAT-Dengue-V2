"""Pure EXP03.1 cell planning and fail-closed EXP03 V09 reuse decisions."""

from __future__ import annotations

from typing import Any

from sat_dengue.experiments.exp03_1_contract import cells, protocol


def reuse_decision(current: dict[str, str], reference: dict[str, str]) -> dict[str, Any]:
    required = protocol()["reuse_identity_fields"]
    missing = [name for name in required if name not in current or name not in reference]
    mismatched = [
        name
        for name in required
        if name in current and name in reference and current[name] != reference[name]
    ]
    reused = not missing and not mismatched
    return {
        "schema": "exp03-1-reuse-decision-v1",
        "decision": "reused" if reused else "refitted",
        "reason": "all_contract_hashes_identical"
        if reused
        else "missing_or_mismatched_contract_hash",
        "required_fields": required,
        "missing": missing,
        "mismatched": mismatched,
        "current": {name: current.get(name) for name in required},
        "reference": {name: reference.get(name) for name in required},
    }


def execution_plan(decision: dict[str, Any]) -> dict[str, Any]:
    if decision.get("decision") not in {"reused", "refitted"}:
        raise ValueError("Invalid EXP03.1 reuse decision")
    grid = cells()
    planned = []
    for cell in grid:
        origin = (
            "reused_exp03_v09"
            if decision["decision"] == "reused" and cell["variant"] == "M00"
            else "new_fit"
        )
        planned.append({**cell, "origin": origin})
    reused = sum(row["origin"] == "reused_exp03_v09" for row in planned)
    return {
        "schema": "exp03-1-execution-plan-v1",
        "cells": planned,
        "counts": {"total": len(planned), "reused": reused, "new_fits": len(planned) - reused},
        "searches": 0,
    }


def variant_predictors(v09: list[str], variant: str) -> list[str]:
    p = protocol()
    if len(v09) != len(set(v09)) or variant not in p["variants"]:
        raise ValueError("Invalid ordered V09 predictors or variant")
    blocks = p["variants"][variant]["blocks"]
    result = list(v09)
    if "recent" in blocks:
        result.extend(p["predictors"]["recent"])
    if "change" in blocks:
        result.extend(p["predictors"]["change"])
    if len(result) != len(set(result)):
        raise ValueError("Deterministically redundant EXP03.1 predictor list")
    return result
