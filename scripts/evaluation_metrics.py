"""Shared supplementary evaluation over unchanged training-era metric definitions."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from sklearn.metrics import roc_auc_score  # type: ignore[import-untyped]

from scripts.model_training.metrics import _aligned, _numeric, _record, evaluate_metrics


def auroc_metric(y_true: pd.Series, score: pd.Series) -> dict[str, Any]:
    """Evaluate binary AUROC on the complete aligned population, including tied scores.

    Args:
        y_true: Binary outcomes with the original evaluation index.
        score: Continuous candidate scores, or documented deterministic reference scores.

    Returns:
        AUROC with positive/negative and missing support. Numerator/denominator
        describe positive/total rows, not an alternative formula for AUROC.

    Raises:
        ValueError: If indices disagree, outcomes are nonbinary or values are nonfinite.
    """
    _aligned(y_true, score)
    y, scores = _numeric(y_true, binary=True), _numeric(score)
    positives, negatives = int(y.eq(1).sum()), int(y.eq(0).sum())
    missing_y, missing_score = int(y.isna().sum()), int(scores.isna().sum())
    value = None
    detail = "insufficient_classes_or_rows"
    if missing_y or missing_score:
        detail = "unavailable_labels_or_predictions"
    elif positives and negatives:
        value = float(roc_auc_score(y.to_numpy(dtype=int), scores.to_numpy(dtype=float)))
        detail = "binary_rank_AUROC_ties_half_credit; support_positive_over_total_rows"
    return _record(
        "auroc",
        positives,
        len(y),
        value,
        detail,
        missing_labels=missing_y,
        missing_predictions=missing_score,
        positive_rows=positives,
        negative_rows=negatives,
    )


def evaluate_comparison_metrics(
    reference: str,
    y_true: pd.Series,
    predictions: pd.DataFrame,
    index: pd.DataFrame,
    *,
    target_column: str,
    threshold_policy_declared: bool,
    event_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Extend the shared four-metric evaluator with complementary AUROC.

    Args:
        reference: Candidate or deterministic reference identifier.
        y_true: Aligned observed binary outcomes.
        predictions: Existing score, probability, alert and prediction-kind columns.
        index: Unchanged municipality/origin/target keys.
        target_column: Horizon-specific target-month column.
        threshold_policy_declared: Existing alert interpretation policy.
        event_context: Evaluation-only scientific S/S−1 context.

    Returns:
        The unchanged four metric records plus AUROC. No fitting, ranking or
        threshold selection is performed; persistence Brier stays non-applicable.
    """
    records = evaluate_metrics(
        reference,
        y_true,
        predictions,
        index,
        target_column=target_column,
        threshold_policy_declared=threshold_policy_declared,
        event_context=event_context,
    )
    auroc = auroc_metric(y_true, predictions["prediction_score"])
    auroc.update(
        reference=reference,
        score_interpretation=(
            "deterministic_reference_score_not_calibrated_probability"
            if predictions.prediction_kind.eq("deterministic").all()
            else "continuous_model_score"
        ),
    )
    return [*records, auroc]
