"""National calendar projection using unchanged BETA H5 and climate calculations."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, COUNTS, KEYS, PREDICTORS, build_table
from sat_dengue.data.consolidation import (
    CLIMATE_DAILY_VARIABLES,
    aggregate_monthly_climate,
    compute_y_labels,
)
from sat_dengue.experiments.onset import labels, predictor_projection


def aggregate_view(chunks: Iterable[pd.DataFrame], start: str, end: str) -> pd.DataFrame:
    """Complete municipality-month groups across chunks without partial-month sums.

    Daily numeric conversion and aggregation match Stage 2. Only incomplete groups
    remain buffered; completed months are small monthly frames, not a second daily
    file. A repeated completed key or a duplicate day is rejected, never removed.
    """
    pending = pd.DataFrame()
    monthly = []
    for raw in chunks:
        raw = raw.loc[raw["date"].str[:7].between(start, end)].copy()
        if raw.empty:
            continue
        if not raw.mpio_cdpmp.str.fullmatch(r"\d{5}").all():
            raise ValueError("Malformed national climate code")
        if not raw.dpto_ccdgo.eq(raw.mpio_cdpmp.str[:2]).all():
            raise ValueError("Climate department mismatch")
        daily = raw[["mpio_cdpmp", *CLIMATE_DAILY_VARIABLES]].rename(
            columns={"mpio_cdpmp": "climate_municipality_code"}
        )
        daily["climate_date"] = pd.to_datetime(raw.date, format="%Y-%m-%d", errors="raise")
        daily["year_month"] = raw.date.str[:7]
        for name in CLIMATE_DAILY_VARIABLES:
            daily[name] = pd.to_numeric(raw[name].str.strip().replace("", pd.NA), errors="raise")
            daily[name] = daily[name].astype("float64")
            if not np.isfinite(daily[name].dropna()).all():
                raise ValueError("Nonfinite daily climate value")
        daily = pd.concat([pending, daily], ignore_index=True)
        keys = ["climate_municipality_code", "year_month"]
        if daily.duplicated(["climate_municipality_code", "climate_date"]).any():
            raise ValueError("Duplicate climate municipality-day")
        size = daily.groupby(keys)["climate_date"].transform("size")
        complete = size.ge(daily.climate_date.dt.days_in_month)
        if size.gt(daily.climate_date.dt.days_in_month).any():
            raise ValueError("Too many climate days in month")
        if complete.any():
            monthly.append(aggregate_monthly_climate(daily.loc[complete]))
        pending = daily.loc[~complete].copy()
    if not pending.empty:
        monthly.append(aggregate_monthly_climate(pending))
    if not monthly:
        raise ValueError("No monthly national climate")
    result = pd.concat(monthly, ignore_index=True).sort_values(KEYS).reset_index(drop=True)
    if result.duplicated(KEYS).any():
        raise ValueError("Repeated completed climate month")
    return result


def predictor_matrix(table: pd.DataFrame, contract: dict[str, Any], climate: bool) -> pd.DataFrame:
    """Use the exact positive list and reject future fields or positive offsets."""
    if contract["predictors"] != PREDICTORS or contract["climate_predictors"] != CLIMATE:
        raise ValueError("National predictor contract changed")
    selected = [n for n in PREDICTORS if climate or n not in CLIMATE]
    specs = {field["name"]: field for field in contract["columns"]}
    if len(specs) != len(contract["columns"]):
        raise ValueError("Repeated contract column")
    availability = {n: specs[n]["available_month_offset"] for n in selected}
    if any(specs[n]["role"] != "feature" for n in selected):
        raise ValueError("Predictor role changed")
    return predictor_projection(table[selected], selected, availability)


def build_national(
    calendar: pd.DataFrame, monthly: pd.DataFrame, baseline: pd.DataFrame, contract: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Retain the review grid; restrict history and outcomes by their explicit roles."""
    window = contract["window"]
    if (
        len(calendar) != window["rows"]
        or calendar.municipality_code.nunique() != window["municipalities"]
        or calendar.year_month.nunique() != window["months"]
        or calendar.duplicated(KEYS).any()
        or not calendar.year_month.between(window["start"], window["end"]).all()
    ):
        raise ValueError("National review calendar changed")
    if not calendar.department_code.eq(calendar.municipality_code.str[:2]).all():
        raise ValueError("National territorial identity changed")
    fields = [
        *KEYS,
        "department_code",
        "municipality_name",
        *COUNTS[:2],
        "requires_record_review",
        "historical_territory_applicability",
        *(f"{n}_zero_from_absence" for n in COUNTS[:2]),
    ]
    panel = calendar[fields].merge(monthly, on=KEYS, how="left", validate="one_to_one")
    panel[COUNTS[2]] = panel[COUNTS[0]] + panel[COUNTS[1]]
    panel["in_epi_coverage"] = True
    panel["epi_count_status"] = np.where(
        panel[COUNTS[2]].eq(0), "zero_in_coverage", "records_present"
    )
    reference_codes = set(baseline.municipality_code)
    panel["history_context"] = np.where(
        panel.municipality_code.isin(reference_codes), "BETA_V1_BEFORE_WINDOW", "WINDOW_ONLY"
    )
    days = pd.PeriodIndex(panel.year_month, freq="M").days_in_month
    panel["expected_days_in_month"] = days
    for name in ["climate_days_observed", *(f"{n}_valid_days" for n in CLIMATE)]:
        panel[name] = panel[name].fillna(0).astype(int)
    # Only past rows are admitted as warmup; no baseline targets or future values.
    prior = baseline.loc[baseline.year_month.lt(window["start"])].copy()
    prior["history_context"] = "BETA_V1_BEFORE_WINDOW"
    prior["historical_territory_applicability"] = "UNVERIFIED"
    prior["requires_record_review"] = False
    for name in COUNTS[:2]:
        prior[f"{name}_zero_from_absence"] = prior[name].eq(0)
    panel = pd.concat([prior[list(panel)], panel], ignore_index=True)
    panel, _ = compute_y_labels(panel)
    table, _ = build_table(panel)
    states = table[KEYS].copy()
    states["excess"] = table.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[table.zona_canal_t.isna(), "excess"] = pd.NA
    for h in (1, 2):
        outcomes = labels(states, h)
        table[f"onset_T{h}"] = outcomes.onset_target
        lookup = table.set_index(KEYS)[COUNTS[0]].to_dict()
        table[f"future_dengue_count_t{h}"] = pd.array(
            [
                lookup.get((m, t), pd.NA)
                for m, t in zip(table.municipality_code, outcomes.target_month, strict=True)
            ],
            dtype="Float64",
        )
    table = table.loc[table.year_month.between(window["start"], window["end"])].reset_index(
        drop=True
    )
    no_climate = predictor_matrix(table, contract, False).notna().all(axis=1)
    table["climate_eligible"] = table[CLIMATE].notna().all(axis=1)
    for h in (1, 2):
        table[f"temporally_eligible_t{h}"] = table[f"target_period_t{h}"].between(
            window["start"], window["end"]
        )
        table[f"epidemiologically_eligible_t{h}"] = (
            no_climate & table[f"onset_T{h}"].notna() & ~table.requires_record_review
        )
        table[f"g1_no_climate_t{h}"] = (
            table[f"epidemiologically_eligible_t{h}"]
            & table[f"temporally_eligible_t{h}"]
            & table.zona_canal_t.ne("EXCESO").fillna(False)
        )
        table[f"g1_with_climate_t{h}"] = table[f"g1_no_climate_t{h}"] & table.climate_eligible
    expected = {field["name"] for field in contract["columns"]}
    if set(table) != expected:
        raise ValueError(f"Undeclared national columns: {set(table) ^ expected}")
    table = table[[f["name"] for f in contract["columns"]]]
    for name in COUNTS:
        expected_count = (
            calendar[COUNTS[:2]].sum(axis=1).sum() if name == COUNTS[2] else calendar[name].sum()
        )
        if table[name].sum() != expected_count:
            raise ValueError("National notification counts were not conserved")
    schema = {
        "schema": contract["dataset"],
        "key": KEYS,
        "column_roles": {
            role: [f["name"] for f in contract["columns"] if f["role"] == role]
            for role in ("key", "feature", "target", "control", "metadata")
        },
        "columns": [
            {
                **f,
                "dtype": str(table[f["name"]].dtype),
                "nullable": bool(table[f["name"]].isna().any()),
            }
            for f in contract["columns"]
        ],
    }
    return table, schema


def compare_baseline(table: pd.DataFrame, baseline: pd.DataFrame) -> pd.DataFrame:
    """Account for every common value; unexplained scientific differences block."""
    # Reconstruct the exact BETA direct-onset cohort without importing its fits.
    baseline = baseline.loc[baseline.year_month.lt("2025-01")].copy().reset_index(drop=True)
    states = baseline[KEYS].copy()
    states["excess"] = baseline.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[baseline.zona_canal_t.isna(), "excess"] = pd.NA
    for h in (1, 2):
        outcome = labels(states, h)
        baseline[f"onset_T{h}"] = outcome.onset_target
        for name, predictors in (
            ("g1_with_climate", PREDICTORS),
            ("g1_no_climate", [n for n in PREDICTORS if n not in CLIMATE]),
        ):
            baseline[f"{name}_t{h}"] = (
                outcome.eligible_at_t
                & outcome.onset_target.notna()
                & baseline[predictors].notna().all(axis=1)
                & outcome.target_month.between(table.year_month.min(), table.year_month.max())
            )
    paired = table.merge(baseline, on=KEYS, suffixes=("_new", "_old"), validate="one_to_one")
    if len(paired) != int(table.municipality_code.isin(baseline.municipality_code).sum()):
        raise ValueError("Missing original-municipality comparison keys")
    rows = []
    for name in sorted((set(table) & set(baseline)) - set(KEYS)):
        left, right = paired[f"{name}_new"], paired[f"{name}_old"]
        equal = (left.eq(right) | (left.isna() & right.isna())).fillna(False)
        different = ~equal
        reason = "EXACT_MATCH"
        material = different.copy()
        max_difference = None
        if pd.api.types.is_numeric_dtype(left) and pd.api.types.is_numeric_dtype(right):
            both = left.notna() & right.notna()
            delta = (left[both].astype(float) - right[both].astype(float)).abs()
            max_difference = float(delta.max()) if len(delta) else 0.0
            if name in CLIMATE:
                numeric_equal = pd.Series(False, index=paired.index)
                numeric_equal.loc[both] = delta.le(1e-10)
                material &= ~numeric_equal
                if different.any():
                    reason = "CLIMATE_FLOAT_SERIALIZATION_PRECISION"
        # Legacy outcome columns can see 2025; this table deliberately cannot.
        for h in (1, 2):
            if name in (f"p75_t{h}", f"y_t{h}", f"y_evaluable_t{h}", f"y_status_t{h}"):
                outside = paired[f"target_period_t{h}_new"].gt(table.year_month.max())
                if (different & outside).any():
                    reason = "OUTCOME_OUTSIDE_NATIONAL_WINDOW_NOT_ADMITTED"
                material &= ~outside
        if name == "municipality_name":
            material[:] = False
            if different.any():
                reason = "DISPLAY_NAME_ONLY_CODE_IDENTITY_PRESERVED"
        rows.append(
            {
                "column": name,
                "paired_rows": len(paired),
                "different_rows": int(different.sum()),
                "affected_municipalities": int(
                    paired.loc[different, "municipality_code"].nunique()
                ),
                "affected_municipality_codes": "|".join(
                    sorted(paired.loc[different, "municipality_code"].unique())
                ),
                "affected_origins": "|".join(sorted(paired.loc[different, "year_month"].unique())),
                "first_affected_origin": str(paired.loc[different, "year_month"].min())
                if different.any()
                else "",
                "last_affected_origin": str(paired.loc[different, "year_month"].max())
                if different.any()
                else "",
                "maximum_absolute_difference": max_difference,
                "cause": reason,
                "material_unexplained_rows": int(material.sum()),
            }
        )
    return pd.DataFrame(rows)


def eligibility_report(table: pd.DataFrame) -> dict[str, Any]:
    """Describe horizon-specific masks; these flags do not authorize model fitting."""
    result: dict[str, Any] = {
        "rows": len(table),
        "municipalities": int(table.municipality_code.nunique()),
        "months": int(table.year_month.nunique()),
        "horizons": {},
        "missing_by_column": {n: int(table[n].isna().sum()) for n in table},
        "real_model_fits": 0,
    }
    for h in (1, 2):
        result["horizons"][str(h)] = {}
        for name in ("epidemiologically_eligible", "g1_no_climate", "g1_with_climate"):
            group = table.loc[table[f"{name}_t{h}"]]
            result["horizons"][str(h)][name] = {
                "rows": len(group),
                "municipalities": int(group.municipality_code.nunique()),
                "origin_months": int(group.year_month.nunique()),
                "first_origin": str(group.year_month.min()) if len(group) else None,
                "last_origin": str(group.year_month.max()) if len(group) else None,
            }
    return result
