"""Existing EXP04 runner wiring for historical OOF preparation, never MLflow.

Only execute_oof reads admitted scientific sources. Source-free preflight and
synthetic tests never call it. Policy evaluation remains a separate explicit
caller action with predeclared settings, not an automatic policy search.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03_1_reporting import _restore_frame
from sat_dengue.experiments.exp03_preflight import safe_path
from sat_dengue.experiments.exp04 import (
    apply_calibrator,
    calibration_window,
    evaluate_frozen,
    fit_calibrator,
    temporal_roles,
    threshold_policy,
)
from sat_dengue.experiments.exp04_contract import digest
from sat_dengue.experiments.exp04_oof import (
    calendar,
    configuration,
    generate,
    history,
    publish,
    reload_bundle,
)


def preflight() -> dict[str, Any]:
    """Configuration-only calendar/counts; no private or historical-artifact reads."""
    plan = calendar()
    return {
        "schema": "exp04-oof-preflight-v1",
        "experiment_id": "EXP04",
        "status": "OOF_IMPLEMENTED_NOT_EXECUTED",
        "baseline_id": "M00-REPLAY-v1",
        "calendar": plan,
        "scientific_execution_authorized": False,
        "source_identity_status": "pending_future_admission",
        "C2": "NOT_EVALUABLE_until_two_chronological_blocks_have_both_classes",
        "scientific_hypotheses": "NOT_EVALUATED",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "private_source_reads": 0,
        "model_fits": 0,
        "calibrator_fits": 0,
        "mlflow_writes": 0,
    }


def references() -> dict[str, Any]:
    """Called only by future execution; verify the pinned immutable replay first."""
    from sat_dengue.experiments.exp03_1_reporting import read_real_bundle
    from sat_dengue.experiments.exp03_persistence import load_cell

    cfg = configuration()
    identity = cfg["reconstruction_identity"]
    root = safe_path(identity["bundle_path"])
    for name, field in (
        ("bundle.json", "bundle_sha256"),
        ("manifest.json", "manifest_sha256"),
        ("replay/manifest.json", "replay_manifest_sha256"),
    ):
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != identity[field]:
            raise ValueError("Pinned M00-REPLAY-v1 bytes differ")
    read_real_bundle(root, identity["bundle_id"])
    cells = {}
    for group in cfg["oof_history_assessment"]["cell_groups"]:
        for cell_id in group["cells"].values():
            cell = load_cell(root / "replay" / cell_id)
            if cell.metadata["scientific_cell"]["variant"] != "M00":
                raise ValueError("EXP04 cannot consume a non-M00 predictor")
            cells[cell_id] = cell
    return cells


def prepare(panel: pd.DataFrame, contract: dict[str, Any]) -> dict[tuple[int, str], pd.DataFrame]:
    """Reuse exact EXP03.1 paired eligibility, H5 and M00 feature recipes."""
    from sat_dengue.experiments.exp03_1_features import paired_cohort
    from sat_dengue.experiments.exp03_1_runner import _prepare

    if panel.year_month.ge("2025-01").any():
        raise ValueError("EXP04 rejects 2025 sources")
    cfg = configuration()
    frames = {}
    for horizon in (1, 2):
        audits: dict[int, dict[str, Any]] = {}
        frame = _prepare(panel, contract, horizon, audits)
        dates = audits[horizon]["source_months"]
        if not isinstance(dates, pd.DataFrame):
            raise ValueError("Missing M00 feature date provenance")
        for name in cfg["ordered_predictors"]:
            if (
                name not in dates
                or dates[name].isna().any()
                or (dates[name].astype(str) > audits[horizon]["keys"].year_month.astype(str)).any()
            ):
                raise ValueError("Future or unknown M00 feature source")
        for objective in ("onset",) if horizon == 1 else ("onset", "excess_control"):
            labels = ["onset_target"] + (["excess_target"] if objective != "onset" else [])
            common, _ = paired_cohort(
                frame, base_predictors=cfg["ordered_predictors"], labels=labels
            )
            frames[horizon, objective] = common.loc[
                common.eligible_at_t.fillna(False).astype(bool)
            ].copy()
    return frames


def reference_role(cell: Any, group: dict[str, Any], role: str) -> pd.DataFrame:
    """Trim existing raw selection/evaluation rows; never substitute target scores."""
    frame = _restore_frame(cell.metadata["roles"][role]["frame"])
    start, end = group["roles"][role]
    frame = frame.loc[frame.target_month.between(start, end)].copy()
    expected = {str(m) for m in pd.period_range(start, end, freq="M")}
    if set(frame.target_month) != expected:
        raise ValueError("Missing reference role month support")
    horizon = group["horizon"]
    cutoff = cell.metadata["window"]["train"][1]
    frame["forecast_issue_date"] = frame.year_month + "-01"
    frame["target_date"] = frame.target_month + "-01"
    frame["label_available_date"] = frame.target_month.map(
        lambda m: str(pd.Period(m, freq="M").end_time.date())
    )
    frame["training_cutoff"] = str(pd.Period(cutoff, freq="M").end_time.date())
    frame["truth"] = frame[
        "onset_target" if group["objective"] == "onset" else "excess_target"
    ].astype(int)
    frame["error_class"] = frame.error_type.astype(str)
    frame["horizon"], frame["objective"] = horizon, group["objective"]
    frame["family"], frame["cut"] = group["family"], group["cut"]
    # Retain any predeclared blocks. Do not invent a partition to make C2 pass.
    return frame


def policy_inputs(
    result: dict[str, Any],
    group: dict[str, Any],
    cell: Any,
    months: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Bridge the OOF bundle to unchanged calibration/selection/frozen evaluation."""
    cal = history(result, group, months)
    selection = reference_role(cell, group, "selection")
    evaluation = reference_role(cell, group, "evaluation")
    temporal_roles(
        cal,
        selection,
        evaluation,
        horizon=group["horizon"],
        calibration_cutoff=group["calibration_cutoff"],
        decision_date=group["decision_date"],
    )
    chosen, info = calibration_window(
        cal,
        months=months,
        last_mature_month=group["roles"]["calibration"][1],
        cutoff=group["calibration_cutoff"],
    )
    if info["status"] != "evaluable":
        raise ValueError("EXP04 insufficient OOF window/class support")
    return chosen, selection, evaluation


def evaluate_policy(
    result: dict[str, Any],
    group: dict[str, Any],
    cell: Any,
    *,
    months: int,
    method: str,
    selector: str,
    bins: int,
    minimum_class_support: int | None = None,
) -> dict[str, Any]:
    """Use only a caller's predeclared policy; no new selection/search/fallback.

    The existing onset selector is never applied to the separate excess control.
    No policy or confirmatory scientific input is chosen by OOF generation.
    """
    cal, selection, evaluation = policy_inputs(result, group, cell, months)
    state = fit_calibrator(
        cal,
        method="sigmoid" if method == "original" else method,
        seed=configuration()["seed"],
        minimum_class_support=minimum_class_support,
    )
    if state.get("status") == "NOT_EVALUABLE":
        return state
    if group["objective"] == "excess_control":
        threshold = {
            "threshold": cell.threshold,
            "source": "frozen_excess_control_reference_no_onset_budget_reselection",
        }
    else:
        selection["score"] = apply_calibrator(selection, state)
        threshold = threshold_policy(selection, policy=selector)
    if threshold.get("status") == "NOT_EVALUABLE":
        return threshold
    rows, metrics = evaluate_frozen(
        evaluation, state, threshold["threshold"], bins=bins, objective=group["objective"]
    )
    return {
        "predictions": rows.to_dict(orient="records"),
        "metrics": metrics,
        "calibrator": state,
        "threshold": threshold,
    }


def execute_oof(destination: Path) -> dict[str, Any]:
    """Future explicit entry point. No tracker construction or historical writes."""
    from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
    from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs
    from sat_dengue.experiments.exp01_preflight import git_identity
    from sat_dengue.experiments.exp03_1_preflight import observed_environment
    from sat_dengue.experiments.exp03_1_runner import _apply_coverage, _read_coverage
    from sat_dengue.experiments.exp03_admission import admit_sources, reverify, verified_snapshot
    from sat_dengue.experiments.exp03_preflight import descriptor
    from sat_dengue.experiments.exp04_runner import _provenance

    target = safe_path(str(destination))
    if (
        target.exists()
        or not target.is_relative_to(Path.cwd().resolve() / "tmp")
        or not (target.name.startswith("exp04-"))
    ):
        raise ValueError("EXP04 needs a new tmp/exp04-* destination before source admission")
    plan = calendar()
    code = _provenance()
    environment = observed_environment()
    provenance = {
        "code_sha256": code["code_sha256"],
        "protocol_sha256": code["protocol_sha256"],
        "parent_protocol_sha256": code["parent_protocol_sha256"],
        "configuration_id": plan["configuration_id"],
        "calendar_id": plan["calendar_id"],
        "git": git_identity(),
        "environment": environment,
        "environment_sha256": digest(environment),
        "evidence_type": "retrospective_consolidated_OOF",
    }
    cells = references()
    sources = descriptor()
    receipt = {"sources": sources, "expected_source_sha256": sources["expected_source_sha256"]}
    config = PreparationConfig(Path.cwd())
    admission = admit_sources(receipt, config)
    with verified_snapshot(config, admission) as snapshot:
        inputs = prepare_exp01_inputs(snapshot)
        coverage = _read_coverage(snapshot, inputs.contract)
    panel = _apply_coverage(inputs.panel, coverage)
    frames = prepare(panel, inputs.contract)
    reverify(admission)
    result, models = generate(frames, cells, plan)
    # The adapter is exercised for every authorized window before publication;
    # this validates roles and class support without fitting any calibrator.
    for group in plan["groups"]:
        for size in (12, 24, 36):
            policy_inputs(result, group, cells[group["reference_cell_id"]], size)
    result["source_admission"] = admission
    result["source_admission_sha256"] = digest(admission)
    result["baseline_reconstruction"] = configuration()["reconstruction_identity"]
    result["provenance"] = provenance
    result["C2"] = {"status": "NOT_EVALUABLE", "reason": "no_predeclared_supported_block_partition"}
    result["policy_execution"] = "NOT_EXECUTED_NO_AUTOMATIC_POLICY_CHOICE"
    reverify(admission)
    if _provenance()["code_sha256"] != provenance["code_sha256"]:
        raise ValueError("EXP04 code changed during historical fitting")
    publish(result, models, target)
    checked = reload_bundle(target)
    return {
        "status": "OOF_GENERATED",
        "bundle_id": checked["bundle_id"],
        "counts": checked["counts"],
        "path": str(target),
    }
