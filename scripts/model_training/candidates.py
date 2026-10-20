"""Bounded XGBoost orchestration over the shared Stage 4 source and evaluation pipeline."""

from __future__ import annotations

import hashlib
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.training_preparation.pipeline import fingerprint

from .candidate_selection import select_and_fit
from .contract import ModelTrainingConfig, ModelTrainingError, read_json
from .events import load_event_context
from .loading import TemporalSource, load_temporal_source, load_window_dataset
from .metrics import average_precision_metric, brier_metric, evaluate_metrics
from .persistence import (
    bytes_record,
    json_bytes,
    publish_artifacts,
    serialize_table,
    verify_artifacts,
)
from .pipeline import (
    ModelTrainingResult,
    _enforce_window_rules,
    _window_base,
    build_model_training,
    code_fingerprints,
)
from .xgboost_adapter import restore_candidate

NOTEBOOK = Path("notebooks/06_candidate_models.ipynb")


def candidate_code(root: Path) -> dict[str, Any]:
    """Bind candidate execution to common code, notebook06 source and dependencies.

    Args:
        root: Repository root.

    Returns:
        Content fingerprints, excluding notebook outputs to avoid circular identities.
    """
    records = code_fingerprints(root)
    nb = read_json(root / NOTEBOOK)
    records[str(NOTEBOOK)] = bytes_record(
        json_bytes(
            {
                "cells": [
                    {"cell_type": c["cell_type"], "source": "".join(c["source"])}
                    for c in nb["cells"]
                ]
            }
        )
    )
    records["requirements-modeling.txt"] = fingerprint(root / "requirements-modeling.txt")
    return records


def probability_frame(probability: pd.Series) -> pd.DataFrame:
    """Create shared metric inputs with explicitly unavailable event alerts.

    Args:
        probability: Key-aligned binary probabilities.

    Returns:
        Shared prediction schema, with no provisional operational threshold.
    """
    return pd.DataFrame(
        dict(
            reference="xgboost",
            prediction_kind="probabilistic",
            prediction_score=probability,
            prediction_probability=probability,
            prediction_label=pd.Series(pd.NA, index=probability.index, dtype="Int64"),
        )
    )


def diagnostic_scores(y: pd.Series, probability: pd.Series) -> dict[str, Any]:
    """Report only existing AP/Brier plus support, validity and constancy diagnostics.

    Args:
        y: Observed binary labels for this diagnostic population.
        probability: Aligned probabilities.

    Returns:
        Scores and explicit support/evaluability; no new ranking metric.
    """
    return dict(
        rows=len(y),
        positives=int(y.sum()),
        ap=average_precision_metric(y, probability)["value"],
        brier=brier_metric(y, probability)["value"],
        invalid_predictions=int((~np.isfinite(probability)).sum()),
        constant_predictions=bool(probability.nunique() <= 1),
    )


def verify_candidate_bundle(
    bundle: Path, identity: dict[str, Any], source: TemporalSource
) -> dict[str, Any]:
    """Verify all persisted bytes and reproduce each saved external prediction without fitting.

    Args:
        bundle: Existing local immutable candidate directory.
        identity: Identity recomputed from current verified inputs/config/code/runtime.
        source: Current verified Stage 3 data, reused without copying it.

    Returns:
        Verified candidate manifest.
    """
    manifest = read_json(bundle / "manifest.json")
    if (
        manifest["identity"] != identity
        or bundle.name != hashlib.sha256(json_bytes(identity)).hexdigest()
    ):
        raise ModelTrainingError("Candidate identity is stale")
    payloads = {}
    for name, record in manifest["files"].items():
        path = (bundle / name).resolve()
        if not path.is_relative_to(bundle.resolve()) or fingerprint(path) != record:
            raise ModelTrainingError(f"Invalid candidate payload: {name}")
        payloads[name] = path.read_bytes()
    payloads["manifest.json"] = (bundle / "manifest.json").read_bytes()
    verify_artifacts(bundle, payloads)
    predictions = pd.read_csv(
        bundle / "predictions.csv",
        dtype={"municipality_code": "string"},
        float_precision="round_trip",
    )
    for window in manifest["windows"]:
        dataset = load_window_dataset(source, window)
        saved = predictions[predictions.window_id == window].reset_index(drop=True)
        expected_keys = _window_base(dataset)
        for key in ["municipality_code", "origin_period", "target_period", "feature_row"]:
            if saved[key].astype(str).tolist() != expected_keys[key].astype(str).tolist():
                raise ModelTrainingError("Saved prediction cohort/order changed")
        fitted = restore_candidate(
            payloads[f"{window}_model.json"], read_json(bundle / f"{window}_preparer.json")
        )
        reproduced = fitted.predict(dataset.validation_X)
        if not np.array_equal(reproduced.to_numpy(), saved.prediction_probability.to_numpy()):
            raise ModelTrainingError("Native model/preparer roundtrip differs")
    return manifest


def build_candidates(
    config: ModelTrainingConfig, *, verify_only: bool = False
) -> ModelTrainingResult:
    """Execute a frozen bounded search or verify/reuse identical artifacts without refitting.

    Args:
        config: Existing repository-scoped Stage 4 configuration.
        verify_only: Require existing current artifacts, never fit or publish.

    Returns:
        Immutable candidate bundle with models, preparation, search and evaluation evidence.
    """
    contract = read_json(config.resolve(config.contract_path))
    settings = contract["xgboost_candidate"]
    if (
        settings["threads"] != 1
        or settings["inner_cutoff_offsets_months"] != [12, 6]
        or settings["inner_validation_months"] != 6
        or settings["early_stopping"]
        or settings["threshold_policy"] is not None
        or settings["maximum_fits_per_run"] > 104
    ):
        raise ModelTrainingError("Unsupported bounded candidate protocol")
    expected_fits = len(contract["windows"]) * (2 * len(settings["configurations"]) + 1)
    if expected_fits > settings["maximum_fits_per_run"]:
        raise ModelTrainingError("Candidate fit budget exceeded before execution")
    if settings["preparer"] != {
        "encoding": "onehot",
        "numeric_scaling": "none",
        "numeric_missing": "error",
        "unknown_municipality": "explicit",
    }:
        raise ModelTrainingError("Candidate requires the declared one-hot preparation profile")
    references = build_model_training(config, verify_only=verify_only)
    source = load_temporal_source(config)
    identity = dict(
        configuration=settings,
        selection_policy=contract["selection_policy"],
        contract=fingerprint(config.resolve(config.contract_path)),
        temporal_manifest=fingerprint(source.bundle / "manifest.json"),
        reference_manifest=fingerprint(references.bundle / "manifest.json"),
        code=candidate_code(config.root),
        runtime={name: version(name) for name in ("xgboost", "scipy", "numpy", "pandas")},
    )
    bid = hashlib.sha256(json_bytes(identity)).hexdigest()
    bundle = config.resolve(settings["artifacts_dir"]) / bid
    if bundle.exists() or verify_only:
        manifest = verify_candidate_bundle(bundle, identity, source)
        return ModelTrainingResult(bundle, manifest)
    payloads: dict[str, bytes] = {}
    predictions = []
    metrics: list[dict[str, Any]] = []
    diagnostics = []
    territories = []
    calibration = []
    contexts = []
    started = perf_counter()
    total_fits = 0
    for window in contract["windows"]:
        dataset = load_window_dataset(source, window)
        _enforce_window_rules(
            dataset, reserved_start=contract["rules"]["reserved_final_block_start"]
        )
        result = select_and_fit(
            dataset.train_X,
            dataset.train_y[dataset.y_column],
            dataset.train_index,
            cutoff=dataset.cutoff,
            horizon=dataset.horizon,
            settings=settings,
            policy=contract["selection_policy"],
        )
        total_fits += result.evidence["fit_count"]
        if total_fits > settings["maximum_fits_per_run"]:
            raise ModelTrainingError("Candidate fit budget exceeded")
        probability = result.fitted.predict(dataset.validation_X)
        frame = probability_frame(probability)
        predictions.append(pd.concat([_window_base(dataset), frame], axis=1))
        context = load_event_context(
            config, source, dataset.validation_index, target_column=dataset.target_column
        )
        contexts.append(context.assign(window_id=window, horizon=dataset.horizon))
        scored = evaluate_metrics(
            "xgboost",
            dataset.validation_y[dataset.y_column],
            frame,
            dataset.validation_index,
            target_column=dataset.target_column,
            threshold_policy_declared=False,
            event_context=context,
        )
        metrics.extend(
            dict(r, window_id=window, cutoff=dataset.cutoff, horizon=dataset.horizon)
            for r in scored
        )
        payloads[f"{window}_model.json"] = result.fitted.model_bytes()
        payloads[f"{window}_preparer.json"] = json_bytes(result.fitted.preparer)
        payloads[f"{window}_search.json"] = json_bytes(result.evidence)
        payloads[f"{window}_inner_predictions.csv"] = serialize_table(result.oof)
        restored = restore_candidate(payloads[f"{window}_model.json"], result.fitted.preparer)
        if not np.array_equal(
            probability.to_numpy(), restored.predict(dataset.validation_X).to_numpy()
        ):
            raise ModelTrainingError("Model serialization roundtrip failed")
        train_score = diagnostic_scores(
            dataset.train_y[dataset.y_column], result.fitted.predict(dataset.train_X)
        )
        valid_score = diagnostic_scores(dataset.validation_y[dataset.y_column], probability)
        diagnostics.append(
            dict(
                window_id=window,
                horizon=dataset.horizon,
                selected=result.selected,
                train=train_score,
                validation=valid_score,
                ap_train_minus_validation=train_score["ap"] - valid_score["ap"],
                brier_validation_minus_train=valid_score["brier"] - train_score["brier"],
                train_target_end=str(dataset.train_index[dataset.target_column].max()),
                effective_origin_start=str(dataset.validation_index.year_month.min()),
                effective_origin_end=str(dataset.validation_index.year_month.max()),
                effective_target_start=str(dataset.validation_index[dataset.target_column].min()),
                effective_target_end=str(dataset.validation_index[dataset.target_column].max()),
                configured_target_start=str(pd.Period(dataset.cutoff, freq="M") + 1),
                configured_target_end=str(pd.Period(dataset.cutoff, freq="M") + 6),
            )
        )
        for municipality, idx in dataset.validation_index.groupby(
            "municipality_code"
        ).groups.items():
            territories.append(
                dict(
                    window_id=window,
                    horizon=dataset.horizon,
                    municipality_code=municipality,
                    **diagnostic_scores(
                        dataset.validation_y.loc[idx, dataset.y_column], probability.loc[idx]
                    ),
                )
            )
        for lower in (0.0, 0.2, 0.4, 0.6, 0.8):
            mask = probability.ge(lower) & (
                probability.lt(lower + 0.2) if lower < 0.8 else probability.le(1)
            )
            calibration.append(
                dict(
                    window_id=window,
                    bin_lower=lower,
                    rows=int(mask.sum()),
                    mean_probability=float(probability[mask].mean()) if mask.any() else None,
                    observed_fraction=float(dataset.validation_y.loc[mask, dataset.y_column].mean())
                    if mask.any()
                    else None,
                )
            )
    comparison = pd.concat(
        [pd.read_csv(references.bundle / "metrics.csv"), pd.DataFrame(metrics)], ignore_index=True
    )
    means = (
        comparison[comparison.metric.isin(["average_precision", "brier"])]
        .groupby(["horizon", "reference", "metric"], dropna=False)
        .agg(value=("value", "mean"), windows=("value", "count"))
        .reset_index()
    )
    summary = dict(
        status="PASS",
        windows=diagnostics,
        fit_count=total_fits,
        inner_fits=total_fits - len(contract["windows"]),
        outer_fits=len(contract["windows"]),
        elapsed_seconds=perf_counter() - started,
        threshold_policy=None,
        scientific_gates_approved=False,
        calibration="Descriptive fixed bins only; no fitted calibrator or operative threshold.",
        comparison_semantics=(
            "Equal weight across four windows per horizon; diagnostic references, no champion."
        ),
    )
    payloads.update(
        {
            "predictions.csv": serialize_table(pd.concat(predictions, ignore_index=True)),
            "evaluation_context.csv": serialize_table(pd.concat(contexts, ignore_index=True)),
            "metrics.csv": serialize_table(pd.DataFrame(metrics)),
            "comparison.csv": serialize_table(comparison),
            "horizon_means.csv": serialize_table(means),
            "territorial_diagnostics.csv": serialize_table(pd.DataFrame(territories)),
            "calibration_diagnostics.csv": serialize_table(pd.DataFrame(calibration)),
            "run_summary.json": json_bytes(summary),
        }
    )
    manifest = dict(
        schema="stage4-xgboost-v1",
        bundle_id=bid,
        identity=identity,
        windows=contract["windows"],
        stage3_temporal_bundle=str(source.bundle.relative_to(config.root)),
        reference_bundle=str(references.bundle.relative_to(config.root)),
        preparation="Stage3 functions; fresh train-only JSON state; source data not copied.",
        files={name: bytes_record(data) for name, data in payloads.items()},
    )
    payloads["manifest.json"] = json_bytes(manifest)
    if candidate_code(config.root) != identity["code"]:
        raise ModelTrainingError("Code changed during candidate execution")
    publish_artifacts(bundle.parent, bid, payloads)
    verify_candidate_bundle(bundle, identity, source)
    return ModelTrainingResult(bundle, manifest)


def candidate_summary(result: ModelTrainingResult, root: Path) -> dict[str, Any]:
    """Return bounded notebook metadata and equal-window diagnostic comparison.

    Args:
        result: Verified candidate artifact result.
        root: Repository root for portable paths.

    Returns:
        Summary without individual health records.
    """
    run = read_json(result.bundle / "run_summary.json")
    means = pd.read_csv(result.bundle / "horizon_means.csv").astype(object)
    means = means.where(pd.notna(means), None)
    return dict(
        status="PASS",
        candidate_bundle=str(result.bundle.relative_to(root)),
        bundle_id=result.manifest["bundle_id"],
        windows=len(run["windows"]),
        fit_count=run["fit_count"],
        elapsed_seconds=run["elapsed_seconds"],
        comparison=means.to_dict(orient="records"),
        threshold_policy=None,
    )
