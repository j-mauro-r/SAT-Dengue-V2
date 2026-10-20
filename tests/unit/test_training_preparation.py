"""Synthetic rejection tests for preparation boundaries; no private inputs required."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.training_preparation.contract import (
    CONTRACT_PATH,
    PreparationConfig,
    PreparationError,
    read_json,
    validate_predictors,
)
from scripts.training_preparation.pipeline import fingerprint, prepare_inputs, read_panel
from scripts.training_preparation.validation import validate_panel, validate_roles

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def contract() -> dict[str, Any]:
    return read_json(ROOT / CONTRACT_PATH)


@pytest.fixture
def coverage() -> dict[str, Any]:
    return dict(
        panel_month_start="2020-01",
        panel_month_end="2020-03",
        epi_coverage_start_month="2020-01",
        epi_coverage_end_month="2020-03",
        climate_coverage_start_month="2020-01",
        climate_coverage_end_month="2020-03",
        scope_municipalities=2,
    )


@pytest.fixture
def panel(contract: dict[str, Any]) -> pd.DataFrame:
    rows = []
    for municipality in ("50001", "73001"):
        for period in pd.period_range("2020-01", "2020-03", freq="M"):
            row: dict[str, Any] = {}
            for field in contract["schema"]:
                dtype = field["dtype"].lower()
                row[field["name"]] = (
                    None
                    if field["nullable"]
                    else True
                    if dtype == "bool"
                    else 0
                    if dtype in ("float64", "int64")
                    else ""
                )
            row.update(
                municipality_code=municipality,
                department_code=municipality[:2],
                municipality_name="Synthetic",
                year_month=str(period),
                in_epi_coverage=True,
                epi_count_status="zero_in_coverage",
                expected_days_in_month=period.days_in_month,
                climate_days_observed=period.days_in_month,
            )
            for c in row:
                if c.endswith("_valid_days"):
                    row[c] = period.days_in_month
                    row[c.removesuffix("_valid_days")] = 1.0
            for h in (1, 2):
                row[f"target_period_t{h}"] = str(period + h)
                row[f"y_evaluable_t{h}"] = False
                row[f"y_status_t{h}"] = "insufficient_history"
            rows.append(row)
    frame = pd.DataFrame(rows)
    for field in contract["schema"]:
        dtype = field["dtype"].lower()
        if dtype in ("float64", "int64"):
            frame[field["name"]] = frame[field["name"]].astype(
                "Float64" if dtype == "float64" else "Int64"
            )
    return frame


def test_valid_input_is_not_mutated(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any]
) -> None:
    before = panel.copy(deep=True)
    report = validate_panel(panel, contract, coverage)
    assert report["rows"] == 6
    assert report["municipalities"] == 2
    pd.testing.assert_frame_equal(panel, before)


@pytest.mark.parametrize("fault", ["missing", "unexpected", "wrong_type", "null", "infinite"])
def test_bad_schema_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], fault: str
) -> None:
    if fault == "missing":
        panel = panel.drop(columns="year_month")
    elif fault == "unexpected":
        panel["future_count"] = 0
    elif fault == "wrong_type":
        panel["dengue_notifications_count"] = "1"
    elif fault == "null":
        panel.loc[0, "municipality_code"] = None
    else:
        panel.loc[0, "rain_mm_month_sum"] = float("inf")
    with pytest.raises(PreparationError):
        validate_panel(panel, contract, coverage)


def test_duplicate_keys_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any]
) -> None:
    with pytest.raises(PreparationError, match="Duplicate"):
        validate_panel(pd.concat([panel, panel.iloc[[0]]]), contract, coverage)


@pytest.mark.parametrize("removed", [[1], [0], [0, 1, 2]])
def test_month_gap_edge_and_missing_municipality_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], removed: list[int]
) -> None:
    with pytest.raises(PreparationError, match="support|coverage"):
        validate_panel(panel.drop(index=removed), contract, coverage)


@pytest.mark.parametrize(
    "column",
    [
        "y_t1",
        "y_t2",
        "target_period_t1",
        "p75_t2",
        "history_valid_years_t1",
        "y_evaluable_t2",
        "municipality_code",
        "total_notifications_count",
        "future_observed_dengue",
        "p75_canal_t",
    ],
)
def test_forbidden_predictors_rejected(contract: dict[str, Any], column: str) -> None:
    with pytest.raises(PreparationError, match="Forbidden"):
        validate_predictors([column], contract)


def test_edited_role_contract_cannot_admit_target(contract: dict[str, Any]) -> None:
    altered = copy.deepcopy(contract)
    altered["roles"]["predictors"].append("y_t1")
    with pytest.raises(PreparationError):
        validate_roles(altered)


@pytest.mark.parametrize(
    "column,value",
    [
        ("zona_canal_t", "unknown"),
        ("year_month", "2020-13"),
        ("in_epi_coverage", False),
        ("rain_mm_month_sum_valid_days", 2),
        ("y_t1", 1),
        ("target_period_t2", "2021-03"),
        ("dengue_notifications_count", -1),
        ("department_code", "50"),
    ],
)
def test_semantic_faults_rejected(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], column: str, value: Any
) -> None:
    panel.loc[5, column] = value
    with pytest.raises(PreparationError):
        validate_panel(panel, contract, coverage)


def test_read_csv_preserves_empty_traces_and_zero(
    panel: pd.DataFrame, contract: dict[str, Any], coverage: dict[str, Any], tmp_path: Path
) -> None:
    path = tmp_path / "panel.csv"
    panel.to_csv(path, index=False)
    restored = read_panel(path, contract)
    assert restored["history_periods_used_t1"].eq("").all()
    assert restored["dengue_notifications_count"].eq(0).all()
    assert restored["y_t1"].isna().all()
    validate_panel(restored, contract, coverage)
    path.write_text(path.read_text().replace("True", "garbage", 1))
    with pytest.raises(PreparationError, match="Invalid CSV"):
        read_panel(path, contract)


def test_reader_rejects_duplicate_header(tmp_path: Path, contract: dict[str, Any]) -> None:
    path = tmp_path / "panel.csv"
    path.write_text("municipality_code,municipality_code\n50001,50001\n")
    with pytest.raises(PreparationError, match="Duplicate CSV"):
        read_panel(path, contract)


def test_input_path_cannot_escape_repository(tmp_path: Path) -> None:
    with pytest.raises(PreparationError, match="outside repository"):
        PreparationConfig(tmp_path).resolve("../private.csv")


def test_code_only_notebook_delegates_without_consolidation() -> None:
    notebook = read_json(ROOT / "notebooks/04_training_preparation_pipeline.ipynb")
    assert all(c["cell_type"] == "code" for c in notebook["cells"])
    source = "".join("".join(c["source"]) for c in notebook["cells"])
    assert "prepare_inputs(config)" in source
    assert "stage2_consolidated_dataset_pipeline" not in source
    for cell in notebook["cells"]:
        compile("".join(cell["source"]), "notebook04", "exec")


def test_manifest_tamper_detected_before_parsing(tmp_path: Path, contract: dict[str, Any]) -> None:
    contract_path = tmp_path / CONTRACT_PATH
    contract_path.parent.mkdir(parents=True)
    contract_path.write_text(json.dumps(contract))
    panel_path = tmp_path / "data/processed/dengue_y_dengue_grave.csv"
    panel_path.parent.mkdir(parents=True)
    panel_path.write_text("synthetic\n")
    expected = fingerprint(panel_path)
    panel_path.write_text("tampered\n")
    manifest_path = tmp_path / PreparationConfig(tmp_path).manifest_path
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps(
            {
                "outputs": {
                    "dengue_y_dengue_grave": {
                        "path": str(panel_path.relative_to(tmp_path)),
                        **expected,
                    }
                }
            }
        )
    )
    with pytest.raises(PreparationError, match="fingerprint mismatch"):
        prepare_inputs(PreparationConfig(tmp_path))
