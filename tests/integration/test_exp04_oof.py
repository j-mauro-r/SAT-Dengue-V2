"""Five bounded synthetic EXP04 OOF cases; no sources, trackers or native fits."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp03_1_reporting import _frame_state
from sat_dengue.experiments.exp03_persistence import NativePredictor
from sat_dengue.experiments.exp04 import temporal_roles
from sat_dengue.experiments.exp04_contract import digest
from sat_dengue.experiments.exp04_execution import evaluate_policy, policy_inputs, preflight
from sat_dengue.experiments.exp04_oof import (
    calendar,
    configuration,
    generate,
    history,
    publish,
    reload_bundle,
    restore_predictor,
    retained_scores,
)


class TinyModel:
    def __init__(self, preparer: dict[str, Any]) -> None:
        self.preparer = preparer

    def predict(self, frame: pd.DataFrame) -> pd.Series:
        return frame.municipality_code.map(
            {"50001": 0.12345678912345678, "73001": 0.8765432198765432}
        ).astype(float)

    def model_bytes(self) -> bytes:
        return canonical_bytes(self.preparer)


def tiny_fit(
    family: str,
    X: pd.DataFrame,
    y: pd.Series,
    parameters: dict[str, Any],
    seed: int,
) -> NativePredictor:
    cfg = configuration()
    assert list(X) == cfg["ordered_predictors"]
    assert parameters == cfg["family_parameters"][family] and seed == cfg["seed"]
    assert len(X) == len(y) and set(y) == {0, 1}
    return NativePredictor(
        family,
        TinyModel({"training_indices": X.index.tolist()}),
        list(X),
        ["municipality_code"],
        {},
    )


def fixture(horizon: int = 1, objective: str = "onset") -> tuple[dict[str, Any], dict, dict]:
    plan = calendar()
    group = next(
        g
        for g in plan["groups"]
        if g["cut"] == "development_2020"
        and g["horizon"] == horizon
        and g["objective"] == objective
        and g["family"] == "gam"
    )
    plan = {
        **plan,
        "groups": [group],
        "jobs": [j for j in plan["jobs"] if j["job_id"] in group["jobs"]],
    }
    plan["counts"] = {
        **plan["counts"],
        "groups": 1,
        "historical_refits": sum(j["source"] == "historical_refit" for j in plan["jobs"]),
        "retained_origin_jobs": sum(j["source"] == "retained" for j in plan["jobs"]),
        "group_month_uses": 36,
        "A1_A2_A3_cells": 3,
    }
    plan["calendar_id"] = digest({k: v for k, v in plan.items() if k != "calendar_id"})
    cfg = configuration()
    rows = []
    for month in pd.period_range("2012-07", "2020-12", freq="M"):
        for truth, municipality in enumerate(("50001", "73001")):
            row: dict[str, Any] = {name: float(month.ordinal) for name in cfg["ordered_predictors"]}
            row.update(
                municipality_code=municipality,
                municipality_code_feature=municipality,
                year_month=str(month - horizon),
                target_month=str(month),
                onset_target=truth,
                excess_target=truth,
                error_type="onset" if truth else "no_excess",
            )
            rows.append(row)
    frame = pd.DataFrame(rows)
    original = next(
        g
        for g in cfg["oof_history_assessment"]["cell_groups"]
        if g["cut"] == group["cut"] and g["horizon"] == horizon and g["objective"] == objective
    )
    training = frame.loc[frame.target_month.le(original["roles"]["train"][1])]
    predictor = tiny_fit(
        "gam",
        training[cfg["ordered_predictors"]],
        training.onset_target,
        cfg["family_parameters"]["gam"],
        cfg["seed"],
    )
    role_frames = {}
    for name, definition in original["roles"].items():
        part = frame.loc[frame.target_month.between(definition[0], definition[1])].copy()
        if name != "train":
            part["raw_score"] = predictor.predict(part[cfg["ordered_predictors"]])
        role_frames[name] = {"frame": _frame_state(part)}
    cell = SimpleNamespace(
        predictor=predictor,
        metadata={
            "scientific_cell": {
                "variant": "M00",
                "cell_id": group["reference_cell_id"],
                "family": "gam",
                "horizon": horizon,
                "objective": objective,
                "predictors": cfg["ordered_predictors"],
            },
            "window": {"train": ["2012-01", "2018-12"]},
            "roles": role_frames,
        },
    )
    cell.threshold = 0.5
    return plan, {(horizon, objective): frame}, {group["reference_cell_id"]: cell}


def test_calibration_selection_boundary() -> None:
    plan, frames, refs = fixture()
    result, _ = generate(frames, refs, plan, fit=tiny_fit)
    group = plan["groups"][0]
    cal, selection, evaluation = policy_inputs(result, group, refs[group["reference_cell_id"]], 36)
    assert cal.target_month.max() == "2019-05"
    assert cal.label_available_date.max() < selection.forecast_issue_date.min()
    assert selection.forecast_issue_date.min() == "2019-06-01"
    assert selection.target_month.nunique() == 5
    assert all(j["training_target_cutoff"] < j["origin_month"] for j in result["jobs"])
    boundary = next(j for j in result["jobs"] if j["target_month"] == "2019-01")
    assert (
        boundary["source"] == "historical_refit" and boundary["training_target_cutoff"] == "2018-11"
    )
    corrupt = cal.copy()
    corrupt.loc[corrupt.index[-1], "label_available_date"] = "2019-06-01"
    with pytest.raises(ValueError, match="Immature"):
        temporal_roles(
            corrupt,
            selection,
            evaluation,
            horizon=1,
            calibration_cutoff=group["calibration_cutoff"],
            decision_date=group["decision_date"],
        )
    # No partition is invented to make C2 evaluable on a short block.
    assert (
        evaluate_policy(
            result,
            group,
            refs[group["reference_cell_id"]],
            months=12,
            method="sigmoid",
            selector="C2",
            bins=10,
        )["status"]
        == "NOT_EVALUABLE"
    )


def test_selection_evaluation_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    plan, frames, refs = fixture(2)
    result, _ = generate(frames, refs, plan, fit=tiny_fit)
    group = plan["groups"][0]
    cal, selection, evaluation = policy_inputs(result, group, refs[group["reference_cell_id"]], 12)
    assert selection.target_month.min() == "2019-08"
    assert selection.target_month.max() == "2019-11" and selection.target_month.nunique() == 4
    assert selection.label_available_date.max() < evaluation.forecast_issue_date.min()
    assert evaluation.forecast_issue_date.min() == "2019-12-01"
    for frame in (cal, selection, evaluation):
        assert (
            pd.PeriodIndex(frame.target_month, freq="M")
            == pd.PeriodIndex(frame.forecast_issue_date, freq="M") + 2
        ).all()
    with pytest.raises(ValueError, match="Evaluation precedes"):
        temporal_roles(
            cal,
            selection,
            evaluation,
            horizon=2,
            calibration_cutoff=group["calibration_cutoff"],
            decision_date="2019-12-01",
        )
    evaluated = evaluate_policy(
        result,
        group,
        refs[group["reference_cell_id"]],
        months=12,
        method="sigmoid",
        selector="C0",
        bins=10,
    )
    assert len(evaluated["predictions"]) == len(evaluation)
    assert evaluated["metrics"]["objective"] == "onset"
    control_plan, control_frames, control_refs = fixture(2, "excess_control")
    control, _ = generate(control_frames, control_refs, control_plan, fit=tiny_fit)
    import sat_dengue.experiments.exp04_execution as execution

    monkeypatch.setattr(
        execution,
        "threshold_policy",
        lambda *a, **kw: pytest.fail("Excess control must not select on the onset budget"),
    )
    control_group = control_plan["groups"][0]
    evaluated = evaluate_policy(
        control,
        control_group,
        control_refs[control_group["reference_cell_id"]],
        months=12,
        method="original",
        selector="C0",
        bins=10,
    )
    assert evaluated["metrics"]["objective"] == "excess_control"
    assert evaluated["metrics"]["budget_excess"] is None


def test_inventory_without_duplicate_origins() -> None:
    plan = calendar()
    assert plan["counts"]["historical_refits"] == 726
    assert plan["counts"]["retained_origin_jobs"] == 120
    assert plan["counts"]["group_month_uses"] == 1296
    assert plan["counts"]["A1_A2_A3_cells"] == 108
    assert {j["family"] for j in plan["jobs"]} == {"gam", "lightgbm", "xgboost"}
    assert {(j["horizon"], j["objective"]) for j in plan["jobs"]} == {
        (1, "onset"),
        (2, "onset"),
        (2, "excess_control"),
    }
    generated = [j for j in plan["jobs"] if j["source"] == "historical_refit"]
    keys = [(j["family"], j["horizon"], j["objective"], j["origin_month"]) for j in generated]
    assert len(keys) == len(set(keys))
    assert any(len(j["uses"]) > 1 for j in generated)
    for group in plan["groups"]:
        assert group["generate_or_replace_by_window"] == dict(
            zip(
                ("12", "24", "36"),
                (8, 20, 32) if group["horizon"] == 1 else (9, 21, 33),
                strict=True,
            )
        )
        assert len(group["jobs"]) == len(set(group["jobs"])) == 36
    assert preflight()["private_source_reads"] == preflight()["model_fits"] == 0


def test_reuse_and_replacement() -> None:
    plan, frames, refs = fixture()
    result, _ = generate(frames, refs, plan, fit=tiny_fit)
    assert {r["target_month"] for r in result["scores"] if r["source"] == "retained"} == {
        "2019-02",
        "2019-03",
        "2019-04",
        "2019-05",
    }
    job = next(j for j in plan["jobs"] if j["source"] == "retained")
    expected = frames[1, "onset"].loc[frames[1, "onset"].target_month.eq(job["target_month"])]
    cell = refs[job["reference_cell_id"]]
    retained = retained_scores(job, expected, cell)
    copied = [r for r in result["scores"] if r["job_id"] == job["job_id"]]
    assert [r["raw_score"] for r in copied] == retained.raw_score.tolist()
    with pytest.raises(ValueError, match="strict training cutoff"):
        retained_scores({**job, "origin_month": "2018-12"}, expected, cell)
    corrupt = deepcopy(cell)
    raw_state = corrupt.metadata["roles"]["calibration"]["frame"]
    index = raw_state["columns"].index("raw_score")
    target_index = raw_state["columns"].index("target_month")
    row = next(row for row in raw_state["rows"] if row[target_index] == job["target_month"])
    row[index] = float(np.nextafter(row[index], 1.0))
    with pytest.raises(ValueError, match="full precision"):
        retained_scores(job, expected, corrupt)
    with pytest.raises(ValueError, match="paired support"):
        retained_scores(job, expected.iloc[:1], cell)
    missing = frames[1, "onset"].loc[~frames[1, "onset"].target_month.eq("2016-06")]
    with pytest.raises(ValueError, match="missing historical"):
        generate(
            {(1, "onset"): missing}, refs, plan, fit=lambda *a: pytest.fail("fit before support")
        )


def test_persistence_and_rejections(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan, frames, refs = fixture()
    result, models = generate(frames, refs, plan, fit=tiny_fit)
    with pytest.raises(ValueError, match="expanding"):
        calendar(windows=(12, 24, 36, 48))
    with pytest.raises(ValueError, match="2025"):
        history(result, {**plan["groups"][0], "cut": "development_2025"}, 12)
    with pytest.raises(ValueError, match="2025"):
        generate(
            {(1, "onset"): frames[1, "onset"].assign(target_month="2025-01")},
            refs,
            plan,
            fit=lambda *a: pytest.fail("2025 fit"),
        )
    monkeypatch.chdir(repo_tmp_path)
    destination = Path("tmp/exp04-synthetic-oof")
    publish(result, models, destination)
    restored = reload_bundle(destination)
    assert restored["scores"] == result["scores"]
    assert restored["jobs"] == result["jobs"]
    import sat_dengue.model_training.candidate_families as families

    monkeypatch.setattr(
        families, "restore_model", lambda family, native, preparer: TinyModel(json.loads(native))
    )
    identity = result["scores"][0]["predictor_id"]
    predictor = restore_predictor(destination, identity)
    assert predictor.model.preparer == models[identity]["state"]["preparer"]
    assert predictor.model.model_bytes() == models[identity]["native"]
    with pytest.raises(FileExistsError):
        publish(result, models, destination)
    (destination / "models" / identity / "model.native").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="integrity failure"):
        reload_bundle(destination)
