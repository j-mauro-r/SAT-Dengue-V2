"""Stage 4 metrics with grouped thresholds and explicit evaluation populations."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.metrics import roc_auc_score  # type: ignore[import-untyped]


def _aligned(*objects: pd.Series | pd.DataFrame) -> None:
    """Reject positional/index ambiguity instead of silently aligning a subset."""
    if any(not obj.index.equals(objects[0].index) for obj in objects[1:]):
        raise ValueError("Metric inputs must have identical aligned indices")


def _numeric(series: pd.Series, *, binary: bool = False) -> pd.Series:
    """Validate finite numeric values, preserving explicitly unavailable entries."""
    values = series.astype("Float64")
    if not np.isfinite(values.dropna().to_numpy(dtype=float)).all():
        raise ValueError("Metric inputs must be finite")
    if binary and not values.dropna().isin([0, 1]).all():
        raise ValueError("Labels must be binary 0/1")
    return values.astype("Int64") if binary else values


def _record(
    metric: str, numerator: int, denominator: int, value: float | None, detail: str, **extra: Any
) -> dict[str, Any]:
    """Create one metric record with its explicit denominator and status."""
    return dict(
        metric=metric,
        value=value,
        evaluable=value is not None,
        detail=detail,
        numerator=numerator,
        denominator=denominator,
        **extra,
    )


def average_precision_metric(y_true: pd.Series, score: pd.Series) -> dict[str, Any]:
    """Compute non-interpolated AP by distinct descending score thresholds.

    Args:
        y_true: Aligned binary labels; empty/single-class samples are non-evaluable.
        score: Finite scores. Missing predictions make the whole metric non-evaluable.

    Returns:
        Sum of recall increments times threshold precision, with support counts.

    Raises:
        ValueError: For misalignment, nonbinary labels or nonfinite/nonnumeric scores.
    """
    _aligned(y_true, score)
    y, s = _numeric(y_true, binary=True), _numeric(score)
    positives, negatives = int(y.eq(1).sum()), int(y.eq(0).sum())
    missing_y, missing_score = int(y.isna().sum()), int(s.isna().sum())
    value = None
    detail = "insufficient_classes_or_rows"
    if missing_y or missing_score:
        detail = "unavailable_labels_or_predictions"
    elif positives and negatives:
        order = np.argsort(-s.to_numpy(dtype=float))
        ranked_y, ranked_score = y.to_numpy(dtype=int)[order], s.to_numpy(dtype=float)[order]
        # Every tied group enters precision/recall at once; no row-order tie break.
        ends = np.r_[np.flatnonzero(np.diff(ranked_score) != 0), len(y) - 1]
        true_positives = np.cumsum(ranked_y)[ends]
        precision = true_positives / (ends + 1)
        recall_increment = np.diff(np.r_[0, true_positives]) / positives
        value = float(np.sum(recall_increment * precision))
        detail = "non_interpolated_average_precision_by_distinct_score_threshold"
    return _record(
        "average_precision",
        positives,
        len(y),
        value,
        detail,
        missing_labels=missing_y,
        missing_predictions=missing_score,
    )


def onset_sensitivity_metric(
    y_true: pd.Series,
    prediction_label: pd.Series,
    index: pd.DataFrame,
    *,
    target_column: str,
    event_context: pd.DataFrame,
) -> dict[str, Any]:
    """Evaluate predictions against independently constructed retrospective onsets.

    Args:
        y_true: Selected labels at S, checked against the scientific context.
        prediction_label: Binary alerts; missing predictions never reduce true onsets.
        index: Selected municipality/target keys in prediction order.
        target_column: Horizon-specific target month.
        event_context: Keyed S/S-1 states from the verified scientific source.

    Returns:
        Detected/real-onset counts, unknown-context exclusions and unavailable alerts.
        With missing alerts the point metric is unavailable; a lower bound is explicit.

    Raises:
        ValueError: For context/key/label disagreement or invalid prediction values.
    """
    _aligned(y_true, prediction_label, index, event_context)
    y, p = _numeric(y_true, binary=True), _numeric(prediction_label, binary=True)
    keys = (
        index[["municipality_code", target_column]]
        .rename(columns={target_column: "target_period"})
        .astype("string")
    )
    if not keys.equals(event_context[["municipality_code", "target_period"]].astype("string")):
        raise ValueError("Event context keys differ from prediction targets")
    actual = _numeric(event_context["actual_excess"], binary=True)
    if not y.equals(actual):
        raise ValueError("Selected Y disagrees with scientific target state")
    onset = event_context["actual_onset"].fillna(False).astype(bool)
    detected = onset & p.eq(1).fillna(False)
    total, count = int(onset.sum()), int(detected.sum())
    missing = int(p.isna().sum())
    lower_bound = float(count / total) if total else None
    value = lower_bound if not missing else None
    detail = "detected_onsets_over_all_known_real_onsets" if total else "no_evaluable_onsets"
    if missing:
        detail = "unavailable_predictions_true_onsets_retained"
    return _record(
        "onset_sensitivity",
        count,
        total,
        value,
        detail,
        real_onsets=total,
        detected_onsets=count,
        predictions_available=int(p.notna().sum()),
        predictions_unavailable=missing,
        onsets_without_prediction=int((onset & p.isna()).sum()),
        unknown_previous_periods=int(event_context["previous_excess"].isna().sum()),
        unknown_target_periods=int(actual.isna().sum()),
        excluded_unknown_context=int((~event_context["onset_evaluable"]).sum()),
        detection_fraction_lower_bound=lower_bound,
    )


def false_alarm_ratio_metric(y_true: pd.Series, prediction_label: pd.Series) -> dict[str, Any]:
    """Compute false/emitted alerts without hiding unavailable predictions.

    Args:
        y_true: Aligned observed binary outcomes.
        prediction_label: Binary emitted alerts or explicit missing predictions.

    Returns:
        False-alarm counts and ratio, unavailable for incomplete prediction populations.
    """
    _aligned(y_true, prediction_label)
    y, p = _numeric(y_true, binary=True), _numeric(prediction_label, binary=True)
    alerts = p.eq(1)
    denominator, numerator = int(alerts.sum()), int((alerts & y.eq(0)).sum())
    missing = int((y.isna() | p.isna()).sum())
    value = float(numerator / denominator) if denominator and not missing else None
    detail = (
        "unavailable_labels_or_predictions"
        if missing
        else ("incorrect_alerts_over_emitted_alerts" if denominator else "no_alerts_emitted")
    )
    return _record(
        "false_alarm_ratio",
        numerator,
        denominator,
        value,
        detail,
        unavailable_rows=missing,
        predictions_unavailable=int(p.isna().sum()),
    )


def brier_metric(y_true: pd.Series, probability: pd.Series) -> dict[str, Any]:
    """Compute Brier on a complete probabilistic population, never a silent subset.

    Args:
        y_true: Aligned binary labels.
        probability: Finite values in [0,1], or explicit missing predictions.

    Returns:
        Mean squared probability error or a non-evaluable record with missing counts.
    """
    _aligned(y_true, probability)
    y, p = _numeric(y_true, binary=True), _numeric(probability)
    if not p.dropna().between(0, 1).all():
        raise ValueError("Probabilities must be in [0, 1]")
    missing = int((y.isna() | p.isna()).sum())
    value = float(((p - y) ** 2).mean()) if len(y) and not missing else None
    detail = (
        "mean_squared_probability_error"
        if value is not None
        else "no_complete_probabilistic_population"
    )
    return _record(
        "brier", int((y.notna() & p.notna()).sum()), len(y), value, detail, unavailable_rows=missing
    )


def evaluate_metrics(
    reference: str,
    y_true: pd.Series,
    predictions: pd.DataFrame,
    index: pd.DataFrame,
    *,
    target_column: str,
    threshold_policy_declared: bool,
    event_context: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Evaluate shared references with context kept outside fitting and X.

    Args:
        reference: Reference identifier.
        y_true: Observed validation outcomes.
        predictions: Reference outputs, aligned to the selected keys.
        index: Municipality/origin/target linkage.
        target_column: Horizon-specific target column.
        threshold_policy_declared: Whether event-alert interpretation is authorized.
        event_context: Retrospective scientific S/S-1 states, evaluation only.

    Returns:
        Four metric records with explicit evaluability and event accounting.
    """
    _aligned(y_true, predictions, index, event_context)
    probabilistic = (
        not predictions.empty and predictions["prediction_kind"].eq("probabilistic").all()
    )
    records = [average_precision_metric(y_true, predictions["prediction_score"])]
    records.append(
        brier_metric(y_true, predictions["prediction_probability"])
        if probabilistic
        else _record("brier", 0, 0, None, "not_a_probabilistic_forecast")
    )
    onset = onset_sensitivity_metric(
        y_true,
        predictions["prediction_label"],
        index,
        target_column=target_column,
        event_context=event_context,
    )
    far = false_alarm_ratio_metric(y_true, predictions["prediction_label"])
    if probabilistic and not threshold_policy_declared:
        for event in (onset, far):
            event.update(value=None, evaluable=False, detail="threshold_policy_not_declared")
        # A lower-bound detection claim also requires an alert threshold policy.
        onset["detection_fraction_lower_bound"] = None
    records.extend([onset, far])
    for record in records:
        record.update(
            reference=reference,
            event_definition="onset: observed excess at S and no excess at exactly S-1",
            anticipation_rule="each origin predicts its own target S=T+h; S-1 is evaluation only",
            evaluable_population=(
                "all selected keys; real onset denominator independent of predictions"
            ),
            unknown_periods_treatment=(
                "unknown scientific S/S-1 excluded and counted; "
                "unavailable alerts retain true onset denominator"
            ),
        )
    return records


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
