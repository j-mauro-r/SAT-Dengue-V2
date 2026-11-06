"""Generated outcomes expose onset/excess differences and dependent sampling boundaries."""

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp_delta03_evaluation import difference, metrics, paired, uncertainty


def predictions(years=(2020, 2021, 2022)):
    rows = []
    for year in years:
        for code in ["50001", "73001"]:
            for month in [1, 2, 3, 4]:
                target = pd.Period(f"{year}-{month:02}", freq="M")
                truth = int(month == 1)
                rows.append(
                    {
                        "divipola_municipio": code,
                        "periodo_mes": str(target - 1),
                        "horizon": 1,
                        "target_month": str(target),
                        "truth": truth,
                        "target_excess": int(month <= 2),
                        "score": 0.8 if month <= 2 else 0.1,
                        "alert": month <= 2,
                        "episode_id": f"{code}-{year}" if month <= 2 else None,
                    }
                )
    return pd.DataFrame(rows)


def exposures(frame):
    f = frame[["divipola_municipio", "target_month"]].copy()
    f["year"] = pd.PeriodIndex(f.target_month, freq="M").year
    return (
        f.groupby(["divipola_municipio", "year"])
        .size()
        .rename("months")
        .reset_index()
        .assign(monitored_exposure=1.0)
    )


def spec():
    return {
        "method": "paired municipality and episode-preserving connected calendar-year blocks",
        "draws": 40,
        "confidence": 0.95,
        "seed": 1729,
        "minimum_municipalities": 2,
        "minimum_temporal_blocks": 2,
        "minimum_valid_fraction": 0.8,
    }


def test_onset_false_alert_is_not_excess_false_alert_and_episode_counts_are_separate():
    f = predictions()
    m = metrics(f, monitored_exposure=6, expected_rows=len(f))
    assert m["false_onset_alerts"] == 6 and m["false_excess_alerts"] == 0
    assert m["precision"] == 0.5 and m["academic_excess_FAR"] == 0
    assert m["onsets_detected"] == 6 and m["episodes"]["observed"] == 6
    assert m["anticipation_months_detected"] == 1
    assert m["false_onset_alerts_per_eligible_municipality_year"] == 3
    assert m["false_onset_alerts_per_monitored_municipality_year"] == 1
    assert m["coverage"] == 1 and m["calibration"]["reliability"]


def test_zero_alerts_no_positives_missing_outcome_and_exposure_never_fake_zero():
    f = predictions()
    f["alert"] = False
    m = metrics(f)
    assert m["precision"] is None and m["academic_excess_FAR"] is None
    assert m["metric_status"]["precision"] == "NO_EVALUABLE_NO_ALERTS"
    assert m["excess_status"] == "NO_EVALUABLE_NO_ALERTS"
    assert m["false_onset_alerts_per_monitored_municipality_year"] is None
    f["truth"] = 0
    m = metrics(f)
    assert m["metric_status"]["sensitivity"] == "NO_EVALUABLE_NO_ONSETS"
    assert m["metric_status"]["average_precision"] == "NO_EVALUABLE_CLASS_SUPPORT"
    assert (
        m["sensitivity"] is None and m["average_precision"] is None and m["auroc_secondary"] is None
    )
    f = f.drop(columns="target_excess")
    m = metrics(f)
    assert m["academic_excess_FAR"] is None and m["excess_status"].startswith("UNAVAILABLE")
    assert difference(m, m)["sensitivity"]["relative"] is None
    with pytest.raises(ValueError, match="exposure"):
        metrics(f, monitored_exposure=0.01)


def test_paired_keys_and_outcomes_cannot_be_intersected_or_substituted():
    f = predictions()
    with pytest.raises(ValueError, match="mismatch"):
        paired(f, f.iloc[1:])
    changed = f.copy()
    changed.loc[0, "truth"] = 0
    with pytest.raises(ValueError, match="outcomes"):
        paired(f, changed)
    with pytest.raises(ValueError, match="Duplicate"):
        metrics(pd.concat([f, f.iloc[[0]]]))


def test_structured_uncertainty_is_paired_reproducible_and_resamples_exposure():
    f = predictions()
    other = f.copy()
    other["alert"] = False
    other["score"] = 0.2
    result = uncertainty(f, other, exposures(f), spec())
    assert result == uncertainty(f, other, exposures(f), spec())
    assert result["status"] == "EVALUABLE" and result["temporal_blocks"] == 3
    assert result["intervals"]["sensitivity"]["low"] == 1
    assert result["intervals"]["sensitivity"]["high"] == 1
    assert result["intervals"]["false_onset_alerts"]["valid_draws"] == 40


def test_episode_year_connections_can_collapse_all_blocks_without_iid_fallback():
    f = predictions()
    f.loc[f.divipola_municipio.eq("50001"), "episode_id"] = "cross-year-episode"
    r = uncertainty(f, f, exposures(f), spec())
    assert r["status"] == "NO_EVALUABLE_INSUFFICIENT_CLUSTER_SUPPORT"
    assert r["temporal_blocks"] == 1 and r["intervals"] is None
    stress = predictions((2024,))
    r = uncertainty(stress, stress, exposures(stress), spec())
    assert r["status"].startswith("NO_EVALUABLE")
    with pytest.raises(ValueError, match="Stress2024"):
        both = pd.concat([predictions(), stress])
        uncertainty(both, both, exposures(both), spec())
    with pytest.raises(ValueError, match="exposure"):
        f = predictions()
        uncertainty(f, f, exposures(f).iloc[1:], spec())


@pytest.mark.parametrize(
    "key,value",
    [
        ("method", "iid"),
        ("draws", 0),
        ("confidence", 1.0),
        ("minimum_valid_fraction", float("nan")),
        ("minimum_temporal_blocks", 1),
    ],
)
def test_uncertainty_method_and_parameter_identity_cannot_lie(key, value):
    f = predictions()
    config = spec()
    config[key] = value
    with pytest.raises(ValueError):
        uncertainty(f, f, exposures(f), config)


def test_deterministic_comparators_do_not_invent_probability_metrics():
    f = predictions().drop(columns="score")
    result = metrics(f, probabilities_available=False)
    assert result["onsets_detected"] == 6 and result["sensitivity"] == 1
    assert result["brier"] is None and result["average_precision"] is None
    assert result["calibration"]["status"] == "NO_EVALUABLE_NO_PROBABILITIES"
