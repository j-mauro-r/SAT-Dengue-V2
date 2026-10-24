"""Pure window structures and exact raw-feature alignment checks."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd  # type: ignore[import-untyped]

from .contract import ModelTrainingError

KEY_COLUMNS = ["municipality_code", "year_month"]
WINDOW_RE = re.compile(r"^(?P<cutoff>\d{4}-\d{2})_t(?P<horizon>[12])$")


@dataclass(frozen=True)
class WindowDataset:
    """Train/validation rows for one cutoff-horizon window.

    Args:
        window_id: Window key such as 2024-06_t1.
        cutoff: Training cutoff month.
        horizon: Forecast horizon in months.
        target_column: Target-period column for this horizon.
        y_column: Binary target label column for this horizon.
        train_X: Raw predictors for training rows.
        train_y: Binary labels for training rows.
        train_index: Row linkage keys and metadata for training rows.
        validation_X: Raw predictors for validation rows.
        validation_y: Binary labels for validation rows.
        validation_index: Row linkage keys and metadata for validation rows.
    """

    window_id: str
    cutoff: str
    horizon: int
    target_column: str
    y_column: str
    train_X: pd.DataFrame
    train_y: pd.DataFrame
    train_index: pd.DataFrame
    validation_X: pd.DataFrame
    validation_y: pd.DataFrame
    validation_index: pd.DataFrame


def parse_window_id(window_id: str) -> tuple[str, int]:
    """Parse and validate a Stage 3 window identifier.

    Args:
        window_id: Window key in cutoff-horizon format.

    Returns:
        Tuple of cutoff month and horizon.

    Raises:
        ModelTrainingError: If format is invalid.
    """
    match = WINDOW_RE.match(window_id)
    if match is None:
        raise ModelTrainingError(f"Invalid window id: {window_id}")
    return match.group("cutoff"), int(match.group("horizon"))


def _validate_alignment(
    X: pd.DataFrame,
    y: pd.DataFrame,
    index: pd.DataFrame,
    *,
    y_column: str,
    target_column: str,
    development_X: pd.DataFrame,
) -> None:
    """Enforce row-level alignment between X, y and key metadata.

    Args:
        X: Raw predictor matrix.
        y: Binary labels.
        index: Key table including target periods.
        y_column: Label column name.
        target_column: Target-period column name.

    Raises:
        ModelTrainingError: If alignment or domain checks fail.
    """
    if not (len(X) == len(y) == len(index)):
        raise ModelTrainingError("X/y/index row counts differ")
    required_index = [*KEY_COLUMNS, target_column, "feature_row"]
    if list(index.columns) != required_index:
        raise ModelTrainingError("Unexpected index columns in temporal bundle")
    if KEY_COLUMNS[0] not in X.columns:
        raise ModelTrainingError("Raw X must include municipality_code")
    if not X[KEY_COLUMNS[0]].astype("string").equals(index[KEY_COLUMNS[0]].astype("string")):
        raise ModelTrainingError("X and index municipality order differs")
    feature_rows = index["feature_row"]
    if feature_rows.isna().any():
        raise ModelTrainingError("feature_row contains missing values")
    if feature_rows.min() < 0 or feature_rows.max() >= len(development_X):
        raise ModelTrainingError("feature_row points outside development bundle")
    expected_X = development_X.iloc[feature_rows.astype(int)].reset_index(drop=True)
    if list(X.columns) != list(expected_X.columns):
        raise ModelTrainingError("Raw X columns differ from development source columns")
    observed = X.reset_index(drop=True).copy()
    expected = expected_X.copy()
    observed["municipality_code"] = observed["municipality_code"].astype("string").str.zfill(5)
    expected["municipality_code"] = expected["municipality_code"].astype("string").str.zfill(5)
    try:
        pd.testing.assert_frame_equal(observed, expected, check_dtype=False)
    except AssertionError as exc:
        raise ModelTrainingError("Raw X rows do not match feature_row linkage order") from exc
    if list(y.columns) != [y_column]:
        raise ModelTrainingError("Unexpected y column for window")
    values = y[y_column].dropna()
    if not values.isin([0, 1]).all():
        raise ModelTrainingError("Non-binary labels in temporal bundle")
    if index.duplicated([*KEY_COLUMNS, target_column]).any():
        raise ModelTrainingError("Duplicate key-target rows in temporal index")
