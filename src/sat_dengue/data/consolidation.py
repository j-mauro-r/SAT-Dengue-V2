"""Preserved Stage 2 calculations extracted without algorithm changes."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

EPI_FILENAMES = ("dengue.csv", "dengue_grave.csv")


CLIMATE_FILENAME = "google_earth_engine.csv"


SCOPE_DEPARTMENTS = {"50", "73"}


CLIMATE_DAILY_VARIABLES = [
    "rain_mm_day",
    "temp_mean_c",
    "dewpoint_mean_c",
    "soil_water_l1_mean",
    "surface_runoff_mm_day",
    "total_evaporation_mm_day_ecmwf",
    "wind_u_mean_ms",
    "wind_v_mean_ms",
    "solar_radiation_mj_m2_day",
]


CLIMATE_MONTHLY_SUM_MAP = {
    "rain_mm_day": "rain_mm_month_sum",
    "surface_runoff_mm_day": "surface_runoff_mm_month_sum",
    "total_evaporation_mm_day_ecmwf": "total_evaporation_mm_month_sum_ecmwf",
    "solar_radiation_mj_m2_day": "solar_radiation_mj_m2_month_sum",
}


CLIMATE_MONTHLY_MEAN_MAP = {
    "temp_mean_c": "temp_mean_c_month_mean",
    "dewpoint_mean_c": "dewpoint_mean_c_month_mean",
    "soil_water_l1_mean": "soil_water_l1_month_mean",
    "wind_u_mean_ms": "wind_u_ms_month_mean",
    "wind_v_mean_ms": "wind_v_ms_month_mean",
}


SOURCE_LABEL_BY_FILE = {
    "dengue.csv": "dengue",
    "dengue_grave.csv": "dengue_grave",
}


EXPECTED_OUTPUT_PATH_BY_KEY = {
    "dengue_y_dengue_grave": "data/processed/dengue_y_dengue_grave.csv",
    "panel_mensual_dengue_clima": "data/processed/panel_mensual_dengue_clima.csv",
    "y_label_history_traceability": (
        "data/interim/stage2_consolidated_dataset_pipeline/y_label_history_traceability.csv"
    ),
    "current_endemic_channel_traceability": (
        "data/interim/stage2_consolidated_dataset_pipeline/current_endemic_channel_traceability.csv"
    ),
    "candidate_contract": (
        "data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json"
    ),
}


Y_HORIZONS = (1, 2)


Y_REFERENCE_YEARS = 5


Y_PERCENTILE = 0.75


Y_PERCENTILE_METHOD = "hyndman_fan_type7_linear"


CANAL_PERCENTILES = (0.25, 0.50, 0.75)


CANAL_ZONE_VALUES = ("EXITO", "SEGURIDAD", "ALERTA", "EXCESO")


class PipelineValidationError(RuntimeError):
    """Raised when a blocking validation fails."""


def normalize_numeric_code(value: Any, width: int) -> str:
    """Normalize numeric-like codes preserving only valid digit payloads.

    Args:
        value: Raw value.
        width: Target zero-padded width.

    Returns:
        Normalized code or empty string when invalid.
    """

    text = "" if value is None else str(value).strip()
    if text == "" or not text.isdigit() or len(text) > width:
        return ""
    return text.zfill(width)


def normalize_code_series(series: pd.Series, width: int) -> pd.Series:
    """Normalize a pandas code series using strict digit validation.

    Args:
        series: Input series.
        width: Target width.

    Returns:
        Normalized string series.
    """

    values = series.fillna("").astype(str).str.strip()
    valid = values.str.fullmatch(rf"\d{{1,{width}}}")
    filtered = values.where(valid, "")
    return filtered.where(filtered.eq(""), filtered.str.zfill(width))


def parse_epi_date_series(series: pd.Series) -> pd.Series:
    """Parse epidemiological dates in dd/mm/YYYY format.

    Args:
        series: Raw date-like values.

    Returns:
        Parsed datetime64 series with NaT on invalid values.
    """

    cleaned = series.fillna("").astype(str).str.strip()
    cleaned = cleaned.str.split().str[0]
    return pd.to_datetime(cleaned, format="%d/%m/%Y", errors="coerce")


def date_parse_status(raw_series: pd.Series, parsed_series: pd.Series) -> pd.Series:
    """Classify date parsing outcome.

    Args:
        raw_series: Raw date values.
        parsed_series: Parsed datetime output.

    Returns:
        Status labels: parsed, missing, or unparseable.
    """

    raw_text = raw_series.fillna("").astype(str).str.strip()
    status = pd.Series("parsed", index=raw_series.index, dtype="string")
    status = status.where(parsed_series.notna(), "unparseable")
    status = status.where(raw_text != "", "missing")
    return status


def panel_assignment_reason(
    municipality_code: pd.Series,
    in_scope: pd.Series,
    date_status: pd.Series,
) -> pd.Series:
    """Classify assignment reason for monthly panel eligibility.

    Args:
        municipality_code: Normalized municipality code.
        in_scope: Scope inclusion mask.
        date_status: Date parse status labels.

    Returns:
        Assignment reason series.
    """

    reason = pd.Series("assignable", index=municipality_code.index, dtype="string")
    reason = reason.where(municipality_code.ne(""), "missing_residence_code")
    reason = reason.where(municipality_code.eq("") | in_scope, "out_of_scope_municipality")
    reason = reason.where(date_status != "missing", "missing_ini_sin")
    reason = reason.where(date_status != "unparseable", "unparseable_ini_sin")
    return reason


def enrich_epi_chunk(
    chunk: pd.DataFrame,
    *,
    source_file: str,
    source_row_start: int,
    scope_codes: set[str],
    climate_lookup: pd.DataFrame,
) -> pd.DataFrame:
    """Add provenance, normalized helpers and climate left-join columns.

    Args:
        chunk: Epidemiological chunk with original columns.
        source_file: Source filename label.
        source_row_start: One-based row number for first chunk row in source.
        scope_codes: Scope municipality codes.
        climate_lookup: Unique climate lookup dataframe keyed by climate_join_key.

    Returns:
        Enriched chunk preserving original columns.
    """

    enriched = chunk.copy()
    enriched["source_file"] = source_file
    enriched["source_label"] = SOURCE_LABEL_BY_FILE[source_file]
    enriched["source_row_number"] = range(source_row_start, source_row_start + len(enriched))

    enriched["norm_residence_dept_code"] = normalize_code_series(enriched["COD_DPTO_R"], 2)
    enriched["norm_residence_mun_code"] = normalize_code_series(enriched["COD_MUN_R"], 3)
    enriched["norm_residence_municipality_code"] = (
        enriched["norm_residence_dept_code"] + enriched["norm_residence_mun_code"]
    )
    no_code_mask = enriched["norm_residence_dept_code"].eq("") | enriched[
        "norm_residence_mun_code"
    ].eq("")
    enriched.loc[no_code_mask, "norm_residence_municipality_code"] = ""

    parsed_ini_sin = parse_epi_date_series(enriched["INI_SIN"])
    enriched["norm_ini_sin_date"] = parsed_ini_sin.dt.strftime("%Y-%m-%d").fillna("")
    enriched["norm_ini_sin_parse_status"] = date_parse_status(enriched["INI_SIN"], parsed_ini_sin)
    enriched["in_scope_catalog"] = enriched["norm_residence_municipality_code"].isin(scope_codes)
    enriched["panel_assignment_reason"] = panel_assignment_reason(
        enriched["norm_residence_municipality_code"],
        enriched["in_scope_catalog"],
        enriched["norm_ini_sin_parse_status"],
    )

    has_join_key = (
        enriched["panel_assignment_reason"].eq("assignable")
        & enriched["norm_ini_sin_date"].ne("")
        & enriched["norm_residence_municipality_code"].ne("")
    )
    enriched["climate_join_key"] = ""
    enriched.loc[has_join_key, "climate_join_key"] = (
        enriched.loc[has_join_key, "norm_residence_municipality_code"]
        + "|"
        + enriched.loc[has_join_key, "norm_ini_sin_date"]
    )

    joined = enriched.merge(
        climate_lookup,
        on="climate_join_key",
        how="left",
        validate="many_to_one",
    )

    for column in CLIMATE_DAILY_VARIABLES:
        joined[f"climate_{column}"] = joined[column]
        joined = joined.drop(columns=[column])

    joined["climate_source_municipality_code"] = joined["climate_municipality_code"].fillna("")
    joined["climate_source_date"] = joined["climate_date_iso"].fillna("")
    joined = joined.drop(columns=["climate_municipality_code", "climate_date_iso", "climate_date"])

    climate_matched = joined["climate_source_municipality_code"].ne("")
    joined["climate_join_status"] = "not_assignable"
    joined.loc[joined["panel_assignment_reason"].eq("assignable"), "climate_join_status"] = (
        "no_climate_match"
    )
    joined.loc[
        joined["panel_assignment_reason"].eq("assignable") & climate_matched,
        "climate_join_status",
    ] = "matched"

    return joined


def build_epi_monthly_counts(consolidated: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly epidemiological notification counts by source stream.

    Args:
        consolidated: Consolidated enriched dataframe.

    Returns:
        Monthly counts with separated dengue streams.
    """

    assignable = consolidated[consolidated["panel_assignment_reason"].eq("assignable")].copy()
    assignable["year_month"] = assignable["norm_ini_sin_date"].str.slice(0, 7)

    grouped = (
        assignable.groupby(
            ["norm_residence_municipality_code", "year_month", "source_label"], dropna=False
        )
        .size()
        .rename("count")
        .reset_index()
    )

    if grouped.empty:
        return pd.DataFrame(
            columns=[
                "municipality_code",
                "year_month",
                "dengue_notifications_count",
                "dengue_grave_notifications_count",
            ]
        )

    pivot = grouped.pivot_table(
        index=["norm_residence_municipality_code", "year_month"],
        columns="source_label",
        values="count",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    pivot = pivot.rename(columns={"norm_residence_municipality_code": "municipality_code"})
    if "dengue" not in pivot.columns:
        pivot["dengue"] = 0
    if "dengue_grave" not in pivot.columns:
        pivot["dengue_grave"] = 0

    pivot = pivot.rename(
        columns={
            "dengue": "dengue_notifications_count",
            "dengue_grave": "dengue_grave_notifications_count",
        }
    )

    return pivot[
        [
            "municipality_code",
            "year_month",
            "dengue_notifications_count",
            "dengue_grave_notifications_count",
        ]
    ]


def build_epi_monthly_counts_from_counter(
    counter: dict[tuple[str, str], dict[str, int]],
) -> pd.DataFrame:
    """Create monthly epidemiological count table from incremental counters.

    Args:
        counter: Nested counter keyed by (municipality_code, year_month).

    Returns:
        Dataframe with separated dengue and dengue_grave counts.
    """

    rows: list[dict[str, Any]] = []
    for (municipality_code, year_month), payload in sorted(counter.items()):
        rows.append(
            {
                "municipality_code": municipality_code,
                "year_month": year_month,
                "dengue_notifications_count": int(payload.get("dengue", 0)),
                "dengue_grave_notifications_count": int(payload.get("dengue_grave", 0)),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "municipality_code",
            "year_month",
            "dengue_notifications_count",
            "dengue_grave_notifications_count",
        ],
    )


def describe_consolidated_schema_from_columns(columns: list[str]) -> list[dict[str, Any]]:
    """Describe consolidated output schema without loading full dataset.

    Args:
        columns: Ordered consolidated column names.

    Returns:
        Schema descriptor list with type/nullability hints.
    """

    numeric_columns = {
        "source_row_number",
        *[f"climate_{column}" for column in CLIMATE_DAILY_VARIABLES],
    }
    boolean_columns = {"in_scope_catalog"}

    schema: list[dict[str, Any]] = []
    for column in columns:
        if column in numeric_columns:
            dtype = "float64" if column.startswith("climate_") else "int64"
            nullable = column.startswith("climate_")
        elif column in boolean_columns:
            dtype = "bool"
            nullable = False
        else:
            dtype = "string"
            nullable = True
        schema.append({"name": column, "dtype": dtype, "nullable": nullable})
    return schema


def aggregate_monthly_climate(climate_daily: pd.DataFrame) -> pd.DataFrame:
    """Aggregate monthly climate from daily source rows.

    Args:
        climate_daily: Unique climate daily dataframe.

    Returns:
        Monthly climate aggregates and per-variable coverage counters.
    """

    frame = climate_daily.copy()
    frame["year_month"] = frame["climate_date"].dt.to_period("M").astype(str)

    grouped = frame.groupby(["climate_municipality_code", "year_month"], dropna=False)
    result = grouped.size().rename("climate_days_observed").reset_index()
    result = result.rename(columns={"climate_municipality_code": "municipality_code"})
    result["expected_days_in_month"] = pd.PeriodIndex(result["year_month"], freq="M").days_in_month

    for source_column, output_column in CLIMATE_MONTHLY_SUM_MAP.items():
        aggregate = (
            grouped[source_column].sum(min_count=1).rename(output_column).reset_index(drop=True)
        )
        valid_days = (
            grouped[source_column]
            .count()
            .rename(f"{output_column}_valid_days")
            .reset_index(drop=True)
        )
        result[output_column] = aggregate
        result[f"{output_column}_valid_days"] = valid_days
        result.loc[
            result[f"{output_column}_valid_days"] != result["expected_days_in_month"],
            output_column,
        ] = pd.NA

    for source_column, output_column in CLIMATE_MONTHLY_MEAN_MAP.items():
        aggregate = grouped[source_column].mean().rename(output_column).reset_index(drop=True)
        valid_days = (
            grouped[source_column]
            .count()
            .rename(f"{output_column}_valid_days")
            .reset_index(drop=True)
        )
        result[output_column] = aggregate
        result[f"{output_column}_valid_days"] = valid_days
        result.loc[
            result[f"{output_column}_valid_days"] != result["expected_days_in_month"],
            output_column,
        ] = pd.NA

    return result.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)


def month_range(start_month: str, end_month: str) -> list[str]:
    """Generate inclusive month range in YYYY-MM format.

    Args:
        start_month: First month.
        end_month: Last month.

    Returns:
        Ordered month list.
    """

    periods = pd.period_range(start=start_month, end=end_month, freq="M")
    return [str(period) for period in periods]


def build_panel_grid(
    catalog: pd.DataFrame,
    start_month: str,
    end_month: str,
) -> pd.DataFrame:
    """Build municipality-month mesh grid from scope catalog and month range.

    Args:
        catalog: Scope municipality catalog.
        start_month: Inclusive start month.
        end_month: Inclusive end month.

    Returns:
        Municipality-month mesh dataframe.
    """

    months = pd.DataFrame({"year_month": month_range(start_month, end_month)})
    catalog_with_key = catalog.assign(_merge_key=1)
    months_with_key = months.assign(_merge_key=1)
    grid = catalog_with_key.merge(months_with_key, on="_merge_key", how="inner").drop(
        columns=["_merge_key"]
    )
    return grid.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)


def build_monthly_panel(
    *,
    grid: pd.DataFrame,
    epi_counts: pd.DataFrame,
    climate_monthly: pd.DataFrame,
    epi_coverage_start: str,
    epi_coverage_end: str,
) -> pd.DataFrame:
    """Join monthly epidemiological and climate tables on shared municipality-month mesh.

    Args:
        grid: Municipality-month mesh.
        epi_counts: Aggregated epidemiological monthly counts.
        climate_monthly: Aggregated monthly climate table.
        epi_coverage_start: Epidemiological coverage start month.
        epi_coverage_end: Epidemiological coverage end month.

    Returns:
        Panel dataframe.
    """

    panel = grid.merge(
        epi_counts,
        on=["municipality_code", "year_month"],
        how="left",
        validate="one_to_one",
    )
    panel = panel.merge(
        climate_monthly,
        on=["municipality_code", "year_month"],
        how="left",
        validate="one_to_one",
    )

    in_epi_coverage = panel["year_month"].between(epi_coverage_start, epi_coverage_end)
    panel["in_epi_coverage"] = in_epi_coverage

    for count_column in ["dengue_notifications_count", "dengue_grave_notifications_count"]:
        panel[count_column] = panel[count_column].astype("float64")
        panel.loc[in_epi_coverage & panel[count_column].isna(), count_column] = 0.0

    panel["total_notifications_count"] = (
        panel["dengue_notifications_count"] + panel["dengue_grave_notifications_count"]
    )

    panel.loc[~in_epi_coverage, "dengue_notifications_count"] = pd.NA
    panel.loc[~in_epi_coverage, "dengue_grave_notifications_count"] = pd.NA
    panel.loc[~in_epi_coverage, "total_notifications_count"] = pd.NA

    panel["epi_count_status"] = "outside_epi_coverage_missing"
    panel.loc[
        in_epi_coverage & panel["total_notifications_count"].fillna(0).eq(0),
        "epi_count_status",
    ] = "zero_in_coverage"
    panel.loc[
        in_epi_coverage & panel["total_notifications_count"].fillna(0).gt(0),
        "epi_count_status",
    ] = "records_present"

    return panel.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)


def add_months(year_month: str, offset: int) -> str:
    """Shift a YYYY-MM period by offset months.

    Args:
        year_month: Source period in YYYY-MM format.
        offset: Number of months to shift.

    Returns:
        Shifted period in YYYY-MM format.
    """

    return str(pd.Period(year_month, freq="M") + offset)


def percentile_type7(values: list[float], q: float) -> float:
    """Compute percentile with Hyndman-Fan type-7 linear interpolation.

    Args:
        values: Numeric values.
        q: Quantile between 0 and 1.

    Returns:
        Quantile value.

    Raises:
        PipelineValidationError: If inputs are invalid.
    """

    if not values:
        raise PipelineValidationError("percentile_type7 requires at least one value")
    if q < 0 or q > 1:
        raise PipelineValidationError("percentile_type7 requires q in [0, 1]")

    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]

    rank = (len(ordered) - 1) * q
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = rank - lower_index
    if lower_index == upper_index:
        return ordered[lower_index]
    return ordered[lower_index] + fraction * (ordered[upper_index] - ordered[lower_index])


def history_periods_for_target(target_period: str, history_years: int) -> list[str]:
    """Build same-month historical reference periods for a target period.

    The reference set uses the same calendar month from the `history_years`
    immediately prior years relative to the target-year component.

    Args:
        target_period: Target period in YYYY-MM format.
        history_years: Number of prior years to reference.

    Returns:
        Ordered list of historical YYYY-MM periods.

    Raises:
        PipelineValidationError: If target_period format is invalid.
    """

    parts = target_period.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        raise PipelineValidationError(f"Invalid target period format: {target_period}")

    target_year = int(parts[0])
    target_month = parts[1]
    return [
        f"{year:04d}-{target_month}" for year in range(target_year - history_years, target_year)
    ]


def classify_endemic_zone(current_count: float, p25: float, p50: float, p75: float) -> str:
    """Classify current endemic-channel zone from municipality-month thresholds.

    Args:
        current_count: Current municipality-month dengue count at period T.
        p25: Historical P25 threshold from same-month prior years.
        p50: Historical P50 threshold from same-month prior years.
        p75: Historical P75 threshold from same-month prior years.

    Returns:
        Canonical endemic-channel zone.
    """

    if current_count < p25:
        return "EXITO"
    if current_count <= p50:
        return "SEGURIDAD"
    if current_count <= p75:
        return "ALERTA"
    return "EXCESO"


def compute_current_endemic_channel(
    panel: pd.DataFrame,
    *,
    history_years: int = Y_REFERENCE_YEARS,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Compute current-period endemic-channel thresholds and zone at reference month T.

    Args:
        panel: Monthly panel with dengue notification counts.
        history_years: Number of same-month prior-year observations required.

    Returns:
        Tuple of (panel_with_channel_columns, traceability_table, summary).
    """

    required = {"municipality_code", "year_month", "dengue_notifications_count"}
    missing_required = sorted(required - set(panel.columns))
    if missing_required:
        raise PipelineValidationError(
            f"Cannot compute current endemic channel, panel missing columns: {missing_required}"
        )

    channel_panel = (
        panel.sort_values(["municipality_code", "year_month"]).reset_index(drop=True).copy()
    )

    lookup = channel_panel.set_index(["municipality_code", "year_month"])[
        "dengue_notifications_count"
    ].to_dict()

    p25_values: list[float | None] = []
    p50_values: list[float | None] = []
    p75_values: list[float | None] = []
    zone_values: list[str | None] = []

    trace_rows: list[dict[str, Any]] = []

    for row in channel_panel.itertuples(index=False):
        municipality_code = str(row.municipality_code)
        reference_period = str(row.year_month)

        history_periods_expected = history_periods_for_target(reference_period, history_years)
        history_used: list[str] = []
        history_missing: list[str] = []
        history_values: list[float] = []

        for history_period in history_periods_expected:
            history_value = lookup.get((municipality_code, history_period), pd.NA)
            if pd.isna(history_value):
                history_missing.append(history_period)
                continue
            history_used.append(history_period)
            history_values.append(float(history_value))

        current_count_raw = lookup.get((municipality_code, reference_period), pd.NA)

        p25_value: float | None = None
        p50_value: float | None = None
        p75_value: float | None = None
        zone_value: str | None = None
        canal_status = "insufficient_history"

        if pd.isna(current_count_raw):
            canal_status = "current_count_missing"
        elif len(history_values) < history_years:
            canal_status = "insufficient_history"
        else:
            current_count = float(current_count_raw)
            p25_value = percentile_type7(history_values, CANAL_PERCENTILES[0])
            p50_value = percentile_type7(history_values, CANAL_PERCENTILES[1])
            p75_value = percentile_type7(history_values, CANAL_PERCENTILES[2])
            zone_value = classify_endemic_zone(current_count, p25_value, p50_value, p75_value)
            canal_status = "evaluable"

        p25_values.append(p25_value)
        p50_values.append(p50_value)
        p75_values.append(p75_value)
        zone_values.append(zone_value)

        trace_rows.append(
            {
                "municipality_code": municipality_code,
                "reference_period": reference_period,
                "current_count": (None if pd.isna(current_count_raw) else float(current_count_raw)),
                "history_required_years": history_years,
                "history_valid_years": len(history_values),
                "history_periods_expected": "|".join(history_periods_expected),
                "history_periods_used": "|".join(history_used),
                "history_missing_periods": "|".join(history_missing),
                "p25_canal_t": p25_value,
                "p50_canal_t": p50_value,
                "p75_canal_t": p75_value,
                "zona_canal_t": zone_value,
                "canal_status": canal_status,
            }
        )

    channel_panel["p25_canal_t"] = pd.Series(p25_values, dtype="float64")
    channel_panel["p50_canal_t"] = pd.Series(p50_values, dtype="float64")
    channel_panel["p75_canal_t"] = pd.Series(p75_values, dtype="float64")
    channel_panel["zona_canal_t"] = pd.array(zone_values, dtype="string")

    traceability = pd.DataFrame(trace_rows).sort_values(["municipality_code", "reference_period"])
    traceability = traceability.reset_index(drop=True)

    status_counts = {
        str(key): int(value)
        for key, value in traceability["canal_status"].value_counts(dropna=False).items()
    }

    zone_counts: dict[str, int] = {}
    for key, value in traceability["zona_canal_t"].value_counts(dropna=False).items():
        zone_key = "NA" if pd.isna(key) else str(key)
        zone_counts[zone_key] = int(value)

    summary = {
        "reference_period_basis": "current_month_t",
        "reference_years": history_years,
        "percentile_method": Y_PERCENTILE_METHOD,
        "percentiles": {
            "p25": CANAL_PERCENTILES[0],
            "p50": CANAL_PERCENTILES[1],
            "p75": CANAL_PERCENTILES[2],
        },
        "zone_values": list(CANAL_ZONE_VALUES),
        "zone_rule": {
            "EXITO": "c < p25",
            "SEGURIDAD": "p25 <= c <= p50",
            "ALERTA": "p50 < c <= p75",
            "EXCESO": "c > p75",
        },
        "status_counts": status_counts,
        "zone_counts": zone_counts,
    }

    return channel_panel, traceability, summary


def compute_y_labels(
    panel: pd.DataFrame,
    *,
    horizons: tuple[int, ...] = Y_HORIZONS,
    history_years: int = Y_REFERENCE_YEARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute retrospective Y labels for each municipality-month cutoff.

    Args:
        panel: Monthly panel with dengue notification counts.
        horizons: Prediction horizons in months.
        history_years: Number of prior same-month yearly observations required.

    Returns:
        Tuple of (panel_with_labels, traceability_table).
    """

    required = {"municipality_code", "year_month", "dengue_notifications_count"}
    missing_required = sorted(required - set(panel.columns))
    if missing_required:
        raise PipelineValidationError(
            f"Cannot compute Y labels, panel missing columns: {missing_required}"
        )

    labeled = panel.sort_values(["municipality_code", "year_month"]).reset_index(drop=True).copy()

    lookup = labeled.set_index(["municipality_code", "year_month"])[
        "dengue_notifications_count"
    ].to_dict()
    lookup_keys = set(lookup.keys())
    trace_rows: list[dict[str, Any]] = []

    for horizon in horizons:
        suffix = f"t{horizon}"
        target_periods: list[str] = []
        p75_values: list[float | None] = []
        history_valid_years: list[int] = []
        y_values: list[int | None] = []
        y_evaluable: list[bool] = []
        y_statuses: list[str] = []
        history_periods_expected_values: list[str] = []
        history_periods_used_values: list[str] = []
        history_missing_periods_values: list[str] = []

        for row in labeled.itertuples(index=False):
            municipality_code = str(row.municipality_code)
            cutoff_period = str(row.year_month)
            target_period = add_months(cutoff_period, horizon)
            target_periods.append(target_period)

            history_periods_expected = history_periods_for_target(target_period, history_years)
            history_periods_expected_values.append("|".join(history_periods_expected))

            history_used: list[str] = []
            history_missing: list[str] = []
            history_values: list[float] = []
            for history_period in history_periods_expected:
                history_value = lookup.get((municipality_code, history_period), pd.NA)
                if pd.isna(history_value):
                    history_missing.append(history_period)
                    continue
                history_used.append(history_period)
                history_values.append(float(history_value))

            history_periods_used_values.append("|".join(history_used))
            history_missing_periods_values.append("|".join(history_missing))
            history_valid_years.append(len(history_values))

            target_key = (municipality_code, target_period)
            target_observed_count = lookup.get(target_key, pd.NA)
            evaluable = False
            status = "target_outside_panel"
            p75_value: float | None = None
            y_value: int | None = None

            if target_key in lookup_keys:
                if pd.isna(target_observed_count):
                    status = "future_observation_missing"
                elif len(history_values) < history_years:
                    status = "insufficient_history"
                else:
                    p75_value = percentile_type7(history_values, Y_PERCENTILE)
                    status = "evaluable"
                    evaluable = True
                    y_value = 1 if float(target_observed_count) > p75_value else 0

            p75_values.append(p75_value)
            y_values.append(y_value)
            y_evaluable.append(evaluable)
            y_statuses.append(status)

            trace_rows.append(
                {
                    "municipality_code": municipality_code,
                    "cutoff_period": cutoff_period,
                    "horizon_months": horizon,
                    "target_period": target_period,
                    "target_observed_count": (
                        None if pd.isna(target_observed_count) else float(target_observed_count)
                    ),
                    "history_required_years": history_years,
                    "history_valid_years": len(history_values),
                    "history_periods_expected": "|".join(history_periods_expected),
                    "history_periods_used": "|".join(history_used),
                    "history_missing_periods": "|".join(history_missing),
                    "p75": p75_value,
                    "y_evaluable": evaluable,
                    "y_status": status,
                    "y_label": y_value,
                }
            )

        labeled[f"target_period_{suffix}"] = pd.Series(target_periods, dtype="string")
        labeled[f"p75_{suffix}"] = pd.Series(p75_values, dtype="float64")
        labeled[f"history_valid_years_{suffix}"] = pd.Series(history_valid_years, dtype="int64")
        labeled[f"history_periods_expected_{suffix}"] = pd.Series(
            history_periods_expected_values,
            dtype="string",
        )
        labeled[f"history_periods_used_{suffix}"] = pd.Series(
            history_periods_used_values,
            dtype="string",
        )
        labeled[f"history_missing_periods_{suffix}"] = pd.Series(
            history_missing_periods_values,
            dtype="string",
        )
        labeled[f"y_evaluable_{suffix}"] = pd.Series(y_evaluable, dtype="bool")
        labeled[f"y_status_{suffix}"] = pd.Series(y_statuses, dtype="string")
        labeled[f"y_{suffix}"] = pd.array(y_values, dtype="Int64")

    traceability = pd.DataFrame(trace_rows).sort_values(
        ["municipality_code", "cutoff_period", "horizon_months"]
    )
    traceability = traceability.reset_index(drop=True)
    if not traceability.empty:
        traceability["y_label"] = pd.array(traceability["y_label"], dtype="Int64")

    return labeled, traceability


def summarize_y_labels(panel: pd.DataFrame) -> dict[str, Any]:
    """Create aggregated Y label diagnostics for manifest reporting.

    Args:
        panel: Monthly panel with Y label columns.

    Returns:
        Horizon-level summary metrics.
    """

    summary: dict[str, Any] = {
        "reference_years": Y_REFERENCE_YEARS,
        "percentile": Y_PERCENTILE,
        "percentile_method": Y_PERCENTILE_METHOD,
        "decision_rule": "strict_greater_than",
        "horizons": {},
    }

    for horizon in Y_HORIZONS:
        suffix = f"t{horizon}"
        evaluable_column = f"y_evaluable_{suffix}"
        status_column = f"y_status_{suffix}"
        label_column = f"y_{suffix}"

        if not {evaluable_column, status_column, label_column}.issubset(panel.columns):
            continue

        label_counts = panel[label_column].value_counts(dropna=False)
        summary["horizons"][suffix] = {
            "rows": int(len(panel)),
            "evaluable_rows": int(panel[evaluable_column].sum()),
            "non_evaluable_rows": int((~panel[evaluable_column]).sum()),
            "status_counts": {
                str(key): int(value)
                for key, value in panel[status_column].value_counts(dropna=False).items()
            },
            "label_counts": {
                ("NA" if pd.isna(key) else str(int(key))): int(value)
                for key, value in label_counts.items()
            },
        }

    return summary


def compute_schema_contract(
    consolidated_schema: list[dict[str, Any]],
    panel: pd.DataFrame,
    *,
    version: str,
    generated_utc: str = "",
) -> dict[str, Any]:
    """Create candidate construction contract metadata.

    Args:
        consolidated_schema: Consolidated schema descriptor.
        panel: Monthly panel dataframe.
        version: Candidate contract version.

    Returns:
        Candidate contract metadata dictionary.
    """

    def describe_schema(frame: pd.DataFrame) -> list[dict[str, Any]]:
        columns: list[dict[str, Any]] = []
        for column in frame.columns:
            series = frame[column]
            columns.append(
                {
                    "name": column,
                    "dtype": str(series.dtype),
                    "nullable": bool(series.isna().any()),
                }
            )
        return columns

    panel_columns = set(panel.columns)
    observation_columns = [
        "dengue_notifications_count",
        "dengue_grave_notifications_count",
        "total_notifications_count",
        "in_epi_coverage",
        "epi_count_status",
    ]
    historical_reference_columns = [
        column
        for column in [
            "target_period_t1",
            "target_period_t2",
            "p75_t1",
            "p75_t2",
            "history_valid_years_t1",
            "history_valid_years_t2",
            "history_periods_expected_t1",
            "history_periods_expected_t2",
            "history_periods_used_t1",
            "history_periods_used_t2",
            "history_missing_periods_t1",
            "history_missing_periods_t2",
        ]
        if column in panel_columns
    ]
    label_columns = [
        column
        for column in [
            "y_t1",
            "y_t2",
            "y_evaluable_t1",
            "y_evaluable_t2",
            "y_status_t1",
            "y_status_t2",
        ]
        if column in panel_columns
    ]
    endemic_channel_columns = [
        column
        for column in [
            "p25_canal_t",
            "p50_canal_t",
            "p75_canal_t",
            "zona_canal_t",
        ]
        if column in panel_columns
    ]

    return {
        "contract_version": version,
        "classification": "candidate_construction_contract",
        "generated_utc": generated_utc,
        "notes": {
            "status": "candidate_only_not_training_contract",
            "aggregation_review_required": True,
        },
        "target_labeling_policy": {
            "series": "dengue_notifications_count",
            "horizons_months": list(Y_HORIZONS),
            "reference_years": Y_REFERENCE_YEARS,
            "seasonality_basis": "same_calendar_month",
            "historical_reference_rule": (
                "For target period YYYY-MM, use the same MM from the five prior years "
                "(YYYY-5..YYYY-1) without substituting older years when a required observation "
                "is genuinely missing."
            ),
            "decision_rule": "label_1_if_observed_strictly_greater_than_p75",
            "non_evaluable_rule": "missing_future_or_insufficient_history_yields_null_label",
            "percentile": Y_PERCENTILE,
            "percentile_method": Y_PERCENTILE_METHOD,
        },
        "current_endemic_channel_policy": {
            "series": "dengue_notifications_count",
            "reference_period": "current_month_t",
            "reference_years": Y_REFERENCE_YEARS,
            "historical_reference_rule": (
                "For reference month T (YYYY-MM), use the same MM from the five prior years "
                "(YYYY-5..YYYY-1) without substituting older years when a required observation "
                "is genuinely missing."
            ),
            "percentiles": {
                "p25": CANAL_PERCENTILES[0],
                "p50": CANAL_PERCENTILES[1],
                "p75": CANAL_PERCENTILES[2],
            },
            "percentile_method": Y_PERCENTILE_METHOD,
            "zone_values": list(CANAL_ZONE_VALUES),
            "zone_rule": {
                "EXITO": "c < p25",
                "SEGURIDAD": "p25 <= c <= p50",
                "ALERTA": "p50 < c <= p75",
                "EXCESO": "c > p75",
            },
            "non_evaluable_rule": (
                "missing_current_count_or_insufficient_history_yields_null_zone_and_thresholds"
            ),
        },
        "datasets": {
            "dengue_y_dengue_grave": {
                "row_unit": "notification_row",
                "climate_join_key": ["norm_residence_municipality_code", "norm_ini_sin_date"],
                "schema": consolidated_schema,
            },
            "panel_mensual_dengue_clima": {
                "row_unit": "municipality_month",
                "scope": "Tolima_Meta_DIVIPOLA",
                "key": ["municipality_code", "year_month"],
                "column_roles": {
                    "keys": ["municipality_code", "year_month"],
                    "observations": [
                        column for column in observation_columns if column in panel_columns
                    ],
                    "historical_references": historical_reference_columns,
                    "labels": label_columns,
                    "current_endemic_channel": endemic_channel_columns,
                },
                "schema": describe_schema(panel),
            },
        },
        "climate_monthly_aggregation": {
            "sum_variables": CLIMATE_MONTHLY_SUM_MAP,
            "mean_variables": CLIMATE_MONTHLY_MEAN_MAP,
            "coverage_rule": "aggregate_only_when_valid_days_equals_expected_days",
            "imputation": "none",
        },
    }


def normalize_scope_catalog(payload: dict[str, Any]) -> pd.DataFrame:
    """Load Tolima/Meta municipality catalog from local DIVIPOLA snapshot.

    Args:
        paths: Pipeline paths.

    Returns:
        Catalog dataframe with municipality and department metadata.

    Raises:
        PipelineValidationError: If catalog shape is unexpected.
    """

    records = payload.get("resultado", [])
    catalog = pd.DataFrame(records)
    required = {
        "CODIGO_MUNICIPIO",
        "CODIGO_DEPARTAMENTO",
        "CODIGO_DPTO_MPIO",
        "NOMBRE_MUNICIPIO",
    }
    if not required.issubset(catalog.columns):
        missing = sorted(required - set(catalog.columns))
        raise PipelineValidationError(f"DIVIPOLA catalog missing required columns: {missing}")

    catalog = catalog[catalog["CODIGO_DEPARTAMENTO"].astype(str).isin(SCOPE_DEPARTMENTS)].copy()
    catalog["municipality_code"] = catalog["CODIGO_DPTO_MPIO"].astype(str).str.zfill(5)
    catalog["department_code"] = catalog["CODIGO_DEPARTAMENTO"].astype(str).str.zfill(2)
    catalog["municipality_name"] = catalog["NOMBRE_MUNICIPIO"].astype(str)

    unique_codes = catalog["municipality_code"].nunique()
    if unique_codes != 76:
        raise PipelineValidationError(
            f"Expected 76 Tolima/Meta municipalities in DIVIPOLA catalog, found {unique_codes}"
        )

    catalog = catalog[
        ["municipality_code", "department_code", "municipality_name"]
    ].drop_duplicates()
    return catalog.sort_values("municipality_code").reset_index(drop=True)


def normalize_climate_chunks(
    raw_chunks: Iterable[pd.DataFrame],
    scope_codes: set[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Load and validate daily climate rows for Tolima/Meta scope.

    Args:
        paths: Pipeline paths.
        scope_codes: Valid municipality codes in scope.
        config: Pipeline configuration.

    Returns:
        Tuple of unique daily climate dataframe and summary metrics.

    Raises:
        PipelineValidationError: On key/date/type conflicts.
    """

    chunks: list[pd.DataFrame] = []
    source_rows = 0
    filtered_rows = 0
    for chunk in raw_chunks:
        source_rows += len(chunk)
        chunk["mpio_cdpmp"] = normalize_code_series(chunk["mpio_cdpmp"], 5)
        chunk["dpto_ccdgo"] = normalize_code_series(chunk["dpto_ccdgo"], 2)
        chunk = chunk[chunk["mpio_cdpmp"].isin(scope_codes)].copy()
        filtered_rows += len(chunk)
        chunks.append(chunk)

    if not chunks:
        raise PipelineValidationError("No climate rows found for Tolima/Meta scope")

    climate = pd.concat(chunks, ignore_index=True)
    climate["climate_date"] = pd.to_datetime(climate["date"], format="%Y-%m-%d", errors="coerce")
    if climate["climate_date"].isna().any():
        bad = climate.loc[climate["climate_date"].isna(), "date"].head(5).tolist()
        raise PipelineValidationError(f"Climate source contains unparseable dates, sample={bad}")

    department_match = climate["dpto_ccdgo"] == climate["mpio_cdpmp"].str[:2]
    if not bool(department_match.all()):
        mismatches = climate.loc[~department_match, ["dpto_ccdgo", "mpio_cdpmp"]].head(5)
        raise PipelineValidationError(
            "Climate source has municipality/department code mismatch, sample="
            f"{mismatches.to_dict(orient='records')}"
        )

    for column in CLIMATE_DAILY_VARIABLES:
        raw = climate[column].astype(str).str.strip()
        values = pd.to_numeric(raw.replace({"": pd.NA}), errors="coerce")
        invalid = values.isna() & raw.ne("")
        if bool(invalid.any()):
            sample = raw[invalid].head(5).tolist()
            raise PipelineValidationError(
                f"Climate source has invalid numeric values in {column}, sample={sample}"
            )
        climate[column] = values.astype("float64")

    climate["climate_date_iso"] = climate["climate_date"].dt.strftime("%Y-%m-%d")
    climate["climate_join_key"] = climate["mpio_cdpmp"] + "|" + climate["climate_date_iso"]

    duplicates = climate[climate.duplicated("climate_join_key", keep=False)].copy()
    conflicting_duplicate_keys: list[str] = []
    duplicate_exact_count = 0
    if not duplicates.empty:
        for key, group in duplicates.groupby("climate_join_key", sort=False):
            # Exact duplicates are tolerable; conflicting duplicates are blocking.
            normalized = group[CLIMATE_DAILY_VARIABLES].copy()
            sentinel = "__MISSING__"
            normalized = normalized.astype(object).where(normalized.notna(), sentinel)
            distinct_rows = normalized.drop_duplicates()
            if len(distinct_rows) > 1:
                conflicting_duplicate_keys.append(str(key))
            else:
                duplicate_exact_count += len(group) - 1

    if conflicting_duplicate_keys:
        sample = conflicting_duplicate_keys[:5]
        raise PipelineValidationError(
            "Climate key duplicates with conflicting values detected before join, "
            f"sample_keys={sample}, total={len(conflicting_duplicate_keys)}"
        )

    climate_unique = climate.drop_duplicates("climate_join_key", keep="first").copy()
    climate_unique = climate_unique.rename(columns={"mpio_cdpmp": "climate_municipality_code"})
    climate_unique = climate_unique[
        [
            "climate_join_key",
            "climate_municipality_code",
            "climate_date_iso",
            "climate_date",
            *CLIMATE_DAILY_VARIABLES,
        ]
    ].reset_index(drop=True)

    summary = {
        "source_rows": source_rows,
        "scope_rows": filtered_rows,
        "unique_scope_keys": int(climate_unique["climate_join_key"].nunique()),
        "duplicate_exact_rows_ignored": duplicate_exact_count,
        "conflicting_duplicate_keys": len(conflicting_duplicate_keys),
        "scope_min_date": str(climate_unique["climate_date"].min().date()),
        "scope_max_date": str(climate_unique["climate_date"].max().date()),
    }
    return climate_unique, summary
