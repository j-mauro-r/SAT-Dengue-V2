"""Critical Stage 5 assessment boundaries and approved utility semantics."""

import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.model_assessment.policy import proposed_calendar, require_development, utility
from scripts.model_evaluation.availability import availability_transition
from scripts.model_evaluation.contract import ModelEvaluationError
from scripts.model_training.metrics import false_alarm_ratio_metric, onset_sensitivity_metric


def test_early_t2_origin_rejects_december_component() -> None:
    """January2025 T2 cannot consume labels through December2024."""
    with pytest.raises(ModelEvaluationError, match="availability"):
        availability_transition(
            pd.Series(["2024-12"]),
            pd.Series(["2024-11"]),
            dependencies={},
            producer="outer",
            consumer="January2025_t2",
        )
    calendar = proposed_calendar(2)
    assert calendar["origins"][0] == "2024-11"
    assert calendar["training_target_end"] == "2024-11"


def test_reserved_targets_rejected_before_development_selection() -> None:
    """The boundary follows targets rather than origins or calendar years of fitting."""
    require_development(pd.Series(["2012-01", "2024-12"]))
    with pytest.raises(ValueError, match="Reserved"):
        require_development(pd.Series(["2024-12", "2025-01"]))


def test_utility_uses_onsets_and_emitted_alerts_with_fixed_knobs() -> None:
    """Continuing excess and true negatives must not inflate utility denominators."""
    y = pd.Series([1, 1, 0, 0, 0], dtype="Int64")
    alerts = pd.Series([1, 0, 1, 0, 0], dtype="Int64")
    index = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 5,
            "target_period": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        }
    )
    context = index.assign(
        actual_excess=y,
        previous_excess=pd.Series([0, 1, 1, 0, 0], dtype="Int64"),
        actual_onset=[True, False, False, False, False],
        onset_evaluable=True,
    )
    onset = onset_sensitivity_metric(
        y, alerts, index, target_column="target_period", event_context=context
    )
    far = false_alarm_ratio_metric(y, alerts)
    assert (onset["numerator"], onset["denominator"]) == (1, 1)
    assert (far["numerator"], far["denominator"]) == (1, 2)
    assert utility(0.10, 0.05) == "meets_point_criteria"
    assert utility(0.099, 0.05) == "does_not_meet_point_criteria"
    assert utility(0.10, 0.051) == "does_not_meet_point_criteria"
    assert utility(None, 0.0) == "insufficient_evidence"
