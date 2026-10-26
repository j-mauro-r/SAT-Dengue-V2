"""R1 regressions using generated manifests; never load private source contents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp01_inputs_fixture import generated_panel, write_sources
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.contract import PreparationError
from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint, prepare_inputs
from sat_dengue.experiments.exp01 import load_protocol, prepare
from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs
from sat_dengue.experiments.onset import partitions


def test_legacy_values_never_affect_admission_or_prepared_science(repo_tmp_path: Path) -> None:
    source = generated_panel()
    baseline = prepare_exp01_inputs(write_sources(repo_tmp_path / "baseline", source))
    controls = set(baseline.report["validated_controls"])
    ignored = set(source) - set(baseline.panel) - controls
    assert {"y_t1", "y_t2", "zona_canal_t", "p75_canal_t", "p75_t2"} <= ignored
    for number, value in enumerate(("", "invalid-unused-value", "999")):
        changed = source.copy()
        for name in ignored:
            changed[name] = value
        actual = prepare_exp01_inputs(write_sources(repo_tmp_path / str(number), changed))
        assert_frame_equal(actual.panel, baseline.panel)
        assert actual.report["input_fingerprints"] != baseline.report["input_fingerprints"]
        for h in (1, 2):
            assert_frame_equal(
                prepare(actual.panel, actual.contract, h),
                prepare(baseline.panel, baseline.contract, h),
            )
    assert not (set(baseline.panel) & controls)


def test_integrity_is_not_bypassed_for_unused_fields(repo_tmp_path: Path) -> None:
    source = generated_panel("2024-01", "2024-12")
    config = write_sources(repo_tmp_path, source)
    path = config.resolve("data/processed/panel_mensual_dengue_clima.csv")
    source["y_t1"] = "altered without refreshing manifest"
    source.to_csv(path, index=False)
    with pytest.raises(PreparationError, match="fingerprint mismatch"):
        prepare_exp01_inputs(config)


@pytest.mark.parametrize(
    "fault",
    [
        "predictor",
        "missing",
        "key",
        "calendar",
        "duplicate",
        "category",
        "coverage",
        "population",
        "days",
    ],
)
def test_consumed_inputs_still_fail_closed(repo_tmp_path: Path, fault: str) -> None:
    source = generated_panel("2024-01", "2024-12")
    if fault == "predictor":
        source["rain_mm_month_sum"] = "invalid"
    elif fault == "missing":
        source = source.drop(columns="rain_mm_month_sum")
    elif fault == "key":
        source.loc[0, "municipality_code"] = "invalid"
    elif fault == "calendar":
        source.loc[0, "year_month"] = "invalid"
    elif fault == "duplicate":
        source = pd.concat([source, source.iloc[:1]], ignore_index=True)
    elif fault == "category":
        source["epi_count_status"] = "invalid"
    elif fault == "coverage":
        source = source.drop(index=3)
    elif fault == "population":
        source.loc[source.municipality_code.eq("73001"), "municipality_code"] = "73002"
    elif fault == "days":
        source["rain_mm_month_sum_valid_days"] = -1
    config = write_sources(repo_tmp_path, source)
    with pytest.raises(PreparationError):
        prepare_exp01_inputs(config)


def test_future_rows_are_excluded_before_predictor_typing_and_late_history_stays(
    repo_tmp_path: Path,
) -> None:
    source = generated_panel()
    source["rain_mm_month_sum"] = source.rain_mm_month_sum.astype(object)
    source.loc[source.year_month.ge("2025-01"), "rain_mm_month_sum"] = "invalid future predictor"
    result = prepare_exp01_inputs(write_sources(repo_tmp_path, source))
    assert result.panel.year_month.max() == "2024-12"
    assert len(result.panel.loc[result.panel.year_month.isin(["2024-11", "2024-12"])]) == 4
    for h in (1, 2):
        cohort = prepare(result.panel, result.contract, h)
        for window in load_protocol()["design"]["windows"]:
            for frame in partitions(cohort, window).values():
                assert frame.target_month.lt("2025-01").all()


def test_nullable_predictor_keeps_approved_missingness(repo_tmp_path: Path) -> None:
    source = generated_panel("2024-01", "2024-12")
    source.loc[0, "rain_mm_month_sum"] = None
    source.loc[0, "rain_mm_month_sum_valid_days"] = 0
    result = prepare_exp01_inputs(write_sources(repo_tmp_path, source))
    assert pd.isna(result.panel.loc[0, "rain_mm_month_sum"])
    assert len(result.panel) == len(source)


def test_historical_loader_still_validates_legacy_values(repo_tmp_path: Path) -> None:
    source = generated_panel("2024-01", "2024-12")
    config = write_sources(repo_tmp_path, source)
    original = prepare_inputs(config)
    assert "y_t1" in original.panel and len(original.panel.columns) == len(source.columns)
    source["y_t1"] = "invalid historical target"
    config = write_sources(repo_tmp_path, source)
    assert prepare_exp01_inputs(config).report["status"] == "PASS"
    with pytest.raises(PreparationError, match="y_t1"):
        prepare_inputs(config)


@pytest.mark.parametrize("fault", ["output_path", "schema", "dimensions"])
def test_manifest_and_contract_checks_remain_required(repo_tmp_path: Path, fault: str) -> None:
    config = write_sources(repo_tmp_path, generated_panel("2024-01", "2024-12"))
    manifest_path = config.resolve(config.manifest_path)
    manifest: dict[str, Any] = json.loads(manifest_path.read_text())
    if fault == "output_path":
        manifest["outputs"]["panel_mensual_dengue_clima"]["path"] = "../outside.csv"
    elif fault == "dimensions":
        manifest["outputs"]["panel_mensual_dengue_clima"]["rows"] += 1
    else:
        record = manifest["outputs"]["candidate_contract"]
        path = config.resolve(record["path"])
        path.write_text(json.dumps({"datasets": {"panel_mensual_dengue_clima": {"schema": []}}}))
        record.update(fingerprint(path))
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(PreparationError):
        prepare_exp01_inputs(config)
