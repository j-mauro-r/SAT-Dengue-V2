"""Stage 5 temporal calibration/threshold pipeline over verified Stage 4 evidence."""

from __future__ import annotations

import hashlib
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.model_evaluation.calibration import (
    ROLE_CALENDAR_TO_SPLIT as ROLE_CALENDAR_TO_SPLIT,
)
from sat_dengue.model_evaluation.calibration import (
    ROLE_SEQUENCE as ROLE_SEQUENCE,
)
from sat_dengue.model_evaluation.calibration import (
    _apply_saved_calibrator as _apply_saved_calibrator,
)
from sat_dengue.model_evaluation.calibration import _apply_sigmoid as _apply_sigmoid
from sat_dengue.model_evaluation.calibration import (
    _assert_selection_independence as _assert_selection_independence,
)
from sat_dengue.model_evaluation.calibration import _assert_verify_allowed as _assert_verify_allowed
from sat_dengue.model_evaluation.calibration import _assign_internal_role as _assign_internal_role
from sat_dengue.model_evaluation.calibration import (
    _build_temporal_audit_row as _build_temporal_audit_row,
)
from sat_dengue.model_evaluation.calibration import _build_threshold_grid as _build_threshold_grid
from sat_dengue.model_evaluation.calibration import (
    _calibration_curve_table as _calibration_curve_table,
)
from sat_dengue.model_evaluation.calibration import _calibrator_provenance as _calibrator_provenance
from sat_dengue.model_evaluation.calibration import _choose_calibration as _choose_calibration
from sat_dengue.model_evaluation.calibration import _extract_fold_months as _extract_fold_months
from sat_dengue.model_evaluation.calibration import _fit_sigmoid as _fit_sigmoid
from sat_dengue.model_evaluation.calibration import (
    _merge_internal_with_truth as _merge_internal_with_truth,
)
from sat_dengue.model_evaluation.calibration import _month_gap as _month_gap
from sat_dengue.model_evaluation.calibration import _month_lag_series as _month_lag_series
from sat_dengue.model_evaluation.calibration import _month_ordinal as _month_ordinal
from sat_dengue.model_evaluation.calibration import _oracle_event_counts as _oracle_event_counts
from sat_dengue.model_evaluation.calibration import _read_window_calendar as _read_window_calendar
from sat_dengue.model_evaluation.calibration import _role_boundaries as _role_boundaries
from sat_dengue.model_evaluation.calibration import (
    _select_configuration_from_hyperparameter_role,
)
from sat_dengue.model_evaluation.calibration import (
    _select_threshold_from_grid as _select_threshold_from_grid,
)
from sat_dengue.model_evaluation.calibration import _threshold_limits as _threshold_limits
from sat_dengue.model_evaluation.calibration import _to_bool as _to_bool
from sat_dengue.model_evaluation.calibration import (
    _validate_role_calendar_against_dataset as _validate_role_calendar_against_dataset,
)
from sat_dengue.model_evaluation.calibration import (
    _window_index_with_labels as _window_index_with_labels,
)
from scripts.model_training.candidate_families import fit_model, restore_model
from scripts.model_training.candidate_suite import build_candidate_suite
from scripts.model_training.contract import read_json as read_stage4_json
from scripts.model_training.events import load_event_context
from scripts.model_training.loading import (
    TemporalSource,
    load_temporal_source,
    load_window_dataset,
    parse_window_id,
)
from scripts.model_training.metrics import (
    brier_metric,
    evaluate_metrics,
)
from scripts.model_training.persistence import (
    bytes_record,
    json_bytes,
    publish_artifacts,
    serialize_table,
)
from scripts.model_training.pipeline import ModelTrainingResult
from scripts.model_training.pipeline import code_fingerprints as stage4_code_fingerprints
from scripts.model_training.references import persistence_reference
from scripts.training_preparation.pipeline import fingerprint

from .availability import preflight_window, transition_records
from .contract import ModelEvaluationConfig, ModelEvaluationError, Stage5Contract, load_contract
from .internal_evidence import internal_evidence

NOTEBOOK_PATH = Path("notebooks/07_probability_calibration_thresholds.ipynb")


@dataclass(frozen=True)
class ModelEvaluationResult:
    """Immutable Stage 5 execution output."""

    bundle: Path
    manifest: dict[str, Any]


@dataclass(frozen=True)
class Stage4Inputs:
    """Verified Stage 4 inputs consumed by Stage 5."""

    suite: ModelTrainingResult
    source: TemporalSource
    stage4_contract: dict[str, Any]
    reference_bundle: Path
    candidate_bundles: dict[str, Path]


def _runtime_versions() -> dict[str, str]:
    """Return runtime versions bound to Stage 5 artifacts."""
    return {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "scikit-learn": __import__("sklearn").__version__,
    }


def code_fingerprints(root: Path) -> dict[str, Any]:
    """Fingerprint all Stage 5 load-bearing code and notebook07 sources."""
    paths = sorted((root / "scripts/model_evaluation").glob("*.py"))
    paths += [root / "pyproject.toml", root / NOTEBOOK_PATH]
    records = {str(path.relative_to(root)): fingerprint(path) for path in paths}
    notebook = read_stage4_json(root / NOTEBOOK_PATH)
    code_only = {
        "cells": [
            {"cell_type": cell["cell_type"], "source": "".join(cell["source"])}
            for cell in notebook["cells"]
        ]
    }
    records[str(NOTEBOOK_PATH)] = {
        **bytes_record(json_bytes(code_only)),
        "kind": "notebook_code_only",
    }
    return records


def _bundle_identity(payload: dict[str, Any]) -> str:
    """Return deterministic SHA-256 identity for a payload."""
    return hashlib.sha256(json_bytes(payload)).hexdigest()


def _load_stage4_inputs(config: ModelEvaluationConfig, contract: Stage5Contract) -> Stage4Inputs:
    """Load and verify Stage 4 candidate suite, source and component manifests."""
    stage4_config = config.stage4_config()
    stage4_contract = read_stage4_json(stage4_config.resolve(stage4_config.contract_path))
    suite = build_candidate_suite(stage4_config, verify_only=True)
    source = load_temporal_source(stage4_config)
    suite_manifest = suite.manifest
    identity = suite_manifest["identity"]

    reference_path = config.resolve(identity["references"]["path"])
    if fingerprint(reference_path / "manifest.json") != identity["references"]["manifest"]:
        raise ModelEvaluationError("Stage4 reference bundle manifest fingerprint mismatch")

    bundles: dict[str, Path] = {}
    for family in contract.raw["candidate_families"]:
        metadata = identity["bundles"].get(family)
        if not isinstance(metadata, dict):
            raise ModelEvaluationError(f"Missing Stage4 candidate family in suite: {family}")
        path = config.resolve(metadata["path"])
        if fingerprint(path / "manifest.json") != metadata["manifest"]:
            raise ModelEvaluationError(f"Stage4 bundle fingerprint mismatch: {family}")
        bundles[family] = path

    return Stage4Inputs(
        suite=suite,
        source=source,
        stage4_contract=stage4_contract,
        reference_bundle=reference_path,
        candidate_bundles=bundles,
    )


def _load_internal_predictions(
    candidate_bundle: Path,
    window: str,
    target_column: str,
) -> pd.DataFrame:
    """Load internal out-of-time predictions for one candidate/window."""
    return pd.read_csv(
        candidate_bundle / f"{window}_inner_predictions.csv",
        dtype={
            "municipality_code": "string",
            "year_month": "string",
            target_column: "string",
            "feature_row": "Int64",
            "configuration_id": "string",
            "fold": "Int64",
        },
    )


def _verify_manifest_payloads(bundle: Path, manifest: dict[str, Any]) -> None:
    """Require exact file set and payload hashes for an existing Stage 5 bundle."""
    expected_files = set(manifest["files"].keys()) | {"manifest.json"}
    observed_files = {path.name for path in bundle.iterdir() if path.is_file()}
    if expected_files != observed_files:
        raise ModelEvaluationError("Existing Stage5 bundle has missing or unexpected files")
    for name, record in manifest["files"].items():
        payload = (bundle / name).read_bytes()
        if bytes_record(payload) != record:
            raise ModelEvaluationError(f"Existing Stage5 bundle is stale or corrupted: {name}")


def _identity_payload(
    *,
    config: ModelEvaluationConfig,
    contract: Stage5Contract,
    stage4: Stage4Inputs,
) -> dict[str, Any]:
    """Build deterministic Stage 5 identity payload."""
    contract_path = config.resolve(config.contract_path)
    bundle_manifests = {
        family: fingerprint(path / "manifest.json")
        for family, path in stage4.candidate_bundles.items()
    }
    return {
        "stage5_contract": fingerprint(contract_path),
        "stage4_candidate_suite_manifest": fingerprint(stage4.suite.bundle / "manifest.json"),
        "stage4_reference_manifest": fingerprint(stage4.reference_bundle / "manifest.json"),
        "stage4_candidate_manifests": bundle_manifests,
        "configuration": {
            "candidate_families": contract.raw["candidate_families"],
            "reserved_final_block_start": contract.raw["reserved_final_block_start"],
            "knobs": contract.raw["knobs"],
            "window_role_calendar": contract.raw["window_role_calendar"],
            "role_reuse_policy": contract.raw["role_reuse_policy"],
            "calibration_policy": contract.raw["calibration_policy"],
            "threshold_policy": contract.raw["threshold_policy"],
        },
        "code": code_fingerprints(config.root),
        "stage4_code": stage4_code_fingerprints(config.root),
        "runtime": _runtime_versions(),
    }


def _verify_existing_bundle(
    *,
    config: ModelEvaluationConfig,
    contract: Stage5Contract,
    stage4: Stage4Inputs,
    windows: list[str],
    reserved_start: str,
    identity: dict[str, Any],
    bundle: Path,
) -> dict[str, Any]:
    """Verify an existing Stage 5 bundle by replaying inference without fitting."""
    if not bundle.is_dir() or bundle.is_symlink():
        raise ModelEvaluationError(f"Expected existing Stage5 bundle directory: {bundle}")

    manifest = read_stage4_json(bundle / "manifest.json")
    if manifest.get("bundle_id") != bundle.name:
        raise ModelEvaluationError("Stage5 bundle_id does not match directory name")
    if manifest.get("identity") != identity:
        raise ModelEvaluationError("Stale Stage5 identity for current contract/code/runtime")
    _verify_manifest_payloads(bundle, manifest)

    threshold_selection = pd.read_csv(
        bundle / "threshold_selection.csv",
        dtype={
            "candidate": "string",
            "window_id": "string",
            "selected_configuration_id": "string",
            "calibration_choice": "string",
            "status": "string",
        },
    )
    posterior_saved = pd.read_csv(
        bundle / "posterior_predictions.csv",
        dtype={
            "candidate": "string",
            "window_id": "string",
            "municipality_code": "string",
            "origin_period": "string",
            "target_period": "string",
            "feature_row": "Int64",
            "selected_configuration_id": "string",
            "calibration_choice": "string",
            "model_artifact": "string",
            "preparer_artifact": "string",
        },
    )
    temporal_audit_saved = pd.read_csv(
        bundle / "temporal_audit.csv",
        dtype={
            "candidate": "string",
            "window_id": "string",
            "horizon": "Int64",
            "selected_configuration_id": "string",
        },
    )
    calibrator_payload = read_stage4_json(bundle / "calibrators.json")
    calibrators = calibrator_payload.get("calibrators")
    if not isinstance(calibrators, list):
        raise ModelEvaluationError("Invalid Stage5 calibrators.json structure")

    calibrator_lookup: dict[tuple[str, str, int], dict[str, Any]] = {}
    for entry in calibrators:
        if not isinstance(entry, dict):
            raise ModelEvaluationError("Invalid calibrator entry in Stage5 bundle")
        key = (str(entry["candidate"]), str(entry["window_id"]), int(entry["horizon"]))
        if key in calibrator_lookup:
            raise ModelEvaluationError(f"Duplicated calibrator entry for {key}")
        calibrator_lookup[key] = entry

    for candidate in contract.raw["candidate_families"]:
        for window in windows:
            cutoff, horizon = parse_window_id(window)
            target_column = f"target_period_t{horizon}"
            dataset = load_window_dataset(stage4.source, window)
            calendar = _read_window_calendar(contract, window)
            _validate_role_calendar_against_dataset(
                window,
                dataset,
                horizon,
                calendar,
                reserved_start=reserved_start,
            )

            search, merged, selected_id, _selected_parameters, _selection_table = internal_evidence(
                dataset=dataset,
                calendar=calendar,
                support=contract.raw["support_requirements"],
                candidate=candidate,
                settings=stage4.stage4_contract[f"{candidate}_candidate"],
                policy=stage4.stage4_contract["selection_policy"],
                selector=_select_configuration_from_hyperparameter_role,
                bundle=bundle,
            )

            selected_internal = merged[merged["configuration_id"] == selected_id].copy()
            selected_internal.rename(
                columns={"prediction_probability": "probability_raw"},
                inplace=True,
            )
            hp_folds, development_folds = _assert_selection_independence(selected_internal)

            external_origin_start = str(dataset.validation_index["year_month"].min())
            temporal_audit_row = _build_temporal_audit_row(
                candidate=candidate,
                window=window,
                horizon=horizon,
                cutoff=cutoff,
                selected_configuration_id=selected_id,
                selected_internal=selected_internal,
                target_column=target_column,
                calendar=calendar,
                reserved_start=reserved_start,
                external_origin_start=external_origin_start,
                hp_folds=hp_folds,
                development_folds=development_folds,
                components=search["components"],
            )
            temporal_audit_row["independence_pass"] = True

            saved_audit = temporal_audit_saved[
                temporal_audit_saved["candidate"].eq(candidate)
                & temporal_audit_saved["window_id"].eq(window)
                & temporal_audit_saved["horizon"].eq(horizon)
            ]
            if saved_audit.shape[0] != 1:
                raise ModelEvaluationError(
                    f"Missing temporal_audit row for {candidate} {window} horizon {horizon}"
                )
            saved_audit_row = saved_audit.iloc[0].to_dict()
            for flag in (
                "chronology_pass",
                "target_origin_lag_pass",
                "chronology_by_target_pass",
                "chronology_by_origin_pass",
                "hyperparameter_to_calibration_fit_pass",
                "calibration_fit_to_calibration_selection_pass",
                "calibration_selection_to_threshold_pass",
                "threshold_to_external_origin_pass",
                "component_available_pass",
                "independence_pass",
                "no_reserved_pass",
            ):
                if flag in saved_audit_row and _to_bool(saved_audit_row[flag]) != bool(
                    temporal_audit_row[flag]
                ):
                    raise ModelEvaluationError(
                        f"temporal_audit mismatch for {candidate} {window} {flag}"
                    )

            observed_transitions = transition_records(
                selected_internal,
                target_column,
                dataset.validation_index.year_month,
                search["components"],
            )
            saved_transitions = pd.read_csv(bundle / "availability_transitions.csv")
            saved_transitions = saved_transitions[
                saved_transitions.candidate.eq(candidate) & saved_transitions.window_id.eq(window)
            ]
            expected_transitions = pd.DataFrame(
                [
                    dict(candidate=candidate, window_id=window, horizon=horizon, **row)
                    for row in observed_transitions
                ]
            )
            if (
                not saved_transitions.reset_index(drop=True)
                .astype(str)
                .equals(expected_transitions[saved_transitions.columns].astype(str))
            ):
                raise ModelEvaluationError("Saved availability dates/dependencies differ from rows")

            threshold_row = threshold_selection[
                threshold_selection["candidate"].eq(candidate)
                & threshold_selection["window_id"].eq(window)
                & threshold_selection["horizon"].eq(horizon)
            ]
            if threshold_row.shape[0] != 1:
                raise ModelEvaluationError(
                    f"Missing threshold_selection row for {candidate} {window} horizon {horizon}"
                )
            threshold_record = threshold_row.iloc[0].to_dict()
            if str(threshold_record["selected_configuration_id"]) != selected_id:
                raise ModelEvaluationError(
                    f"Selected configuration mismatch in saved threshold_selection for "
                    f"{candidate} {window}: expected={selected_id} "
                    f"saved={threshold_record['selected_configuration_id']}"
                )

            calibrator_key = (candidate, window, horizon)
            if calibrator_key not in calibrator_lookup:
                raise ModelEvaluationError(
                    f"Missing calibrator for {candidate} {window} horizon {horizon}"
                )
            calibrator_record = calibrator_lookup[calibrator_key]
            if calibrator_record["fit_provenance"] != _calibrator_provenance(
                selected_internal, horizon
            ):
                raise ModelEvaluationError("Calibrator labeled-input provenance differs")
            if str(calibrator_record["selected_configuration_id"]) != selected_id:
                raise ModelEvaluationError(
                    f"Calibrator selected configuration mismatch for {candidate} {window}"
                )
            if str(calibrator_record["calibration_choice"]) != str(
                threshold_record["calibration_choice"]
            ):
                raise ModelEvaluationError(
                    f"Calibrator/threshold calibration choice mismatch for {candidate} {window}"
                )

            model_artifact = f"{candidate}_{window}_outer_model.json"
            preparer_artifact = f"{candidate}_{window}_outer_preparer.json"
            outer_model = restore_model(
                candidate,
                (bundle / model_artifact).read_bytes(),
                read_stage4_json(bundle / preparer_artifact),
            )

            training_record = dict(
                target_max=str(dataset.train_index[target_column].max()),
                keys=bytes_record(serialize_table(dataset.train_index)),
                X=bytes_record(serialize_table(dataset.train_X)),
                y=bytes_record(serialize_table(dataset.train_y)),
                selected_parameters=_selected_parameters,
            )
            if (
                read_stage4_json(bundle / f"{candidate}_{window}_outer_training.json")
                != training_record
            ):
                raise ModelEvaluationError("Outer training provenance differs")
            if outer_model.preparer["fit_X_fingerprint"] != training_record["X"]:
                raise ModelEvaluationError("Outer preparer training provenance differs")

            posterior_index = dataset.validation_index[
                ["municipality_code", "year_month", target_column, "feature_row"]
            ].reset_index(drop=True)
            posterior = posterior_saved[
                posterior_saved["candidate"].eq(candidate)
                & posterior_saved["window_id"].eq(window)
                & posterior_saved["horizon"].eq(horizon)
            ].copy()
            if posterior.empty:
                raise ModelEvaluationError(
                    f"Missing posterior predictions for {candidate} {window} horizon {horizon}"
                )
            posterior = posterior.sort_values(
                ["municipality_code", "origin_period", "target_period", "feature_row"]
            ).reset_index(drop=True)

            expected_keys = (
                pd.DataFrame(
                    {
                        "municipality_code": posterior_index["municipality_code"].astype("string"),
                        "origin_period": posterior_index["year_month"].astype("string"),
                        "target_period": posterior_index[target_column].astype("string"),
                        "feature_row": posterior_index["feature_row"].astype("Int64"),
                    }
                )
                .sort_values(["municipality_code", "origin_period", "target_period", "feature_row"])
                .reset_index(drop=True)
            )
            observed_keys = posterior[
                ["municipality_code", "origin_period", "target_period", "feature_row"]
            ].copy()
            observed_keys["municipality_code"] = observed_keys["municipality_code"].astype("string")
            observed_keys["origin_period"] = observed_keys["origin_period"].astype("string")
            observed_keys["target_period"] = observed_keys["target_period"].astype("string")
            observed_keys["feature_row"] = observed_keys["feature_row"].astype("Int64")
            if not observed_keys.equals(expected_keys):
                raise ModelEvaluationError(
                    f"Posterior key alignment mismatch for {candidate} {window} horizon {horizon}"
                )

            if set(posterior["model_artifact"].astype("string")) != {model_artifact}:
                raise ModelEvaluationError(
                    f"Posterior model artifact mismatch for {candidate} {window}"
                )
            if set(posterior["preparer_artifact"].astype("string")) != {preparer_artifact}:
                raise ModelEvaluationError(
                    f"Posterior preparer artifact mismatch for {candidate} {window}"
                )

            probability_raw = (
                outer_model.predict(dataset.validation_X).astype("Float64").reset_index(drop=True)
            )
            probability_sigmoid = _apply_saved_calibrator(probability_raw, calibrator_record)
            calibration_choice = str(threshold_record["calibration_choice"])
            probability_selected = (
                probability_sigmoid if calibration_choice == "sigmoid" else probability_raw
            ).astype("Float64")

            threshold_value = threshold_record.get("selected_threshold")
            threshold = None if pd.isna(threshold_value) else float(threshold_value)
            prediction_label = (
                probability_selected.ge(threshold).astype("Int64")
                if threshold is not None
                else pd.Series([pd.NA] * len(probability_selected), dtype="Int64")
            )

            saved_raw = posterior["probability_raw"].astype(float).to_numpy()
            if not np.allclose(
                probability_raw.to_numpy(dtype=float),
                saved_raw,
                rtol=0,
                atol=1e-12,
            ):
                raise ModelEvaluationError(
                    "Posterior raw probabilities mismatch for "
                    f"{candidate} {window} horizon {horizon}"
                )
            saved_sigmoid = posterior["probability_sigmoid"].astype(float).to_numpy()
            if not np.allclose(
                probability_sigmoid.to_numpy(dtype=float),
                saved_sigmoid,
                rtol=0,
                atol=1e-12,
            ):
                raise ModelEvaluationError(
                    "Posterior sigmoid probabilities mismatch for "
                    f"{candidate} {window} horizon {horizon}"
                )
            saved_selected = posterior["probability_selected"].astype(float).to_numpy()
            if not np.allclose(
                probability_selected.to_numpy(dtype=float),
                saved_selected,
                rtol=0,
                atol=1e-12,
            ):
                raise ModelEvaluationError(
                    "Posterior selected probabilities mismatch for "
                    f"{candidate} {window} horizon {horizon}"
                )

            saved_labels = posterior["prediction_label"].astype("Int64").reset_index(drop=True)
            if not prediction_label.reset_index(drop=True).equals(saved_labels):
                raise ModelEvaluationError(
                    f"Posterior labels mismatch for {candidate} {window} horizon {horizon}"
                )

    return manifest


def build_model_evaluation(
    config: ModelEvaluationConfig,
    *,
    verify_only: bool = False,
) -> ModelEvaluationResult:
    """Build or verify corrected Stage 5 calibration and threshold artifacts."""
    from sat_dengue.datasets.legacy_training.contract import resolve_root

    if config.root.resolve() == resolve_root():
        from sat_dengue.datasets.evaluation_legacy import STAGE5, checked_evaluation_bundle

        from .contract import CONTRACT_PATH

        if config.contract_path != CONTRACT_PATH:
            raise ModelEvaluationError("Unapproved legacy evaluation configuration")
        manifest = checked_evaluation_bundle(STAGE5)
        return ModelEvaluationResult(config.root / STAGE5, manifest)
    contract = load_contract(config)
    stage4 = _load_stage4_inputs(config, contract)
    windows = stage4.suite.manifest["windows"]
    calendar_windows = sorted(contract.raw["window_role_calendar"].keys())
    if set(calendar_windows) != set(windows):
        raise ModelEvaluationError("window_role_calendar must match Stage4 windows exactly")

    reserved_start = contract.raw["reserved_final_block_start"]
    policy = contract.raw["calibration_policy"]
    threshold_policy = contract.raw["threshold_policy"]
    precision = int(threshold_policy["probability_precision"])
    identity = _identity_payload(config=config, contract=contract, stage4=stage4)
    bundle_id = _bundle_identity(identity)
    base = config.resolve(contract.raw["artifacts"]["base_dir"])
    bundle = base / bundle_id
    existing_policy = contract.raw["artifacts"]["existing_policy"]

    if verify_only:
        manifest = _verify_existing_bundle(
            config=config,
            contract=contract,
            stage4=stage4,
            windows=windows,
            reserved_start=reserved_start,
            identity=identity,
            bundle=bundle,
        )
        return ModelEvaluationResult(bundle=bundle, manifest=manifest)

    if bundle.exists():
        if existing_policy == "error":
            raise ModelEvaluationError("Output already exists; replacement is forbidden")
        manifest = _verify_existing_bundle(
            config=config,
            contract=contract,
            stage4=stage4,
            windows=windows,
            reserved_start=reserved_start,
            identity=identity,
            bundle=bundle,
        )
        return ModelEvaluationResult(bundle=bundle, manifest=manifest)

    planned_models = len(windows) * sum(
        len(stage4.stage4_contract[f"{family}_candidate"]["configurations"]) + 2
        for family in contract.raw["candidate_families"]
    )
    planned_sigmoid = len(windows) * len(contract.raw["candidate_families"])
    budget = contract.raw["execution_budget"]
    if (
        planned_models > budget["max_total_model_fits"]
        or planned_models - 2 * planned_sigmoid > budget["max_hyperparameter_model_fits"]
        or planned_sigmoid > budget["max_internal_model_refits"]
        or planned_sigmoid > budget["max_outer_model_refits"]
        or planned_sigmoid > budget["max_sigmoid_fits"]
        or planned_models + planned_sigmoid > budget["max_total_fits"]
    ):
        raise ModelEvaluationError("Stage5 fit budget exceeded before training")
    preflight = {
        window: preflight_window(
            load_window_dataset(stage4.source, window),
            _read_window_calendar(contract, window),
            contract.raw["support_requirements"],
        )
        for window in windows
    }
    availability_rows: list[dict[str, Any]] = []
    development_rows: list[pd.DataFrame] = []
    posterior_rows: list[pd.DataFrame] = []
    calibration_rows: list[dict[str, Any]] = []
    calibration_curves: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    threshold_grid_rows: list[dict[str, Any]] = []
    temporal_audit_rows: list[dict[str, Any]] = []
    independent_rows: list[dict[str, Any]] = []
    posterior_metric_rows: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    calibrators: list[dict[str, Any]] = []
    model_artifacts: dict[str, bytes] = {}

    for candidate in contract.raw["candidate_families"]:
        settings = stage4.stage4_contract[f"{candidate}_candidate"]

        for window in windows:
            cutoff, horizon = parse_window_id(window)
            target_column = f"target_period_t{horizon}"
            y_column = f"y_t{horizon}"
            dataset = load_window_dataset(stage4.source, window)
            calendar = _read_window_calendar(contract, window)
            _validate_role_calendar_against_dataset(
                window,
                dataset,
                horizon,
                calendar,
                reserved_start=reserved_start,
            )

            search, merged, selected_id, selected_parameters, selection_table = internal_evidence(
                dataset=dataset,
                calendar=calendar,
                support=contract.raw["support_requirements"],
                candidate=candidate,
                settings=settings,
                policy=stage4.stage4_contract["selection_policy"],
                selector=_select_configuration_from_hyperparameter_role,
                payloads=model_artifacts,
            )

            selection_table["window_id"] = window
            selection_table["horizon"] = horizon
            selection_rows.extend(selection_table.to_dict(orient="records"))

            selected_internal = merged[merged["configuration_id"] == selected_id].copy()
            selected_internal.rename(
                columns={"prediction_probability": "probability_raw"}, inplace=True
            )
            selected_internal["selected_configuration_id"] = selected_id

            hp_folds, development_folds = _assert_selection_independence(selected_internal)
            independence_pass = True

            fit_split = selected_internal[
                selected_internal["split_role"] == "calibration_fit"
            ].reset_index(drop=True)
            calibration_selection = selected_internal[
                selected_internal["split_role"] == "calibration_selection"
            ].reset_index(drop=True)
            threshold_selection = selected_internal[
                selected_internal["split_role"] == "threshold_selection"
            ].reset_index(drop=True)

            calibrator = _fit_sigmoid(
                fit_split["probability_raw"],
                fit_split[y_column],
                seed=contract.knobs.seed,
                allow_fit=not verify_only,
            )
            selected_internal["probability_sigmoid"] = _apply_sigmoid(
                selected_internal["probability_raw"], calibrator
            )
            calibration_selection["probability_sigmoid"] = _apply_sigmoid(
                calibration_selection["probability_raw"], calibrator
            )

            raw_brier = brier_metric(
                calibration_selection[y_column], calibration_selection["probability_raw"]
            )["value"]
            sigmoid_brier = brier_metric(
                calibration_selection[y_column], calibration_selection["probability_sigmoid"]
            )["value"]
            if raw_brier is None:
                raise ModelEvaluationError(
                    f"Raw calibration-selection Brier unavailable for {candidate} {window}"
                )

            raw_curve_table, raw_curve_summary = _calibration_curve_table(
                calibration_selection["probability_raw"],
                calibration_selection[y_column],
                bins=int(policy["curve_bins"]),
                min_bin_support=int(policy["min_bin_support"]),
            )
            sigmoid_curve_table, sigmoid_curve_summary = _calibration_curve_table(
                calibration_selection["probability_sigmoid"],
                calibration_selection[y_column],
                bins=int(policy["curve_bins"]),
                min_bin_support=int(policy["min_bin_support"]),
            )

            choice = _choose_calibration(
                raw_brier=float(raw_brier),
                sigmoid_brier=float(sigmoid_brier) if sigmoid_brier is not None else None,
                raw_curve=raw_curve_summary,
                sigmoid_curve=sigmoid_curve_summary if sigmoid_brier is not None else None,
                policy=policy,
            )

            calibration_rows.extend(
                [
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "alternative": "original",
                        "selection_split": "calibration_selection",
                        "brier": float(raw_brier),
                        **raw_curve_summary,
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "alternative": "sigmoid",
                        "selection_split": "calibration_selection",
                        "brier": float(sigmoid_brier) if sigmoid_brier is not None else None,
                        **sigmoid_curve_summary,
                    },
                ]
            )

            for alternative, table in (
                ("original", raw_curve_table),
                ("sigmoid", sigmoid_curve_table),
            ):
                curve = table.copy()
                curve["candidate"] = candidate
                curve["window_id"] = window
                curve["horizon"] = horizon
                curve["alternative"] = alternative
                calibration_curves.extend(curve.to_dict(orient="records"))

            chosen_alternative = str(choice["selected"])
            threshold_selection["probability_sigmoid"] = _apply_sigmoid(
                threshold_selection["probability_raw"], calibrator
            )
            selected_probability = (
                threshold_selection["probability_sigmoid"]
                if chosen_alternative == "sigmoid"
                else threshold_selection["probability_raw"]
            ).astype("Float64")

            threshold_index = threshold_selection[
                ["municipality_code", "year_month", target_column, "feature_row"]
            ].reset_index(drop=True)
            threshold_y = threshold_selection[y_column].astype("Int64").reset_index(drop=True)
            threshold_context = load_event_context(
                config.stage4_config(),
                stage4.source,
                threshold_index,
                target_column=target_column,
            ).reset_index(drop=True)

            persistence_frame = persistence_reference(
                pd.DataFrame({"zona_canal_t": threshold_selection["zona_canal_t"]}),
                horizon=horizon,
            ).reset_index(drop=True)
            persistence_metrics = {
                row["metric"]: row
                for row in evaluate_metrics(
                    "persistence",
                    threshold_y,
                    persistence_frame,
                    threshold_index,
                    target_column=target_column,
                    threshold_policy_declared=True,
                    event_context=threshold_context,
                )
            }
            persistence_onset = persistence_metrics["onset_sensitivity"]["value"]
            persistence_far = persistence_metrics["false_alarm_ratio"]["value"]
            min_onset, max_far = _threshold_limits(persistence_onset, persistence_far, contract)

            threshold_grid = _build_threshold_grid(
                candidate=candidate,
                horizon=horizon,
                probability=selected_probability,
                y_true=threshold_y,
                index=threshold_index,
                event_context=threshold_context,
                precision=precision,
            )
            threshold_grid["candidate"] = candidate
            threshold_grid["window_id"] = window
            threshold_grid["horizon"] = horizon
            threshold_grid["calibration_choice"] = chosen_alternative
            threshold_grid["max_allowed_false_alarm_ratio"] = max_far
            threshold_grid["min_required_onset_sensitivity"] = min_onset
            threshold_grid["is_feasible"] = (
                threshold_grid["onset_sensitivity_evaluable"]
                & threshold_grid["false_alarm_ratio_evaluable"]
                & (threshold_grid["false_alarm_ratio"] <= max_far if max_far is not None else False)
            )
            threshold_grid_rows.extend(threshold_grid.to_dict(orient="records"))

            selected_threshold = _select_threshold_from_grid(
                threshold_grid,
                min_required_onset=min_onset,
                max_allowed_false_alarm=max_far,
                allow_selection=not verify_only,
            )
            threshold_rows.append(
                {
                    "candidate": candidate,
                    "window_id": window,
                    "horizon": horizon,
                    "selected_configuration_id": selected_id,
                    "calibration_choice": chosen_alternative,
                    "calibration_reason": choice["reason"],
                    "persistence_onset_sensitivity": persistence_onset,
                    "persistence_false_alarm_ratio": persistence_far,
                    "max_allowed_false_alarm_ratio": max_far,
                    "min_required_onset_sensitivity": min_onset,
                    **selected_threshold,
                }
            )

            if selected_threshold["selected_threshold"] is not None:
                labels = selected_probability.ge(selected_threshold["selected_threshold"]).astype(
                    "Int64"
                )
                oracle = _oracle_event_counts(threshold_y, labels, threshold_context)
                chosen_row = threshold_grid[
                    threshold_grid["threshold"] == selected_threshold["selected_threshold"]
                ].iloc[0]
                independent_rows.append(
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "threshold_selection_counts",
                        "pass": bool(
                            oracle["false_alerts"] == int(chosen_row["false_alerts"])
                            and oracle["emitted_alerts"] == int(chosen_row["emitted_alerts"])
                            and oracle["detected_onsets"] == int(chosen_row["detected_onsets"])
                            and oracle["real_onsets"] == int(chosen_row["real_onsets"])
                        ),
                        "oracle_false_alerts": oracle["false_alerts"],
                        "metric_false_alerts": int(chosen_row["false_alerts"]),
                        "oracle_emitted_alerts": oracle["emitted_alerts"],
                        "metric_emitted_alerts": int(chosen_row["emitted_alerts"]),
                        "oracle_detected_onsets": oracle["detected_onsets"],
                        "metric_detected_onsets": int(chosen_row["detected_onsets"]),
                        "oracle_real_onsets": oracle["real_onsets"],
                        "metric_real_onsets": int(chosen_row["real_onsets"]),
                    }
                )

            development_rows.append(
                selected_internal[
                    [
                        "window_id",
                        "cutoff",
                        "horizon",
                        "split_role",
                        "configuration_id",
                        "fold",
                        "municipality_code",
                        "year_month",
                        target_column,
                        "feature_row",
                        y_column,
                        "probability_raw",
                        "probability_sigmoid",
                        "model_artifact",
                        "preparer_artifact",
                        "model_available_month",
                        "configuration_available_month",
                    ]
                ]
                .rename(columns={target_column: "target_period", y_column: "y_true"})
                .assign(
                    candidate=candidate,
                    selected_configuration_id=selected_id,
                    selected_configuration=selected_parameters,
                    calibration_choice=chosen_alternative,
                    selected_threshold=selected_threshold["selected_threshold"],
                )
            )

            _assert_verify_allowed(verify_only=verify_only, operation="outer_model_fit")
            outer_model = fit_model(
                candidate,
                dataset.train_X,
                dataset.train_y[y_column],
                selected_parameters,
                seed=int(settings["seed"]),
                threads=int(settings["threads"]),
            )
            model_file = f"{candidate}_{window}_outer_model.json"
            preparer_file = f"{candidate}_{window}_outer_preparer.json"
            model_artifacts[model_file] = outer_model.model_bytes()
            model_artifacts[preparer_file] = json_bytes(outer_model.preparer)
            model_artifacts[f"{candidate}_{window}_outer_training.json"] = json_bytes(
                dict(
                    target_max=str(dataset.train_index[target_column].max()),
                    keys=bytes_record(serialize_table(dataset.train_index)),
                    X=bytes_record(serialize_table(dataset.train_X)),
                    y=bytes_record(serialize_table(dataset.train_y)),
                    selected_parameters=selected_parameters,
                )
            )

            posterior_probability_raw = outer_model.predict(dataset.validation_X).astype("Float64")
            posterior_probability_sigmoid = _apply_sigmoid(posterior_probability_raw, calibrator)
            posterior_probability_selected = (
                posterior_probability_sigmoid
                if chosen_alternative == "sigmoid"
                else posterior_probability_raw
            ).astype("Float64")
            threshold = selected_threshold["selected_threshold"]
            prediction_label = (
                posterior_probability_selected.ge(threshold).astype("Int64")
                if threshold is not None
                else pd.Series([pd.NA] * len(posterior_probability_selected), dtype="Int64")
            )

            posterior_index = dataset.validation_index[
                ["municipality_code", "year_month", target_column, "feature_row"]
            ].reset_index(drop=True)
            posterior_y = dataset.validation_y[y_column].astype("Int64").reset_index(drop=True)
            posterior_context = load_event_context(
                config.stage4_config(),
                stage4.source,
                posterior_index,
                target_column=target_column,
            ).reset_index(drop=True)

            candidate_frame = pd.DataFrame(
                {
                    "prediction_kind": "probabilistic",
                    "prediction_score": posterior_probability_selected,
                    "prediction_probability": posterior_probability_selected,
                    "prediction_label": prediction_label,
                }
            )
            candidate_metrics = evaluate_metrics(
                candidate,
                posterior_y,
                candidate_frame,
                posterior_index,
                target_column=target_column,
                threshold_policy_declared=threshold is not None,
                event_context=posterior_context,
            )
            for row in candidate_metrics:
                posterior_metric_rows.append(
                    {
                        **row,
                        "candidate": candidate,
                        "window_id": window,
                        "cutoff": cutoff,
                        "horizon": horizon,
                        "selected_configuration_id": selected_id,
                        "calibration_choice": chosen_alternative,
                        "threshold": threshold,
                        "selection_status": selected_threshold["status"],
                        "split_role": "posterior_evaluation",
                    }
                )

            persistence_eval = persistence_reference(dataset.validation_X, horizon=horizon)
            persistence_metric_rows = evaluate_metrics(
                "persistence",
                posterior_y,
                persistence_eval.reset_index(drop=True),
                posterior_index,
                target_column=target_column,
                threshold_policy_declared=True,
                event_context=posterior_context,
            )
            for row in persistence_metric_rows:
                posterior_metric_rows.append(
                    {
                        **row,
                        "candidate": "persistence",
                        "window_id": window,
                        "cutoff": cutoff,
                        "horizon": horizon,
                        "selected_configuration_id": "deterministic",
                        "calibration_choice": "none",
                        "threshold": "deterministic",
                        "selection_status": "reference",
                        "split_role": "posterior_evaluation",
                    }
                )

            posterior_rows.append(
                pd.DataFrame(
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "cutoff": cutoff,
                        "horizon": horizon,
                        "municipality_code": posterior_index["municipality_code"],
                        "origin_period": posterior_index["year_month"],
                        "target_period": posterior_index[target_column],
                        "feature_row": posterior_index["feature_row"],
                        "selected_configuration_id": selected_id,
                        "probability_raw": posterior_probability_raw,
                        "probability_sigmoid": posterior_probability_sigmoid,
                        "probability_selected": posterior_probability_selected,
                        "selected_threshold": threshold,
                        "prediction_label": prediction_label,
                        "calibration_choice": chosen_alternative,
                        "selection_status": selected_threshold["status"],
                        "model_artifact": model_file,
                        "preparer_artifact": preparer_file,
                    }
                )
            )

            external_origin_start = str(dataset.validation_index["year_month"].min())
            temporal_audit_row = _build_temporal_audit_row(
                candidate=candidate,
                window=window,
                horizon=horizon,
                cutoff=cutoff,
                selected_configuration_id=selected_id,
                selected_internal=selected_internal,
                target_column=target_column,
                calendar=calendar,
                reserved_start=reserved_start,
                external_origin_start=external_origin_start,
                hp_folds=hp_folds,
                development_folds=development_folds,
                components=search["components"],
            )
            temporal_audit_row["independence_pass"] = independence_pass
            temporal_audit_rows.append(temporal_audit_row)
            availability_rows.extend(
                dict(r, candidate=candidate, window_id=window, horizon=horizon)
                for r in transition_records(
                    selected_internal,
                    target_column,
                    dataset.validation_index.year_month,
                    search["components"],
                )
            )

            independent_rows.extend(
                [
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "selection_independence",
                        "pass": independence_pass,
                        "selected_configuration_id": selected_id,
                        "hyperparameter_selection_folds": sorted(hp_folds),
                        "development_folds": sorted(development_folds),
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "component_availability_vs_external_origin",
                        "pass": bool(temporal_audit_row["component_available_pass"]),
                        "component_available_by_origin": temporal_audit_row[
                            "component_available_by_origin"
                        ],
                        "external_origin_start": external_origin_start,
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "target_origin_lag_matches_horizon",
                        "pass": bool(temporal_audit_row["target_origin_lag_pass"]),
                        "observed_target_origin_lag_months": temporal_audit_row[
                            "observed_target_origin_lag_months"
                        ],
                        "expected_target_origin_lag_months": horizon,
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "internal_origin_transition_hp_to_calibration_fit",
                        "pass": bool(temporal_audit_row["hyperparameter_to_calibration_fit_pass"]),
                        "component_available_by_origin": temporal_audit_row[
                            "hyperparameter_to_calibration_fit_component_available_by_origin"
                        ],
                        "consumer_origin_start": temporal_audit_row[
                            "hyperparameter_to_calibration_fit_consumer_origin_start"
                        ],
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "internal_origin_transition_calibration_fit_to_selection",
                        "pass": bool(
                            temporal_audit_row["calibration_fit_to_calibration_selection_pass"]
                        ),
                        "component_available_by_origin": temporal_audit_row[
                            "calibration_fit_to_calibration_selection_component_available_by_origin"
                        ],
                        "consumer_origin_start": temporal_audit_row[
                            "calibration_fit_to_calibration_selection_consumer_origin_start"
                        ],
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "internal_origin_transition_calibration_selection_to_threshold",
                        "pass": bool(temporal_audit_row["calibration_selection_to_threshold_pass"]),
                        "component_available_by_origin": temporal_audit_row[
                            "calibration_selection_to_threshold_component_available_by_origin"
                        ],
                        "consumer_origin_start": temporal_audit_row[
                            "calibration_selection_to_threshold_consumer_origin_start"
                        ],
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "internal_origin_transition_threshold_to_external",
                        "pass": bool(temporal_audit_row["threshold_to_external_origin_pass"]),
                        "component_available_by_origin": temporal_audit_row[
                            "threshold_component_available_by_origin"
                        ],
                        "consumer_origin_start": external_origin_start,
                    },
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "no_reserved_block_access",
                        "pass": bool(temporal_audit_row["no_reserved_pass"]),
                        "reserved_start": reserved_start,
                    },
                ]
            )

            if threshold is not None:
                oracle = _oracle_event_counts(posterior_y, prediction_label, posterior_context)
                independent_rows.append(
                    {
                        "candidate": candidate,
                        "window_id": window,
                        "horizon": horizon,
                        "check": "posterior_counts_recomputed",
                        "pass": True,
                        "false_alerts": oracle["false_alerts"],
                        "emitted_alerts": oracle["emitted_alerts"],
                        "detected_onsets": oracle["detected_onsets"],
                        "real_onsets": oracle["real_onsets"],
                        "false_alarm_ratio": oracle["false_alarm_ratio"],
                        "onset_sensitivity": oracle["onset_sensitivity"],
                    }
                )

            calibrators.append(
                {
                    "candidate": candidate,
                    "window_id": window,
                    "horizon": horizon,
                    "selected_configuration_id": selected_id,
                    "fit_provenance": _calibrator_provenance(selected_internal, horizon),
                    "available": calibrator is not None,
                    "method": "sigmoid",
                    "coefficient": float(calibrator.coef_[0][0])
                    if calibrator is not None
                    else None,
                    "intercept": float(calibrator.intercept_[0])
                    if calibrator is not None
                    else None,
                    "calibration_choice": chosen_alternative,
                    "reason": choice["reason"],
                }
            )

    temporal_audit_df = pd.DataFrame(temporal_audit_rows)
    audit_flags = [
        "chronology_pass",
        "target_origin_lag_pass",
        "chronology_by_target_pass",
        "chronology_by_origin_pass",
        "hyperparameter_to_calibration_fit_pass",
        "calibration_fit_to_calibration_selection_pass",
        "calibration_selection_to_threshold_pass",
        "threshold_to_external_origin_pass",
        "independence_pass",
        "component_available_pass",
        "no_reserved_pass",
    ]
    if not temporal_audit_df[audit_flags].all(axis=None):
        raise ModelEvaluationError("Temporal audit detected chronology or independence violations")

    independent_df = pd.DataFrame(independent_rows)
    if not independent_df["pass"].fillna(False).all():
        failed = independent_df[~independent_df["pass"].fillna(False)]
        raise ModelEvaluationError(
            f"Independent checks failed for {len(failed)} candidate/window/horizon checks"
        )

    development_df = pd.concat(development_rows, ignore_index=True)
    posterior_df = pd.concat(posterior_rows, ignore_index=True)
    calibration_df = pd.DataFrame(calibration_rows)
    threshold_df = pd.DataFrame(threshold_rows)
    threshold_grid_df = pd.DataFrame(threshold_grid_rows)
    posterior_metrics_df = pd.DataFrame(posterior_metric_rows)
    selection_df = pd.DataFrame(selection_rows)

    summary = {
        "status": "PASS",
        "candidate_families": contract.raw["candidate_families"],
        "horizons": [1, 2],
        "calibration_method": "sigmoid",
        "selection_scope": "per_window",
        "calibration_selected": {
            f"{row['candidate']}_{row['window_id']}": row["calibration_choice"]
            for row in threshold_rows
        },
        "threshold_status": {
            f"{row['candidate']}_{row['window_id']}": row["status"] for row in threshold_rows
        },
        "threshold_meets_gain": {
            f"{row['candidate']}_{row['window_id']}": row["meets_min_onset_gain"]
            for row in threshold_rows
        },
        "stage4_suite_bundle": str(stage4.suite.bundle.relative_to(config.root)),
        "stage4_reference_bundle": str(stage4.reference_bundle.relative_to(config.root)),
        "fit_counts": dict(
            hyperparameter_models=planned_models - 2 * planned_sigmoid,
            internal_models=planned_sigmoid,
            outer_models=planned_sigmoid,
            sigmoid=sum(bool(c["available"]) for c in calibrators),
            total=planned_models + sum(bool(c["available"]) for c in calibrators),
        ),
        "development_rows": int(development_df.shape[0]),
        "posterior_rows": int(posterior_df.shape[0]),
        "independent_checks": int(independent_df.shape[0]),
        "knobs": contract.raw["knobs"],
        "determinism_limits": contract.raw["determinism_limits"],
        "supersedes": contract.raw.get("supersedes", {}),
    }

    payloads: dict[str, bytes] = {
        "calendar_preflight.json": json_bytes(preflight),
        "availability_transitions.csv": serialize_table(pd.DataFrame(availability_rows)),
        "development_predictions.csv": serialize_table(development_df),
        "hyperparameter_selection.csv": serialize_table(selection_df),
        "calibration_selection.csv": serialize_table(calibration_df),
        "calibration_curves.csv": serialize_table(pd.DataFrame(calibration_curves)),
        "calibrators.json": json_bytes({"calibrators": calibrators}),
        "threshold_grid.csv": serialize_table(threshold_grid_df),
        "threshold_selection.csv": serialize_table(threshold_df),
        "temporal_audit.csv": serialize_table(temporal_audit_df),
        "posterior_predictions.csv": serialize_table(posterior_df),
        "posterior_metrics.csv": serialize_table(posterior_metrics_df),
        "independent_checks.csv": serialize_table(independent_df),
        "run_summary.json": json_bytes(summary),
    }
    payloads.update(model_artifacts)

    identity = _identity_payload(config=config, contract=contract, stage4=stage4)
    bundle_id = _bundle_identity(identity)
    manifest = {
        "schema": "stage5-calibration-threshold-artifacts-v3",
        "bundle_id": bundle_id,
        "identity": identity,
        "stage4_candidate_suite_bundle": str(stage4.suite.bundle.relative_to(config.root)),
        "stage4_reference_bundle": str(stage4.reference_bundle.relative_to(config.root)),
        "files": {name: bytes_record(data) for name, data in payloads.items()},
        "rules": {
            "false_alarm_constraint": (
                "false_alarm_ratio_candidate <= false_alarm_ratio_persistence + "
                "max_false_alarm_increase_pp/100"
            ),
            "onset_constraint": (
                "onset_sensitivity_candidate >= onset_sensitivity_persistence + "
                "min_onset_sensitivity_gain_pp/100"
            ),
            "no_reserved_targets": f"target_period < {reserved_start}",
            "selection_boundary": (
                "Configuration selection uses hyperparameter-selection role targets only; "
                "calibration/threshold roles use new frozen early-selected internal models; "
                "labeled producer targets and dependencies precede consumer origins."
            ),
            "external_boundary": (
                "Each external window is evaluated with its own selected configuration, calibrator "
                "choice and threshold determined from that window's prior internal role calendars."
            ),
        },
    }
    payloads["manifest.json"] = json_bytes(manifest)

    if code_fingerprints(config.root) != identity["code"]:
        raise ModelEvaluationError("Stage5 code changed while building artifacts")

    bundle = publish_artifacts(
        base,
        bundle_id,
        payloads,
        existing_policy=existing_policy,
    )

    return ModelEvaluationResult(bundle=bundle, manifest=manifest)


def run_summary(result: ModelEvaluationResult, root: Path) -> dict[str, Any]:
    """Return bounded run metadata for notebook rendering and receipts."""
    summary = read_stage4_json(result.bundle / "run_summary.json")
    return {
        "status": "PASS",
        "model_evaluation_bundle": str(result.bundle.relative_to(root)),
        "bundle_id": result.manifest["bundle_id"],
        "stage4_candidate_suite_bundle": result.manifest["stage4_candidate_suite_bundle"],
        "candidate_families": summary["candidate_families"],
        "calibration_selected": summary["calibration_selected"],
        "threshold_status": summary["threshold_status"],
        "threshold_meets_gain": summary["threshold_meets_gain"],
        "fit_counts": summary["fit_counts"],
        "development_rows": summary["development_rows"],
        "posterior_rows": summary["posterior_rows"],
        "knobs": summary["knobs"],
        "determinism_limits": summary["determinism_limits"],
        "supersedes": summary["supersedes"],
    }
