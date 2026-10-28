"""Causal exact-calendar trajectory features for EXP03.1.

The module performs no I/O. Covered missing notification rows become zero cases;
uncovered or absent calendar months stay unknown. Each historical zone is
reconstructed at its own month from its five prior same-calendar-month values.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

KEYS = ["municipality_code", "year_month"]
COUNT = "dengue_notifications_count"
STATES = ("EXITO", "SEGURIDAD", "ALERTA", "EXCESO")
PREDICTORS = (
    "channel_security_recent_6m_count",
    "channel_warning_recent_6m_count",
    "channel_excess_recent_6m_count",
    "channel_security_change_6m",
    "channel_warning_change_6m",
    "channel_excess_change_6m",
)


def _month(value: str) -> pd.Period:
    if not isinstance(value, str) or pd.Period(value, freq="M").strftime("%Y-%m") != value:
        raise ValueError("EXP03.1 requires canonical YYYY-MM months")
    return pd.Period(value, freq="M")


def _lookup(panel: pd.DataFrame) -> dict[tuple[str, str], float | None]:
    required = {*KEYS, COUNT, "covered"}
    if not required.issubset(panel) or panel.duplicated(KEYS).any():
        raise ValueError("EXP03.1 panel requires unique keys, count and covered")
    values: dict[tuple[str, str], float | None] = {}
    for municipality, month, count, covered in panel[[*KEYS, COUNT, "covered"]].itertuples(
        index=False, name=None
    ):
        if _month(month) > pd.Period("2024-12", freq="M"):
            raise ValueError("EXP03.1 rejects 2025 and later observations")
        if not isinstance(covered, (bool, np.bool_)):
            raise ValueError("covered must be boolean")
        if not covered:
            values[str(municipality), month] = None
        elif pd.isna(count):
            values[str(municipality), month] = 0.0
        else:
            number = float(count)
            if not np.isfinite(number) or number < 0:
                raise ValueError("covered counts must be finite nonnegative values")
            values[str(municipality), month] = number
    return values


def historical_zone(
    values: dict[tuple[str, str], float | None], municipality: str, event_month: pd.Period
) -> str | None:
    """Reconstruct one zone with data available no later than its event month."""
    observed = values.get((municipality, str(event_month)))
    history = [values.get((municipality, str(event_month - 12 * year))) for year in range(1, 6)]
    if observed is None or any(value is None for value in history):
        return None
    reference = np.asarray(history, dtype=float)
    p25, p50, p75 = np.quantile(reference, [0.25, 0.5, 0.75], method="linear")
    return (
        "EXITO"
        if observed < p25
        else "SEGURIDAD"
        if observed <= p50
        else "ALERTA"
        if observed <= p75
        else "EXCESO"
    )


def _counts(zones: list[str]) -> dict[str, int]:
    return {state: zones.count(state) for state in STATES}


def trajectory_features(panel: pd.DataFrame, origins: pd.DataFrame) -> pd.DataFrame:
    """Build predictors and audit values for explicit municipality/origin keys."""
    if list(origins.columns) != KEYS or origins.duplicated(KEYS).any():
        raise ValueError("origins must contain unique municipality_code/year_month keys")
    values = _lookup(panel)
    rows: list[dict[str, Any]] = []
    for municipality, origin_text in origins.itertuples(index=False, name=None):
        municipality = str(municipality)
        origin = _month(origin_text)
        if origin > pd.Period("2024-12", freq="M"):
            raise ValueError("EXP03.1 rejects 2025 and later origins")
        recent_months = [origin - offset for offset in range(1, 7)]
        prior_months = [origin - offset for offset in range(7, 13)]
        recent_zones = [historical_zone(values, municipality, month) for month in recent_months]
        prior_zones = [historical_zone(values, municipality, month) for month in prior_months]
        known_recent = sum(zone is not None for zone in recent_zones)
        known_prior = sum(zone is not None for zone in prior_zones)
        complete = known_recent == known_prior == 6
        row: dict[str, Any] = {
            "municipality_code": municipality,
            "year_month": origin_text,
            "channel_recent_6m_known": known_recent,
            "channel_prior_6m_known": known_prior,
            "channel_trajectory_known": complete,
            "channel_trajectory_exclusion_reason": None
            if complete
            else "unknown_recent_state"
            if known_recent < 6
            else "unknown_prior_state",
            "channel_recent_source_months": [str(month) for month in recent_months],
            "channel_prior_source_months": [str(month) for month in prior_months],
        }
        if complete:
            recent = _counts([str(zone) for zone in recent_zones])
            prior = _counts([str(zone) for zone in prior_zones])
            for state, slug in (
                ("SEGURIDAD", "security"),
                ("ALERTA", "warning"),
                ("EXCESO", "excess"),
            ):
                row[f"channel_{slug}_recent_6m_count"] = recent[state]
                row[f"channel_{slug}_prior_6m_count"] = prior[state]
                row[f"channel_{slug}_change_6m"] = recent[state] - prior[state]
            row["channel_success_recent_6m_count_audit"] = recent["EXITO"]
            row["channel_success_prior_6m_count_audit"] = prior["EXITO"]
        else:
            for name in PREDICTORS:
                row[name] = pd.NA
            for name in (
                "channel_security_prior_6m_count",
                "channel_warning_prior_6m_count",
                "channel_excess_prior_6m_count",
                "channel_success_recent_6m_count_audit",
                "channel_success_prior_6m_count_audit",
            ):
                row[name] = pd.NA
        for name in PREDICTORS:
            row[f"{name}__latest_source_month"] = str(origin - 1)
        rows.append(row)
    result = pd.DataFrame(rows)
    for name in (*PREDICTORS, "channel_recent_6m_known", "channel_prior_6m_known"):
        result[name] = result[name].astype("Int64")
    return result


def paired_cohort(
    frame: pd.DataFrame,
    *,
    base_predictors: Iterable[str],
    labels: Iterable[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return one common row set and an explicit exclusion ledger."""
    required = [*KEYS, *base_predictors, *labels, *PREDICTORS, "channel_trajectory_known"]
    missing = [name for name in required if name not in frame]
    if missing or frame.duplicated(KEYS).any():
        raise ValueError("Invalid paired cohort input: " + ",".join(missing))
    known_trajectory = frame["channel_trajectory_known"].astype(bool)
    base_known = frame[list(base_predictors)].notna().all(axis=1)
    labels_known = frame[list(labels)].notna().all(axis=1)
    included = known_trajectory & base_known & labels_known
    ledger = frame[KEYS].copy()
    ledger["included"] = included
    ledger["exclusion_reason"] = np.select(
        [~known_trajectory, ~base_known, ~labels_known],
        ["unknown_channel_history", "missing_v09_predictor", "unknown_label"],
        default="included",
    )
    return frame.loc[included].copy(), ledger
