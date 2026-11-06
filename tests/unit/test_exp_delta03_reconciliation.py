"""Generated-only scientific correspondence and composition controls; never fits."""

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data.exp_delta03_reconciliation import (
    composition_audit,
    exact_parity,
    grouped_counts,
    observed_event_union,
    residence_onset_counts,
)


def test_residence_and_onset_never_fall_back_to_occurrence_or_notification():
    raw = pd.DataFrame(
        {
            "COD_DPTO_R": ["5", "5", "5", ""],
            "COD_MUN_R": ["1", "1", "1", "1"],
            "COD_DPTO_O": ["73"] * 4,
            "COD_MUN_O": ["1"] * 4,
            "INI_SIN": ["31/12/2019", "01/01/2020", "", "01/01/2020"],
            "FEC_NOT": ["01/01/2020"] * 4,
        }
    )
    result = residence_onset_counts(raw)
    assert result.to_dict("records") == [
        {"municipality_code": "05001", "year_month": "2019-12", "count": 1},
        {"municipality_code": "05001", "year_month": "2020-01", "count": 1},
    ]


def test_full_key_parity_refuses_convenient_intersection_and_zero_substitution():
    expected = pd.DataFrame({"key": ["a", "b"], "value": [0, 1]})
    actual = pd.DataFrame({"key": ["a", "c"], "value": [None, 1]})
    result = exact_parity(expected, actual, ["key"], ["value"])
    assert result["expected_only"] == result["actual_only"] == 1
    assert result["value_mismatches"] == {"value": 1}
    assert not result["exact"]


def test_numeric_parity_does_not_infer_semantic_equivalence():
    frame = pd.DataFrame({"key": ["a", "b"], "value": [None, 0]})
    result = exact_parity(frame, frame.iloc[::-1], ["key"], ["value"])
    assert result["exact"]
    assert not result["semantic_equivalence_inferred"]


def test_parity_rejects_duplicate_keys():
    frame = pd.DataFrame({"key": ["a", "a"], "value": [0, 1]})
    with pytest.raises(ValueError, match="Duplicate"):
        exact_parity(frame, frame, ["key"], ["value"])


def test_parity_rejects_null_keys_instead_of_matching_them():
    frame = pd.DataFrame({"key": [None], "value": [1]})
    with pytest.raises(ValueError, match="Missing"):
        exact_parity(frame, frame, ["key"], ["value"])


def test_notification_aggregate_rejects_misalignment():
    with pytest.raises(ValueError, match="Unaligned"):
        grouped_counts(pd.Series(["05001"]), pd.Series(["2020-01"], index=[2]))


def test_observed_union_retains_raw_derived_keys_absent_from_published_fact():
    actual = observed_event_union(
        {"210": {("05001", "2020-01"): 3}, "220": {("73001", "2020-01"): 2}}
    )
    assert len(actual) == 2
    assert actual.notificados_210.tolist() == [3, 0]
    assert actual.notificados_220.tolist() == [0, 2]
    result = exact_parity(
        actual.iloc[:1], actual, ["municipality_code", "year_month"], ["notificados_210"]
    )
    assert not result["exact"] and result["actual_only"] == 1


def test_modis_audit_preserves_mosaic_zeros_and_annual_observation_unit():
    frame = pd.DataFrame({"divipola_municipio": ["05001"] * 2, "anio": [2020] * 2})
    parts = pd.DataFrame(
        {
            "natural": [60, 60],
            "crop": [10, 10],
            "urban": [5, 5],
            "other": [0, 0],
            "mosaic": [25, 25],
        }
    )
    report = composition_audit(frame, parts)
    assert report["annual_rows"] == report["complete_annual_rows"] == 1
    assert report["closure_failures"] == 0
    assert report["zero_annual_values"]["other"] == 1
    assert not report["predictive_encoding_selected"]
    assert "mosaic" in report["parts"]


def test_modis_audit_does_not_fill_missing_year_or_hide_bad_closure():
    frame = pd.DataFrame({"divipola_municipio": ["05001"] * 2, "anio": [2024, 2025]})
    parts = pd.DataFrame({c: [10, None] for c in ["natural", "crop", "urban", "other", "mosaic"]})
    report = composition_audit(frame, parts)
    assert report["complete_annual_rows"] == 1
    assert report["closure_failures"] == 1
    assert report["coverage_by_year"][-1]["complete"] == 0


def test_modis_audit_rejects_within_year_changes():
    frame = pd.DataFrame({"divipola_municipio": ["05001"] * 2, "anio": [2020] * 2})
    parts = pd.DataFrame({c: [20, 21] for c in ["natural", "crop", "urban", "other", "mosaic"]})
    with pytest.raises(ValueError, match="within"):
        composition_audit(frame, parts)


def test_modis_boundary_roundoff_is_distinct_from_physical_bound_failure():
    frame = pd.DataFrame({"divipola_municipio": ["05001"], "anio": [2020]})
    parts = pd.DataFrame(
        {"natural": [100 + 1e-12], "crop": [0], "urban": [0], "other": [0], "mosaic": [0]}
    )
    result = composition_audit(frame, parts)
    assert result["strict_boundary_roundoff_values"] == 1
    assert result["negative_or_above_100_beyond_tolerance"] == 0
    assert result["closure_failures"] == 0
