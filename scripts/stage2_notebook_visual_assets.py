"""Utilities for Stage 2 notebook visual and tabular assets.

This module centralizes deterministic data preparation used by
notebooks/03_consolidated_dataset_pipeline.ipynb to produce:

1) Missingness and continuity table.
2) Municipality seasonality heatmap inputs.
3) Lag-association heatmap inputs for Y(T+1/T+2).
4) Temporal-validation audit table.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


@dataclass(frozen=True)
class VariableSpec:
    """Specification for a variable included in missingness auditing.

    Args:
        name: Column name in the panel.
        unit: Human-readable measurement unit.
        eligible_rule: Eligibility denominator rule.
            Accepted values: ``epi_coverage``, ``climate_expected_days``,
            ``y_evaluable_t1``, ``y_evaluable_t2``, ``all_rows``.
    """

    name: str
    unit: str
    eligible_rule: str


@dataclass(frozen=True)
class PredictorSpec:
    """Specification for lag-association predictors.

    Args:
        family: Visual group name used in heatmap rows.
        base_column: Source column from which lag values are built.
        display_name: Human-readable predictor label.
        lags: Ordered lag months to evaluate.
    """

    family: str
    base_column: str
    display_name: str
    lags: tuple[int, ...]


def build_month_calendar(start_period: str, end_period: str) -> pd.PeriodIndex:
    """Build an explicit monthly calendar.

    Args:
        start_period: First period in ``YYYY-MM`` format.
        end_period: Last period in ``YYYY-MM`` format.

    Returns:
        Monthly ``PeriodIndex`` including both boundaries.
    """

    start = pd.Period(start_period, freq="M")
    end = pd.Period(end_period, freq="M")
    if end < start:
        raise ValueError("end_period must be equal to or after start_period")
    return pd.period_range(start=start, end=end, freq="M")


def longest_true_run(series: pd.Series) -> tuple[int, str | None, str | None]:
    """Return the longest run of ``True`` values in monthly order.

    Args:
        series: Boolean series indexed by monthly ``PeriodIndex``.

    Returns:
        Tuple with run length, start period, and end period.
        Period values are returned as ``YYYY-MM`` strings.
    """

    if not isinstance(series.index, pd.PeriodIndex):
        raise TypeError("series index must be PeriodIndex")

    best_len = 0
    best_start: pd.Period | None = None
    best_end: pd.Period | None = None

    current_len = 0
    current_start: pd.Period | None = None

    for period, flag in series.items():
        if bool(flag):
            if current_len == 0:
                current_start = period
            current_len += 1
            if current_len > best_len:
                best_len = current_len
                best_start = current_start
                best_end = period
        else:
            current_len = 0
            current_start = None

    if best_len == 0:
        return 0, None, None
    return best_len, str(best_start), str(best_end)


def _eligible_mask(panel: pd.DataFrame, spec: VariableSpec) -> pd.Series:
    """Build eligibility mask for a variable specification.

    Args:
        panel: Municipality-month panel.
        spec: Variable specification.

    Returns:
        Boolean mask with eligible rows.
    """

    if spec.eligible_rule == "epi_coverage":
        return panel["in_epi_coverage"].fillna(False).astype(bool)
    if spec.eligible_rule == "climate_expected_days":
        return panel["in_epi_coverage"].fillna(False).astype(bool)
    if spec.eligible_rule == "y_evaluable_t1":
        return panel["y_evaluable_t1"].fillna(False).astype(bool)
    if spec.eligible_rule == "y_evaluable_t2":
        return panel["y_evaluable_t2"].fillna(False).astype(bool)
    if spec.eligible_rule == "all_rows":
        return pd.Series(True, index=panel.index)
    raise ValueError(f"Unsupported eligible_rule: {spec.eligible_rule}")


def build_missingness_inventory(
    panel_development: pd.DataFrame,
    specs: list[VariableSpec],
    top_k: int = 10,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Build full and compact missingness-continuity inventories.

    The function computes missingness on an explicit municipality-month calendar
    and separates eligible missingness from out-of-coverage and out-of-panel
    months.

    Args:
        panel_development: Development split with at least municipality and
            month identifiers.
        specs: Variables to audit.
        top_k: Number of rows to expose in the compact table.

    Returns:
        Tuple with:
        1) full inventory dataframe,
        2) compact deterministic selection,
        3) denominator note dictionary.
    """

    required = {
        "municipality_code",
        "year_month",
        "in_epi_coverage",
        "expected_days_in_month",
        "epi_count_status",
    }
    missing = sorted(required - set(panel_development.columns))
    if missing:
        raise ValueError(f"panel_development missing required columns: {missing}")

    work = panel_development.copy()
    work["municipality_code"] = work["municipality_code"].astype(str).str.zfill(5)
    work["year_period"] = pd.PeriodIndex(work["year_month"].astype(str), freq="M")

    calendar = build_month_calendar(
        str(work["year_month"].min()),
        str(work["year_month"].max()),
    )
    municipalities = sorted(work["municipality_code"].astype(str).unique())

    calendar_frame = pd.MultiIndex.from_product(
        [municipalities, calendar],
        names=["municipality_code", "year_period"],
    ).to_frame(index=False)

    merged = calendar_frame.merge(
        work,
        how="left",
        on=["municipality_code", "year_period"],
        validate="one_to_one",
    )

    merged["is_in_panel"] = merged["year_month"].notna()
    merged["year_month"] = merged["year_period"].astype(str)

    rows: list[dict[str, object]] = []
    variable_denominators: dict[str, dict[str, object]] = {}
    denominator_note: dict[str, object] = {
        "development_start": str(calendar.min()),
        "development_end": str(calendar.max()),
        "municipality_count": len(municipalities),
        "calendar_months_per_municipality": len(calendar),
        "calendar_rows_total": int(len(calendar_frame)),
        "variable_denominators": variable_denominators,
    }

    for spec in specs:
        if spec.name not in merged.columns:
            continue

        eligible = _eligible_mask(merged, spec) & merged["is_in_panel"]
        value_missing = merged[spec.name].isna()
        eligible_missing = eligible & value_missing

        outside_panel = ~merged["is_in_panel"]
        out_of_coverage = merged["is_in_panel"] & ~_eligible_mask(merged, spec)

        expected_eligible = int(eligible.sum())
        missing_count = int(eligible_missing.sum())
        missing_pct = (
            float(missing_count / expected_eligible) if expected_eligible else float("nan")
        )

        affected_municipalities = int(
            merged.loc[eligible_missing, "municipality_code"].astype(str).nunique()
        )

        best_gap_len = 0
        best_gap_code: str | None = None
        best_gap_start: str | None = None
        best_gap_end: str | None = None

        for municipality, group in merged.groupby("municipality_code", sort=True):
            run_series = group.set_index("year_period")["municipality_code"].notna().astype(bool)
            # Replace with the specific eligible-missing run mask.
            run_series = group.set_index("year_period")[spec.name].isna() & (
                _eligible_mask(group, spec).to_numpy(dtype=bool)
                & group["is_in_panel"].to_numpy(dtype=bool)
            )
            gap_len, gap_start, gap_end = longest_true_run(run_series)
            if gap_len > best_gap_len:
                best_gap_len = gap_len
                best_gap_code = str(municipality)
                best_gap_start = gap_start
                best_gap_end = gap_end

        if spec.name.startswith("y_"):
            absence_type = "non_evaluable_distinguished_from_predictor_missingness"
        elif missing_count == 0:
            absence_type = "no_missing_in_eligible_scope"
        elif int(out_of_coverage.sum()) > 0:
            absence_type = "eligible_missing_and_out_of_coverage_separated"
        else:
            absence_type = "eligible_missing_in_coverage"

        impact_score = float(best_gap_len) + float(missing_pct if pd.notna(missing_pct) else 0.0)

        variable_denominators[spec.name] = {
            "expected_eligible_rows": expected_eligible,
            "eligible_rule": spec.eligible_rule,
            "outside_panel_rows": int(outside_panel.sum()),
            "out_of_coverage_rows": int(out_of_coverage.sum()),
        }

        rows.append(
            {
                "variable": spec.name,
                "unit": spec.unit,
                "expected_eligible_rows": expected_eligible,
                "missing_rows": missing_count,
                "missing_pct": missing_pct,
                "affected_municipalities": affected_municipalities,
                "longest_missing_gap_months": int(best_gap_len),
                "longest_gap_municipality": best_gap_code,
                "longest_gap_period_start": best_gap_start,
                "longest_gap_period_end": best_gap_end,
                "absence_type": absence_type,
                "outside_panel_rows": int(outside_panel.sum()),
                "out_of_coverage_rows": int(out_of_coverage.sum()),
                "impact_score": impact_score,
            }
        )

    inventory = pd.DataFrame(rows).sort_values(
        ["impact_score", "missing_rows", "variable"],
        ascending=[False, False, True],
    )
    compact = inventory.head(top_k).reset_index(drop=True)
    return inventory.reset_index(drop=True), compact, denominator_note


def compute_municipality_seasonality(
    panel_development: pd.DataFrame,
    value_column: str = "dengue_notifications_count",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Compute raw and normalized municipality seasonality profiles.

    Args:
        panel_development: Development split panel.
        value_column: Main epidemiological count column.

    Returns:
        Tuple with normalized matrix (rows=municipalities, cols=month 1..12),
        raw long profile, support long table, and metadata.
    """

    required = {
        "municipality_code",
        "municipality_name",
        "department_code",
        "year_month",
        value_column,
    }
    missing = sorted(required - set(panel_development.columns))
    if missing:
        raise ValueError(f"panel_development missing required columns: {missing}")

    frame = panel_development.copy()
    frame["year_month"] = frame["year_month"].astype(str)
    frame["year"] = frame["year_month"].str.slice(0, 4).astype(int)
    frame["calendar_month"] = frame["year_month"].str.slice(5, 7).astype(int)
    frame[value_column] = pd.to_numeric(frame[value_column], errors="coerce")

    raw_profile = (
        frame.groupby(
            ["department_code", "municipality_code", "municipality_name", "calendar_month"],
            as_index=False,
        )[value_column]
        .mean()
        .sort_values(["department_code", "municipality_code", "calendar_month"])
    )

    support = (
        frame.dropna(subset=[value_column])
        .groupby(
            ["department_code", "municipality_code", "municipality_name", "calendar_month"],
            as_index=False,
        )
        .agg(
            years_with_data=("year", "nunique"),
            month_observations=(value_column, "size"),
        )
        .sort_values(["department_code", "municipality_code", "calendar_month"])
    )

    pivot = raw_profile.pivot_table(
        index=["department_code", "municipality_code", "municipality_name"],
        columns="calendar_month",
        values=value_column,
        aggfunc="mean",
    )
    pivot = pivot.reindex(columns=list(range(1, 13)))

    normalized = pivot.copy()
    normalization_mode: dict[str, str] = {}

    for idx in normalized.index:
        values = normalized.loc[idx]
        finite = values.dropna()
        label = f"{idx[1]} | {idx[2]}"

        if finite.empty:
            normalization_mode[label] = "all_missing"
            continue

        min_value = float(finite.min())
        max_value = float(finite.max())

        if max_value == min_value:
            if max_value == 0.0:
                normalized.loc[idx, finite.index] = 0.0
                normalization_mode[label] = "constant_zero"
            else:
                normalized.loc[idx, finite.index] = 0.5
                normalization_mode[label] = "constant_nonzero"
        else:
            normalized.loc[idx, finite.index] = (finite - min_value) / (max_value - min_value)
            normalization_mode[label] = "minmax"

    normalized.index = [f"{code} | {name}" for _, code, name in normalized.index]

    meta = {
        "value_column": value_column,
        "normalization": "within_municipality_minmax_with_constant_handling",
        "constant_nonzero_value": 0.5,
        "month_order": list(range(1, 13)),
        "municipality_count": int(normalized.shape[0]),
        "normalization_mode_counts": pd.Series(normalization_mode).value_counts().to_dict(),
    }

    return normalized, raw_profile, support, meta


def add_consecutive_lag(
    frame: pd.DataFrame,
    value_column: str,
    lag_months: int,
) -> pd.Series:
    """Create municipality-wise lag preserving exact month adjacency.

    Args:
        frame: Municipality-month panel.
        value_column: Column to lag.
        lag_months: Positive lag offset.

    Returns:
        Lagged series with NaN for non-consecutive month gaps.
    """

    if lag_months <= 0:
        raise ValueError("lag_months must be positive")

    periods = pd.PeriodIndex(frame["year_month"].astype(str), freq="M")
    lagged_values = frame.groupby("municipality_code", sort=False)[value_column].shift(lag_months)
    lagged_periods = (
        periods.to_series(index=frame.index)
        .groupby(frame["municipality_code"], sort=False)
        .shift(lag_months)
    )
    expected = periods - lag_months
    valid = lagged_periods == expected
    return lagged_values.where(valid)


def point_biserial_correlation(x: pd.Series, y: pd.Series) -> float:
    """Compute point-biserial correlation via Pearson on binary-coded targets.

    Args:
        x: Numeric predictor series.
        y: Binary target series coded as 0/1.

    Returns:
        Correlation coefficient.

    Raises:
        ValueError: When support is invalid (constant values or single class).
    """

    clean = pd.DataFrame(
        {"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}
    ).dropna()
    if len(clean) < 2:
        raise ValueError("insufficient_rows")
    if clean["x"].nunique() < 2:
        raise ValueError("constant_predictor")
    if clean["y"].nunique() < 2:
        raise ValueError("single_target_class")

    corr = clean["x"].corr(clean["y"], method="pearson")
    if corr is None or pd.isna(corr):
        raise ValueError("invalid_correlation")
    return float(corr)


def compute_lag_association_summary(
    panel_development: pd.DataFrame,
    predictors: list[PredictorSpec],
    min_rows_per_municipality: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Compute municipality-adjusted lag associations with Y(T+1/T+2).

    Associations are estimated within municipality, then aggregated across
    municipalities with an unweighted median to avoid implicit weighting by
    municipality size.

    Args:
        panel_development: Development split panel.
        predictors: Predictor specification list.
        min_rows_per_municipality: Minimum rows for municipality-level estimate.

    Returns:
        Aggregate table, municipality-level detail table, and metadata.
    """

    frame = (
        panel_development.copy()
        .sort_values(["municipality_code", "year_month"])
        .reset_index(drop=True)
    )

    for predictor in predictors:
        for lag in predictor.lags:
            lag_column = f"{predictor.base_column}__lag_{lag}"
            frame[lag_column] = add_consecutive_lag(frame, predictor.base_column, lag)

    detail_rows: list[dict[str, object]] = []
    aggregate_rows: list[dict[str, object]] = []

    for horizon in (1, 2):
        y_column = f"y_t{horizon}"
        evaluable_column = f"y_evaluable_t{horizon}"

        scoped = frame[frame[evaluable_column].fillna(False)].copy()
        municipality_total = int(scoped["municipality_code"].nunique())

        for predictor in predictors:
            for lag in predictor.lags:
                lag_column = f"{predictor.base_column}__lag_{lag}"
                eval_corrs: list[float] = []
                rows_used_total = 0
                reason_counts: dict[str, int] = {
                    "insufficient_rows": 0,
                    "constant_predictor": 0,
                    "single_target_class": 0,
                    "invalid_correlation": 0,
                }

                for municipality, group in scoped.groupby("municipality_code", sort=True):
                    sample = group[[lag_column, y_column]].dropna()
                    if len(sample) < min_rows_per_municipality:
                        reason_counts["insufficient_rows"] += 1
                        detail_rows.append(
                            {
                                "horizon": f"t{horizon}",
                                "family": predictor.family,
                                "predictor": predictor.display_name,
                                "lag_months": lag,
                                "municipality_code": str(municipality),
                                "rows_used": int(len(sample)),
                                "status": "not_evaluable",
                                "reason": "insufficient_rows",
                                "correlation": np.nan,
                            }
                        )
                        continue

                    try:
                        corr = point_biserial_correlation(sample[lag_column], sample[y_column])
                    except ValueError as exc:
                        reason = str(exc)
                        reason_counts[reason] = reason_counts.get(reason, 0) + 1
                        detail_rows.append(
                            {
                                "horizon": f"t{horizon}",
                                "family": predictor.family,
                                "predictor": predictor.display_name,
                                "lag_months": lag,
                                "municipality_code": str(municipality),
                                "rows_used": int(len(sample)),
                                "status": "not_evaluable",
                                "reason": reason,
                                "correlation": np.nan,
                            }
                        )
                        continue

                    rows_used_total += int(len(sample))
                    eval_corrs.append(corr)
                    detail_rows.append(
                        {
                            "horizon": f"t{horizon}",
                            "family": predictor.family,
                            "predictor": predictor.display_name,
                            "lag_months": lag,
                            "municipality_code": str(municipality),
                            "rows_used": int(len(sample)),
                            "status": "evaluable",
                            "reason": "ok",
                            "correlation": corr,
                        }
                    )

                municipalities_evaluable = len(eval_corrs)
                aggregate_rows.append(
                    {
                        "horizon": f"t{horizon}",
                        "family": predictor.family,
                        "predictor": predictor.display_name,
                        "lag_months": lag,
                        "municipalities_total": municipality_total,
                        "municipalities_evaluable": municipalities_evaluable,
                        "rows_used_total": rows_used_total,
                        "association_point_biserial_median": (
                            float(np.median(eval_corrs)) if eval_corrs else np.nan
                        ),
                        "status": "evaluable" if eval_corrs else "not_evaluable",
                        "non_evaluable_counts": json.dumps(reason_counts, sort_keys=True),
                    }
                )

    aggregate = pd.DataFrame(aggregate_rows)
    detail = pd.DataFrame(detail_rows)
    meta = {
        "method": "point_biserial_within_municipality_unweighted_median",
        "min_rows_per_municipality": min_rows_per_municipality,
        "interpretation_limit": "descriptive_association_not_causality_or_model_selection",
    }
    return aggregate, detail, meta


def add_months(period: str, months: int) -> str:
    """Shift a ``YYYY-MM`` period by an integer number of months.

    Args:
        period: Base period.
        months: Signed month shift.

    Returns:
        Shifted period in ``YYYY-MM`` format.
    """

    return str(pd.Period(period, freq="M") + months)


def build_temporal_validation_audit(
    panel_development: pd.DataFrame,
    panel_reserved: pd.DataFrame,
    window_train_endpoints: list[str],
    predictor_columns_used: list[str],
) -> pd.DataFrame:
    """Build executable temporal protocol audit by window.

    Args:
        panel_development: Development split panel.
        panel_reserved: Reserved final-block split panel.
        window_train_endpoints: Train-end checkpoints.
        predictor_columns_used: Predictor columns used in this scope.

    Returns:
        Audit dataframe with one row per temporal window.
    """

    rows: list[dict[str, object]] = []
    reserved_start = str(panel_reserved["year_month"].min()) if not panel_reserved.empty else None

    for train_end in window_train_endpoints:
        validation_start = add_months(train_end, 1)
        validation_end = add_months(train_end, 6)

        train_scope = panel_development[panel_development["year_month"] <= train_end].copy()
        validation_scope = panel_development[
            panel_development["year_month"].between(validation_start, validation_end)
        ].copy()

        train_before_validation = train_end < validation_start

        obs_failures = []
        for horizon in (1, 2):
            target_column = f"target_period_t{horizon}"
            evaluable_column = f"y_evaluable_t{horizon}"
            scoped = train_scope[train_scope[evaluable_column].fillna(False)]
            if scoped.empty:
                continue
            violations = scoped[target_column].astype(str) > train_end
            if bool(violations.any()):
                obs_failures.append(f"t{horizon}:{int(violations.sum())}")
        labels_observable = len(obs_failures) == 0

        both_eval = train_scope[
            train_scope["y_evaluable_t1"].fillna(False)
            & train_scope["y_evaluable_t2"].fillna(False)
        ]
        if both_eval.empty:
            horizon_separation_ok = False
            horizon_reason = "no_rows_with_both_horizons_evaluable"
        else:
            expected_t2 = both_eval["target_period_t1"].astype(str).map(lambda v: add_months(v, 1))
            horizon_separation_ok = bool(
                both_eval["target_period_t2"].astype(str).equals(expected_t2.astype(str))
            )
            horizon_reason = "ok" if horizon_separation_ok else "t1_to_t2_offset_mismatch"

        leakage_columns = [
            column
            for column in predictor_columns_used
            if column.startswith("y_") or column.startswith("target_period_")
        ]
        no_future_labels_in_x = len(leakage_columns) == 0

        transformation_status = "NOT_EXECUTED"
        transformation_reason = "no_fitted_transformer_artifact_in_this_scope"

        reserved_excluded = True
        reserved_reason = "ok"
        if reserved_start is not None and validation_end >= reserved_start:
            reserved_excluded = False
            reserved_reason = "validation_overlaps_reserved_block"

        train_unique_start = train_scope.groupby("municipality_code")["year_month"].min().nunique()
        train_unique_end = train_scope.groupby("municipality_code")["year_month"].max().nunique()
        val_unique_start = (
            validation_scope.groupby("municipality_code")["year_month"].min().nunique()
        )
        val_unique_end = validation_scope.groupby("municipality_code")["year_month"].max().nunique()
        shared_cutoffs = (
            train_unique_start == 1
            and train_unique_end == 1
            and val_unique_start <= 1
            and val_unique_end <= 1
        )

        temporal_ok = all(
            [
                train_before_validation,
                labels_observable,
                horizon_separation_ok,
                no_future_labels_in_x,
                reserved_excluded,
                shared_cutoffs,
            ]
        )

        reasons = []
        if not train_before_validation:
            reasons.append("train_not_before_validation")
        if not labels_observable:
            reasons.append(f"labels_not_observable_at_cutoff:{'|'.join(obs_failures)}")
        if not horizon_separation_ok:
            reasons.append(horizon_reason)
        if not no_future_labels_in_x:
            reasons.append(f"leakage_columns:{'|'.join(leakage_columns)}")
        if not reserved_excluded:
            reasons.append(reserved_reason)
        if not shared_cutoffs:
            reasons.append("municipality_cutoff_inconsistency")

        rows.append(
            {
                "window_id": f"window_until_{train_end}",
                "horizon": "t1_and_t2",
                "train_start": str(train_scope["year_month"].min())
                if not train_scope.empty
                else None,
                "train_end": train_end,
                "validation_start": validation_start,
                "validation_end": validation_end,
                "last_train_target_period_t1": add_months(train_end, 1),
                "last_train_target_period_t2": add_months(train_end, 2),
                "train_rows": int(len(train_scope)),
                "train_municipalities": int(train_scope["municipality_code"].nunique()),
                "validation_rows": int(len(validation_scope)),
                "validation_municipalities": int(validation_scope["municipality_code"].nunique()),
                "check_train_before_validation": "PASS" if train_before_validation else "FAIL",
                "check_labels_observable_at_cutoff": "PASS" if labels_observable else "FAIL",
                "check_horizon_separation": "PASS" if horizon_separation_ok else "FAIL",
                "check_no_future_labels_in_x": "PASS" if no_future_labels_in_x else "FAIL",
                "check_transform_fit_train_only": transformation_status,
                "check_reserved_block_excluded": "PASS" if reserved_excluded else "FAIL",
                "check_shared_cutoffs_by_municipality": "PASS" if shared_cutoffs else "FAIL",
                "temporal_validation_result": "PASS" if temporal_ok else "FAIL",
                "reason_if_not_pass": "ok" if temporal_ok else "; ".join(reasons),
                "transform_note": transformation_reason,
            }
        )

    return pd.DataFrame(rows)


def assert_notebook_code_only(notebook_path: Path) -> dict[str, object]:
    """Validate that notebook cells are code-only.

    Args:
        notebook_path: Notebook path.

    Returns:
        Summary dictionary with counts and offending cell ids.
    """

    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = payload.get("cells", [])
    non_code = [
        {
            "id": cell.get("id"),
            "cell_type": cell.get("cell_type"),
        }
        for cell in cells
        if cell.get("cell_type") != "code"
    ]
    return {
        "cell_count": len(cells),
        "code_only": len(non_code) == 0,
        "non_code_cells": non_code,
    }
