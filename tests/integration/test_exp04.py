from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp04 import (
    apply_calibrator,
    calibration_window,
    evaluate_frozen,
    fit_calibrator,
    temporal_roles,
    threshold_policy,
)
from sat_dengue.experiments.exp04_baseline import audit_baseline, common_exposure, paired_support
from sat_dengue.experiments.exp04_contract import digest
from sat_dengue.experiments.exp04_runner import (
    compare_policies,
    functional_run,
    preflight,
    write_result,
)


def score_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["50001", "73001", "50001", "73001"],
            "target_month": ["2019-01", "2019-01", "2019-02", "2019-02"],
            "raw_score": [0.1, 0.3, 0.6, 0.8],
            "truth": [0, 0, 1, 1],
            "error_class": ["no_excess", "no_excess", "onset", "onset"],
        }
    )


def test_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Control 2: preserve mandatory M00 and identical common-cohort exposure."""
    monkeypatch.chdir(tmp_path)
    missing = audit_baseline()
    assert missing["status"] == "BLOCKED_BASELINE"
    assert missing["reconstruction_identity"] is None
    directory = Path("tmp/baseline")
    directory.mkdir(parents=True)
    (directory / "bundle.json").write_text(json.dumps({"source_variant": "M00"}))
    (directory / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="exact original"):
        audit_baseline(directory)
    with pytest.raises(ValueError, match="repository-local"):
        audit_baseline(Path("/etc"))
    frame = score_frame()
    assert common_exposure(frame) == 4 / 12
    assert paired_support(frame, frame.iloc[::-1])["common_exposure"] == 4 / 12
    assert paired_support(frame, frame.iloc[:3])["status"] == "NOT_EVALUABLE"
    changed = frame.copy()
    changed.loc[0, "truth"] = 1
    assert paired_support(frame, changed)["status"] == "NOT_EVALUABLE"
    changed = frame.copy()
    changed.loc[0, "raw_score"] = 0.2
    assert paired_support(frame, changed)["reason"] == "base_predictor_scores_differ"
    assert (
        paired_support(frame.assign(horizon=1), frame.assign(horizon=2))["reason"]
        == "paired_dimensions_differ"
    )
    with pytest.raises(ValueError, match="duplicate"):
        common_exposure(pd.concat([frame, frame]))
    later = frame.copy()
    later.loc[0, "target_month"] = "2025-01"
    with pytest.raises(ValueError, match="2025"):
        common_exposure(later)


def temporal_frame(start: str, end: str, horizon: int = 2) -> pd.DataFrame:
    rows = []
    for i, month in enumerate(pd.period_range(start, end, freq="M")):
        for j, code in enumerate(("50001", "50002", "73001", "73002")):
            truth = int((i + j) % 3 == 0)
            rows.append(
                {
                    "municipality_code": code,
                    "target_month": str(month),
                    "forecast_issue_date": str((month - horizon).start_time.date()),
                    "target_date": str(month.start_time.date()),
                    "label_available_date": str((month.start_time + pd.Timedelta(days=14)).date()),
                    "training_cutoff": "2014-01-01",
                    "raw_score": float(((i * 3 + j * 7) % 19 + 1) / 21),
                    "truth": truth,
                    "error_class": "onset" if truth else "no_excess",
                    "selection_block": str(month.year) + ("a" if month.month < 7 else "b"),
                }
            )
    return pd.DataFrame(rows)


def test_temporal() -> None:
    """Control 3: mature OOF roles, fixed policies and whole ties with adversarial cases."""
    cal = temporal_frame("2016-01", "2018-12")
    sel = temporal_frame("2019-04", "2019-12")
    ev = temporal_frame("2020-03", "2020-12")
    kwargs: dict[str, Any] = {
        "horizon": 2,
        "calibration_cutoff": "2019-01-15",
        "decision_date": "2019-12-31",
    }
    assert temporal_roles(cal, sel, ev, **kwargs)["status"] == "evaluable"
    for change, message in (
        ({"training_cutoff": "2020-01-01"}, "In-sample"),
        ({"label_available_date": "2020-01-01"}, "Immature"),
    ):
        corrupt = cal.copy()
        for key, value in change.items():
            corrupt.loc[0, key] = value
        with pytest.raises(ValueError, match=message):
            temporal_roles(corrupt, sel, ev, **kwargs)
    with pytest.raises(ValueError, match="horizon drift"):
        temporal_roles(cal, sel, ev, **{**kwargs, "horizon": 1})
    with pytest.raises(ValueError, match="Evaluation precedes"):
        temporal_roles(cal, sel, ev, **{**kwargs, "decision_date": "2020-02-01"})
    for months in (None, 12, 24, 36):
        chosen, support = calibration_window(
            cal, months=months, last_mature_month="2018-12", cutoff="2019-01-15"
        )
        assert support["status"] == "evaluable"
        assert chosen.target_month.nunique() == (months or 36)
    gap = cal.loc[cal.target_month.ne("2018-06")]
    assert (
        calibration_window(gap, months=12, last_mature_month="2018-12", cutoff="2019-01-15")[1][
            "status"
        ]
        == "NOT_EVALUABLE"
    )
    assert fit_calibrator(cal, method="isotonic", seed=1)["status"] == "NOT_EVALUABLE"
    for method in ("sigmoid", "isotonic", "identity"):
        state = fit_calibrator(cal, method=method, seed=1, minimum_class_support=2)
        scored = sel.copy()
        scored["score"] = apply_calibrator(sel, state)
        for policy in ("C0", "C1", "C2"):
            threshold = threshold_policy(scored, policy=policy)
            assert threshold.get("status") != "NOT_EVALUABLE"
            assert threshold["false_alerts"] / common_exposure(sel) <= 1
            if policy == "C2":
                alerts = (
                    pd.Series(False, index=scored.index)
                    if threshold["threshold"] is None
                    else scored.score.ge(threshold["threshold"])
                )
                for _, block in scored.groupby("selection_block"):
                    assert (
                        int((alerts.loc[block.index] & block.truth.eq(0)).sum())
                        / common_exposure(block)
                        <= 1
                    )
        assert (
            threshold_policy(scored, policy="C0")["threshold"]
            == threshold_policy(scored, policy="C1")["threshold"]
        )
        before = json.dumps(state, sort_keys=True)
        rows, metrics = evaluate_frozen(
            ev, state, threshold["threshold"], bins=10, objective="onset", historical_exposure=10
        )
        assert json.dumps(state, sort_keys=True) == before
        assert metrics["common_exposure"] == len(ev) / 12
        assert metrics["historical_FA_rate"] == metrics["false_alerts"] / 10
        assert metrics["common_FA_rate"] == metrics["false_alerts"] / (len(ev) / 12)
        assert metrics["uncertainty"]["status"] == "UNAVAILABLE"
        assert len(rows) == len(ev)
    one = scored.assign(selection_block="one")
    assert threshold_policy(one, policy="C2")["status"] == "NOT_EVALUABLE"
    tied = scored.copy()
    tied["score"] = 0.5
    selected = threshold_policy(tied, policy="C1")
    assert selected["threshold"] is None  # Cannot split a tied group to meet the budget.
    assert selected["alerts"] == 0
    interleaved = scored.assign(selection_block=[i % 2 for i in range(len(scored))])
    with pytest.raises(ValueError, match="chronological"):
        threshold_policy(interleaved, policy="C2")
    with pytest.raises(ValueError, match="excess-control"):
        threshold_policy(scored, policy="C1", objective="excess_control")


def test_functional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Control 4: minimal generated execution and dry-run with no real-data substitute."""
    ready = preflight(Path("tmp/exp04-missing-baseline-fixture"))
    assert ready["status"] == "BLOCKED_BASELINE"
    assert all(a["status"] == "NOT_EVALUABLE" for a in ready["arms"].values())
    assert ready["model_fits"] == ready["calibrator_fits"] == ready["threshold_selections"] == 0
    result = functional_run()
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.configuration import validate_parameters
    from sat_dengue.hooks import TrackingHooks
    from sat_dengue.pipeline_registry import register_pipelines

    parameters = {"profile": "exp04_functional", "tracking": "disabled"}
    catalog = DataCatalog({"parameters": MemoryDataset(parameters)})
    graph = register_pipelines()["exp04_functional"]
    hooked = TrackingHooks()
    hooked.before_pipeline_run({"pipeline_names": ["exp04_functional"]}, catalog)
    assert hooked.tracker is None
    runner_result = SequentialRunner().run(graph, catalog)
    assert runner_result["exp04_functional_result"].load()["bundle_id"] == result["bundle_id"]
    for changed_parameters in (
        dict(parameters, tracking="enabled"),
        dict(parameters, experiment_id="EXP04"),
    ):
        with pytest.raises(ValueError, match="EXP04"):
            validate_parameters(changed_parameters)
    with pytest.raises(ValueError, match="must match"):
        hooked.before_pipeline_run({"pipeline_names": ["replay"]}, catalog)
    assert result["evidence_type"] == "generated_functional_only"
    assert result["reference_is_M00"] is False
    assert len(result["metrics"]) == 22
    assert len(result["contrasts"]) == 16
    assert {r["horizon"] for r in result["metrics"]} == {1, 2}
    assert len(result["thresholds"]) == len(result["calibrators"]) == 22
    assert all(m["objective"] == "onset" for m in result["metrics"])
    assert result["excess_control"]["metrics"]["objective"] == "excess_control"
    assert result["excess_control"]["metrics"]["budget_excess"] is None
    assert result["D"]["status"] == "NOT_EVALUABLE"
    assert set(result["scientific_hypotheses"].values()) == {"NOT_EVALUATED"}
    assert set(result["execution_counters"].values()) == {0}
    assert result["strata"] and result["fixed_uncalibrated_diagnostics"]
    assert {s["department"] for s in result["strata"]} == {"50", "73"}
    frame = pd.DataFrame(result["predictions"])
    assert frame.groupby(["horizon", "arm"]).size().nunique() == 1
    assert not frame.duplicated(["horizon", "arm", "municipality_code", "target_month"]).any()
    fields = {
        "raw_score",
        "forecast_issue_date",
        "label_available_date",
        "training_cutoff",
        "calibration_cutoff",
        "decision_date",
    }
    assert fields <= set(frame)
    a = frame.loc[frame.arm.eq("C0") & frame.horizon.eq(2)].reset_index(drop=True)
    b = frame.loc[frame.arm.eq("C1") & frame.horizon.eq(2)].reset_index(drop=True)
    ma = next(m for m in result["metrics"] if m["arm"] == "C0" and m["horizon"] == 2)
    mb = next(m for m in result["metrics"] if m["arm"] == "C1" and m["horizon"] == 2)
    changed = dict(mb, common_exposure=999)
    assert compare_policies(a, b, ma, changed)["status"] == "NOT_EVALUABLE"
    monkeypatch.chdir(tmp_path)
    write_result(result, Path("tmp/exp04-functional-test"))
    assert (
        json.loads(Path("tmp/exp04-functional-test/result.json").read_text())["bundle_id"]
        == result["bundle_id"]
    )
    with pytest.raises(FileExistsError):
        write_result(result, Path("tmp/exp04-functional-test"))
    with pytest.raises(ValueError):
        write_result(result, Path("tmp/old-experiment"))


def test_reproducibility(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Control 5: exact complete-output repeatability, identities and precision."""
    from sat_dengue.experiments import exp04_runner

    first, second = functional_run(), functional_run()
    assert canonical_bytes(first) == canonical_bytes(second)
    original_id = first["bundle_id"]
    assert digest({k: v for k, v in first.items() if k != "bundle_id"}) == original_id
    assert first["provenance"]["code_sha256"]
    assert first["provenance"]["packages"]
    assert set(first["input_sha256_by_horizon"]) == {"1", "2"}
    assert first["input_sha256_by_horizon"]["1"] != first["input_sha256_by_horizon"]["2"]
    assert canonical_bytes(json.loads(canonical_bytes(first))) == canonical_bytes(first)
    original_generator = exp04_runner.generated_scores

    def changed_scores(start: str, end: str, horizon: int) -> pd.DataFrame:
        frame = original_generator(start, end, horizon)
        frame.loc[0, "raw_score"] += 0.001
        return frame

    monkeypatch.setattr(exp04_runner, "generated_scores", changed_scores)
    changed = functional_run()
    assert changed["bundle_id"] != original_id
    assert changed["input_sha256_by_horizon"] != first["input_sha256_by_horizon"]
    monkeypatch.chdir(tmp_path)
    write_result(first, Path("tmp/exp04-reproducibility"))
    assert Path("tmp/exp04-reproducibility/result.json").read_bytes() == canonical_bytes(first)
