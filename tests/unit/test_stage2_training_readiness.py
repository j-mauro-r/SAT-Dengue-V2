from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "stage2_training_readiness",
    ROOT / "scripts/validate_stage2_training_readiness.py",
)
assert SPEC and SPEC.loader
readiness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = readiness
SPEC.loader.exec_module(readiness)


def test_build_model_eligibility_policy_uses_conservative_bounds() -> None:
    policy = readiness.build_model_eligibility_policy(2007, 2025)

    assert policy["source_coverage_backed_by_notification_year"]["start"] == "2007-01"
    assert policy["source_coverage_backed_by_notification_year"]["end"] == "2025-12"
    assert policy["development_target_eligibility"]["target_min"] == "2012-01"
    assert policy["development_target_eligibility"]["target_max"] == "2024-12"
    assert policy["earliest_cutoff_with_eligible_target"]["t1"] == "2011-12"
    assert policy["earliest_cutoff_with_eligible_target"]["t2"] == "2011-11"


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


def test_validate_notebook_surface_detects_two_tables_and_two_figures(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    notebook_dir = repo / "notebooks"
    notebook_dir.mkdir(parents=True)

    payload = {
        "cells": [
            {
                "cell_type": "code",
                "source": [
                    "import matplotlib.pyplot as plt\n",
                    "from IPython.display import display\n",
                    "display(df1)\n",
                    "plt.show()\n",
                ],
            },
            {
                "cell_type": "code",
                "source": [
                    "display(df2)\n",
                    "plt.show()\n",
                ],
            },
        ]
    }
    (notebook_dir / "03_consolidated_dataset_pipeline.ipynb").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )
    (repo / "AGENTS.md").write_text("x", encoding="utf-8")
    (repo / "pyproject.toml").write_text("x", encoding="utf-8")

    messages = readiness.validate_notebook_surface(repo)
    by_check = {message.check: message for message in messages}

    assert by_check["notebook_code_only"].status == "PASS"
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
