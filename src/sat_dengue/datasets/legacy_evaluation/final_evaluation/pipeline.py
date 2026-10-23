"""Six fixed final fits with immutable artifacts, guarded replay and no fallback training."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_evaluation.model_evaluation.contract import ModelEvaluationConfig
from sat_dengue.datasets.legacy_evaluation.model_evaluation.pipeline import (
    build_model_evaluation,
)
from sat_dengue.final_evaluation.prediction import predict_procedure as predict_procedure
from scripts.model_training.candidate_families import fit_model, restore_model, validate_grid
from scripts.model_training.persistence import (
    bytes_record,
    json_bytes,
    publish_artifacts,
    serialize_table,
    verify_artifacts,
)
from scripts.model_training.references import persistence_reference
from scripts.training_preparation.pipeline import fingerprint

from .cohorts import Cohort, load_cohorts, validate_cohort
from .evaluation import evaluate_horizon
from .protocol import (
    AUTHORIZATION,
    NOTEBOOK,
    PROPOSAL_BUNDLE,
    PROPOSAL_SHA,
    checked_manifest,
    code_fingerprints,
    load_archived_proposal,
    load_proposal,
    require_authorization,
)

BASE = Path("artifacts/model_final_evaluation")


def execute_bundle(
    root: Path,
    proposal: dict[str, Any],
    cohorts: dict[int, Cohort],
    identity: dict[str, Any],
    *,
    verify_only: bool = False,
) -> dict[str, Any]:
    """Execute the common engine after authorization and source preflight by its caller.

    Args:
        root: Output repository, or isolated synthetic-test directory.
        proposal: Verified protocol.
        cohorts: Both fully preflighted horizon populations.
        identity: Code, inputs, configuration and human authorization identities.
        verify_only: Never fit, create or repair any missing artifact.

    Returns:
        Current run receipt with actual new-fit counts and persisted scientific summary.
    """
    from sat_dengue.datasets.legacy_training.contract import resolve_root

    if root.resolve() == resolve_root():
        raise PermissionError(
            "2025 is consumed; real fitting/tuning/selection is forbidden; use evaluation_replay"
        )
    if set(cohorts) != {1, 2}:
        raise ValueError("Both horizons must pass before the first fit")
    procedures = proposal["procedures"]
    if len(procedures) != 6 or {(p["candidate"], p["horizon"]) for p in procedures} != {
        (f, h) for f in ["xgboost", "lightgbm", "gam"] for h in [1, 2]
    }:
        raise ValueError("Exactly six distinct final procedures required")
    audits = [validate_cohort(cohorts[h], proposal) for h in [1, 2]]
    for p in procedures:
        validate_grid(p["candidate"], [p["retained_internal_components"]["selected_parameters"]])
        if p["future_preparer"]["spec"] != dict(
            encoding="onehot",
            numeric_missing="error",
            numeric_scaling="none",
            unknown_municipality="explicit",
        ):
            raise ValueError("Adapter preparation differs from the frozen specification")
        if (
            p["retained_calibrator"]["calibration_choice"]
            != p["retained_threshold"]["calibration_choice"]
        ):
            raise ValueError("Retained threshold/calibration mismatch")
        threshold = p["retained_threshold"]["selected_threshold"]
        calibration = p["retained_calibrator"]
        if threshold is None or not np.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("Unavailable frozen threshold before fitting")
        if calibration["calibration_choice"] not in {"original", "sigmoid"}:
            raise ValueError("Unknown retained calibration")
        if calibration["calibration_choice"] == "sigmoid" and (
            not calibration.get("available")
            or not np.isfinite(
                [calibration.get("coefficient", np.nan), calibration.get("intercept", np.nan)]
            ).all()
        ):
            raise ValueError("Unavailable frozen sigmoid before fitting")
    bundle_id = hashlib.sha256(json_bytes(identity)).hexdigest()
    bundle = root / BASE / bundle_id
    existing = bundle.exists()
    if verify_only and not existing:
        raise FileNotFoundError("No final bundle for current identity; verify never trains")
    manifest = checked_manifest(bundle) if existing else None
    if manifest is not None and manifest["identity"] != identity:
        raise ValueError("Final identity mismatch")
    fit_record: dict[str, Any] = dict(
        proposal_sha256=PROPOSAL_SHA,
        identity=bundle_id,
        status="running",
        attempted_model_calls=0,
        completed_model_fits=0,
        completed_preparer_fits=0,
        hyperparameter_search=0,
        calibrator_fits=0,
        threshold_selection=0,
    )
    ledger = root / BASE / ".fit_attempts" / f"{PROPOSAL_SHA}.json"
    if not existing:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        # An interrupted or different-identity run requires explicit recovery;
        # never silently repeat any of the six scientifically authorized fits.
        with ledger.open("x") as stream:
            stream.write(json_bytes(fit_record).decode())
    payloads: dict[str, bytes] = {}
    predictions: dict[int, dict[str, pd.DataFrame]] = {
        h: {"persistence": persistence_reference(cohorts[h].X, horizon=h)} for h in [1, 2]
    }
    for p in procedures:
        family, h = p["candidate"], p["horizon"]
        cohort = cohorts[h]
        prefix = f"{family}_t{h}"
        model_name, prep_name = f"{prefix}_model.json", f"{prefix}_preparer.json"
        if existing:
            model_data = (bundle / model_name).read_bytes()
            preparer = json.loads((bundle / prep_name).read_text())
            model = restore_model(family, model_data, preparer)
        else:
            if fit_record["attempted_model_calls"] >= 6:
                raise ValueError("Final model-fit budget exhausted")
            fit_record["attempted_model_calls"] += 1
            ledger.write_bytes(json_bytes(fit_record))
            try:
                model = fit_model(
                    family,
                    cohort.train_X,
                    cohort.train_y,
                    p["retained_internal_components"]["selected_parameters"],
                    seed=42,
                    threads=1,
                )
            except BaseException:
                fit_record["status"] = (
                    "failed; adapter may have partially fitted; explicit recovery required"
                )
                ledger.write_bytes(json_bytes(fit_record))
                raise
            # Each frozen adapter executes exactly one train-only representation fit.
            fit_record["completed_model_fits"] += 1
            fit_record["completed_preparer_fits"] += 1
            ledger.write_bytes(json_bytes(fit_record))
            preparer, model_data = model.preparer, model.model_bytes()
        if (
            preparer["spec"] != p["future_preparer"]["spec"]
            or preparer["input_columns"] != p["future_preparer"]["input_columns"]
        ):
            raise ValueError("Saved preparation violates retained specification/order")
        if preparer["fit_X_fingerprint"] != bytes_record(serialize_table(cohort.train_X)):
            raise ValueError("Preparer was not fitted on this exact training X")
        prediction = predict_procedure(model, cohort.X, p)
        restored = restore_model(family, model_data, preparer)
        replay = predict_procedure(restored, cohort.X, p)
        pd.testing.assert_frame_equal(prediction, replay, check_exact=True)
        predictions[h][family] = prediction
        payloads[model_name] = model_data
        payloads[prep_name] = json_bytes(preparer)
        payloads[f"{prefix}_retained_decisions.json"] = json_bytes(p)
        payloads[f"{prefix}_training_provenance.json"] = json_bytes(
            dict(
                X=bytes_record(serialize_table(cohort.train_X)),
                y=bytes_record(serialize_table(cohort.train_y.to_frame("y"))),
                keys=bytes_record(serialize_table(cohort.train_index)),
                target_max=str(cohort.train_index.target_period.max()),
                rows=len(cohort.train_y),
            )
        )
    comparisons, metrics, intervals, linked = [], [], [], []
    for h in [1, 2]:
        cohort = cohorts[h]
        comparison, detail, uncertainty, draws = evaluate_horizon(
            cohort, predictions[h], proposal["rules"]["proposed_final"]["uncertainty"]
        )
        comparisons.append(comparison)
        metrics.append(detail)
        intervals.append(uncertainty)
        payloads[f"t{h}_resampled_month_indices.csv"] = serialize_table(pd.DataFrame(draws))
        payloads[f"t{h}_evaluation_context.csv"] = serialize_table(cohort.context)
        payloads[f"t{h}_evaluation_index.csv"] = serialize_table(cohort.index)
        for family, prediction in predictions[h].items():
            linked.append(
                pd.concat([cohort.index, prediction], axis=1).assign(
                    candidate=family, horizon=h, y_true=cohort.y
                )
            )
    tables = dict(
        comparison=pd.concat(comparisons, ignore_index=True),
        metrics=pd.concat(metrics, ignore_index=True),
        uncertainty=pd.concat(intervals, ignore_index=True),
        predictions=pd.concat(linked, ignore_index=True),
    )
    payloads.update({f"{name}.csv": serialize_table(frame) for name, frame in tables.items()})
    payloads["preflight.json"] = json_bytes(
        dict(cohorts=audits, all_six_preflighted_before_first_fit=True)
    )
    fits = dict(models=6, preparers=6, searches=0, calibrators=0, threshold_selections=0)
    summary = dict(
        bundle=str(bundle.relative_to(root)),
        proposal_sha256=PROPOSAL_SHA,
        historical_fits=fits,
        comparison=json.loads(tables["comparison"].to_json(orient="records")),
        G5="NOT_APPROVED",
        champion="not_selected",
        interpretation=(
            "retrospective; marginal_intervals; "
            "holdout_consumed_for_comparison_not_independent_postselection_test"
        ),
    )
    accounting = (
        json.loads((bundle / "fit_accounting.json").read_text())
        if existing
        else {
            k: fit_record[k]
            for k in (
                "attempted_model_calls",
                "completed_model_fits",
                "completed_preparer_fits",
                "hyperparameter_search",
                "calibrator_fits",
                "threshold_selection",
            )
        }
    )
    if accounting != dict(
        attempted_model_calls=6,
        completed_model_fits=6,
        completed_preparer_fits=6,
        hyperparameter_search=0,
        calibrator_fits=0,
        threshold_selection=0,
    ):
        raise ValueError("Final actual fit accounting differs from the six-fit protocol")
    payloads["fit_accounting.json"] = json_bytes(accounting)
    payloads["run_summary.json"] = json_bytes(summary)
    payloads["manifest.json"] = json_bytes(
        dict(
            schema="stage5-final-evaluation-v1",
            bundle_id=bundle_id,
            identity=identity,
            files={n: bytes_record(d) for n, d in payloads.items()},
        )
    )
    if existing:
        verify_artifacts(bundle, payloads)
    else:
        publish_artifacts(root / BASE, bundle_id, payloads, existing_policy="error")
        fit_record["status"] = "complete"
        ledger.write_bytes(json_bytes(fit_record))
    return dict(
        summary=summary,
        new_model_fits=0 if existing else 6,
        new_preparer_fits=0 if existing else 6,
        mode="verify" if verify_only else ("reuse" if existing else "fit"),
    )


def run_final(root: Path, *, verify_only: bool = False) -> dict[str, Any]:
    """Require human authority before data loading, then execute or verify frozen science.

    Args:
        root: Repository root.
        verify_only: Load and reproduce only; never fallback train.

    Returns:
        Final artifact and current-run fit receipt.
    """
    from sat_dengue.datasets.legacy_training.contract import resolve_root

    if root.resolve() == resolve_root():
        raise PermissionError(
            "2025 is consumed; real fitting/tuning/selection is forbidden; use evaluation_replay"
        )
    decision = require_authorization(root)
    proposal = load_proposal(root)
    source = build_model_evaluation(ModelEvaluationConfig(root), verify_only=True)
    if str(source.bundle.relative_to(root)) != proposal["identity_inputs"]["input_bundle"]:
        raise ValueError("Live dependency differs from the exact frozen proposal")
    code = code_fingerprints(root)
    cohorts, inputs = load_cohorts(root, proposal)
    identity = dict(
        proposal_sha256=PROPOSAL_SHA,
        proposal_manifest=fingerprint(root / PROPOSAL_BUNDLE / "manifest.json"),
        code=code,
        inputs=inputs,
        authorization=decision,
        authorization_file=fingerprint(root / AUTHORIZATION),
        seed=42,
        threads=1,
        frozen_notebook=proposal["identity_inputs"]["code"][str(NOTEBOOK)],
        versions=proposal["identity_inputs"]["versions"],
    )
    result = execute_bundle(root, proposal, cohorts, identity, verify_only=verify_only)
    if code_fingerprints(root) != code or any(
        fingerprint(root / name) != record for name, record in inputs.items()
    ):
        raise ValueError("Code/input changed during final evaluation; do not accept outputs")
    return result


def readiness(root: Path) -> dict[str, Any]:
    """Inspect immutable evidence and report live dependency compatibility.

    Args:
        root: Repository root.

    Returns:
        Bounded status with archived identity and explicit live dependency drift.

    Notes:
        Post-evaluation refactors may change live development dependencies. Readiness
        reports that drift without treating it as proposal corruption. Scientific
        execution remains fail-closed because :func:`run_final` calls
        :func:`load_proposal` directly.
    """
    proposal = load_archived_proposal(root)
    try:
        load_proposal(root)
        dependency_status = "exact_frozen_match"
        dependency_error = None
    except ValueError as exc:
        dependency_status = "changed_after_freeze"
        dependency_error = str(exc)
    try:
        require_authorization(root)
        status = "human_authorization_recorded"
    except PermissionError:
        status = "awaiting_explicit_human_G4_protocol_and_execution_acceptance"
    return dict(
        status=status,
        proposal_sha256=PROPOSAL_SHA,
        live_frozen_dependencies=dependency_status,
        live_dependency_error=dependency_error,
        scientific_execution_allowed=dependency_status == "exact_frozen_match",
        procedures=6,
        new_fits=0,
        reserved_results_read=False,
        G5="NOT_APPROVED",
        original_notebook_code=proposal["identity_inputs"]["code"][str(NOTEBOOK)],
        final_route_code=code_fingerprints(root),
        development_summary=json.loads((root / PROPOSAL_BUNDLE / "run_summary.json").read_text()),
    )
