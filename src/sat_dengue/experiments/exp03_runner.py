"""EXP03 authorization precedes private reads, reservations, fits and tracking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sat_dengue.configuration import AUTHORITIES
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import execute, load_protocol, native_fit
from sat_dengue.experiments.exp03_admission import (
    AdmissionError,
    admit_sources,
    reverify,
    verified_file,
    verified_snapshot,
)
from sat_dengue.experiments.exp03_persistence import fit_calibration
from sat_dengue.experiments.exp03_preflight import OUTPUT_ROOT, authorize, safe_path


def load_authorized_sources(receipt: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_engine import require_budget

    require_budget(load_protocol()["design"])
    approval = authorize(receipt)
    from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
    from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs

    try:
        config = PreparationConfig(Path.cwd())
        admission = admit_sources(receipt, config)
        # The unchanged adapter parses verified copies, never a later source reopen.
        reverify(admission)
        with verified_snapshot(config, admission) as snapshot:
            inputs = prepare_exp01_inputs(snapshot)
        reverify(admission)
        observed = {
            str((config.root / name).absolute().relative_to(Path.cwd())): record
            for name, record in inputs.report["input_fingerprints"].items()
        }
        if observed != admission["files"]:
            raise AdmissionError("EXP03 consumed identities differ from admission")
        if (
            inputs.panel.year_month.ge("2025-01").any()
            or inputs.panel.municipality_code.nunique() != 76
        ):
            raise AdmissionError("EXP03 population/time mismatch")
        contract = json.loads(
            safe_path(AUTHORITIES["training_preparation_contract_v1"]["path"]).read_text()
        )
        if inputs.contract != contract:
            raise AdmissionError("Preparation authority changed")
        admission["status"] = "verified"
        return {
            "panel": inputs.panel,
            "contract": contract,
            "fingerprints": observed,
            "admission": admission,
            "preparation_config": config,
            "preflight": receipt,
            "approval_sha256": digest(approval),
        }
    except (ValueError, OSError, KeyError, TypeError) as error:
        if isinstance(error, AdmissionError):
            raise
        raise AdmissionError(str(error)) from error


def execute_authorized(sources: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_engine import require_budget
    from sat_dengue.tracking.exp03 import Exp03Tracking

    try:
        require_budget(load_protocol()["design"])
        receipt = sources["preflight"]
        if digest(authorize(receipt)) != sources["approval_sha256"]:
            raise PermissionError("Approval changed")

        def verify() -> None:
            reverify(sources["admission"])
            if sources["admission"].get("status") != "verified" or (
                sources["admission"]["structural_receipt_sha256"] != digest(receipt)
                or sources["fingerprints"] != sources["admission"]["files"]
            ):
                raise ValueError("EXP03 admission changed")
            if digest(authorize(receipt)) != sources["approval_sha256"]:
                raise PermissionError("Authorization changed")

        verify()
        provenance = {
            k: receipt[k]
            for k in (
                "protocol_sha256",
                "configuration_sha256",
                "git_revision",
                "data_version",
                "code_sha256",
                "environment_sha256",
            )
        }
        provenance["data_sha256"] = digest(sources["fingerprints"])
        provenance["source_admission"] = sources["admission"]
        provenance["admission_sha256"] = digest(sources["admission"])
        import hashlib

        provenance["scope_sha256"] = hashlib.sha256(
            safe_path("docs/product/experiments/EXP03_feature_ablation/alcance.md").read_bytes()
        ).hexdigest()
        provenance["matrix_sha256"] = digest(load_protocol()["design"])
        from sat_dengue.experiments.exp03_features import cohorts

        cohorts(sources["panel"], sources["contract"], load_protocol()["design"])
        # Recheck after deterministic preparation, immediately before reservation/tracking.
        verify()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise AdmissionError(str(error)) from error
    execution_id = reserve_execution(provenance)
    tracker = Exp03Tracking(
        "exp03", execution_id, receipt["tracking"]["root"], experiment_id="EXP03"
    )
    try:
        tracker.initialize_ablation(provenance)
        result = execute(
            sources["panel"],
            sources["contract"],
            load_protocol()["design"],
            fit=native_fit,
            calibrate=fit_calibration,
            terminal_root=safe_path(OUTPUT_ROOT) / (execution_id + "-terminal"),
            provenance=provenance,
        )
        provenance["freeze_timestamp"] = result["terminal_manifest"]["frozen_at"]
        benchmark = evaluate_authorized_benchmark(
            sources, result, safe_path(OUTPUT_ROOT) / (execution_id + "-terminal")
        )
        result["transport_2024_2025"] = benchmark["transport_2024_2025"]
        result["benchmark_predictions"] = benchmark["benchmark_predictions"]
        result["benchmark_execution_counters"] = benchmark["execution_counters"]
        result["performance_by_group"].extend(benchmark["performance_by_group"])
        verify()
        return {"result": result, "provenance": provenance, "tracker": tracker}
    except BaseException:
        tracker.fail()
        raise


def reserve_execution(provenance: dict[str, Any]) -> str:
    """Exclusive persistent marker; interrupted runs require human recovery."""
    execution_id = digest(provenance)
    root = safe_path(OUTPUT_ROOT, OUTPUT_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    # Persistent exclusive marker survives interrupts; retry needs human recovery.
    with safe_path(str(root / (execution_id + ".reservation"))).open("x") as stream:
        stream.write(execution_id + "\n")
    return execution_id


def evaluate_authorized_benchmark(
    sources: dict[str, Any], result: dict[str, Any], terminal_root: Path
) -> dict[str, Any]:
    """Admit governed consumed-year sources only after the complete terminal freeze.

    Source provenance must explicitly establish coverage and maturity. Missing
    evidence is a per-cell not-evaluable result, never a guessed calendar approval.
    """
    import pandas as pd  # type: ignore[import-untyped]

    from sat_dengue.experiments.exp03_benchmark import evaluate_benchmark
    from sat_dengue.experiments.exp03_engine import require_budget
    from sat_dengue.experiments.exp03_inputs import prepare_benchmark_inputs
    from sat_dengue.experiments.exp03_persistence import _load_terminal

    design = load_protocol()["design"]
    require_budget(design)
    if digest(authorize(sources["preflight"])) != sources["approval_sha256"]:
        raise PermissionError("Benchmark authorization changed")
    _, _, freeze_identity = _load_terminal(terminal_root)
    if freeze_identity != result["terminal_manifest"]["manifest_sha256"]:
        raise ValueError("Terminal freeze changed before source admission")
    admission = sources["admission"]
    reverify(admission)
    manifest_path = sources["preflight"]["sources"]["manifest_path"]
    source_manifest = json.loads(
        verified_file(manifest_path, admission["files"][manifest_path], read=True)
    )
    readiness = source_manifest.get("coverage", {}).get("exp03_consumed_2025_readiness", {})
    if not isinstance(readiness, dict):
        raise ValueError("Invalid consumed-year provenance readiness record")
    coverage = {**readiness, "provenance_sha256": digest(source_manifest)}
    ready = coverage.get("governed_coverage") is True and coverage.get("maturity_verified") is True
    panel = pd.DataFrame()
    if ready:
        with verified_snapshot(sources["preparation_config"], admission) as snapshot:
            panel = prepare_benchmark_inputs(snapshot, coverage).panel
    reverify(admission)
    return evaluate_benchmark(
        panel, sources["contract"], design, terminal_root, coverage, freeze_identity
    )
