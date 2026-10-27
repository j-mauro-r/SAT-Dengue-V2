"""Generated-source tests for the separate, guarded consumed-2025 raw adapter."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp01_inputs_fixture import ROOT, generated_panel, write_sources

from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig, PreparationError
from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs
from sat_dengue.experiments.exp03_inputs import prepare_benchmark_inputs

READY = {
    "governed_coverage": True,
    "maturity_verified": True,
    "provenance_sha256": "generated-fixture-provenance",
}


def _codes() -> list[str]:
    """Only the public municipality inventory is read; every scientific value is generated."""
    result: list[str] = []
    for department in ("meta", "tolima"):
        fixture = json.loads(
            (ROOT / f"scripts/read_only_api/fixtures/dashboard_{department}.json").read_text()
        )
        result.extend(row["municipality_code"] for row in fixture["municipalities"])
    return result


def _panel(end: str = "2025-12") -> pd.DataFrame:
    base = generated_panel("2024-11", end)
    base = base.loc[base.municipality_code.eq("50001")]
    return pd.concat(
        [base.assign(municipality_code=code, department_code=code[:2]) for code in _codes()],
        ignore_index=True,
    )


def _sources(root: Path, panel: pd.DataFrame) -> PreparationConfig:
    config = write_sources(root, panel)
    manifest_path = config.resolve(config.manifest_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["coverage"]["scope_municipalities"] = 76
    manifest_path.write_text(json.dumps(manifest))
    config.resolve("data/sources/Divipola-municipios.md").write_text(
        json.dumps(
            {
                "resultado": [
                    {"CODIGO_DPTO_MPIO": code, "CODIGO_DEPARTAMENTO": code[:2]} for code in _codes()
                ]
            }
        )
    )
    return config


@pytest.mark.parametrize(
    "metadata",
    [
        {},
        {**READY, "governed_coverage": False},
        {**READY, "maturity_verified": False},
        {**READY, "maturity_verified": "true"},
        {**READY, "provenance_sha256": ""},
    ],
)
def test_unverified_metadata_blocks_before_any_source_read(
    metadata: dict[str, Any],
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("unverified readiness reached source access")

    monkeypatch.setattr("sat_dengue.experiments.exp03_inputs.verified_sources", forbidden)
    monkeypatch.setattr(PreparationConfig, "resolve", forbidden)
    with pytest.raises(PermissionError, match="private reads forbidden"):
        prepare_benchmark_inputs(PreparationConfig(repo_tmp_path), metadata)


def test_raw2025_admitted_without_changing_historical_exp01_boundary(repo_tmp_path: Path) -> None:
    source = _panel()
    config = _sources(repo_tmp_path, source)
    benchmark = prepare_benchmark_inputs(config, READY)
    historical = prepare_exp01_inputs(config)
    assert benchmark.panel.year_month.max() == "2025-12"
    assert historical.panel.year_month.max() == "2024-12"
    assert benchmark.report["municipalities"] == 76
    assert benchmark.report["full_2025_calendar_coverage"]
    assert benchmark.report["evidence_type"] == "consumed_retrospective_benchmark"
    assert benchmark.report["coverage_provenance_sha256"] == READY["provenance_sha256"]
    assert not {"zona_canal_t", "y_t1", "y_t2", "in_epi_coverage"}.intersection(benchmark.panel)
    assert "data/sources/Divipola-municipios.md" in benchmark.report["input_fingerprints"]


def test_supplied_future_labels_channels_and_later_predictors_are_not_consumed(
    repo_tmp_path: Path,
) -> None:
    source = _panel("2026-01")
    first = prepare_benchmark_inputs(_sources(repo_tmp_path / "first", source), READY)
    ignored = set(source) - set(first.panel) - set(first.report["validated_controls"])
    source[list(ignored)] = "invalid supplied target or reconstructed-channel value"
    source["rain_mm_month_sum"] = source.rain_mm_month_sum.astype(object)
    source.loc[source.year_month.eq("2026-01"), "rain_mm_month_sum"] = "unused future value"
    second = prepare_benchmark_inputs(_sources(repo_tmp_path / "second", source), READY)
    pd.testing.assert_frame_equal(first.panel, second.panel)
    assert first.report["input_fingerprints"] != second.report["input_fingerprints"]


@pytest.mark.parametrize("fault", ["2025_predictor", "days", "count", "duplicate", "scope"])
def test_consumed2025_values_and_governed_scope_remain_validated(
    fault: str,
    repo_tmp_path: Path,
) -> None:
    source = _panel()
    if fault == "2025_predictor":
        source["rain_mm_month_sum"] = source.rain_mm_month_sum.astype(object)
        source.loc[source.year_month.eq("2025-12"), "rain_mm_month_sum"] = "invalid consumed value"
    elif fault == "days":
        source.loc[source.year_month.eq("2025-12"), "rain_mm_month_sum_valid_days"] = -1
    elif fault == "count":
        source.loc[source.year_month.eq("2025-12"), "total_notifications_count"] = -1
    elif fault == "duplicate":
        source = pd.concat([source, source.iloc[:1]], ignore_index=True)
    elif fault == "scope":
        source = source.loc[source.municipality_code.ne("50001")]
    with pytest.raises(PreparationError):
        prepare_benchmark_inputs(_sources(repo_tmp_path, source), READY)


def test_byte_tamper_cannot_hide_in_unused_targets(repo_tmp_path: Path) -> None:
    source = _panel()
    config = _sources(repo_tmp_path, source)
    path = config.resolve("data/processed/panel_mensual_dengue_clima.csv")
    source["y_t2"] = "tampered after manifest fingerprint"
    source.to_csv(path, index=False)
    with pytest.raises(PreparationError, match="fingerprint mismatch"):
        prepare_benchmark_inputs(config, READY)


def test_incomplete_calendar_is_reported_without_inventing_maturity(repo_tmp_path: Path) -> None:
    result = prepare_benchmark_inputs(_sources(repo_tmp_path, _panel("2025-06")), READY)
    assert result.report["end"] == "2025-06"
    assert not result.report["full_2025_calendar_coverage"]
    assert "UNPROVEN" in result.report["operational_historical_availability"]
