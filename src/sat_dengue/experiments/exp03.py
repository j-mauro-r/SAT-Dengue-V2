"""Revised bounded EXP03 entry points; legacy scientific identities are not executable."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01
from sat_dengue.experiments.exp03_engine import execute
from sat_dengue.experiments.exp03_persistence import fit_calibration
from sat_dengue.experiments.exp03_persistence import fit_native as native_fit
from sat_dengue.experiments.exp03_revision import COMPOSITIONS, validate_design

PROTOCOL = Path("docs/product/experiments/EXP03_feature_ablation/protocol.json")
VARIANTS = tuple(COMPOSITIONS)


def load_protocol() -> dict[str, Any]:
    from sat_dengue.tracking.experiments import resolve_experiment

    p = json.loads(PROTOCOL.read_text())
    if exp01.digest(p) != resolve_experiment("EXP03")["protocol_sha256"]:
        raise ValueError("EXP03 protocol changed")
    source = exp01.load_protocol()
    if exp01.digest(source) != p["reproducibility"]["exp01_protocol_sha256"]:
        raise ValueError("EXP01 scientific interface changed")
    for key in ("families", "seed", "threads", "calibration"):
        if p["design"][key] != source["design"][key]:
            raise ValueError("EXP03 differs from fixed EXP01 families: " + key)
    validate_design(p["design"])
    return p


def variant_names() -> tuple[str, ...]:
    return tuple(load_protocol()["design"]["variants"])


def synthetic_run() -> dict[str, Any]:
    """Complete generated native-estimator example; never reads scientific sources."""
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(v, freq="M") + 180) for v in panel.year_month]
    import numpy as np

    extension = panel.loc[panel.year_month.str.startswith("2024")].copy()
    extension["year_month"] = extension.year_month.str.replace("2024", "2025")
    rng = np.random.default_rng(4303)
    for column in contract["roles"]["predictors"]:
        if column != "zona_canal_t":
            extension[column] = rng.integers(0, 100, size=len(extension)).astype(float)
    benchmark_panel = pd.concat([panel, extension], ignore_index=True)
    panel.attrs["synthetic_generated"] = True
    design = load_protocol()["design"]
    design.update(
        B_primary=2.0,
        budget_rationale="Synthetic fixture only; no operational or scientific authorization",
        synthetic_budget_fixture=True,
    )
    import hashlib

    from sat_dengue.experiments.exp01_preflight import execution_metadata, git_identity
    from sat_dengue.experiments.exp03_engine import records

    scope = Path("docs/product/experiments/EXP03_feature_ablation/alcance.md")
    metadata = execution_metadata()
    provenance = {
        **metadata,
        **git_identity(),
        "synthetic": True,
        "evidence_class": "synthetic_generated_data",
        "protocol_sha256": exp01.digest(load_protocol()),
        "scope_sha256": hashlib.sha256(scope.read_bytes()).hexdigest(),
        "matrix_sha256": exp01.digest(design),
        "configuration_sha256": exp01.digest(design),
        "data_sha256": exp01.digest(records(panel)),
        "benchmark_data_sha256": exp01.digest(records(benchmark_panel)),
    }
    root = Path("tmp/exp03-synthetic")
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as folder:
        result = execute(
            panel,
            contract,
            design,
            fit=native_fit,
            calibrate=fit_calibration,
            synthetic=True,
            terminal_root=Path(folder) / "model_artifacts",
            provenance=provenance,
        )

        from sat_dengue.experiments.exp03_benchmark import evaluate_benchmark

        benchmark = evaluate_benchmark(
            benchmark_panel,
            contract,
            design,
            Path(folder) / "model_artifacts",
            {
                "governed_coverage": True,
                "maturity_verified": True,
                "provenance_sha256": provenance["benchmark_data_sha256"],
                "synthetic": True,
            },
            result["terminal_manifest"]["manifest_sha256"],
        )
        provenance["freeze_timestamp"] = result["terminal_manifest"]["frozen_at"]
        result["synthetic_provenance"] = provenance
        result["transport_2024_2025"] = benchmark["transport_2024_2025"]
        result["benchmark_predictions"] = benchmark["benchmark_predictions"]
        result["benchmark_execution_counters"] = benchmark["execution_counters"]
        result["performance_by_group"].extend(benchmark["performance_by_group"])
        return result
