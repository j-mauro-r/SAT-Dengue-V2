"""Validate schema, keys, monthly support and observed categories without repairs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationError, validate_predictors


def validate_roles(contract: dict[str, Any]) -> None:
    """Check that every panel column has exactly one role and X is isolated.

    Args:
        contract: Preparation contract.

    Raises:
        PreparationError: If role sets overlap or do not cover the schema.
    """
    roles = contract["roles"]
    names = [c["name"] for c in contract["schema"]]
    assigned = [
        name for role in ("keys", "predictors", "targets", "controls") for name in roles[role]
    ]
    excluded = set(roles["keys"] + roles["targets"] + roles["controls"])
    if (
        len(assigned) != len(set(assigned))
        or set(assigned) != set(names)
        or set(roles["excluded_predictors"]) != excluded
    ):
        raise PreparationError("Contract roles must partition the input schema")
    if set(roles["predictors"]) & excluded:
        raise PreparationError("Excluded columns cannot be predictors")
    # These are scientific boundaries, even if an edited allowlist includes them.
    unsafe = [
        c
        for c in roles["predictors"]
        if c.startswith(("y_", "target_", "history_", "p75_t")) or c == "total_notifications_count"
    ]
    if unsafe:
        raise PreparationError(f"Forbidden predictor columns: {unsafe}")
    validate_predictors(roles["predictors"], contract)


def validate_schema(panel: pd.DataFrame, contract: dict[str, Any]) -> None:
    """Validate exact columns, semantic dtypes and nullability.

    Args:
        panel: Input frame, never mutated.
        contract: Preparation schema.

    Raises:
        PreparationError: If columns, values or nullability violate the schema.
    """
    expected = {c["name"] for c in contract["schema"]}
    actual = set(panel.columns)
    if actual != expected or panel.columns.duplicated().any():
        raise PreparationError(
            f"Schema mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    if panel.empty:
        raise PreparationError("Empty panel")
    for field in contract["schema"]:
        name = field["name"]
        values = panel[name]
        if not field["nullable"] and values.isna().any():
            raise PreparationError(f"Non-nullable column: {name}")
        present = values.dropna()
        dtype = field["dtype"].lower()
        if dtype == "bool":
            if not all(isinstance(v, (bool, np.bool_)) for v in present):
                raise PreparationError(f"Expected booleans: {name}")
        elif dtype in ("float64", "int64"):
            if (
                not pd.api.types.is_numeric_dtype(values)
                or pd.api.types.is_bool_dtype(values)
                or not np.isfinite(present.astype(float)).all()
            ):
                raise PreparationError(f"Expected finite numeric values: {name}")
            if dtype == "int64" and (present % 1 != 0).any():
                raise PreparationError(f"Expected integral values: {name}")
        elif not all(isinstance(v, str) for v in present):
            raise PreparationError(f"Expected strings: {name}")


def validate_panel(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    """Validate panel support and return aggregate diagnostics, preserving all rows.

    Args:
        panel: Existing municipality-month panel.
        contract: Preparation contract.
        coverage: Construction manifest coverage bounds and municipality count.

    Returns:
        Aggregate coverage and missingness diagnostics without source records.

    Raises:
        PreparationError: If any blocking input invariant fails.
    """
    validate_roles(contract)
    validate_schema(panel, contract)
    periods, expected, covered = validate_monthly_support(panel, coverage)
    for column, allowed in contract["categories"].items():
        if not panel[column].dropna().isin(allowed).all():
            raise PreparationError(f"Invalid category: {column}")
    validate_counts(panel, covered)
    validate_climate_coverage(panel, periods, coverage)
    validate_target_metadata(panel, periods)
    return {
        "rows": len(panel),
        "municipalities": panel["municipality_code"].nunique(),
        "start": str(expected[0]),
        "end": str(expected[-1]),
        "covered_rows": int(panel["in_epi_coverage"].sum()),
        "missing_by_column": {c: int(n) for c, n in panel.isna().sum().items()},
        "operational_historical_availability": "UNPROVEN; retrospective consolidated data",
    }


def validate_monthly_support(
    panel: pd.DataFrame, coverage: dict[str, Any]
) -> tuple[pd.PeriodIndex, pd.PeriodIndex, Any]:
    """Validate keys and complete monthly support for every municipality.

    Args:
        panel: Existing panel, never mutated.
        coverage: Upstream manifest coverage bounds.

    Returns:
        Monthly index, expected calendar and coverage mask.

    Raises:
        PreparationError: If input invariants fail.
    """
    keys = ["municipality_code", "year_month"]
    if panel.duplicated(keys).any():
        raise PreparationError("Duplicate municipality-month keys")
    if not panel["municipality_code"].str.fullmatch(r"(50|73)\d{3}").all():
        raise PreparationError("Invalid municipality codes")
    if not panel["department_code"].eq(panel["municipality_code"].str[:2]).all():
        raise PreparationError("Department/municipality mismatch")
    if not panel["year_month"].str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise PreparationError("Invalid monthly keys")
    expected = pd.period_range(coverage["panel_month_start"], coverage["panel_month_end"], freq="M")
    if panel["municipality_code"].nunique() != coverage["scope_municipalities"]:
        raise PreparationError("Municipality coverage differs from manifest")
    for _, group in panel.groupby("municipality_code"):
        actual = pd.PeriodIndex(group["year_month"], freq="M").sort_values()
        if not actual.equals(expected):
            raise PreparationError("Discontinuous monthly support or missing boundary months")
    periods = pd.PeriodIndex(panel["year_month"], freq="M")
    covered = (periods >= pd.Period(coverage["epi_coverage_start_month"], freq="M")) & (
        periods <= pd.Period(coverage["epi_coverage_end_month"], freq="M")
    )
    if not panel["in_epi_coverage"].eq(covered).all():
        raise PreparationError("Epidemiological coverage contradicts manifest")
    return periods, expected, covered


def validate_counts(panel: pd.DataFrame, covered: Any) -> None:
    """Validate separate counts, reconciliation and approved zero statuses.

    Args:
        panel: Existing panel, never mutated.
        covered: Manifest-backed epidemiological coverage mask.

    Raises:
        PreparationError: If input invariants fail.
    """
    counts = ["dengue_notifications_count", "dengue_grave_notifications_count"]
    for column in counts + ["total_notifications_count"]:
        s = panel[column]
        if ((s < 0) | (s % 1 != 0)).any():
            raise PreparationError(f"Invalid notification counts: {column}")
    total = panel[counts].sum(axis=1)
    if not panel["total_notifications_count"].eq(total).all():
        raise PreparationError("Count reconciliation mismatch")
    statuses = np.where(
        covered,
        np.where(total.eq(0), "zero_in_coverage", "records_present"),
        "outside_epi_coverage_missing",
    )
    if not panel["epi_count_status"].eq(statuses).all():
        raise PreparationError("Count status contradicts coverage/counts")


def validate_climate_coverage(
    panel: pd.DataFrame, periods: pd.PeriodIndex, coverage: dict[str, Any]
) -> None:
    """Validate monthly climate aggregates and available-day coverage.

    Args:
        panel: Existing panel, never mutated.
        coverage: Upstream manifest coverage bounds.
        periods: Monthly index matching panel rows.

    Raises:
        PreparationError: If input invariants fail.
    """
    climate_covered = (periods >= pd.Period(coverage["climate_coverage_start_month"], freq="M")) & (
        periods <= pd.Period(coverage["climate_coverage_end_month"], freq="M")
    )
    if not panel["expected_days_in_month"].notna().eq(climate_covered).all():
        raise PreparationError("Climate coverage contradicts manifest")
    days = pd.Series(periods.days_in_month, index=panel.index)
    if (
        not panel["expected_days_in_month"]
        .dropna()
        .eq(days[panel["expected_days_in_month"].notna()])
        .all()
    ):
        raise PreparationError("Invalid expected monthly climate days")
    for column in [c for c in panel if c.endswith("_valid_days")] + ["climate_days_observed"]:
        s = panel[column]
        if ((s < 0) | (s > days) | (s % 1 != 0)).any():
            raise PreparationError(f"Invalid climate day coverage: {column}")
        if column.endswith("_valid_days"):
            value = panel[column.removesuffix("_valid_days")]
            if (value.notna() & ~s.eq(days).fillna(False)).any() or (
                value.isna() & s.eq(days)
            ).any():
                raise PreparationError(f"Incomplete climate aggregate: {column}")


def validate_target_metadata(panel: pd.DataFrame, periods: pd.PeriodIndex) -> None:
    """Validate horizon calendars and existing label/evaluability metadata.

    Args:
        panel: Existing panel, never mutated.
        periods: Monthly index matching panel rows.

    Raises:
        PreparationError: If input invariants fail.
    """
    for h in (1, 2):
        target = pd.Series((periods + h).astype(str), index=panel.index)
        if not panel[f"target_period_t{h}"].eq(target).all():
            raise PreparationError(f"Invalid target calendar: t{h}")
        y = panel[f"y_t{h}"]
        evaluable = panel[f"y_evaluable_t{h}"]
        if (
            not y.dropna().isin([0, 1]).all()
            or not y.notna().eq(evaluable).all()
            or not panel[f"y_status_t{h}"].eq("evaluable").eq(evaluable).all()
            or not panel[f"p75_t{h}"].notna().eq(evaluable).all()
        ):
            raise PreparationError(f"Inconsistent label/evaluability: t{h}")
