"""Transport rule coverage separated from native bundle boundary coverage."""

from __future__ import annotations

from typing import Any

import pytest

from sat_dengue.experiments.exp03_benchmark import ZERO_COUNTERS
from sat_dengue.experiments.exp03_reporting import (
    _validate_transport,
)


def annual_row() -> dict[str, Any]:
    return {
        "target_year": 2025,
        "view": "annual",
        "target_months": ["2025-01"],
        "evidence_type": "consumed_retrospective_benchmark",
        **ZERO_COUNTERS,
    }


MUTATIONS = [
    ("evidence_type", "prospective_confirmation", "labelled"),
    ("target_year", "__absent__", "temporal identity"),
    ("target_year", None, "temporal identity"),
    ("target_year", "", "temporal identity"),
    ("target_year", "2025.0", "temporal identity"),
    ("target_year", True, "temporal identity"),
    ("target_year", 2025.0, "temporal identity"),
    ("target_year", 2023, "temporal identity"),
    ("year", 2024, "Conflicting"),
    ("year", "garbage", "temporal identity"),
    ("view", "unknown", "view"),
    ("target_months", ["2023-01"], "temporal identity"),
    ("target_months", ["2025-13"], "temporal identity"),
    ("target_months", None, "temporal identity"),
    *[
        (key, value, "zero")
        for key in ZERO_COUNTERS
        for value in (99, "__absent__", None, False, "0", 0.5)
    ],
]


@pytest.mark.parametrize("field,value,match", MUTATIONS)
def test_transport_rule_rejects_invalid_value(field: str, value: Any, match: str) -> None:
    row = annual_row()
    if value == "__absent__":
        row.pop(field)
    else:
        row[field] = value
    with pytest.raises(ValueError, match=match):
        _validate_transport(row)


@pytest.mark.parametrize(
    "kind", ["annual", "common_calendar_months", "count_pooled_descriptive", "not_evaluable"]
)
def test_record_classes_share_evidence_and_counter_rules(kind: str) -> None:
    row = annual_row()
    if kind == "not_evaluable":
        row.update(status="not_evaluable", reason="generated_missing_coverage", target_months=[])
    else:
        row["view"] = kind
    if kind == "count_pooled_descriptive":
        row.update(target_year="2024-2025", evidence_type="descriptive_consumed_2024_2025_context")
    _validate_transport(row)
    row["evidence_type"] = "prospective_confirmation"
    with pytest.raises(ValueError, match="labelled"):
        _validate_transport(row)
    row["evidence_type"] = (
        "descriptive_consumed_2024_2025_context"
        if kind == "count_pooled_descriptive"
        else "consumed_retrospective_benchmark"
    )
    row["model_fits"] = 99
    with pytest.raises(ValueError, match="zero"):
        _validate_transport(row)


@pytest.mark.parametrize("period", [2024, 2025, "2024-2025"])
def test_period_alias_normalization_and_legacy_rejection(period: Any) -> None:
    row = annual_row()
    row.update(target_year=str(period), year=period, target_months=[])
    row["evidence_type"] = {
        2024: "retrospective_stress",
        2025: "consumed_retrospective_benchmark",
        "2024-2025": "descriptive_consumed_2024_2025_context",
    }[period]
    if period == "2024-2025":
        row["view"] = "count_pooled_descriptive"
    _validate_transport(row)
    del row["target_year"]
    with pytest.raises(ValueError, match="temporal identity"):
        _validate_transport(row)


@pytest.mark.parametrize(
    "field,value,match",
    [
        ("evidence_type", "consumed_retrospective_benchmark", "labelled"),
        ("model_fits", 1, "zero"),
        ("target_months", ["2025-01"], "temporal identity"),
        ("view", "count_pooled_descriptive", "view"),
    ],
)
def test_stress_identity_remains_distinct(field: str, value: Any, match: str) -> None:
    row = annual_row()
    row.update(target_year=2024, evidence_type="retrospective_stress", target_months=["2024-01"])
    _validate_transport(row)
    row[field] = value
    with pytest.raises(ValueError, match=match):
        _validate_transport(row)
