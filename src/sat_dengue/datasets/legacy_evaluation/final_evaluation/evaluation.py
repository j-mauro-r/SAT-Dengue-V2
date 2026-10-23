"""Legacy default-policy adapter; all evaluation formulas have one pure owner."""

from typing import Any

from sat_dengue.datasets.legacy_evaluation.model_assessment.policy import _default_decision_policy
from sat_dengue.final_evaluation.evaluation import circular_draws as circular_draws
from sat_dengue.final_evaluation.evaluation import evaluate_horizon as evaluate
from sat_dengue.final_evaluation.evaluation import metric_records as metric_records
from sat_dengue.final_evaluation.evaluation import research_result as classify


def research_result(
    complete: bool,
    onset_gain: float,
    far_increase: float,
    lower_onset: float,
    upper_far: float,
    decision_policy: Any = None,
) -> str:
    return classify(
        complete,
        onset_gain,
        far_increase,
        lower_onset,
        upper_far,
        decision_policy or _default_decision_policy(),
    )


def evaluate_horizon(cohort: Any, predictions: Any, settings: Any) -> Any:
    return evaluate(cohort, predictions, settings, _default_decision_policy())
