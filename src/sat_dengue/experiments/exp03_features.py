"""Exact-calendar EXP03 recipes, pre-gate exposure and frozen historical profiles.

This module has no input I/O. EXP01's historical 2025 rejection is untouched;
EXP03 admits consumed-year inputs only at its explicit benchmark boundary.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03_revision import (
    CLIMATE_RECIPES,
    climate_name,
    validate_design,
)
from sat_dengue.experiments.onset import KEYS, labels, validate_keys

COUNT = "dengue_notifications_count"
SEVERE = "dengue_grave_notifications_count"


def prepare(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    horizon: int,
    *,
    allow_benchmark: bool = False,
    delay: bool = False,
) -> pd.DataFrame:
    """Reconstruct all predictors and outcomes, retaining the pre-gate population.

    `delay` affects current recipes only. Eligibility and outcomes remain those
    of the original origin; strict availability cannot establish that gate.
    Effective event months for each predictor are in attrs['source_months'].
    """
    del contract  # Explicit EXP03 recipes supersede ambiguous legacy aliases.
    validate_keys(panel)
    if not panel.year_month.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise ValueError("EXP03 requires canonical YYYY-MM event months")
    if panel.year_month.ge("2025-01").any() and not allow_benchmark:
        raise ValueError("Consumed 2025 requires explicit EXP03 benchmark boundary")
    if panel.year_month.gt("2025-12").any():
        raise ValueError("EXP03 does not admit observations after consumed 2025")
    frame = panel.sort_values(KEYS).reset_index(drop=True)
    for source in (COUNT, SEVERE):
        present = frame[source].dropna().astype(float)
        if not np.isfinite(present).all() or present.lt(0).any():
            raise ValueError("Notification counts must be finite nonnegative or missing")
    counts = frame.set_index(KEYS)[COUNT].to_dict()
    raw = {c: frame.set_index(KEYS)[c].to_dict() for c in frame if c not in KEYS}

    def value(m: str, t: pd.Period, source: str = COUNT) -> float:
        v = raw.get(source, {}).get((m, str(t)), np.nan)
        return np.nan if pd.isna(v) else float(v)

    def history(m: str, t: pd.Period) -> list[float]:
        return [value(m, t - 12 * n) for n in range(1, 6)]

    state_lookup: dict[tuple[str, str], Any] = {}
    zone_lookup: dict[tuple[str, str], Any] = {}
    for (m, t), observed in counts.items():
        reference = history(m, pd.Period(t, freq="M"))
        if pd.isna(observed) or not np.isfinite(reference).all():
            state_lookup[m, t] = pd.NA
            zone_lookup[m, t] = pd.NA
            continue
        if float(observed) < 0 or any(v < 0 for v in reference):
            raise ValueError("Negative notification count")
        p25, p50, p75 = np.quantile(reference, [0.25, 0.5, 0.75], method="linear")
        state_lookup[m, t] = int(float(observed) > p75)
        zone_lookup[m, t] = (
            "EXITO"
            if observed < p25
            else "SEGURIDAD"
            if observed <= p50
            else "ALERTA"
            if observed <= p75
            else "EXCESO"
        )
    states = frame[KEYS].copy()
    states["excess"] = pd.Series(
        [state_lookup[m, t] for m, t in frame[KEYS].itertuples(index=False, name=None)],
        dtype="Int64",
    )
    out = labels(states, horizon)
    out["current_excess"] = states.excess
    rows, dates, recipe_dates = [], [], []
    for m, origin in frame[KEYS].itertuples(index=False, name=None):
        t = pd.Period(origin, freq="M")
        current = t - 1 if delay else t
        r: dict[str, Any] = {}
        source_dates: dict[str, str] = {}

        def put(
            name: str,
            v: Any,
            date: pd.Period,
            values: dict[str, Any] = r,
            event_dates: dict[str, str] = source_dates,
        ) -> None:
            values[name] = v
            event_dates[name] = str(date)

        for lag in (1, 2, 3):
            put(f"dengue_lag_{lag}", value(m, t - lag), t - lag)
        for lag in (1, 2):
            put(f"grave_lag_{lag}", value(m, t - lag, SEVERE), t - lag)
        lagged = [value(m, t - lag) for lag in (1, 2, 3)]
        put("dengue_mean_lagged_3m", float(np.mean(lagged)), t - 1)
        put("dengue_difference_lagged_1m", value(m, t - 1) - value(m, t - 2), t - 1)
        put("dengue_notifications_count", value(m, current), current)
        put("dengue_grave_notifications_count", value(m, current, SEVERE), current)
        # Recompute each current recipe at the latest complete month. Independent
        # B/L/R-/C- columns keep their original exact-calendar source dates.
        put("dengue_cambio_1m", value(m, current) - value(m, current - 1), current)
        put(
            "dengue_media_3m",
            float(np.mean([value(m, current - offset) for offset in (0, 1, 2)])),
            current,
        )
        for suffix, s in (("t", current), ("lag_1", t - 1)):
            zone = zone_lookup.get((m, str(s)), pd.NA)
            state = state_lookup.get((m, str(s)), pd.NA)
            put("zona_canal_" + suffix, zone, s)
            put("channel_excess_" + suffix, state, s)
            hist = history(m, s)
            observed = value(m, s)
            expected = float(np.mean(hist))
            available = np.isfinite([*hist, observed]).all()
            put(
                "notification_log1p_oe_" + suffix,
                float(np.log1p(observed / expected))
                if available and expected > 0
                else 0.0
                if available
                else np.nan,
                s,
            )
            put("expected_zero_" + suffix, float(expected == 0) if available else np.nan, s)
            r["positive_zero_reference_" + suffix] = bool(
                available and observed > 0 and expected == 0
            )
            r["missing_reference_" + suffix] = not available
            r["expected_notification_" + suffix] = expected if available else np.nan
            r["reference_covered_months_" + suffix] = int(np.isfinite(hist).sum())
        target = t + horizon
        refs = [pd.Period(year=target.year - n, month=target.month, freq="M") for n in range(1, 6)]
        if max(refs) > t - 1:
            raise ValueError("Target threshold sources must precede T")
        p25, p75 = np.quantile([value(m, s) for s in refs], [0.25, 0.75], method="linear")
        put("channel_target_p25", float(p25), max(refs))
        put("channel_target_p75", float(p75), max(refs))
        phase = 2 * np.pi * (t.month - 1) / 12
        put("mes_sin", float(np.sin(phase)), t)
        put("mes_cos", float(np.cos(phase)), t)
        put("municipality_code_feature", m, t)
        for source, lag in set(
            CLIMATE_RECIPES + [(s, offset + 1) for s, offset in CLIMATE_RECIPES]
        ):
            date = t - lag if lag else current
            put(climate_name(source, lag), value(m, date, source), date)
        # Exact recipe sources complement the latest-source date projection.
        all_dates: dict[str, tuple[str, ...]] = {
            name: (date,) for name, date in source_dates.items()
        }
        all_dates["dengue_mean_lagged_3m"] = tuple(str(t - lag) for lag in (1, 2, 3))
        all_dates["dengue_difference_lagged_1m"] = tuple(str(t - lag) for lag in (1, 2))
        all_dates["dengue_cambio_1m"] = tuple(str(current - lag) for lag in (0, 1))
        all_dates["dengue_media_3m"] = tuple(str(current - lag) for lag in (0, 1, 2))
        for suffix, event in (("t", current), ("lag_1", t - 1)):
            recipe_reference = tuple(str(event - 12 * n) for n in range(1, 6))
            for prefix in (
                "zona_canal_",
                "channel_excess_",
                "notification_log1p_oe_",
                "expected_zero_",
            ):
                all_dates[prefix + suffix] = (str(event), *recipe_reference)
        for name in ("channel_target_p25", "channel_target_p75"):
            all_dates[name] = tuple(str(event) for event in refs)
        rows.append(r)
        dates.append(source_dates)
        recipe_dates.append(all_dates)
    features = pd.DataFrame(rows, index=out.index)
    for column in features:
        if column.startswith("zona_canal_"):
            features[column] = features[column].astype("string")
    out = pd.concat([out, features], axis=1)
    out["department_code"] = out.municipality_code.str[:2]
    out["target_year"] = out.target_month.str[:4].astype(int)
    out["horizon"] = horizon
    out["known_current_state"] = out.current_excess.notna()
    out["outcome_covered"] = out.onset_target.notna() & out.excess_target.notna()
    out["monitored"] = out.known_current_state & out.outcome_covered
    out["error_type"] = pd.Series(pd.NA, index=out.index, dtype="string")
    out.loc[out.excess_target.eq(0).fillna(False), "error_type"] = "no_excess"
    out.loc[out.onset_target.eq(1).fillna(False), "error_type"] = "onset"
    out.loc[(out.excess_target.eq(1) & out.onset_target.eq(0)).fillna(False), "error_type"] = (
        "continuation"
    )
    out.attrs["source_months"] = pd.DataFrame(dates, index=out.index)
    out.attrs["source_event_months"] = pd.DataFrame(recipe_dates, index=out.index)
    out.attrs["delay_interpretation"] = (
        "conditional_feature_stress_gate_independently_known"
        if delay
        else "event_time_retrospective"
    )
    out.attrs["strict_availability_gate"] = "unavailable_abstain" if delay else "requires_Y_T_known"
    return out


def historical_profiles(
    panel: pd.DataFrame, training_end: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Freeze profiles from 60 exact historical calendar months only."""
    validate_keys(panel)
    end = pd.Period(training_end, freq="M")
    start = str(end - 59)
    selected = panel.loc[panel.year_month.between(start, str(end))]
    records = []
    for municipality in sorted(panel.municipality_code.unique()):
        observed = (
            selected.loc[selected.municipality_code.eq(municipality), COUNT].dropna().astype(float)
        )
        n = len(observed)
        records.append(
            {
                "municipality_code": municipality,
                "profile_covered_months": n,
                "profile_coverage": n / 60,
                "profile_zero_fraction": float(observed.eq(0).mean()) if n else None,
                "profile_mean_count": float(observed.mean()) if n else None,
                "profile_history_start": start,
                "profile_history_end": str(end),
            }
        )
    result = pd.DataFrame(records)
    sufficient = result.profile_covered_months.ge(48)
    intermittent = sufficient & result.profile_zero_fraction.ge(0.5)
    remaining = sufficient & ~intermittent
    means = result.loc[remaining, "profile_mean_count"].to_numpy(dtype=float)
    boundaries = (
        np.quantile(means, [1 / 3, 2 / 3], method="linear").tolist() if len(means) else [None, None]
    )
    result["transmission_profile"] = "history_insufficient"
    result.loc[intermittent, "transmission_profile"] = "intermittent"
    if boundaries[0] is None or boundaries[0] == boundaries[1]:
        result.loc[remaining, "transmission_profile"] = "volume_tertiles_collapsed"
    else:
        result.loc[remaining, "transmission_profile"] = [
            "low" if v <= boundaries[0] else "medium" if v <= boundaries[1] else "high"
            for v in means
        ]
    # Historical onset counts use only states built from observations <= training_end.
    counts = panel.loc[panel.year_month.le(str(end))].set_index(KEYS)[COUNT].to_dict()
    counts = {k: np.nan if pd.isna(v) else float(v) for k, v in counts.items()}

    def state(m: str, t: pd.Period) -> int | None:
        vals = [counts.get((m, str(t - 12 * i)), np.nan) for i in range(1, 6)]
        count = counts.get((m, str(t)), np.nan)
        return (
            int(count > np.quantile(vals, 0.75, method="linear"))
            if np.isfinite([*vals, count]).all()
            else None
        )

    onset_counts: list[int | None] = []
    onset_support: list[int] = []
    for municipality in result.municipality_code:
        transitions = [
            (state(municipality, month - 1), state(municipality, month))
            for month in pd.period_range(start, str(end), freq="M")
        ]
        known = [
            (previous, current)
            for previous, current in transitions
            if previous is not None and current is not None
        ]
        onset_support.append(len(known))
        onset_counts.append(
            sum(previous == 0 and current == 1 for previous, current in known) if known else None
        )
    result["profile_onset_evaluable_months"] = onset_support
    result["profile_onset_unknown_months"] = 60 - result.profile_onset_evaluable_months
    result["profile_historical_onsets"] = pd.Series(onset_counts, index=result.index, dtype="Int64")
    metadata = {
        "training_target_end": str(end),
        "history_start": start,
        "boundaries": boundaries,
        "rule": (
            "60 months; >=48 covered; zero fraction>=0.5 intermittent; "
            "type7 equal-municipality tertiles; <= lower category"
        ),
    }
    return result, metadata


COVERAGE_DIMENSIONS = (
    "department_code",
    "transmission_profile",
    "target_year",
    "municipality_code",
)


def _coverage_group_labels(frame: pd.DataFrame, dimension: str) -> pd.Series:
    if dimension in frame:
        return frame[dimension].astype("string").fillna("unknown")
    return pd.Series("unknown", index=frame.index, dtype="string")


def role_parts(frame: pd.DataFrame, window: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Preserve pre-eligibility rows and exact embargo/exclusion bookkeeping."""
    output = {}
    previous = None
    # Avoid DataFrame-valued attrs comparisons during later concat/merge.
    source_months = frame.attrs.get("source_months")
    source_event_months = frame.attrs.get("source_event_months")
    frame = frame.copy()
    frame.attrs = {}
    for role in ("train", "calibration", "selection", "evaluation"):
        start, end = window[role]
        if previous is not None and start <= previous:
            raise ValueError("Temporal role overlap")
        if role != "evaluation" and end >= "2024-01":
            raise ValueError("Stress cannot fit/select")
        if end >= "2025-01":
            raise ValueError("Benchmark is not a fitting role")
        target = frame.target_month.between(start, end)
        boundary = frame.year_month.ge(previous) if previous else pd.Series(True, index=frame.index)
        part = frame.loc[target & boundary].copy()
        part["window"] = window["id"]
        part["role"] = role
        part["evidence_type"] = window["evidence_type"]
        part.attrs["coverage"] = {
            "target_role_rows": int(target.sum()),
            "embargo_excluded_rows": int((target & ~boundary).sum()),
            "unknown_current_rows": int(part.current_excess.isna().sum()),
            "ineligible_at_t_rows": int((part.current_excess.notna() & ~part.eligible_at_t).sum()),
        }
        # Group-ledger starts before embargo so a group with no retained rows is
        # still represented in the scientific exclusion table. Numerical views
        # carry no date-audit DataFrame attrs.
        role_frame = frame.loc[target]
        group_roles = []
        for dimension in COVERAGE_DIMENSIONS:
            labels = _coverage_group_labels(role_frame, dimension)
            for group in sorted(labels.unique()):
                group_index = role_frame.index[labels.eq(group)]
                group_roles.append(
                    {
                        "dimension": dimension,
                        "group": str(group),
                        "target_role_rows": len(group_index),
                        "embargo_excluded_rows": int((~boundary.loc[group_index]).sum()),
                    }
                )
        part.attrs["coverage_group_roles"] = group_roles
        if source_months is not None:
            part.attrs["source_months"] = source_months.loc[part.index].copy()
        if source_event_months is not None:
            part.attrs["source_event_months"] = source_event_months.loc[part.index].copy()
        output[role] = part
        previous = end
    return output


def cohorts(
    panel: pd.DataFrame, contract: dict[str, Any], design: dict[str, Any]
) -> dict[tuple[int, str], Any]:
    validate_design(design)
    output = {}
    for horizon in design["horizons"]:
        frame = prepare(panel, contract, horizon)
        for window in design["windows"]:
            profiles, metadata = historical_profiles(panel, window["train"][1])
            attrs = frame.attrs
            profiled = frame.merge(profiles, on="municipality_code", validate="many_to_one")
            profiled.attrs = attrs
            parts = role_parts(profiled, window)
            common = {}
            for role, part in parts.items():
                mask = (
                    part.monitored
                    & part.eligible_at_t
                    & part[design["predictors"]].notna().all(axis=1)
                )
                part["common_predictors_available"] = part[design["predictors"]].notna().all(axis=1)
                part["common_eligible"] = mask
                selected = part.loc[mask].copy()
                if "source_months" in part.attrs:
                    selected.attrs["source_months"] = (
                        part.attrs["source_months"].loc[selected.index].copy()
                    )
                if "source_event_months" in part.attrs:
                    selected.attrs["source_event_months"] = (
                        part.attrs["source_event_months"].loc[selected.index].copy()
                    )
                selected.attrs["profiles"] = metadata
                common[role] = selected
            output[horizon, window["id"]] = (parts, common)
    return output


def exposure_table(parts: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Cluster denominators include covered ineligible months with no score row."""
    records = []
    for role, rich_part in parts.items():
        # Date-audit DataFrames live in attrs; numerical grouping must not deepcopy
        # that metadata for every column access or inherit it into group slices.
        part = pd.DataFrame(rich_part, copy=False)
        for (municipality, year), group in part.groupby(
            ["municipality_code", "target_year"], sort=True
        ):
            monitored = group.monitored.astype(bool)
            eligible = monitored & group.eligible_at_t
            common = eligible & group.get(
                "common_predictors_available", pd.Series(True, index=group.index)
            )
            records.append(
                {
                    "municipality_code": municipality,
                    "target_year": int(year),
                    "department_code": str(municipality)[:2],
                    "transmission_profile": str(group.transmission_profile.iloc[0])
                    if "transmission_profile" in group
                    else "history_insufficient",
                    "window": str(group.window.iloc[0]),
                    "source_cut": str(group.window.iloc[0]),
                    "role": role,
                    "monitored_exposure": group.loc[monitored, "target_month"].nunique() / 12,
                    "eligible_exposure": group.loc[eligible, "target_month"].nunique() / 12,
                    "common_exposure": group.loc[common, "target_month"].nunique() / 12,
                    "known_covered_onsets": int(group.loc[monitored, "onset_target"].sum()),
                    "known_eligible_onsets": int(group.loc[eligible, "onset_target"].sum()),
                    "excluded_onsets": int(group.loc[eligible & ~common, "onset_target"].sum()),
                }
            )
    return pd.DataFrame(records)


def coverage(
    frame: pd.DataFrame, columns: list[str], full: list[str] | None = None
) -> dict[str, Any]:
    frame = pd.DataFrame(frame, copy=False)
    eligible = frame.eligible_at_t & frame.onset_target.notna() & frame.excess_target.notna()
    valid = eligible & frame[columns].notna().all(axis=1)
    common = eligible & frame[full or columns].notna().all(axis=1)
    recovered = valid & ~common
    return {
        "rows": int(valid.sum()),
        "additional_municipality_months": int(recovered.sum()),
        "recovered_rows": int(recovered.sum()),
        "potential_coverage_only": True,
        "municipalities": frame.loc[valid, "municipality_code"].nunique(),
        "months": frame.loc[valid, "target_month"].nunique(),
        "known_eligible_onsets": int(frame.loc[eligible, "onset_target"].sum()),
        "excluded_onsets": int(frame.loc[eligible & ~valid, "onset_target"].sum()),
        "additional_potential_onsets": int(frame.loc[recovered, "onset_target"].sum()),
        "excluded_outcome": int(frame.onset_target.isna().sum()),
        "unknown_current_state": int(frame.current_excess.isna().sum()),
        "ineligible_at_t": int((frame.current_excess.notna() & ~frame.eligible_at_t).sum()),
        "missing_predictors": {c: int(frame.loc[eligible, c].isna().sum()) for c in columns},
    }


def coverage_groups(
    part: pd.DataFrame, columns: list[str], full: list[str] | None = None
) -> list[dict[str, Any]]:
    """Pre-embargo to prediction stage counts by four declared dimensions.

    Each dimension separately partitions the same role population. Unknown state,
    unknown outcome, ineligibility and missing recipes remain distinct reasons;
    groups removed entirely by embargo retain a zero post-embargo row.
    """
    prior_groups = part.attrs.get("coverage_group_roles", [])
    frame = pd.DataFrame(part, copy=False)
    groups = {(r["dimension"], r["group"]): r for r in prior_groups}
    for dimension in COVERAGE_DIMENSIONS:
        labels = _coverage_group_labels(frame, dimension)
        for group in sorted(labels.unique()):
            groups.setdefault(
                (dimension, str(group)),
                {
                    "dimension": dimension,
                    "group": str(group),
                    "target_role_rows": int(labels.eq(group).sum()),
                    "embargo_excluded_rows": 0,
                },
            )
    output = []
    for (dimension, group), before in groups.items():
        subset = frame.loc[_coverage_group_labels(frame, dimension).eq(group)]
        known_state = subset.current_excess.notna()
        outcome_known = subset.onset_target.notna() & subset.excess_target.notna()
        eligible = subset.eligible_at_t & outcome_known
        variant_available = subset[columns].notna().all(axis=1)
        common_available = subset[full or columns].notna().all(axis=1)
        monitored = known_state & outcome_known
        counts = coverage(subset, columns, full)
        counts.update(
            dimension=dimension,
            group=group,
            target_role_rows=int(before["target_role_rows"]),
            embargo_excluded_rows=int(before["embargo_excluded_rows"]),
            post_embargo_rows=len(subset),
            known_current_state_rows=int(known_state.sum()),
            unknown_current_state_rows=int((~known_state).sum()),
            ineligible_at_t_rows=int((known_state & ~subset.eligible_at_t).sum()),
            known_outcome_rows=int(outcome_known.sum()),
            unknown_outcome_rows=int((~outcome_known).sum()),
            monitored_rows=int(monitored.sum()),
            eligible_rows=int(subset.eligible_at_t.sum()),
            eligible_known_outcome_rows=int(eligible.sum()),
            eligible_unknown_outcome_rows=int((subset.eligible_at_t & ~outcome_known).sum()),
            variant_complete_rows=int((eligible & variant_available).sum()),
            common_complete_rows=int((eligible & common_available).sum()),
            variant_abstentions=int((eligible & ~variant_available).sum()),
            common_abstentions=int((eligible & ~common_available).sum()),
            known_covered_onsets=int(subset.loc[monitored, "onset_target"].sum()),
            common_excluded_onsets=int(
                subset.loc[eligible & ~common_available, "onset_target"].sum()
            ),
            eligibility_stage_reconciles=(
                int(known_state.sum())
                == int((known_state & ~subset.eligible_at_t).sum())
                + int(subset.eligible_at_t.sum())
            ),
            prediction_stage_reconciles=(
                int(eligible.sum())
                == int((eligible & variant_available).sum())
                + int((eligible & ~variant_available).sum())
            ),
            stage_counts_reconcile=(
                len(subset) + int(before["embargo_excluded_rows"])
                == int(before["target_role_rows"])
            ),
        )
        output.append(counts)
    return output
