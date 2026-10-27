"""Independent temporal, preparation, selection and native inference regressions."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_training.contract import (
    read_json,
)
from sat_dengue.datasets.legacy_training.loading import WindowDataset

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = read_json(ROOT / "docs/product/stage-4/model_engineering_contract_v1.json")


def settings() -> dict[str, Any]:
    """Use a tiny computational fixture, preserving actual scientific protocol."""
    result = copy.deepcopy(CONTRACT["xgboost_candidate"])
    result["configurations"] = [dict(result["configurations"][0], n_estimators=3)]
    return result


def window(horizon: int = 1) -> WindowDataset:
    """Create two municipalities with known alternating labels and monthly linkage."""
    rows = []
    for municipality in ["05001", "05002"]:
        for i, period in enumerate(pd.period_range("2011-12", "2017-05", freq="M")):
            rows.append(
                dict(
                    municipality_code=municipality,
                    year_month=str(period),
                    target=str(period + horizon),
                    signal=float(i % 7),
                    y=i % 2,
                )
            )
    frame = pd.DataFrame(rows)
    train = frame[frame.target.between("2012-01", "2016-12")].reset_index(drop=True)
    valid = frame[(frame.year_month >= "2016-12") & (frame.target <= "2017-06")].reset_index(
        drop=True
    )

    def parts(f: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        X = f[["municipality_code", "signal"]].assign(
            zona_canal_t="EXITO", zona_canal_lag_1="SEGURIDAD"
        )
        y = f[["y"]].rename(columns={"y": f"y_t{horizon}"})
        index = f[["municipality_code", "year_month", "target"]].rename(
            columns={"target": f"target_period_t{horizon}"}
        )
        index["feature_row"] = np.arange(len(f))
        return X, y, index

    tx, ty, ti = parts(train)
    vx, vy, vi = parts(valid)
    return WindowDataset(
        f"2016-12_t{horizon}",
        "2016-12",
        horizon,
        f"target_period_t{horizon}",
        f"y_t{horizon}",
        tx,
        ty,
        ti,
        vx,
        vy,
        vi,
    )
