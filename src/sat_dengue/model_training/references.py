"""Simple Stage 4 references: persistence and train-prevalence."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .contract import ModelTrainingError

ZONE_TO_LABEL = {
    "EXITO": 0,
    "SEGURIDAD": 0,
    "ALERTA": 0,
    "EXCESO": 1,
}


def persistence_reference(validation_X: pd.DataFrame, *, horizon: int) -> pd.DataFrame:
    """Project current endemic state to T+h as a deterministic alert.

    Args:
        validation_X: Raw validation predictors containing zona_canal_t.
        horizon: Forecast horizon in months.

    Returns:
        Deterministic reference columns for evaluation.

    Raises:
        ModelTrainingError: If required columns are missing.
    """
    if "zona_canal_t" not in validation_X.columns:
        raise ModelTrainingError("Persistence reference requires zona_canal_t")
    zone = validation_X["zona_canal_t"].astype("string")
    label = zone.map(ZONE_TO_LABEL).astype("Int64")
    unknown = zone.isna() | ~zone.isin(list(ZONE_TO_LABEL))
    label = label.mask(unknown)
    score = label.astype("Float64")
    reason = pd.Series(pd.NA, index=validation_X.index, dtype="string")
    reason = reason.mask(unknown, "non_evaluable_zone_state")
    return pd.DataFrame(
        {
            "reference": "persistence",
            "horizon": horizon,
            "prediction_label": label,
            "prediction_score": score,
            "prediction_probability": pd.Series(pd.NA, index=validation_X.index, dtype="Float64"),
            "state_evaluable": (~unknown).astype("boolean"),
            "non_evaluable_reason": reason,
            "reference_formula": (
                "predict_excess_t_plus_h = 1 if zona_canal_t == 'EXCESO' else 0; "
                "unknown/missing state => non-evaluable"
            ),
            "prediction_kind": "deterministic",
        }
    )


def train_prevalence_reference(train_y: pd.Series, rows: int) -> tuple[pd.DataFrame, float]:
    """Estimate a constant probability from Y_train only.

    Args:
        train_y: Training labels for one window/horizon.
        rows: Number of prediction rows to emit.

    Returns:
        Constant-probability predictions and the fitted prevalence.

    Raises:
        ModelTrainingError: If training labels are empty or non-binary.
    """
    clean = train_y.dropna().astype("Int64")
    if clean.empty or not clean.isin([0, 1]).all():
        raise ModelTrainingError("Train prevalence requires non-empty binary Y_train")
    prevalence = float(clean.mean())
    probability = pd.Series([prevalence] * rows, dtype="Float64")
    return (
        pd.DataFrame(
            {
                "reference": "train_prevalence",
                "horizon": pd.Series([pd.NA] * rows, dtype="Int64"),
                "prediction_label": pd.Series([pd.NA] * rows, dtype="Int64"),
                "prediction_score": probability,
                "prediction_probability": probability,
                "state_evaluable": pd.Series([True] * rows, dtype="boolean"),
                "non_evaluable_reason": pd.Series([pd.NA] * rows, dtype="string"),
                "reference_formula": (
                    "predict_probability = mean(Y_train for the same cutoff and horizon)"
                ),
                "prediction_kind": "probabilistic",
            }
        ),
        prevalence,
    )


def reference_overview(prevalence: float) -> dict[str, Any]:
    """Return bounded metadata for logs and manifests.

    Args:
        prevalence: Fitted training prevalence.

    Returns:
        Compact reference summary.
    """
    return {
        "persistence": {
            "type": "deterministic",
            "note": "binary alerts from current endemic zone state",
        },
        "train_prevalence": {
            "type": "probabilistic",
            "train_prevalence": prevalence,
            "train_only": True,
        },
    }
