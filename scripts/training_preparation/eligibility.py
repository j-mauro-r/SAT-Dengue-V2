"""Audit existing horizon eligibility after constructing complete antecedents."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationError
from .features import KEYS

# Adapter to the existing standalone script, whose public payloads are JSON-like.
readiness = import_module("scripts.validate_stage2_training_readiness")


def build_controls(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    policy: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Separate controls from X and audit only development-target eligibility.

    Args:
        panel: Development reference rows, already used to build antecedents.
        contract: Preparation role contract.
        policy: Existing notification-year-backed eligibility policy.

    Returns:
        Keyed controls with reserved-target metadata masked, plus horizon audit.

    Raises:
        PreparationError: If independent selectors disagree or policy differs.
    """
    bounds = policy["development_target_eligibility"]
    target_min, target_max = bounds["target_min"], bounds["target_max"]
    if target_max >= contract["temporal_policy"]["reserved_final_block_start"]:
        raise PreparationError("Eligibility policy exposes reserved targets")
    frame = panel.sort_values(KEYS).reset_index(drop=True)
    controls = frame[KEYS + contract["roles"]["targets"] + contract["roles"]["controls"]].copy()
    audit: dict[str, Any] = {}
    for horizon in (1, 2):
        suffix = f"t{horizon}"
        target = frame[f"target_period_{suffix}"]
        allowed_target = target.between(target_min, target_max)
        eligible = allowed_target & frame[f"y_evaluable_{suffix}"]
        # Restrict before consulting either selector; no reserved outcome is used.
        safe = frame.loc[allowed_target]
        independent = readiness.independent_select_supervised_rows(
            safe,
            horizon,
            target_min_period=target_min,
            target_max_period=target_max,
            reference_max_period=contract["development_output"]["reference_end"],
        )
        expected = frame.loc[eligible, KEYS].reset_index(drop=True)
        if list(expected.itertuples(index=False, name=None)) != list(
            independent[KEYS].itertuples(index=False, name=None)
        ):
            raise PreparationError(f"Eligibility selector mismatch: {suffix}")
        controls[f"eligible_{suffix}"] = eligible
        reserved = target >= bounds["reserved_block_start"]
        for column in contract["roles"]["targets"] + contract["roles"]["controls"]:
            if column.endswith(f"_{suffix}") and column != f"target_period_{suffix}":
                controls[column] = controls[column].mask(reserved)
        controls[f"reserved_target_masked_{suffix}"] = reserved
        audit[suffix] = {
            "rows": int(eligible.sum()),
            "reference_start": str(frame.loc[eligible, "year_month"].min())
            if eligible.any()
            else None,
            "reference_end": str(frame.loc[eligible, "year_month"].max())
            if eligible.any()
            else None,
            "target_start": str(target[eligible].min()) if eligible.any() else None,
            "target_end": str(target[eligible].max()) if eligible.any() else None,
            "independent_selector_agrees": True,
            "reserved_targets_used": 0,
        }
    return controls, audit


def policy_from_years(min_year: int, max_year: int, reserved: str) -> dict[str, Any]:
    """Reuse the existing conservative policy without duplicating its date rules.

    Args:
        min_year: Minimum notification year from consolidated ANO metadata.
        max_year: Maximum notification year from consolidated ANO metadata.
        reserved: First reserved target month.

    Returns:
        Existing policy payload; no case counts or outcomes are analyzed.
    """
    return readiness.build_model_eligibility_policy(
        min_year, max_year, reserved_block_start=reserved
    )


def notification_year_metadata(path: Path) -> dict[str, Any]:
    """Read only source ANO metadata through the existing standalone validator.

    Args:
        path: Existing consolidated product, already fingerprint-verified.

    Returns:
        Notification-year metadata used by the existing eligibility policy.
    """
    return readiness.read_notification_year_metadata(path)
