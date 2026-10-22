from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets import legacy_readiness as readiness

ROOT = Path(__file__).resolve().parents[2]


def test_build_model_eligibility_policy_uses_conservative_bounds() -> None:
    policy = readiness.build_model_eligibility_policy(2007, 2025)

    assert policy["source_coverage_backed_by_notification_year"]["start"] == "2007-01"
    assert policy["source_coverage_backed_by_notification_year"]["end"] == "2025-12"
    assert policy["development_target_eligibility"]["target_min"] == "2012-01"
    assert policy["development_target_eligibility"]["target_max"] == "2024-12"
    assert policy["earliest_cutoff_with_eligible_target"]["t1"] == "2011-12"
    assert policy["earliest_cutoff_with_eligible_target"]["t2"] == "2011-11"


def test_extract_development_target_bounds_uses_policy_payload() -> None:
    policy = readiness.build_model_eligibility_policy(2007, 2025)
    target_min, target_max, reserved_start = readiness.extract_development_target_bounds(policy)

    assert target_min == "2012-01"
    assert target_max == "2024-12"
    assert reserved_start == "2025-01"


def test_compute_edge_contribution_counts_rows_outside_backed_interval() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50001"],
            "year_month": ["2006-12", "2007-01", "2026-01"],
            "in_epi_coverage": [True, True, True],
            "dengue_notifications_count": [1.0, 2.0, 3.0],
            "dengue_grave_notifications_count": [0.0, 1.0, 0.0],
            "y_evaluable_t1": [False, True, True],
            "y_evaluable_t2": [False, True, False],
        }
    )

    edge = readiness.compute_edge_contribution(panel, backed_start="2007-01", backed_end="2025-12")

    assert edge["rows"] == 2
    assert edge["months"] == ["2006-12", "2026-01"]
    assert edge["dengue_count_sum"] == 4.0
    assert edge["dengue_grave_count_sum"] == 0.0
    assert edge["y_evaluable_t1_rows"] == 1
    assert edge["y_evaluable_t2_rows"] == 0


def test_compare_snapshot_allows_only_channel_additive_columns() -> None:
    baseline = {
        "inputs": {"fingerprints": {"a": 1}, "source_rows": {"dengue.csv": 1}},
        "panel": {
            "rows": 10,
            "columns": ["municipality_code", "year_month", "y_t1", "y_t2"],
            "duplicate_keys": 0,
            "y_p75_signature_sha256": "same",
        },
    }
    current = {
        "inputs": {"fingerprints": {"a": 1}, "source_rows": {"dengue.csv": 1}},
        "panel": {
            "rows": 10,
            "columns": [
                "municipality_code",
                "year_month",
                "y_t1",
                "y_t2",
                "p25_canal_t",
                "p50_canal_t",
                "p75_canal_t",
                "zona_canal_t",
            ],
            "duplicate_keys": 0,
            "y_p75_signature_sha256": "same",
        },
    }

    messages = readiness.compare_snapshot(baseline, current)
    by_check = {message.check: message for message in messages}

    assert by_check["input_fingerprints"].status == "PASS"
    assert by_check["source_lineage_counts"].status == "PASS"
    assert by_check["panel_columns_added"].status == "PASS"
    assert by_check["y_p75_signature"].status == "PASS"


def _stream_output(payload: dict[str, object]) -> dict[str, object]:
    return {
        "output_type": "stream",
        "name": "stdout",
        "text": [json.dumps(payload, indent=2) + "\n"],
    }


def _chapter8_stream_output() -> dict[str, object]:
    payload = {
        "split_strategy": "shared_date_cutoffs_across_all_municipalities",
        "audit_summary": {"windows_audited": 2, "windows_pass": 2, "windows_fail": 0},
    }
    return {
        "output_type": "stream",
        "name": "stdout",
        "text": ["Table 2 status note: executed checks.\n" + json.dumps(payload, indent=2) + "\n"],
    }


def _table_output(frame: pd.DataFrame) -> dict[str, object]:
    return {
        "output_type": "display_data",
        "data": {
            "text/html": [frame.to_html(index=False)],
            "text/plain": [frame.to_string(index=False)],
        },
        "metadata": {},
    }


def _figure_output() -> dict[str, object]:
    return {
        "output_type": "display_data",
        "data": {
            "image/png": "ZmFrZS1pbWFnZS1ieXRlcw==",
            "text/plain": ["<Figure size 100x100 with 1 Axes>"],
        },
        "metadata": {},
    }


def _build_notebook_surface_fixture(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    notebook_path = repo / "notebooks/03_consolidated_dataset_pipeline.ipynb"
    analysis_dir = repo / "tmp/stage2_y_reconciliation"
    panel_path = repo / "data/processed/panel_mensual_dengue_clima.csv"

    notebook_path.parent.mkdir(parents=True)
    analysis_dir.mkdir(parents=True)
    panel_path.parent.mkdir(parents=True)
    (repo / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "pyproject.toml").write_text("x", encoding="utf-8")

    for relative_path in readiness.NOTEBOOK_FINGERPRINT_MODULE_PATHS:
        module_path = repo / relative_path
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text(f"# fixture module: {relative_path}\n", encoding="utf-8")

    panel = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001", "50002"],
            "year_month": ["2024-01", "2024-02", "2024-01"],
            "dengue_notifications_count": [1.0, 2.0, 3.0],
            "zona_canal_t": ["SEGURIDAD", "ALERTA", "EXCESO"],
        }
    )
    panel.to_csv(panel_path, index=False)

    chapter6_summary = {
        "aggregate_rows": 24,
        "detail_rows": 1824,
        "method": "point_biserial_within_municipality_unweighted_median",
        "selection_rows_by_horizon": {"t1": 11856, "t2": 11856},
        "selection_bounds_by_horizon": {
            "t1": {
                "target_min_selected": "2012-01",
                "target_max_selected": "2024-12",
                "reference_min_selected": "2011-12",
                "reference_max_selected": "2024-11",
            },
            "t2": {
                "target_min_selected": "2012-01",
                "target_max_selected": "2024-12",
                "reference_min_selected": "2011-11",
                "reference_max_selected": "2024-10",
            },
        },
    }
    (analysis_dir / "chapter6_summary.json").write_text(
        json.dumps(chapter6_summary, indent=2),
        encoding="utf-8",
    )

    temporal_table = pd.DataFrame(
        [
            {
                "window_id": "window_until_2018-12",
                "horizon": "t1",
                "train_rows": 1000,
                "train_municipalities": 76,
                "validation_rows": 456,
                "validation_municipalities": 76,
                "temporal_validation_result": "PASS",
            },
            {
                "window_id": "window_until_2018-12",
                "horizon": "t2",
                "train_rows": 990,
                "train_municipalities": 76,
                "validation_rows": 380,
                "validation_municipalities": 76,
                "temporal_validation_result": "PASS",
            },
        ]
    )
    temporal_table.to_csv(
        analysis_dir / "chapter8_table2_temporal_validation_audit.csv",
        index=False,
    )

    table1 = pd.DataFrame(
        {
            "variable": ["x"],
            "missing_rows": [0],
        }
    )

    notebook_payload: dict[str, Any] = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "# Chapter 1 - Section 6: Monthly panel inspection\n",
                    "print('panel summary')\n",
                ],
                "execution_count": 1,
                "outputs": [
                    _stream_output(
                        {
                            "rows": int(len(panel)),
                            "columns": int(len(panel.columns)),
                        }
                    )
                ],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "# Chapter 3 - Missingness analysis and handling proposals\n",
                    "print('table 1')\n",
                ],
                "execution_count": 2,
                "outputs": [
                    _table_output(table1),
                    {"output_type": "stream", "name": "stdout", "text": ["ok\n"]},
                ],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "# Chapter 4 - Distributions, trends and seasonality diagnostics\n",
                    "print('figure 1')\n",
                ],
                "execution_count": 3,
                "outputs": [
                    _figure_output(),
                    {"output_type": "stream", "name": "stdout", "text": ["ok\n"]},
                ],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "# Chapter 6 - Relationships with Y and lag diagnostics by horizon\n",
                    "print('chapter 6 summary')\n",
                ],
                "execution_count": 4,
                "outputs": [_figure_output(), _stream_output(chapter6_summary)],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "# Chapter 8 - Temporal validation protocol structure\n",
                    "print('table 2')\n",
                ],
                "execution_count": 5,
                "outputs": [_table_output(temporal_table), _chapter8_stream_output()],
            },
            {
                "cell_type": "code",
                "metadata": {"language": "python"},
                "source": [
                    "# Chapter 10 - Analysis manifest and scope validator\n",
                    "print('manifest')\n",
                ],
                "execution_count": 6,
                "outputs": [],
            },
        ],
    }
    notebook_path.write_text(json.dumps(notebook_payload, indent=2), encoding="utf-8")

    execution_fingerprint = readiness.compute_notebook_execution_fingerprint(repo)
    analysis_manifest = {
        "generated_utc": "2026-10-19T00:00:00+00:00",
        "analysis_dir": "tmp/stage2_y_reconciliation",
        "input_panel": "data/processed/panel_mensual_dengue_clima.csv",
        "files": [
            {
                "path": "tmp/stage2_y_reconciliation/chapter6_summary.json",
                "bytes": int((analysis_dir / "chapter6_summary.json").stat().st_size),
                "sha256": readiness.sha256_file(analysis_dir / "chapter6_summary.json"),
            },
            {
                "path": "tmp/stage2_y_reconciliation/chapter8_table2_temporal_validation_audit.csv",
                "bytes": int(
                    (analysis_dir / "chapter8_table2_temporal_validation_audit.csv").stat().st_size
                ),
                "sha256": readiness.sha256_file(
                    analysis_dir / "chapter8_table2_temporal_validation_audit.csv"
                ),
            },
        ],
        "notebook_execution_fingerprint": execution_fingerprint,
    }
    (analysis_dir / "notebook_analysis_manifest.json").write_text(
        json.dumps(analysis_manifest, indent=2),
        encoding="utf-8",
    )

    notebook_payload["cells"][-1]["outputs"] = [
        _stream_output(
            {
                "analysis_manifest": analysis_manifest,
                "scope_report": {"status": "PASS"},
            }
        )
    ]
    notebook_path.write_text(json.dumps(notebook_payload, indent=2), encoding="utf-8")
    return repo, notebook_path


def _load_notebook_payload(notebook_path: Path) -> dict[str, Any]:
    return json.loads(notebook_path.read_text(encoding="utf-8"))


def _save_notebook_payload(notebook_path: Path, payload: dict[str, Any]) -> None:
    notebook_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_validate_notebook_surface_fails_without_outputs_and_execution_counts(
    tmp_path: Path,
) -> None:
    repo, notebook_path = _build_notebook_surface_fixture(tmp_path)
    payload = _load_notebook_payload(notebook_path)

    for cell in payload["cells"]:
        cell["execution_count"] = None
        cell["outputs"] = []

    _save_notebook_payload(notebook_path, payload)

    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_required_cells_executed"].status == "FAIL"
    assert by_check["notebook_required_cells_have_outputs"].status == "FAIL"
    assert "cell" in by_check["notebook_required_cells_have_outputs"].detail


def test_validate_notebook_surface_fails_when_panel_dimensions_saved_output_is_tampered(
    tmp_path: Path,
) -> None:
    repo, notebook_path = _build_notebook_surface_fixture(tmp_path)
    payload = _load_notebook_payload(notebook_path)
    panel_cell = payload["cells"][0]

    panel_summary = json.loads("".join(panel_cell["outputs"][0]["text"]))
    panel_summary["rows"] = int(panel_summary["rows"]) + 1
    panel_cell["outputs"][0]["text"] = [json.dumps(panel_summary, indent=2) + "\n"]
    _save_notebook_payload(notebook_path, payload)

    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_panel_summary_alignment"].status == "FAIL"
    assert "Cell" in by_check["notebook_panel_summary_alignment"].detail


def test_validate_notebook_surface_fails_when_temporal_table_saved_output_is_tampered(
    tmp_path: Path,
) -> None:
    repo, notebook_path = _build_notebook_surface_fixture(tmp_path)
    payload = _load_notebook_payload(notebook_path)

    chapter8_cell = payload["cells"][4]
    tampered_table = pd.DataFrame(
        [
            {
                "window_id": "window_until_2018-12",
                "horizon": "t1",
                "train_rows": 1000,
                "train_municipalities": 76,
                "validation_rows": 455,
                "validation_municipalities": 76,
                "temporal_validation_result": "PASS",
            },
            {
                "window_id": "window_until_2018-12",
                "horizon": "t2",
                "train_rows": 990,
                "train_municipalities": 76,
                "validation_rows": 380,
                "validation_municipalities": 76,
                "temporal_validation_result": "PASS",
            },
        ]
    )
    chapter8_cell["outputs"][0] = _table_output(tampered_table)
    _save_notebook_payload(notebook_path, payload)

    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_temporal_table_alignment"].status == "FAIL"
    assert "Cell" in by_check["notebook_temporal_table_alignment"].detail


def test_validate_notebook_surface_fails_when_embedded_manifest_is_stale(
    tmp_path: Path,
) -> None:
    repo, notebook_path = _build_notebook_surface_fixture(tmp_path)
    payload = _load_notebook_payload(notebook_path)

    chapter10_cell = payload["cells"][5]
    saved_output = json.loads("".join(chapter10_cell["outputs"][0]["text"]))
    stale_manifest = deepcopy(saved_output["analysis_manifest"])
    stale_manifest["files"] = stale_manifest["files"][:-1]
    saved_output["analysis_manifest"] = stale_manifest
    chapter10_cell["outputs"][0]["text"] = [json.dumps(saved_output, indent=2) + "\n"]
    _save_notebook_payload(notebook_path, payload)

    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_embedded_manifest_alignment"].status == "FAIL"


def test_validate_notebook_surface_fails_when_code_changes_without_rerun(tmp_path: Path) -> None:
    repo, notebook_path = _build_notebook_surface_fixture(tmp_path)
    payload = _load_notebook_payload(notebook_path)

    chapter6_cell = payload["cells"][3]
    chapter6_cell["source"].append("# stale code change without rerun\n")
    _save_notebook_payload(notebook_path, payload)

    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_execution_fingerprint_alignment"].status == "FAIL"


def test_validate_notebook_surface_passes_when_notebook_outputs_are_coherent(
    tmp_path: Path,
) -> None:
    repo, _notebook_path = _build_notebook_surface_fixture(tmp_path)
    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_code_only"].status == "PASS"
    assert by_check["notebook_error_outputs"].status == "PASS"
    assert by_check["notebook_required_cells_executed"].status == "PASS"
    assert by_check["notebook_required_cells_have_outputs"].status == "PASS"
    assert by_check["notebook_panel_summary_alignment"].status == "PASS"
    assert by_check["notebook_chapter6_summary_alignment"].status == "PASS"
    assert by_check["notebook_temporal_table_alignment"].status == "PASS"
    assert by_check["notebook_embedded_manifest_alignment"].status == "PASS"
    assert by_check["notebook_execution_fingerprint_alignment"].status == "PASS"
    assert by_check["notebook_figures_count"].status == "PASS"
    assert by_check["notebook_tables_count"].status == "PASS"


def test_validate_scope_reporting_checks_partial_scope_and_helpers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    notebook_dir = repo / "notebooks"
    notebook_dir.mkdir(parents=True)

    payload = {
        "cells": [
            {
                "cell_type": "code",
                "source": [
                    "sample_size = 150_000\n",
                    "profile_scope = visual_assets.summarize_profile_scope("
                    "raw_sample, sample_size)\n",
                    "note = 'partial evidence for this stage'\n",
                    "raw, adjusted, redundancy, meta = "
                    "visual_assets.build_correlation_diagnostics(panel, features)\n",
                    "statement = 'global calendar-month mean centering'\n",
                ],
            }
        ]
    }
    (notebook_dir / "03_consolidated_dataset_pipeline.ipynb").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    (repo / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "pyproject.toml").write_text("x", encoding="utf-8")

    messages = readiness.validate_scope_reporting(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["scope_sample_size_declared"].status == "PASS"
    assert by_check["scope_profile_helper_used"].status == "PASS"
    assert by_check["scope_partial_findings_declared"].status == "PASS"
    assert by_check["scope_correlation_helper_used"].status == "PASS"
    assert by_check["scope_month_adjustment_declared"].status == "PASS"


def test_compare_snapshot_reports_output_hash_mismatches() -> None:
    baseline = {
        "inputs": {"fingerprints": {"a": 1}, "source_rows": {"dengue.csv": 1}},
        "panel": {
            "rows": 10,
            "columns": ["municipality_code", "year_month", "y_t1", "y_t2"],
            "duplicate_keys": 0,
            "y_p75_signature_sha256": "same",
        },
        "output_hashes": {
            "consolidated_sha256": "hash-a",
            "traceability_sha256": "hash-b",
        },
    }
    current = {
        "inputs": {
            "fingerprints": {"a": 1},
            "source_rows": {"dengue.csv": 1},
            "manifest_input_fingerprints_before": {"a": 1},
            "manifest_input_fingerprints_after": {"a": 1},
        },
        "panel": {
            "rows": 10,
            "columns": ["municipality_code", "year_month", "y_t1", "y_t2"],
            "duplicate_keys": 0,
            "y_p75_signature_sha256": "same",
        },
        "output_hashes": {
            "consolidated_sha256": "hash-a",
            "traceability_sha256": "different",
        },
    }

    messages = readiness.compare_snapshot(baseline, current)
    by_check = {message.check: message for message in messages}

    assert by_check["baseline_consolidated_hash"].status == "PASS"
    assert by_check["baseline_traceability_hash"].status == "FAIL"


def test_validate_current_endemic_channel_integrity_detects_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    processed = repo / "data/processed"
    processed.mkdir(parents=True)

    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 6,
            "year_month": ["2020-01", "2021-01", "2022-01", "2023-01", "2024-01", "2025-01"],
            "dengue_notifications_count": [1.0, 2.0, 3.0, 4.0, 5.0, 4.0],
            "p25_canal_t": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 2.0],
            "p50_canal_t": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 3.0],
            "p75_canal_t": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, 4.0],
            "zona_canal_t": [pd.NA, pd.NA, pd.NA, pd.NA, pd.NA, "EXCESO"],
        }
    )
    panel.to_csv(processed / "panel_mensual_dengue_clima.csv", index=False)

    messages = readiness.validate_current_endemic_channel_integrity(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["channel_independent_recompute_match"].status == "FAIL"


def test_validate_current_endemic_channel_integrity_fails_on_duplicate_keys(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    processed = repo / "data/processed"
    processed.mkdir(parents=True)

    panel = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001"],
            "year_month": ["2025-01", "2025-01"],
            "dengue_notifications_count": [4.0, 4.0],
            "p25_canal_t": [2.0, 2.0],
            "p50_canal_t": [3.0, 3.0],
            "p75_canal_t": [4.0, 4.0],
            "zona_canal_t": ["EXCESO", "EXCESO"],
        }
    )
    panel.to_csv(processed / "panel_mensual_dengue_clima.csv", index=False)

    messages = readiness.validate_current_endemic_channel_integrity(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["channel_panel_key_uniqueness"].status == "FAIL"


def test_validate_execution_manifest_hashes_detects_stale_metadata(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    output_dir = repo / "data/processed"
    interim_dir = repo / "data/interim/stage2_consolidated_dataset_pipeline"
    output_dir.mkdir(parents=True)
    interim_dir.mkdir(parents=True)

    output_file = output_dir / "panel_mensual_dengue_clima.csv"
    output_file.write_text("a,b\n1,2\n", encoding="utf-8")

    manifest = {
        "outputs": {
            "panel_mensual_dengue_clima": {
                "path": "data/processed/panel_mensual_dengue_clima.csv",
                "sha256": "deadbeef",
                "bytes": 999,
            }
        }
    }
    (interim_dir / "execution_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    messages = readiness.validate_execution_manifest_hashes(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["execution_manifest_pipeline_code_fingerprint"].status == "FAIL"
    assert by_check["execution_manifest_output_files_exist"].status == "PASS"
    assert by_check["execution_manifest_output_hash_alignment"].status == "FAIL"


def test_validate_execution_manifest_hashes_handles_missing_manifest_file(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    messages = readiness.validate_execution_manifest_hashes(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["execution_manifest_pipeline_code_fingerprint"].status == "FAIL"
    assert by_check["execution_manifest_output_files_exist"].status == "FAIL"
    assert by_check["execution_manifest_output_hash_alignment"].status == "FAIL"
    assert (
        "Execution manifest missing" in by_check["execution_manifest_output_hash_alignment"].detail
    )


def test_validate_execution_manifest_hashes_handles_invalid_outputs_shape(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    interim_dir = repo / "data/interim/stage2_consolidated_dataset_pipeline"
    interim_dir.mkdir(parents=True)

    manifest = {
        "pipeline": {
            "module": "scripts/stage2_consolidated_dataset_pipeline.py",
            "module_sha256": "dummy",
        },
        "outputs": ["not", "a", "mapping"],
    }
    (interim_dir / "execution_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    messages = readiness.validate_execution_manifest_hashes(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["execution_manifest_output_files_exist"].status == "FAIL"
    assert by_check["execution_manifest_output_hash_alignment"].status == "FAIL"
    assert (
        "outputs section is missing or invalid"
        in by_check["execution_manifest_output_hash_alignment"].detail
    )


def test_validate_execution_manifest_hashes_handles_invalid_bytes_metadata(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    output_dir = repo / "data/processed"
    interim_dir = repo / "data/interim/stage2_consolidated_dataset_pipeline"
    output_dir.mkdir(parents=True)
    interim_dir.mkdir(parents=True)

    output_file = output_dir / "panel_mensual_dengue_clima.csv"
    output_file.write_text("a,b\n1,2\n", encoding="utf-8")

    manifest = {
        "pipeline": {
            "module": "scripts/stage2_consolidated_dataset_pipeline.py",
            "module_sha256": readiness.sha256_file(
                repo / "scripts/stage2_consolidated_dataset_pipeline.py"
            )
            if (repo / "scripts/stage2_consolidated_dataset_pipeline.py").exists()
            else "missing-in-fixture",
        },
        "outputs": {
            "panel_mensual_dengue_clima": {
                "path": "data/processed/panel_mensual_dengue_clima.csv",
                "sha256": readiness.sha256_file(output_file),
                "bytes": "not-an-integer",
            }
        },
    }
    (interim_dir / "execution_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    messages = readiness.validate_execution_manifest_hashes(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["execution_manifest_output_hash_alignment"].status == "FAIL"
    assert "bytes_invalid" in by_check["execution_manifest_output_hash_alignment"].detail


def test_validate_execution_manifest_hashes_fails_when_sha256_missing(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    output_dir = repo / "data/processed"
    interim_dir = repo / "data/interim/stage2_consolidated_dataset_pipeline"
    output_dir.mkdir(parents=True)
    interim_dir.mkdir(parents=True)

    output_file = output_dir / "panel_mensual_dengue_clima.csv"
    output_file.write_text("a,b\n1,2\n", encoding="utf-8")

    manifest = {
        "pipeline": {
            "module": "scripts/stage2_consolidated_dataset_pipeline.py",
            "module_sha256": "dummy",
        },
        "outputs": {
            "panel_mensual_dengue_clima": {
                "path": "data/processed/panel_mensual_dengue_clima.csv",
                "bytes": output_file.stat().st_size,
            }
        },
    }
    (interim_dir / "execution_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    messages = readiness.validate_execution_manifest_hashes(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["execution_manifest_output_hash_alignment"].status == "FAIL"
    assert "sha256_missing" in by_check["execution_manifest_output_hash_alignment"].detail


def test_validate_notebook_artifact_manifest_detects_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    analysis_dir = repo / "tmp/stage2_y_reconciliation"
    analysis_dir.mkdir(parents=True)

    artifact = analysis_dir / "chapter6_summary.json"
    artifact.write_text('{"x": 1}\n', encoding="utf-8")

    manifest = {
        "files": [
            {
                "path": "tmp/stage2_y_reconciliation/chapter6_summary.json",
                "bytes": 1,
                "sha256": "deadbeef",
            }
        ],
        "resource_manifest": {
            "figure_2_lag_associations": {
                "metadata": "tmp/stage2_y_reconciliation/chapter6_lag_associations_meta.json"
            }
        },
    }
    (analysis_dir / "notebook_analysis_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    messages = readiness.validate_notebook_artifact_manifest(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_manifest_file_hash_alignment"].status == "FAIL"
    assert by_check["notebook_manifest_resource_consistency"].status == "FAIL"


def test_validate_notebook_artifact_manifest_handles_invalid_bytes_metadata(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    analysis_dir = repo / "tmp/stage2_y_reconciliation"
    analysis_dir.mkdir(parents=True)

    artifact = analysis_dir / "chapter6_summary.json"
    artifact.write_text('{"x": 1}\n', encoding="utf-8")

    manifest = {
        "files": [
            {
                "path": "tmp/stage2_y_reconciliation/chapter6_summary.json",
                "bytes": "NaN",
                "sha256": readiness.sha256_file(artifact),
            }
        ],
        "resource_manifest": {},
    }
    (analysis_dir / "notebook_analysis_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    messages = readiness.validate_notebook_artifact_manifest(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_manifest_file_hash_alignment"].status == "FAIL"
    assert "bytes_invalid" in by_check["notebook_manifest_file_hash_alignment"].detail


def test_validate_notebook_artifact_manifest_handles_malformed_json(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    analysis_dir = repo / "tmp/stage2_y_reconciliation"
    analysis_dir.mkdir(parents=True)

    (analysis_dir / "notebook_analysis_manifest.json").write_text(
        "{not-valid-json}\n",
        encoding="utf-8",
    )

    messages = readiness.validate_notebook_artifact_manifest(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_manifest_file_hash_alignment"].status == "FAIL"
    assert by_check["notebook_manifest_missing_files"].status == "FAIL"
    assert by_check["notebook_manifest_resource_consistency"].status == "FAIL"
    assert "not valid JSON" in by_check["notebook_manifest_file_hash_alignment"].detail


def test_validate_temporal_artifact_selections_detects_count_mismatch(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    processed = repo / "data/processed"
    analysis_dir = repo / "tmp/stage2_y_reconciliation"
    processed.mkdir(parents=True)
    analysis_dir.mkdir(parents=True)

    periods = pd.period_range(start="2020-10", end="2021-08", freq="M")
    panel = pd.DataFrame(
        {
            "municipality_code": ["50001"] * len(periods),
            "year_month": [str(period) for period in periods],
            "y_evaluable_t1": [True] * len(periods),
            "y_evaluable_t2": [True] * len(periods),
            "target_period_t1": [str(period + 1) for period in periods],
            "target_period_t2": [str(period + 2) for period in periods],
        }
    )
    panel.to_csv(processed / "panel_mensual_dengue_clima.csv", index=False)

    (analysis_dir / "chapter6_summary.json").write_text(
        json.dumps({"selection_rows_by_horizon": {"t1": 1, "t2": 1}}),
        encoding="utf-8",
    )
    (analysis_dir / "chapter6_lag_associations_meta.json").write_text(
        json.dumps(
            {
                "selection": {
                    "target_min_period": "2021-01",
                    "target_max_period": "2021-06",
                    "reference_max_period": "2021-06",
                }
            }
        ),
        encoding="utf-8",
    )

    pd.DataFrame(
        [
            {
                "window_id": "window_until_2020-12",
                "horizon": "t1",
                "validation_rows": 99,
                "validation_reference_before_cutoff_count": 0,
                "check_validation_target_within_declared_window": "PASS",
                "check_reserved_block_excluded": "PASS",
            },
            {
                "window_id": "window_until_2020-12",
                "horizon": "t2",
                "validation_rows": 99,
                "validation_reference_before_cutoff_count": 0,
                "check_validation_target_within_declared_window": "PASS",
                "check_reserved_block_excluded": "PASS",
            },
        ]
    ).to_csv(analysis_dir / "chapter8_table2_temporal_validation_audit.csv", index=False)

    policy = {
        "development_target_eligibility": {
            "target_min": "2021-01",
            "target_max": "2021-06",
            "reserved_block_start": "2021-07",
        }
    }

    messages = readiness.validate_temporal_artifact_selections(
        repo,
        policy=policy,
        window_train_endpoints=("2020-12",),
    )
    by_check = {message.check: message for message in messages}

    assert by_check["chapter6_selection_rows_reported"].status == "FAIL"
    assert by_check["chapter8_validation_row_counts"].status == "FAIL"
