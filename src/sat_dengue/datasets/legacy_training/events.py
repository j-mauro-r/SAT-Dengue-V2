"""Retrospective event context, isolated from predictors and reference fitting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.temporal import read_artifact
from sat_dengue.model_training.events import build_event_context as build_event_context

from .contract import ModelTrainingConfig, ModelTrainingError, read_json

if TYPE_CHECKING:
    from .loading import TemporalSource


def load_event_context(
    config: ModelTrainingConfig,
    source: TemporalSource,
    index: pd.DataFrame,
    *,
    target_column: str,
) -> pd.DataFrame:
    """Read only requested development states from the verified scientific bundle.

    Args:
        config: Repository paths; no inputs are rewritten.
        source: Already verified Stage 3 temporal source and manifest lineage.
        index: Selected evaluation rows, never used as training predictors here.
        target_column: Horizon-specific target month.

    Returns:
        Evaluation-only context from approved zona_canal_t, without recomputing Y/P75.
    """
    settings = source.manifest["identity"]["configuration"]
    selected_targets = index[target_column].astype("string")
    if (
        selected_targets.isna().any()
        or not selected_targets.between(settings["target_start"], "2025-01", inclusive="left").all()
    ):
        raise ModelTrainingError("Event targets outside development")
    bundle = config.resolve(source.manifest["development_bundle"])
    manifest = read_json(bundle / "manifest.json")
    keys = read_artifact(bundle, "keys.csv", manifest, dtype="string")
    # Hash the complete file, parse only the necessary scientific-state column.
    zones = read_artifact(
        bundle, "features.csv", manifest, usecols=["zona_canal_t"], dtype="string"
    )
    requested = index[["municipality_code", target_column]].astype("string")
    targets = pd.PeriodIndex(requested[target_column], freq="M")
    needed = set(zip(requested["municipality_code"], targets.astype(str), strict=True))
    needed.update(zip(requested["municipality_code"], (targets - 1).astype(str), strict=True))
    selected = [tuple(row) in needed for row in keys.itertuples(index=False, name=None)]
    states = keys.loc[selected].rename(columns={"year_month": "target_period"}).copy()
    scientific_zone = zones.loc[selected, "zona_canal_t"]
    valid_zones = ["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"]
    if not scientific_zone.dropna().isin(valid_zones).all():
        raise ModelTrainingError("Invalid scientific zone in requested event context")
    states["excess"] = scientific_zone.eq("EXCESO").astype("Int64")
    return build_event_context(
        index,
        states,
        target_column=target_column,
        target_start=settings["target_start"],
        reserved_start="2025-01",
    )
