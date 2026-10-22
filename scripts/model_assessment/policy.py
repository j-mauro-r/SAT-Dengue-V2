"""Fixed development utility rules and pending final protocol."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from scripts.model_evaluation.availability import availability_transition
from scripts.model_evaluation.decision_policy import (
    ChampionDecisionPolicy,
    load_decision_policy,
)


def _default_decision_policy() -> ChampionDecisionPolicy:
    """Load the repository-owned policy for direct utility calls."""
    return load_decision_policy(Path(__file__).resolve().parents[2])


def utility(
    onset_gain: float | None,
    false_alarm_increase: float | None,
    decision_policy: ChampionDecisionPolicy | None = None,
) -> str:
    """Apply DEC-125 point criteria without converting missing evidence into success.

    Args:
        onset_gain: Equal-window sensitivity difference against persistence.
        false_alarm_increase: Equal-window false/emitted-alert ratio difference.
        decision_policy: Validated policy; repository policy is loaded when omitted.

    Returns:
        Point utility status, separate from uncertainty and research acceptance.
    """
    if onset_gain is None or false_alarm_increase is None:
        return "insufficient_evidence"
    if pd.isna(onset_gain) or pd.isna(false_alarm_increase):
        return "insufficient_evidence"
    policy = decision_policy or _default_decision_policy()
    return (
        "meets_point_criteria"
        if onset_gain >= policy.knobs.min_onset_sensitivity_gain
        and false_alarm_increase <= policy.knobs.max_false_alarm_increase
        else "does_not_meet_point_criteria"
    )


def require_development(targets: pd.Series) -> None:
    """Reject reserved, missing or malformed target months before dependent operations."""
    if targets.empty or targets.isna().any():
        raise ValueError("Complete development targets required")
    periods = pd.PeriodIndex(targets, freq="M")
    if list(periods.astype(str)) != targets.astype(str).tolist():
        raise ValueError("Canonical target months required")
    if not targets.astype(str).between("2012-01", "2024-12").all():
        raise ValueError("Reserved targets cannot enter development fitting or selection")


def proposed_calendar(horizon: int, final: dict[str, Any] | None = None) -> dict[str, Any]:
    """Specify final dates without reading reserved labels or pretending fits occurred."""
    if horizon not in (1, 2):
        raise ValueError("Horizon must be 1 or 2")
    if final is None:
        final = {
            "target_start": "2025-01",
            "target_end": "2025-12",
            "outer_training_target_start": "2012-01",
            "outer_training_target_end": {"1": "2024-12", "2": "2024-11"},
        }
    if (
        final["target_start"] != "2025-01"
        or final["target_end"] != "2025-12"
        or final["outer_training_target_start"] != "2012-01"
        or final["outer_training_target_end"] != {"1": "2024-12", "2": "2024-11"}
    ):
        raise ValueError("Unsupported final calendar: explicit protocol revision required")
    targets = pd.period_range(final["target_start"], final["target_end"], freq="M")
    origins = (targets - horizon).astype(str)
    cutoff = final["outer_training_target_end"][str(horizon)]
    audit = availability_transition(
        pd.Series([cutoff]),
        pd.Series(origins),
        dependencies={"retained_internal_decisions": "2024-03"},
        producer="proposed_outer_fit",
        consumer="proposed_reserved_prediction",
    )
    return {
        "horizon": horizon,
        "training_target_start": "2012-01",
        "training_target_end": cutoff,
        "targets": targets.astype(str).tolist(),
        "origins": origins.tolist(),
        "retained_internal_window": f"2024-06_t{horizon}",
        "hyperparameter_targets": ["2023-01", "2023-06"],
        "calibration_fit_targets": ["2023-08", "2023-09"],
        "calibration_selection_targets": ["2023-11", "2023-12"],
        "threshold_selection_targets": ["2024-02", "2024-03"],
        "planned_availability_check": audit,
        "actual_final_components": "not_fitted_pending_authorization",
    }
