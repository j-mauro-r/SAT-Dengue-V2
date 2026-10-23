"""Preserved shared window/reference output construction."""

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.metrics import average_precision_metric, brier_metric, evaluate_metrics

from .contract import ModelTrainingError
from .loading import WindowDataset
from .references import persistence_reference, train_prevalence_reference


def _window_base(dataset: WindowDataset) -> pd.DataFrame:
    """Build key linkage columns for one validation window."""
    return pd.DataFrame(
        {
            "window_id": dataset.window_id,
            "cutoff": dataset.cutoff,
            "horizon": dataset.horizon,
            "municipality_code": dataset.validation_index["municipality_code"].astype("string"),
            "origin_period": dataset.validation_index["year_month"].astype("string"),
            "target_period": dataset.validation_index[dataset.target_column].astype("string"),
            "feature_row": dataset.validation_index["feature_row"].astype("Int64"),
        }
    )


def _enforce_window_rules(dataset: WindowDataset, *, reserved_start: str) -> None:
    """Reject temporal windows that leak reserved targets."""
    train_targets = dataset.train_index[dataset.target_column].astype("string")
    if (train_targets >= reserved_start).any():
        raise ModelTrainingError(
            f"Window {dataset.window_id} includes reserved training targets >= {reserved_start}"
        )
    validation_targets = dataset.validation_index[dataset.target_column].astype("string")
    if (validation_targets >= reserved_start).any():
        raise ModelTrainingError(
            f"Window {dataset.window_id} includes reserved targets >= {reserved_start}"
        )


def _build_window_outputs(
    dataset: WindowDataset,
    references: dict[str, Any],
    event_context: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict[str, Any]], dict[str, Any]]:
    """Generate reference predictions and metrics for one window."""
    base = _window_base(dataset)
    y_validation = dataset.validation_y[dataset.y_column]

    persistence = persistence_reference(dataset.validation_X, horizon=dataset.horizon)
    prevalence, train_prevalence = train_prevalence_reference(
        dataset.train_y[dataset.y_column],
        rows=len(y_validation),
    )

    prediction_frames: list[pd.DataFrame] = []
    metrics: list[dict[str, Any]] = []

    for name, frame in (("persistence", persistence), ("train_prevalence", prevalence)):
        overlap = [column for column in frame.columns if column in base.columns]
        merged = pd.concat([base, frame.drop(columns=overlap)], axis=1)
        merged["train_prevalence"] = (
            pd.Series([train_prevalence] * len(merged), dtype="Float64")
            if name == "train_prevalence"
            else pd.Series([pd.NA] * len(merged), dtype="Float64")
        )
        prediction_frames.append(merged)
        threshold_declared = references[name].get("threshold_policy") is not None
        metric_rows = evaluate_metrics(
            name,
            y_validation,
            frame,
            dataset.validation_index,
            target_column=dataset.target_column,
            threshold_policy_declared=threshold_declared,
            event_context=event_context,
        )
        for row in metric_rows:
            row["window_id"] = dataset.window_id
            row["cutoff"] = dataset.cutoff
            row["horizon"] = dataset.horizon
            row["train_prevalence"] = train_prevalence
        metrics.extend(metric_rows)

    window_summary = {
        "window_id": dataset.window_id,
        "cutoff": dataset.cutoff,
        "horizon": dataset.horizon,
        "train_rows": len(dataset.train_y),
        "validation_rows": len(dataset.validation_y),
        "train_prevalence": train_prevalence,
    }
    return pd.concat(prediction_frames, ignore_index=True), metrics, window_summary


def probability_frame(probability: pd.Series, name: str = "xgboost") -> pd.DataFrame:
    """Create shared metric inputs with explicitly unavailable event alerts.

    Args:
        probability: Key-aligned binary probabilities.
        name: Family or ablation identifier.

    Returns:
        Shared prediction schema, with no provisional operational threshold.
    """
    return pd.DataFrame(
        dict(
            reference=name,
            prediction_kind="probabilistic",
            prediction_score=probability,
            prediction_probability=probability,
            prediction_label=pd.Series(pd.NA, index=probability.index, dtype="Int64"),
        )
    )


def diagnostic_scores(y: pd.Series, probability: pd.Series) -> dict[str, Any]:
    """Report only existing AP/Brier plus support, validity and constancy diagnostics.

    Args:
        y: Observed binary labels for this diagnostic population.
        probability: Aligned probabilities.

    Returns:
        Scores and explicit support/evaluability; no new ranking metric.
    """
    return dict(
        rows=len(y),
        positives=int(y.sum()),
        ap=average_precision_metric(y, probability)["value"],
        brier=brier_metric(y, probability)["value"],
        invalid_predictions=int((~np.isfinite(probability)).sum()),
        constant_predictions=bool(probability.nunique() <= 1),
    )
