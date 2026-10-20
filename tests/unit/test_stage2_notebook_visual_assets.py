from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.stage2_notebook_visual_assets import (
    PredictorSpec,
    VariableSpec,
    add_consecutive_lag,
    assert_notebook_code_only,
    build_correlation_diagnostics,
    build_missingness_inventory,
    build_month_calendar,
    build_temporal_validation_audit,
    compute_lag_association_summary,
    compute_municipality_seasonality,
    longest_true_run,
    point_biserial_correlation,
    select_supervised_rows,
    summarize_endemic_channel,
    summarize_profile_scope,
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
            "y_status_t1": [
                "evaluable",
                "evaluable",
                "evaluable",
                "evaluable",
                "evaluable",
                "insufficient_history",
                "target_outside_panel",
            ],
            "y_status_t2": [
                "evaluable",
                "evaluable",
                "evaluable",
                "evaluable",
                "evaluable",
                "future_observation_missing",
                "target_outside_panel",
            ],
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
    assert int(y_row["non_evaluable_rows"]) == 2

    assert len(compact) == 2
    assert note["municipality_count"] == 2
    assert note["examples_total"] == 7
    y_reasons = cast(dict[str, dict[str, int]], note["y_non_evaluable_reasons"])
    assert y_reasons["t1"]["insufficient_history"] == 1
    assert y_reasons["t1"]["target_outside_panel"] == 1


def test_summarize_profile_scope_declares_sample_limits() -> None:
    raw_sample = pd.DataFrame(
        {
            "INI_SIN": [
                "01/01/2006",
                "15/06/2008",
                "01/01/2011",
                "05/01/2019",
                "",
            ]
        }
    )

    summary = summarize_profile_scope(raw_sample, sample_size=150_000)

    assert summary["source_stream"] == "dengue_general_only"
    assert summary["includes_dengue_grave_stream"] is False
    assert summary["sample_rows_requested"] == 150_000
    assert summary["sample_rows_loaded"] == 5
    assert summary["ini_sin_year_min"] == 2006
    assert summary["ini_sin_year_max"] == 2019
    assert summary["share_rows_2006_2011"] == 0.75


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


def test_select_supervised_rows_excludes_reserved_targets_and_keeps_horizon_scope() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 5,
            "year_month": ["2024-09", "2024-10", "2024-11", "2024-12", "2025-01"],
            "target_period_t1": ["2024-10", "2024-11", "2024-12", "2025-01", "2025-02"],
            "target_period_t2": ["2024-11", "2024-12", "2025-01", "2025-02", "2025-03"],
            "y_evaluable_t1": [True, True, True, True, True],
            "y_evaluable_t2": [True, True, True, True, True],
        }
    )

    selected_t1 = select_supervised_rows(
        panel,
        1,
        reference_max_period="2024-12",
        target_max_period="2024-12",
    )
    selected_t2 = select_supervised_rows(
        panel,
        2,
        reference_max_period="2024-12",
        target_max_period="2024-12",
    )

    assert selected_t1["target_period_t1"].tolist() == ["2024-10", "2024-11", "2024-12"]
    assert selected_t2["target_period_t2"].tolist() == ["2024-11", "2024-12"]


def test_point_biserial_rejects_invalid_support() -> None:
    x_constant = pd.Series([1.0, 1.0, 1.0])
    y_binary = pd.Series([0, 1, 0])
    try:
        point_biserial_correlation(x_constant, y_binary)
    except ValueError as exc:
        assert str(exc) == "constant_predictor"
    else:
        raise AssertionError("Expected constant_predictor ValueError")


def test_select_supervised_rows_enforces_target_min_and_accepts_boundary() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 6,
            "year_month": ["2011-10", "2011-11", "2011-12", "2012-01", "2012-02", "2012-03"],
            "target_period_t1": ["2011-11", "2011-12", "2012-01", "2012-02", "2012-03", "2012-04"],
            "target_period_t2": ["2011-12", "2012-01", "2012-02", "2012-03", "2012-04", "2012-05"],
            "y_evaluable_t1": [True] * 6,
            "y_evaluable_t2": [True] * 6,
        }
    )

    t1 = select_supervised_rows(
        panel,
        1,
        target_min_period="2012-01",
        target_max_period="2012-04",
    )
    t2 = select_supervised_rows(
        panel,
        2,
        target_min_period="2012-01",
        target_max_period="2012-05",
    )

    assert bool((t1["target_period_t1"].astype(str) < "2012-01").any()) is False
    assert bool((t2["target_period_t2"].astype(str) < "2012-01").any()) is False
    assert "2012-01" in t1["target_period_t1"].astype(str).tolist()
    assert "2012-01" in t2["target_period_t2"].astype(str).tolist()


def test_validation_t2_rejects_pre_cutoff_reference_and_keeps_cutoff_boundary() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50001"],
            "year_month": ["2018-11", "2018-12", "2019-01"],
            "target_period_t1": ["2018-12", "2019-01", "2019-02"],
            "target_period_t2": ["2019-01", "2019-02", "2019-03"],
            "y_evaluable_t1": [True, True, True],
            "y_evaluable_t2": [True, True, True],
        }
    )

    legacy_t2 = select_supervised_rows(
        panel,
        2,
        target_min_period="2019-01",
        target_max_period="2019-06",
    )
    corrected_t2 = select_supervised_rows(
        panel,
        2,
        reference_min_period="2018-12",
        target_min_period="2019-01",
        target_max_period="2019-06",
    )

    assert "2018-11" in legacy_t2["year_month"].astype(str).tolist()
    assert "2018-11" not in corrected_t2["year_month"].astype(str).tolist()
    assert "2018-12" in corrected_t2["year_month"].astype(str).tolist()


def test_compute_lag_association_marks_non_evaluable_groups() -> None:
    months = pd.period_range("2022-01", "2023-12", freq="M")
    rows = []
    for i, period in enumerate(months):
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": str(period),
                "target_period_t1": str(period + 1),
                "target_period_t2": str(period + 2),
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
                "target_period_t1": str(period + 1),
                "target_period_t2": str(period + 2),
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


def test_build_correlation_diagnostics_reports_global_month_adjustment() -> None:
    months = pd.period_range("2018-01", "2023-12", freq="M")
    panel = pd.DataFrame(
        {
            "year_month": [str(period) for period in months],
            "dengue_notifications_count": [float(i + 1) for i, _ in enumerate(months)],
            "rain_mm_month_sum": [float((i + 1) * 2) for i, _ in enumerate(months)],
            "temp_mean_c_month_mean": [float(500 - i) for i, _ in enumerate(months)],
        }
    )

    raw, adjusted, redundancy, meta = build_correlation_diagnostics(
        panel,
        ["dengue_notifications_count", "rain_mm_month_sum", "temp_mean_c_month_mean"],
        redundancy_threshold=0.90,
    )

    assert raw.shape == (3, 3)
    assert adjusted.shape == (3, 3)
    assert meta["month_adjustment"] == "global_calendar_month_mean_centering"
    assert meta["interpretation_limit"] == "descriptive_association_not_causal_or_auto_feature_drop"
    assert len(redundancy) >= 1


def test_summarize_endemic_channel_reports_null_threshold_consistency() -> None:
    panel = pd.DataFrame(
        {
            "p25_canal_t": [1.0, None, None],
            "p50_canal_t": [2.0, None, None],
            "p75_canal_t": [3.0, None, 1.0],
            "zona_canal_t": ["SEGURIDAD", None, None],
        }
    )

    summary = summarize_endemic_channel(panel)

    assert summary["status"] == "ok"
    assert summary["rows_with_zone"] == 1
    assert summary["rows_null_zone"] == 2
    assert summary["rows_null_zone_with_any_threshold_value"] == 1
    assert summary["rows_zone_with_missing_threshold"] == 0


def test_temporal_validation_audit_uses_safe_target_selection_per_horizon() -> None:
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

    assert len(audit) == 2
    assert set(audit["horizon"].tolist()) == {"t1", "t2"}
    assert set(audit["check_labels_observable_at_cutoff"].tolist()) == {"PASS"}
    assert set(audit["check_validation_reference_at_or_after_cutoff"].tolist()) == {"PASS"}
    assert set(audit["check_validation_target_within_declared_window"].tolist()) == {"PASS"}
    assert set(audit["check_reserved_block_excluded"].tolist()) == {"PASS"}
    assert set(audit["temporal_validation_result"].tolist()) == {"PASS"}


def test_temporal_windows_apply_policy_bounds_and_fix_t2_reference_leakage() -> None:
    municipalities = [f"{50001 + idx:05d}" for idx in range(76)]
    periods = pd.period_range("2011-01", "2024-12", freq="M")

    rows: list[dict[str, object]] = []
    for municipality in municipalities:
        for period in periods:
            rows.append(
                {
                    "municipality_code": municipality,
                    "year_month": str(period),
                    "target_period_t1": str(period + 1),
                    "target_period_t2": str(period + 2),
                    "y_evaluable_t1": True,
                    "y_evaluable_t2": True,
                }
            )

    panel_development = pd.DataFrame(rows)
    panel_reserved = pd.DataFrame(
        {
            "municipality_code": municipalities,
            "year_month": ["2025-01"] * len(municipalities),
        }
    )
    window_train_endpoints = ["2018-12", "2020-12", "2022-12", "2024-06"]

    audit = build_temporal_validation_audit(
        panel_development,
        panel_reserved,
        window_train_endpoints=window_train_endpoints,
        predictor_columns_used=["rain_lag1"],
        development_target_min="2012-01",
        development_target_max="2024-12",
    )

    assert len(audit) == len(window_train_endpoints) * 2
    assert set(audit["temporal_validation_result"].tolist()) == {"PASS"}

    for train_end in window_train_endpoints:
        validation_start = f"{int(train_end[:4]) + 1:04d}-01" if train_end.endswith("-12") else None
        # Legacy selection (without reference_min_period) incorrectly includes one extra
        # reference month per municipality for T+2 (e.g., 2018-11 -> target 2019-01).
        legacy_t2 = select_supervised_rows(
            panel_development,
            2,
            target_min_period=str(pd.Period(train_end, freq="M") + 1),
            target_max_period=str(pd.Period(train_end, freq="M") + 6),
        )
        corrected_t2 = select_supervised_rows(
            panel_development,
            2,
            reference_min_period=train_end,
            reference_max_period=str(pd.Period(train_end, freq="M") + 6),
            target_min_period=max(str(pd.Period(train_end, freq="M") + 1), "2012-01"),
            target_max_period=min(str(pd.Period(train_end, freq="M") + 6), "2024-12"),
        )
        assert int(len(legacy_t2) - len(corrected_t2)) == 76
        if validation_start is not None:
            assert validation_start >= "2012-01"

    assert bool((audit["validation_reference_before_cutoff_count"] == 0).all()) is True
    assert bool((audit["check_validation_reference_at_or_after_cutoff"] == "PASS").all()) is True
    assert bool((audit["validation_target_min_selected"].dropna() >= "2012-01").all()) is True
    assert bool((audit["validation_target_max_selected"].dropna() <= "2024-12").all()) is True


ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_PATH = ROOT / "notebooks/03_consolidated_dataset_pipeline.ipynb"


@pytest.mark.skipif(
    not NOTEBOOK_PATH.exists(),
    reason="notebook fixture is not present in this checkout",
)
def test_notebook_is_code_only() -> None:
    result = assert_notebook_code_only(NOTEBOOK_PATH)
    assert result["code_only"] is True
    assert result["non_code_cells"] == []
