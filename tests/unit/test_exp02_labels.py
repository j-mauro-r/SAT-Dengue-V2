"""Verificaciones discriminantes de calendario, cobertura y episodios EXP02."""

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp02_labels import (
    change_interval,
    compare_stability,
    construct_variants,
    episode_overlap,
    episodes,
)


def panel(counts=None):
    months = pd.period_range("2000-01", "2012-12", freq="M").astype(str)
    result = pd.DataFrame(
        {"municipality_code": "50001", "year_month": months, "dengue_notifications_count": 0}
    )
    for month, count in (counts or {}).items():
        result.loc[result.year_month.eq(month), "dengue_notifications_count"] = count
    return result


def test_zero_percentile_complete_history_strict_rule_and_no_backfill():
    data = panel({"2010-01": 1})
    result = construct_variants(data)
    for history, variant in result.items():
        frame = variant["states"].set_index("year_month")
        assert frame.loc["2010-01", "p75"] == 0
        assert frame.loc["2010-01", "excess"] == 1
        assert frame.loc["2010-02", "excess"] == 0
        assert frame.loc["2010-01", "history_available"] == history
    missing = data.loc[~data.year_month.eq("2001-01")]
    frame = construct_variants(missing)[9]["states"].set_index("year_month")
    assert pd.isna(frame.loc["2010-01", "excess"])
    assert frame.loc["2010-01", "non_evaluable_reason"] == "insufficient_history"


def test_five_seven_nine_labels_can_differ_on_identical_target_keys():
    data = panel({"2001-01": 100, "2002-01": 100, "2003-01": 100, "2004-01": 100, "2010-01": 10})
    variants = construct_variants(data)
    assert [
        variants[h]["states"].set_index("year_month").loc["2010-01", "excess"] for h in [5, 7, 9]
    ] == [1, 0, 0]
    design = {
        "seed": 42,
        "windows": [
            {
                "id": "development_2010",
                "evaluation": ["2010-01", "2010-12"],
                "evidence_type": "retrospective_development",
            }
        ],
    }
    result = compare_stability(variants, design)
    pair = next(p for p in result["pairs"] if p["reference_years"] == 5 and p["variant_years"] == 9)
    assert pair["excess"]["changed"] == 1
    assert pair["excess"]["one_to_zero"] == 1
    assert pair["excess"]["paired_rows"] == 12
    assert len({r["common_keys_sha256"] for r in result["children"]}) == 1
    assert any(x["dimension"] == "zero_heavy" for x in result["by_group"])


@pytest.mark.parametrize(
    "target_count,expected_labels",
    [(5, [1, 0, 0]), (8, [1, 1, 0]), (15, [1, 1, 0]), (16, [1, 1, 1])],
)
def test_five_seven_nine_manual_interpolation_oracle(target_count, expected_labels):
    # January history in chronological order, oldest first. The sorted windows
    # are [0,1,2,3,4], [0,1,2,3,4,11,15], [0,1,2,3,4,11,15,20,30].
    # HF7 ranks 3, 4.5 and 6 give P75=3, (4+11)/2=7.5 and 15.
    # n=5/9 have integer ranks for integer counts; n=7 discriminates interpolation.
    counts = {
        f"{year}-01": value
        for year, value in zip(range(2001, 2010), [20, 30, 11, 15, 0, 1, 2, 3, 4], strict=True)
    }
    counts["2010-01"] = target_count
    variants = construct_variants(panel(counts))
    for history, expected_p75, expected_label in zip(
        [5, 7, 9], [3.0, 7.5, 15.0], expected_labels, strict=True
    ):
        state = variants[history]["states"].set_index("year_month").loc["2010-01"]
        assert state["p75"] == expected_p75
        assert state["excess"] == expected_label
        assert state["history_available"] == history


def test_future_mutation_does_not_change_earlier_channel_and_legacy_ignored():
    data = panel({"2010-01": 3})
    original = construct_variants(data)
    changed = data.copy()
    changed.loc[changed.year_month.ge("2011-01"), "dengue_notifications_count"] = 10000
    changed["y_t1"] = "invalid future supplied label"
    changed["zona_canal_t"] = "EXCESO"
    for h, variant in construct_variants(changed).items():
        pd.testing.assert_frame_equal(
            variant["states"].loc[
                lambda x: x.year_month.le("2010-12"), ["year_month", "excess", "p75"]
            ],
            original[h]["states"].loc[
                lambda x: x.year_month.le("2010-12"), ["year_month", "excess", "p75"]
            ],
        )


def state_frame(months, values):
    return pd.DataFrame(
        {
            "municipality_code": "50001",
            "year_month": months,
            "excess": pd.array(values, dtype="Int64"),
        }
    )


def test_episode_crosses_year_and_unknown_is_censored_not_false_onset():
    f = state_frame(
        ["2023-11", "2023-12", "2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        [0, 1, 1, None, 1, 0, 1],
    )
    labels, eps = episodes(f, 5)
    assert [e["observed_duration"] for e in eps] == [2, 1, 1]
    assert eps[0]["confirmed_onset"] and eps[0]["right_censored"]
    assert eps[1]["left_censored"] and eps[1]["confirmed_end"]
    assert pd.isna(labels.loc[4, "onset"])
    assert labels.loc[1, "episode_id"] == labels.loc[2, "episode_id"]
    assert eps[-1]["right_censored"]


def test_missing_calendar_month_never_bridged():
    _, eps = episodes(state_frame(["2020-01", "2020-03"], [1, 1]), 5)
    assert len(eps) == 2
    assert all(e["left_censored"] and e["right_censored"] for e in eps)


def test_fragmentation_and_merging_are_episode_relations():
    dates = pd.period_range("2020-01", "2020-06", freq="M").astype(str)
    a, _ = episodes(state_frame(dates, [0, 1, 1, 1, 1, 0]), 5)
    b, _ = episodes(state_frame(dates, [0, 1, 0, 1, 1, 0]), 9)
    mask = pd.Series(True, index=a.index)
    assert episode_overlap(a, b, mask)["fragmented_reference_episodes"] == 1
    assert episode_overlap(b, a, mask)["merged_variant_episodes"] == 1


def test_invalid_counts_duplicate_keys_and_consumed_year_fail():
    for data in [
        panel().assign(year_month="2025-01"),
        pd.concat([panel(), panel().iloc[:1]]),
        panel().assign(dengue_notifications_count=-1),
    ]:
        with pytest.raises(ValueError):
            construct_variants(data)


def test_interval_requires_cluster_support_and_keeps_pairs():
    f = state_frame(["2020-01", "2020-02"], [0, 1])
    assert change_interval(f, np.array([0, 1]), seed=42)["interval"] is None
    keys = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "73001", "73001"],
            "year_month": ["2020-01", "2022-01"] * 2,
        }
    )
    assert change_interval(keys, np.ones(4), seed=42, repeats=20)["interval"] == [1, 1]


def test_unknown_gap_is_ambiguous_not_confirmed_fragmentation_or_merge():
    months = pd.period_range("2024-01", periods=5, freq="M").astype(str)
    left, _ = episodes(state_frame(months, [0, 1, 1, 1, 0]), 5)
    right, _ = episodes(state_frame(months, [0, 1, None, 1, 0]), 9)
    common = left.excess.notna() & right.excess.notna()
    forward, reverse = episode_overlap(left, right, common), episode_overlap(right, left, common)
    assert forward["fragmented_reference_episodes"] == reverse["merged_variant_episodes"] == 0
    assert forward["ambiguous_fragmentation"] == reverse["ambiguous_merging"] == 1


def test_paired_strata_detect_changes_hidden_by_equal_positive_totals():
    variants = construct_variants(panel({"2010-01": 3}))
    for h in (7, 9):
        frame = variants[h]["states"]
        frame.loc[frame.year_month.eq("2010-01"), "excess"] = 0
        frame.loc[frame.year_month.eq("2010-02"), "excess"] = 1
        variants[h]["states"], variants[h]["episodes"] = episodes(frame, h)
    result = compare_stability(
        variants,
        {
            "seed": 42,
            "windows": [
                {
                    "id": "fixture",
                    "evaluation": ["2010-01", "2010-12"],
                    "evidence_type": "generated",
                }
            ],
        },
    )
    pair = next(
        p
        for p in result["paired_by_group"]
        if p["dimension"] == "municipality"
        and p["reference_years"] == 5
        and p["variant_years"] == 9
    )
    assert pair["excess"]["zero_to_one"] == pair["excess"]["one_to_zero"] == 1
    assert pair["excess"]["changed"] == 2
    assert pair["stratum_definition"] == "five_year_reference"
