"""Shared source-free EXP03 preparation fixture."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01, exp03


def generated() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(v, freq="M") + 180) for v in panel.year_month]
    return panel, contract, exp03.load_protocol()["design"]


def cluster_pair() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    left = pd.DataFrame(
        {
            "municipality_code": ["50001", "73001"] * 3,
            "target_month": [f"{year}-02" for year in (2020, 2021, 2022) for _ in range(2)],
            "onset_target": [1, 1] * 3,
            "alert": [True] * 6,
        }
    )
    right = left.copy()
    right["alert"] = False
    exposure = pd.DataFrame(
        {
            "municipality_code": ["50001", "73001"] * 3,
            "target_year": [year for year in (2020, 2021, 2022) for _ in range(2)],
            "monitored_exposure": [1.0, 2.0] * 3,
            "eligible_exposure": [0.5] * 6,
            "common_exposure": [1 / 12] * 6,
        }
    )
    return left, right, exposure
