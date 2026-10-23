"""Validate monthly keys and the resolved approved Stage 2 scientific settings."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.data.consolidation import compute_schema_contract


def validate_panel_keys(panel: pd.DataFrame) -> None:
    required = {"municipality_code", "year_month", "dengue_notifications_count"}
    if not required.issubset(panel.columns) or panel.empty:
        raise ValueError("Invalid panel schema or empty cohort")
    if (
        panel[list(required)].columns.duplicated().any()
        or panel.duplicated(["municipality_code", "year_month"]).any()
    ):
        raise ValueError("Duplicate panel keys")
    if not panel["municipality_code"].astype(str).str.fullmatch(r"\d{5}").all():
        raise ValueError("Invalid municipality key")
    if not panel["year_month"].astype(str).str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise ValueError("Invalid monthly coverage")
    periods = (
        pd.period_range(panel["year_month"].min(), panel["year_month"].max(), freq="M")
        .astype(str)
        .tolist()
    )
    for _, group in panel.groupby("municipality_code"):
        if sorted(group["year_month"].tolist()) != periods:
            raise ValueError("Invalid monthly coverage: gaps or unequal municipality cohorts")


def validate_stage2_configuration(resolved: dict[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != resolved.get("configuration_sha256"):
        raise ValueError("Resolved configuration fingerprint mismatch")
    if resolved["operational"]["profile"] != "data" or resolved["operational"]["tracking"] not in (
        "disabled",
        "enabled",
    ):
        raise ValueError("Stage 2 requires the validated data/disabled profile")
    contract = resolved["stage2"]["construction"]
    approved = compute_schema_contract([], pd.DataFrame(), version="candidate-construction-v1")
    for section in (
        "target_labeling_policy",
        "current_endemic_channel_policy",
        "climate_monthly_aggregation",
    ):
        if contract.get(section) != approved[section]:
            raise ValueError(f"Contradictory Stage 2 scientific configuration: {section}")
    if (
        contract.get("contract_version") != "candidate-construction-v1"
        or contract.get("classification") != "candidate_construction_contract"
    ):
        raise ValueError("Unapproved construction contract")
    return contract
