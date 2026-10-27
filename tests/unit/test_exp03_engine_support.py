"""Generated engine control seam: fitting and evaluation support are distinct."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments import exp03_engine as engine
from sat_dengue.experiments.exp03_evaluation import BUDGET_UNITS


def test_fitted_cell_without_evaluation_never_calls_empty_predictor(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = dict(variant="V00", objective="onset", family="gam", horizon=1, window="stress_2024")
    design = dict(
        B_primary=2.0,
        budget_units=BUDGET_UNITS,
        budget_rationale="generated fixture",
        variants={"V00": ["x"]},
        predictors=["x"],
        families={"gam": {}},
        horizons=[1],
        seed=42,
        windows=[{"id": "stress_2024", "evidence_type": "retrospective_stress"}],
        delay_variants=[],
    )
    train = pd.DataFrame(
        dict(
            municipality_code=["50001", "50001"],
            year_month=["2023-01", "2023-02"],
            target_month=["2023-02", "2023-03"],
            onset_target=[0, 1],
            excess_target=[0, 1],
            eligible_at_t=[True, True],
            transmission_profile=["low", "low"],
            x=[0.0, 1.0],
        )
    )
    empty = train.iloc[:0].copy()
    roles = {
        r: (empty.copy() if r == "evaluation" else train.copy())
        for r in ("train", "calibration", "selection", "evaluation")
    }
    for frame in roles.values():
        frame.attrs = {
            "source_months": pd.DataFrame(index=frame.index),
            "source_event_months": pd.DataFrame(index=frame.index),
        }
    ledger = pd.DataFrame(
        [
            dict(
                role=r,
                window="stress_2024",
                municipality_code="50001",
                target_year=2024,
                monitored_exposure=1.0,
                eligible_exposure=1.0,
                common_exposure=0.0 if r == "evaluation" else 1.0,
                known_eligible_onsets=1,
                excluded_onsets=1 if r == "evaluation" else 0,
            )
            for r in roles
        ]
    )
    monkeypatch.setattr(engine, "validate_design", lambda d: 1)
    monkeypatch.setattr(engine, "cell_grid", lambda d: [spec])
    common = {r: f.copy() for r, f in roles.items()}
    monkeypatch.setattr(engine, "cohorts", lambda *args: {(1, "stress_2024"): (roles, common)})
    monkeypatch.setattr(engine, "exposure_table", lambda parts: ledger.copy())
    monkeypatch.setattr(engine, "coverage", lambda *args: {"status": "generated_control"})
    monkeypatch.setattr(engine, "coverage_groups", lambda *args: [])
    monkeypatch.setattr(engine, "prepare", lambda *args, **kw: pd.DataFrame())
    monkeypatch.setattr(engine, "_contrasts", lambda *args: [])
    monkeypatch.setattr(engine, "freeze_terminal", lambda *args, **kw: {"frozen_at": "synthetic"})
    calls = []

    class Model:
        columns = ["x"]

        def predict(self, frame: pd.DataFrame) -> pd.Series:
            assert not frame.empty, "predict called without evaluation support"
            calls.append(len(frame))
            return pd.Series([0.1, 0.9], index=frame.index)

    def fit(*args: Any) -> Model:
        return Model()

    panel = pd.DataFrame()
    panel.attrs["synthetic_generated"] = True
    result = engine.execute(
        panel,
        {},
        design,
        fit=fit,
        calibrate=lambda *a: lambda s: s,
        synthetic=True,
        terminal_root=repo_tmp_path / "terminal",
    )
    assert calls == [2, 2]  # calibration and selection, never empty evaluation
    cell = result["children"][0]
    assert cell["model_fitted"] is True
    assert cell["status"] == "non_evaluable" and cell["reason"] == "no_common_evaluation_support"
    assert result["synthetic_interface_fits"] == 1 and result["real_model_fits"] == 0
    assert result["oof_predictions"] == []
