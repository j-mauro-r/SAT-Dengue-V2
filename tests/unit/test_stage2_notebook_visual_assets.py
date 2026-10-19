from __future__ import annotations

import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

from scripts.stage2_notebook_visual_assets import (
    PredictorSpec,
    VariableSpec,
    add_consecutive_lag,
    assert_notebook_code_only,
    build_missingness_inventory,
    build_month_calendar,
    build_temporal_validation_audit,
    compute_lag_association_summary,
    compute_municipality_seasonality,
    longest_true_run,
    point_biserial_correlation,
)


def test_build_month_calendar_and_longest_true_run() -> None:
    calendar = build_month_calendar("2024-01", "2024-04")
    assert [str(value) for value in calendar] == ["2024-01", "2024-02", "2024-03", "2024-04"]

    flags = pd.Series(
        [True, False, True, True],
        index=calendar,
    )
    length, start, end = longest_true_run(flags)
    assert length == 2
    assert start == "2024-03"
    assert end == "2024-04"


def test_missingness_inventory_distinguishes_zero_missing_and_calendar_gaps() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50001", "50002", "50002", "50002", "50002"],
            "year_month": [
                "2024-01",
                "2024-02",
                "2024-04",
                "2024-01",
                "2024-02",
                "2024-03",
                "2024-04",
            ],
            "in_epi_coverage": [True] * 7,
            "expected_days_in_month": [31, 29, 30, 31, 29, 31, 30],
            "epi_count_status": [
                "zero_in_coverage",
                "records_present",
                "records_present",
                "records_present",
                "zero_in_coverage",
                "records_present",
                "records_present",
            ],
            "dengue_notifications_count": [0.0, None, 2.0, 1.0, 0.0, None, None],
            "rain_mm_month_sum": [10.0, None, 30.0, 5.0, 7.0, 8.0, None],
            "y_evaluable_t1": [True, True, True, True, True, False, False],
            "y_evaluable_t2": [True, True, True, True, True, False, False],
            "y_t1": [0.0, None, 1.0, 1.0, 0.0, None, None],
            "y_t2": [0.0, None, 1.0, 1.0, 0.0, None, None],
        }
    )

    specs = [
        VariableSpec("dengue_notifications_count", "cases", "epi_coverage"),
        VariableSpec("rain_mm_month_sum", "mm", "climate_expected_days"),
        VariableSpec("y_t1", "binary", "y_evaluable_t1"),
    ]

    full_inventory, compact, note = build_missingness_inventory(panel, specs, top_k=2)

    dengue_row = full_inventory.loc[
        full_inventory["variable"] == "dengue_notifications_count"
    ].iloc[0]
    assert int(dengue_row["expected_eligible_rows"]) == 7
    assert int(dengue_row["missing_rows"]) == 3
    assert int(dengue_row["outside_panel_rows"]) == 1
    assert int(dengue_row["longest_missing_gap_months"]) == 2

    y_row = full_inventory.loc[full_inventory["variable"] == "y_t1"].iloc[0]
    assert int(y_row["expected_eligible_rows"]) == 5
    assert int(y_row["missing_rows"]) == 1
    assert y_row["absence_type"] == "non_evaluable_distinguished_from_predictor_missingness"

    assert len(compact) == 2
    assert note["municipality_count"] == 2


def test_compute_municipality_seasonality_handles_constant_and_zero_profiles() -> None:
    rows = []
    for month in range(1, 13):
        ym = f"2024-{month:02d}"
        rows.append(
            {
                "department_code": "50",
                "municipality_code": "50001",
                "municipality_name": "A",
                "year_month": ym,
                "dengue_notifications_count": 0.0,
            }
        )
        rows.append(
            {
                "department_code": "50",
                "municipality_code": "50002",
                "municipality_name": "B",
                "year_month": ym,
                "dengue_notifications_count": 5.0,
            }
        )
        rows.append(
            {
                "department_code": "73",
                "municipality_code": "73001",
                "municipality_name": "C",
                "year_month": ym,
                "dengue_notifications_count": float(month),
            }
        )

    panel = pd.DataFrame(rows)
    normalized, raw_profile, support, meta = compute_municipality_seasonality(panel)

    assert normalized.shape[1] == 12
    assert list(normalized.columns) == list(range(1, 13))
    assert normalized.loc["50001 | A"].dropna().eq(0.0).all()
    assert normalized.loc["50002 | B"].dropna().eq(0.5).all()
    assert float(normalized.loc["73001 | C", 1]) == 0.0
    assert float(normalized.loc["73001 | C", 12]) == 1.0
    assert len(raw_profile) == 36
    assert len(support) == 36
    assert meta["municipality_count"] == 3


def test_add_consecutive_lag_respects_calendar_gaps() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50001"],
            "year_month": ["2024-01", "2024-03", "2024-04"],
            "value": [1.0, 2.0, 3.0],
        }
    )

    lagged = add_consecutive_lag(frame, "value", lag_months=1)
    assert pd.isna(lagged.iloc[1])
    assert lagged.iloc[2] == 2.0


def test_point_biserial_rejects_invalid_support() -> None:
    x_constant = pd.Series([1.0, 1.0, 1.0])
    y_binary = pd.Series([0, 1, 0])
    try:
        point_biserial_correlation(x_constant, y_binary)
    except ValueError as exc:
        assert str(exc) == "constant_predictor"
    else:
        raise AssertionError("Expected constant_predictor ValueError")


def test_compute_lag_association_marks_non_evaluable_groups() -> None:
    months = pd.period_range("2022-01", "2023-12", freq="M")
    rows = []
    for i, period in enumerate(months):
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": str(period),
                "dengue_notifications_count": float(i + 1),
                "rain_mm_month_sum": float((i % 5) + 1),
                "y_evaluable_t1": True,
                "y_evaluable_t2": True,
                "y_t1": int(i % 2 == 0),
                "y_t2": int(i % 3 == 0),
            }
        )
        rows.append(
            {
                "municipality_code": "50002",
                "year_month": str(period),
                "dengue_notifications_count": 10.0,
                "rain_mm_month_sum": 2.0,
                "y_evaluable_t1": True,
                "y_evaluable_t2": True,
                "y_t1": int(i % 2 == 0),
                "y_t2": int(i % 3 == 0),
            }
        )

    panel = pd.DataFrame(rows)
    predictors = [
        PredictorSpec("epi_history", "dengue_notifications_count", "dengue", (1,)),
    ]

    aggregate, detail, _meta = compute_lag_association_summary(
        panel,
        predictors,
        min_rows_per_municipality=8,
    )

    assert not aggregate.empty
    assert not detail.empty
    row = aggregate.iloc[0]
    assert int(row["municipalities_total"]) == 2
    assert int(row["municipalities_evaluable"]) == 1
    counts = json.loads(str(row["non_evaluable_counts"]))
    assert counts["constant_predictor"] >= 1


def test_temporal_validation_audit_detects_invalid_window_and_reserved_overlap() -> None:
    rows = []
    for period in pd.period_range("2024-01", "2024-06", freq="M"):
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": str(period),
                "target_period_t1": str(period + 1),
                "target_period_t2": str(period + 2),
                "y_evaluable_t1": True,
                "y_evaluable_t2": True,
            }
        )
    panel_dev = pd.DataFrame(rows)
    panel_reserved = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2024-06"],
        }
    )

    audit = build_temporal_validation_audit(
        panel_dev,
        panel_reserved,
        window_train_endpoints=["2024-04"],
        predictor_columns_used=["dengue_lag1", "rain_lag1"],
    )

    assert len(audit) == 1
    row = audit.iloc[0]
    assert row["check_labels_observable_at_cutoff"] == "FAIL"
    assert row["check_reserved_block_excluded"] == "FAIL"
    assert row["temporal_validation_result"] == "FAIL"


def test_notebook_is_code_only() -> None:
    notebook_path = Path("notebooks/03_consolidated_dataset_pipeline.ipynb")
    result = assert_notebook_code_only(notebook_path)
    assert result["code_only"] is True
    assert result["non_code_cells"] == []
