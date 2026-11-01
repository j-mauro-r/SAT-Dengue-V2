"""Build one canonical municipality-origin table with explicit, safe column roles."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import (
    CLIMATE_MONTHLY_MEAN_MAP,
    CLIMATE_MONTHLY_SUM_MAP,
    add_months,
    compute_current_endemic_channel,
    history_periods_for_target,
    percentile_type7,
)

KEYS = ["municipality_code", "year_month"]
COUNTS = [
    "dengue_notifications_count",
    "dengue_grave_notifications_count",
    "total_notifications_count",
]
CLIMATE = [*CLIMATE_MONTHLY_SUM_MAP.values(), *CLIMATE_MONTHLY_MEAN_MAP.values()]
CHANNEL = ["p25_canal_t", "p50_canal_t", "p75_canal_t", "zona_canal_t"]
LAGS = (1, 2, 3, 12)
PREDICTORS = [
    *COUNTS,
    *CLIMATE,
    *CHANNEL,
    "month_of_year",
    *(f"{name}_lag{lag}" for name in COUNTS for lag in LAGS),
    *(f"{stat}_h5_t{h}" for h in (1, 2) for stat in ("p25", "p75")),
]


def validate_source(panel: pd.DataFrame) -> None:
    """Reject ambiguous keys, count semantics and incomplete-climate aggregates."""
    required = {
        *KEYS,
        *COUNTS,
        *CLIMATE,
        "department_code",
        "in_epi_coverage",
        "epi_count_status",
        "expected_days_in_month",
        "climate_days_observed",
        *(f"{name}_valid_days" for name in CLIMATE),
    }
    if panel.empty or panel.columns.duplicated().any() or not required <= set(panel):
        raise ValueError("Empty or invalid Stage 2 schema")
    if panel[KEYS].isna().any().any() or panel.duplicated(KEYS).any():
        raise ValueError("Null or duplicate municipality-period keys")
    if not panel["municipality_code"].str.fullmatch(r"\d{5}").all():
        raise ValueError("Invalid DANE municipality code")
    if not panel["year_month"].str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise ValueError("Invalid origin month")
    if not panel["department_code"].eq(panel["municipality_code"].str[:2]).fillna(False).all():
        raise ValueError("Department and DANE municipality disagree")
    coverage = panel["in_epi_coverage"]
    if coverage.isna().any() or not coverage.isin([True, False]).all():
        raise ValueError("Invalid epidemiological coverage")
    for name in COUNTS:
        values = panel[name]
        if (
            values[coverage].isna().any()
            or values[~coverage].notna().any()
            or (values.dropna() < 0).any()
            or (values.dropna() % 1 != 0).any()
            or not np.isfinite(values.dropna().astype(float)).all()
        ):
            raise ValueError("Count/coverage mismatch; missing counts cannot become zero")
    if (
        not (panel[COUNTS[2]].eq(panel[COUNTS[0]] + panel[COUNTS[1]]) | ~coverage)
        .fillna(False)
        .all()
    ):
        raise ValueError("Total notifications disagree with component counts")
    expected_status = pd.Series("outside_epi_coverage_missing", index=panel.index)
    expected_status.loc[coverage & panel[COUNTS[2]].eq(0)] = "zero_in_coverage"
    expected_status.loc[coverage & panel[COUNTS[2]].gt(0)] = "records_present"
    if not panel["epi_count_status"].eq(expected_status).all():
        raise ValueError("Epidemiological status disagrees with counts")
    days = pd.Series(pd.PeriodIndex(panel["year_month"], freq="M").days_in_month, index=panel.index)
    if not (
        panel["expected_days_in_month"].eq(days) | panel["expected_days_in_month"].isna()
    ).all():
        raise ValueError("Incorrect calendar-day coverage")
    for name in CLIMATE:
        valid = panel[f"{name}_valid_days"]
        complete = valid.eq(days).fillna(False)
        if (
            (valid.dropna() < 0).any()
            or (valid.dropna() % 1 != 0).any()
            or valid.gt(days).any()
            or panel.loc[~complete, name].notna().any()
            or not np.isfinite(panel[name].dropna().astype(float)).all()
        ):
            raise ValueError("Climate aggregation/coverage mismatch")


def build_table(panel: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Preserve Stage 2 values and add only calendar-exact retrospective predictors."""
    validate_source(panel)
    table = panel.sort_values(KEYS).reset_index(drop=True).copy()
    channel, _, _ = compute_current_endemic_channel(table)
    for name in CHANNEL:
        if name in table:
            equal = table[name].eq(channel[name]) | (table[name].isna() & channel[name].isna())
            if not equal.fillna(False).all():
                raise ValueError("Stage 2 channel disagrees with H5")
        table[name] = channel[name]
    new_columns = {
        "month_of_year",
        *(f"{name}_lag{lag}" for name in COUNTS for lag in LAGS),
        *(f"{stat}_h5_t{h}" for h in (1, 2) for stat in ("p25", "p75", "history_valid_years")),
    }
    if new_columns & set(panel):
        raise ValueError("Canonical derived columns collide with source schema")
    table["month_of_year"] = table["year_month"].str[-2:].astype(int)
    for name in COUNTS:
        lookup = table.set_index(KEYS)[name].to_dict()
        for lag in LAGS:
            table[f"{name}_lag{lag}"] = pd.array(
                [
                    lookup.get((m, add_months(t, -lag)), pd.NA)
                    for m, t in table[KEYS].itertuples(index=False, name=None)
                ],
                dtype="Float64",
            )
    lookup = table.set_index(KEYS)[COUNTS[0]].to_dict()
    for horizon in (1, 2):
        histories = []
        for municipality, origin in table[KEYS].itertuples(index=False, name=None):
            periods = history_periods_for_target(add_months(origin, horizon), 5)
            if any(period > origin for period in periods):
                raise ValueError("Historical threshold would use information after origin T")
            values = [lookup.get((municipality, period), pd.NA) for period in periods]
            histories.append([float(v) for v in values if pd.notna(v)])
        table[f"history_valid_years_h5_t{horizon}"] = [len(v) for v in histories]
        for stat, quantile in (("p25", 0.25), ("p75", 0.75)):
            table[f"{stat}_h5_t{horizon}"] = pd.array(
                [percentile_type7(v, quantile) if len(v) == 5 else pd.NA for v in histories],
                dtype="Float64",
            )
    roles = {
        "key": list(KEYS),
        "metadata": [
            n for n in ("department_code", "municipality_name", "department_name") if n in table
        ],
        "feature": list(PREDICTORS),
        "target": [n for n in ("y_t1", "y_t2") if n in table],
    }
    assigned = {n for columns in roles.values() for n in columns}
    roles["control"] = [n for n in table if n not in assigned]
    schema = {
        "schema": "canonical_model_table_v1",
        "key": KEYS,
        "column_roles": roles,
        "columns": [
            {
                "name": n,
                "dtype": str(table[n].dtype),
                "nullable": bool(table[n].isna().any()),
                "role": next(role for role, columns in roles.items() if n in columns),
                "source": "stage2" if n in panel else "derived_at_origin",
            }
            for n in table
        ],
    }
    return table, schema


def predictor_matrix(table: pd.DataFrame, schema: dict[str, Any]) -> pd.DataFrame:
    """Select the fixed predictor allowlist; future target availability is never X."""
    roles = schema["column_roles"]
    assigned = [n for columns in roles.values() for n in columns]
    if (
        roles.get("feature") != PREDICTORS
        or len(assigned) != len(set(assigned))
        or set(assigned) != set(table)
    ):
        raise ValueError("Canonical column roles changed")
    return table.loc[:, schema["column_roles"]["feature"]].copy()


def coverage_report(table: pd.DataFrame, schema: dict[str, Any]) -> dict[str, Any]:
    """Report actual support and technical eligibility without cohort filtering."""
    result: dict[str, Any] = {
        "rows": len(table),
        "municipalities": int(table["municipality_code"].nunique()),
        "period_start": str(table["year_month"].min()),
        "period_end": str(table["year_month"].max()),
        "department_codes": sorted(table["department_code"].unique().tolist()),
        "national_availability": "UNVERIFIED; no national ingestion in Phase 1",
        "eligibility_rule": (
            "complete canonical predictors and observed target; "
            "technical only, no experiment admission"
        ),
        "departments": {},
        "missing_by_column": {n: int(table[n].isna().sum()) for n in table},
    }
    ready = table[schema["column_roles"]["feature"]].notna().all(axis=1)
    for code, name in (("50", "Meta"), ("73", "Tolima")):
        group = table.loc[table["department_code"].eq(code)]
        result["departments"][name] = {
            "status": "AVAILABLE" if len(group) else "UNAVAILABLE",
            "rows": len(group),
            "municipalities": int(group["municipality_code"].nunique()),
            "period_start": str(group["year_month"].min()) if len(group) else None,
            "period_end": str(group["year_month"].max()) if len(group) else None,
            "observed_zero_rows": int(group["epi_count_status"].eq("zero_in_coverage").sum()),
            "missing_epi_rows": int(group[COUNTS[0]].isna().sum()),
            "complete_climate_rows": int(group[CLIMATE].notna().all(axis=1).sum()),
            "predictor_complete_rows": int(ready.loc[group.index].sum()),
            "eligible_rows_by_target": {
                target: int((ready.loc[group.index] & group[target].notna()).sum())
                for target in schema["column_roles"]["target"]
            },
        }
    return result
