"""Engineering fixtures only; never evidence of private-data coverage or parity."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DataCatalog, DatasetError, MemoryDataset
from kedro.runner import SequentialRunner
from pandas.testing import assert_frame_equal  # type: ignore[import-untyped]

from sat_dengue.canonical.table import (
    CHANNEL,
    CLIMATE,
    COUNTS,
    KEYS,
    build_table,
    coverage_report,
    predictor_matrix,
)
from sat_dengue.config_loader import CATALOG, ValidatedConfigLoader
from sat_dengue.configuration import CANONICAL_AUTHORITY, canonical_bytes, validate_parameters
from sat_dengue.data.consolidation import (
    compute_current_endemic_channel,
    compute_schema_contract,
    compute_y_labels,
)
from sat_dengue.datasets import canonical as datasets
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS = {"profile": "canonical_model_table_v1", "tracking": "disabled"}


@pytest.fixture
def panel() -> pd.DataFrame:
    periods = pd.period_range("2015-01", "2022-12", freq="M")
    rows = []
    for code in ("50001", "73001"):
        for i, period in enumerate(periods):
            count = float(i % 17)
            row = {
                "municipality_code": code,
                "department_code": code[:2],
                "municipality_name": "Engineering fixture",
                "year_month": str(period),
                COUNTS[0]: count,
                COUNTS[1]: 0.0,
                COUNTS[2]: count,
                "in_epi_coverage": True,
                "epi_count_status": "zero_in_coverage" if count == 0 else "records_present",
                "expected_days_in_month": period.days_in_month,
                "climate_days_observed": period.days_in_month,
            }
            for name in CLIMATE:
                row[name] = -0.7 if "evaporation" in name else 3.0
                row[f"{name}_valid_days"] = period.days_in_month
            rows.append(row)
    frame, _, _ = compute_current_endemic_channel(pd.DataFrame(rows))
    frame, _ = compute_y_labels(frame)
    return frame


def test_preserves_source_roles_climate_and_reproducible_bytes(panel: pd.DataFrame) -> None:
    table, schema = build_table(panel.sample(frac=1, random_state=2))
    assert not table.duplicated(KEYS).any()
    assert_frame_equal(table[list(panel)], panel)
    assert table[CLIMATE].equals(panel[CLIMATE])
    assert table["total_evaporation_mm_month_sum_ecmwf"].lt(0).all()
    matrix = predictor_matrix(table, schema)
    assert not set(matrix) & {"y_t1", "y_t2", "y_evaluable_t1", "y_status_t1", "p75_t1"}
    assert set(CLIMATE) <= set(matrix)
    assert set(CHANNEL) <= set(matrix)
    assert {c["name"] for c in schema["columns"]} == set(table)
    first = datasets.assemble_canonical(_sources(panel), PARAMETERS)
    second = datasets.assemble_canonical(_sources(panel.sample(frac=1)), PARAMETERS)
    assert first["payloads"] == second["payloads"]


def _sources(panel: pd.DataFrame) -> dict[str, Any]:
    return {
        "panel": panel,
        "contract": json.loads((ROOT / CANONICAL_AUTHORITY["path"]).read_text()),
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }


def test_future_changes_cannot_change_origin_predictors(panel: pd.DataFrame) -> None:
    original, schema = build_table(panel)
    changed = panel.copy()
    future = changed["year_month"].gt("2020-12")
    changed.loc[future, COUNTS[0]] = 9999.0
    changed.loc[future, COUNTS[2]] = 9999.0
    changed.loc[future, "epi_count_status"] = "records_present"
    changed.loc[future, CLIMATE] = 123.0
    changed, _, _ = compute_current_endemic_channel(changed)
    changed, _ = compute_y_labels(changed)
    updated, _ = build_table(changed)
    earlier = original["year_month"].le("2020-12")
    assert_frame_equal(
        predictor_matrix(original, schema).loc[earlier],
        predictor_matrix(updated, schema).loc[earlier],
    )
    assert not original.loc[earlier, "y_t1"].equals(updated.loc[earlier, "y_t1"])


def test_thresholds_independent_of_future_and_missing_exact_history(panel: pd.DataFrame) -> None:
    table, _ = build_table(panel)
    row = table.loc[(table.municipality_code == "50001") & (table.year_month == "2022-12")].iloc[0]
    assert pd.isna(row.p75_t1)  # Source gates it on unavailable future observation.
    assert pd.notna(row.p75_h5_t1)
    assert row.history_valid_years_h5_t1 == 5
    expected = panel.loc[
        (panel.municipality_code == "50001")
        & panel.year_month.isin([f"{y}-01" for y in range(2018, 2023)]),
        COUNTS[0],
    ]
    assert row.p25_h5_t1 == expected.quantile(0.25)
    # Removing a required calendar month must not substitute an older year.
    sparse = panel.loc[
        ~((panel.municipality_code == "50001") & (panel.year_month == "2020-01"))
    ].drop(columns=CHANNEL)
    sparse_table, _ = build_table(sparse)
    row = sparse_table.loc[
        (sparse_table.municipality_code == "50001") & (sparse_table.year_month == "2022-12")
    ].iloc[0]
    assert pd.isna(row.p75_h5_t1)
    assert row.history_valid_years_h5_t1 == 4
    # Row shifts would silently pick the wrong month across this gap.
    after_gap = sparse_table.loc[
        (sparse_table.municipality_code == "50001") & (sparse_table.year_month == "2020-02")
    ].iloc[0]
    assert pd.isna(after_gap.dengue_notifications_count_lag1)


def test_missing_is_preserved_and_not_observed_zero(panel: pd.DataFrame) -> None:
    frame = panel.drop(columns=CHANNEL).copy()
    frame.loc[0, COUNTS] = float("nan")
    frame.loc[0, "in_epi_coverage"] = False
    frame.loc[0, "epi_count_status"] = "outside_epi_coverage_missing"
    frame.loc[0, CLIMATE] = float("nan")
    frame.loc[0, [f"{c}_valid_days" for c in CLIMATE]] = 0
    table, schema = build_table(frame)
    assert table.loc[0, COUNTS].isna().all()
    assert table.loc[0, CLIMATE].isna().all()
    assert table.loc[17, COUNTS[0]] == 0
    coverage = coverage_report(table, schema)
    assert coverage["departments"]["Meta"]["missing_epi_rows"] == 1
    assert coverage["departments"]["Meta"]["observed_zero_rows"] > 0
    only_meta = table.loc[table.department_code == "50"]
    assert coverage_report(only_meta, schema)["departments"]["Tolima"]["status"] == "UNAVAILABLE"


@pytest.mark.parametrize(
    "mutation",
    ["duplicate", "code", "period", "coverage", "status", "negative", "climate", "channel"],
)
def test_invalid_source_fails_closed(panel: pd.DataFrame, mutation: str) -> None:
    if mutation == "duplicate":
        panel = pd.concat([panel, panel.iloc[:1]], ignore_index=True)
    elif mutation == "code":
        panel.loc[0, "municipality_code"] = "1"
    elif mutation == "period":
        panel.loc[0, "year_month"] = "2020-13"
    elif mutation == "coverage":
        panel.loc[0, COUNTS[0]] = float("nan")
    elif mutation == "status":
        panel.loc[0, "epi_count_status"] = "records_present"
    elif mutation == "negative":
        panel.loc[0, COUNTS[0]] = -1.0
    elif mutation == "climate":
        panel.loc[0, f"{CLIMATE[0]}_valid_days"] = 2
    else:
        panel.loc[80, "p75_canal_t"] = -1.0
    with pytest.raises(ValueError):
        build_table(panel)


def test_role_tampering_cannot_select_future_targets(panel: pd.DataFrame) -> None:
    table, schema = build_table(panel)
    schema = copy.deepcopy(schema)
    schema["column_roles"]["feature"].append("y_t1")
    with pytest.raises(ValueError, match="roles changed"):
        predictor_matrix(table, schema)


def test_configuration_catalog_and_independent_graph() -> None:
    loader = ValidatedConfigLoader(
        str(ROOT / "conf"), base_env="base", default_run_env="base", runtime_params=PARAMETERS
    )
    assert loader["catalog"] == CATALOG
    assert loader["parameters"] == PARAMETERS
    graph = register_pipelines()["canonical_model_table_v1"]
    assert graph.inputs() == {"canonical_stage2_sources", "parameters"}
    assert graph.outputs() == {"canonical_model_table_v1"}
    for runtime in (
        {**PARAMETERS, "tracking": "enabled"},
        {**PARAMETERS, "experiment_id": "EXP01"},
        {**PARAMETERS, "seed": 1},
    ):
        with pytest.raises(ValueError):
            validate_parameters(runtime)


def test_runner_atomic_publication_and_tamper_detection(
    panel: pd.DataFrame, repo_tmp_path: Path
) -> None:
    dataset = datasets.CanonicalBundleDataset(str(repo_tmp_path))
    with pytest.raises(DatasetError, match="No explicit"):
        dataset.load()
    catalog = DataCatalog(
        {
            "canonical_stage2_sources": MemoryDataset(_sources(panel)),
            "parameters": MemoryDataset(PARAMETERS),
            "canonical_model_table_v1": dataset,
        }
    )
    SequentialRunner().run(register_pipelines()["canonical_model_table_v1"], catalog)
    receipt = dataset.load()
    folder = ROOT / receipt["path"]
    assert list(folder.glob("*.csv")) == [folder / "canonical_model_table_v1.csv"]
    payload = datasets.assemble_canonical(_sources(panel), PARAMETERS)
    with pytest.raises(DatasetError, match="replacement is forbidden"):
        dataset.save(payload)
    assert dataset.load() == receipt
    csv = folder / "canonical_model_table_v1.csv"
    csv.chmod(0o644)
    csv.write_text("corrupted")
    with pytest.raises(DatasetError, match="payload changed"):
        dataset.load()


@pytest.fixture
def native_fixture(
    panel: pd.DataFrame, repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Path:
    # Explicit fixture pins; never substitute these for protected private evidence.
    construction = compute_schema_contract([], panel, version="candidate-construction-v1")
    for relative, payload in {
        datasets.PANEL: panel.to_csv(index=False).encode(),
        datasets.CONSTRUCTION: canonical_bytes(construction),
        CANONICAL_AUTHORITY["path"]: (ROOT / CANONICAL_AUTHORITY["path"]).read_bytes(),
    }.items():
        path = repo_tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    manifest = {
        "outputs": {
            "panel_mensual_dengue_clima": {
                "path": datasets.PANEL,
                "rows": len(panel),
                "columns": len(panel.columns),
                **datasets.identity(repo_tmp_path / datasets.PANEL),
            }
        }
    }
    path = repo_tmp_path / datasets.NATIVE_MANIFEST
    path.write_bytes(canonical_bytes(manifest))
    monkeypatch.setattr(
        datasets,
        "NATIVE_IDENTITIES",
        {
            relative: datasets.identity(repo_tmp_path / relative)
            for relative in (datasets.NATIVE_MANIFEST, datasets.CONSTRUCTION)
        },
    )
    monkeypatch.setattr(datasets, "execution_identity", lambda: {"code": {}})
    monkeypatch.chdir(repo_tmp_path)
    return repo_tmp_path


def test_curated_source_loading_and_identity_recheck(native_fixture: Path) -> None:
    dataset = datasets.CanonicalSourcesDataset()
    sources = dataset.load()
    result = datasets.assemble_canonical(sources, PARAMETERS)
    sources["panel"] = None
    panel_path = native_fixture / datasets.PANEL
    panel_path.write_text(panel_path.read_text() + "\n")
    with pytest.raises(DatasetError, match="input changed"):
        dataset.load()
    with pytest.raises(DatasetError, match="input changed"):
        datasets.CanonicalBundleDataset("data/processed/canonical_model_table_v1").save(result)


def test_missing_private_source_reports_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(DatasetError, match="missing"):
        datasets.CanonicalSourcesDataset().load()
