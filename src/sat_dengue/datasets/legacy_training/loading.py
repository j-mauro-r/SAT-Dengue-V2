"""Verified access to Stage 3 temporal artifacts for Stage 4 references."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.datasets.legacy_preparation.temporal import build_temporal, read_artifact
from sat_dengue.model_training.loading import WindowDataset as WindowDataset
from sat_dengue.model_training.loading import _validate_alignment as _validate_alignment
from sat_dengue.model_training.loading import parse_window_id as parse_window_id

from .contract import ModelTrainingConfig, read_json

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
