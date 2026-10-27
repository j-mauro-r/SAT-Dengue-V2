"""Generated orchestration captures prove evaluation cannot enter fitted roles.

The one-cell grid and persistence/contrast seams bound this control-flow test;
preparation, common-cohort admission, thresholds and evaluation remain real.
Full-grid fitting and native freeze persistence are tested independently.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01, exp03
from sat_dengue.experiments import exp03_engine as engine
from sat_dengue.experiments.exp03_features import cohorts


def test_evaluation_label_mutation_cannot_change_fit_inputs_or_selection_policy(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(v, freq="M") + 180) for v in panel.year_month]
    panel.attrs["synthetic_generated"] = True
    design = exp03.load_protocol()["design"]
    prepared = cohorts(panel, contract, design)
    key = (1, "development_2020")
    parts, common = prepared[key]
    assert all(not f.empty for f in common.values())
    assert all(common[role].onset_target.nunique() == 2 for role in ("train", "calibration"))
    spec = dict(variant="V00", objective="onset", family="gam", horizon=1, window=key[1])
    monkeypatch.setattr(engine, "validate_design", lambda d: 1)
    monkeypatch.setattr(engine, "cell_grid", lambda d: [spec])
    monkeypatch.setattr(engine, "freeze_terminal", lambda *a, **kw: {"frozen_at": "generated"})
    monkeypatch.setattr(engine, "_contrasts", lambda *a, **kw: [])
    design["delay_variants"] = []
    original_selector = engine.select_threshold
    captures: list[dict[str, Any]] = []

    def run(changed: bool, *, poisoned_selection: bool = False) -> dict[str, Any]:
        roles = copy.deepcopy(common)
        if changed:
            # Swap one positive/negative: denominators remain valid while labels
            # at actual evaluation origins change. Raw observations are untouched.
            evaluation = roles["evaluation"]
            municipality = next(
                code
                for code, group in evaluation.groupby("municipality_code")
                if group.onset_target.nunique() == 2
            )
            local = evaluation.loc[evaluation.municipality_code.eq(municipality)]
            positive = local.index[local.onset_target.eq(1)][0]
            negative = local.index[local.onset_target.eq(0)][-1]
            evaluation.loc[[positive, negative], "onset_target"] = [0, 1]
        monkeypatch.setattr(engine, "cohorts", lambda *a: {key: (copy.deepcopy(parts), roles)})
        captured: dict[str, Any] = {"predict": []}
        captures.append(captured)

        class Predictor:
            columns = design["variants"]["V00"]

            def predict(self, frame: pd.DataFrame) -> pd.Series:
                clean = frame.copy()
                clean.attrs = {}
                captured["predict"].append(clean)
                return pd.Series(np.linspace(0.1, 0.9, len(frame)), index=frame.index)

        def fit(family: str, x: pd.DataFrame, y: pd.Series, *args: Any) -> Predictor:
            captured["fit_x"], captured["fit_y"] = x.copy(), y.copy()
            captured["fit_x"].attrs = {}
            return Predictor()

        def calibrate(scores: pd.Series, truth: pd.Series, seed: int) -> Any:
            captured["calibration_scores"] = scores.copy()
            captured["calibration_y"] = truth.copy()
            return lambda values: values

        def select(truth: pd.Series, scores: pd.Series, *args: Any) -> dict[str, Any]:
            if poisoned_selection:
                # Deliberate regression: hand evaluation labels to selection.
                truth = roles["evaluation"].onset_target.iloc[: len(truth)].copy()
                truth.index = scores.index
            captured["selection_y"], captured["selection_scores"] = truth.copy(), scores.copy()
            captured["policy"] = original_selector(truth, scores, *args)
            return dict(captured["policy"])

        monkeypatch.setattr(engine, "select_threshold", select)
        return engine.execute(
            panel,
            contract,
            design,
            fit=fit,
            calibrate=calibrate,
            synthetic=True,
            terminal_root=repo_tmp_path / ("changed" if changed else "original"),
        )

    before, after = run(False), run(True)

    def assert_fitted_roles_unchanged(left: dict[str, Any], right: dict[str, Any]) -> None:
        assert_frame_equal(left["fit_x"], right["fit_x"])
        for field in (
            "fit_y",
            "calibration_y",
            "calibration_scores",
            "selection_y",
            "selection_scores",
        ):
            assert_series_equal(left[field], right[field])
        assert left["policy"] == right["policy"]
        # These are the actual inputs passed to prediction: calibration, selection, evaluation.
        assert len(left["predict"]) == len(right["predict"]) == 3
        for a, b in zip(left["predict"], right["predict"], strict=True):
            assert_frame_equal(a, b)

    assert_fitted_roles_unchanged(captures[0], captures[1])
    for role, captured in (
        ("train", "fit_y"),
        ("calibration", "calibration_y"),
        ("selection", "selection_y"),
    ):
        assert captures[0][captured].index.equals(common[role].index)
        assert common[role].target_month.max() < common["evaluation"].target_month.min()
    native_before, native_after = (
        pd.DataFrame(before["oof_predictions"]),
        pd.DataFrame(after["oof_predictions"]),
    )
    assert not native_before.onset_target.equals(native_after.onset_target)
    assert native_before.onset_target.sum() == native_after.onset_target.sum()
    assert native_before.target_month.equals(native_after.target_month)
    assert native_before.score.equals(native_after.score)
    assert before["children"][0]["metrics"] != after["children"][0]["metrics"]
    # The comparison oracle is itself exercised against a real forbidden routing mutation.
    run(True, poisoned_selection=True)
    with pytest.raises(AssertionError):
        assert_fitted_roles_unchanged(captures[0], captures[2])
