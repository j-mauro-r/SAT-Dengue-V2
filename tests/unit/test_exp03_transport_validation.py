"""Producer-shaped generated transport must pass semantic checks at both boundaries."""

from __future__ import annotations

import copy
import json
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
from test_exp03_benchmark import _coverage, _fixture
from test_exp03_reporting import generated_delivery

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_benchmark import ZERO_COUNTERS, _evaluate_frozen_grid
from sat_dengue.experiments.exp03_reporting import (
    _csv,
    _transport_summary,
    validate_bundle,
    write_bundle,
)
from sat_dengue.training_preparation.serialization import bytes_record


@pytest.fixture(scope="module")
def producer_rows() -> Iterator[list[dict[str, Any]]]:
    """Use actual generated-data inference and actual missing-coverage producer paths."""
    with TemporaryDirectory(dir="tmp", prefix="exp03-transport-regression-") as directory:
        root = Path(directory) / "terminal"
        panel, contract, design, specs, identity = _fixture(root)
        rows = []
        for coverage in (_coverage(), {}):
            result = _evaluate_frozen_grid(panel, contract, design, root, coverage, identity, specs)
            rows.extend(result["transport_2024_2025"])
        assert all("target_year" in row and "year" not in row for row in rows)
        yield rows


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


def test_valid_producer_transport_roundtrip(
    repo_tmp_path: Path, producer_rows: list[dict[str, Any]]
) -> None:
    result, provenance, design = generated_delivery()
    result["transport_2024_2025"] = producer_rows
    manifest = write_bundle(repo_tmp_path / "valid", result, provenance, design)
    assert validate_bundle(repo_tmp_path / "valid") == manifest
    assert {r.get("view", "annual") for r in producer_rows} == {
        "annual",
        "common_calendar_months",
        "count_pooled_descriptive",
    }
    assert any(r["status"] == "not_evaluable" and r["reason"] for r in producer_rows)


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


@pytest.mark.parametrize("boundary", ["write", "reload"])
@pytest.mark.parametrize(
    "kind", ["annual", "common_calendar_months", "count_pooled_descriptive", "not_evaluable"]
)
@pytest.mark.parametrize("field,value,match", MUTATIONS)
def test_invalid_native_transport_rejected(
    repo_tmp_path: Path,
    producer_rows: list[dict[str, Any]],
    boundary: str,
    kind: str,
    field: str,
    value: Any,
    match: str,
) -> None:
    rows = copy.deepcopy(producer_rows)
    row = next(
        r
        for r in rows
        if (
            r["status"] == "not_evaluable" and r["target_year"] == 2025
            if kind == "not_evaluable"
            else r.get("view") == kind and r["target_year"] in (2025, "2024-2025")
        )
    )
    result, provenance, design = generated_delivery()
    result["transport_2024_2025"] = rows
    root = repo_tmp_path / "bundle"
    if boundary == "reload":
        write_bundle(root, result, provenance, design)
    if value == "__absent__":
        row.pop(field)
    else:
        row[field] = value
    with pytest.raises(ValueError, match=match):
        if boundary == "write":
            write_bundle(root, result, provenance, design)
        else:
            rewrite_native_transport(root, rows)
            validate_bundle(root)


@pytest.mark.parametrize("period", [2024, 2025, "2024-2025"])
@pytest.mark.parametrize("boundary", ["write", "reload"])
def test_alias_normalization_and_legacy_year_only_rejection(
    repo_tmp_path: Path, producer_rows: list[dict[str, Any]], period: Any, boundary: str
) -> None:
    result, provenance, design = generated_delivery()
    row = copy.deepcopy(next(r for r in producer_rows if r["target_year"] == period))
    row.update(target_year=str(period), year=period)
    result["transport_2024_2025"] = [row]
    root = repo_tmp_path / "alias"
    manifest = write_bundle(root, result, provenance, design)
    assert validate_bundle(root) == manifest
    del row["target_year"]
    with pytest.raises(ValueError, match="temporal identity"):
        if boundary == "write":
            write_bundle(repo_tmp_path / "legacy", result, provenance, design)
        else:
            rewrite_native_transport(root, [row])
            validate_bundle(root)


@pytest.mark.parametrize("boundary", ["write", "reload"])
@pytest.mark.parametrize(
    "field,value,match",
    [
        ("evidence_type", "consumed_retrospective_benchmark", "labelled"),
        ("model_fits", 1, "zero"),
        ("target_months", ["2025-01"], "temporal identity"),
        ("view", "count_pooled_descriptive", "view"),
    ],
)
def test_stress_identity_is_distinct(
    repo_tmp_path: Path,
    producer_rows: list[dict[str, Any]],
    boundary: str,
    field: str,
    value: Any,
    match: str,
) -> None:
    result, provenance, design = generated_delivery()
    row = copy.deepcopy(next(r for r in producer_rows if r["target_year"] == 2024))
    result["transport_2024_2025"] = [row]
    root = repo_tmp_path / "stress"
    if boundary == "reload":
        write_bundle(root, result, provenance, design)
    row[field] = value
    with pytest.raises(ValueError, match=match):
        if boundary == "write":
            write_bundle(root, result, provenance, design)
        else:
            rewrite_native_transport(root, [row])
            validate_bundle(root)
