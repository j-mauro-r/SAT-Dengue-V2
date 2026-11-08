"""Pure national notification diagnostic calculations; filesystem work lives in datasets."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Protocol

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import normalize_code_series, parse_epi_date_series

SOURCES = (
    "data/raw/dengue.csv",
    "data/raw/dengue_grave.csv",
    "data/sources/Listados_DIVIPOLA.xlsx",
    "data/sources/Divipola-municipios.md",
    "data/sources/Divipola-departamentos.md",
    "data/sources/divipola-provenance.json",
)


ESSENTIAL = ("COD_DPTO_R", "COD_MUN_R", "INI_SIN", "COD_EVE")


STREAMS = {"dengue.csv": "210", "dengue_grave.csv": "220"}


COUNTS = {"210": "dengue_notifications_count", "220": "dengue_grave_notifications_count"}


LIMITATIONS = [
    "D1: occurrence/notification date differences are accepted; INI_SIN is never replaced.",
    "D2/D3: within the configured review calendar, absence of rows means zero notifications.",
    "File hashes establish snapshot integrity, not completeness of official extraction.",
    "Current DIVIPOLA membership does not establish historical territorial applicability.",
    "No validated historical crosswalk is supplied; no territorial reassignment is applied.",
    "Counts describe notifications, not unique patients, episodes or confirmed cases.",
    "Retrospective extracts cannot establish operational point-in-time availability.",
    "Climate, H5, labels and training admission are not evaluated in this analysis.",
]


@dataclass(frozen=True)
class AnalysisConfig:
    """Explicit review window, independent of future notification density.

    The defaults follow EXP-BETA01's training start and stop before its reserved
    2025 block. This diagnostic window is not a source-completeness assertion.
    """

    start_month: str = "2011-06"
    end_month: str = "2024-12"
    chunksize: int = 100_000
    output_dir: str = "data/interim/canonical-nacional-data"

    def __post_init__(self) -> None:
        for value in (self.start_month, self.end_month):
            if str(pd.Period(value, freq="M")) != value:
                raise ValueError("Review bounds must use YYYY-MM")
        if self.start_month > self.end_month or self.chunksize < 1:
            raise ValueError("Invalid review bounds or chunk size")
        if self.end_month >= "2025-01":
            raise ValueError("The reserved 2025 block is outside this diagnostic task")
        if self.output_dir.startswith("/") or ".." in self.output_dir.split("/"):
            raise ValueError("Output must be repository relative")
        if not self.output_dir.startswith("data/interim/canonical-nacional-data"):
            raise ValueError("Keep diagnostic outputs inside the dedicated interim directory")


class CalendarWindow(Protocol):
    """Bounds shared by historical diagnostics and explicitly authorized new panels."""

    @property
    def start_month(self) -> str: ...

    @property
    def end_month(self) -> str: ...


def classify_notifications(
    raw: pd.DataFrame, catalog: pd.DataFrame, expected_event: str, config: CalendarWindow
) -> pd.DataFrame:
    """Classify rows without changing raw fields or removing duplicate notifications.

    Args:
        raw: One source chunk, read as strings.
        catalog: Full national reference.
        expected_event: Event required by this source stream.
        config: Fixed review parameters.

    Returns:
        Separate helpers and independent exclusion flags, aligned to input rows.
    """
    fields = {name: raw[name].fillna("").astype(str).str.strip() for name in ESSENTIAL}
    dept = normalize_code_series(fields["COD_DPTO_R"], 2)
    mun = normalize_code_series(fields["COD_MUN_R"], 3)
    code = (dept + mun).where(dept.ne("") & mun.ne(""), "")
    valid = code.isin(catalog["municipality_code"])
    category = pd.Series("requires_review", index=raw.index)
    # Potentially historical is a triage category, never a proven equivalence.
    category.loc[dept.isin(catalog["department_code"]) & ~valid] = (
        "historical_or_potentially_homologable"
    )
    category.loc[code.eq("")] = "incomplete_or_unknown"
    category.loc[valid] = "valid"
    onset = parse_epi_date_series(raw["INI_SIN"])
    month = onset.dt.strftime("%Y-%m").fillna("")
    event = normalize_code_series(fields["COD_EVE"], 3)
    frame = pd.DataFrame(
        {
            "municipality_code": code,
            "territory_status": category,
            "year_month": month,
            "event": event,
            "invalid_territory": ~valid,
            "invalid_onset": onset.isna(),
            "invalid_event": ~event.isin(COUNTS),
            "stream_event_mismatch": event.ne(expected_event),
            "outside_review_window": ~month.between(config.start_month, config.end_month),
        }
    )
    frame["accepted"] = ~frame[
        [
            "invalid_territory",
            "invalid_onset",
            "invalid_event",
            "stream_event_mismatch",
            "outside_review_window",
        ]
    ].any(axis=1)
    return frame


def build_review_calendar(
    catalog: pd.DataFrame,
    monthly: pd.DataFrame,
    config: CalendarWindow,
    located_rows: pd.DataFrame,
) -> pd.DataFrame:
    """Complete the fixed territorial calendar with epidemiological zeros only.

    Args:
        catalog: Territorial universe chosen before reviewing case density.
        monthly: Accepted monthly event counts.
        config: Explicit interval; no future-density admission filters.
        located_rows: All geographically and temporally assignable source rows,
            including rows whose event requires review.

    Returns:
        Unique municipality-month rows with separate absence indicators per stream.
    """
    months = pd.period_range(config.start_month, config.end_month, freq="M").astype(str)
    grid = catalog.merge(pd.DataFrame({"year_month": months}), how="cross")
    result = grid.merge(
        monthly, on=["municipality_code", "year_month"], how="left", validate="one_to_one"
    )
    result = result.merge(
        located_rows, on=["municipality_code", "year_month"], how="left", validate="one_to_one"
    )
    result["requires_record_review"] = False
    for column in COUNTS.values():
        result[column] = result[column].fillna(0).astype("int64")
        raw_column = f"{column}_source_rows"
        result[raw_column] = result[raw_column].fillna(0).astype("int64")
        result[f"{column}_has_rows"] = result[raw_column].gt(0)
        result[f"{column}_zero_from_absence"] = result[raw_column].eq(0)
        result["requires_record_review"] |= result[raw_column].gt(result[column])
    result["eligible_for_canonical_review"] = ~result["requires_record_review"]
    result["historical_territory_applicability"] = "UNVERIFIED"
    result["training_eligibility"] = "NOT_ASSESSED"
    if result.duplicated(["municipality_code", "year_month"]).any():
        raise ValueError("Repeated municipality-month")
    for column in COUNTS.values():
        if result[column].lt(0).any() or result[column].sum() != monthly[column].sum():
            raise ValueError("Notification counts were not conserved")
    return result.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)


def _increment(counter: Counter[Any], frame: pd.DataFrame, columns: list[str]) -> None:
    """Accumulate grouped counts across chunks."""
    for key, count in frame.groupby(columns, dropna=False).size().items():
        counter[key if isinstance(key, tuple) else (key,)] += int(count)


def _counter_frame(counter: Counter[Any], columns: list[str]) -> pd.DataFrame:
    """Convert a sorted counter to a reproducible aggregate table."""
    return pd.DataFrame(
        [(*key, value) for key, value in sorted(counter.items())],
        columns=[*columns, "notifications"],
    )


def _derive_tables(
    tables: dict[str, pd.DataFrame], catalog: pd.DataFrame, config: AnalysisConfig
) -> None:
    """Derive calendar, coverage denominators and admission-for-review summaries."""
    grouped = tables.pop("accepted_monthly")
    if grouped.empty:
        monthly = pd.DataFrame(columns=["municipality_code", "year_month", *COUNTS.values()])
    else:
        monthly = (
            grouped.pivot(
                index=["municipality_code", "year_month"], columns="event", values="notifications"
            )
            .reindex(columns=list(COUNTS))
            .fillna(0)
        )
        monthly = monthly.rename(columns=COUNTS).reset_index()
    located = (
        tables.pop("located_rows")
        .pivot(
            index=["municipality_code", "year_month"],
            columns="source_event",
            values="notifications",
        )
        .reindex(columns=list(COUNTS))
        .fillna(0)
        .rename(columns={event: f"{column}_source_rows" for event, column in COUNTS.items()})
        .reset_index()
    )
    calendar = build_review_calendar(catalog, monthly, config, located)
    accepted = tables["record_reconciliation"].query("accepted")["notifications"].sum()
    if calendar[list(COUNTS.values())].to_numpy().sum() != accepted:
        raise ValueError("Accepted notification reconciliation failed")
    total = tables["source_records"]["rows"].sum()
    if tables["record_reconciliation"]["notifications"].sum() != total:
        raise ValueError("Source rows were lost in reconciliation")
    territorial = tables["territorial_discrepancies"]
    summary = territorial.groupby(["source", "territory_status"], as_index=False)[
        "notifications"
    ].sum()
    summary["source_notifications"] = summary.groupby("source")["notifications"].transform("sum")
    summary["proportion_of_source"] = summary["notifications"] / summary["source_notifications"]
    tables["territorial_coverage"] = summary
    valid = territorial.loc[territorial["territory_status"].eq("valid")]
    tables["territorial_totals"] = pd.DataFrame(
        [
            {
                "observed_valid_municipalities": valid["municipality_code"].nunique(),
                "observed_valid_departments": valid["municipality_code"].str[:2].nunique(),
                "catalog_territories": len(catalog),
                "catalog_departments": catalog["department_code"].nunique(),
                "unresolved_notifications": int(
                    territorial.loc[
                        ~territorial["territory_status"].eq("valid"), "notifications"
                    ].sum()
                ),
            }
        ]
    )
    tables["municipality_month"] = calendar
    tables["municipality_eligibility"] = calendar.groupby("municipality_code", as_index=False).agg(
        review_months=("year_month", "size"),
        dengue_months_with_rows=(f"{COUNTS['210']}_has_rows", "sum"),
        severe_months_with_rows=(f"{COUNTS['220']}_has_rows", "sum"),
        eligible_review_months=("eligible_for_canonical_review", "sum"),
        months_requiring_record_review=("requires_record_review", "sum"),
    )
    eligibility = tables["municipality_eligibility"]
    eligibility["months_without_any_rows"] = (
        calendar.assign(absent=~calendar[[f"{c}_has_rows" for c in COUNTS.values()]].any(axis=1))
        .groupby("municipality_code")["absent"]
        .sum()
        .to_numpy()
    )
    eligibility["intermittent_notifications"] = eligibility["months_without_any_rows"].between(
        1, eligibility["review_months"] - 1
    )
    eligibility["eligible_for_canonical_review"] = eligibility["eligible_review_months"].gt(0)
    eligibility["training_eligibility"] = "NOT_ASSESSED"
    tables["period_eligibility"] = calendar.groupby("year_month", as_index=False)[
        list(COUNTS.values())
    ].sum()
    tables["period_eligibility"]["eligible_territories_for_review"] = (
        calendar.groupby("year_month")["eligible_for_canonical_review"].sum().to_numpy()
    )
    temporal = tables["temporal_coverage"]
    tables["annual_notifications"] = temporal.groupby(["source", "onset_year"], as_index=False)[
        "notifications"
    ].sum()
