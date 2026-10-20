from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "panel_review", ROOT / "scripts/stage2_panel_review.py"
)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)


def test_panel_independent_sources_survive_empty_dengue_month() -> None:
    keys = {"mun_full": ["50001", "50001"], "year_month": ["2020-01", "2020-02"]}
    grid = pd.DataFrame(keys)
    d = pd.DataFrame(
        {
            "mun_full": ["50001"],
            "year_month": ["2020-01"],
            "dengue_recorded_count": [2],
            "anomaly_count": [0],
        }
    )
    severe = pd.DataFrame({**keys, "severe_recorded_count": [1, 3]})
    climate = pd.DataFrame({**keys, "climate_days": [0, 29]})
    for col in review.CLIMATE:
        climate[col] = [float("nan"), 12.0]
        climate[col + "_valid_days"] = [0, 29]
    p = review.join_panel(grid, d, severe, climate, d, "S1")
    assert p.severe_recorded_count.sum() == 4
    assert p.loc[1, "temp_mean_c"] == 12.0
    assert pd.isna(p.loc[1, "dengue_count"])
    assert p.loc[1, "dengue_observation_state"] == "no_records_reporting_unknown"
    empty = d.iloc[:0]
    q = review.join_panel(grid, empty, severe, climate, d, "S3")
    pd.testing.assert_series_equal(p.severe_count, q.severe_count)
    pd.testing.assert_series_equal(p.temp_mean_c, q.temp_mean_c)
    assert q.loc[0, "dengue_observation_state"] == "all_records_removed_by_scenario"


def test_panel_invalid_geography_is_quarantined_without_losing_accounting() -> None:
    raw = pd.DataFrame(
        {
            "mun_full": ["50001", "50000", "73001"],
            "INI_SIN_dt": pd.to_datetime(["2013-01-01", "2013-01-01", None]),
            "COD_EVE": ["210", "210", "210"],
        }
    )
    c = pd.DataFrame({"mun_full": ["50001", "73001"]})
    result = review.partition_epi(raw, c, "210")
    assert result.disposition.tolist() == [
        "included",
        "unresolved_municipality",
        "missing_or_invalid_onset",
    ]
    assert len(result) == len(raw)


def test_panel_date_parser_does_not_swap_ambiguous_dates() -> None:
    parsed = review.parse_date(pd.Series(["03/04/2013 12:00:00 a. m.", "31/02/2013", None]))
    assert parsed.iloc[0] == pd.Timestamp("2013-04-03")
    assert parsed.iloc[1:].isna().all()


def test_sensitivity_equal_dates_are_not_true_swaps() -> None:
    d = pd.DataFrame(
        {
            "ini_current": pd.to_datetime(["2013-01-01", "2013-01-02", "2013-01-03"]),
            "not_current": pd.to_datetime(["2013-01-01", "2013-01-03", "2013-01-02"]),
            "ini_reference": pd.to_datetime(["2013-01-01", "2013-01-02", "2013-01-02"]),
            "not_reference": pd.to_datetime(["2013-01-01", "2013-01-03", "2013-01-03"]),
        }
    )
    result = review.date_pair_metrics(d)
    assert result["naive_inverted_pairs"] == 2
    assert result["equal_date_inverted_pairs"] == 1
    assert result["genuine_non_equal_inverted_pairs"] == 1


def test_sensitivity_support_is_common_and_excludes_unknown_target_and_partial_climate() -> None:
    f = pd.DataFrame(
        {
            "common_source_window": [True] * 4,
            "target_window": [True] * 4,
            "dengue_count": [1.0, 2.0, 3.0, 4.0],
            "target": [2.0, 3.0, 4.0, 5.0],
            "temp_mean_c": [20.0] * 4,
            "temp_mean_c_valid_days": [31, 30, 31, 31],
            "expected_climate_days": [31] * 4,
        }
    )
    frames = {s: f.copy() for s in ["S1", "S2", "S3"]}
    frames["S2"].loc[2, "target"] = float("nan")
    frames["S3"].loc[3, "target_window"] = False
    assert review.common_support(frames, "temp_mean_c").tolist() == [True, False, False, False]


def test_climate_days_conservation_accepts_zero_for_source_missing_keys() -> None:
    panel = pd.DataFrame(
        {
            "mun_full": ["50001", "50001", "73001", "73001"],
            "year_month": ["2020-01", "2020-02", "2020-01", "2020-02"],
            "climate_days": [0, 29, 0, 29],
        }
    )
    climate_monthly = pd.DataFrame(
        {
            "mun_full": ["50001", "73001"],
            "year_month": ["2020-02", "2020-02"],
            "climate_days": [29, 29],
        }
    )
    review.assert_climate_days_conservation(panel, climate_monthly)


def test_climate_days_conservation_rejects_nonzero_when_source_key_missing() -> None:
    panel = pd.DataFrame(
        {
            "mun_full": ["50001", "50001"],
            "year_month": ["2020-01", "2020-02"],
            "climate_days": [1, 29],
        }
    )
    climate_monthly = pd.DataFrame(
        {
            "mun_full": ["50001"],
            "year_month": ["2020-02"],
            "climate_days": [29],
        }
    )

    raised = False
    try:
        review.assert_climate_days_conservation(panel, climate_monthly)
    except AssertionError:
        raised = True
    assert raised


def test_rules_never_promote_retrospective_rows_to_operational_approval() -> None:
    rules = review.retrospective_rules()
    assert rules["historical_availability_reconstructed"] is False
    assert rules["operational_feature_use_approved"] is False
    assert rules["G2_closed"] is False
    assert rules["streams"]["combine"] is False
    assert "no certified disease zeros" in rules["zero_policy"]
    assert "no patient-level deduplication authority" in rules["duplicates"]


def test_rules_eligibility_counts_calendar_adjacent_observations_only() -> None:
    d = pd.DataFrame(
        {
            "mun_full": ["50001"] * 4,
            "municipality_name": ["EXAMPLE"] * 4,
            "department_name": ["Meta"] * 4,
            "year_month": ["2020-01", "2020-02", "2020-03", "2020-04"],
            "common_source_window": [True] * 4,
            "dengue_count": [1.0, float("nan"), 2.0, 3.0],
            "severe_count": [float("nan")] * 4,
            "climate_state": ["complete"] * 4,
            "expected_climate_days": [31, 29, 31, 30],
        }
    )
    for col in review.CLIMATE:
        d[col + "_valid_days"] = d.expected_climate_days
    result = review.eligibility_table(d)
    assert result.loc[0, "observed_pairs_t1"] == 1
    assert result.loc[0, "observed_pairs_t2"] == 1
    assert result.loc[0, "dengue_no_records_months"] == 1
    assert not result.loc[0, "operational_eligible"]
