"""Generated-only causal feature, support and exposure-aware regression checks.

Evaluation-label perturbations and changes to raw counts are deliberately distinct:
raw observations may legitimately feed subsequent origins and later-cut training.
"""

from __future__ import annotations

import copy
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01, exp03
from sat_dengue.experiments.exp03_evaluation import metrics, paired_interval, select_threshold
from sat_dengue.experiments.exp03_features import (
    cohorts,
    coverage,
    exposure_table,
    historical_profiles,
    prepare,
    validate_design,
)


def generated() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(v, freq="M") + 180) for v in panel.year_month]
    return panel, contract, exp03.load_protocol()["design"]


@pytest.mark.parametrize("horizon", [1, 2])
def test_no_future_observation_changes_origin_predictors_or_gate(horizon: int) -> None:
    panel, contract, design = generated()
    origin = "2020-10"
    before = prepare(panel, contract, horizon)
    altered = panel.copy()
    for column in contract["roles"]["predictors"]:
        if column != "zona_canal_t":
            altered.loc[altered.year_month.gt(origin), column] = 9999.0
    after = prepare(altered, contract, horizon)
    cols = design["predictors"] + ["eligible_at_t", "current_excess"]
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
    assert row.channel_target_p25 == np.quantile(historical, 0.25, method="linear")
    assert row.channel_target_p75 == np.quantile(historical, 0.75, method="linear")
    # Raw counts at an observed month legitimately change later-origin lag recipes.
    next_origin = str(pd.Period(origin, freq="M") + 2)
    assert not before.loc[before.year_month.eq(next_origin), "dengue_lag_1"].equals(
        after.loc[after.year_month.eq(next_origin), "dengue_lag_1"]
    )


def test_notification_observed_expected_zero_and_missing_are_distinct() -> None:
    panel, contract, _ = generated()
    panel["dengue_notifications_count"] = 0.0
    first = prepare(panel, contract, 1)
    origin = first.year_month.eq("2020-10")
    assert first.loc[origin, "notification_log1p_oe_t"].eq(0).all()
    assert first.loc[origin, "expected_zero_t"].eq(1).all()
    assert first.loc[origin, "eligible_at_t"].all()
    panel.loc[panel.year_month.eq("2020-10"), "dengue_notifications_count"] = 1.0
    second = prepare(panel, contract, 1)
    assert second.loc[origin, "notification_log1p_oe_t"].eq(0).all()
    assert second.loc[origin, "expected_zero_t"].eq(1).all()
    assert second.loc[origin, "positive_zero_reference_t"].all()
    assert not second.loc[origin, "eligible_at_t"].any()
    # Positive/zero is excluded by Y(T)=1, not an artificial missing ratio.
    panel.loc[panel.year_month.eq("2017-10"), "dengue_notifications_count"] = np.nan
    unknown = prepare(panel, contract, 1)
    assert unknown.loc[origin, "notification_log1p_oe_t"].isna().all()
    assert unknown.loc[origin, "expected_zero_t"].isna().all()
    assert unknown.loc[origin, "missing_reference_t"].all()


def test_variant_coverage_is_potential_and_primary_common_rows_do_not_change() -> None:
    panel, contract, design = generated()
    altered = panel.copy()
    altered["rain_mm_month_sum"] = np.nan
    frame = prepare(altered, contract, 1)
    base = coverage(frame, design["variants"]["V00"], design["predictors"])
    full = coverage(frame, design["variants"]["V09"])
    assert base["rows"] > full["rows"] == 0
    assert base["recovered_rows"] == base["rows"]
    assert base["potential_coverage_only"] is True
    assert base["municipalities"] == 2
    prepared = cohorts(altered, contract, design)
    for parts, common in prepared.values():
        # Missing any union recipe empties every primary arm's shared cohort.
        assert common["evaluation"].empty
        ledger = exposure_table(parts)
        evaluation = ledger.loc[ledger.role.eq("evaluation")]
        assert evaluation.monitored_exposure.sum() > 0
        assert evaluation.common_exposure.sum() == 0
        assert evaluation.excluded_onsets.sum() == evaluation.known_eligible_onsets.sum()


def cluster_pair() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    left = pd.DataFrame(
        {
            "municipality_code": ["50001", "73001"] * 3,
            "target_month": [f"{year}-02" for year in (2020, 2021, 2022) for _ in range(2)],
            "onset_target": [1, 1] * 3,
            "alert": [True] * 6,
        }
    )
    right = left.copy()
    right["alert"] = False
    exposure = pd.DataFrame(
        {
            "municipality_code": ["50001", "73001"] * 3,
            "target_year": [year for year in (2020, 2021, 2022) for _ in range(2)],
            "monitored_exposure": [1.0, 2.0] * 3,
            "eligible_exposure": [0.5] * 6,
            "common_exposure": [1 / 12] * 6,
        }
    )
    return left, right, exposure


def test_temporal_support_and_stress_isolation_with_resampled_exposure() -> None:
    _, _, design = generated()
    short = copy.deepcopy(design)
    short["windows"] = [w for w in short["windows"] if w["id"] != "development_2021"]
    with pytest.raises(ValueError, match="scientific field"):
        validate_design(short)
    future = copy.deepcopy(design)
    future["windows"][0]["selection"] = ["2024-01", "2024-02"]
    with pytest.raises(ValueError):
        validate_design(future)
    left, right, exposure = cluster_pair()
    result = paired_interval(left, right, exposure, seed=42)
    sensitivity = result["sensitivity_difference"]
    assert sensitivity["status"] == "available"
    assert sensitivity["lower"] == sensitivity["upper"] == 1.0
    assert sensitivity["valid_draws"] == 1000
    assert result["exposure_draws"]["resampled"] is True
    assert result["exposure_draws"]["minimum"] < result["exposure_draws"]["maximum"]
    single = paired_interval(left.iloc[:2], right.iloc[:2], exposure.iloc[:2], seed=42)
    assert single["sensitivity_difference"]["status"] == "unavailable"
    assert single["sensitivity_difference"]["valid_draws"] == 0
    bad = left.copy()
    bad.loc[0, "target_month"] = "2024-02"
    with pytest.raises(ValueError, match="development"):
        paired_interval(bad, bad, exposure)


def test_zero_oof_onsets_is_unknown_not_a_successful_guardrail() -> None:
    left, right, exposure = cluster_pair()
    left["onset_target"] = 0
    right["onset_target"] = 0
    result = paired_interval(left, right, exposure)
    assert result["sensitivity_difference"]["estimate"] is None
    assert result["sensitivity_difference"]["status"] == "unavailable"
    assert result["false_alert_rate_difference"]["valid_draws"] == 1000
    assert result["false_alert_rate_difference"]["estimate"] == pytest.approx(6 / 9)
    # Unknown labels are not promoted to negatives, while known unsupported zeros
    # still supply a meaningful false-alert numerator and monitored denominator.
    left.loc[0, "onset_target"] = np.nan
    summary = metrics(left, left.alert, 9.0, 3.0)
    assert summary["onset_sensitivity"] is None
    assert summary["unknown_outcomes"] == 1
    assert summary["false_alerts"] == 5


def test_evaluation_label_mutation_cannot_change_fit_inputs_or_selection_policy() -> None:
    panel, contract, design = generated()
    # Supplied stored labels and zones are never trusted to construct X or Y.
    before = prepare(panel, contract, 2)
    injected = panel.assign(onset_target=999, excess_target=999, zona_canal_t="EXCESO")
    after = prepare(injected, contract, 2)
    assert_frame_equal(before, after)
    parts, common = cohorts(panel, contract, design)[2, "development_2020"]
    columns = design["variants"]["V09"]
    train = common["train"][columns].copy()
    train.attrs = {}
    training_truth = common["train"].onset_target.copy()
    selection = common["selection"]
    score = np.linspace(0.05, 0.95, len(selection))
    d = exposure_table(parts).query("role=='selection'").monitored_exposure.sum()
    policy = select_threshold(selection.onset_target, score, 2.0, d)
    changed = common["evaluation"].copy()
    changed["onset_target"] = 1 - changed.onset_target
    changed.attrs = {}
    original_x = common["evaluation"][columns].copy()
    original_x.attrs = {}
    assert_frame_equal(original_x, changed[columns])
    actual_train = common["train"][columns].copy()
    actual_train.attrs = {}
    assert_frame_equal(train, actual_train)
    pd.testing.assert_series_equal(training_truth, common["train"].onset_target)
    assert select_threshold(selection.onset_target, score, 2.0, d) == policy
    before_profile, meta = historical_profiles(panel, "2018-12")
    panel.loc[panel.year_month.gt("2018-12"), "dengue_notifications_count"] = 10000.0
    after_profile, changed_meta = historical_profiles(panel, "2018-12")
    assert_frame_equal(before_profile, after_profile)
    assert meta == changed_meta
