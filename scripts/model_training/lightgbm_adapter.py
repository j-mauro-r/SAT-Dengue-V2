"""Small deterministic CPU LightGBM adapter with native text persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .candidate_preparation import fit_representation, transform_representation, validate_training
from .contract import ModelTrainingError


@dataclass
class FittedLightGBM:
    """Native binary booster and training-only one-hot state.

    Args:
        model: Native LightGBM booster.
        preparer: Frozen Stage3-compatible JSON state.
    """

    model: lgb.Booster
    preparer: dict[str, Any]

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Predict binary probabilities using frozen preparation.

        Args:
            X: Ordered raw predictors.

        Returns:
            Finite aligned probabilities.
        """
        matrix = transform_representation(X, self.preparer).to_numpy(dtype=float)
        values = np.asarray(self.model.predict(matrix, num_threads=1), dtype=float)
        if not np.isfinite(values).all() or not ((values >= 0) & (values <= 1)).all():
            raise ModelTrainingError("Invalid LightGBM probabilities")
        return pd.Series(values, index=X.index)

    def model_bytes(self) -> bytes:
        """Return native text, never an executable object snapshot."""
        return self.model.model_to_string().encode()


def restore_candidate(model_bytes: bytes, preparer: dict[str, Any]) -> FittedLightGBM:
    """Restore a locally trusted verified model without fitting.

    Args:
        model_bytes: Native LightGBM text.
        preparer: Corresponding JSON preparation.

    Returns:
        Inference object.
    """
    return FittedLightGBM(lgb.Booster(model_str=model_bytes.decode()), preparer)


def fit_candidate(
    X: pd.DataFrame, y: pd.Series, parameters: dict[str, Any], *, seed: int, threads: int
) -> FittedLightGBM:
    """Fit on training only, with no evaluation set or early stopping.

    Args:
        X: Raw training predictors.
        y: Aligned binary training labels.
        parameters: Predeclared tree complexity, rate and penalty.
        seed: Fixed random seed.
        threads: Explicit CPU thread count.

    Returns:
        Native binary booster and fitted representation.
    """
    validate_training(X, y)
    preparer = fit_representation(X)
    matrix = transform_representation(X, preparer).to_numpy(dtype=float)
    params = {k: v for k, v in parameters.items() if k != "n_estimators"}
    params.update(
        objective="binary",
        metric="None",
        verbosity=-1,
        seed=seed,
        num_threads=threads,
        deterministic=True,
        force_col_wise=True,
        feature_fraction=1.0,
        bagging_fraction=1.0,
        bagging_freq=0,
        is_unbalance=False,
        scale_pos_weight=1.0,
    )
    model = lgb.train(
        params,
        lgb.Dataset(matrix, label=y.to_numpy(dtype=int)),
        num_boost_round=parameters["n_estimators"],
    )
    return FittedLightGBM(model, preparer)
