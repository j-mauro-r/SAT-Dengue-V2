"""Canonical EXP03 revision: finite recipes, temporal roles and derived cell grid.

No scientific input or estimator is loaded here. Recipe identity is source,
transformation and exact calendar offset; shared climate recipes reuse a column.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

CLIMATE_SOURCES = (
    "rain_mm_month_sum",
    "temp_mean_c_month_mean",
    "dewpoint_mean_c_month_mean",
    "surface_runoff_mm_month_sum",
    "total_evaporation_mm_month_sum_ecmwf",
    "solar_radiation_mj_m2_month_sum",
    "soil_water_l1_month_mean",
    "wind_u_ms_month_mean",
    "wind_v_ms_month_mean",
)
CLIMATE_RECIPES = [(s, 0) for s in CLIMATE_SOURCES] + [
    (CLIMATE_SOURCES[i], lag) for i, lag in ((0, 1), (0, 2), (1, 1), (1, 2), (2, 1), (3, 1))
]
COMPOSITIONS = {
    "V00": ["B"],
    "V01": ["B", "F"],
    "V02": ["B", "L", "Z"],
    "V03": ["B", "R0"],
    "V04": ["B", "C-"],
    "V05": ["B", "F", "L", "R-"],
    "V06": ["B", "U", "Z", "R0"],
    "V07": ["B", "F", "L", "R-", "C-"],
    "V08": ["B", "F", "L", "R-", "U", "Z", "R0"],
    "V09": ["B", "F", "L", "R-", "U", "Z", "R0", "C-"],
    "V10": ["B", "L", "R-", "U", "Z", "R0", "C-"],
    "V11": ["B", "F", "R-", "U", "R0", "C-"],
    "V12": ["B", "F", "L", "U", "Z", "C-"],
    "V13": ["B", "F", "L", "R-", "U", "Z", "R0", "Cm"],
    "V14": ["B", "F", "L", "Z", "R-", "R0"],
    "V15": ["B", "U", "C-"],
}
NAMES = (
    "base_lagged",
    "base_plus_target_thresholds",
    "base_plus_recent_channel_state",
    "base_plus_current_notification_ratio",
    "base_plus_lagged_climate",
    "base_plus_historical_channel",
    "base_plus_current_state",
    "full_without_current_state",
    "full_without_climate",
    "full",
    "full_without_target_thresholds",
    "full_without_recent_channel_state",
    "full_without_notification_ratios",
    "full_mixed_climate",
    "base_plus_complete_channel",
    "full_without_complete_channel",
)


def climate_name(source: str, lag: int) -> str:
    return source if lag == 0 else f"{source}__lag_{lag}"


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def build_design(legacy_design: dict[str, Any]) -> dict[str, Any]:
    """Build the revised matrix from canonical groups, never legacy aliases."""
    d = deepcopy(legacy_design)
    groups = {
        "B": [
            "dengue_lag_1",
            "dengue_lag_2",
            "dengue_lag_3",
            "grave_lag_1",
            "grave_lag_2",
            "dengue_mean_lagged_3m",
            "dengue_difference_lagged_1m",
            "mes_sin",
            "mes_cos",
            "municipality_code_feature",
        ],
        "U": [
            "dengue_notifications_count",
            "dengue_grave_notifications_count",
            "dengue_cambio_1m",
            "dengue_media_3m",
        ],
        "L": ["zona_canal_lag_1", "channel_excess_lag_1"],
        "Z": ["zona_canal_t", "channel_excess_t"],
        "R-": ["notification_log1p_oe_lag_1", "expected_zero_lag_1"],
        "R0": ["notification_log1p_oe_t", "expected_zero_t"],
        "F": ["channel_target_p25", "channel_target_p75"],
        "C-": [climate_name(s, lag + 1) for s, lag in CLIMATE_RECIPES],
        "Cm": [climate_name(s, lag) for s, lag in CLIMATE_RECIPES],
    }
    variants = {v: unique([c for g in gs for c in groups[g]]) for v, gs in COMPOSITIONS.items()}
    inventory: dict[str, Any] = {}
    for group, columns in groups.items():
        for col in columns:
            lag = int(col.rsplit("__lag_", 1)[1]) if "__lag_" in col else 0
            if group in ("B", "L", "R-"):
                lag = 1
            if group == "F":
                lag = 1
            if col.startswith(("mes_", "municipality_")):
                lag = 0
            if col.startswith(("dengue_lag_", "grave_lag_")):
                lag = int(col.rsplit("_", 1)[1])
            recipe = {
                "source": col.split("__lag_")[0],
                "transform": "exact_calendar_lookup",
                "formula": col,
                "latest_event_offset_months": -lag,
                "availability_offset_months": -lag,
                "assumed_publication_availability": (
                    "event-month proxy; actual publication unverified"
                ),
                "as_of_policy": "no observation after forecast origin",
                "groups": [group],
                "leakage_risk": "publication dates not demonstrated",
            }
            if col in inventory:
                inventory[col]["groups"].append(group)
            else:
                inventory[col] = recipe
    inventory["dengue_mean_lagged_3m"]["formula"] = (
        "mean(count[T-1],count[T-2],count[T-3]); all required"
    )
    inventory["dengue_difference_lagged_1m"]["formula"] = "count[T-1]-count[T-2]"
    for suffix, offset in (("t", 0), ("lag_1", -1)):
        inventory[f"notification_log1p_oe_{suffix}"]["formula"] = (
            "log1p(count_s/mean(previous five same-month counts)) "
            "if expected>0 else 0; missing remains missing"
        )
        inventory[f"expected_zero_{suffix}"]["formula"] = (
            "1[expected_s=0]; missing required history remains missing"
        )
        inventory[f"notification_log1p_oe_{suffix}"]["latest_event_offset_months"] = offset
    for col, row in inventory.items():
        offset = row["latest_event_offset_months"]
        if col.startswith("dengue_lag_"):
            row.update(source="dengue_notifications_count", formula=f"count[T{offset:+d}]")
        elif col.startswith("grave_lag_"):
            row.update(
                source="dengue_grave_notifications_count", formula=f"severe_count[T{offset:+d}]"
            )
        elif col in ("dengue_mean_lagged_3m", "dengue_difference_lagged_1m"):
            row.update(
                source="dengue_notifications_count", transform="complete_calendar_arithmetic"
            )
        elif col == "dengue_cambio_1m":
            row.update(
                source="dengue_notifications_count",
                formula="count[T]-count[T-1]",
                transform="difference",
            )
        elif col == "dengue_media_3m":
            row.update(
                source="dengue_notifications_count",
                formula="mean(count[T],count[T-1],count[T-2]); all required",
                transform="complete_mean",
            )
        elif col.startswith("channel_target_"):
            row.update(
                source="dengue_notifications_count",
                transform="type7_quantile",
                formula=(
                    "type7 quantile of counts in five years preceding target calendar "
                    "month S; all event dates<T"
                ),
            )
        elif col.startswith(("zona_canal_", "channel_excess_")):
            row.update(
                source="dengue_notifications_count",
                transform="historical_channel",
                formula=(
                    "zone=P25/P50/P75 of five prior same-calendar counts; "
                    "excess=1[count>P75]; all required"
                ),
            )
        elif col.startswith(("notification_log1p_oe_", "expected_zero_")):
            row.update(
                source="dengue_notifications_count",
                transform="historical_notification_observed_expected",
            )
        elif col.startswith("mes_"):
            row.update(
                source="forecast_origin_calendar_month",
                transform="seasonal_phase",
                formula="sin/cos(2*pi*(month(T)-1)/12)",
            )
        elif col == "municipality_code_feature":
            row.update(
                source="municipality_code",
                transform="categorical_identity",
                formula="municipality_code categorical; learned encoding training-only",
            )
        elif col.split("__lag_")[0] in CLIMATE_SOURCES:
            row.update(transform="exact_calendar_lookup", formula=f"{row['source']}[T{offset:+d}]")

    # Record raw source identities and every event offset used by the recipe.
    # Latest event time is distinct from historically unverified publication.
    for col, row in inventory.items():
        offsets = [row["latest_event_offset_months"]]
        if col == "dengue_mean_lagged_3m":
            offsets = [-1, -2, -3]
            row["transform"] = "complete_arithmetic_mean"
        elif col == "dengue_difference_lagged_1m":
            offsets = [-1, -2]
            row["transform"] = "difference"
        elif col == "dengue_cambio_1m":
            offsets = [0, -1]
        elif col == "dengue_media_3m":
            offsets = [0, -1, -2]
        elif col.startswith(
            ("zona_canal_", "channel_excess_", "notification_log1p_oe_", "expected_zero_")
        ):
            event_offset = -1 if col.endswith("lag_1") else 0
            offsets = [event_offset] + [event_offset - 12 * n for n in range(1, 6)]
            if col.startswith("zona_canal_"):
                row.update(
                    transform="type7_historical_channel_zone",
                    formula=(
                        "At s=T+source_offsets[0], reconstruct type7 P25/P50/P75 "
                        "from count[s-12*k], k=1..5. EXITO if count[s]<P25; "
                        "SEGURIDAD if <=P50; ALERTA if <=P75; EXCESO otherwise. "
                        "Any required missing count makes zone unavailable."
                    ),
                )
            elif col.startswith("channel_excess_"):
                row.update(
                    transform="strict_historical_p75_excess_indicator",
                    formula=(
                        "At s=T+source_offsets[0], 1[count[s]>type7_P75("
                        "count[s-12*k],k=1..5)]; missing observations remain unknown."
                    ),
                )
            elif col.startswith("notification_log1p_oe_"):
                row.update(
                    transform="finite_notification_observed_expected_log1p",
                    formula=(
                        "s=T+source_offsets[0]; E_s=mean(count[s-12*k],k=1..5); "
                        "log1p(count[s]/E_s) when E_s>0; otherwise sentinel0 "
                        "with expected_zero flag. Missing count or any reference "
                        "makes both ratio representation columns unavailable."
                    ),
                )
            else:
                row.update(
                    transform="zero_expected_notification_reference_indicator",
                    formula=(
                        "s=T+source_offsets[0]; E_s=mean(count[s-12*k],k=1..5); "
                        "1[E_s=0]; missing count[s] or any reference remains unknown. "
                        "The matching raw count and ratio sentinel are separate."
                    ),
                )
        elif col == "mes_sin":
            row.update(transform="calendar_sine", formula="sin(2*pi*(month(T)-1)/12)")
        elif col == "mes_cos":
            row.update(transform="calendar_cosine", formula="cos(2*pi*(month(T)-1)/12)")
        elif col in ("dengue_notifications_count", "dengue_grave_notifications_count"):
            row.update(transform="raw_notification_count", formula=f"{col}[T]")
        row.update(
            source_columns=[row["source"]],
            source_offsets=offsets,
            publication_availability_verified=False,
            availability_policy="event-month proxy only; historical publication dates unverified",
            source_time_unit="calendar_months_relative_to_forecast_origin_T",
            source_date_evidence="per-row source_months and source_event_months; checked <=T",
            missing_policy="required source absent stays unavailable; covered zero is valid",
        )
        if col.startswith("channel_target_"):
            quantile = 0.25 if col.endswith("p25") else 0.75
            horizon_offsets = {str(h): [h - 12 * n for n in range(1, 6)] for h in (1, 2)}
            row.update(
                source_offsets=horizon_offsets,
                latest_event_offset_months=max(max(v) for v in horizon_offsets.values()),
                availability_offset_months=max(max(v) for v in horizon_offsets.values()),
                transform="type7_same_target_calendar_month_historical_quantile",
                formula=(
                    f"S=T+h; type7_P{int(100 * quantile)}(count[S-12*k],k=1..5). "
                    "All five historical sources required. Actual dates asserted <=T-1; "
                    "no supplied future zone, label or percentile is consumed."
                ),
                quantile=quantile,
            )

    inventory["channel_excess_t"]["cohort_constraint"] = (
        "Constant zero under known Y(T)=0 eligibility; no learned predictive value claimed"
    )
    primary = [("V06", "V00"), ("V09", "V07"), ("V04", "V00"), ("V01", "V00")]
    secondary = [
        ("V02", "V00"),
        ("V03", "V00"),
        ("V05", "V00"),
        ("V14", "V00"),
        ("V09", "V00"),
        ("V09", "V10"),
        ("V09", "V11"),
        ("V09", "V12"),
        ("V09", "V08"),
        ("V09", "V15"),
        ("V07", "V00"),
        ("V13", "V09"),
    ]
    contrasts = [
        {
            "id": f"{tier}{i}",
            "left": left,
            "right": right,
            "tier": "primary" if tier == "P" else "secondary",
            "interpretation": "block_removal_loss"
            if right in {"V08", "V10", "V11", "V12", "V15"}
            else "incremental",
        }
        for tier, pairs in (("P", primary), ("S", secondary))
        for i, (left, right) in enumerate(pairs, 1)
    ]
    windows = []
    for year in (2020, 2021, 2022, 2024):
        prior = year - 1
        windows.append(
            {
                "id": f"{'stress' if year == 2024 else 'development'}_{year}",
                "train": ["2012-01", f"{year - 2}-12"],
                "calibration": [f"{prior}-01", f"{prior}-06"],
                "selection": [f"{prior}-07", f"{prior}-12"],
                "evaluation": [f"{year}-01", f"{year}-12"],
                "evidence_type": "retrospective_stress"
                if year == 2024
                else "retrospective_development",
            }
        )
    d.update(
        revision="exp03-complete-scope-v2",
        groups=groups,
        variants=variants,
        variant_groups=deepcopy(COMPOSITIONS),
        variant_names=dict(zip(variants, NAMES, strict=True)),
        predictors=unique([c for columns in variants.values() for c in columns]),
        inventory=inventory,
        contrasts=contrasts,
        windows=windows,
        horizons=[1, 2],
        excess_controls=["V00", "V09"],
        B_primary=None,
        budget_units="false_onset_alerts_per_monitored_municipality_year",
        budget_rationale=None,
        delay_variants=["V09", "V13"],
        profile_rule={
            "months": 60,
            "minimum_covered": 48,
            "intermittent_zero_fraction": 0.5,
            "quantiles": [1 / 3, 2 / 3],
            "method": "type7",
            "collapsed": "volume_tertiles_collapsed",
        },
    )
    counts = cell_counts(d)
    d.update(
        expected_children=counts["total"],
        expected_model_fits=counts["total"],
        expected_calibrator_fits=counts["total"],
        expected_terminal_cells=counts["terminal"],
    )
    return d


def cell_grid(design: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "variant": variant,
            "objective": objective,
            "family": family,
            "horizon": horizon,
            "window": window["id"],
        }
        for window in design["windows"]
        for family in design["families"]
        for horizon in design["horizons"]
        for variant in design["variants"]
        for objective in (
            ["onset", "excess"]
            if horizon == 2 and variant in design["excess_controls"]
            else ["onset"]
        )
    ]


def cell_counts(design: dict[str, Any]) -> dict[str, int]:
    grid = cell_grid(design)
    terminal_ids = {
        w["id"] for w in design["windows"] if w["evidence_type"] == "retrospective_stress"
    }
    return {
        "onset": sum(c["objective"] == "onset" for c in grid),
        "excess": sum(c["objective"] == "excess" for c in grid),
        "total": len(grid),
        "terminal": sum(c["window"] in terminal_ids for c in grid),
    }


def validate_design(design: dict[str, Any]) -> int:
    if design.get("revision") != "exp03-complete-scope-v2":
        raise ValueError("Superseded EXP03 revision cannot execute")
    variants, groups = design["variants"], design["groups"]
    canonical = build_design(design)
    for field in (
        "groups",
        "variant_groups",
        "contrasts",
        "windows",
        "excess_controls",
        "delay_variants",
        "profile_rule",
    ):
        if design[field] != canonical[field]:
            raise ValueError("Noncanonical EXP03 scientific field: " + field)
    if set(variants) != set(COMPOSITIONS):
        raise ValueError("Exactly V00..V15 required")
    expected = {v: unique([c for g in gs for c in groups[g]]) for v, gs in COMPOSITIONS.items()}
    if variants != expected or len({frozenset(v) for v in variants.values()}) != len(COMPOSITIONS):
        raise ValueError("Duplicate or noncanonical predictor composition")
    if design["predictors"] != unique([c for cols in variants.values() for c in cols]):
        raise ValueError("Common predictor union mismatch")
    if set(design["inventory"]) != set(design["predictors"]):
        raise ValueError("Incomplete provenance inventory")
    for name, row in design["inventory"].items():
        if row["latest_event_offset_months"] > 0 or row["availability_offset_months"] > 0:
            raise ValueError("Future predictor recipe: " + name)
    if design["excess_controls"] != ["V00", "V09"] or design["horizons"] != [1, 2]:
        raise ValueError("Unlisted objective/horizon control")
    if len(design["contrasts"]) != 16 or len({c["id"] for c in design["contrasts"]}) != 16:
        raise ValueError("Four primary and twelve secondary contrasts required")
    years = set()
    for window in design["windows"]:
        roles = [window[r] for r in ("train", "calibration", "selection", "evaluation")]
        if any(a[1] >= b[0] for a, b in zip(roles, roles[1:], strict=False)):
            raise ValueError("Temporal roles overlap")
        if any(end >= "2024-01" for _, end in roles[:-1]) or roles[-1][1] >= "2025-01":
            raise ValueError("Reserved year in fitting/selection")
        if window["evidence_type"] == "retrospective_development":
            year = int(roles[-1][0][:4])
            if year in years or year >= 2024:
                raise ValueError("Duplicate/stress development year")
            years.add(year)
    if years != {2020, 2021, 2022}:
        raise ValueError("Three declared OOF years required")
    counts = cell_counts(design)
    if (
        any(
            design[k] != counts["total"]
            for k in ("expected_children", "expected_model_fits", "expected_calibrator_fits")
        )
        or design["expected_terminal_cells"] != counts["terminal"]
    ):
        raise ValueError("Derived fit count mismatch")
    return counts["total"]
