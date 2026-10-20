from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "consolidated_pipeline", ROOT / "scripts/stage2_consolidated_dataset_pipeline.py"
)
assert SPEC and SPEC.loader
pipeline = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = pipeline
SPEC.loader.exec_module(pipeline)


def _prepare_reuse_manifest_fixture(
    tmp_path: Path,
) -> tuple[Path, Any, dict[str, object], tuple[str, ...]]:
    root = tmp_path / "repo"
    (root / "data/raw").mkdir(parents=True)
    (root / "data/sources").mkdir(parents=True)
    (root / "data/processed").mkdir(parents=True)
    (root / "data/interim/stage2_consolidated_dataset_pipeline").mkdir(parents=True)

    for relative_path, content in {
        "data/raw/dengue.csv": "a,b\n1,2\n",
        "data/raw/dengue_grave.csv": "a,b\n3,4\n",
        "data/raw/google_earth_engine.csv": "date,dpto_ccdgo,mpio_cdpmp\n2020-01-01,50,50001\n",
        "data/sources/Divipola-municipios.md": "{}\n",
        "data/sources/divipola-provenance.json": "{}\n",
        "scripts/stage2_consolidated_dataset_pipeline.py": "# synthetic pipeline module\n",
    }.items():
        file_path = root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    output_payloads = {
        "dengue_y_dengue_grave": ("data/processed/dengue_y_dengue_grave.csv", "x\n1\n", 1),
        "panel_mensual_dengue_clima": (
            "data/processed/panel_mensual_dengue_clima.csv",
            "municipality_code,year_month\n50001,2020-01\n",
            1,
        ),
        "y_label_history_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/y_label_history_traceability.csv",
            "x\n1\n",
            1,
        ),
        "current_endemic_channel_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/current_endemic_channel_traceability.csv",
            "x\n1\n",
            1,
        ),
        "candidate_contract": (
            "data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json",
            "{}\n",
            0,
        ),
    }

    outputs: dict[str, object] = {}
    for output_key, (relative_path, content, rows) in output_payloads.items():
        output_path = root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        outputs[output_key] = {
            "path": relative_path,
            "rows": rows,
            "sha256": pipeline.sha256_file(output_path),
            "bytes": output_path.stat().st_size,
        }

    cfg = pipeline.PipelineConfig(
        chunksize_epi=200_000,
        chunksize_climate=250_000,
        contract_version="candidate-construction-v1",
        perform_safe_write=True,
    )
    paths = pipeline.build_paths(root)
    manifest = {
        "pipeline": pipeline.build_pipeline_signature(paths, cfg),
        "input_fingerprints_before": pipeline.fingerprint_inputs(paths),
        "input_fingerprints_after": pipeline.fingerprint_inputs(paths),
        "outputs": outputs,
    }
    required_output_keys = tuple(output_payloads.keys())
    return root, cfg, manifest, required_output_keys


def test_validate_manifest_reuse_candidate_allows_reuse_when_everything_matches(
    tmp_path: Path,
) -> None:
    root, cfg, manifest, required_output_keys = _prepare_reuse_manifest_fixture(tmp_path)

    can_reuse, reasons, summary = pipeline.validate_manifest_reuse_candidate(
        root=root,
        config=cfg,
        manifest=manifest,
        required_output_keys=required_output_keys,
    )

    assert can_reuse is True
    assert reasons == []
    assert summary["consolidated_rows"] == 1
    assert summary["panel_rows"] == 1


def test_validate_manifest_reuse_candidate_rejects_code_change_with_same_inputs_and_config(
    tmp_path: Path,
) -> None:
    root, cfg, manifest, required_output_keys = _prepare_reuse_manifest_fixture(tmp_path)

    # Regression guard for the previous blind spot: code drift with stable input/config.
    module_path = root / "scripts/stage2_consolidated_dataset_pipeline.py"
    module_path.write_text("# synthetic pipeline module changed\n", encoding="utf-8")

    can_reuse, reasons, _summary = pipeline.validate_manifest_reuse_candidate(
        root=root,
        config=cfg,
        manifest=manifest,
        required_output_keys=required_output_keys,
    )

    assert can_reuse is False
    assert "pipeline_module_sha256_mismatch" in reasons


def test_validate_manifest_reuse_candidate_rejects_input_and_config_changes(
    tmp_path: Path,
) -> None:
    root, cfg, manifest, required_output_keys = _prepare_reuse_manifest_fixture(tmp_path)

    (root / "data/raw/dengue.csv").write_text("a,b\n7,8\n", encoding="utf-8")
    can_reuse_inputs, reasons_inputs, _summary_inputs = pipeline.validate_manifest_reuse_candidate(
        root=root,
        config=cfg,
        manifest=manifest,
        required_output_keys=required_output_keys,
    )

    assert can_reuse_inputs is False
    assert "input_fingerprints_before_mismatch" in reasons_inputs
    assert "input_fingerprints_after_mismatch" in reasons_inputs

    can_reuse_cfg, reasons_cfg, _summary_cfg = pipeline.validate_manifest_reuse_candidate(
        root=root,
        config=pipeline.PipelineConfig(
            chunksize_epi=cfg.chunksize_epi,
            chunksize_climate=cfg.chunksize_climate,
            contract_version="candidate-construction-v2",
            perform_safe_write=True,
        ),
        manifest=manifest,
        required_output_keys=required_output_keys,
    )

    assert can_reuse_cfg is False
    assert "pipeline_contract_version_mismatch" in reasons_cfg


def test_validate_manifest_reuse_candidate_rejects_missing_code_hash_and_tampered_output(
    tmp_path: Path,
) -> None:
    root, cfg, manifest, required_output_keys = _prepare_reuse_manifest_fixture(tmp_path)

    missing_hash_manifest = json.loads(json.dumps(manifest))
    del missing_hash_manifest["pipeline"]["module_sha256"]
    can_reuse_missing, reasons_missing, _summary_missing = (
        pipeline.validate_manifest_reuse_candidate(
            root=root,
            config=cfg,
            manifest=missing_hash_manifest,
            required_output_keys=required_output_keys,
        )
    )

    assert can_reuse_missing is False
    assert "pipeline_module_sha256_missing" in reasons_missing

    missing_bytes_manifest = json.loads(json.dumps(manifest))
    del missing_bytes_manifest["outputs"]["candidate_contract"]["bytes"]
    can_reuse_missing_bytes, reasons_missing_bytes, _summary_missing_bytes = (
        pipeline.validate_manifest_reuse_candidate(
            root=root,
            config=cfg,
            manifest=missing_bytes_manifest,
            required_output_keys=required_output_keys,
        )
    )

    assert can_reuse_missing_bytes is False
    assert "output_bytes_missing:candidate_contract" in reasons_missing_bytes

    tampered_panel_path = root / "data/processed/panel_mensual_dengue_clima.csv"
    tampered_panel_path.write_text(
        "municipality_code,year_month\n50001,2020-02\n", encoding="utf-8"
    )
    can_reuse_tampered, reasons_tampered, _summary_tampered = (
        pipeline.validate_manifest_reuse_candidate(
            root=root,
            config=cfg,
            manifest=manifest,
            required_output_keys=required_output_keys,
        )
    )

    assert can_reuse_tampered is False
    assert "output_sha256_mismatch:panel_mensual_dengue_clima" in reasons_tampered


def test_validate_manifest_reuse_candidate_rejects_output_alias_path_spoofing(
    tmp_path: Path,
) -> None:
    root, cfg, manifest, required_output_keys = _prepare_reuse_manifest_fixture(tmp_path)

    spoofed_manifest = json.loads(json.dumps(manifest))
    spoofed_manifest["outputs"]["panel_mensual_dengue_clima"]["path"] = (
        "data/processed/dengue_y_dengue_grave.csv"
    )
    spoofed_manifest["outputs"]["panel_mensual_dengue_clima"]["sha256"] = spoofed_manifest[
        "outputs"
    ]["dengue_y_dengue_grave"]["sha256"]
    spoofed_manifest["outputs"]["panel_mensual_dengue_clima"]["bytes"] = spoofed_manifest[
        "outputs"
    ]["dengue_y_dengue_grave"]["bytes"]

    can_reuse, reasons, _summary = pipeline.validate_manifest_reuse_candidate(
        root=root,
        config=cfg,
        manifest=spoofed_manifest,
        required_output_keys=required_output_keys,
    )

    assert can_reuse is False
    assert "output_path_mismatch:panel_mensual_dengue_clima" in reasons


def test_normalize_code_preserves_leading_zeroes_and_rejects_invalid_values() -> None:
    series = pd.Series(["1", "001", "", "A2", "12345"])
    normalized = pipeline.normalize_code_series(series, 3)
    assert normalized.tolist() == ["001", "001", "", "", ""]


def test_parse_epi_date_uses_day_month_order_without_swapping() -> None:
    parsed = pipeline.parse_epi_date_series(
        pd.Series(["03/04/2013", "31/02/2013", "", "03/04/2013 12:00:00 a. m."])
    )
    assert parsed.iloc[0] == pd.Timestamp("2013-04-03")
    assert pd.isna(parsed.iloc[1])
    assert pd.isna(parsed.iloc[2])
    assert parsed.iloc[3] == pd.Timestamp("2013-04-03")


def test_enrich_chunk_keeps_rows_columns_provenance_and_missing_climate_records() -> None:
    chunk = pd.DataFrame(
        {
            "CONSECUTIVE": ["100", "100", "200"],
            "COD_DPTO_R": ["50", "50", "99"],
            "COD_MUN_R": ["001", "001", "999"],
            "INI_SIN": ["01/01/2020", "02/01/2020", "03/01/2020"],
            "fuente": ["x", "x", "y"],
        }
    )
    climate_lookup = pd.DataFrame(
        {
            "climate_join_key": ["50001|2020-01-01"],
            "climate_municipality_code": ["50001"],
            "climate_date_iso": ["2020-01-01"],
            "climate_date": [pd.Timestamp("2020-01-01")],
            "rain_mm_day": [1.5],
            "temp_mean_c": [23.0],
            "dewpoint_mean_c": [15.0],
            "soil_water_l1_mean": [0.3],
            "surface_runoff_mm_day": [0.1],
            "total_evaporation_mm_day_ecmwf": [-2.0],
            "wind_u_mean_ms": [1.2],
            "wind_v_mean_ms": [0.8],
            "solar_radiation_mj_m2_day": [17.0],
        }
    )

    enriched = pipeline.enrich_epi_chunk(
        chunk,
        source_file="dengue.csv",
        source_row_start=1,
        scope_codes={"50001"},
        climate_lookup=climate_lookup,
    )

    assert len(enriched) == len(chunk)
    for column in chunk.columns:
        assert column in enriched.columns
        assert enriched[column].tolist() == chunk[column].tolist()

    assert enriched["source_file"].tolist() == ["dengue.csv", "dengue.csv", "dengue.csv"]
    assert enriched["source_row_number"].tolist() == [1, 2, 3]
    assert enriched.loc[0, "climate_join_status"] == "matched"
    assert enriched.loc[1, "climate_join_status"] == "no_climate_match"
    assert enriched.loc[2, "panel_assignment_reason"] == "out_of_scope_municipality"
    assert pd.isna(enriched.loc[1, "climate_rain_mm_day"])


def test_load_scope_climate_detects_conflicting_duplicates(tmp_path: Path) -> None:
    root = tmp_path
    (root / "data/raw").mkdir(parents=True)
    (root / "data/sources").mkdir(parents=True)

    climate = pd.DataFrame(
        [
            {
                "date": "2020-01-01",
                "dpto_ccdgo": "50",
                "mpio_cdpmp": "50001",
                "rain_mm_day": "1",
                "temp_mean_c": "20",
                "dewpoint_mean_c": "10",
                "soil_water_l1_mean": "0.1",
                "surface_runoff_mm_day": "0.2",
                "total_evaporation_mm_day_ecmwf": "-1",
                "wind_u_mean_ms": "1",
                "wind_v_mean_ms": "1",
                "solar_radiation_mj_m2_day": "15",
            },
            {
                "date": "2020-01-01",
                "dpto_ccdgo": "50",
                "mpio_cdpmp": "50001",
                "rain_mm_day": "2",
                "temp_mean_c": "20",
                "dewpoint_mean_c": "10",
                "soil_water_l1_mean": "0.1",
                "surface_runoff_mm_day": "0.2",
                "total_evaporation_mm_day_ecmwf": "-1",
                "wind_u_mean_ms": "1",
                "wind_v_mean_ms": "1",
                "solar_radiation_mj_m2_day": "15",
            },
        ]
    )
    climate.to_csv(root / "data/raw/google_earth_engine.csv", index=False)

    paths = pipeline.build_paths(root)
    cfg = pipeline.PipelineConfig(chunksize_climate=10)
    raised = False
    try:
        pipeline.load_scope_climate_daily(paths, {"50001"}, cfg)
    except pipeline.PipelineValidationError:
        raised = True
    assert raised


def test_aggregate_monthly_climate_respects_coverage_and_leap_february() -> None:
    days = pd.date_range("2020-02-01", "2020-02-29", freq="D")
    climate_daily = pd.DataFrame(
        {
            "climate_join_key": [f"50001|{d:%Y-%m-%d}" for d in days],
            "climate_municipality_code": ["50001"] * len(days),
            "climate_date_iso": [f"{d:%Y-%m-%d}" for d in days],
            "climate_date": days,
            "rain_mm_day": [1.0] * len(days),
            "temp_mean_c": [20.0] * len(days),
            "dewpoint_mean_c": [12.0] * len(days),
            "soil_water_l1_mean": [0.2] * len(days),
            "surface_runoff_mm_day": [0.5] * len(days),
            "total_evaporation_mm_day_ecmwf": [-2.0] * len(days),
            "wind_u_mean_ms": [1.0] * len(days),
            "wind_v_mean_ms": [2.0] * len(days),
            "solar_radiation_mj_m2_day": [10.0] * len(days),
        }
    )
    climate_daily.loc[0, "temp_mean_c"] = pd.NA

    monthly = pipeline.aggregate_monthly_climate(climate_daily)
    assert len(monthly) == 1
    row = monthly.iloc[0]
    assert row["expected_days_in_month"] == 29
    assert row["rain_mm_month_sum"] == 29.0
    assert row["total_evaporation_mm_month_sum_ecmwf"] == -58.0
    assert row["temp_mean_c_month_mean_valid_days"] == 28
    assert pd.isna(row["temp_mean_c_month_mean"])


def test_build_monthly_panel_distinguishes_zero_vs_missing() -> None:
    grid = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50001"],
            "department_code": ["50", "50", "50"],
            "municipality_name": ["VILLAVICENCIO"] * 3,
            "year_month": ["2019-12", "2020-01", "2020-02"],
        }
    )
    epi_counts = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2020-02"],
            "dengue_notifications_count": [2],
            "dengue_grave_notifications_count": [1],
        }
    )
    climate_monthly = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50001"],
            "year_month": ["2019-12", "2020-01", "2020-02"],
            "climate_days_observed": [31, 31, 29],
            "expected_days_in_month": [31, 31, 29],
        }
    )

    panel = pipeline.build_monthly_panel(
        grid=grid,
        epi_counts=epi_counts,
        climate_monthly=climate_monthly,
        epi_coverage_start="2020-01",
        epi_coverage_end="2020-02",
    )

    assert pd.isna(panel.loc[0, "dengue_notifications_count"])
    assert panel.loc[1, "dengue_notifications_count"] == 0
    assert panel.loc[2, "dengue_notifications_count"] == 2
    assert panel.loc[1, "epi_count_status"] == "zero_in_coverage"
    assert panel.loc[0, "epi_count_status"] == "outside_epi_coverage_missing"
    assert not panel.duplicated(["municipality_code", "year_month"]).any()


def test_safe_replace_file_creates_backup_and_replaces_atomically(tmp_path: Path) -> None:
    target = tmp_path / "out.csv"
    backup_dir = tmp_path / "backups"
    target.write_text("old", encoding="utf-8")

    tmp = tmp_path / "out.csv.tmp"
    tmp.write_text("new", encoding="utf-8")

    metadata = pipeline.safe_replace_file(tmp_path=tmp, final_path=target, backup_dir=backup_dir)
    assert target.read_text(encoding="utf-8") == "new"
    assert metadata["had_previous"] is True
    assert Path(metadata["backup_path"]).exists()


def test_build_epi_monthly_counts_from_counter_keeps_dengue_grave_without_dengue() -> None:
    counter = {
        ("50001", "2020-01"): {"dengue_grave": 3, "dengue": 0},
    }
    table = pipeline.build_epi_monthly_counts_from_counter(counter)
    assert table.loc[0, "dengue_notifications_count"] == 0
    assert table.loc[0, "dengue_grave_notifications_count"] == 3


def test_describe_consolidated_schema_marks_climate_nullable_numeric() -> None:
    schema = pipeline.describe_consolidated_schema_from_columns(
        [
            "CONSECUTIVE",
            "source_row_number",
            "in_scope_catalog",
            "climate_rain_mm_day",
        ]
    )
    by_name = {row["name"]: row for row in schema}
    assert by_name["CONSECUTIVE"]["dtype"] == "string"
    assert by_name["source_row_number"]["dtype"] == "int64"
    assert by_name["in_scope_catalog"]["dtype"] == "bool"
    assert by_name["climate_rain_mm_day"]["nullable"] is True


def test_compute_schema_contract_includes_candidate_flags() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2020-01"],
            "dengue_notifications_count": [0],
        }
    )
    contract = pipeline.compute_schema_contract(
        consolidated_schema=[{"name": "CONSECUTIVE", "dtype": "string", "nullable": True}],
        panel=panel,
        version="candidate-construction-v1",
    )
    assert contract["classification"] == "candidate_construction_contract"
    assert contract["notes"]["status"] == "candidate_only_not_training_contract"


def test_scope_catalog_loader_requires_76_scope_municipalities(tmp_path: Path) -> None:
    root = tmp_path
    (root / "data/sources").mkdir(parents=True)
    payload = {
        "resultado": [
            {
                "CODIGO_MUNICIPIO": "001",
                "CODIGO_DEPARTAMENTO": "50",
                "CODIGO_DPTO_MPIO": "50001",
                "NOMBRE_MUNICIPIO": "X",
            }
        ]
    }
    (root / "data/sources/Divipola-municipios.md").write_text(json.dumps(payload), encoding="utf-8")

    raised = False
    try:
        pipeline.load_scope_catalog(pipeline.build_paths(root))
    except pipeline.PipelineValidationError:
        raised = True
    assert raised


def test_percentile_type7_uses_hf7_linear_interpolation() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert pipeline.percentile_type7(values, 0.75) == 4.0


def test_compute_y_labels_t1_uses_same_month_previous_five_years() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 7,
            "year_month": [
                "2019-01",
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2023-12",
                "2024-01",
            ],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 5.0],
        }
    )

    labeled, traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2023-12"].iloc[0]
    assert row["target_period_t1"] == "2024-01"
    assert row["history_valid_years_t1"] == 5
    assert row["history_periods_used_t1"] == "2019-01|2020-01|2021-01|2022-01|2023-01"
    assert row["p75_t1"] == 4.0
    assert row["y_status_t1"] == "evaluable"
    assert row["y_t1"] == 1

    trace_row = traceability[
        (traceability["cutoff_period"] == "2023-12") & (traceability["horizon_months"] == 1)
    ].iloc[0]
    assert trace_row["history_periods_expected"] == "2019-01|2020-01|2021-01|2022-01|2023-01"


def test_compute_y_labels_t2_crosses_calendar_year_without_leakage() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 8,
            "year_month": [
                "2020-02",
                "2021-02",
                "2022-02",
                "2023-02",
                "2024-02",
                "2024-12",
                "2025-02",
                "2025-03",
            ],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 6.0, 0.0],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2024-12"].iloc[0]
    assert row["target_period_t2"] == "2025-02"
    assert row["history_periods_used_t2"] == "2020-02|2021-02|2022-02|2023-02|2024-02"
    assert row["p75_t2"] == 4.0
    assert row["y_t2"] == 1


def test_compute_y_labels_isolated_by_municipality() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": [
                "50001",
                "50001",
                "50001",
                "50001",
                "50001",
                "50001",
                "50001",
                "50002",
                "50002",
                "50002",
                "50002",
                "50002",
                "50002",
                "50002",
            ],
            "year_month": [
                "2019-01",
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2023-12",
                "2024-01",
                "2019-01",
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2023-12",
                "2024-01",
            ],
            "dengue_notifications_count": [
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                0.0,
                2.0,
                10.0,
                10.0,
                10.0,
                10.0,
                10.0,
                0.0,
                10.0,
            ],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row_a = labeled[
        (labeled["municipality_code"] == "50001") & (labeled["year_month"] == "2023-12")
    ].iloc[0]
    row_b = labeled[
        (labeled["municipality_code"] == "50002") & (labeled["year_month"] == "2023-12")
    ].iloc[0]

    assert row_a["p75_t1"] == 1.0
    assert row_a["y_t1"] == 1
    assert row_b["p75_t1"] == 10.0
    assert row_b["y_t1"] == 0


def test_compute_y_labels_zero_history_is_valid_when_within_coverage() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 7,
            "year_month": [
                "2019-03",
                "2020-03",
                "2021-03",
                "2022-03",
                "2023-03",
                "2024-02",
                "2024-03",
            ],
            "dengue_notifications_count": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2024-02"].iloc[0]
    assert row["history_valid_years_t1"] == 5
    assert row["y_status_t1"] == "evaluable"
    assert row["y_t1"] == 0


def test_compute_y_labels_insufficient_history_stays_non_evaluable() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 6,
            "year_month": ["2019-01", "2020-01", "2022-01", "2023-01", "2023-12", "2024-01"],
            "dengue_notifications_count": [1.0, 2.0, 4.0, 5.0, 0.0, 6.0],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2023-12"].iloc[0]
    assert row["history_valid_years_t1"] == 4
    assert row["y_status_t1"] == "insufficient_history"
    assert pd.isna(row["y_t1"])


def test_compute_y_labels_missing_future_observation_stays_non_evaluable() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 7,
            "year_month": [
                "2019-01",
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2023-12",
                "2024-01",
            ],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, pd.NA],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2023-12"].iloc[0]
    assert row["y_status_t1"] == "future_observation_missing"
    assert bool(row["y_evaluable_t1"]) is False
    assert pd.isna(row["y_t1"])


def test_compute_y_labels_target_outside_panel_is_non_evaluable() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 6,
            "year_month": ["2019-01", "2020-01", "2021-01", "2022-01", "2023-01", "2023-12"],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2023-12"].iloc[0]
    assert row["target_period_t1"] == "2024-01"
    assert row["y_status_t1"] == "target_outside_panel"
    assert pd.isna(row["y_t1"])


def test_compute_y_labels_preserves_key_and_row_count() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50002", "50002"],
            "year_month": ["2020-01", "2020-02", "2020-01", "2020-02"],
            "dengue_notifications_count": [0.0, 1.0, 0.0, 2.0],
            "rain_mm_month_sum": [1.0, 2.0, 3.0, 4.0],
        }
    )

    labeled, traceability = pipeline.compute_y_labels(panel)
    assert len(labeled) == len(panel)
    assert labeled[["municipality_code", "year_month"]].equals(
        panel.sort_values(["municipality_code", "year_month"]).reset_index(drop=True)[
            ["municipality_code", "year_month"]
        ]
    )
    assert len(traceability) == len(panel) * 2
    assert "rain_mm_month_sum" in labeled.columns


def test_compute_y_labels_independent_from_climate_columns() -> None:
    base = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 7,
            "year_month": [
                "2019-01",
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2023-12",
                "2024-01",
            ],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 6.0],
        }
    )
    panel_a = base.assign(temp_mean_c_month_mean=10.0)
    panel_b = base.assign(temp_mean_c_month_mean=99.0)

    labeled_a, _trace_a = pipeline.compute_y_labels(panel_a)
    labeled_b, _trace_b = pipeline.compute_y_labels(panel_b)

    assert labeled_a["y_t1"].tolist() == labeled_b["y_t1"].tolist()
    pd.testing.assert_series_equal(labeled_a["p75_t1"], labeled_b["p75_t1"])


def test_compute_current_endemic_channel_boundaries_and_traceability() -> None:
    rows: list[dict[str, object]] = []
    expected_zone_by_period = {
        "2024-01": "EXITO",
        "2024-02": "SEGURIDAD",
        "2024-03": "SEGURIDAD",
        "2024-04": "ALERTA",
        "2024-05": "ALERTA",
        "2024-06": "EXCESO",
    }
    current_by_period = {
        "2024-01": 1.0,
        "2024-02": 2.0,
        "2024-03": 4.0,
        "2024-04": 5.0,
        "2024-05": 6.0,
        "2024-06": 7.0,
    }

    for month in range(1, 7):
        history_periods = [f"{year:04d}-{month:02d}" for year in range(2019, 2024)]
        for history_period, history_value in zip(
            history_periods,
            [0.0, 2.0, 4.0, 6.0, 8.0],
            strict=False,
        ):
            rows.append(
                {
                    "municipality_code": "50001",
                    "year_month": history_period,
                    "dengue_notifications_count": history_value,
                }
            )

        period = f"2024-{month:02d}"
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": period,
                "dengue_notifications_count": current_by_period[period],
            }
        )

    panel = pd.DataFrame(rows)
    labeled, traceability, _summary = pipeline.compute_current_endemic_channel(panel)

    for period, expected_zone in expected_zone_by_period.items():
        row = labeled[labeled["year_month"] == period].iloc[0]
        assert row["p25_canal_t"] == 2.0
        assert row["p50_canal_t"] == 4.0
        assert row["p75_canal_t"] == 6.0
        assert row["zona_canal_t"] == expected_zone

    trace_row = traceability[traceability["reference_period"] == "2024-03"].iloc[0]
    assert trace_row["history_periods_expected"] == "2019-03|2020-03|2021-03|2022-03|2023-03"
    assert trace_row["history_periods_used"] == "2019-03|2020-03|2021-03|2022-03|2023-03"
    assert trace_row["history_valid_years"] == 5
    assert trace_row["canal_status"] == "evaluable"


def test_compute_current_endemic_channel_zero_and_null_handling() -> None:
    rows: list[dict[str, object]] = []

    for month in (7, 8):
        for year in range(2019, 2024):
            rows.append(
                {
                    "municipality_code": "50001",
                    "year_month": f"{year:04d}-{month:02d}",
                    "dengue_notifications_count": 0.0,
                }
            )

    rows.extend(
        [
            {
                "municipality_code": "50001",
                "year_month": "2024-07",
                "dengue_notifications_count": 0.0,
            },
            {
                "municipality_code": "50001",
                "year_month": "2024-08",
                "dengue_notifications_count": 1.0,
            },
        ]
    )

    for period, value in [
        ("2019-09", 1.0),
        ("2020-09", 2.0),
        ("2021-09", pd.NA),
        ("2022-09", 4.0),
        ("2023-09", 5.0),
        ("2024-09", 3.0),
    ]:
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": period,
                "dengue_notifications_count": value,
            }
        )

    for year, value in zip(
        range(2019, 2024),
        [1.0, 2.0, 3.0, 4.0, 5.0],
        strict=False,
    ):
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": f"{year:04d}-10",
                "dengue_notifications_count": value,
            }
        )
    rows.append(
        {
            "municipality_code": "50001",
            "year_month": "2024-10",
            "dengue_notifications_count": pd.NA,
        }
    )

    panel = pd.DataFrame(rows)
    labeled, traceability, _summary = pipeline.compute_current_endemic_channel(panel)

    row_07 = labeled[labeled["year_month"] == "2024-07"].iloc[0]
    assert row_07["p25_canal_t"] == 0.0
    assert row_07["p50_canal_t"] == 0.0
    assert row_07["p75_canal_t"] == 0.0
    assert row_07["zona_canal_t"] == "SEGURIDAD"

    row_08 = labeled[labeled["year_month"] == "2024-08"].iloc[0]
    assert row_08["zona_canal_t"] == "EXCESO"

    row_09 = labeled[labeled["year_month"] == "2024-09"].iloc[0]
    assert pd.isna(row_09["p25_canal_t"])
    assert pd.isna(row_09["p50_canal_t"])
    assert pd.isna(row_09["p75_canal_t"])
    assert pd.isna(row_09["zona_canal_t"])

    row_10 = labeled[labeled["year_month"] == "2024-10"].iloc[0]
    assert pd.isna(row_10["zona_canal_t"])

    trace_09 = traceability[traceability["reference_period"] == "2024-09"].iloc[0]
    assert trace_09["canal_status"] == "insufficient_history"
    trace_10 = traceability[traceability["reference_period"] == "2024-10"].iloc[0]
    assert trace_10["canal_status"] == "current_count_missing"


def test_compute_current_endemic_channel_isolation_and_future_invariance() -> None:
    rows: list[dict[str, object]] = []

    for year in range(2019, 2024):
        rows.append(
            {
                "municipality_code": "50001",
                "year_month": f"{year:04d}-01",
                "dengue_notifications_count": 1.0,
            }
        )
        rows.append(
            {
                "municipality_code": "50002",
                "year_month": f"{year:04d}-01",
                "dengue_notifications_count": 10.0,
            }
        )

    rows.extend(
        [
            {
                "municipality_code": "50001",
                "year_month": "2024-01",
                "dengue_notifications_count": 2.0,
            },
            {
                "municipality_code": "50002",
                "year_month": "2024-01",
                "dengue_notifications_count": 2.0,
            },
            {
                "municipality_code": "50001",
                "year_month": "2023-02",
                "dengue_notifications_count": 999.0,
            },
            {
                "municipality_code": "50001",
                "year_month": "2026-01",
                "dengue_notifications_count": 100.0,
            },
        ]
    )

    base_panel = pd.DataFrame(rows)
    variant_panel = base_panel.copy()
    variant_panel.loc[
        (variant_panel["municipality_code"] == "50001")
        & (variant_panel["year_month"] == "2026-01"),
        "dengue_notifications_count",
    ] = 5_000.0

    labeled_base, _trace_base, _summary_base = pipeline.compute_current_endemic_channel(base_panel)
    labeled_variant, _trace_variant, _summary_variant = pipeline.compute_current_endemic_channel(
        variant_panel
    )

    base_a = labeled_base[
        (labeled_base["municipality_code"] == "50001") & (labeled_base["year_month"] == "2024-01")
    ].iloc[0]
    base_b = labeled_base[
        (labeled_base["municipality_code"] == "50002") & (labeled_base["year_month"] == "2024-01")
    ].iloc[0]
    variant_a = labeled_variant[
        (labeled_variant["municipality_code"] == "50001")
        & (labeled_variant["year_month"] == "2024-01")
    ].iloc[0]

    assert base_a["p75_canal_t"] == 1.0
    assert base_a["zona_canal_t"] == "EXCESO"
    assert base_b["p75_canal_t"] == 10.0
    assert base_b["zona_canal_t"] == "EXITO"

    assert base_a["p25_canal_t"] == variant_a["p25_canal_t"]
    assert base_a["p50_canal_t"] == variant_a["p50_canal_t"]
    assert base_a["p75_canal_t"] == variant_a["p75_canal_t"]
    assert base_a["zona_canal_t"] == variant_a["zona_canal_t"]


def test_summarize_y_labels_reports_horizon_counts() -> None:
    panel = pd.DataFrame(
        {
            "y_evaluable_t1": [True, False, True],
            "y_status_t1": ["evaluable", "insufficient_history", "evaluable"],
            "y_t1": pd.array([1, None, 0], dtype="Int64"),
            "y_evaluable_t2": [False, False, True],
            "y_status_t2": ["target_outside_panel", "future_observation_missing", "evaluable"],
            "y_t2": pd.array([None, None, 1], dtype="Int64"),
        }
    )

    summary = pipeline.summarize_y_labels(panel)
    assert summary["decision_rule"] == "strict_greater_than"
    assert summary["horizons"]["t1"]["evaluable_rows"] == 2
    assert summary["horizons"]["t1"]["label_counts"]["1"] == 1
    assert summary["horizons"]["t1"]["label_counts"]["0"] == 1
    assert summary["horizons"]["t1"]["label_counts"]["NA"] == 1


def test_compute_schema_contract_includes_y_column_roles() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"],
            "year_month": ["2020-01"],
            "dengue_notifications_count": [0.0],
            "target_period_t1": ["2020-02"],
            "p75_t1": [0.0],
            "history_valid_years_t1": [5],
            "history_periods_used_t1": ["2015-02|2016-02|2017-02|2018-02|2019-02"],
            "y_evaluable_t1": [True],
            "y_status_t1": ["evaluable"],
            "y_t1": pd.array([0], dtype="Int64"),
        }
    )
    contract = pipeline.compute_schema_contract(
        consolidated_schema=[{"name": "CONSECUTIVE", "dtype": "string", "nullable": True}],
        panel=panel,
        version="candidate-construction-v1",
    )
    roles = contract["datasets"]["panel_mensual_dengue_clima"]["column_roles"]
    assert "municipality_code" in roles["keys"]
    assert "target_period_t1" in roles["historical_references"]
    assert "y_t1" in roles["labels"]
    assert contract["target_labeling_policy"]["percentile_method"] == "hyndman_fan_type7_linear"


def _independent_history_periods(target_period: str, years: int = 5) -> list[str]:
    target_year = int(target_period[:4])
    target_month = target_period[5:7]
    return [f"{year:04d}-{target_month}" for year in range(target_year - years, target_year)]


def test_temporal_regression_november_to_january_main_case() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 8,
            "year_month": [
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2024-01",
                "2024-11",
                "2025-01",
                "2026-01",
            ],
            "dengue_notifications_count": [2.0, 3.0, 4.0, 5.0, 100.0, 0.0, 5.0, 999.0],
        }
    )

    labeled, traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2024-11"].iloc[0]
    assert row["target_period_t2"] == "2025-01"
    assert row["history_periods_expected_t2"] == "2020-01|2021-01|2022-01|2023-01|2024-01"
    assert row["history_periods_used_t2"] == "2020-01|2021-01|2022-01|2023-01|2024-01"
    assert row["p75_t2"] == 5.0
    assert row["y_t2"] == 0

    trace_row = traceability[
        (traceability["cutoff_period"] == "2024-11") & (traceability["horizon_months"] == 2)
    ].iloc[0]
    assert trace_row["history_periods_used"] == "2020-01|2021-01|2022-01|2023-01|2024-01"


def test_temporal_regression_november_to_december_reference() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 7,
            "year_month": [
                "2019-12",
                "2020-12",
                "2021-12",
                "2022-12",
                "2023-12",
                "2024-11",
                "2024-12",
            ],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 6.0],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2024-11"].iloc[0]
    assert row["target_period_t1"] == "2024-12"
    assert row["history_periods_used_t1"] == "2019-12|2020-12|2021-12|2022-12|2023-12"
    assert row["p75_t1"] == 4.0
    assert row["y_t1"] == 1


def test_temporal_regression_december_to_january_and_february() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 13,
            "year_month": [
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2024-01",
                "2020-02",
                "2021-02",
                "2022-02",
                "2023-02",
                "2024-02",
                "2024-12",
                "2025-01",
                "2025-02",
            ],
            "dengue_notifications_count": [
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                1.0,
                1.0,
                2.0,
                2.0,
                3.0,
                0.0,
                4.0,
                3.0,
            ],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2024-12"].iloc[0]
    assert row["target_period_t1"] == "2025-01"
    assert row["target_period_t2"] == "2025-02"
    assert row["history_periods_used_t1"] == "2020-01|2021-01|2022-01|2023-01|2024-01"
    assert row["history_periods_used_t2"] == "2020-02|2021-02|2022-02|2023-02|2024-02"


def test_temporal_regression_all_cutoff_months_and_horizons_reference_rule() -> None:
    rows: list[dict[str, object]] = []
    municipality = "50001"
    cutoff_months = [f"2024-{month:02d}" for month in range(1, 13)]

    for month in range(1, 13):
        for year in range(2019, 2027):
            rows.append(
                {
                    "municipality_code": municipality,
                    "year_month": f"{year:04d}-{month:02d}",
                    "dengue_notifications_count": float((year - 2018) + month),
                }
            )

    panel = pd.DataFrame(rows).drop_duplicates(["municipality_code", "year_month"])
    labeled, _traceability = pipeline.compute_y_labels(panel)

    for cutoff in cutoff_months:
        current = labeled[labeled["year_month"] == cutoff].iloc[0]
        for horizon in (1, 2):
            suffix = f"t{horizon}"
            target_period = str(current[f"target_period_{suffix}"])
            expected = "|".join(_independent_history_periods(target_period, years=5))
            assert current[f"history_periods_expected_{suffix}"] == expected


def test_temporal_regression_target_count_change_does_not_change_its_own_threshold() -> None:
    base = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 7,
            "year_month": [
                "2020-01",
                "2021-01",
                "2022-01",
                "2023-01",
                "2024-01",
                "2024-11",
                "2025-01",
            ],
            "dengue_notifications_count": [2.0, 3.0, 4.0, 5.0, 100.0, 0.0, 5.0],
        }
    )

    variant = base.copy()
    variant.loc[variant["year_month"] == "2025-01", "dengue_notifications_count"] = 50.0

    labeled_base, _trace_a = pipeline.compute_y_labels(base)
    labeled_variant, _trace_b = pipeline.compute_y_labels(variant)

    row_a = labeled_base[labeled_base["year_month"] == "2024-11"].iloc[0]
    row_b = labeled_variant[labeled_variant["year_month"] == "2024-11"].iloc[0]
    assert row_a["p75_t2"] == row_b["p75_t2"]


def test_temporal_regression_missing_required_history_never_substitutes_older_year() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 8,
            "year_month": [
                "2019-01",
                "2020-01",
                "2021-01",
                "2023-01",
                "2024-01",
                "2024-11",
                "2025-01",
                "2018-01",
            ],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 5.0, 100.0, 0.0, 5.0, 99.0],
        }
    )

    labeled, _traceability = pipeline.compute_y_labels(panel)
    row = labeled[labeled["year_month"] == "2024-11"].iloc[0]
    assert row["history_periods_expected_t2"] == "2020-01|2021-01|2022-01|2023-01|2024-01"
    assert row["history_missing_periods_t2"] == "2022-01"
    assert row["history_valid_years_t2"] == 4
    assert row["y_status_t2"] == "insufficient_history"
    assert pd.isna(row["y_t2"])


def test_compute_y_labels_requires_expected_columns() -> None:
    with pytest.raises(pipeline.PipelineValidationError):
        pipeline.compute_y_labels(pd.DataFrame({"municipality_code": ["50001"]}))
