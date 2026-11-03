"""Generated arithmetic, chronology and immutable-publication checks; zero fits."""

import json

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle, verify_bundle
from sat_dengue.experiments.academic_benchmark import (
    ARMS,
    aggregate,
    comparator_inputs,
    comparisons,
    deterministic_alerts,
    read_predictions,
    summarize,
)
from sat_dengue.experiments.exp_beta01_v2 import require_pair
from sat_dengue.training_preparation.serialization import bytes_record


def sample() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["50001"] * 4,
            "truth": [1, 0, 0, 0],
            "target_excess": [1, 1, 0, 0],
            "alert": [True, True, True, False],
            "score": [0.9, 0.8, 0.7, 0.1],
        }
    )


def test_far_excess_is_not_onset_false_discovery_or_fpr():
    result = aggregate(sample())
    assert result["detected"] == 1
    assert result["false_alerts"] == 2
    assert result["false_alerts_excess"] == 1
    assert result["continuation_alerts"] == 1
    assert result["far_excess"] == pytest.approx(1 / 3)
    assert result["fpr_excess"] == 0.5
    assert result["fpr_onset"] == pytest.approx(2 / 3)
    assert result["precision"] == pytest.approx(1 / 3)
    assert result["false_alerts_per_municipality_year"] == 6
    assert result["brier"] == pytest.approx((0.01 + 0.64 + 0.49 + 0.01) / 4)


def test_zero_alerts_and_zero_positive_denominators_remain_undefined():
    frame = sample().assign(alert=False, score=np.nan)
    value = aggregate(frame)
    assert value["far_excess"] is None and value["precision"] is None
    assert value["average_precision"] is None and value["brier"] is None
    assert value["false_alerts_per_municipality_year"] == 0
    assert aggregate(frame.assign(truth=0))["sensitivity"] is None


def test_strict_channel_ties_zero_threshold_and_future_mutation():
    inputs = pd.DataFrame(
        {"origin_count": [0, 1, 5, 6], "target_p75": [0, 0, 5, 5], "origin_zone": ["SEGURIDAD"] * 4}
    )
    channel, persistence = deterministic_alerts(inputs, 2)
    assert channel.tolist() == [False, True, False, True]
    assert not persistence.any()
    changed = inputs.assign(target_excess=[0, 1, 1, 0], future_count=[999, 0, 50, 0])
    pd.testing.assert_series_equal(channel, deterministic_alerts(changed, 2)[0])


def history_fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    periods = pd.period_range("2014-01", "2020-03", freq="M").astype(str)
    table = pd.DataFrame(
        {
            "municipality_code": "50001",
            "year_month": periods,
            "dengue_notifications_count": 5.0,
            "zona_canal_t": "ALERTA",
            "p75_h5_t2": 5.0,
        }
    )
    # T is non-excess; T+1 and T+2 are excess => continuation, not onset T+2.
    table.loc[
        table.year_month.isin(["2020-02", "2020-03"]),
        ["dengue_notifications_count", "zona_canal_t"],
    ] = [6.0, "EXCESO"]
    cohort = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2020-01"],
            "target_month": ["2020-03"],
            "truth": [0],
        }
    )
    return table, cohort


def test_h5_exact_history_and_future_outcomes_cannot_change_alert():
    table, cohort = history_fixture()
    first = comparator_inputs(table, cohort, 2)
    assert first.target_excess.tolist() == [1]
    assert first.history_first.tolist() == ["2015-03"]
    assert first.history_last.tolist() == ["2019-03"]
    table.loc[table.year_month.eq("2020-03"), ["dengue_notifications_count", "zona_canal_t"]] = [
        0.0,
        "EXITO",
    ]
    second = comparator_inputs(table, cohort, 2)
    assert second.target_excess.tolist() == [0]
    pd.testing.assert_series_equal(
        deterministic_alerts(first, 2)[0], deterministic_alerts(second, 2)[0]
    )
    with pytest.raises(ValueError, match="value mismatch"):
        comparator_inputs(table, cohort.assign(truth=1), 2)
    with pytest.raises(ValueError, match="Missing CHANNEL"):
        comparator_inputs(table.loc[table.year_month.ne("2017-03")], cohort, 2)
    with pytest.raises(ValueError, match="P75 mismatch"):
        comparator_inputs(table.assign(p75_h5_t2=9.0), cohort, 2)


def test_pairing_rejects_intersection_duplicates_and_label_changes():
    _, cohort = history_fixture()
    with pytest.raises(ValueError, match="key mismatch"):
        require_pair(cohort, cohort.iloc[:0], ["truth"])
    with pytest.raises(ValueError, match="key mismatch"):
        require_pair(cohort, pd.concat([cohort, cohort]), ["truth"])
    with pytest.raises(ValueError, match="value mismatch"):
        require_pair(cohort, cohort.assign(truth=1), ["truth"])


def test_frozen_csv_boolean_and_probability_rejection(tmp_path):
    file = tmp_path / "predictions.csv"
    frame = sample().assign(department_code="50")
    frame.to_csv(file, index=False)
    loaded = read_predictions(file)
    assert loaded.alert.tolist() == [True, True, True, False]
    frame.assign(alert="not_false").to_csv(file, index=False)
    with pytest.raises(ValueError, match="tokens"):
        read_predictions(file)
    frame.assign(score=2).to_csv(file, index=False)
    with pytest.raises(ValueError, match="probabilities"):
        read_predictions(file)


def test_joint_acceptance_is_strict_and_inclusive_at_exact_five_pp():
    base = {
        "horizon": 1,
        "year": "all",
        "department": "all",
        "rows": 40,
        "onsets": 20,
        "alerts": 20,
        "detected": 10,
        "sensitivity": 0.5,
        "false_alerts": 10,
        "false_alerts_excess": 4,
        "far_excess": 0.2,
        "false_alerts_per_municipality_year": 3,
        "budget_met": False,
    }
    rows = [{**base, "arm": arm} for arm in ARMS]
    rows[1].update(detected=0, alerts=0, far_excess=np.nan)
    rows[3].update(detected=11, false_alerts_excess=5, far_excess=0.25)
    rows[4].update(detected=11, false_alerts_excess=6, far_excess=0.3)
    table = comparisons(pd.DataFrame(rows))
    primary = table.loc[table.reference.eq("CHANNEL")].set_index("arm")
    assert primary.loc["G0_OFF", "academic_status"] == "MEETS"
    assert primary.loc["G0_ON", "academic_status"] == "DOES_NOT_MEET"
    assert primary.loc["R0", "academic_status"] == "DOES_NOT_MEET"  # equality fails A
    assert not primary.loc["G0_OFF", "beta_joint_descriptive"]
    rows[0].update(alerts=0, far_excess=np.nan)
    assert comparisons(pd.DataFrame(rows)).academic_status.eq("NOT_EVALUABLE").all()


def test_strata_reconcile_counts_and_do_not_mix_departments():
    frames = []
    for arm in ARMS:
        for year in (2020, 2021):
            for department in ("50", "73"):
                frames.append(
                    sample().assign(arm=arm, horizon=2, year=year, department_code=department)
                )
    metrics, paired = summarize(pd.concat(frames, ignore_index=True))
    assert len(metrics) == 6 * 3 * 3
    assert len(paired) == 4 * 3 * 3 * 3
    for _, frame in metrics.groupby("arm"):
        all_row = frame.loc[frame.year.eq("all") & frame.department.eq("all")].iloc[0]
        annual = frame.loc[frame.year.ne("all") & frame.department.eq("all")]
        for name in ("rows", "onsets", "detected", "alerts", "false_alerts_excess"):
            assert all_row[name] == annual[name].sum()


def test_existing_publisher_rejects_overwrite_and_tampered_reproduction(tmp_path):
    # The production adapter is reused unchanged; exercise its no-overwrite contract.
    body = {"files": {"predictions.csv": bytes_record(b"generated\n")}}
    bundle_id = bytes_record(canonical_bytes(body))["sha256"]
    payloads = {
        "predictions.csv": b"generated\n",
        "manifest.json": canonical_bytes({**body, "bundle_id": bundle_id}),
    }
    target = publish_bundle(tmp_path, bundle_id, payloads, existing_policy="error")
    verify_bundle(target, payloads)
    with pytest.raises(ValueError, match="replacement is forbidden"):
        publish_bundle(tmp_path, bundle_id, payloads, existing_policy="error")
    (target / "predictions.csv").write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="corrupted"):
        verify_bundle(target, payloads)
    assert json.loads(payloads["manifest.json"])["bundle_id"] == bundle_id
