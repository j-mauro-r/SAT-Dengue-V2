"""Pure EXP-DELTA03 training contracts: no filesystem, estimator or tracking access."""

from __future__ import annotations

import hashlib
import json
from typing import Any

REGIME = "RETROSPECTIVE_CONSOLIDATED"
ROLES = ("train", "calibration", "selection", "evaluation")
PENDING = "PENDING_HUMAN_FREEZE"


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def derive_plan(metadata: dict[str, Any], *, metadata_sha256: str) -> dict[str, Any]:
    """Derive every cell/count from the verified preparation descriptor, never a grid copy."""
    if (
        metadata.get("availability_regime") != REGIME
        or metadata.get("operational_PIT") is not False
    ):
        raise ValueError("Only explicitly retrospective preparation is admitted")
    cells, unsupported, seen = [], [], set()
    features = {r["name"] for r in metadata["feature_contract"]}
    for view in metadata["views"]:
        ident = view["id"]
        if ident in seen:
            raise ValueError("Duplicate execution cell")
        seen.add(ident)
        if view["horizon"] not in (1, 2) or view["year"] >= 2025:
            raise ValueError("Unapproved horizon/year")
        if view["evidence_type"] != (
            "consumed_retrospective_stress" if view["year"] == 2024 else "consumed_retrospective"
        ):
            raise ValueError("Stress2024 must remain separate")
        if view["status"] != "MATERIALIZABLE_RETROSPECTIVE":
            if view["reference"] != "water":
                raise ValueError("Unexpected unsupported primary cell")
            unsupported.append({"id": ident, "status": view["status"], "reason": view["reason"]})
            continue
        columns = view["columns"]
        if not columns or len(columns) != len(set(columns)) or not set(columns) <= features:
            raise ValueError("Invalid positive feature list")
        if any(role not in view["roles"] for role in ROLES):
            raise ValueError("Missing learned/evaluation role")
        support = {}
        for role in ROLES:
            r = view["roles"][role]
            n, positive = r["rows"], r["onsets"]
            if n < 1 or positive < 0 or positive > n:
                raise ValueError("Invalid role support")
            if any(len(r[k]) != 64 for k in ("key_sha256", "key_label_sha256", "X_sha256")):
                raise ValueError("Missing role identity")
            support[role] = {"rows": n, "positive": positive, "negative": n - positive}
        cells.append(
            {
                "id": ident,
                "variant": view["variant"],
                "horizon": view["horizon"],
                "year": view["year"],
                "reference": view["reference"],
                "evidence_type": view["evidence_type"],
                "columns": columns,
                "physical_columns": view["physical_columns"],
                "roles": view["roles"],
                "support": support,
                "weight": view["comparison_row_weight"],
                "training_scope": "outside_Meta_Tolima"
                if view["reference"] == "transfer"
                else "national",
                "evaluation_scope": "Meta_Tolima",
                "national_evaluation": "UNAVAILABLE_FROZEN_REGIONAL_COHORT",
            }
        )
    lookup = {(v["horizon"], v["year"], v["variant"]): v for v in cells}
    pairs = []
    for cell in cells:
        reference: str | None
        variant = cell["variant"]
        if variant.startswith("FULL_MINUS_") or variant == "HISTORY":
            reference = "FULL_COMMON"
        else:
            reference = {
                "FULL_PLUS_SURFACE_WATER": "WATER_REFERENCE",
                "FULL_ERA5_PRECIPITATION": "ERA5_REFERENCE",
                "TRANSFER_EXCLUDE_META_TOLIMA": "TRANSFER_REFERENCE",
            }.get(variant)
        if reference is None:
            continue
        ref = lookup.get((cell["horizon"], cell["year"], reference))
        if ref is None:
            raise ValueError("Missing paired reference")
        matched_roles = ("evaluation",) if cell["reference"] == "transfer" else ROLES
        for role in matched_roles:
            if cell["roles"][role]["key_label_sha256"] != ref["roles"][role]["key_label_sha256"]:
                raise ValueError("Unpaired cohort/labels")
        pairs.append(
            {
                "left": cell["id"],
                "right": ref["id"],
                "matched_roles": list(matched_roles),
                "interpretation": "whole_procedure_geographic_transfer"
                if cell["reference"] == "transfer"
                else "paired_predictive_ablation",
            }
        )
    if not cells:
        raise ValueError("Empty execution plan")
    counts = {
        "descriptors": len(seen),
        "models": len(cells),
        "calibrators": len(cells),
        "unsupported": len(unsupported),
        "comparisons": len(pairs),
        "parent_runs": 1,
        "child_runs": len(cells),
        "runs": len(cells) + 1,
    }
    return {
        "schema": "exp-delta03-execution-plan-v1",
        "metadata_sha256": metadata_sha256,
        "regime": REGIME,
        "operational_PIT": False,
        "cells": cells,
        "unsupported": unsupported,
        "pairs": pairs,
        "counts": counts,
    }


def validate_freeze(contract: dict[str, Any], *, synthetic: bool) -> None:
    """Synthetic decisions are explicit fixtures, never a grant for private fitting."""
    if contract["regime"] != REGIME or contract["operational_PIT"] is not False:
        raise ValueError("Invalid availability regime")
    if not synthetic and contract.get("decision_status") != "APPROVED":
        raise ValueError("Scientific contract awaits explicit human freeze")
    if synthetic and contract.get("evidence_type") != "generated_only":
        raise ValueError("Synthetic execution requires generated-only contract")
    if contract.get("phase3_authorized") or contract.get("training_authorized"):
        raise ValueError("Phase2 cannot grant scientific training authorization")
    model = contract["model"]
    if (
        model["n_jobs"] != 1
        or model["random_state"] != contract["seed"]
        or model["objective"] != "binary:logistic"
        or model["tree_method"] != "hist"
    ):
        raise ValueError("Unexpected model family/resource/seed")
    if contract["calibration"]["method"] != "regularized_intercept":
        raise ValueError("Unsupported calibration method")
    if contract["calibration"]["penalty"] <= 0 or contract["policy"]["B"] < 0:
        raise ValueError("Invalid penalty or budget")
    if contract["policy"]["unit"] != "false_onset_alerts_per_eligible_municipality_year":
        raise ValueError("Budget unit mismatch")
    if not (0 < contract["uncertainty"]["confidence"] < 1) or contract["uncertainty"]["draws"] < 1:
        raise ValueError("Invalid uncertainty configuration")
