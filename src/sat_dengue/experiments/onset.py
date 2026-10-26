"""Pure EXP01 eligibility, retrospective labels and strictly historical channel.

No I/O, estimator, Kedro or MLflow belongs in this module. Operational eligibility
has a deliberately smaller interface than retrospective outcome construction.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import history_periods_for_target, percentile_type7

KEYS = ["municipality_code", "year_month"]


def validate_keys(frame: pd.DataFrame) -> None:
    if not set(KEYS) <= set(frame) or frame[KEYS].isna().any().any():
        raise ValueError("Missing municipality/month keys")
    if frame.duplicated(KEYS).any():
        raise ValueError("Duplicate municipality/month")
    pd.PeriodIndex(frame.year_month, freq="M")


def operational_eligibility(current_excess: pd.Series) -> pd.Series:
    """Both horizons require observed non-excess at T, never T+1/T+2."""
    if not current_excess.dropna().isin([0, 1]).all():
        raise ValueError("Current excess must be binary or unavailable")
    return current_excess.eq(0).fillna(False).astype(bool)


def labels(states: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Use exact calendar predecessors; missing months are never bridged.

    T+2 earlier onsets are negatives, including continuing episodes. Unknown
    outcomes remain unavailable and never change operational eligibility.
    """
    validate_keys(states)
    if horizon not in (1, 2) or not states.excess.dropna().isin([0, 1]).all():
        raise ValueError("Invalid horizon or excess state")
    result = states[KEYS].copy()
    lookup = states.set_index(KEYS).excess.to_dict()
    target, previous = [], []
    for municipality, origin in result.itertuples(index=False, name=None):
        month = pd.Period(origin, freq="M")
        target.append(lookup.get((municipality, str(month + horizon)), pd.NA))
        previous.append(lookup.get((municipality, str(month + horizon - 1)), pd.NA))
    result["eligible_at_t"] = operational_eligibility(states.excess)
    result["target_month"] = [str(pd.Period(v, freq="M") + horizon) for v in states.year_month]
    future = pd.Series(target, index=result.index, dtype="Int64")
    preceding = pd.Series(previous, index=result.index, dtype="Int64")
    result["excess_target"] = future
    result["onset_target"] = (preceding.eq(0) & future.eq(1)).astype("Int64")
    result.loc[preceding.isna() | future.isna(), "onset_target"] = pd.NA
    result["earlier_onset_t1"] = (
        operational_eligibility(states.excess)
        & pd.Series(
            [
                lookup.get((m, str(pd.Period(t, freq="M") + 1)), pd.NA)
                for m, t in states[KEYS].itertuples(index=False, name=None)
            ],
            index=result.index,
            dtype="Int64",
        ).eq(1)
    ).fillna(False)
    return result


def historical_state(
    panel: pd.DataFrame, municipality: str, period: str, *, as_of: str
) -> tuple[int | None, tuple[str, ...]]:
    """Recompute P75 from five same-month prior years available by as_of.

    Future counts can supply retrospective outcomes only. Reference percentiles
    never consult observations after the forecast origin.
    """
    validate_keys(panel)
    history = tuple(history_periods_for_target(period, 5))
    if period > as_of or any(month > as_of for month in history):
        return None, history
    counts = panel.set_index(KEYS).dengue_notifications_count.to_dict()
    values = [counts.get((municipality, month)) for month in history]
    count = counts.get((municipality, period))
    if any(v is None or pd.isna(v) for v in [*values, count]):
        return None, history
    if not np.isfinite(np.asarray([*values, count], dtype=float)).all():
        raise ValueError("Nonfinite channel count")
    return int(float(count) > percentile_type7([float(v) for v in values], 0.75)), history


def predictor_projection(
    frame: pd.DataFrame, allowed: Sequence[str], availability: dict[str, int]
) -> pd.DataFrame:
    """Closed predictor allowlist plus explicit availability relative to T."""
    if list(frame.columns) != list(allowed) or set(availability) != set(allowed):
        raise ValueError("Predictors must match the frozen ordered allowlist")
    if any(not isinstance(availability[name], int) or availability[name] > 0 for name in allowed):
        raise ValueError("Future predictor availability")
    if any(
        name.startswith(("y_", "target_", "onset_", "eligible_", "p75_t"))
        or name in {"excess_target", "earlier_onset_t1"}
        for name in allowed
    ):
        raise ValueError("Future label/control is forbidden in predictors")
    return frame.copy(deep=True)


def partitions(cohort: pd.DataFrame, window: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Assign labels by observation time and embargo origins after prior roles.

    Every fitted role excludes 2024/2025. Stress 2024 is evaluation-only. End
    dates are target dates, so no horizon may cross a fitting cutoff.
    """
    validate_keys(cohort)
    roles = ("train", "calibration", "selection", "evaluation")
    previous_end = None
    output = {}
    for role in roles:
        start, end = window[role]
        pd.Period(start, freq="M")
        pd.Period(end, freq="M")
        if start > end or (previous_end is not None and start <= previous_end):
            raise ValueError("Temporal roles overlap or are unordered")
        if end >= "2025-01" or (role != "evaluation" and end >= "2024-01"):
            raise ValueError("Consumed 2025 and stress 2024 cannot fit or select")
        if (
            role == "evaluation"
            and end >= "2024-01"
            and window.get("evidence_type") != "retrospective_stress"
        ):
            raise ValueError("2024 evaluation must be declared retrospective stress")
        mask = cohort.target_month.between(start, end)
        if previous_end is not None:
            mask &= cohort.year_month.ge(previous_end)
        output[role] = cohort.loc[mask & cohort.eligible_at_t].copy()
        previous_end = end
    return output
