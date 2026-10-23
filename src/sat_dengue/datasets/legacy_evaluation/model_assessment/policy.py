"""Fixed development utility rules and pending final protocol."""

from __future__ import annotations

from sat_dengue.datasets.legacy_evaluation.model_evaluation.decision_policy import (
    ChampionDecisionPolicy,
    load_decision_policy,
)
from sat_dengue.datasets.legacy_training.contract import resolve_root
from sat_dengue.model_assessment.policy import proposed_calendar as proposed_calendar
from sat_dengue.model_assessment.policy import require_development as require_development


def _default_decision_policy() -> ChampionDecisionPolicy:
    """Load the repository-owned policy for direct utility calls."""
    return load_decision_policy(resolve_root())


def utility(
    onset_gain: float | None,
    false_alarm_increase: float | None,
    decision_policy: ChampionDecisionPolicy | None = None,
) -> str:
    """Compatibility default-policy I/O; the domain owns the scientific rule."""
    from sat_dengue.model_assessment.policy import utility as calculate

    return calculate(
        onset_gain, false_alarm_increase, decision_policy or _default_decision_policy()
    )
