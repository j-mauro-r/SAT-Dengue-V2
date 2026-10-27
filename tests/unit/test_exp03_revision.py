"""Generated-only acceptance for exact-calendar revised EXP03 feature contracts."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp03_causal_fixture import generated
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03_features import (
    cohorts,
    coverage,
    coverage_groups,
    exposure_table,
    historical_profiles,
    prepare,
    role_parts,
)
from sat_dengue.experiments.exp03_revision import (
    CLIMATE_SOURCES,
    build_design,
    cell_counts,
    cell_grid,
    validate_design,
)


def design():
    legacy = json.loads(
        Path("docs/product/experiments/EXP03_feature_ablation/protocol.json").read_text()
    )["design"]
    return build_design(legacy)


def panel():
    rng = np.random.default_rng(419)
    rows = []
    for code in ("50001", "50002", "50003", "73001", "73002", "73003"):
        for date in pd.period_range("2005-01", "2025-12", freq="M"):
            row = {
                "municipality_code": code,
                "year_month": str(date),
                "dengue_notifications_count": float(rng.integers(0, 30)),
                "dengue_grave_notifications_count": float(rng.integers(0, 4)),
            }
            row.update({s: float(rng.uniform(1, 50)) for s in CLIMATE_SOURCES})
            rows.append(row)
    return pd.DataFrame(rows)


def test_canonical_sets_and_counts_no_duplicate_or_t1_excess():
    d = design()
    assert validate_design(d) == 408
    assert cell_counts(d) == {"onset": 384, "excess": 24, "total": 408, "terminal": 102}
    assert len({frozenset(v) for v in d["variants"].values()}) == 16
    assert not any(c["horizon"] == 1 and c["objective"] == "excess" for c in cell_grid(d))
    assert len(d["groups"]["C-"]) == len(d["groups"]["Cm"]) == 15
    assert set(d["groups"]["C-"]) & set(d["groups"]["Cm"])
    assert set(d["variants"]["V09"]) - set(d["variants"]["V07"]) == set(
        d["groups"]["U"] + d["groups"]["Z"] + d["groups"]["R0"]
    )
    d["variants"]["V14"] = d["variants"]["V08"]
    with pytest.raises(ValueError, match="composition"):
        validate_design(d)


def test_future_perturbation_does_not_change_predictors_or_gate():
    p = panel()
    before = prepare(p, {}, 2, allow_benchmark=True)
    p.loc[p.year_month.gt("2020-04"), "dengue_notifications_count"] += 10000
    after = prepare(p, {}, 2, allow_benchmark=True)
    keep = before.year_month.eq("2020-04")
    columns = design()["predictors"] + ["eligible_at_t"]
    pd.testing.assert_frame_equal(before.loc[keep, columns], after.loc[keep, columns])
    dates = before.attrs["source_months"]
    for c in design()["predictors"]:
        assert dates[c].le(before.year_month).all()
    lagged = (
        design()["groups"]["B"]
        + design()["groups"]["F"]
        + design()["groups"]["L"]
        + design()["groups"]["R-"]
        + design()["groups"]["C-"]
    )
    for c in lagged:
        if c not in {"mes_sin", "mes_cos", "municipality_code_feature"}:
            assert dates[c].lt(before.year_month).all()


def test_exact_lags_do_not_bridge_missing_calendar_month():
    p = panel()
    p = p.loc[~(p.municipality_code.eq("50001") & p.year_month.eq("2020-02"))]
    frame = prepare(p, {}, 1, allow_benchmark=True)
    row = frame.loc[frame.municipality_code.eq("50001") & frame.year_month.eq("2020-03")].iloc[0]
    assert pd.isna(row.dengue_lag_1)
    assert pd.isna(row.dengue_mean_lagged_3m)
    assert pd.isna(row["rain_mm_month_sum__lag_1"])
    assert not pd.isna(row.dengue_lag_2)


def test_zero_reference_finite_sentinel_flag_and_gate_are_distinct_from_missing():
    p = panel().loc[lambda f: f.municipality_code.eq("50001")].copy()
    p["dengue_notifications_count"] = 0.0
    p.loc[p.year_month.eq("2020-02"), "dengue_notifications_count"] = 3.0
    f = prepare(p, {}, 1, allow_benchmark=True).set_index("year_month")
    assert f.loc["2020-02", "notification_log1p_oe_t"] == 0
    assert f.loc["2020-02", "expected_zero_t"] == 1
    assert f.loc["2020-02", "positive_zero_reference_t"]
    assert not f.loc["2020-02", "eligible_at_t"]
    assert f.loc["2020-01", "eligible_at_t"]
    p.loc[p.year_month.eq("2017-01"), "dengue_notifications_count"] = np.nan
    f = prepare(p, {}, 1, allow_benchmark=True).set_index("year_month")
    assert pd.isna(f.loc["2020-01", "expected_zero_t"])
    assert pd.isna(f.loc["2020-01", "notification_log1p_oe_t"])


def test_profiles_are_historical_and_collapsed_not_forced_tertiles():
    p = panel()
    p["dengue_notifications_count"] = 5.0
    a, meta = historical_profiles(p, "2018-12")
    assert a.transmission_profile.eq("volume_tertiles_collapsed").all()
    assert meta["boundaries"] == [5.0, 5.0]
    p.loc[p.year_month.gt("2018-12"), "dengue_notifications_count"] = 999.0
    b, _ = historical_profiles(p, "2018-12")
    pd.testing.assert_frame_equal(a, b)
    p.loc[
        p.municipality_code.eq("50001") & p.year_month.between("2014-01", "2015-12"),
        "dengue_notifications_count",
    ] = np.nan
    a, _ = historical_profiles(p, "2018-12")
    assert (
        a.loc[a.municipality_code.eq("50001"), "transmission_profile"].iloc[0]
        == "history_insufficient"
    )


def test_pre_gate_exposure_includes_ineligible_months_and_embargo():
    p = panel().loc[lambda f: f.year_month.lt("2025-01")]
    d = design()
    prepared = cohorts(p, {}, d)
    parts, common = prepared[2, "development_2020"]
    evaluation = parts["evaluation"]
    assert evaluation.target_month.min() == "2020-02"
    assert not evaluation.eligible_at_t.all()
    exposure = exposure_table(parts).query("role=='evaluation'")
    assert exposure.monitored_exposure.sum() == pytest.approx(len(evaluation) / 12)
    assert exposure.monitored_exposure.sum() > exposure.eligible_exposure.sum()
    assert exposure.common_exposure.sum() == pytest.approx(len(common["evaluation"]) / 12)
    assert common["evaluation"].eligible_at_t.all()
    assert common["evaluation"].attrs["profiles"]["training_target_end"] == "2018-12"


def test_benchmark_boundary_and_delay_preserve_gate_and_lagged_dates():
    p = panel()
    with pytest.raises(ValueError, match="benchmark"):
        prepare(p, {}, 1)
    now = prepare(p, {}, 2, allow_benchmark=True)
    stale = prepare(p, {}, 2, allow_benchmark=True, delay=True)
    pd.testing.assert_series_equal(now.eligible_at_t, stale.eligible_at_t)
    d = design()
    cols = d["groups"]["B"] + d["groups"]["F"] + d["groups"]["C-"]
    pd.testing.assert_frame_equal(now[cols], stale[cols])
    assert stale.attrs["source_months"].dengue_notifications_count.lt(stale.year_month).all()
    assert stale.attrs["strict_availability_gate"] == "unavailable_abstain"


def test_t2_continuation_never_changes_t_eligibility_or_uses_t1_as_predictor():
    p = panel().loc[lambda f: f.municipality_code.eq("50001")].copy()
    p["dengue_notifications_count"] = 1.0
    p.loc[p.year_month.isin(["2020-02", "2020-03"]), "dengue_notifications_count"] = 10.0
    f = prepare(p, {}, 2, allow_benchmark=True).set_index("year_month")
    # T=January admits forecast although T+1 excess begins; March is continuation.
    assert f.loc["2020-01", "eligible_at_t"]
    assert f.loc["2020-01", "earlier_onset_t1"]
    assert f.loc["2020-01", "excess_target"] == 1
    assert f.loc["2020-01", "onset_target"] == 0
    assert f.loc["2020-01", "error_type"] == "continuation"
    # T=December forecasts exact February onset, with January non-excess.
    assert f.loc["2019-12", "onset_target"] == 1
    assert f.loc["2019-12", "error_type"] == "onset"
    h1 = prepare(p, {}, 1, allow_benchmark=True)
    known = h1.eligible_at_t & h1.onset_target.notna()
    pd.testing.assert_series_equal(
        h1.loc[known, "onset_target"], h1.loc[known, "excess_target"], check_names=False
    )


def test_noncanonical_temporal_roles_or_contrast_are_rejected():
    d = design()
    d["windows"][0]["train"][1] = "2019-01"
    with pytest.raises(ValueError, match="scientific field"):
        validate_design(d)
    d = design()
    d["contrasts"][0]["right"] = "V09"
    with pytest.raises(ValueError, match="scientific field"):
        validate_design(d)


def test_delay_recomputes_whole_current_arithmetic_without_shifting_lagged_blocks():
    p = panel().loc[lambda f: f.municipality_code.eq("50001")].copy()
    for month, count in (("2020-01", 2.0), ("2020-02", 5.0), ("2020-03", 11.0), ("2020-04", 20.0)):
        p.loc[p.year_month.eq(month), "dengue_notifications_count"] = count
    now = prepare(p, {}, 2, allow_benchmark=True)
    stale = prepare(p, {}, 2, allow_benchmark=True, delay=True)
    row = stale.loc[stale.year_month.eq("2020-04")].iloc[0]
    assert row.dengue_cambio_1m == 11.0 - 5.0
    assert row.dengue_media_3m == pytest.approx((11.0 + 5.0 + 2.0) / 3)
    assert row.dengue_mean_lagged_3m == row.dengue_media_3m
    assert row.dengue_difference_lagged_1m == row.dengue_cambio_1m
    pd.testing.assert_frame_equal(now[design()["groups"]["B"]], stale[design()["groups"]["B"]])
    key = row.name
    assert stale.attrs["source_event_months"].loc[key, "dengue_cambio_1m"] == ("2020-03", "2020-02")
    assert stale.attrs["source_event_months"].loc[key, "dengue_media_3m"] == (
        "2020-03",
        "2020-02",
        "2020-01",
    )


def test_inventory_has_raw_sources_exact_offsets_and_unverified_publication():
    inventory = design()["inventory"]
    assert inventory["dengue_lag_1"]["source_columns"] == ["dengue_notifications_count"]
    assert inventory["dengue_lag_1"]["source_offsets"] == [-1]
    assert inventory["grave_lag_2"]["source_columns"] == ["dengue_grave_notifications_count"]
    assert inventory["grave_lag_2"]["source_offsets"] == [-2]
    assert inventory["dengue_mean_lagged_3m"]["source_offsets"] == [-1, -2, -3]
    assert inventory["dengue_media_3m"]["source_offsets"] == [0, -1, -2]
    zone = inventory["zona_canal_lag_1"]
    assert zone["source_columns"] == ["dengue_notifications_count"]
    assert zone["source_offsets"] == [-1, -13, -25, -37, -49, -61]
    assert zone["transform"] == "type7_historical_channel_zone"
    assert "P25/P50/P75" in zone["formula"]
    assert inventory["channel_excess_t"]["transform"] == "strict_historical_p75_excess_indicator"
    assert inventory["notification_log1p_oe_t"]["source_offsets"] == [0, -12, -24, -36, -48, -60]
    assert "sentinel0" in inventory["notification_log1p_oe_t"]["formula"]
    assert inventory["expected_zero_lag_1"]["source_offsets"] == zone["source_offsets"]
    target = inventory["channel_target_p75"]
    assert target["source_columns"] == ["dengue_notifications_count"]
    assert target["source_offsets"] == {
        "1": [-11, -23, -35, -47, -59],
        "2": [-10, -22, -34, -46, -58],
    }
    assert target["latest_event_offset_months"] == -10
    assert target["quantile"] == 0.75
    assert "<=T-1" in target["formula"]
    assert inventory["mes_sin"]["source_columns"] == ["forecast_origin_calendar_month"]
    assert inventory["mes_sin"]["transform"] == "calendar_sine"
    assert inventory["mes_cos"]["transform"] == "calendar_cosine"
    assert all(row["publication_availability_verified"] is False for row in inventory.values())
    assert all("unverified" in row["availability_policy"] for row in inventory.values())
    assert all(row["source_columns"] and row["source_offsets"] for row in inventory.values())


def test_reconstructed_zone_p25_boundary_matches_existing_channel_contract():
    p = panel().loc[lambda f: f.municipality_code.eq("50001")].copy()
    p["dengue_notifications_count"] = 0.0
    frame = prepare(p, {}, 1, allow_benchmark=True)
    # Covered0 with P25=P50=P75=0 belongs to SEGURIDAD, not EXITO.
    assert frame.loc[frame.year_month.eq("2020-01"), "zona_canal_t"].iloc[0] == "SEGURIDAD"
    assert frame.loc[frame.year_month.eq("2020-02"), "zona_canal_lag_1"].iloc[0] == "SEGURIDAD"


def test_profile_onset_count_distinguishes_missing_references_from_observed_zero():
    # Forty-eight raw months support a volume profile, but not even one onset
    # label when the required preceding five same-month years are unavailable.
    raw = pd.DataFrame(
        {
            "municipality_code": "50001",
            "year_month": pd.period_range("2015-01", "2018-12", freq="M").astype(str),
            "dengue_notifications_count": 1.0,
        }
    )
    insufficient_labels, _ = historical_profiles(raw, "2018-12")
    row = insufficient_labels.iloc[0]
    assert row.profile_covered_months == 48
    assert row.transmission_profile == "volume_tertiles_collapsed"
    assert row.profile_onset_evaluable_months == 0
    assert row.profile_onset_unknown_months == 60
    assert pd.isna(row.profile_historical_onsets)
    # Earlier reference observations make transitions genuinely evaluable; only
    # then is an observed zero-onset diagnostic justified.
    extended = pd.DataFrame(
        {
            "municipality_code": "50001",
            "year_month": pd.period_range("2011-01", "2018-12", freq="M").astype(str),
            "dengue_notifications_count": 1.0,
        }
    )
    known_labels, _ = historical_profiles(extended, "2018-12")
    known = known_labels.iloc[0]
    assert known.transmission_profile == row.transmission_profile
    assert known.profile_onset_evaluable_months == 35
    assert known.profile_onset_unknown_months == 25
    assert known.profile_historical_onsets == 0


def test_covered_onsets_include_events_outside_current_nonexcess_risk_set():
    p = panel().loc[lambda f: f.municipality_code.eq("50001")].copy()
    p["dengue_notifications_count"] = 1.0
    p.loc[p.year_month.isin(["2020-01", "2020-03"]), "dengue_notifications_count"] = 10.0
    prepared = prepare(p, {}, 2, allow_benchmark=True)
    january = prepared.loc[prepared.year_month.eq("2020-01")].iloc[0]
    # Origin excess is known, then Y(T+1)=0 and Y(T+2)=1: a covered future onset
    # that the declared Y(T)=0 primary issuance gate cannot forecast.
    assert january.current_excess == 1
    assert not january.eligible_at_t
    assert january.target_month == "2020-03"
    assert january.onset_target == 1
    window = next(w for w in design()["windows"] if w["id"] == "development_2020")
    ledger = exposure_table(role_parts(prepared, window))
    evaluation = ledger.loc[ledger.role.eq("evaluation")]
    assert evaluation.known_covered_onsets.sum() == 1
    assert evaluation.known_eligible_onsets.sum() == 0
    assert evaluation.monitored_exposure.sum() > evaluation.eligible_exposure.sum()


def test_group_coverage_reconciles_embargo_missingness_and_zero_retained_groups():
    frame = pd.DataFrame(
        {
            "municipality_code": ["50099", "50001", "50001", "50001", "73001", "73001"],
            "department_code": ["50", "50", "50", "50", "73", "73"],
            "transmission_profile": ["embargo_only", "low", "low", None, "high", "high"],
            "year_month": ["2019-11", "2019-11", "2019-12", "2020-01", "2020-02", "2020-03"],
            "target_month": ["2020-01", "2020-01", "2020-02", "2020-03", "2020-04", "2020-05"],
            "target_year": 2020,
            "current_excess": pd.Series([0, 0, 0, pd.NA, 0, 1], dtype="Int64"),
            "eligible_at_t": [True, True, True, False, True, False],
            "onset_target": pd.Series([1, 0, 1, 0, pd.NA, 1], dtype="Int64"),
            "excess_target": pd.Series([1, 0, 1, 0, pd.NA, 1], dtype="Int64"),
            "monitored": [True, True, True, False, False, True],
            "base_recipe": 1.0,
            "climate_recipe": [1.0, 1.0, np.nan, 1.0, 1.0, 1.0],
        }
    )
    window = next(w for w in design()["windows"] if w["id"] == "development_2020")
    part = role_parts(frame, window)["evaluation"]
    rows = coverage_groups(part, ["base_recipe"], ["base_recipe", "climate_recipe"])
    result = pd.DataFrame(rows)
    for _, group in result.groupby("dimension"):
        assert group.target_role_rows.sum() == 6
        assert group.embargo_excluded_rows.sum() == 2
        assert group.post_embargo_rows.sum() == 4
        assert group.unknown_current_state_rows.sum() == 1
        assert group.unknown_outcome_rows.sum() == 1
        assert group.ineligible_at_t_rows.sum() == 1
        assert group.known_covered_onsets.sum() == 2
        assert group.known_eligible_onsets.sum() == 1
        assert group.variant_complete_rows.sum() == 1
        assert group.common_complete_rows.sum() == 0
        assert group.common_abstentions.sum() == 1
        assert group.common_excluded_onsets.sum() == 1
        assert group.stage_counts_reconcile.all()
        assert group.eligibility_stage_reconciles.all()
        assert group.prediction_stage_reconciles.all()
        assert group.eligible_unknown_outcome_rows.sum() == 1
    lost = result.loc[result.dimension.eq("municipality_code") & result.group.eq("50099")].iloc[0]
    assert lost.target_role_rows == lost.embargo_excluded_rows == 1
    assert lost.post_embargo_rows == lost.known_eligible_onsets == 0
    lost_profile = result.loc[
        result.dimension.eq("transmission_profile") & result.group.eq("embargo_only")
    ].iloc[0]
    assert lost_profile.post_embargo_rows == 0
    missing = coverage_groups(part, ["base_recipe", "climate_recipe"])
    missing_municipality = next(
        r for r in missing if r["dimension"] == "municipality_code" and r["group"] == "50001"
    )
    assert missing_municipality["missing_predictors"]["climate_recipe"] == 1
    assert missing_municipality["variant_abstentions"] == 1
    unknown_profile = result.loc[
        result.dimension.eq("transmission_profile") & result.group.eq("unknown")
    ].iloc[0]
    assert unknown_profile.unknown_current_state_rows == 1


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


def test_stored_labels_are_reconstructed_and_post_cut_counts_do_not_change_profiles() -> None:
    panel, contract, _ = generated()
    before = prepare(panel, contract, 2)
    injected = panel.assign(onset_target=999, excess_target=999, zona_canal_t="EXCESO")
    after = prepare(injected, contract, 2)
    assert_frame_equal(before, after)
    before_profile, meta = historical_profiles(panel, "2018-12")
    panel.loc[panel.year_month.gt("2018-12"), "dengue_notifications_count"] = 10000.0
    after_profile, changed_meta = historical_profiles(panel, "2018-12")
    assert_frame_equal(before_profile, after_profile)
    assert meta == changed_meta
