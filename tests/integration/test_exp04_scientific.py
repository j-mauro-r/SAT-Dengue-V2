"""Five generated-only scientific-runner cases; immutable real bundles are never opened."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments import exp04_oof as oof
from sat_dengue.experiments import exp04_scientific as science
from sat_dengue.experiments import exp04_scientific_runner as runner
from sat_dengue.experiments.exp03_1_reporting import _frame_state, _restore_frame
from sat_dengue.experiments.exp04 import apply_calibrator
from sat_dengue.experiments.exp04_contract import digest

REAL_PROTOCOL = runner.scientific_protocol


@pytest.fixture
def generated(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    p = deepcopy(REAL_PROTOCOL())
    plan, cfg = oof.calendar(), oof.configuration()
    scores, jobs, models = [], [], {}
    codes = ("50001", "50002", "73001", "73002")
    for job in plan["jobs"]:
        cutoff = str(pd.Period(job["origin_month"], freq="M") - 1)
        state = {
            "historical_fit": {
                "job_id": job["job_id"],
                "configuration_id": plan["configuration_id"],
                "training_keys_sha256": digest([]),
            },
            "family": job["family"],
            "columns": [],
            "envelope_columns": [],
            "support": {},
            "preparer": {},
        }
        native = b"generated_frozen_native_bytes_never_loaded"
        identity = hashlib.sha256(canonical_bytes(state) + native).hexdigest()
        preparer_id = digest({"historical_fit": state["historical_fit"], "preparer": {}})
        models[identity] = {"state": state, "native": native}
        jobs.append(
            {
                **job,
                "predictor_id": identity,
                "preparer_id": preparer_id,
                "training_target_cutoff": cutoff,
                "training_keys_sha256": digest([]),
                "score_keys_sha256": digest(codes),
                "score_rows": 4,
                "positives": 2,
                "negatives": 2,
            }
        )
        for index, code in enumerate(codes):
            truth = index % 2
            row = {
                "municipality_code": code,
                "target_month": job["target_month"],
                "origin_month": job["origin_month"],
                "forecast_issue_date": job["origin_month"] + "-01",
                "target_date": job["target_month"] + "-01",
                "label_available_date": str(
                    pd.Period(job["target_month"], freq="M").end_time.date()
                ),
                "training_cutoff": str(pd.Period(cutoff, freq="M").end_time.date()),
                "training_target_cutoff": cutoff,
                "family": job["family"],
                "horizon": job["horizon"],
                "objective": job["objective"],
                "raw_score": 0.9 if truth else 0.1,
                "truth": truth,
                "error_class": "onset" if truth else "no_excess",
                "role": "calibration",
                "uses": job["uses"],
                "predictor_id": identity,
                "preparer_id": preparer_id,
                "configuration_id": plan["configuration_id"],
                "baseline_id": "M00-REPLAY-v1",
                "source": "historical_refit",
                "job_id": job["job_id"],
            }
            row["score_id"] = digest(row)
            scores.append(row)
    counts = {
        **plan["counts"],
        "prediction_rows": len(scores),
        "generated_rows": len(scores),
        "retained_rows": 0,
    }
    body = {
        "schema": "exp04-oof-bundle-v1",
        "experiment_id": "EXP04",
        "calendar": plan,
        "jobs": jobs,
        "scores": scores,
        "counts": counts,
    }
    oof_path = repo_tmp_path / "exp04-generated-oof"
    oof.publish(body, models, oof_path)
    p["oof"]["bundle_id"] = digest(body)
    p["oof"]["counts"]["prediction_rows"] = len(scores)
    refs = {}
    for group in plan["groups"]:
        original = next(
            g
            for g in cfg["oof_history_assessment"]["cell_groups"]
            if all(g[k] == group[k] for k in ("cut", "horizon", "objective"))
        )
        roles = {}
        for role in ("calibration", "selection", "evaluation"):
            start, end = original["roles"][role][:2]
            rows = []
            for month in pd.period_range(start, end, freq="M"):
                for index, code in enumerate(codes):
                    truth = index % 2
                    rows.append(
                        {
                            "municipality_code": code,
                            "target_month": str(month),
                            "year_month": str(month - group["horizon"]),
                            "onset_target": truth,
                            "excess_target": truth,
                            "error_type": "onset" if truth else "no_excess",
                            "raw_score": 0.9 if truth else 0.1,
                            "truth": truth,
                            "error_class": "onset" if truth else "no_excess",
                        }
                    )
            frame = pd.DataFrame(rows)
            frame["score"] = apply_calibrator(
                frame, {"method": "sigmoid", "coefficient": 8.0, "intercept": -4.0}
            )
            frame["alert"] = frame.score.ge(0.5)
            roles[role] = {"frame": _frame_state(frame)}
        refs[group["reference_cell_id"]] = SimpleNamespace(
            metadata={"roles": roles, "window": {k: v[:2] for k, v in original["roles"].items()}},
            calibrator=SimpleNamespace(coefficient=8.0, intercept=-4.0),
            threshold=0.5,
        )
    monkeypatch.setattr(runner, "scientific_protocol", lambda: deepcopy(p))
    monkeypatch.setattr(runner, "references", lambda: refs)
    monkeypatch.setattr(
        runner, "git_identity", lambda: {"git_revision": "a" * 40, "git_dirty": False}
    )
    return {
        "p": p,
        "oof": oof_path,
        "id": p["oof"]["bundle_id"],
        "root": repo_tmp_path,
        "output": repo_tmp_path / "exp04-generated-scientific",
    }


def receipt_and_approval(g: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt = runner.preflight(g["oof"], g["id"], g["output"])
    return receipt, runner.approval_record(receipt, "Mauricio", "Independent Reviewer")


def test_preflight_and_exact_authorization(
    generated: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    p = REAL_PROTOCOL()
    assert p["protocol_sha256"] == digest({k: v for k, v in p.items() if k != "protocol_sha256"})
    receipt, approval = receipt_and_approval(generated)
    assert len(receipt["cells"]) == 282
    assert {c["arm"] for c in receipt["cells"] if c["status"] == "CONDITIONAL_SUPPORT"} == {
        "B2",
        "C2",
    }
    assert receipt["predictor_fits"] == receipt["calibrator_fits"] == receipt["mlflow_writes"] == 0
    assert receipt == runner.preflight(generated["oof"], generated["id"], generated["output"])
    runner.authorize(receipt, approval)
    for name, value in (
        ("receipt_sha256", "b" * 64),
        ("git_revision", "b" * 40),
        ("scientific_protocol_sha256", "b" * 64),
        ("oof_bundle_id", "b" * 64),
        ("predictor_refits_authorized", True),
        ("G5_approval", True),
        ("champion_selection", True),
        ("calibration_selection_evaluation_authorized", False),
    ):
        with pytest.raises(PermissionError):
            runner.authorize(receipt, {**approval, name: value})
    with pytest.raises(PermissionError):
        runner.approval_record(receipt, "Mauricio", "Mauricio")
    with pytest.raises(ValueError, match="OOF identity"):
        runner.preflight(generated["oof"], "0" * 64, generated["output"])
    baseline_path = Path(oof.configuration()["reconstruction_identity"]["bundle_path"])
    for protected in (generated["oof"], baseline_path):
        with pytest.raises(ValueError, match="disjoint"):
            runner.preflight(generated["oof"], generated["id"], protected / "exp04-invalid")
    for protected in (generated["oof"], baseline_path, generated["output"]):
        with pytest.raises(ValueError, match="cannot write inside"):
            runner.write_record(approval, protected / "approval.json", receipt)
    with monkeypatch.context() as changed:
        changed.setattr(
            runner, "git_identity", lambda: {"git_revision": "b" * 40, "git_dirty": False}
        )
        with pytest.raises(PermissionError, match="changed"):
            runner.authorize(receipt, approval)
    with monkeypatch.context() as changed:
        bad = generated["root"] / "protocol.json"
        bad.write_bytes(canonical_bytes({**p, "B_primary": 9}))
        changed.setattr(runner, "PROTOCOL", bad)
        with pytest.raises(ValueError, match="protocol"):
            REAL_PROTOCOL()
    data = generated["oof"] / "result.json"
    data.write_bytes(data.read_bytes() + b" ")
    with pytest.raises(ValueError, match="integrity failure"):
        runner.preflight(generated["oof"], generated["id"], generated["output"])


def test_consumes_oof_without_predictor_fits(
    generated: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.experiments import exp03_persistence, exp04_execution

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Predictor fit or OOF regeneration reached")

    for module, names in (
        (oof, ("generate", "fit_native")),
        (exp03_persistence, ("fit_native",)),
        (exp04_execution, ("generate", "execute_oof")),
    ):
        for name in names:
            monkeypatch.setattr(module, name, forbidden)
    receipt, approval = receipt_and_approval(generated)
    # Each test owns an independent ignored reservation root.
    root = generated["root"].relative_to(Path.cwd()) / "reservations"
    monkeypatch.setattr(runner, "RESERVATIONS", str(root))
    before = (generated["oof"] / "result.json").read_bytes()
    result = runner.execute(receipt, approval)
    checked = runner.validate_bundle(generated["output"], result["bundle_id"])
    assert checked["execution_counters"]["predictor_fits"] == 0
    assert checked["execution_counters"]["calibrator_fits"] > 0
    assert checked["execution_counters"]["threshold_selections"] > 0
    assert len(checked["cells"]) == 282
    controls = [c for c in checked["cells"] if c["objective"] == "excess_control"]
    assert len(controls) == 12 and {c["arm"] for c in controls} == {"A0"}
    assert all(c["metrics"]["budget_excess"] is None for c in controls)
    assert before == (generated["oof"] / "result.json").read_bytes()
    with pytest.raises(ValueError, match="new disjoint"):
        runner.execute(receipt, approval)
    retry = runner.preflight(generated["oof"], generated["id"], generated["root"] / "exp04-retry")
    with pytest.raises(ValueError, match="duplicate or interrupted"):
        runner.execute(retry, runner.approval_record(retry, "Mauricio", "Independent Reviewer"))


def test_development_selection_freezes_before_stress(generated: dict[str, Any]) -> None:
    p = generated["p"]
    inputs, _ = runner.load_inputs(generated["oof"], generated["id"], p)
    first = science.run_phases(inputs, p)
    changed = deepcopy(inputs)
    for source in changed.values():
        if source["group"]["cut"] != "stress_2024":
            continue
        frame = _restore_frame(source["evaluation"])
        frame["truth"] = 1 - frame.truth
        source["evaluation"] = _frame_state(frame)
    second = science.run_phases(dict(reversed(list(changed.items()))), p)
    assert first["frozen"] == second["frozen"] and first["freeze_id"] == second["freeze_id"]
    assert all(option["A"]["selected"] == "A1" for option in first["frozen"].values())
    assert all(option["B"]["selected"] == "B2" for option in first["frozen"].values())
    assert all(option["C"]["selected"] == "C0" for option in first["frozen"].values())
    assert all(row["B0_B1_identical"] for row in first["B0_B1_identity"])
    assert all(
        c["cut"] == "stress_2024" and c["freeze_id"] == first["freeze_id"]
        for c in first["cells"]
        if c["arm"] == "D"
    )
    # No eligible development window means no dependent policy or D fallback.
    candidates = deepcopy(
        [
            c
            for c in first["cells"]
            if c["family"] == "gam" and c["horizon"] == 1 and c["objective"] == "onset"
        ]
    )
    for c in candidates:
        if c["arm"] in ("A1", "A2", "A3") and c["cut"] != "stress_2024":
            c["metrics"]["common_FA_rate"] = 1.01
    assert science.choose(candidates, "A", p)["selected"] is None
    for c in candidates:
        if c["arm"] in ("A1", "A2", "A3") and c["cut"] != "stress_2024":
            c["metrics"]["common_FA_rate"] = 0
            c["metrics"]["detected"] = 0
    assert science.choose(candidates, "A", p)["selected"] is None


def test_b2_c2_support_is_cell_local(generated: dict[str, Any]) -> None:
    p = generated["p"]
    inputs, _ = runner.load_inputs(generated["oof"], generated["id"], p)
    for horizon in (1, 2):
        source = next(
            deepcopy(v)
            for v in inputs.values()
            if v["group"]["horizon"] == horizon
            and v["group"]["family"] == "gam"
            and v["group"]["cut"] == "development_2020"
            and v["group"]["objective"] == "onset"
        )
        counters = {"calibrator_fits": 0, "threshold_selections": 0}
        assert (
            science.policy_cell(source, "B2", 12, "isotonic", "C0", p, counters)["status"]
            == "evaluable"
        )
        altered = deepcopy(source)
        frame = _restore_frame(altered["history"])
        frame["truth"] = 0
        frame.loc[frame.index[-19:], "truth"] = 1
        altered["history"] = _frame_state(frame)
        rejected = science.policy_cell(altered, "B2", 12, "isotonic", "C0", p, counters)
        assert (
            rejected["status"] == "NOT_EVALUABLE" and rejected["reason"] == "isotonic_class_support"
        )
        blocks = science.selection_blocks(_restore_frame(source["selection"]), horizon, p)
        assert blocks.selection_block.nunique() == 2
        for block in ("1", "2"):
            bad = deepcopy(source)
            selection = blocks.copy()
            selection.loc[selection.selection_block.eq(block), "truth"] = 1
            bad["selection"] = _frame_state(selection)
            state = {"method": "sigmoid", "coefficient": 8.0, "intercept": -4.0}
            assert (
                science.policy_cell(bad, "C2", 12, "original", "C2", p, counters, state)["status"]
                == "NOT_EVALUABLE"
            )
            assert (
                science.policy_cell(bad, "C0", 12, "original", "C0", p, counters, state)["status"]
                == "evaluable"
            )


def test_publication_reload_and_semantic_rejections(
    generated: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt, approval = receipt_and_approval(generated)
    monkeypatch.setattr(
        runner, "RESERVATIONS", str(generated["root"].relative_to(Path.cwd()) / "reservations")
    )
    summary = runner.execute(receipt, approval)
    result = runner.validate_bundle(generated["output"], summary["bundle_id"])
    assert result["G5"] == "NOT_APPROVED" and result["champion"] == "not_selected"
    assert result["uncertainty"] == "UNAVAILABLE"
    # Reload is read-only and cannot refit even calibrators.
    monkeypatch.setattr(science, "fit_calibrator", lambda *a, **k: pytest.fail("Validator fitting"))
    assert (
        runner.validate_bundle(generated["output"], summary["bundle_id"])["bundle_id"]
        == summary["bundle_id"]
    )
    for index, change in enumerate(("metrics", "freeze", "predictor_fits", "G5")):
        corrupt = deepcopy({k: v for k, v in result.items() if k != "bundle_id"})
        if change == "metrics":
            corrupt["cells"][0]["metrics"]["detected"] += 1
        elif change == "freeze":
            corrupt["frozen"]["gam/T+1"]["A"]["selected"] = "A3"
            corrupt["freeze_id"] = digest(corrupt["frozen"])
        elif change == "predictor_fits":
            corrupt["execution_counters"]["predictor_fits"] = 1
        else:
            corrupt["G5"] = "APPROVED"
        destination = generated["root"] / f"exp04-corrupt-{index}"
        identity = runner.publish(corrupt, destination)
        with pytest.raises(ValueError):
            runner.validate_bundle(destination, identity)
    with pytest.raises(FileExistsError):
        runner.publish({k: v for k, v in result.items() if k != "bundle_id"}, generated["output"])
    (generated["output"] / "result.json").write_text(json.dumps({**result, "champion": "selected"}))
    with pytest.raises(ValueError, match="integrity"):
        runner.validate_bundle(generated["output"], summary["bundle_id"])
