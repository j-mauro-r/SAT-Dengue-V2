"""Read-only M00 reconstruction diagnosis and common-cohort exposure accounting."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03 import load_protocol
from sat_dengue.experiments.exp04_contract import (
    BASELINE,
    BASELINE_MANIFEST_SHA256,
    BASELINE_SHA256,
)
from sat_dengue.tracking.experiments import unique_object

KEYS = ["municipality_code", "target_month"]
MISSING = [
    "original_M00_fitted_predictor_and_preparer_with_output_identity",
    "original_M00_fitted_calibrator_coefficients_with_output_identity",
    "original_M00_raw_calibration_selection_and_evaluation_scores",
    "per_score_training_cutoff_label_maturity_and_role_membership",
    "verified_prior_OOF_history_for_rolling_windows",
    "original_runtime_native_library_and_numerical_environment_identity",
]


def audit_baseline(directory: Path = BASELINE) -> dict[str, Any]:
    """Inspect the pinned result, never infer raw scores or open private sources.

    The historical bundle schema has no fitted-state/raw-score artifacts. Even
    an intact result therefore cannot establish original fitted-state equivalence.
    No retraining or inversion is attempted. A future recovery needs its own
    verified evidence; a caller cannot promote readiness with a boolean flag.
    """
    root = Path.cwd().resolve() / "tmp"
    if not directory.resolve().is_relative_to(root) or any(
        p.is_symlink() for p in (directory, *directory.parents)
    ):
        raise ValueError("EXP04 baseline input must be a repository-local tmp directory")
    result: dict[str, Any] = {
        "status": "BLOCKED_BASELINE",
        "source_experiment": "EXP03.1",
        "source_variant": "M00",
        "original_identity": None,
        "reconstruction_identity": None,
        "equivalence": "NOT_VERIFIABLE_FROM_AVAILABLE_ARTIFACTS",
        "missing_dependencies": list(MISSING),
        "private_source_reads": 0,
        "model_fits": 0,
        "mlflow_writes": 0,
    }
    paths = [directory / "bundle.json", directory / "manifest.json"]
    if not all(p.is_file() and not p.is_symlink() for p in paths):
        result["reason"] = "original_bundle_or_manifest_unavailable"
        return result
    raw, manifest_raw = (p.read_bytes() for p in paths)
    if (
        hashlib.sha256(raw).hexdigest() != BASELINE_SHA256
        or hashlib.sha256(manifest_raw).hexdigest() != BASELINE_MANIFEST_SHA256
    ):
        raise ValueError("EXP04 requires the exact original EXP03.1 M00 bundle and manifest")
    bundle = json.loads(raw, object_pairs_hook=unique_object)
    manifest = json.loads(manifest_raw, object_pairs_hook=unique_object)
    reference = load_protocol()["design"]
    cells = [c for c in bundle["cells"] if c["variant"] == "M00"]
    if len(cells) != 36 or any(c["predictors"] != reference["variants"]["V09"] for c in cells):
        raise ValueError("M00 cells or exact ordered V09 predictors differ")
    result.update(
        original_identity={
            "bundle_id": manifest["bundle_id"],
            "bundle_sha256": BASELINE_SHA256,
            "manifest_sha256": BASELINE_MANIFEST_SHA256,
            "git_revision": bundle["provenance"]["git_revision"],
        },
        reason="configuration_and_seed_are_not_original_fitted_state_evidence",
        source_reuse_decision=bundle["reuse_decision"]["decision"],
        ordered_predictors=reference["variants"]["V09"],
        family_parameters=reference["families"],
        seed=reference["seed"],
        reference_temporal_roles=reference["windows"],
        retained_fields=sorted(bundle["predictions"][0]),
        M00_cells=len(cells),
        fitted_calibrator_state=None,
        raw_score_artifacts=None,
        private_reads_discrepancy={
            "execution_counters": bundle["execution_counters"]["real_private_reads"],
            "provenance": bundle["provenance"]["real_private_reads"],
            "resolution": "UNRESOLVED",
        },
    )
    return result


def validate_scores(frame: pd.DataFrame) -> None:
    """Require one already-eligible, observable probability row per monthly key."""
    required = {*KEYS, "raw_score", "truth", "error_class"}
    if not required <= set(frame) or frame.empty or frame[list(required)].isna().any().any():
        raise ValueError("EXP04 requires complete eligible probability rows")
    if frame.duplicated(KEYS).any():
        raise ValueError("EXP04 duplicate municipality-target month key")
    months = frame.target_month.astype(str)
    dates = pd.to_datetime(months + "-01", errors="coerce")
    if dates.isna().any() or not months.str.fullmatch(r"\d{4}-\d{2}").all():
        raise ValueError("Invalid target month")
    if dates.dt.year.gt(2024).any():
        raise ValueError("EXP04 rejects 2025 and later targets")
    scores = frame.raw_score.to_numpy(dtype=float)
    if not np.isfinite(scores).all() or not frame.raw_score.between(0, 1).all():
        raise ValueError("Finite probability scores required")
    if not frame.truth.isin([0, 1]).all():
        raise ValueError("Binary truth required")
    if not frame.error_class.isin(["onset", "continuation", "no_excess"]).all():
        raise ValueError("Unknown error class; do not shrink support silently")
    for name in ("family", "horizon", "objective", "cut"):
        if name in frame and (frame[name].isna().any() or frame[name].nunique() != 1):
            raise ValueError("EXP04 scores must describe one family/horizon/objective/cut")


def common_exposure(frame: pd.DataFrame) -> float:
    """The caller supplies the complete common eligible/observable cohort."""
    validate_scores(frame)
    return len(frame) / 12.0


def paired_support(left: pd.DataFrame, right: pd.DataFrame) -> dict[str, Any]:
    """Never silently change cohorts or count different exposure as a policy effect."""
    validate_scores(left)
    validate_scores(right)
    a = left.sort_values(KEYS).reset_index(drop=True)
    b = right.sort_values(KEYS).reset_index(drop=True)
    if not a[KEYS].equals(b[KEYS]):
        return {
            "status": "NOT_EVALUABLE",
            "reason": "eligible_cohort_or_exposure_differs",
            "left_rows": len(a),
            "right_rows": len(b),
            "intersection_rows": len(a[KEYS].merge(b[KEYS], on=KEYS)),
        }
    if not a[["truth", "error_class"]].equals(b[["truth", "error_class"]]):
        return {"status": "NOT_EVALUABLE", "reason": "paired_labels_or_error_class_differ"}
    for name in ("family", "horizon", "objective", "cut"):
        if name in a or name in b:
            if name not in a or name not in b or not a[name].equals(b[name]):
                return {"status": "NOT_EVALUABLE", "reason": "paired_dimensions_differ"}
    if not a.raw_score.equals(b.raw_score):
        return {"status": "NOT_EVALUABLE", "reason": "base_predictor_scores_differ"}
    return {"status": "evaluable", "rows": len(a), "common_exposure": common_exposure(a)}
