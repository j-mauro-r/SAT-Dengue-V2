"""Pure retrospective S/S-1 context construction; excluded from fitting."""

import pandas as pd  # type: ignore[import-untyped]

from .contract import ModelTrainingError


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
