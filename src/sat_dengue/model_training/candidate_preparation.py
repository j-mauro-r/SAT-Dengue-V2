"""Shared train-only representation and explicit ablation projections."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.training_preparation.preprocessing import (
    CATEGORICAL,
    PreparerSpec,
    fit_preparer,
    transform_predictors,
)

from .contract import ModelTrainingError

EVENT_CONTROLS = {
    "actual_excess",
    "previous_excess",
    "actual_onset",
    "onset_evaluable",
    "context_status",
    "previous_target_period",
}


def validate_training(X: pd.DataFrame, y: pd.Series) -> None:
    """Reject incomplete labels, misalignment and retrospective evaluation controls.

    Args:
        X: Raw training predictors.
        y: Aligned binary labels with both classes.
    """
    if not X.index.equals(y.index) or y.isna().any() or set(y.unique()) != {0, 1}:
        raise ModelTrainingError("Training requires aligned, complete binary classes")
    if EVENT_CONTROLS.intersection(X.columns):
        raise ModelTrainingError("Retrospective evaluation context is forbidden in X")


def _project(X: pd.DataFrame, excluded: list[str]) -> pd.DataFrame:
    """Remove ablated inputs and supply empty required category slots to Stage3.

    Args:
        X: Complete raw predictor schema.
        excluded: Columns removed from all estimator inputs.

    Returns:
        Stage3-compatible frame; placeholder encodings are discarded downstream.
    """
    frame = X.drop(columns=excluded).copy()
    for name in CATEGORICAL:
        if name in excluded:
            frame[name] = pd.NA
    return frame


def fit_representation(X: pd.DataFrame, excluded: list[str] | None = None) -> dict[str, Any]:
    """Fit the unchanged Stage3 one-hot function after declared feature removal.

    Args:
        X: Training predictors only.
        excluded: Explicit ablation columns, absent from fitted estimator matrix.

    Returns:
        Safe JSON preparation state including stable projected output names.
    """
    removed = excluded or []
    state = fit_preparer(_project(X, removed), PreparerSpec(encoding="onehot"))
    if removed:
        state["ablation"] = {
            "source_columns": list(X.columns),
            "excluded_columns": removed,
            "retained_columns": [
                c for c in state["output_columns"] if c.split("=", 1)[0] not in removed
            ],
        }
    return state


def transform_representation(X: pd.DataFrame, state: dict[str, Any]) -> pd.DataFrame:
    """Apply frozen preparation and remove all excluded encodings.

    Args:
        X: Raw predictors in the saved source order.
        state: Training-only preparation state.

    Returns:
        Fixed estimator matrix; no data-dependent fitting.
    """
    if "ablation" not in state:
        return transform_predictors(X, state)
    projection = state["ablation"]
    if list(X.columns) != projection["source_columns"]:
        raise ModelTrainingError("Ablation source schema/order mismatch")
    return transform_predictors(_project(X, projection["excluded_columns"]), state)[
        projection["retained_columns"]
    ]
