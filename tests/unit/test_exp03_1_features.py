from __future__ import annotations

import copy

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp03_1_features import PREDICTORS, paired_cohort, trajectory_features


def panel(*, end: str = "2024-12") -> pd.DataFrame:
    rows = []
    for month in pd.period_range("2018-01", end, freq="M"):
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": str(month),
                "dengue_notifications_count": float((month.year + month.month) % 7),
                "covered": True,
            }
        )
    return pd.DataFrame(rows)


def origin(month: str = "2024-03") -> pd.DataFrame:
    return pd.DataFrame([{"municipality_code": "50001", "year_month": month}])


def test_exact_windows_year_crossing_counts_changes_and_provenance() -> None:
    result = trajectory_features(panel(), origin("2024-03")).iloc[0]
    assert result.channel_recent_source_months == [
        "2024-02",
        "2024-01",
        "2023-12",
        "2023-11",
        "2023-10",
        "2023-09",
    ]
    assert result.channel_prior_source_months == [
        "2023-08",
        "2023-07",
        "2023-06",
        "2023-05",
        "2023-04",
        "2023-03",
    ]
    recent = sum(int(result[name]) for name in PREDICTORS[:3])
    prior = sum(
        int(result[f"channel_{slug}_prior_6m_count"]) for slug in ("security", "warning", "excess")
    )
    assert recent + int(result.channel_success_recent_6m_count_audit) == 6
    assert prior + int(result.channel_success_prior_6m_count_audit) == 6
    for slug in ("security", "warning", "excess"):
        assert (
            result[f"channel_{slug}_change_6m"]
            == result[f"channel_{slug}_recent_6m_count"] - result[f"channel_{slug}_prior_6m_count"]
        )
    assert all(result[f"{name}__latest_source_month"] == "2024-02" for name in PREDICTORS)


def test_future_mutation_does_not_change_features_and_no_future_is_consumed() -> None:
    source = panel()
    before = trajectory_features(source, origin())
    changed = source.copy()
    changed.loc[changed.year_month.ge("2024-03"), "dengue_notifications_count"] = 9999
    after = trajectory_features(changed, origin())
    pd.testing.assert_frame_equal(before, after)
    assert max(before.iloc[0].channel_recent_source_months) < "2024-03"


def test_historical_states_use_their_own_cut() -> None:
    source = panel()
    before = trajectory_features(source, origin())
    changed = source.copy()
    # 2024-01 can affect later reconstructions, but not the zone reconstructed for 2023-12.
    changed.loc[changed.year_month.eq("2024-01"), "dengue_notifications_count"] = 9999
    after = trajectory_features(changed, origin())
    assert before.iloc[0].channel_recent_source_months == after.iloc[0].channel_recent_source_months
    # The mutation is inside the requested window, so the aggregate may change; it cannot
    # leak backward into December's historical cutoff or source-month membership.
    assert "2023-12" in after.iloc[0].channel_recent_source_months


def test_unknown_and_covered_zero_are_distinct_and_gaps_are_not_crossed() -> None:
    source = panel()
    zero = source.copy()
    zero.loc[zero.year_month.eq("2024-02"), "dengue_notifications_count"] = pd.NA
    assert bool(trajectory_features(zero, origin()).iloc[0].channel_trajectory_known)
    unknown = zero.copy()
    unknown.loc[unknown.year_month.eq("2024-02"), "covered"] = False
    row = trajectory_features(unknown, origin()).iloc[0]
    assert not row.channel_trajectory_known
    assert row.channel_recent_6m_known == 5
    assert pd.isna(row.channel_security_recent_6m_count)


def test_missing_calendar_key_is_unknown_not_compacted() -> None:
    source = panel().loc[lambda frame: ~frame.year_month.eq("2023-12")]
    row = trajectory_features(source, origin()).iloc[0]
    assert row.channel_recent_6m_known == 5
    assert row.channel_trajectory_exclusion_reason == "unknown_recent_state"


def test_counts_never_exceed_six_and_only_six_predictors_are_exposed() -> None:
    row = trajectory_features(panel(), origin()).iloc[0]
    assert all(-6 <= int(row[name]) <= 6 for name in PREDICTORS)
    assert all(0 <= int(row[name]) <= 6 for name in PREDICTORS[:3])
    assert "channel_success_recent_6m_count" not in PREDICTORS


def test_paired_cohort_uses_identical_rows_and_exclusion_reasons() -> None:
    features = trajectory_features(panel(), origin())
    features["v09"] = 1.0
    features["onset"] = 1
    common, ledger = paired_cohort(features, base_predictors=["v09"], labels=["onset"])
    assert common[["municipality_code", "year_month"]].to_dict("records") == origin().to_dict(
        "records"
    )
    assert ledger.exclusion_reason.tolist() == ["included"]
    broken = copy.deepcopy(features)
    broken.loc[0, "channel_trajectory_known"] = False
    common, ledger = paired_cohort(broken, base_predictors=["v09"], labels=["onset"])
    assert common.empty and ledger.exclusion_reason.tolist() == ["unknown_channel_history"]


def test_invalid_or_post_2024_inputs_fail_closed() -> None:
    bad = panel()
    bad["covered"] = bad.covered.astype(object)
    bad.loc[0, "covered"] = "yes"
    with pytest.raises(ValueError, match="covered"):
        trajectory_features(bad, origin())
    with pytest.raises(ValueError, match="2025"):
        trajectory_features(panel(end="2025-01"), origin())
    with pytest.raises(ValueError, match="2025"):
        trajectory_features(panel(), origin("2025-01"))
