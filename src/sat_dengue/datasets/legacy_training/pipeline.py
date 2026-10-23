"""Shared Stage 4 pipeline for simple references over verified Stage 3 artifacts."""

from __future__ import annotations

import hashlib
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.model_training.workflow import _build_window_outputs as _build_window_outputs
from sat_dengue.model_training.workflow import _enforce_window_rules as _enforce_window_rules
from sat_dengue.model_training.workflow import _window_base as _window_base

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

NOTEBOOK_PATH = Path("notebooks/05_baseline_models.ipynb")


@dataclass(frozen=True)
class ModelTrainingResult:
    """Immutable Stage 4 execution output.

    Args:
        bundle: Published or verified artifact directory.
        manifest: Run manifest with reproducible identity and file hashes.
    """

    bundle: Path
    manifest: dict[str, Any]


def _runtime_versions() -> dict[str, str]:
    """Return runtime versions relevant to deterministic execution."""
    return {
        "python": platform.python_version(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
    }


def code_fingerprints(root: Path) -> dict[str, Any]:
    """Fingerprint all Stage 4 load-bearing code and notebook sources."""
    paths = sorted((root / "scripts/model_training").glob("*.py"))
    paths += [root / "pyproject.toml", root / NOTEBOOK_PATH]
    records = {str(path.relative_to(root)): fingerprint(path) for path in paths}
    notebook = read_json(root / NOTEBOOK_PATH)
    code_only = {
        "nbformat": notebook.get("nbformat"),
        "cells": [
            {"cell_type": cell["cell_type"], "source": "".join(cell["source"])}
            for cell in notebook["cells"]
        ],
    }
    records[str(NOTEBOOK_PATH)] = {
        **bytes_record(json_bytes(code_only)),
        "kind": "notebook_code_only",
    }
    return records


def _identity_payload(
    config: ModelTrainingConfig,
    contract: dict[str, Any],
    temporal_bundle: Path,
    temporal_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic identity payload for artifact publication."""
    return {
        "stage4_contract": fingerprint(config.resolve(config.contract_path)),
        "stage3_temporal_manifest": fingerprint(temporal_bundle / "manifest.json"),
        "stage3_temporal_bundle_id": temporal_manifest["bundle_id"],
        "configuration": {
            "windows": contract["windows"],
            "references": contract["references"],
            "metrics": contract["metrics"],
            "seed": contract["seed"],
        },
        "code": code_fingerprints(config.root),
        "runtime": _runtime_versions(),
    }


def build_model_training(
    config: ModelTrainingConfig,
    *,
    verify_only: bool = False,
) -> ModelTrainingResult:
    """Build or verify Stage 4 reference outputs on top of Stage 3 artifacts."""
    if (config.root / "src/sat_dengue").is_dir():
        from sat_dengue.datasets.training_legacy import LegacyTrainingLoader

        return LegacyTrainingLoader.legacy_result(config)
    contract = read_json(config.resolve(config.contract_path))
    source = load_temporal_source(config)
    reserved_start = contract["rules"]["reserved_final_block_start"]

    prediction_tables: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    window_summaries: list[dict[str, Any]] = []
    contexts: list[pd.DataFrame] = []

    for window_id in contract["windows"]:
        dataset = load_window_dataset(source, window_id)
        _enforce_window_rules(dataset, reserved_start=reserved_start)
        context = load_event_context(
            config, source, dataset.validation_index, target_column=dataset.target_column
        )
        predictions, metrics, summary = _build_window_outputs(
            dataset, contract["references"], context
        )
        contexts.append(context.assign(window_id=window_id, horizon=dataset.horizon))
        prediction_tables.append(predictions)
        metric_rows.extend(metrics)
        window_summaries.append(summary)

    predictions_df = pd.concat(prediction_tables, ignore_index=True).sort_values(
        ["window_id", "reference", "municipality_code", "target_period"]
    )
    metrics_df = pd.DataFrame(metric_rows).sort_values(["window_id", "reference", "metric"])

    summary = {
        "status": "PASS",
        "references_executed": ["persistence", "train_prevalence"],
        "planned_references_not_executed": contract["planned_references_not_in_scope"],
        "windows": window_summaries,
        "deterministic_forecasts": ["persistence"],
        "probabilistic_forecasts": ["train_prevalence"],
        "threshold_policy": {
            name: details.get("threshold_policy")
            for name, details in contract["references"].items()
        },
        "metrics_non_evaluable": int((~metrics_df["evaluable"]).sum()) if len(metrics_df) else 0,
    }

    payloads = {
        "predictions.csv": serialize_table(predictions_df.reset_index(drop=True)),
        "evaluation_context.csv": serialize_table(pd.concat(contexts, ignore_index=True)),
        "metrics.csv": serialize_table(metrics_df.reset_index(drop=True)),
        "run_summary.json": json_bytes(summary),
    }

    identity = _identity_payload(config, contract, source.bundle, source.manifest)
    bundle_id = hashlib.sha256(json_bytes(identity)).hexdigest()
    manifest = {
        "schema": "stage4-model-training-artifacts-v1",
        "bundle_id": bundle_id,
        "identity": identity,
        "stage3_temporal_bundle": str(source.bundle.relative_to(config.root)),
        "predictions_rows": len(predictions_df),
        "metrics_rows": len(metrics_df),
        "window_count": len(window_summaries),
        "references_executed": ["persistence", "train_prevalence"],
        "evaluation_context": {
            "file": "evaluation_context.csv",
            "role": "retrospective evaluation only; excluded from X, fitting and selection",
            "keys": ["window_id", "municipality_code", "target_period"],
            "source": source.manifest["development_bundle"],
            "state_definition": "approved zona_canal_t at S and exact calendar S-1",
        },
        "determinism_limits": contract["determinism_limits"],
        "files": {name: bytes_record(payload) for name, payload in payloads.items()},
    }
    payloads["manifest.json"] = json_bytes(manifest)

    if code_fingerprints(config.root) != identity["code"]:
        raise ModelTrainingError("Code changed while building Stage 4 artifacts")

    base = config.resolve(contract["artifacts"]["base_dir"])
    if verify_only:
        bundle = base / bundle_id
        verify_artifacts(bundle, payloads)
    else:
        bundle = publish_artifacts(
            base,
            bundle_id,
            payloads,
            existing_policy=contract["artifacts"]["existing_policy"],
        )
    return ModelTrainingResult(bundle=bundle, manifest=manifest)


def run_summary(result: ModelTrainingResult, root: Path) -> dict[str, Any]:
    """Return bounded run metadata for notebook rendering and receipts."""
    return {
        "status": "PASS",
        "model_training_bundle": str(result.bundle.relative_to(root)),
        "stage3_temporal_bundle": result.manifest["stage3_temporal_bundle"],
        "bundle_id": result.manifest["bundle_id"],
        "window_count": result.manifest["window_count"],
        "predictions_rows": result.manifest["predictions_rows"],
        "metrics_rows": result.manifest["metrics_rows"],
        "references_executed": result.manifest["references_executed"],
        "determinism_limits": result.manifest["determinism_limits"],
    }
