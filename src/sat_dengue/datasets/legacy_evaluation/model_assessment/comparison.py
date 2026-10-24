"""Legacy default-policy input adapter for the pure development comparison."""

from typing import Any

from sat_dengue.model_assessment.comparison import summarize as calculate

from .policy import _default_decision_policy


def summarize(metrics: Any, decision_policy: Any = None) -> Any:
    return calculate(metrics, decision_policy or _default_decision_policy())
