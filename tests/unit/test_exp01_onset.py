"""EXP01 pure temporal, target, paired-budget and metric contracts."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp01 import SyntheticPredictor
from sat_dengue.experiments.onset import (
    historical_state,
    labels,
    operational_eligibility,
    partitions,
    predictor_projection,
)
from sat_dengue.experiments.onset_evaluation import (
    assert_paired,
    calibration_summary,
    episode_metrics,
    matched_thresholds,
    paired_block_interval,
)


def state_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["50001"] * 6,
            "year_month": ["2020-11", "2020-12", "2021-01", "2021-02", "2021-03", "2021-04"],
            "excess": pd.Series([0, 0, 1, 1, 0, 0], dtype="Int64"),
        }
    )


def test_t1_label_uses_exact_next_calendar_month_across_year_boundary() -> None:
    result = labels(state_frame(), 1)
    assert result.loc[0, "onset_target"] == 0
    assert result.loc[1, "target_month"] == "2021-01"
    assert result.loc[1, "onset_target"] == 1


def test_t2_exact_onset_and_continuing_episode_negative_are_frozen() -> None:
    result = labels(state_frame(), 2)
    assert result.loc[0, "onset_target"] == 1
    assert result.loc[1, "onset_target"] == 0
    assert result.loc[1, "earlier_onset_t1"]
    assert result.loc[1, "eligible_at_t"]


def test_operational_eligibility_depends_only_on_observed_current_state() -> None:
    current = pd.Series([0, 1, pd.NA], dtype="Int64")
    before = operational_eligibility(current)
    # The function accepts only Y(T), so future states cannot alter its result.
    future = pd.Series([1, 0, 1], dtype="Int64")
    future[:] = [0, 1, 0]
    assert operational_eligibility(current).equals(before)
    assert before.tolist() == [True, False, False]


def test_future_label_and_positive_availability_offsets_are_rejected() -> None:
    with pytest.raises(ValueError, match="Future label"):
        predictor_projection(
            pd.DataFrame({"onset_target": [0]}), ["onset_target"], {"onset_target": 0}
        )
    with pytest.raises(ValueError, match="availability"):
        predictor_projection(pd.DataFrame({"rain": [1.0]}), ["rain"], {"rain": 1})


def test_unknown_current_excess_is_not_operationally_eligible() -> None:
    assert not operational_eligibility(pd.Series([pd.NA], dtype="Int64")).iloc[0]


def test_missing_calendar_month_is_never_bridged() -> None:
    frame = state_frame().drop(index=1).reset_index(drop=True)
    result = labels(frame, 2)
    assert pd.isna(result.loc[0, "onset_target"])
    assert result.loc[0, "eligible_at_t"]


def test_duplicate_municipality_month_keys_fail_closed() -> None:
    frame = pd.concat([state_frame(), state_frame().head(1)], ignore_index=True)
    with pytest.raises(ValueError, match="Duplicate"):
        labels(frame, 1)


def test_2025_is_rejected_for_all_partition_roles() -> None:
    cohort = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2024-12"],
            "target_month": ["2025-01"],
            "eligible_at_t": [True],
        }
    )
    window: dict[str, Any] = {
        "train": ["2024-01", "2024-12"],
        "calibration": ["2025-01", "2025-02"],
        "selection": ["2025-03", "2025-04"],
        "evaluation": ["2025-05", "2025-06"],
    }
    with pytest.raises(ValueError, match="Consumed 2025"):
        partitions(cohort, window)


def test_temporal_roles_are_disjoint_and_ordered_by_target_month() -> None:
    cohort = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 8,
            "year_month": [f"2000-{month:02d}" for month in range(1, 9)],
            "target_month": [f"2000-{month:02d}" for month in range(1, 9)],
            "eligible_at_t": [True] * 8,
        }
    )
    window = {
        "train": ["2000-01", "2000-02"],
        "calibration": ["2000-03", "2000-04"],
        "selection": ["2000-05", "2000-06"],
        "evaluation": ["2000-07", "2000-08"],
    }
    result = partitions(cohort, window)
    assert [len(result[k]) for k in ("train", "calibration", "selection", "evaluation")] == [2] * 4
    assert max(result["train"].target_month) < min(result["calibration"].target_month)


def test_2024_is_permitted_only_as_evaluation_stress() -> None:
    cohort = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2023-12"],
            "target_month": ["2024-01"],
            "eligible_at_t": [True],
        }
    )
    window: dict[str, Any] = {
        "train": ["2023-01", "2023-06"],
        "calibration": ["2023-07", "2023-08"],
        "selection": ["2023-09", "2023-12"],
        "evaluation": ["2024-01", "2024-12"],
    }
    with pytest.raises(ValueError, match="declared retrospective stress"):
        partitions(cohort, window)
    window["evidence_type"] = "retrospective_stress"
    assert len(partitions(cohort, window)["evaluation"]) == 1


def test_historical_channel_uses_only_five_prior_same_month_values() -> None:
    rows = [
        {
            "municipality_code": "50001",
            "year_month": f"{year}-01",
            "dengue_notifications_count": value,
        }
        for year, value in zip(range(2015, 2021), [1, 2, 3, 4, 5, 9], strict=True)
    ]
    state, history = historical_state(pd.DataFrame(rows), "50001", "2020-01", as_of="2020-01")
    assert state == 1 and history == tuple(f"{year}-01" for year in range(2015, 2020))
    unavailable, _ = historical_state(pd.DataFrame(rows), "50001", "2020-01", as_of="2019-12")
    assert unavailable is None
    changed_future = pd.DataFrame(
        rows
        + [
            {
                "municipality_code": "50001",
                "year_month": "2021-01",
                "dengue_notifications_count": 1_000_000,
            }
        ]
    )
    same_state, _ = historical_state(changed_future, "50001", "2020-01", as_of="2020-01")
    assert same_state == state


def test_paired_comparison_requires_identical_rows_and_predictors() -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2020-01"],
            "target_month": ["2020-02"],
            "rain": [5.0],
            "onset_target": [1],
        }
    )
    other = frame.assign(onset_target=0)
    assert_paired(frame, other, predictors=["rain"])
    with pytest.raises(ValueError, match="differ"):
        assert_paired(frame, other.assign(rain=6.0), predictors=["rain"])


def test_matched_budget_uses_whole_ties_and_same_false_onset_cap() -> None:
    truth = np.array([1, 0, 1, 0])
    excess = np.array([0.9, 0.8, 0.8, 0.1])
    onset = np.array([0.8, 0.3, 0.7, 0.1])
    result = matched_thresholds(truth, excess, onset, budget=0)
    assert result == {"excess": 0.9, "onset": 0.7}


def test_episode_metrics_count_continuation_as_false_onset_alert() -> None:
    frame = labels(state_frame(), 2)
    frame["year_month"] = state_frame().year_month
    result = episode_metrics(frame.iloc[[1]], np.array([True]))
    assert result["real_onsets"] == 0
    assert result["false_alerts"] == 1


def test_episode_metrics_keep_unpredicted_onsets_in_denominator() -> None:
    frame = labels(state_frame(), 1).iloc[[1]].copy()
    result = episode_metrics(frame, np.array([False]))
    assert result["real_onsets"] == 1
    assert result["missed_episodes"] == 1
    assert result["onset_sensitivity"] == 0.0


def test_calibration_bins_cover_unit_interval_and_single_year_bootstrap_is_guarded() -> None:
    cal = calibration_summary(np.array([0, 1]), np.array([0.0, 1.0]))
    assert cal["expected_calibration_error"] == 0.0
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001", "73001"],
            "target_month": ["2020-01", "2020-02"],
            "onset_target": [0, 1],
        }
    )
    result = paired_block_interval(
        frame, np.array([False, False]), np.array([False, True]), seed=42
    )
    assert result == {"status": "insufficient_cluster_support", "interval": None}


def test_block_bootstrap_is_reproducible_for_multiple_municipalities_and_years() -> None:
    rows = []
    left = []
    right = []
    for municipality in ("50001", "73001"):
        for year in (2020, 2021):
            for month in range(1, 13):
                rows.append(
                    {
                        "municipality_code": municipality,
                        "target_month": f"{year}-{month:02d}",
                        "onset_target": int(month == 1),
                    }
                )
                left.append(False)
                right.append(month == 1 and municipality == "50001")
    frame = pd.DataFrame(rows)
    a = paired_block_interval(frame, np.asarray(left), np.asarray(right), seed=42, repeats=50)
    b = paired_block_interval(frame, np.asarray(left), np.asarray(right), seed=42, repeats=50)
    assert a == b and a["status"] == "retrospective_paired"


def test_synthetic_interface_is_seeded_and_has_zero_real_fits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sat_dengue.experiments import exp01

    def forbidden_native_fit(*args: object, **kwargs: object) -> object:
        pytest.fail("Synthetic execution reached the native estimator adapter")

    monkeypatch.setattr(exp01, "native_fit", forbidden_native_fit)
    X = pd.DataFrame({"dengue_notifications_count": [1.0, 2.0]})
    y = pd.Series([0, 1])
    first = SyntheticPredictor(X, y, 42).predict(X)
    second = SyntheticPredictor(X, y, 42).predict(X)
    assert first.equals(second)
    receipt = exp01.synthetic_run()
    assert len(receipt["children"]) == 36
    assert receipt["real_model_fits"] == receipt["real_preparer_refits"] == 0
    assert all(
        set(child)
        == {"objective", "family", "horizon", "window", "cohort", "seed", "evidence_type"}
        for child in receipt["children"]
    )


def test_exp00_registry_identity_remains_unchanged() -> None:
    from sat_dengue.tracking.experiments import resolve_experiment

    baseline = resolve_experiment("EXP00")
    assert (
        baseline["protocol_sha256"]
        == "4f8e32d8c70ba1661b84efca3cb1cc25288335bbceb2508cec970231756b920b"
    )
    assert baseline["objective_slug"] == "register_pre_kedro_baseline"
