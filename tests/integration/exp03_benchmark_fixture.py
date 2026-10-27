"""Shared generated-only setup, no private sources or permanent stores."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01
from sat_dengue.experiments.exp03_features import prepare
from sat_dengue.experiments.exp03_persistence import (
    FrozenCell,
    fit_calibration,
    fit_native,
    freeze_terminal,
)
from sat_dengue.experiments.exp03_revision import CLIMATE_RECIPES, build_design


def _fixture(
    root: Path,
) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any], list[dict[str, Any]], str]:
    design = build_design(exp01.load_protocol()["design"])
    design["B_primary"] = 2.0
    design["budget_rationale"] = "synthetic fixture, never scientific authorization"
    records = []
    for j, municipality in enumerate(["50001", "73001"]):
        for i, month in enumerate(pd.period_range("2005-01", "2025-12", freq="M")):
            record = {
                "municipality_code": municipality,
                "year_month": str(month),
                "dengue_notifications_count": float((i * 7 + j * 3) % 13),
                "dengue_grave_notifications_count": float(i % 3),
            }
            for source, _ in CLIMATE_RECIPES:
                record[source] = float((i + j) % 17)
            records.append(record)
    panel = pd.DataFrame(records)
    cells, specs = [], []
    for horizon in (1, 2):
        spec = {
            "variant": "V00",
            "objective": "onset",
            "family": "gam",
            "horizon": horizon,
            "window": "stress_2024",
        }
        specs.append(spec)
        frame = prepare(panel, {}, horizon, allow_benchmark=True)
        columns = design["variants"]["V00"]
        train = frame.loc[frame.year_month.between("2020-01", "2022-12")].dropna(subset=columns)
        X = train[columns]
        truth = pd.Series(np.arange(len(X)) % 2, index=X.index)
        predictor = fit_native("gam", X, truth, {"C": 0.1, "n_knots": 4}, 42)
        calibrator = fit_calibration(predictor.predict(X), truth, 42)
        cells.append(
            FrozenCell(
                exp01.digest(spec),
                spec,
                predictor,
                calibrator,
                0.4,
                2.0,
                {
                    "membership": [
                        {"municipality_code": "50001", "transmission_profile": "low"},
                        {"municipality_code": "73001", "transmission_profile": "high"},
                    ]
                },
                {"synthetic": True, "matrix_sha256": exp01.digest(design)},
            )
        )
    manifest = freeze_terminal(cells, root, [c.cell_id for c in cells], {"synthetic": True})
    return panel, {}, design, specs, manifest["manifest_sha256"]


def _coverage() -> dict[str, Any]:
    return {
        "governed_coverage": True,
        "maturity_verified": True,
        "provenance_sha256": "generated-fixture-only",
    }
