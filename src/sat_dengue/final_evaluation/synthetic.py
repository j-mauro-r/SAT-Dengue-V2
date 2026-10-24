"""Deterministic in-memory frozen evaluation fixtures; no real input or fitting interface."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.model_assessment.policy import proposed_calendar
from sat_dengue.training_preparation.features import DERIVED_COLUMNS


def synthetic_sources(authorities: dict[str, Any]) -> dict[str, Any]:
    """Generate the entire fixture internally, including its already frozen toy scores."""
    contract = authorities["training_preparation_contract_v1"]["document"]
    settings = authorities["model_evaluation_contract_v1"]["document"]["proposed_final"][
        "uncertainty"
    ]
    population = ["50001", "73001"]
    rows = []
    for m, code in enumerate(population):
        for i, month in enumerate(pd.period_range("2011-01", "2025-12", freq="M")):
            row: dict[str, Any] = {
                c: float(10 + (i * (m + 1)) % 7) for c in contract["roles"]["predictors"]
            }
            row.update(
                municipality_code=code,
                year_month=str(month),
                zona_canal_t="EXCESO" if (i + m) % 4 in [1, 2] else "SEGURIDAD",
            )
            for h in (1, 2):
                row.update(
                    {
                        f"target_period_t{h}": str(month + h),
                        f"y_t{h}": int((i + h + m) % 4 in [1, 2]),
                        f"y_evaluable_t{h}": True,
                    }
                )
            rows.append(row)
    procedures = []
    for h in (1, 2):
        for family in ("xgboost", "lightgbm", "gam"):
            procedures.append(
                {
                    **proposed_calendar(h),
                    "candidate": family,
                    "future_preparer": {
                        "input_columns": [
                            "municipality_code",
                            *contract["roles"]["predictors"],
                            *DERIVED_COLUMNS,
                        ]
                    },
                    "retained_calibrator": {
                        "calibration_choice": "sigmoid" if family == "gam" else "original",
                        "available": True,
                        "coefficient": 1.25,
                        "intercept": -0.5,
                    },
                    "retained_threshold": {"selected_threshold": 0.55},
                    "retained_component_availability_checks": [
                        {
                            "producer_role": "threshold_selection",
                            "effective_availability": "2024-03",
                        }
                    ],
                }
            )
    return {
        "mode": "synthetic",
        "proposal": {
            "common_population": population,
            "procedures": procedures,
            "rules": {"proposed_final": {"uncertainty": settings}},
        },
        "panel": pd.DataFrame(rows),
        "preparation_contract": contract,
        "components": {},
        "development": {},
        "reference": {},
        "provenance": {
            "fixture": "evaluation-synthetic-v1",
            "real_model_fits": 0,
            "real_preparer_refits": 0,
            "calibrator_fits": 0,
            "threshold_selection": 0,
            "hyperparameter_search": 0,
        },
    }
