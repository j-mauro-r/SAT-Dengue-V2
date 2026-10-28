"""Canonical, source-free EXP03.1 protocol and matrix generator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes

ROOT = Path("docs/product/experiments/EXP03.1_add_pass_info")
PROTOCOL = ROOT / "protocol.json"
MATRIX = ROOT / "ablation-matrix.frozen.yml"
RECENT = [
    "channel_security_recent_6m_count",
    "channel_warning_recent_6m_count",
    "channel_excess_recent_6m_count",
]
CHANGE = [
    "channel_security_change_6m",
    "channel_warning_change_6m",
    "channel_excess_change_6m",
]


def protocol() -> dict[str, Any]:
    return {
        "schema": "sat-dengue-experiment-protocol-v1",
        "version": "1.0.0",
        "experiment_id": "EXP031",
        "scientific_id": "EXP03.1",
        "python_id": "exp03_1",
        "experiment_slug": "recent_endemic_channel_trajectory",
        "hypothesis_id": "EXP031-H1",
        "scientific_hypothesis_id": "EXP03.1-H1",
        "title": "EXP03.1 — Recent endemic-channel trajectory",
        "objective": (
            "Test recent channel memory and semester-over-semester trajectory change "
            "against EXP03 V09 under the same false-alert budget."
        ),
        "execution": {
            "kedro_pipeline": "exp03_1",
            "mode": "infrastructure_only_real_execution_not_authorized",
            "real_execution_authorized": False,
            "synthetic_evidence_only": True,
        },
        "parent_experiment": {
            "experiment_id": "EXP03",
            "reference_variant": "V09",
            "protocol_version": "2.0.1",
        },
        "question": (
            "Does recent endemic-channel trajectory improve future-onset detection over "
            "complete EXP03 V09 at the same false-alert budget?"
        ),
        "windows": {
            "recent": {"offsets": [-1, -2, -3, -4, -5, -6]},
            "prior": {"offsets": [-7, -8, -9, -10, -11, -12]},
        },
        "channel": {
            "states": ["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"],
            "p75_method": "type_7",
            "same_calendar_month_history": 5,
            "epidemic_years": "included",
            "excess_comparison": "strict_greater_than",
            "historical_as_of": "each_historical_month",
        },
        "coverage": {
            "covered_no_notifications": "zero_cases_assumption_not_active_reporting_proof",
            "outside_coverage": "unknown",
            "unreconstructable_zone": "unknown",
            "primary_known_states_required": 12,
            "coverage_is_predictor": False,
        },
        "predictors": {
            "recent": RECENT,
            "change": CHANGE,
            "forbidden": [
                "channel_success_recent_6m_count",
                "prior_counts_as_predictors",
                "coverage_as_predictor",
            ],
        },
        "variants": {
            "M00": {"name": "exp03_v09_reference", "blocks": ["EXP03_V09"]},
            "M01": {
                "name": "v09_plus_recent_channel_memory",
                "blocks": ["EXP03_V09", "recent"],
            },
            "M02": {
                "name": "v09_plus_channel_trajectory",
                "blocks": ["EXP03_V09", "recent", "change"],
            },
        },
        "contrasts": {
            "Q1": ["M01", "M00"],
            "Q2": ["M02", "M01"],
            "Q3": ["M02", "M00"],
        },
        "families": ["gam", "lightgbm", "xgboost"],
        "horizons": [1, 2],
        "cuts": [
            "development_2020",
            "development_2021",
            "development_2022",
            "stress_2024",
        ],
        "objectives": {
            "onset": {"variants": ["M00", "M01", "M02"], "horizons": [1, 2]},
            "excess_control": {"variants": ["M00", "M02"], "horizons": [2]},
        },
        "budget": {
            "B_primary": 1.0,
            "units": "false_onset_alerts_per_monitored_municipality_year",
            "selection_uses_evaluation": False,
        },
        "reuse_identity_fields": [
            "training_cohort",
            "calibration_cohort",
            "selection_cohort",
            "evaluation_cohort",
            "labels",
            "ordered_predictors",
            "preparation",
            "family_configuration",
            "temporal_protocol",
            "budget",
            "relevant_code",
        ],
        "governance": {
            "real_execution": "NOT_AUTHORIZED",
            "private_data_reads": 0,
            "permanent_mlflow_writes": 0,
            "G5": "NOT_APPROVED",
            "champion": "not_selected",
            "year_2025": "REJECTED",
        },
        "mlflow": {
            "experiment_name": "sat-dengue-bounded-v1",
            "required_conceptual_tags": {
                "experiment_id": "EXP031",
                "experiment_slug": "recent_endemic_channel_trajectory",
                "hypothesis_id": "EXP031-H1",
                "objective_slug": "test_recent_channel_trajectory",
                "experiment_type": "paired_feature_trajectory_ablation",
                "target_definition": "exact_onset_with_t2_excess_control",
            },
        },
    }


def digest(value: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def cells(value: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    p = value or protocol()
    output = []
    for objective, spec in p["objectives"].items():
        for variant in spec["variants"]:
            for family in p["families"]:
                for horizon in spec["horizons"]:
                    for cut in p["cuts"]:
                        output.append(
                            {
                                "objective": objective,
                                "variant": variant,
                                "family": family,
                                "horizon": horizon,
                                "cut": cut,
                            }
                        )
    return output


def counts(value: dict[str, Any] | None = None) -> dict[str, int]:
    grid = cells(value)
    onset = sum(row["objective"] == "onset" for row in grid)
    excess = len(grid) - onset
    reused = sum(row["variant"] == "M00" for row in grid)
    return {
        "onset_cells": onset,
        "excess_control_cells": excess,
        "maximum_refit_cells": len(grid),
        "terminal_cells": sum(row["cut"] == "stress_2024" for row in grid),
        "maximum_reused_m00_cells": reused,
        "maximum_new_fit_cells_with_complete_reuse": len(grid) - reused,
    }


def matrix(value: dict[str, Any] | None = None) -> dict[str, Any]:
    p = value or protocol()
    return {
        "schema": "sat-dengue-exp03-1-ablation-matrix-v1",
        "protocol_sha256": digest(p),
        "groups": {"recent": RECENT, "change": CHANGE},
        "variants": p["variants"],
        "contrasts": p["contrasts"],
        "cells": cells(p),
        "derived_counts": counts(p),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected_protocol = protocol()
    expected_matrix = matrix(expected_protocol)
    if args.check:
        if json.loads(PROTOCOL.read_text()) != expected_protocol:
            raise ValueError("EXP03.1 protocol differs from canonical source")
        if yaml.safe_load(MATRIX.read_text()) != expected_matrix:
            raise ValueError("EXP03.1 matrix differs from canonical source")
    else:
        PROTOCOL.write_bytes(canonical_bytes(expected_protocol))
        MATRIX.write_text(yaml.safe_dump(expected_matrix, sort_keys=False, allow_unicode=True))
    print(
        json.dumps(
            {"protocol_sha256": digest(expected_protocol), "counts": counts(expected_protocol)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
