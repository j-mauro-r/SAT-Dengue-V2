"""Generate a deterministic, source-free EXP03.1 evidence example."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp03_1_contract import digest, protocol
from sat_dengue.experiments.exp03_1_engine import execution_plan, reuse_decision
from sat_dengue.experiments.exp03_1_evaluation import metrics, select_threshold
from sat_dengue.experiments.exp03_1_reporting import write_bundle
from sat_dengue.tracking.exp03_1 import aggregate_projection


def _identities() -> dict[str, str]:
    return {
        name: f"{index:064x}" for index, name in enumerate(protocol()["reuse_identity_fields"], 1)
    }


def synthetic_bundle() -> dict[str, Any]:
    """Build one explicitly synthetic bundle without reading sources or fitting models."""
    frame = pd.DataFrame(
        {
            "truth": [1, 0, 0, 1],
            "score": [0.9, 0.8, 0.2, 0.7],
            "municipality_code": ["synthetic-a", "synthetic-a", "synthetic-b", "synthetic-b"],
            "target_year": [2020, 2020, 2021, 2021],
            "target_month": ["2020-02", "2020-03", "2021-02", "2021-03"],
        }
    )
    threshold = select_threshold(frame.truth, frame.score, exposure=2.0)
    frame["alert"] = (
        False if threshold["threshold"] is None else frame.score >= threshold["threshold"]
    )
    decision = reuse_decision(_identities(), _identities())
    predictions = [
        {
            "cell_id": "M00-gam-t1-synthetic_development",
            "municipality_code": row.municipality_code,
            "target_month": row.target_month,
            "score": row.score,
            "alert": row.alert,
        }
        for row in frame.itertuples(index=False)
    ]
    return {
        "schema": "exp03-1-scientific-bundle-v1",
        "experiment_id": "EXP031",
        "scientific_id": "EXP03.1",
        "protocol_sha256": digest(protocol()),
        "reuse_decision": decision,
        "execution_plan": execution_plan(decision),
        "predictions": predictions,
        "thresholds": [{"cell_id": predictions[0]["cell_id"], "budget": 1.0, **threshold}],
        "metrics": [metrics(frame, exposure=2.0, bins=2)],
        "diagnostics": [
            {
                "kind": "synthetic_probe",
                "status": "synthetic_only",
                "source_reads": 0,
                "fits": 0,
            }
        ],
        "execution_counters": {
            "real_private_reads": 0,
            "real_reservations": 0,
            "real_fits": 0,
            "real_calibrations": 0,
            "real_searches": 0,
            "permanent_mlflow_writes": 0,
        },
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "synthetic": True,
    }


def generate(output: Path) -> dict[str, str]:
    root = (Path.cwd() / "tmp").resolve()
    resolved = output.resolve()
    if (
        not resolved.is_relative_to(root)
        or output.exists()
        or any(parent.is_symlink() for parent in output.parents)
    ):
        raise ValueError("Synthetic examples require a new repository-local tmp directory")
    output.mkdir(parents=True, exist_ok=False)
    bundle = synthetic_bundle()
    bundle_path = output / "bundle.json"
    bundle_sha256 = write_bundle(bundle, bundle_path)
    aggregate_path = output / "aggregate.json"
    aggregate_path.write_bytes(canonical_bytes(aggregate_projection(bundle)))
    marker_path = output / "README.md"
    marker_path.write_text(
        "# EXP03.1 source-free example\n\n"
        "Evidence type: `synthetic_generated_data`. No private source was read, no model was "
        "fit, and no permanent tracking write occurred.\n",
        encoding="utf-8",
    )
    return {
        "bundle": str(bundle_path),
        "bundle_sha256": bundle_sha256,
        "aggregate": str(aggregate_path),
        "marker": str(marker_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("tmp/exp03-1-synthetic-example"))
    args = parser.parse_args()
    generated = generate(args.output)
    for key, value in generated.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
