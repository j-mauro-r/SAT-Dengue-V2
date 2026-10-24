"""Preserved Stage 2 calculations extracted without algorithm changes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

RESERVED_BLOCK_START = "2025-01"


ALLOWED_ADDITIVE_PANEL_COLUMNS = {
    "p25_canal_t",
    "p50_canal_t",
    "p75_canal_t",
    "zona_canal_t",
}


INPUT_FINGERPRINT_RELATIVE_PATHS = (
    "data/raw/dengue.csv",
    "data/raw/dengue_grave.csv",
    "data/raw/google_earth_engine.csv",
    "data/sources/Divipola-municipios.md",
    "data/sources/divipola-provenance.json",
)


CANAL_ZONE_VALUES = {"EXITO", "SEGURIDAD", "ALERTA", "EXCESO"}


TEMPORAL_WINDOW_TRAIN_ENDPOINTS = ("2018-12", "2020-12", "2022-12", "2024-06")


NOTEBOOK_ANALYSIS_MANIFEST = "tmp/stage2_y_reconciliation/notebook_analysis_manifest.json"


NOTEBOOK_PATH_RELATIVE = "notebooks/03_consolidated_dataset_pipeline.ipynb"


NOTEBOOK_REQUIRED_OUTPUT_SECTION_MARKERS = (
    "Chapter 1 - Section 6: Monthly panel inspection",
    "Chapter 6 - Relationships with Y and lag diagnostics by horizon",
    "Chapter 8 - Temporal validation protocol structure",
    "Chapter 10 - Analysis manifest and scope validator",
)


NOTEBOOK_FINGERPRINT_MODULE_PATHS = (
    "scripts/stage2_consolidated_dataset_pipeline.py",
    "scripts/stage2_notebook_visual_assets.py",
    "scripts/validate_stage2_training_readiness.py",
)


@dataclass(frozen=True)
class ValidationMessage:
    """Structured validation message.

    Args:
        check: Check identifier.
        status: PASS, FAIL, BLOCKED or UNVERIFIED.
        detail: Human-readable detail.
    """

    check: str
    status: str
    detail: str


def parse_expected_byte_count(value: Any) -> int | None:
    """Parse a manifest byte-count value into a non-negative integer.

    Args:
        value: Raw manifest value.

    Returns:
        Parsed non-negative integer, or None when the value is missing/invalid.
    """

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int):
        return value if value >= 0 else None

    if isinstance(value, float):
        if not value.is_integer():
            return None
        parsed_float = int(value)
        return parsed_float if parsed_float >= 0 else None

    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        if candidate.startswith("+"):
            candidate = candidate[1:]
        if not candidate.isdigit():
            return None
        return int(candidate)

    return None


def independent_percentile_type7(values: list[float], q: float) -> float:
    """Compute Hyndman-Fan type-7 percentile independently of production code.

    Args:
        values: Numeric values.
        q: Quantile in [0, 1].

    Returns:
        Percentile value.
    """

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


def independent_history_periods(target_period: str, history_years: int = 5) -> list[str]:
    """Build expected same-month historical periods without production helpers.

    Args:
        target_period: Target period in YYYY-MM.
        history_years: Number of expected previous years.

    Returns:
        Ordered list of periods.
    """

    target_year = int(target_period[:4])
    target_month = target_period[5:7]
    return [
        f"{year:04d}-{target_month}" for year in range(target_year - history_years, target_year)
    ]


def independent_classify_endemic_zone(
    current_count: float,
    p25: float,
    p50: float,
    p75: float,
) -> str:
    """Classify endemic zone independently of production pipeline function.

    Args:
        current_count: Current count at reference month.
        p25: P25 threshold.
        p50: P50 threshold.
        p75: P75 threshold.

    Returns:
        Zone label.
    """

    if current_count < p25:
        return "EXITO"
    if current_count <= p50:
        return "SEGURIDAD"
    if current_count <= p75:
        return "ALERTA"
    return "EXCESO"


def recompute_channel_independently(panel: pd.DataFrame) -> pd.DataFrame:
    """Recompute current endemic-channel columns from panel counts independently.

    Args:
        panel: Panel dataframe with municipality/month and count columns.

    Returns:
        Dataframe with independent thresholds, zone and status by key.
    """

    required = {"municipality_code", "year_month", "dengue_notifications_count"}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Panel missing required channel columns: {missing}")

    frame = panel.copy()
    frame["municipality_code"] = frame["municipality_code"].astype(str).str.zfill(5)
    frame["year_month"] = frame["year_month"].astype(str).map(period_to_yyyymm)
    frame["dengue_notifications_count"] = pd.to_numeric(
        frame["dengue_notifications_count"],
        errors="coerce",
    )
    frame = frame.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)

    lookup = frame.set_index(["municipality_code", "year_month"])[
        "dengue_notifications_count"
    ].to_dict()

    rows: list[dict[str, Any]] = []
    for row in frame.itertuples(index=False):
        municipality_code = str(row.municipality_code)
        reference_period = str(row.year_month)
        history_expected = independent_history_periods(reference_period, 5)
        history_values: list[float] = []
        history_used: list[str] = []
        history_missing: list[str] = []

        for history_period in history_expected:
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
        status = "insufficient_history"

        if pd.isna(current_count_raw):
            status = "current_count_missing"
        elif len(history_values) < 5:
            status = "insufficient_history"
        else:
            current_count = float(current_count_raw)
            p25_value = independent_percentile_type7(history_values, 0.25)
            p50_value = independent_percentile_type7(history_values, 0.5)
            p75_value = independent_percentile_type7(history_values, 0.75)
            zone_value = independent_classify_endemic_zone(
                current_count,
                p25_value,
                p50_value,
                p75_value,
            )
            status = "evaluable"

        rows.append(
            {
                "municipality_code": municipality_code,
                "year_month": reference_period,
                "independent_history_periods_expected": "|".join(history_expected),
                "independent_history_periods_used": "|".join(history_used),
                "independent_history_missing_periods": "|".join(history_missing),
                "independent_p25_canal_t": p25_value,
                "independent_p50_canal_t": p50_value,
                "independent_p75_canal_t": p75_value,
                "independent_zona_canal_t": zone_value,
                "independent_channel_status": status,
            }
        )

    return pd.DataFrame(rows)


def independent_select_supervised_rows(
    panel: pd.DataFrame,
    horizon: int,
    *,
    reference_min_period: str | None = None,
    reference_max_period: str | None = None,
    target_min_period: str | None = None,
    target_max_period: str | None = None,
) -> pd.DataFrame:
    """Select supervised rows with explicit temporal rules.

    Args:
        panel: Panel dataframe.
        horizon: Horizon number (1 or 2).
        reference_min_period: Optional minimum reference period.
        reference_max_period: Optional maximum reference period.
        target_min_period: Optional minimum target period.
        target_max_period: Optional maximum target period.

    Returns:
        Selected subset.
    """

    evaluable_column = f"y_evaluable_t{horizon}"
    target_column = f"target_period_t{horizon}"

    required = {"municipality_code", "year_month", evaluable_column, target_column}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise RuntimeError(f"Panel missing required supervised-selection columns: {missing}")

    frame = panel.copy()
    frame["municipality_code"] = frame["municipality_code"].astype(str).str.zfill(5)
    frame["year_month"] = frame["year_month"].astype(str).map(period_to_yyyymm)
    frame[target_column] = frame[target_column].astype(str).map(period_to_yyyymm)

    mask = frame[evaluable_column].fillna(False).astype(bool)
    if reference_min_period is not None:
        mask &= frame["year_month"] >= str(reference_min_period)
    if reference_max_period is not None:
        mask &= frame["year_month"] <= str(reference_max_period)
    if target_min_period is not None:
        mask &= frame[target_column] >= str(target_min_period)
    if target_max_period is not None:
        mask &= frame[target_column] <= str(target_max_period)
    return frame[mask].copy()


def collect_manifest_paths(value: Any) -> list[str]:
    """Collect relative path strings from a nested JSON-like value.

    Args:
        value: Nested JSON-like value.

    Returns:
        Collected path-like strings.
    """

    if isinstance(value, str):
        return [value] if "/" in value else []
    if isinstance(value, dict):
        collected: list[str] = []
        for nested in value.values():
            collected.extend(collect_manifest_paths(nested))
        return collected
    if isinstance(value, list):
        collected = []
        for nested in value:
            collected.extend(collect_manifest_paths(nested))
        return collected
    return []


def period_to_yyyymm(value: str) -> str:
    """Normalize a period-like value into YYYY-MM.

    Args:
        value: Input period text.

    Returns:
        Normalized period string.
    """

    return str(pd.Period(str(value), freq="M"))


def add_months(period: str, months: int) -> str:
    """Shift YYYY-MM by a month offset.

    Args:
        period: Base period.
        months: Signed month shift.

    Returns:
        Shifted period.
    """

    return str(pd.Period(period, freq="M") + months)


def panel_y_p75_signature(panel: pd.DataFrame) -> str:
    """Compute stable signature over existing Y/P75 columns.

    Args:
        panel: Panel dataframe.

    Returns:
        SHA-256 over a canonical CSV payload for Y/P75 columns.
    """

    columns = [
        "municipality_code",
        "year_month",
        "target_period_t1",
        "target_period_t2",
        "p75_t1",
        "p75_t2",
        "y_evaluable_t1",
        "y_evaluable_t2",
        "y_status_t1",
        "y_status_t2",
        "y_t1",
        "y_t2",
    ]
    available = [column for column in columns if column in panel.columns]
    payload = panel.sort_values(["municipality_code", "year_month"])[available].to_csv(index=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def compute_edge_contribution(
    panel: pd.DataFrame,
    backed_start: str,
    backed_end: str,
) -> dict[str, Any]:
    """Count in-coverage rows outside backed year metadata interval.

    Args:
        panel: Monthly panel.
        backed_start: Backed interval start YYYY-MM.
        backed_end: Backed interval end YYYY-MM.

    Returns:
        Edge contribution summary.
    """

    scoped = panel.copy()
    scoped["year_month"] = scoped["year_month"].astype(str).map(period_to_yyyymm)
    in_coverage = scoped["in_epi_coverage"].fillna(False)
    out_of_backed = (scoped["year_month"] < backed_start) | (scoped["year_month"] > backed_end)
    edge = scoped[in_coverage & out_of_backed]

    dengue_sum = float(
        pd.to_numeric(
            edge.get("dengue_notifications_count"),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )
    dengue_grave_sum = float(
        pd.to_numeric(
            edge.get("dengue_grave_notifications_count"),
            errors="coerce",
        )
        .fillna(0)
        .sum()
    )
    y_eval_t1 = int(edge.get("y_evaluable_t1", pd.Series(dtype=bool)).fillna(False).sum())
    y_eval_t2 = int(edge.get("y_evaluable_t2", pd.Series(dtype=bool)).fillna(False).sum())

    return {
        "backed_interval": {"start": backed_start, "end": backed_end},
        "rows": int(len(edge)),
        "months": sorted(edge["year_month"].unique().tolist()),
        "dengue_count_sum": dengue_sum,
        "dengue_grave_count_sum": dengue_grave_sum,
        "y_evaluable_t1_rows": y_eval_t1,
        "y_evaluable_t2_rows": y_eval_t2,
    }


def build_model_eligibility_policy(
    notification_min_year: int,
    notification_max_year: int,
    *,
    reserved_block_start: str = RESERVED_BLOCK_START,
) -> dict[str, Any]:
    """Build conservative model-eligibility policy from year metadata.

    Args:
        notification_min_year: Minimum notification year in source metadata.
        notification_max_year: Maximum notification year in source metadata.
        reserved_block_start: Reserved holdout start month.

    Returns:
        Eligibility policy dictionary.
    """

    backed_start = f"{notification_min_year:04d}-01"
    backed_end = f"{notification_max_year:04d}-12"
    earliest_target_with_5y_history = add_months(backed_start, 12 * 5)
    latest_target_before_reserved = add_months(reserved_block_start, -1)

    target_end = min(backed_end, latest_target_before_reserved)
    earliest_cutoff_t1 = add_months(earliest_target_with_5y_history, -1)
    earliest_cutoff_t2 = add_months(earliest_target_with_5y_history, -2)

    return {
        "source_coverage_backed_by_notification_year": {
            "start": backed_start,
            "end": backed_end,
        },
        "development_target_eligibility": {
            "target_min": earliest_target_with_5y_history,
            "target_max": target_end,
            "reserved_block_start": reserved_block_start,
            "rationale": (
                "Conservative modeling eligibility: require target periods fully inside "
                "notification-year-backed interval, below reserved block, and with five same-month "
                "historical observations."
            ),
        },
        "earliest_cutoff_with_eligible_target": {
            "t1": earliest_cutoff_t1,
            "t2": earliest_cutoff_t2,
        },
        "important_distinctions": {
            "coverage": "Backed interval from source notification-year metadata.",
            "history_sufficiency": "Per-row five-year same-month availability for each horizon.",
            "operational_availability": (
                "Retrospective consolidated data do not prove real-time historical "
                "as-of availability."
            ),
        },
    }


def extract_development_target_bounds(policy: dict[str, Any]) -> tuple[str, str, str]:
    """Extract development target bounds from the active policy payload.

    Args:
        policy: Model-eligibility policy dictionary.

    Returns:
        Tuple ``(target_min, target_max, reserved_block_start)``.
    """

    development = policy["development_target_eligibility"]
    return (
        str(development["target_min"]),
        str(development["target_max"]),
        str(development["reserved_block_start"]),
    )


def statuses_summary(messages: list[ValidationMessage]) -> dict[str, int]:
    """Count statuses in validation messages."""

    counts = {"PASS": 0, "FAIL": 0, "BLOCKED": 0, "UNVERIFIED": 0}
    for message in messages:
        counts[message.status] = counts.get(message.status, 0) + 1
    return counts
