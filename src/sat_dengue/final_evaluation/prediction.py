"""Apply saved probabilities, calibration and retained alert thresholds without fitting."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.model_evaluation.calibration import _apply_saved_calibrator


def calibrate_probability(raw: pd.Series, procedure: dict[str, Any]) -> pd.Series:
    """Apply the exact retained representation; never choose or fit a calibrator."""
    calibrator = procedure["retained_calibrator"]
    choice = calibrator["calibration_choice"]
    if choice not in {"original", "sigmoid"}:
        raise ValueError("Unknown frozen calibration representation")
    return raw if choice == "original" else _apply_saved_calibrator(raw, calibrator)


def issue_alerts(probability: pd.Series, procedure: dict[str, Any]) -> pd.Series:
    """Emit alerts from the retained threshold without searching alternatives."""
    threshold = procedure["retained_threshold"]["selected_threshold"]
    if threshold is None or not np.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("Unavailable frozen threshold")
    return probability.ge(threshold).where(probability.notna()).astype("Int64")


def prediction_frame(
    raw: pd.Series, probability: pd.Series, procedure: dict[str, Any]
) -> pd.DataFrame:
    """Keep raw/calibrated scores, nullable labels and row indices aligned."""
    return pd.DataFrame(
        dict(
            prediction_kind="probabilistic",
            probability_raw=raw,
            prediction_score=probability,
            prediction_probability=probability,
            prediction_label=issue_alerts(probability, procedure),
        ),
        index=raw.index,
    )


def predict_procedure(model: Any, X: pd.DataFrame, procedure: dict[str, Any]) -> pd.DataFrame:
    """Replay the existing saved model on complete rows, retaining missing rows explicitly."""
    raw = pd.Series(pd.NA, index=X.index, dtype="Float64")
    complete = X.notna().all(axis=1)
    if complete.any():
        raw.loc[complete] = model.predict(X.loc[complete]).astype("Float64")
    return prediction_frame(raw, calibrate_probability(raw, procedure), procedure)
