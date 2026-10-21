"""Immutable development assessment; reserved execution remains fail-closed."""

from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

from scripts.model_training.persistence import (
    bytes_record,
    json_bytes,
    publish_artifacts,
    serialize_table,
    verify_artifacts,
)
from scripts.training_preparation.pipeline import fingerprint

from .comparison import summarize
from .loading import load_comparison
from .proposal import freeze_proposal

NOTEBOOK = Path("notebooks/08_model_evaluation.ipynb")
CONTRACT = Path("docs/product/stage-5/model_evaluation_contract_v1.json")


def code_fingerprints(root: Path) -> dict[str, Any]:
    """Identify assessment implementation and notebook code without saved outputs."""
    paths = sorted((root / "scripts/model_assessment").glob("*.py"))
    paths.append(root / "scripts/evaluation_metrics.py")
    records = {str(path.relative_to(root)): fingerprint(path) for path in paths}
    notebook = json.loads((root / NOTEBOOK).read_text())
    if any(c["cell_type"] != "code" for c in notebook["cells"]):
        raise ValueError("Notebook08 must contain only code cells")
    code = json_bytes({"cells": ["".join(c["source"]) for c in notebook["cells"]]})
    records[str(NOTEBOOK)] = bytes_record(code)
    return records


def build_assessment(root: Path, *, verify_only: bool = False) -> dict[str, Any]:
    """Recompute development-only assessment and publish or verify identical bytes.

    Args:
        root: Reproducibly resolved repository root.
        verify_only: Require existing identical artifacts; never repair or fit.

    Returns:
        Bounded notebook summary with the exact pending proposal identity.
    """
    contract = json.loads((root / CONTRACT).read_text())
    if contract["knobs"] != {
        "max_false_alarm_increase_pp": 5.0,
        "min_onset_sensitivity_gain_pp": 10.0,
        "seed": 42,
    }:
        raise ValueError("Approved utility knobs must remain fixed")
    bundle, overall, breakdown, predictions, input_receipt = load_comparison(root)
    summary, decisions, intervals = summarize(overall)
    identity_record = {
        "input_bundle": str(bundle.relative_to(root)),
        "input_manifest": fingerprint(bundle / "manifest.json"),
        "contract": fingerprint(root / CONTRACT),
        "code": code_fingerprints(root),
        "versions": {
            name: version(name)
            for name in ("numpy", "pandas", "scikit-learn", "xgboost", "lightgbm", "scipy")
        },
    }
    proposal = freeze_proposal(
        bundle, contract, sorted(predictions.municipality_code.unique().tolist())
    )
    proposal["identity_inputs"] = identity_record
    proposal_bytes = json_bytes(proposal)
    proposal_id = hashlib.sha256(proposal_bytes).hexdigest()
    identity = hashlib.sha256(json_bytes(identity_record)).hexdigest()
    output = root / "artifacts/model_assessment" / identity
    report = {
        "status": "development_complete_reserved_pending",
        "bundle": str(output.relative_to(root)),
        "input_bundle": str(bundle.relative_to(root)),
        "input_verification": input_receipt,
        "proposal_sha256": proposal_id,
        "new_fits": 0,
        "reserved_results_read": False,
        "G4": "OPEN",
        "G5": "NOT_APPROVED",
        "coverage": {
            "windows_per_horizon": 4,
            "municipalities": 76,
            "rows_per_candidate": {
                str(h): int(
                    predictions[
                        predictions.horizon.eq(h) & predictions.candidate.eq("persistence")
                    ].shape[0]
                )
                for h in (1, 2)
            },
        },
        "comparison": json.loads(
            summary.pivot(index=["candidate", "horizon"], columns="metric", values="value")
            .reset_index()
            .to_json(orient="records")
        ),
        "utility": json.loads(decisions.to_json(orient="records")),
        "proposed_procedures": [
            {
                "horizon": p["horizon"],
                "candidate": p["candidate"],
                "configuration": p["retained_internal_components"]["selected_id"],
                "calibration": p["retained_calibrator"]["calibration_choice"],
                "threshold": p["retained_threshold"]["selected_threshold"],
            }
            for p in proposal["procedures"]
        ],
        "final_results": "not_executed_pending_human_authorization",
    }
    payloads = {
        "input_verification.json": json_bytes(input_receipt),
        "window_metrics.csv": serialize_table(overall),
        "breakdown_metrics.csv": serialize_table(breakdown),
        "linked_development_predictions.csv": serialize_table(predictions),
        "comparison.csv": serialize_table(summary),
        "utility.csv": serialize_table(decisions),
        "descriptive_uncertainty.csv": serialize_table(intervals),
        "freeze_proposal.json": proposal_bytes,
        "run_summary.json": json_bytes(report),
    }
    manifest = {
        "schema": "model-assessment-v1",
        "bundle_id": identity,
        "identity": identity_record,
        "files": {name: bytes_record(data) for name, data in payloads.items()},
    }
    payloads["manifest.json"] = json_bytes(manifest)
    if verify_only:
        verify_artifacts(output, payloads)
    else:
        publish_artifacts(output.parent, identity, payloads)
    return report
