"""Primary Stage 4 metrics with explicit non-evaluable handling."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


def _as_binary(series: pd.Series) -> pd.Series:
    """Normalize a nullable label series to Int64 binary values."""
    values = series.astype("Int64")
    mask = values.dropna().isin([0, 1])
    if not mask.all():
        raise ValueError("Labels must be binary 0/1")
    return values


def average_precision_metric(y_true: pd.Series, score: pd.Series) -> dict[str, Any]:
    """Compute average precision for binary labels and arbitrary scores."""
    y = _as_binary(y_true)
    s = score.astype("Float64")
    mask = y.notna() & s.notna()
    y_eval = y[mask].astype(int)
    s_eval = s[mask].astype(float)
    positives = int((y_eval == 1).sum())
    negatives = int((y_eval == 0).sum())
    if len(y_eval) == 0 or positives == 0 or negatives == 0:
        return {
            "metric": "average_precision",
            "value": None,
            "evaluable": False,
            "detail": "insufficient_classes_or_rows",
            "numerator": positives,
            "denominator": len(y_eval),
        }
    order = np.argsort(-s_eval.to_numpy(), kind="mergesort")
    ranked = y_eval.to_numpy()[order]
    tp = np.cumsum(ranked == 1)
    fp = np.cumsum(ranked == 0)
    precision = tp / (tp + fp)
    recall = tp / positives
    ap = float(np.sum((recall - np.r_[0.0, recall[:-1]]) * precision))
    return {
        "metric": "average_precision",
        "value": ap,
        "evaluable": True,
        "detail": "average precision over evaluable rows",
        "numerator": positives,
        "denominator": len(y_eval),
    }


def onset_sensitivity_metric(
    y_true: pd.Series,
    prediction_label: pd.Series,
    index: pd.DataFrame,
    *,
    target_column: str,
) -> dict[str, Any]:
    """Compute onset sensitivity with explicit unknown-period treatment."""
    y = _as_binary(y_true)
    p = prediction_label.astype("Int64")
    valid = y.notna() & p.notna()
    frame = pd.DataFrame(
        {
            "municipality_code": index["municipality_code"].astype("string"),
            "target_period": index[target_column].astype("string"),
            "y": y,
            "pred": p,
            "valid": valid,
        }
    )
    frame = frame.sort_values(["municipality_code", "target_period"]).reset_index(drop=True)
    previous = frame.groupby("municipality_code", sort=False)["y"].shift(1)
    unknown_previous = previous.isna() & frame["y"].eq(1)
    onset = frame["y"].eq(1) & previous.eq(0) & frame["valid"]
    detected = onset & frame["pred"].eq(1)
    denominator = int(onset.sum())
    numerator = int(detected.sum())
    if denominator == 0:
        return {
            "metric": "onset_sensitivity",
            "value": None,
            "evaluable": False,
            "detail": "no_evaluable_onsets",
            "numerator": numerator,
            "denominator": denominator,
            "unknown_previous_periods": int(unknown_previous.sum()),
        }
    return {
        "metric": "onset_sensitivity",
        "value": float(numerator / denominator),
        "evaluable": True,
        "detail": "detected_onsets_over_total_onsets",
        "numerator": numerator,
        "denominator": denominator,
        "unknown_previous_periods": int(unknown_previous.sum()),
    }


def false_alarm_ratio_metric(y_true: pd.Series, prediction_label: pd.Series) -> dict[str, Any]:
    """Compute false alarms over emitted alerts for deterministic outputs."""
    y = _as_binary(y_true)
    p = prediction_label.astype("Int64")
    valid = y.notna() & p.notna()
    alerts = valid & p.eq(1)
    denominator = int(alerts.sum())
    numerator = int((alerts & y.eq(0)).sum())
    if denominator == 0:
        return {
            "metric": "false_alarm_ratio",
            "value": None,
            "evaluable": False,
            "detail": "no_alerts_emitted",
            "numerator": numerator,
            "denominator": denominator,
        }
    return {
        "metric": "false_alarm_ratio",
        "value": float(numerator / denominator),
        "evaluable": True,
        "detail": "incorrect_alerts_over_emitted_alerts",
        "numerator": numerator,
        "denominator": denominator,
    }


def brier_metric(y_true: pd.Series, probability: pd.Series) -> dict[str, Any]:
    """Compute Brier score on probabilistic predictions only."""
    y = _as_binary(y_true)
    p = probability.astype("Float64")
    mask = y.notna() & p.notna()
    y_eval = y[mask].astype(float)
    p_eval = p[mask].astype(float)
    if len(y_eval) == 0:
        return {
            "metric": "brier",
            "value": None,
            "evaluable": False,
            "detail": "no_probabilistic_rows",
            "numerator": 0,
            "denominator": 0,
        }
    if ((p_eval < 0.0) | (p_eval > 1.0)).any():
        raise ValueError("Probabilities must be in [0, 1]")
    value = float(np.mean((p_eval - y_eval) ** 2))
    return {
        "metric": "brier",
        "value": value,
        "evaluable": True,
        "detail": "mean_squared_probability_error",
        "numerator": len(y_eval),
        "denominator": len(y_eval),
    }


def evaluate_metrics(
    reference: str,
    y_true: pd.Series,
    predictions: pd.DataFrame,
    index: pd.DataFrame,
    *,
    target_column: str,
    threshold_policy_declared: bool,
) -> list[dict[str, Any]]:
    """Evaluate the four primary metrics under explicit policy constraints."""
    if predictions.empty:
        records = [
            {
                "metric": metric,
                "value": None,
                "evaluable": False,
                "detail": "no_rows",
                "numerator": 0,
                "denominator": 0,
            }
            for metric in (
                "average_precision",
                "brier",
                "onset_sensitivity",
                "false_alarm_ratio",
            )
        ]
        for record in records:
            record["reference"] = reference
            record["event_definition"] = "onset: y==1 and previous y==0 by municipality"
            record["anticipation_rule"] = "prediction at origin for target period t+h"
            record["evaluable_population"] = (
                "rows with non-missing y and required prediction fields"
            )
            record["unknown_periods_treatment"] = (
                "exclude from denominator; report as non-evaluable"
            )
        return records

    records = [
        average_precision_metric(y_true, predictions["prediction_score"]),
        brier_metric(y_true, predictions["prediction_probability"]),
    ]
    if predictions["prediction_kind"].iloc[0] == "probabilistic" and not threshold_policy_declared:
        records.extend(
            [
                {
                    "metric": "onset_sensitivity",
                    "value": None,
                    "evaluable": False,
                    "detail": "threshold_policy_not_declared",
                    "numerator": 0,
                    "denominator": 0,
                },
                {
                    "metric": "false_alarm_ratio",
                    "value": None,
                    "evaluable": False,
                    "detail": "threshold_policy_not_declared",
                    "numerator": 0,
                    "denominator": 0,
                },
            ]
        )
    else:
        records.append(
            onset_sensitivity_metric(
                y_true,
                predictions["prediction_label"],
                index,
                target_column=target_column,
            )
        )
        records.append(false_alarm_ratio_metric(y_true, predictions["prediction_label"]))
    for record in records:
        record["reference"] = reference
        record["event_definition"] = "onset: y==1 and previous y==0 by municipality"
        record["anticipation_rule"] = "prediction at origin for target period t+h"
        record["evaluable_population"] = "rows with non-missing y and required prediction fields"
        record["unknown_periods_treatment"] = "exclude from denominator; report as non-evaluable"
    return records
