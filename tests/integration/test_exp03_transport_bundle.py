"""Generated native-estimator integration; source-free and isolated."""

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
from sat_dengue.experiments.exp03_benchmark import _evaluate_frozen_grid
from sat_dengue.experiments.exp03_reporting import (
    _csv,
    _transport_summary,
    validate_bundle,
    write_bundle,
)
from sat_dengue.training_preparation.serialization import bytes_record


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
