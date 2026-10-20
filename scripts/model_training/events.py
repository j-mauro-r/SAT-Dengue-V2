"""Retrospective event context, isolated from predictors and reference fitting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd  # type: ignore[import-untyped]

from scripts.training_preparation.temporal import read_artifact

from .contract import ModelTrainingConfig, ModelTrainingError, read_json

if TYPE_CHECKING:
    from .loading import TemporalSource


def build_event_context(
    index: pd.DataFrame,
    states: pd.DataFrame,
    *,
    target_column: str,
    target_start: str = "2012-01",
    reserved_start: str = "2025-01",
) -> pd.DataFrame:
    """Join observed excess at target S and exactly S-1 for evaluation only.

    Args:
        index: Selected prediction keys, in their evaluation order.
        states: Scientific states with municipality_code, target_period and excess.
        target_column: Selected target-month column, independent of forecast origin.
        target_start: First permitted development target.
        reserved_start: First forbidden final-block target.

    Returns:
        Keyed nullable onset context. Missing months are never replaced by prior rows.

    Raises:
        ModelTrainingError: If keys, periods or observed binary states are invalid.
    """
    keys = (
        index[["municipality_code", target_column]]
        .rename(columns={target_column: "target_period"})
        .astype("string")
        .reset_index(drop=True)
    )
    if keys.isna().any().any() or keys.duplicated().any():
        raise ModelTrainingError("Event keys must be unique and nonmissing")
    periods = pd.PeriodIndex(keys["target_period"], freq="M")
    if list(periods.astype(str)) != keys["target_period"].tolist():
        raise ModelTrainingError("Event targets must be canonical calendar months")
    if not keys["target_period"].between(target_start, reserved_start, inclusive="left").all():
        raise ModelTrainingError("Event targets outside development")
    keys["previous_target_period"] = (periods - 1).astype(str)
    source = states[["municipality_code", "target_period", "excess"]].copy()
    source[["municipality_code", "target_period"]] = source[
        ["municipality_code", "target_period"]
    ].astype("string")
    if (
        source[["municipality_code", "target_period"]].isna().any().any()
        or source.duplicated(["municipality_code", "target_period"]).any()
    ):
        raise ModelTrainingError("Scientific event-state keys are invalid")
    source["excess"] = source["excess"].astype("Int64")
    if not source["excess"].dropna().isin([0, 1]).all():
        raise ModelTrainingError("Scientific excess must be binary or unknown")
    lookup = source.set_index(["municipality_code", "target_period"])["excess"]
    for column, month in (
        ("actual_excess", "target_period"),
        ("previous_excess", "previous_target_period"),
    ):
        requested = pd.MultiIndex.from_arrays([keys["municipality_code"], keys[month]])
        keys[column] = pd.array(lookup.reindex(requested), dtype="Int64")
    known = keys["actual_excess"].notna() & keys["previous_excess"].notna()
    keys["onset_evaluable"] = known
    keys["actual_onset"] = (
        (keys["actual_excess"].eq(1) & keys["previous_excess"].eq(0)).where(known).astype("boolean")
    )
    keys["context_status"] = "known"
    keys.loc[keys["previous_excess"].isna(), "context_status"] = "unknown_previous_month"
    keys.loc[keys["actual_excess"].isna(), "context_status"] = "unknown_target_month"
    return keys


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
