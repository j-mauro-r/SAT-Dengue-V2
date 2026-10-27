"""Transport rule coverage separated from native bundle boundary coverage."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from exp03_benchmark_fixture import _coverage, _fixture
from exp03_reporting_fixture import generated_delivery

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_benchmark import ZERO_COUNTERS, _evaluate_frozen_grid
from sat_dengue.experiments.exp03_reporting import (
    _csv,
    _transport_summary,
    _validate_transport,
    validate_bundle,
    write_bundle,
)
from sat_dengue.training_preparation.serialization import bytes_record


def annual_row() -> dict[str, Any]:
    return {
        "target_year": 2025,
        "view": "annual",
        "target_months": ["2025-01"],
        "evidence_type": "consumed_retrospective_benchmark",
        **ZERO_COUNTERS,
    }


def rewrite_native_transport(root: Path, rows: list[dict[str, Any]]) -> None:
    """Re-sign synthetic native payloads so reload must reach semantic validation."""
    result = json.loads((root / "result.json").read_text())
    result["transport_2024_2025"] = rows
    payloads = {
        "result.json": canonical_bytes(result),
        "transport_2024_2025.csv": _csv(rows),
        "transport_summary.csv": _csv(_transport_summary(rows)),
    }
    manifest = json.loads((root / "manifest.json").read_text())
    for name, payload in payloads.items():
        (root / name).write_bytes(payload)
        manifest["files"][name] = bytes_record(payload)
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    manifest["bundle_id"] = digest(body)
    (root / "manifest.json").write_bytes(canonical_bytes(manifest))
    assert manifest["bundle_id"] == digest(body)
    assert all(
        record == bytes_record((root / name).read_bytes())
        for name, record in manifest["files"].items()
    )


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


@pytest.fixture
def producer_rows(repo_tmp_path: Path) -> list[dict[str, Any]]:
    root = repo_tmp_path / "terminal"
    panel, contract, design, specs, identity = _fixture(root)
    rows = []
    for coverage in (_coverage(), {}):
        rows.extend(
            _evaluate_frozen_grid(panel, contract, design, root, coverage, identity, specs)[
                "transport_2024_2025"
            ]
        )
    assert all("target_year" in row and "year" not in row for row in rows)
    return rows


def test_valid_producer_transport_roundtrip(
    repo_tmp_path: Path, producer_rows: list[dict[str, Any]]
) -> None:
    result, provenance, design = generated_delivery()
    result["transport_2024_2025"] = producer_rows
    root = repo_tmp_path / "valid"
    manifest = write_bundle(root, result, provenance, design)
    assert validate_bundle(root) == manifest
    assert {r.get("view", "annual") for r in producer_rows} == {
        "annual",
        "common_calendar_months",
        "count_pooled_descriptive",
    }
    assert any(r["status"] == "not_evaluable" and r["reason"] for r in producer_rows)


@pytest.mark.parametrize("boundary", ["write", "reload"])
def test_invalid_producer_transport_is_rejected_at_both_boundaries(
    repo_tmp_path: Path,
    producer_rows: list[dict[str, Any]],
    boundary: str,
) -> None:
    result, provenance, design = generated_delivery()
    rows = copy.deepcopy(producer_rows)
    result["transport_2024_2025"] = rows
    root = repo_tmp_path / "bundle"
    if boundary == "reload":
        write_bundle(root, result, provenance, design)
    row = next(r for r in rows if r["target_year"] == 2025 and r.get("view") == "annual")
    row.update(evidence_type="prospective_confirmation", model_fits=99)
    with pytest.raises(ValueError, match="labelled"):
        if boundary == "write":
            write_bundle(root, result, provenance, design)
        else:
            rewrite_native_transport(root, rows)
            validate_bundle(root)
