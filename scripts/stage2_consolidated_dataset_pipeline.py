"""Build candidate Stage 2 datasets for consolidated epidemiological-climate analysis.

This module implements Chapter 1 (dataset construction and validation) of the
new consolidated pipeline notebook. It creates two candidate datasets:

1. data/processed/dengue_y_dengue_grave.csv
2. data/processed/panel_mensual_dengue_clima.csv

The implementation preserves raw epidemiological columns as supplied, adds
provenance metadata, links daily climate by residence municipality and symptom
onset date, and derives a municipality-month panel for Tolima/Meta scope.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tempfile
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

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

Y_HORIZONS = (1, 2)
Y_REFERENCE_YEARS = 5
Y_PERCENTILE = 0.75
Y_PERCENTILE_METHOD = "hyndman_fan_type7_linear"


class PipelineValidationError(RuntimeError):
    """Raised when a blocking validation fails."""


@dataclass(frozen=True)
class PipelinePaths:
    """Resolved project paths for the candidate dataset pipeline.

    Args:
        root: Repository root directory.
        raw_dir: Input raw data directory.
        sources_dir: Input reference directory.
        processed_dir: Output processed data directory.
        interim_dir: Output interim evidence directory.
    """

    root: Path
    raw_dir: Path
    sources_dir: Path
    processed_dir: Path
    interim_dir: Path


@dataclass(frozen=True)
class PipelineConfig:
    """Configuration for candidate dataset construction.

    Args:
        chunksize_epi: Chunksize for epidemiological CSV reads.
        chunksize_climate: Chunksize for climate CSV reads.
        contract_version: Candidate construction contract version string.
        perform_safe_write: If true, write outputs to disk; else dry run.
    """

    chunksize_epi: int = 200_000
    chunksize_climate: int = 250_000
    contract_version: str = "candidate-construction-v1"
    perform_safe_write: bool = True


@dataclass
class PipelineResult:
    """Structured output metadata produced by the pipeline run.

    Args:
        consolidated_path: Final consolidated output path.
        panel_path: Final panel output path.
        consolidated_rows: Number of rows written to consolidated output.
        panel_rows: Number of rows written to panel output.
        consolidated_columns: Number of columns written to consolidated output.
        panel_columns: Number of columns written to panel output.
        manifest_path: Execution manifest path.
        contract_path: Candidate contract artifact path.
        y_traceability_path: Y history traceability artifact path.
    """

    consolidated_path: Path
    panel_path: Path
    consolidated_rows: int
    panel_rows: int
    consolidated_columns: int
    panel_columns: int
    manifest_path: Path
    contract_path: Path
    y_traceability_path: Path


def utc_now_iso() -> str:
    """Return an ISO-8601 UTC timestamp.

    Returns:
        Current UTC timestamp in ISO format.
    """

    return datetime.now(UTC).isoformat()


def sha256_file(path: Path) -> str:
    """Compute SHA-256 digest for a file.

    Args:
        path: File path to hash.

    Returns:
        Hex SHA-256 digest.
    """

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_repo_root(start: Path | None = None) -> Path:
    """Resolve repository root by searching parent directories.

    Args:
        start: Optional start path. If omitted, uses this module path.

    Returns:
        Repository root path.

    Raises:
        PipelineValidationError: If root cannot be resolved.
    """

    anchor = (start or Path(__file__).resolve()).resolve()
    candidates = [anchor, *anchor.parents]
    for candidate in candidates:
        if (candidate / "AGENTS.md").exists() and (candidate / "pyproject.toml").exists():
            return candidate
    raise PipelineValidationError("Unable to resolve repository root from module location")


def build_paths(root: Path) -> PipelinePaths:
    """Build standardized pipeline path mapping.

    Args:
        root: Repository root path.

    Returns:
        Resolved path dataclass.
    """

    return PipelinePaths(
        root=root,
        raw_dir=root / "data/raw",
        sources_dir=root / "data/sources",
        processed_dir=root / "data/processed",
        interim_dir=root / "data/interim/stage2_consolidated_dataset_pipeline",
    )


def read_csv_header(path: Path) -> list[str]:
    """Read CSV header preserving original names.

    Args:
        path: CSV file path.

    Returns:
        Ordered header list.
    """

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        return next(reader)


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


def load_scope_catalog(paths: PipelinePaths) -> pd.DataFrame:
    """Load Tolima/Meta municipality catalog from local DIVIPOLA snapshot.

    Args:
        paths: Pipeline paths.

    Returns:
        Catalog dataframe with municipality and department metadata.

    Raises:
        PipelineValidationError: If catalog shape is unexpected.
    """

    payload = json.loads((paths.sources_dir / "Divipola-municipios.md").read_text(encoding="utf-8"))
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


def validate_epi_headers(paths: PipelinePaths) -> list[str]:
    """Validate epidemiological headers and return canonical columns.

    Args:
        paths: Pipeline paths.

    Returns:
        Canonical epidemiological columns.

    Raises:
        PipelineValidationError: If headers diverge.
    """

    headers = {filename: read_csv_header(paths.raw_dir / filename) for filename in EPI_FILENAMES}
    first = headers[EPI_FILENAMES[0]]
    for filename in EPI_FILENAMES[1:]:
        if headers[filename] != first:
            raise PipelineValidationError(
                "Epidemiological headers diverge; candidate requires explicit reconciliation "
                f"before construction ({EPI_FILENAMES[0]} vs {filename})"
            )
    if len(first) != 69:
        raise PipelineValidationError(f"Expected 69 epidemiological columns, found {len(first)}")
    return first


def validate_climate_header(paths: PipelinePaths) -> list[str]:
    """Validate climate source header.

    Args:
        paths: Pipeline paths.

    Returns:
        Climate header list.

    Raises:
        PipelineValidationError: If required columns are missing.
    """

    header = read_csv_header(paths.raw_dir / CLIMATE_FILENAME)
    required = {
        "date",
        "dpto_ccdgo",
        "mpio_cdpmp",
        *CLIMATE_DAILY_VARIABLES,
    }
    missing = sorted(required - set(header))
    if missing:
        raise PipelineValidationError(f"Climate source missing required columns: {missing}")
    return header


def load_scope_climate_daily(
    paths: PipelinePaths,
    scope_codes: set[str],
    config: PipelineConfig,
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

    selected_columns = [
        "date",
        "dpto_ccdgo",
        "mpio_cdpmp",
        *CLIMATE_DAILY_VARIABLES,
    ]

    chunks: list[pd.DataFrame] = []
    source_rows = 0
    filtered_rows = 0
    for chunk in pd.read_csv(
        paths.raw_dir / CLIMATE_FILENAME,
        dtype=str,
        usecols=selected_columns,
        chunksize=config.chunksize_climate,
        keep_default_na=False,
    ):
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

    return {
        "contract_version": version,
        "classification": "candidate_construction_contract",
        "generated_utc": utc_now_iso(),
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


def ensure_directory(path: Path) -> None:
    """Create directory recursively if absent.

    Args:
        path: Directory path.
    """

    path.mkdir(parents=True, exist_ok=True)


def safe_replace_file(
    *,
    tmp_path: Path,
    final_path: Path,
    backup_dir: Path,
) -> dict[str, Any]:
    """Atomically replace output file with backup preservation.

    Args:
        tmp_path: Temporary file path.
        final_path: Final target path.
        backup_dir: Backup directory.

    Returns:
        Backup metadata dictionary.

    Raises:
        PipelineValidationError: If replacement cannot be completed.
    """

    ensure_directory(final_path.parent)
    ensure_directory(backup_dir)

    metadata: dict[str, Any] = {
        "target": str(final_path),
        "had_previous": final_path.exists(),
    }

    if final_path.exists():
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup_path = backup_dir / f"{final_path.name}.{timestamp}.bak"
        shutil.copy2(final_path, backup_path)
        metadata["backup_path"] = str(backup_path)
        metadata["backup_sha256"] = sha256_file(backup_path)

    tmp_path.replace(final_path)
    metadata["final_sha256"] = sha256_file(final_path)
    metadata["final_bytes"] = final_path.stat().st_size
    return metadata


def fingerprint_inputs(paths: PipelinePaths) -> dict[str, Any]:
    """Compute source fingerprints for reproducibility evidence.

    Args:
        paths: Pipeline paths.

    Returns:
        Input fingerprint dictionary.
    """

    files = [
        paths.raw_dir / "dengue.csv",
        paths.raw_dir / "dengue_grave.csv",
        paths.raw_dir / "google_earth_engine.csv",
        paths.sources_dir / "Divipola-municipios.md",
        paths.sources_dir / "divipola-provenance.json",
    ]
    return {
        str(path.relative_to(paths.root)): {
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in files
    }


def write_dataframe_to_tmp(frame: pd.DataFrame, output_path: Path) -> Path:
    """Write dataframe to temp CSV in destination directory.

    Args:
        frame: Dataframe to write.
        output_path: Destination output path.

    Returns:
        Temporary file path.
    """

    ensure_directory(output_path.parent)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".tmp",
        prefix=f"{output_path.name}.",
        dir=output_path.parent,
        delete=False,
    ) as tmp:
        frame.to_csv(tmp.name, index=False)
        return Path(tmp.name)


def run_pipeline(root: Path | None = None, config: PipelineConfig | None = None) -> PipelineResult:
    """Execute the complete candidate dataset construction pipeline.

    Args:
        root: Optional repository root. If omitted, auto-resolved.
        config: Optional pipeline configuration.

    Returns:
        PipelineResult with output paths and shape metadata.

    Raises:
        PipelineValidationError: On any blocking validation issue.
    """

    cfg = config or PipelineConfig()
    repo_root = resolve_repo_root(root)
    paths = build_paths(repo_root)
    ensure_directory(paths.interim_dir)

    input_fingerprints_before = fingerprint_inputs(paths)

    epi_columns = validate_epi_headers(paths)
    climate_header = validate_climate_header(paths)

    catalog = load_scope_catalog(paths)
    scope_codes = set(catalog["municipality_code"].tolist())

    climate_daily, climate_summary = load_scope_climate_daily(paths, scope_codes, cfg)
    climate_lookup = climate_daily[
        [
            "climate_join_key",
            "climate_municipality_code",
            "climate_date_iso",
            "climate_date",
            *CLIMATE_DAILY_VARIABLES,
        ]
    ].copy()

    consolidated_output = paths.processed_dir / "dengue_y_dengue_grave.csv"
    panel_output = paths.processed_dir / "panel_mensual_dengue_clima.csv"
    y_traceability_output = paths.interim_dir / "y_label_history_traceability.csv"

    ensure_directory(paths.processed_dir)
    backups_dir = paths.interim_dir / "backups"

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".tmp",
        prefix=f"{consolidated_output.name}.",
        dir=paths.processed_dir,
        delete=False,
    ) as consolidated_tmp_file:
        consolidated_tmp_path = Path(consolidated_tmp_file.name)

    wrote_consolidated_header = False
    consolidated_columns: list[str] = []
    consolidated_rows_total = 0
    source_row_totals: dict[str, int] = {}
    assignable_counts: dict[str, int] = {"dengue": 0, "dengue_grave": 0}
    monthly_counter: dict[tuple[str, str], dict[str, int]] = defaultdict(
        lambda: {"dengue": 0, "dengue_grave": 0}
    )
    reconciliation_counts: dict[str, int] = {
        "outside_scope_rows": 0,
        "missing_or_unparseable_onset_rows": 0,
        "no_climate_match_assignable_rows": 0,
        "assignable_rows": 0,
    }
    epi_start: str | None = None
    epi_end: str | None = None

    for source_file in EPI_FILENAMES:
        source_path = paths.raw_dir / source_file
        source_rows_seen = 0
        for chunk in pd.read_csv(
            source_path,
            dtype=str,
            usecols=epi_columns,
            chunksize=cfg.chunksize_epi,
            keep_default_na=False,
        ):
            start_row = source_rows_seen + 1
            source_rows_seen += len(chunk)
            enriched = enrich_epi_chunk(
                chunk,
                source_file=source_file,
                source_row_start=start_row,
                scope_codes=scope_codes,
                climate_lookup=climate_lookup,
            )

            if not wrote_consolidated_header:
                consolidated_columns = list(enriched.columns)
                wrote_consolidated_header = True

            enriched.to_csv(
                consolidated_tmp_path,
                mode="a",
                index=False,
                header=not wrote_consolidated_header or consolidated_rows_total == 0,
            )
            consolidated_rows_total += len(enriched)

            reason_series = enriched["panel_assignment_reason"]
            reconciliation_counts["outside_scope_rows"] += int(
                reason_series.eq("out_of_scope_municipality").sum()
            )
            reconciliation_counts["missing_or_unparseable_onset_rows"] += int(
                reason_series.isin(["missing_ini_sin", "unparseable_ini_sin"]).sum()
            )

            assignable = enriched[reason_series.eq("assignable")].copy()
            reconciliation_counts["assignable_rows"] += int(len(assignable))
            reconciliation_counts["no_climate_match_assignable_rows"] += int(
                assignable["climate_join_status"].eq("no_climate_match").sum()
            )

            if not assignable.empty:
                assignable["year_month"] = assignable["norm_ini_sin_date"].str.slice(0, 7)
                month_min = str(assignable["year_month"].min())
                month_max = str(assignable["year_month"].max())
                epi_start = month_min if epi_start is None else min(epi_start, month_min)
                epi_end = month_max if epi_end is None else max(epi_end, month_max)

                grouped = (
                    assignable.groupby(
                        [
                            "norm_residence_municipality_code",
                            "year_month",
                            "source_label",
                        ],
                        dropna=False,
                    )
                    .size()
                    .rename("count")
                    .reset_index()
                )
                for row in grouped.itertuples(index=False):
                    municipality_code = str(row.norm_residence_municipality_code)
                    year_month = str(row.year_month)
                    source_label = str(row.source_label)
                    count = int(row.count)
                    monthly_counter[(municipality_code, year_month)][source_label] += count
                    assignable_counts[source_label] += count
        source_row_totals[source_file] = source_rows_seen

    expected_rows = sum(source_row_totals.values())
    if consolidated_rows_total != expected_rows:
        raise PipelineValidationError(
            "Consolidated row count mismatch: "
            f"got {consolidated_rows_total}, expected {expected_rows}"
        )

    original_columns = set(epi_columns)
    if not original_columns.issubset(set(consolidated_columns)):
        missing = sorted(original_columns - set(consolidated_columns))
        raise PipelineValidationError(f"Consolidated output missing original columns: {missing}")

    if reconciliation_counts["assignable_rows"] == 0 or epi_start is None or epi_end is None:
        raise PipelineValidationError("No assignable epidemiological rows for panel construction")

    epi_counts = build_epi_monthly_counts_from_counter(monthly_counter)

    climate_monthly = aggregate_monthly_climate(climate_daily)
    climate_start = str(climate_monthly["year_month"].min())
    climate_end = str(climate_monthly["year_month"].max())

    panel_start = min(epi_start, climate_start)
    panel_end = max(epi_end, climate_end)

    grid = build_panel_grid(catalog, panel_start, panel_end)
    panel = build_monthly_panel(
        grid=grid,
        epi_counts=epi_counts,
        climate_monthly=climate_monthly,
        epi_coverage_start=epi_start,
        epi_coverage_end=epi_end,
    )

    panel_rows_before_labels = len(panel)
    panel_keys_before_labels = panel[["municipality_code", "year_month"]].copy()
    panel, y_traceability = compute_y_labels(panel)

    if len(panel) != panel_rows_before_labels:
        raise PipelineValidationError(
            "Y labeling changed panel row cardinality, which is not allowed"
        )
    if not panel[["municipality_code", "year_month"]].equals(panel_keys_before_labels):
        raise PipelineValidationError("Y labeling modified panel key columns")

    if panel.duplicated(["municipality_code", "year_month"]).any():
        raise PipelineValidationError("Panel key municipality_code+year_month is not unique")

    for horizon in Y_HORIZONS:
        suffix = f"t{horizon}"
        evaluable_col = f"y_evaluable_{suffix}"
        status_col = f"y_status_{suffix}"
        label_col = f"y_{suffix}"

        non_evaluable_with_label = (~panel[evaluable_col]) & panel[label_col].notna()
        if bool(non_evaluable_with_label.any()):
            raise PipelineValidationError(f"Non-evaluable rows in {label_col} must remain null")

        invalid_labels = panel[label_col].dropna().astype("int64")
        if not invalid_labels.isin([0, 1]).all():
            raise PipelineValidationError(
                f"{label_col} must contain only 0/1 values when evaluable"
            )

        expected_statuses = {
            "evaluable",
            "insufficient_history",
            "future_observation_missing",
            "target_outside_panel",
        }
        unknown_statuses = set(panel[status_col].dropna().unique()) - expected_statuses
        if unknown_statuses:
            raise PipelineValidationError(
                f"{status_col} contains unknown values: {sorted(unknown_statuses)}"
            )

    y_label_summary = summarize_y_labels(panel)

    dengue_total = int(assignable_counts.get("dengue", 0))
    dengue_grave_total = int(assignable_counts.get("dengue_grave", 0))

    panel_dengue_sum = int(panel["dengue_notifications_count"].fillna(0).sum())
    panel_dengue_grave_sum = int(panel["dengue_grave_notifications_count"].fillna(0).sum())
    if panel_dengue_sum != dengue_total:
        raise PipelineValidationError(
            "Panel dengue count reconciliation failed: "
            f"panel={panel_dengue_sum}, assignable={dengue_total}"
        )
    if panel_dengue_grave_sum != dengue_grave_total:
        raise PipelineValidationError(
            "Panel dengue_grave count reconciliation failed: "
            f"panel={panel_dengue_grave_sum}, assignable={dengue_grave_total}"
        )

    panel_tmp = write_dataframe_to_tmp(panel, panel_output)
    y_traceability_tmp = write_dataframe_to_tmp(y_traceability, y_traceability_output)

    consolidated_schema = describe_consolidated_schema_from_columns(consolidated_columns)
    candidate_contract = compute_schema_contract(
        consolidated_schema,
        panel,
        version=cfg.contract_version,
    )
    candidate_contract_path = paths.interim_dir / "candidate_construction_contract_v1.json"

    if cfg.perform_safe_write:
        consolidated_backup = safe_replace_file(
            tmp_path=consolidated_tmp_path,
            final_path=consolidated_output,
            backup_dir=backups_dir,
        )
        panel_backup = safe_replace_file(
            tmp_path=panel_tmp,
            final_path=panel_output,
            backup_dir=backups_dir,
        )
        y_traceability_backup = safe_replace_file(
            tmp_path=y_traceability_tmp,
            final_path=y_traceability_output,
            backup_dir=backups_dir,
        )

        # Write contract via temporary file without converting it to tabular CSV.
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".tmp",
            prefix=f"{candidate_contract_path.name}.",
            dir=candidate_contract_path.parent,
            delete=False,
        ) as contract_tmp:
            contract_tmp.write(json.dumps(candidate_contract, ensure_ascii=False, indent=2) + "\n")
            contract_tmp_path = Path(contract_tmp.name)
        contract_backup = safe_replace_file(
            tmp_path=contract_tmp_path,
            final_path=candidate_contract_path,
            backup_dir=backups_dir,
        )
    else:
        if consolidated_tmp_path.exists():
            consolidated_tmp_path.unlink()
        if panel_tmp.exists():
            panel_tmp.unlink()
        if y_traceability_tmp.exists():
            y_traceability_tmp.unlink()
        consolidated_backup = {}
        panel_backup = {}
        y_traceability_backup = {}
        contract_backup = {}

    input_fingerprints_after = fingerprint_inputs(paths)
    if input_fingerprints_before != input_fingerprints_after:
        raise PipelineValidationError("Input fingerprints changed during pipeline execution")

    summary = {
        "generated_utc": utc_now_iso(),
        "pipeline": {
            "module": "scripts/stage2_consolidated_dataset_pipeline.py",
            "contract_version": cfg.contract_version,
            "chunksize_epi": cfg.chunksize_epi,
            "chunksize_climate": cfg.chunksize_climate,
        },
        "input_fingerprints_before": input_fingerprints_before,
        "input_fingerprints_after": input_fingerprints_after,
        "headers": {
            "epi_columns": epi_columns,
            "climate_columns": climate_header,
        },
        "climate_daily_summary": climate_summary,
        "coverage": {
            "epi_coverage_start_month": epi_start,
            "epi_coverage_end_month": epi_end,
            "climate_coverage_start_month": climate_start,
            "climate_coverage_end_month": climate_end,
            "panel_month_start": panel_start,
            "panel_month_end": panel_end,
            "scope_municipalities": int(catalog["municipality_code"].nunique()),
        },
        "reconciliation": {
            "source_rows": source_row_totals,
            "consolidated_rows": consolidated_rows_total,
            "assignable_rows": reconciliation_counts["assignable_rows"],
            "panel_sum_dengue": panel_dengue_sum,
            "panel_sum_dengue_grave": panel_dengue_grave_sum,
            "outside_scope_rows": reconciliation_counts["outside_scope_rows"],
            "missing_or_unparseable_onset_rows": reconciliation_counts[
                "missing_or_unparseable_onset_rows"
            ],
            "no_climate_match_assignable_rows": reconciliation_counts[
                "no_climate_match_assignable_rows"
            ],
        },
        "target_labeling": {
            "retrospective_assumption": (
                "At cutoff T, each horizon target compares observed dengue count at T+h against "
                "P75 from the same target month across the five prior years before target year."
            ),
            **y_label_summary,
        },
        "outputs": {
            "dengue_y_dengue_grave": {
                "path": str(consolidated_output.relative_to(paths.root)),
                "rows": consolidated_rows_total,
                "columns": int(len(consolidated_columns)),
                "sha256": (
                    sha256_file(consolidated_output) if consolidated_output.exists() else None
                ),
                "bytes": (
                    consolidated_output.stat().st_size if consolidated_output.exists() else None
                ),
                "backup": consolidated_backup,
            },
            "panel_mensual_dengue_clima": {
                "path": str(panel_output.relative_to(paths.root)),
                "rows": int(len(panel)),
                "columns": int(len(panel.columns)),
                "sha256": sha256_file(panel_output) if panel_output.exists() else None,
                "bytes": panel_output.stat().st_size if panel_output.exists() else None,
                "backup": panel_backup,
            },
            "y_label_history_traceability": {
                "path": str(y_traceability_output.relative_to(paths.root)),
                "rows": int(len(y_traceability)),
                "columns": int(len(y_traceability.columns)),
                "sha256": sha256_file(y_traceability_output)
                if y_traceability_output.exists()
                else None,
                "bytes": y_traceability_output.stat().st_size
                if y_traceability_output.exists()
                else None,
                "backup": y_traceability_backup,
            },
            "candidate_contract": {
                "path": str(candidate_contract_path.relative_to(paths.root)),
                "sha256": sha256_file(candidate_contract_path)
                if candidate_contract_path.exists()
                else None,
                "backup": contract_backup,
            },
        },
    }

    manifest_path = paths.interim_dir / "execution_manifest.json"
    manifest_tmp_path = None
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".tmp",
        prefix="execution_manifest.json.",
        dir=paths.interim_dir,
        delete=False,
    ) as manifest_tmp:
        manifest_tmp.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        manifest_tmp_path = Path(manifest_tmp.name)

    safe_replace_file(
        tmp_path=manifest_tmp_path,
        final_path=manifest_path,
        backup_dir=backups_dir,
    )

    return PipelineResult(
        consolidated_path=consolidated_output,
        panel_path=panel_output,
        consolidated_rows=consolidated_rows_total,
        panel_rows=int(len(panel)),
        consolidated_columns=int(len(consolidated_columns)),
        panel_columns=int(len(panel.columns)),
        manifest_path=manifest_path,
        contract_path=candidate_contract_path,
        y_traceability_path=y_traceability_output,
    )


def _print_summary(result: PipelineResult, root: Path) -> None:
    """Print concise aggregate execution summary.

    Args:
        result: Pipeline result metadata.
        root: Repository root.
    """

    payload = {
        "consolidated_path": str(result.consolidated_path.relative_to(root)),
        "panel_path": str(result.panel_path.relative_to(root)),
        "y_traceability_path": str(result.y_traceability_path.relative_to(root)),
        "consolidated_rows": result.consolidated_rows,
        "panel_rows": result.panel_rows,
        "consolidated_columns": result.consolidated_columns,
        "panel_columns": result.panel_columns,
        "manifest_path": str(result.manifest_path.relative_to(root)),
        "contract_path": str(result.contract_path.relative_to(root)),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument iterable.

    Returns:
        Parsed namespace.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build datasets in memory and validate without replacing outputs.",
    )
    parser.add_argument(
        "--chunksize-epi",
        type=int,
        default=PipelineConfig.chunksize_epi,
        help="Chunksize for epidemiological source reads.",
    )
    parser.add_argument(
        "--chunksize-climate",
        type=int,
        default=PipelineConfig.chunksize_climate,
        help="Chunksize for climate source reads.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None) -> int:
    """CLI entry point for candidate dataset construction.

    Args:
        argv: Optional command-line arguments.

    Returns:
        Process exit code.
    """

    args = parse_args(argv)
    config = PipelineConfig(
        chunksize_epi=args.chunksize_epi,
        chunksize_climate=args.chunksize_climate,
        perform_safe_write=not args.dry_run,
    )

    root = resolve_repo_root()
    result = run_pipeline(root=root, config=config)
    _print_summary(result, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
