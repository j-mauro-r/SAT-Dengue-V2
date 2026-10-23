"""Three-family comparison and two controlled XGBoost ablations, without champion selection."""

from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.metrics import evaluate_metrics
from sat_dengue.model_training.workflow import equal_window_means

from .candidates import build_candidates
from .contract import ModelTrainingConfig, ModelTrainingError, read_json
from .events import load_event_context
from .loading import load_temporal_source, load_window_dataset
from .persistence import (
    bytes_record,
    json_bytes,
    publish_artifacts,
    serialize_table,
    verify_artifacts,
)
from .pipeline import ModelTrainingResult, build_model_training


def build_candidate_suite(
    config: ModelTrainingConfig, *, verify_only: bool = False
) -> ModelTrainingResult:
    """Build or verify all frozen experiments, sharing verified source/reference loading.

    Args:
        config: Repository-scoped current configuration.
        verify_only: Verify native inference and identities without any fitting.

    Returns:
        Local immutable comparison bundle referencing component bundles, not dataset copies.
    """
    if (config.root / "src/sat_dengue").is_dir():
        from sat_dengue.datasets.training_legacy import LegacyTrainingLoader

        return LegacyTrainingLoader.legacy_result(config, suite=True)
    contract = read_json(config.resolve(config.contract_path))
    planned_fits = len(contract["windows"]) * (
        sum(
            2 * len(contract[f"{family}_candidate"]["configurations"]) + 1
            for family in ("xgboost", "lightgbm", "gam")
        )
        + len(contract["ablations"])
    )
    if planned_fits > contract["candidate_suite"]["maximum_fits_per_run"]:
        raise ModelTrainingError("Suite fit budget exceeded before execution")
    references = build_model_training(config, verify_only=verify_only)
    source = load_temporal_source(config)
    results = {}
    for family in ("xgboost", "lightgbm", "gam"):
        results[family] = build_candidates(
            config, verify_only=verify_only, family=family, references=references, source=source
        )
    for ablation in contract["ablations"]:
        results[f"xgboost_{ablation}"] = build_candidates(
            config,
            verify_only=verify_only,
            family="xgboost",
            ablation=ablation,
            full_model=results["xgboost"],
            references=references,
            source=source,
        )
    identity = {
        "bundles": {
            name: {
                "path": str(r.bundle.relative_to(config.root)),
                "manifest": fingerprint(r.bundle / "manifest.json"),
            }
            for name, r in results.items()
        },
        "references": {
            "path": str(references.bundle.relative_to(config.root)),
            "manifest": fingerprint(references.bundle / "manifest.json"),
        },
    }
    bid = hashlib.sha256(json_bytes(identity)).hexdigest()
    bundle = config.resolve("artifacts/model_training/candidate_suite") / bid
    if bundle.exists() or verify_only:
        manifest = read_json(bundle / "manifest.json")
        if manifest["identity"] != identity:
            raise ModelTrainingError("Stale suite identity")
        payloads = {}
        for name, record in manifest["files"].items():
            path = (bundle / name).resolve()
            if not path.is_relative_to(bundle.resolve()) or fingerprint(path) != record:
                raise ModelTrainingError("Invalid suite payload")
            payloads[name] = path.read_bytes()
        payloads["manifest.json"] = (bundle / "manifest.json").read_bytes()
        verify_artifacts(bundle, payloads)
        return ModelTrainingResult(bundle, manifest)
    comparison = pd.concat(
        [pd.read_csv(r.bundle / "metrics.csv") for r in [references, *results.values()]],
        ignore_index=True,
    )
    means = equal_window_means(comparison, contract["windows"]).drop(columns="evaluable")
    # Join on all cohort keys before attributing a score difference to feature removal.
    full = pd.read_csv(results["xgboost"].bundle / "predictions.csv")
    deltas = []
    for name, result in results.items():
        pred = pd.read_csv(result.bundle / "predictions.csv")
        keys = ["window_id", "municipality_code", "origin_period", "target_period", "feature_row"]
        if not pred[keys].equals(full[keys]):
            raise ModelTrainingError("Candidate/ablation cohorts differ")
        if not name.startswith("xgboost_"):
            continue
        baseline = comparison[comparison.reference.eq("xgboost")]
        reduced = comparison[comparison.reference.eq(name)]
        joined = reduced.merge(
            baseline,
            on=["window_id", "horizon", "metric"],
            suffixes=("", "_full"),
            validate="one_to_one",
        )
        for row in joined.to_dict(orient="records"):
            deltas.append(
                dict(
                    experiment=name,
                    window_id=row["window_id"],
                    horizon=row["horizon"],
                    metric=row["metric"],
                    value=row["value"],
                    full_value=row["value_full"],
                    delta_reduced_minus_full=row["value"] - row["value_full"],
                )
            )
    territory = [pd.read_csv(r.bundle / "territorial_metrics.csv") for r in results.values()]
    ref_predictions = pd.read_csv(
        references.bundle / "predictions.csv", dtype={"municipality_code": "string"}
    )
    reference_territory: list[dict[str, Any]] = []
    for window in contract["windows"]:
        dataset = load_window_dataset(source, window)
        context = load_event_context(
            config, source, dataset.validation_index, target_column=dataset.target_column
        )
        for reference in contract["references"]:
            frame = ref_predictions[
                (ref_predictions.window_id == window) & (ref_predictions.reference == reference)
            ].reset_index(drop=True)
            for municipality, idx in dataset.validation_index.groupby(
                "municipality_code"
            ).groups.items():
                scored = evaluate_metrics(
                    reference,
                    dataset.validation_y.loc[idx, dataset.y_column].reset_index(drop=True),
                    frame.loc[idx].reset_index(drop=True),
                    dataset.validation_index.loc[idx].reset_index(drop=True),
                    target_column=dataset.target_column,
                    threshold_policy_declared=contract["references"][reference]["threshold_policy"]
                    is not None,
                    event_context=context.loc[idx].reset_index(drop=True),
                )
                reference_territory.extend(
                    dict(
                        r, window_id=window, horizon=dataset.horizon, municipality_code=municipality
                    )
                    for r in scored
                )
    territory.append(pd.DataFrame(reference_territory))
    runs = {name: read_json(r.bundle / "run_summary.json") for name, r in results.items()}
    fits = sum(r["fit_count"] for r in runs.values())
    if fits > contract["candidate_suite"]["maximum_fits_per_run"]:
        raise ModelTrainingError("Suite fit budget exceeded")
    summary = dict(
        status="PASS",
        windows=contract["windows"],
        fit_count=fits,
        elapsed_seconds=sum(r["elapsed_seconds"] for r in runs.values()),
        experiments={
            name: {k: r[k] for k in ("fit_count", "inner_fits", "outer_fits", "elapsed_seconds")}
            for name, r in runs.items()
        },
        threshold_policy=None,
        champion=None,
        gates_approved=False,
        limitations=(
            "Retrospective consolidated data; descriptive comparisons; no causal ablation claims."
        ),
    )
    payloads = {
        "comparison.csv": serialize_table(comparison),
        "horizon_means.csv": serialize_table(means),
        "ablation_deltas.csv": serialize_table(pd.DataFrame(deltas)),
        "territorial_metrics.csv": serialize_table(pd.concat(territory, ignore_index=True)),
        "run_summary.json": json_bytes(summary),
    }
    manifest = dict(
        schema="stage4-candidate-suite-v1",
        bundle_id=bid,
        identity=identity,
        windows=contract["windows"],
        files={n: bytes_record(b) for n, b in payloads.items()},
    )
    payloads["manifest.json"] = json_bytes(manifest)
    publish_artifacts(bundle.parent, bid, payloads)
    verify_artifacts(bundle, payloads)
    return ModelTrainingResult(bundle, manifest)
