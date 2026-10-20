"""Verified access to Stage 3 temporal artifacts for Stage 4 references."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from scripts.training_preparation.contract import PreparationConfig
from scripts.training_preparation.temporal import build_temporal, read_artifact

from .contract import ModelTrainingConfig, ModelTrainingError, read_json

KEY_COLUMNS = ["municipality_code", "year_month"]
WINDOW_RE = re.compile(r"^(?P<cutoff>\d{4}-\d{2})_t(?P<horizon>[12])$")


@dataclass(frozen=True)
class TemporalSource:
    """Verified Stage 3 temporal source bundle.

    Args:
        bundle: Verified temporal bundle directory.
        manifest: Temporal manifest loaded from the bundle.
        development_X: Raw development predictors indexed by feature_row.
    """

    bundle: Path
    manifest: dict[str, Any]
    development_X: pd.DataFrame


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


def load_temporal_source(config: ModelTrainingConfig) -> TemporalSource:
    """Verify and resolve the current Stage 3 temporal bundle.

    Args:
        config: Stage 4 configuration with repository root.

    Returns:
        Verified temporal source bundle and manifest.
    """
    preparation = PreparationConfig(
        root=config.root,
        contract_path=config.stage3_contract_path,
    )
    result = build_temporal(preparation, verify_only=True)
    manifest = read_json(result.bundle / "manifest.json")
    development_bundle = config.resolve(manifest["development_bundle"])
    development_manifest = read_json(development_bundle / "manifest.json")
    keys = read_artifact(
        development_bundle,
        "keys.csv",
        development_manifest,
        dtype={k: "string" for k in KEY_COLUMNS},
    )
    features = read_artifact(development_bundle, "features.csv", development_manifest)
    development_X = pd.concat(
        [keys[["municipality_code"]], features],
        axis=1,
    ).reset_index(drop=True)
    return TemporalSource(bundle=result.bundle, manifest=manifest, development_X=development_X)


def _read_window_table(
    source: TemporalSource,
    filename: str,
    *,
    dtype: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Read one hashed CSV from the verified temporal bundle.

    Args:
        source: Verified temporal source.
        filename: Manifest-declared artifact name.
        dtype: Optional pandas dtype mapping.

    Returns:
        Parsed data frame.
    """
    kwargs: dict[str, Any] = {}
    if dtype is not None:
        kwargs["dtype"] = dtype
    return read_artifact(source.bundle, filename, source.manifest, **kwargs)


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


def load_window_dataset(source: TemporalSource, window_id: str) -> WindowDataset:
    """Load one temporal window with strict alignment checks.

    Args:
        source: Verified temporal source.
        window_id: Window key like 2022-12_t2.

    Returns:
        Fully validated train/validation data for that window.
    """
    cutoff, horizon = parse_window_id(window_id)
    target_column = f"target_period_t{horizon}"
    y_column = f"y_t{horizon}"

    index_dtype = {
        "municipality_code": "string",
        "year_month": "string",
        target_column: "string",
        "feature_row": "Int64",
    }
    y_dtype = {y_column: "Int64"}

    train_X = _read_window_table(source, f"{window_id}_train_X.csv")
    train_y = _read_window_table(source, f"{window_id}_train_y.csv", dtype=y_dtype)
    train_index = _read_window_table(source, f"{window_id}_train_index.csv", dtype=index_dtype)
    validation_X = _read_window_table(source, f"{window_id}_validation_X.csv")
    validation_y = _read_window_table(source, f"{window_id}_validation_y.csv", dtype=y_dtype)
    validation_index = _read_window_table(
        source,
        f"{window_id}_validation_index.csv",
        dtype=index_dtype,
    )

    _validate_alignment(
        train_X,
        train_y,
        train_index,
        y_column=y_column,
        target_column=target_column,
        development_X=source.development_X,
    )
    _validate_alignment(
        validation_X,
        validation_y,
        validation_index,
        y_column=y_column,
        target_column=target_column,
        development_X=source.development_X,
    )

    return WindowDataset(
        window_id=window_id,
        cutoff=cutoff,
        horizon=horizon,
        target_column=target_column,
        y_column=y_column,
        train_X=train_X,
        train_y=train_y,
        train_index=train_index,
        validation_X=validation_X,
        validation_y=validation_y,
        validation_index=validation_index,
    )
