"""Critical final-route regressions using synthetic inputs only; no reserved reads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.datasets.legacy_evaluation.final_evaluation.cohorts import (
    build_cohorts,
)
from sat_dengue.datasets.legacy_evaluation.model_assessment.policy import proposed_calendar
from sat_dengue.training_preparation.features import DERIVED_COLUMNS

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def synthetic() -> tuple[dict[str, Any], dict[int, Any], pd.DataFrame, dict[str, Any]]:
    """Two synthetic municipalities with complete history, actual calendars and both classes."""
    contract = json.loads(
        (ROOT / "docs/product/stage-3/training_preparation_contract_v1.json").read_text()
    )
    settings = json.loads(
        (ROOT / "docs/product/stage-5/model_evaluation_contract_v1.json").read_text()
    )["proposed_final"]["uncertainty"]
    population = ["50001", "73001"]
    periods = pd.period_range("2011-01", "2025-12", freq="M")
    rows = []
    for m, code in enumerate(population):
        for i, month in enumerate(periods):
            row: dict[str, Any] = {
                c: float(10 + (i * (m + 1)) % 7) for c in contract["roles"]["predictors"]
            }
            row.update(
                municipality_code=code,
                year_month=str(month),
                zona_canal_t="EXCESO" if (i + m) % 4 in [1, 2] else "SEGURIDAD",
            )
            for h in [1, 2]:
                row[f"target_period_t{h}"] = str(month + h)
                row[f"y_t{h}"] = int((i + h + m) % 4 in [1, 2])
                row[f"y_evaluable_t{h}"] = True
            rows.append(row)
    panel = pd.DataFrame(rows)
    columns = ["municipality_code", *contract["roles"]["predictors"], *DERIVED_COLUMNS]
    configs = {
        "xgboost": dict(
            n_estimators=3,
            max_depth=2,
            eta=0.1,
            reg_lambda=1,
            reg_alpha=0,
            max_bin=16,
            min_child_weight=1,
        ),
        "lightgbm": dict(
            n_estimators=3,
            max_depth=2,
            num_leaves=3,
            learning_rate=0.1,
            lambda_l1=0,
            lambda_l2=1,
            max_bin=16,
            min_data_in_leaf=3,
        ),
        "gam": dict(n_knots=3, C=1.0),
    }
    procedures = []
    for h in [1, 2]:
        for family, parameters in configs.items():
            procedures.append(
                dict(
                    proposed_calendar(h),
                    candidate=family,
                    retained_internal_components=dict(selected_parameters=parameters),
                    future_preparer=dict(
                        input_columns=columns,
                        spec=dict(
                            encoding="onehot",
                            numeric_missing="error",
                            numeric_scaling="none",
                            unknown_municipality="explicit",
                        ),
                    ),
                    retained_calibrator=dict(calibration_choice="original", available=False),
                    retained_threshold=dict(selected_threshold=0.5, calibration_choice="original"),
                    retained_component_availability_checks=[
                        dict(producer_role="threshold_selection", effective_availability="2024-03")
                    ],
                )
            )
    proposal = dict(
        procedures=procedures,
        common_population=population,
        rules=dict(proposed_final=dict(uncertainty=settings)),
    )
    return proposal, build_cohorts(panel, contract, proposal), panel, contract


@pytest.fixture
def frozen_graph_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    """A complete deterministic in-memory fixture, never evidence of real-data parity."""
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.final_evaluation.workflow import (
        generate_synthetic_sources,
        resolve_synthetic_configuration,
    )

    resolved = resolve_synthetic_configuration(
        ConfigurationInputsDataset().load(),
        {"profile": "evaluation_synthetic", "tracking": "disabled"},
    )
    return generate_synthetic_sources(resolved), resolved
