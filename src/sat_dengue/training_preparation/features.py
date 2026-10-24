"""Deterministic calendar-keyed candidate features, without fitting or eligibility cuts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationError

KEYS = ["municipality_code", "year_month"]
DERIVED_COLUMNS = (
    "dengue_lag_1",
    "dengue_lag_2",
    "dengue_lag_3",
    "grave_lag_1",
    "grave_lag_2",
    "dengue_cambio_1m",
    "dengue_media_3m",
    "zona_canal_lag_1",
    "lluvia_lag_1",
    "lluvia_lag_2",
    "temperatura_lag_1",
    "temperatura_lag_2",
    "rocio_lag_1",
    "escorrentia_lag_1",
    "mes_sin",
    "mes_cos",
)


def calendar_lookup(panel: pd.DataFrame, source: str, months: int) -> pd.Series:
    """Look up a municipal observation at exactly T minus calendar months.

    Args:
        panel: Unique keyed rows in any order, including all needed history.
        source: Source column to retrieve.
        months: Positive lag in calendar months.

    Returns:
        Values aligned to the input rows; absent keys remain missing.
    """
    periods = pd.PeriodIndex(panel["year_month"], freq="M")
    index = pd.MultiIndex.from_arrays([panel["municipality_code"], periods])
    requested = pd.MultiIndex.from_arrays([panel["municipality_code"], periods - months])
    lookup = pd.Series(panel[source].array, index=index)
    return pd.Series(lookup.reindex(requested).array, index=panel.index)


def derive_features(panel: pd.DataFrame, contract: dict[str, Any]) -> pd.DataFrame:
    """Build the sixteen candidates using full earlier municipal history.

    Args:
        panel: Input history, not prefiltered by supervised eligibility.
        contract: Preparation contract with exact derived feature definitions.

    Returns:
        Sorted keys, unchanged current candidate columns and derived columns.

    Raises:
        PreparationError: If keys or definitions are invalid or collide with inputs.
    """
    definitions = contract["derived_features"]
    if set(definitions) != set(DERIVED_COLUMNS):
        raise PreparationError("Expected exactly the sixteen approved derived columns")
    if panel[KEYS].isna().any().any() or panel.duplicated(KEYS).any():
        raise PreparationError("Feature input requires unique, non-null calendar keys")
    if not panel["year_month"].str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise PreparationError("Invalid feature calendar keys")
    if set(DERIVED_COLUMNS) & set(panel.columns):
        raise PreparationError("Derived columns already present; refusing overwrite")
    frame = panel.sort_values(KEYS).reset_index(drop=True)
    result = frame[KEYS + contract["roles"]["predictors"]].copy()
    for name in DERIVED_COLUMNS:
        definition = definitions[name]
        if definition["operation"] == "lag":
            if definition["months"] < 1:
                raise PreparationError("Only positive past calendar lags are permitted")
            result[name] = calendar_lookup(frame, definition["source"], definition["months"])
    counts = frame["dengue_notifications_count"].astype("Float64")
    lag1 = result["dengue_lag_1"].astype("Float64")
    lag2 = result["dengue_lag_2"].astype("Float64")
    result["dengue_cambio_1m"] = counts - lag1
    observations = pd.concat([counts, lag1, lag2], axis=1)
    result["dengue_media_3m"] = observations.mean(axis=1).where(observations.notna().all(axis=1))
    phase = 2 * np.pi * (pd.PeriodIndex(frame["year_month"], freq="M").month - 1) / 12
    result["mes_sin"] = np.sin(phase)
    result["mes_cos"] = np.cos(phase)
    for name in DERIVED_COLUMNS:
        result[name] = result[name].astype("string" if name == "zona_canal_lag_1" else "Float64")
    return result[KEYS + contract["roles"]["predictors"] + list(DERIVED_COLUMNS)]
