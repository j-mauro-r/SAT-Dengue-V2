"""Read-only validator for a complete EXP03.1 real bundle and MLflow lineage."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from sat_dengue.experiments.exp03_1_reporting import (
    read_real_bundle,
    validate_real_mlflow,
)


def score_structure(scores: Any) -> dict[str, Any]:
    """Exact per-row dense ranks/tie groups and the ten frozen reliability bins."""
    import numpy as np

    values = np.asarray(scores, dtype=float)
    if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
        raise ValueError("Nonfinite or out-of-range replay probability")
    _, ranks = np.unique(values, return_inverse=True)
    bins = np.minimum(np.searchsorted(np.linspace(0, 1, 11), values, side="right") - 1, 9)
    return {"rank_and_tie_group": ranks.tolist(), "reliability_bin": bins.tolist()}


def compare_observables(original: dict[str, Any] | None, replay: dict[str, Any]) -> dict[str, Any]:
    """Compare retained science only; absent historical states never become equivalent."""
    absent = {
        name: "NOT_COMPARABLE"
        for name in (
            "predictor",
            "preparer",
            "calibrator",
            "raw_scores",
            "calibration_scores",
            "selection_scores",
            "selection_tie_groups",
            "threshold_selection_details",
            "training_and_role_membership",
            "score_temporal_provenance",
            "observed_environment",
        )
    }
    report: dict[str, Any] = {
        "status": "NOT_COMPARABLE",
        "atol": 1e-12,
        "rtol": 0,
        "historical_intermediates": absent,
        "differences": [],
        "scientific_reference_replacement": False,
    }
    fields = ("protocol_sha256", "matrix_sha256", "cells", "predictions", "thresholds", "contrasts")
    if original is None or any(name not in original or name not in replay for name in fields):
        report["reason"] = "missing_observable_evidence"
        return report
    if any(
        name not in original.get("provenance", {}) or name not in replay.get("provenance", {})
        for name in ("data_version", "data_sha256", "source_admission")
    ):
        report["reason"] = "missing_source_identity_evidence"
        return report
    numeric_difference = False
    differences: list[str] = []

    def compare(a: Any, b: Any, path: str, *, numeric: bool = False) -> None:
        nonlocal numeric_difference
        if type(a) is type(b) and a == b:
            return
        if (
            numeric
            and type(a) in (int, float)
            and type(b) in (int, float)
            and math.isfinite(a)
            and math.isfinite(b)
            and abs(a - b) <= 1e-12
        ):
            numeric_difference = True
            return
        if len(differences) < 30:
            differences.append(path)

    metric_floats = {
        "average_precision",
        "brier",
        "sensitivity",
        "precision",
        "far",
        "fpr",
        "false_alerts_per_monitored_municipality_year",
        "ece",
        "coverage",
        "observed",
        "predicted",
    }

    def metrics(a: Any, b: Any, path: str) -> None:
        if isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
            for name in a:
                if name in metric_floats:
                    compare(a[name], b[name], path + "/" + name, numeric=True)
                else:
                    metrics(a[name], b[name], path + "/" + name)
        elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for i, (left, right) in enumerate(zip(a, b, strict=True)):
                metrics(left, right, path + "/" + str(i))
        else:
            compare(a, b, path)

    for name in ("protocol_sha256", "matrix_sha256", "thresholds"):
        compare(original[name], replay[name], name)
    for name in ("data_version", "data_sha256"):
        compare(
            original.get("provenance", {}).get(name), replay.get("provenance", {}).get(name), name
        )
    compare(
        original.get("provenance", {}).get("source_admission", {}).get("files"),
        replay.get("provenance", {}).get("source_admission", {}).get("files"),
        "source_files",
    )
    # Preserve cell and prediction order as well as uniqueness and membership.
    for name in ("cells", "predictions"):
        left, right = original[name], replay[name]
        compare(len(left), len(right), name + "/count")
        if len(left) != len(right):
            continue
        for i, (a, b) in enumerate(zip(left, right, strict=True)):
            path = name + "/" + str(i)
            compare(set(a), set(b), path + "/fields")
            for field in a.keys() & b.keys():
                if field == "metrics":
                    metrics(a[field], b[field], path + "/metrics")
                else:
                    compare(
                        a[field],
                        b[field],
                        path + "/" + field,
                        numeric=field in metric_floats or field == "score",
                    )
    by_cell: dict[str, list[Any]] = {}
    replay_by_cell: dict[str, list[Any]] = {}
    for target, source in ((by_cell, original), (replay_by_cell, replay)):
        for row in source["predictions"]:
            target.setdefault(row["cell_id"], []).append(row)
    compare(set(by_cell), set(replay_by_cell), "prediction_cell_ids")
    for cell_id in by_cell.keys() & replay_by_cell.keys():
        left, right = by_cell[cell_id], replay_by_cell[cell_id]
        compare(
            score_structure([row["score"] for row in left]),
            score_structure([row["score"] for row in right]),
            cell_id + "/ranking_bins_ties",
        )
        for truth, alert, label in (
            (1, True, "TP"),
            (0, True, "FP"),
            (1, False, "FN"),
            (0, False, "TN"),
        ):
            compare(
                sum(row["truth"] == truth and row["alert"] == alert for row in left),
                sum(row["truth"] == truth and row["alert"] == alert for row in right),
                cell_id + "/" + label,
            )
    left, right = original["contrasts"], replay["contrasts"]
    compare(left.get("definitions"), right.get("definitions"), "contrast_definitions")
    effects_a, effects_b = left.get("paired_effects", []), right.get("paired_effects", [])
    compare(len(effects_a), len(effects_b), "paired_effect_count")
    for i, (a, b) in enumerate(zip(effects_a, effects_b, strict=False)):
        compare(set(a), set(b), f"contrast/{i}/fields")
        for field in a.keys() & b.keys():
            compare(a[field], b[field], f"contrast/{i}/{field}", numeric=field == "score_delta")
    report.update(
        status=(
            "REPLAY_MISMATCH"
            if differences
            else "NUMERICALLY_COMPATIBLE_REPLAY"
            if numeric_difference
            else "EXACT_OBSERVABLE_REPLAY"
        ),
        differences=differences,
        comparable_cells=len(original["cells"]),
        comparable_predictions=len(original["predictions"]),
    )
    return report


def read_original(path: Path) -> dict[str, Any]:
    """Read only during a separately authorized replay or explicit bundle comparison."""
    from sat_dengue.experiments.exp03_1_preflight import ORIGINAL

    publication = read_real_bundle(path, ORIGINAL["bundle_id"])
    bundle = publication["bundle"]
    if (
        hashlib.sha256((path / "bundle.json").read_bytes()).hexdigest() != ORIGINAL["bundle_sha256"]
        or bundle["mlflow_receipt"]["parent_run_id"] != ORIGINAL["parent_run_id"]
        or len(bundle["cells"]) != ORIGINAL["cells"]
        or len(bundle["predictions"]) != ORIGINAL["predictions"]
        or sum(row["variant"] == "M00" for row in bundle["cells"]) != ORIGINAL["M00_cells"]
    ):
        raise ValueError("Original EXP03.1 evidence identity changed")
    return publication


def validate(
    path: Path, expected_bundle_id: str, tracking_root: str, original_path: Path | None = None
) -> dict[str, Any]:
    publication = read_real_bundle(path, expected_bundle_id)
    bundle = publication["bundle"]
    validate_real_mlflow(bundle, tracking_root, publication["manifest"]["bundle_id"])
    replay = publication.get("replay")
    comparison = {"status": "NOT_COMPARABLE", "reason": "historical_bundle_has_no_replay_artifacts"}
    correction: dict[str, str] = {}
    if replay is not None:
        original_path = original_path or Path(bundle["provenance"]["original_bundle_path"])
        original = read_original(original_path)
        comparison = compare_observables(original["bundle"], bundle)
        stored = replay["comparison"]
        if comparison != stored:
            differences = stored.get("differences")
            # Package schema, protocol and hashes were verified by read_real_bundle.
            # Only a threshold-type mismatch with exact persisted science is repairable.
            if (
                stored.get("status") != "REPLAY_MISMATCH"
                or not isinstance(differences, list)
                or not differences
                or any(
                    not isinstance(path, str)
                    or re.fullmatch(r"cells/[0-9]+/threshold", path) is None
                    for path in differences
                )
                or comparison.get("status") != "EXACT_OBSERVABLE_REPLAY"
                or comparison.get("differences") != []
                or comparison != {**stored, "status": "EXACT_OBSERVABLE_REPLAY", "differences": []}
            ):
                raise ValueError("Replay comparison evidence changed")
            correction = {
                "stored_comparison_status": stored["status"],
                "comparison_correction": "canonical_numeric_type_normalization_v1",
            }
    elif original_path is not None:
        raise ValueError("Original/replay validation requires a replay companion package")
    return {
        "status": "verified" if comparison["status"] != "REPLAY_MISMATCH" else "REPLAY_MISMATCH",
        "bundle_id": publication["manifest"]["bundle_id"],
        "protocol_sha256": bundle["protocol_sha256"],
        "cells": len(bundle["cells"]),
        "parent_run_id": bundle["mlflow_receipt"]["parent_run_id"],
        "child_runs": bundle["mlflow_receipt"]["child_count"],
        "replay": comparison,
        **correction,
        "G5": bundle["G5"],
        "champion": bundle["champion"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--tracking-root", required=True)
    parser.add_argument("--original-bundle", type=Path)
    args = parser.parse_args()
    result = validate(args.bundle, args.bundle_id, args.tracking_root, args.original_bundle)
    print(json.dumps(result, sort_keys=True))
    if result["status"] == "REPLAY_MISMATCH":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
