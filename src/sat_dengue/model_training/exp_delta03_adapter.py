"""Single-family native-missing XGBoost adapter; no preparation, policy or tracking."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03_retrospective import values_hash
from sat_dengue.experiments.exp_delta03_contract import digest


def matrix(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    if list(frame) != columns or len(set(columns)) != len(columns):
        raise ValueError("Model column order/schema changed")
    if not all(pd.api.types.is_numeric_dtype(frame[n]) for n in columns):
        raise ValueError("Only declared numeric predictors are supported")
    x = frame.to_numpy(dtype="float64", na_value=np.nan)
    if np.isinf(x).any():
        raise ValueError("Infinite predictor")
    return x


@dataclass
class NativeModel:
    booster: Any
    metadata: dict[str, Any]

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        import xgboost as xgb

        x = matrix(frame, self.metadata["columns"])
        values = self.booster.predict(xgb.DMatrix(x, feature_names=list(frame), nthread=1))
        if not np.isfinite(values).all() or not ((values >= 0) & (values <= 1)).all():
            raise ValueError("Invalid model probabilities")
        return np.asarray(values, dtype="float64")

    def serialize(self) -> bytes:
        return bytes(self.booster.save_raw(raw_format="ubj"))


def fit_native(
    frame: pd.DataFrame, truth: pd.Series, parameters: dict[str, Any], *, cohort_sha256: str
) -> NativeModel:
    """Fit only caller-authorized training rows; the execution boundary owns authority."""
    import xgboost as xgb

    if not frame.index.equals(truth.index):
        raise ValueError("Misaligned training labels")
    x = matrix(frame, list(frame))
    y = truth.to_numpy(dtype=float)
    if len(y) != len(x) or len(np.unique(y)) != 2 or not np.isin(y, [0, 1]).all():
        raise ValueError("Two binary training classes required")
    if np.isnan(x).all(axis=0).any():
        raise ValueError("All-null training predictor")
    if (
        parameters["n_jobs"] != 1
        or parameters["tree_method"] != "hist"
        or parameters["objective"] != "binary:logistic"
        or parameters["device"] != "cpu"
    ):
        raise ValueError("Only single-thread histogram XGBoost is supported")
    params = dict(parameters)
    rounds = params.pop("n_estimators")
    params["nthread"] = params.pop("n_jobs")
    params["seed"] = params.pop("random_state")
    if not isinstance(rounds, int) or rounds < 1:
        raise ValueError("Invalid booster round count")
    booster = xgb.train(
        params,
        xgb.DMatrix(x, label=y, feature_names=list(frame), nthread=1),
        num_boost_round=rounds,
    )
    raw = bytes(booster.save_raw(raw_format="ubj"))
    metadata = {
        "schema": "exp-delta03-model-v1",
        "family": "xgboost",
        "format": "ubj",
        "columns": list(frame),
        "dtype": "float64",
        "parameters": parameters,
        "parameters_sha256": digest(parameters),
        "xgboost_version": xgb.__version__,
        "cohort_sha256": cohort_sha256,
        "training_X_sha256": values_hash(frame),
        "model_sha256": hashlib.sha256(raw).hexdigest(),
    }
    return NativeModel(booster, metadata)


def reload_native(raw: bytes, metadata: dict[str, Any]) -> NativeModel:
    import xgboost as xgb

    if metadata["schema"] != "exp-delta03-model-v1" or metadata["format"] != "ubj":
        raise ValueError("Unexpected native model schema")
    if hashlib.sha256(raw).hexdigest() != metadata["model_sha256"]:
        raise ValueError("Native model identity mismatch")
    if digest(metadata["parameters"]) != metadata["parameters_sha256"]:
        raise ValueError("Model parameter identity mismatch")
    if metadata["xgboost_version"] != xgb.__version__:
        raise ValueError("Model runtime version mismatch")
    booster = xgb.Booster(params={"nthread": 1})
    booster.load_model(bytearray(raw))
    if booster.feature_names != metadata["columns"]:
        raise ValueError("Stored native feature schema mismatch")
    return NativeModel(booster, metadata)
