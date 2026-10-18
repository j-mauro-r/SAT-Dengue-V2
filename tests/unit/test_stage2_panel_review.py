from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "panel_review", ROOT / "scripts/stage2_panel_review.py"
)
assert spec and spec.loader
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


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
