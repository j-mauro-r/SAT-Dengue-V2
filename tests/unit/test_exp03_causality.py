"""Generated-only causal feature, support and coverage regression checks."""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01, exp03
from sat_dengue.experiments.exp03_contrasts import interval
from sat_dengue.experiments.exp03_features import cohorts, coverage, prepare, validate_design


def generated() -> tuple[pd.DataFrame, dict, dict]:
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(v, freq="M") + 180) for v in panel.year_month]
    return panel, contract, exp03.load_protocol()["design"]


@pytest.mark.parametrize("horizon", [1, 2])
def test_no_future_observation_changes_origin_predictors(horizon: int) -> None:
    panel, contract, design = generated()
    origin = "2020-10"
    before = prepare(panel, contract, horizon)
    altered = panel.copy()
    for column in contract["roles"]["predictors"]:
        if column != "zona_canal_t":
            altered.loc[altered.year_month.gt(origin), column] = 9999.0
    after = prepare(altered, contract, horizon)
    cols = design["predictors"]
    assert_frame_equal(
        before.loc[before.year_month.eq(origin), cols], after.loc[after.year_month.eq(origin), cols]
    )
    row = before.loc[(before.year_month == origin) & (before.municipality_code == "50001")].iloc[0]
    target = pd.Period(origin, freq="M") + horizon
    historical = panel.loc[
        (panel.municipality_code == "50001")
        & panel.year_month.isin([f"{target.year - n}-{target.month:02}" for n in range(1, 6)]),
        "dengue_notifications_count",
    ].to_numpy(dtype=float)
    assert row.channel_target_p25 == np.quantile(historical, 0.25)
    assert row.channel_target_p75 == np.quantile(historical, 0.75)


def test_sir_zero_semantics_and_no_population_claim() -> None:
    panel, contract, _ = generated()
    panel["dengue_notifications_count"] = 0.0
    first = prepare(panel, contract, 1)
    assert first.loc[first.year_month == "2020-10", "sir_notification_ratio_t"].eq(0).all()
    panel.loc[panel.year_month == "2020-10", "dengue_notifications_count"] = 1.0
    second = prepare(panel, contract, 1)
    assert second.loc[second.year_month == "2020-10", "sir_notification_ratio_t"].isna().all()
    assert "not census" in exp03.load_protocol()["sir_definition"]["population_reference"]


def test_variant_coverage_is_secondary_and_recovers_climate_missingness() -> None:
    panel, contract, design = generated()
    frame = prepare(panel, contract, 1)
    frame["rain_mm_month_sum"] = np.nan
    base = coverage(frame, design["variants"]["baseline_history_season"], design["predictors"])
    full = coverage(frame, design["variants"]["full"])
    assert base["rows"] > full["rows"] == 0
    assert base["recovered_rows"] == base["rows"]
    assert base["recovered_municipalities"] == base["municipalities"] == 2
    with pytest.raises(ValueError, match="Insufficient common"):
        altered = panel.copy()
        altered["rain_mm_month_sum"] = np.nan
        cohorts(altered, contract, design)


def test_preflight_support_and_stress_isolation() -> None:
    _, _, design = generated()
    short = copy.deepcopy(design)
    short["windows"] = [w for w in short["windows"] if w["id"] != "development_2021"]
    with pytest.raises(ValueError, match="Insufficient temporal"):
        validate_design(short)
    future = copy.deepcopy(design)
    future["windows"][0]["selection"] = ["2024-01", "2024-02"]
    with pytest.raises(ValueError):
        validate_design(future)
    frame = pd.DataFrame(
        {
            "municipality_code": ["a", "b"] * 3,
            "target_month": [f"{year}-01" for year in (2020, 2021, 2022) for _ in range(2)],
            "onset_target": [1, 1] * 3,
        }
    )
    left, right = np.ones(6, dtype=bool), np.zeros(6, dtype=bool)
    assert interval(frame, left, right, 42) == {
        "status": "retrospective_paired",
        "interval": [1.0, 1.0],
        "valid_replicates": 1000,
    }
    assert (
        interval(frame.iloc[:2], left[:2], right[:2], 42)["status"]
        == "insufficient_cluster_support"
    )


def test_no_oof_onsets_stops_before_any_adjustment(monkeypatch: pytest.MonkeyPatch) -> None:
    import sat_dengue.experiments.exp03_features as features

    panel, contract, design = generated()
    actual = features.partitions

    def no_evaluation_onsets(frame: pd.DataFrame, window: dict) -> dict:
        parts = actual(frame, window)
        if window["evidence_type"] == "retrospective_development":
            parts["evaluation"]["onset_target"] = 0
        return parts

    monkeypatch.setattr(features, "partitions", no_evaluation_onsets)
    with pytest.raises(ValueError, match="Insufficient onset cluster"):
        cohorts(panel, contract, design)
