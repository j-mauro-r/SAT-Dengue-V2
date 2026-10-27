"""Generated-only acceptance tests for revised EXP03 fixed-budget evaluation."""

from __future__ import annotations

import copy

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp03_causal_fixture import cluster_pair, generated

from sat_dengue.experiments.exp03_evaluation import (
    BUDGET_UNITS,
    group_summary,
    guardrails,
    metrics,
    paired_interval,
    select_threshold,
)
from sat_dengue.experiments.exp03_features import (
    validate_design,
)


def test_budget_floor_ties_no_alert_and_reconstructable_policy() -> None:
    truth, scores = [1, 0, 1, 0], [0.9, 0.8, 0.8, 0.1]
    # Manual candidate table (threshold, TP, FP, alerts):
    # >.9 -> (0,0,0); .9 -> (1,0,1); .8 -> (2,1,3); .1 -> (2,2,4).
    # floor(.5 * 3)=1 forbids the final candidate, and whole ties forbid
    # separating the positive/negative at .8. Thus .8 uniquely maximizes TP.
    chosen = select_threshold(truth, scores, 0.5, 3.0)
    assert chosen["selection_false_alert_cap"] == 1
    assert chosen["threshold"] == 0.8
    assert chosen["threshold_tie_size"] == 2
    assert chosen["detected_onsets"] == 2
    assert chosen["false_alerts"] == 1
    assert chosen["emitted_alerts"] == 3
    assert chosen["underspend"] == 0
    assert [score >= chosen["threshold"] for score in scores] == [True, True, True, False]
    assert select_threshold([1, 0], [0.7, 0.7], 0, 1)["no_alert"]
    assert select_threshold([0], [0.8], 1, 1)["no_alert"]
    assert select_threshold([1, 0], [0.8, 0.7], 0, 1)["threshold"] == 0.8
    assert select_threshold([], [], 1, 0)["threshold"] is None


@pytest.mark.parametrize("budget", [None, -1, float("inf")])
def test_missing_or_invalid_budget_blocks_selection(budget: float | None) -> None:
    with pytest.raises((PermissionError, ValueError)):
        select_threshold([0, 1], [0.1, 0.9], budget, 1)


def test_budget_metadata_units_and_inputs_are_checked() -> None:
    good = {"value": 0.5, "units": BUDGET_UNITS, "rationale": "synthetic fixture only"}
    assert select_threshold([1], [0.5], good, 1)["budget_rationale"] == good["rationale"]
    with pytest.raises(ValueError, match="units"):
        select_threshold([1], [0.5], {**good, "units": "false_alerts_per_row"}, 1)
    for truth, scores in [([0, 2], [0, 1]), ([0, 1], [0, np.nan]), ([1], [1, 0])]:
        with pytest.raises(ValueError):
            select_threshold(truth, scores, 1, 1)


def test_utility_unknown_labels_abstentions_and_probability_objective() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 4,
            "target_month": ["2020-01", "2020-02", "2020-03", "2020-04"],
            "onset_target": [1, 0, 1, np.nan],
            "excess_target": [1, 1, 1, 0],
            "horizon": [2] * 4,
        }
    )
    frame.attrs["eligible_onsets"] = 3
    result = metrics(frame, [1, 1, None, 0], 1.0, 0.5, [0.8, 0.7, 0.4, 0.1], "excess")
    assert result["detected_onsets"] == 1
    assert result["missed_onsets"] == 1
    assert result["false_alerts"] == 1  # continuation is false for onset
    assert result["onset_sensitivity"] == 0.5
    assert result["coverage_adjusted_sensitivity"] == pytest.approx(1 / 3)
    assert result["false_alarm_ratio"] == 0.5
    assert result["false_alerts_per_monitored_municipality_year"] == 1
    assert result["false_alerts_per_eligible_municipality_year"] == 2
    assert result["abstentions"] == 1
    assert result["unknown_outcomes"] == 1
    assert result["brier"] == pytest.approx(
        np.mean((np.array([0.8, 0.7, 0.4, 0.1]) - [1, 1, 1, 0]) ** 2)
    )
    assert result["actual_lead_months"] is None


def generated_pair() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows, exposure = [], []
    for m, code in enumerate(["50001", "50002", "73001"]):
        for year in [2020, 2021, 2022]:
            rows.extend(
                [
                    {
                        "municipality_code": code,
                        "target_month": f"{year}-02",
                        "onset_target": 1,
                        "alert": m == 0,
                    },
                    {
                        "municipality_code": code,
                        "target_month": f"{year}-03",
                        "onset_target": 0,
                        "alert": m == 0,
                    },
                ]
            )
            exposure.append(
                {
                    "municipality_code": code,
                    "target_year": year,
                    "monitored_exposure": float(m + 1),
                    "eligible_exposure": 0.5,
                    "common_exposure": 2 / 12,
                }
            )
    left = pd.DataFrame(rows)
    right = left.copy()
    right["alert"] = False
    # A wholly ineligible municipality must remain in the sampling universe.
    exposure.extend(
        {
            "municipality_code": "73999",
            "target_year": y,
            "monitored_exposure": 10.0,
            "eligible_exposure": 0.0,
            "common_exposure": 0.0,
        }
        for y in [2020, 2021, 2022]
    )
    return left, right, pd.DataFrame(exposure)


def test_paired_bootstrap_resamples_monitored_denominators_ineligible_clusters() -> None:
    left, right, exposure = generated_pair()
    result = paired_interval(left, right, exposure, draws=1000, seed=7)
    assert result["municipalities"] == 4
    assert result["sensitivity_difference"]["estimate"] == pytest.approx(1 / 3)
    assert result["false_alert_rate_difference"]["estimate"] == pytest.approx(3 / 48)
    assert result["exposure_draws"]["minimum"] != result["exposure_draws"]["maximum"]
    # Independently reproduce weighted rate draws including every pre-gate cluster.
    rng = np.random.default_rng(7)
    rates, valid_sensitivity = [], 0
    for _ in range(1000):
        municipalities = rng.integers(0, 4, 4)
        years = rng.integers(0, 3, 3)
        mw = np.bincount(municipalities, minlength=4)
        yw = np.bincount(years, minlength=3)
        denominator = float(np.dot(mw, [1, 2, 3, 10]) * yw.sum())
        rates.append(float(mw[0] * yw.sum() / denominator))
        valid_sensitivity += int(mw[:3].sum() > 0)
    low, high = np.quantile(rates, [0.025, 0.975])
    assert result["false_alert_rate_difference"]["lower"] == pytest.approx(low)
    assert result["false_alert_rate_difference"]["upper"] == pytest.approx(high)
    assert result["sensitivity_difference"]["valid_draws"] == valid_sensitivity
    assert result["false_alert_rate_difference"]["valid_draws"] == 1000
    assert paired_interval(right, left, exposure, draws=1000, seed=7)[
        "false_alert_rate_difference"
    ]["estimate"] == pytest.approx(-3 / 48)


def test_sparse_interval_has_metric_specific_valid_draws_and_no_iid_fallback() -> None:
    left, right, exposure = generated_pair()
    left = left.loc[left.target_month.str.startswith("2020")]
    right = right.loc[right.target_month.str.startswith("2020")]
    exposure = exposure.loc[exposure.target_year.eq(2020)]
    result = paired_interval(left, right, exposure, draws=100)
    assert result["sensitivity_difference"]["status"] == "unavailable"
    assert result["sensitivity_difference"]["valid_draws"] == 0
    assert result["false_alert_rate_difference"]["valid_draws"] == 100


def test_pairing_stress_and_exposure_reconciliation_fail_closed() -> None:
    left, right, exposure = generated_pair()
    with pytest.raises(ValueError, match="keys or onset"):
        paired_interval(left, right.iloc[1:], exposure)
    changed = right.copy()
    changed.loc[0, "onset_target"] = 0
    with pytest.raises(ValueError, match="keys or onset"):
        paired_interval(left, changed, exposure)
    bad = exposure.copy()
    bad.loc[0, "target_year"] = 2024
    with pytest.raises(ValueError, match="Stress/benchmark"):
        paired_interval(left, right, bad)
    bad = exposure.copy()
    bad.loc[0, "common_exposure"] = 0
    with pytest.raises(ValueError, match="Common exposure"):
        paired_interval(left, right, bad)
    bad = exposure.copy()
    bad.loc[0, "eligible_exposure"] = 100
    with pytest.raises(ValueError, match="reconcile"):
        paired_interval(left, right, bad)


def test_zero_onset_zero_alerts_and_guardrails_remain_unknown() -> None:
    frame = pd.DataFrame(
        {"municipality_code": ["50001"], "target_month": ["2020-01"], "onset_target": [0]}
    )
    result = metrics(frame, [False], 1, 1)
    assert result["onset_sensitivity"] is None
    assert result["onset_precision"] is None
    assert result["false_alarm_ratio"] is None
    assert guardrails(result, result, support=False)["support"] == "unknown"
    assert guardrails(result, result, support=False)["aggregate_benefit"] == "unknown"
    assert guardrails(result, result)["formal_equivalence"] is False


def test_group_micro_macro_support_and_equal_year_are_distinct() -> None:
    left, _, exposure = generated_pair()
    left["historical_profile"] = "low"
    summary = group_summary(left, left.alert, exposure)
    assert summary["micro"]["onset_sensitivity"] == pytest.approx(1 / 3)
    assert summary["macro"]["sensitivity"] == pytest.approx(1 / 3)
    assert summary["macro"]["sensitivity_included_municipalities"] == 3
    assert summary["macro"]["sensitivity_excluded_municipalities"] == 1
    assert summary["equal_year_sensitivity"] == pytest.approx(1 / 3)
    assert all(r["support"] == "insufficient" for r in summary["groups"])


def test_group_coverage_uses_known_eligible_ledger_onsets_outside_common_cohort() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "73001"],
            "target_month": ["2020-01", "2021-01", "2020-01"],
            "onset_target": [1, 0, 0],
            "transmission_profile": ["low", "low", "high"],
        }
    )
    ledger = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "73001", "73002"],
            "target_year": [2020, 2021, 2020, 2020],
            "transmission_profile": ["low", "low", "high", "high"],
            "monitored_exposure": [1.0, 1.0, 1.0, 1.0],
            "eligible_exposure": [0.5, 0.5, 0.5, 0.5],
            "common_exposure": [1 / 12, 1 / 12, 1 / 12, 0.0],
            "known_eligible_onsets": [3, 0, 0, 2],
            "known_covered_onsets": [3, 0, 0, 2],
            "excluded_onsets": [2, 0, 0, 2],
        }
    )
    # Inherited whole-frame attrs must not override the matched cluster ledger.
    frame.attrs["eligible_onsets"] = 999
    result = group_summary(frame, [True, False, False], ledger)
    assert result["micro"]["real_onsets"] == 1
    assert result["micro"]["eligible_onsets"] == 5
    assert result["micro"]["covered_onsets"] == 5
    assert result["micro"]["coverage_adjusted_sensitivity"] == 0.2
    low = next(
        r
        for r in result["groups"]
        if r["dimension"] == "transmission_profile" and r["group"] == "low"
    )
    assert low["common_onsets"] == 1
    assert low["eligible_onsets"] == 3
    assert low["eligible_onsets_excluded_from_common"] == 2
    assert low["onset_sensitivity"] == 1.0
    assert low["coverage_adjusted_sensitivity"] == pytest.approx(1 / 3)
    excluded_municipality = next(
        r
        for r in result["groups"]
        if r["dimension"] == "municipality_code" and r["group"] == "73002"
    )
    assert excluded_municipality["common_onsets"] == 0
    assert excluded_municipality["eligible_onsets"] == 2
    assert excluded_municipality["onset_sensitivity"] is None
    assert excluded_municipality["coverage_adjusted_sensitivity"] == 0.0
    assert excluded_municipality["support"] == "insufficient"
    assert result["macro"]["sensitivity_included_municipalities"] == 1
    assert result["macro"]["sensitivity_excluded_municipalities"] == 2
    assert result["equal_year_sensitivity_included_years"] == 1
    assert result["equal_year_sensitivity_excluded_years"] == 1


def test_profile_exposure_mapping_keeps_each_frozen_cut_and_unknown_outcome_unknown() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001"],
            "target_month": ["2020-01", "2021-01"],
            "onset_target": [1, np.nan],
            "transmission_profile": ["low", "high"],
        }
    )
    ledger = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "73999"],
            "target_year": [2020, 2021, 2020],
            "monitored_exposure": [1.0, 2.0, 4.0],
            "eligible_exposure": [0.5, 0.5, 0.5],
            "common_exposure": [1 / 12, 0.0, 0.0],
            "known_eligible_onsets": [2, 0, 1],
        }
    )
    result = group_summary(frame, [True, False], ledger)
    profiles = {r["group"]: r for r in result["groups"] if r["dimension"] == "transmission_profile"}
    assert profiles["low"]["monitored_exposure"] == 1.0
    assert profiles["high"]["monitored_exposure"] == 2.0
    assert profiles["profile_unavailable"]["monitored_exposure"] == 4.0
    assert profiles["high"]["unknown_outcomes"] == 1
    assert profiles["high"]["real_onsets"] == 0
    assert profiles["high"]["known_outcomes"] == 0
    assert profiles["high"]["coverage_adjusted_sensitivity"] is None
    assert profiles["profile_unavailable"]["coverage_adjusted_sensitivity"] == 0.0
    assert result["micro"]["coverage_adjusted_sensitivity"] == pytest.approx(1 / 3)


def test_inconsistent_known_onset_ledger_is_rejected() -> None:
    frame = pd.DataFrame(
        {"municipality_code": ["50001"], "target_month": ["2020-01"], "onset_target": [1]}
    )
    ledger = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "target_year": [2020],
            "monitored_exposure": [1.0],
            "eligible_exposure": [0.5],
            "known_eligible_onsets": [0],
        }
    )
    with pytest.raises(ValueError, match="cannot be smaller"):
        group_summary(frame, [True], ledger)


def test_all_exposure_denominators_use_the_same_paired_cluster_weights() -> None:
    from hashlib import sha256

    left, right, ledger = generated_pair()
    # Vary denominators by municipality AND year. The entirely ineligible
    # exposure-only municipality remains in the monitored sampling universe.
    for index, row in ledger.iterrows():
        if row.municipality_code == "73999":
            continue
        year_factor = int(row.target_year) - 2019
        municipality_factor = {"50001": 1, "50002": 2, "73001": 3}[row.municipality_code]
        ledger.loc[index, "eligible_exposure"] = 0.5 + year_factor * municipality_factor / 50
        ledger.loc[index, "common_exposure"] = 2 / 12 + year_factor * municipality_factor / 100
    result = paired_interval(left, right, ledger, seed=53, draws=200)
    audit = result["exposure_draws"]
    rng = np.random.default_rng(53)
    municipalities = ["50001", "50002", "73001", "73999"]
    years = [2020, 2021, 2022]
    denominator_tensor = np.array(
        [
            [
                ledger.loc[
                    ledger.municipality_code.eq(m) & ledger.target_year.eq(y),
                    ["monitored_exposure", "eligible_exposure", "common_exposure"],
                ]
                .iloc[0]
                .to_numpy(dtype=float)
                for y in years
            ]
            for m in municipalities
        ]
    )
    expected = []
    for _ in range(200):
        mw = np.bincount(rng.integers(0, 4, 4), minlength=4)
        yw = np.bincount(rng.integers(0, 3, 3), minlength=3)
        expected.append(
            (denominator_tensor * (mw[:, None] * yw[None, :])[:, :, None]).sum(axis=(0, 1))
        )
    array = np.asarray(expected, dtype="<f8")
    assert audit["paired_cluster_weights_shared"] is True
    assert audit["joint_draw_column_order"] == ["monitored", "eligible", "common"]
    # Exact joint-draw identity detects denominator-specific resampling, even if
    # a separately shuffled denominator had identical marginal ranges.
    assert audit["joint_draw_sha256"] == sha256(array.tobytes()).hexdigest()
    for column, name in enumerate(["monitored", "eligible", "common"]):
        values = array[:, column]
        positive = values[values > 0]
        assert audit[name]["minimum"] == pytest.approx(positive.min())
        assert audit[name]["maximum"] == pytest.approx(positive.max())
        assert audit[name]["sum"] == pytest.approx(values.sum())
        assert audit[name]["valid_draws"] == len(positive)
        assert audit[name]["zero_draws"] == 200 - len(positive)
        assert audit[name]["minimum"] != audit[name]["maximum"]
    assert audit["minimum"] == audit["monitored"]["minimum"]
    assert audit["maximum"] == audit["monitored"]["maximum"]


def test_covered_eligible_and_common_onset_populations_are_distinct_at_t2() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "target_month": ["2020-03"],
            "onset_target": [1],
            "horizon": [2],
        }
    )
    ledger = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "target_year": [2020],
            "monitored_exposure": [1.0],
            "eligible_exposure": [0.5],
            "common_exposure": [1 / 12],
            "known_covered_onsets": [5],
            "known_eligible_onsets": [3],
        }
    )
    result = group_summary(frame, [True], ledger)
    for metric in [result["micro"], *result["groups"]]:
        assert metric["covered_onsets"] == 5
        assert metric["eligible_onsets"] == 3
        assert metric["common_onsets"] == 1
        assert metric["onset_sensitivity"] == 1.0
        assert metric["coverage_adjusted_sensitivity"] == pytest.approx(1 / 3)
    # A covered-only attribute is not evidence that every covered event was eligible.
    frame.attrs["covered_onsets"] = 5
    direct = metrics(frame, [True], 1.0, 0.5)
    assert direct["covered_onsets"] == 5
    assert direct["eligible_onsets"] == 1
    frame.attrs = {}
    direct = metrics(frame, [True], 1.0, 0.5)
    assert direct["covered_onsets"] == direct["eligible_onsets"] == 1


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
