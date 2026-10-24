"""Bounded candidate orchestration over the shared Stage 4 source and evaluation pipeline."""

from __future__ import annotations

import hashlib
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.metrics import evaluate_metrics
from sat_dengue.model_training.candidate_families import restore_model
from sat_dengue.model_training.candidate_selection import SelectionResult, select_and_fit
from sat_dengue.model_training.workflow import diagnostic_scores as diagnostic_scores
from sat_dengue.model_training.workflow import probability_frame as probability_frame
from sat_dengue.model_training.xgboost_adapter import fit_candidate

from .contract import ModelTrainingConfig, ModelTrainingError, read_json
from .events import load_event_context
from .loading import TemporalSource, load_temporal_source, load_window_dataset
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
        fitted = restore_model(
            identity["family"],
            payloads[f"{window}_model.json"],
            read_json(bundle / f"{window}_preparer.json"),
        )
        reproduced = fitted.predict(dataset.validation_X)
        if not np.array_equal(reproduced.to_numpy(), saved.prediction_probability.to_numpy()):
            raise ModelTrainingError("Native model/preparer roundtrip differs")
    return manifest


def build_candidates(
    config: ModelTrainingConfig,
    *,
    verify_only: bool = False,
    family: str = "xgboost",
    ablation: str | None = None,
    full_model: ModelTrainingResult | None = None,
    references: ModelTrainingResult | None = None,
    source: TemporalSource | None = None,
) -> ModelTrainingResult:
    """Execute a frozen bounded search or verify/reuse identical artifacts without refitting.

    Args:
        config: Existing repository-scoped Stage 4 configuration.
        verify_only: Require existing current artifacts, never fit or publish.
        family: Declared model family.
        ablation: Optional fixed-parameter XGBoost experiment.
        full_model: Verified complete XGBoost result supplying selected parameters.
        references: Already verified references for a suite run.
        source: Already verified source for a suite run.

    Returns:
        Immutable candidate bundle with models, preparation, search and evaluation evidence.
    """
    if (config.root / "src/sat_dengue").is_dir():
        from sat_dengue.datasets.training_legacy import LegacyTrainingLoader

        return LegacyTrainingLoader.legacy_result(config, family, ablation)
    contract = read_json(config.resolve(config.contract_path))
    settings = contract[f"{family}_candidate"]
    excluded = contract["ablations"][ablation] if ablation else []
    name = f"xgboost_{ablation}" if ablation else family
    if ablation and (family != "xgboost" or full_model is None):
        raise ModelTrainingError("Ablation requires verified full XGBoost selection")
    if (
        settings["threads"] != 1
        or settings["inner_cutoff_offsets_months"] != [12, 6]
        or settings["inner_validation_months"] != 6
        or settings["early_stopping"]
        or settings["threshold_policy"] is not None
        or settings["maximum_fits_per_run"] > 104
    ):
        raise ModelTrainingError("Unsupported bounded candidate protocol")
    expected_fits = len(contract["windows"]) * (
        1 if ablation else 2 * len(settings["configurations"]) + 1
    )
    if expected_fits > settings["maximum_fits_per_run"]:
        raise ModelTrainingError("Candidate fit budget exceeded before execution")
    if settings["preparer"] != {
        "encoding": "onehot",
        "numeric_scaling": "none",
        "numeric_missing": "error",
        "unknown_municipality": "explicit",
    }:
        raise ModelTrainingError("Candidate requires the declared one-hot preparation profile")
    references = references or build_model_training(config, verify_only=verify_only)
    source = source or load_temporal_source(config)
    identity = dict(
        configuration=settings,
        family=family,
        experiment=name,
        excluded_columns=excluded,
        full_model_manifest=fingerprint(full_model.bundle / "manifest.json")
        if full_model
        else None,
        selection_policy=contract["selection_policy"],
        contract=fingerprint(config.resolve(config.contract_path)),
        temporal_manifest=fingerprint(source.bundle / "manifest.json"),
        reference_manifest=fingerprint(references.bundle / "manifest.json"),
        code=candidate_code(config.root),
        runtime={
            name: version(name)
            for name in (
                "xgboost",
                "lightgbm",
                "scikit-learn",
                "threadpoolctl",
                "scipy",
                "numpy",
                "pandas",
            )
        },
    )
    bid = hashlib.sha256(json_bytes(identity)).hexdigest()
    bundle = config.resolve(settings["artifacts_dir"]) / (ablation or "full") / bid
    if bundle.exists() or verify_only:
        manifest = verify_candidate_bundle(bundle, identity, source)
        return ModelTrainingResult(bundle, manifest)
    payloads: dict[str, bytes] = {}
    predictions = []
    metrics: list[dict[str, Any]] = []
    diagnostics = []
    territories = []
    territorial_metrics: list[dict[str, Any]] = []
    calibration = []
    contexts = []
    started = perf_counter()
    total_fits = 0
    for window in contract["windows"]:
        dataset = load_window_dataset(source, window)
        _enforce_window_rules(
            dataset, reserved_start=contract["rules"]["reserved_final_block_start"]
        )
        if ablation and full_model is not None:
            selected = read_json(full_model.bundle / f"{window}_search.json")["selected"]
            fit_started = perf_counter()
            fitted = fit_candidate(
                dataset.train_X,
                dataset.train_y[dataset.y_column],
                selected,
                seed=settings["seed"],
                threads=settings["threads"],
                excluded=excluded,
            )
            evidence = dict(
                selected=selected,
                fit_count=1,
                folds=[],
                candidates=[],
                selection_source=str(full_model.bundle.relative_to(config.root)),
                excluded_columns=excluded,
                outer_fit_seconds=perf_counter() - fit_started,
                train_keys=bytes_record(serialize_table(dataset.train_index)),
                validation_keys=bytes_record(serialize_table(dataset.validation_index)),
            )
            result = SelectionResult(
                fitted, selected, evidence, pd.DataFrame(columns=["configuration_id"])
            )
        else:
            result = select_and_fit(
                dataset.train_X,
                dataset.train_y[dataset.y_column],
                dataset.train_index,
                cutoff=dataset.cutoff,
                horizon=dataset.horizon,
                settings=settings,
                policy=contract["selection_policy"],
                family=family,
            )
        total_fits += result.evidence["fit_count"]
        if total_fits > settings["maximum_fits_per_run"]:
            raise ModelTrainingError("Candidate fit budget exceeded")
        probability = result.fitted.predict(dataset.validation_X)
        frame = probability_frame(probability, name)
        predictions.append(pd.concat([_window_base(dataset), frame], axis=1))
        context = load_event_context(
            config, source, dataset.validation_index, target_column=dataset.target_column
        )
        contexts.append(context.assign(window_id=window, horizon=dataset.horizon))
        scored = evaluate_metrics(
            name,
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
        restored = restore_model(family, payloads[f"{window}_model.json"], result.fitted.preparer)
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
            local_metrics = evaluate_metrics(
                name,
                dataset.validation_y.loc[idx, dataset.y_column].reset_index(drop=True),
                frame.loc[idx].reset_index(drop=True),
                dataset.validation_index.loc[idx].reset_index(drop=True),
                target_column=dataset.target_column,
                threshold_policy_declared=False,
                event_context=context.loc[idx].reset_index(drop=True),
            )
            territorial_metrics.extend(
                dict(r, window_id=window, horizon=dataset.horizon, municipality_code=municipality)
                for r in local_metrics
            )
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
            "territorial_metrics.csv": serialize_table(pd.DataFrame(territorial_metrics)),
            "territorial_diagnostics.csv": serialize_table(pd.DataFrame(territories)),
            "calibration_diagnostics.csv": serialize_table(pd.DataFrame(calibration)),
            "run_summary.json": json_bytes(summary),
        }
    )
    manifest = dict(
        schema="stage4-candidate-v2",
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
