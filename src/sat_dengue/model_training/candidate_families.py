"""Fixed dispatch for three declared candidates, with shared operational boundaries."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from . import gam_adapter, lightgbm_adapter, xgboost_adapter
from .contract import ModelTrainingError

FittedModel = (
    xgboost_adapter.FittedCandidate | lightgbm_adapter.FittedLightGBM | gam_adapter.FittedGAM
)
ADAPTERS = {"xgboost": xgboost_adapter, "lightgbm": lightgbm_adapter, "gam": gam_adapter}


def fit_model(
    family: str,
    X: pd.DataFrame,
    y: pd.Series,
    parameters: dict[str, Any],
    *,
    seed: int,
    threads: int,
) -> FittedModel:
    """Fit one supported adapter without accepting external validation inputs.

    Args:
        family: Fixed supported family name.
        X: Training predictors only.
        y: Aligned training labels.
        parameters: Predeclared family configuration.
        seed: Fixed seed.
        threads: Explicit thread count.

    Returns:
        Model with prediction, preparation and safe persistence operations.
    """
    validate_grid(family, [parameters])
    return ADAPTERS[family].fit_candidate(X, y, parameters, seed=seed, threads=threads)


def restore_model(family: str, data: bytes, preparer: dict[str, Any]) -> FittedModel:
    """Restore one verified local model using its declared family format.

    Args:
        family: Supported adapter name.
        data: Verified native or numeric JSON bytes.
        preparer: Matching train-only state.

    Returns:
        Inference object.
    """
    if family not in ADAPTERS:
        raise ModelTrainingError("Unsupported candidate family")
    return ADAPTERS[family].restore_candidate(data, preparer)


def validate_grid(family: str, grid: list[dict[str, Any]]) -> None:
    """Reject undeclared parameters and unbounded complexity before fitting.

    Args:
        family: Supported adapter.
        grid: At most six frozen configurations.
    """
    if family not in ADAPTERS or not 1 <= len(grid) <= 6:
        raise ModelTrainingError("Unsupported candidate family or search budget")
    for p in grid:
        if family == "gam":
            valid = set(p) == {"n_knots", "C"} and 3 <= p["n_knots"] <= 8 and 0 < p["C"] <= 10
        elif family == "lightgbm":
            valid = (
                set(p)
                == {
                    "n_estimators",
                    "num_leaves",
                    "max_depth",
                    "learning_rate",
                    "lambda_l1",
                    "lambda_l2",
                    "max_bin",
                    "min_data_in_leaf",
                }
                and 1 <= p["n_estimators"] <= 500
                and 2 <= p["num_leaves"] <= 64
                and 1 <= p["max_depth"] <= 8
                and 0 < p["learning_rate"] <= 1
                and 2 <= p["max_bin"] <= 256
                and min(p["lambda_l1"], p["lambda_l2"], p["min_data_in_leaf"]) >= 0
            )
        else:
            valid = (
                set(p)
                == {
                    "n_estimators",
                    "max_depth",
                    "eta",
                    "reg_lambda",
                    "reg_alpha",
                    "max_bin",
                    "min_child_weight",
                }
                and 1 <= p["n_estimators"] <= 500
                and 1 <= p["max_depth"] <= 8
                and 0 < p["eta"] <= 1
                and 2 <= p["max_bin"] <= 256
                and min(p["reg_lambda"], p["reg_alpha"], p["min_child_weight"]) >= 0
            )
        if not valid:
            raise ModelTrainingError(f"Invalid bounded {family} parameter grid")


def simplicity(family: str, features: int, p: dict[str, Any], state: dict[str, Any]) -> list[float]:
    """Compute the already-approved within-family lexicographic simplicity tuple.

    Args:
        family: Supported family.
        features: Raw input feature count.
        p: Candidate parameters.
        state: Fitted representation for exact basis counting.

    Returns:
        Approved tuple; never comparable across families.
    """
    if family == "gam":
        return [
            0,
            len(state["gam"]["output_columns"]),
            sum(t["kind"] == "spline" for t in state["gam"]["terms"]),
            -1 / p["C"],
        ]
    trees = [p["max_depth"] or float("inf"), p["n_estimators"], p["max_bin"]]
    return [features, p["num_leaves"], *trees] if family == "lightgbm" else [features, *trees]
