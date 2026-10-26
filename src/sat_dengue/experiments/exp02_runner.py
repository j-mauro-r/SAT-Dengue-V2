"""EXP02 authorization precedes private reads, reservations, fits and tracking."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sat_dengue.configuration import AUTHORITIES
from sat_dengue.experiments.exp01 import digest, native_calibration
from sat_dengue.experiments.exp02 import execute, load_protocol, native_fit
from sat_dengue.experiments.exp02_preflight import OUTPUT_ROOT, authorize, safe_path


def load_authorized_sources(receipt: dict[str, Any]) -> dict[str, Any]:
    approval = authorize(receipt)
    from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
    from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint, prepare_inputs
    from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, NATIVE_MANIFEST

    for declared in receipt["sources"]["declared_paths"]:
        safe_path(declared)
    if fingerprint(safe_path(NATIVE_MANIFEST)) != NATIVE_IDENTITIES[NATIVE_MANIFEST]:
        raise ValueError("Approved data manifest changed")
    if approval["data_version"] != receipt["data_version"]:
        raise PermissionError("Data version mismatch")
    inputs = prepare_inputs(PreparationConfig(Path.cwd()), reference_end="2024-12")
    if (
        inputs.panel.year_month.ge("2025-01").any()
        or inputs.panel.municipality_code.nunique() != 76
    ):
        raise ValueError("EXP02 population/time mismatch")
    contract = json.loads(
        safe_path(AUTHORITIES["training_preparation_contract_v1"]["path"]).read_text()
    )
    if inputs.contract != contract:
        raise ValueError("Preparation authority changed")
    return {
        "panel": inputs.panel,
        "contract": contract,
        "fingerprints": inputs.report["input_fingerprints"],
        "preflight": receipt,
        "approval_sha256": digest(approval),
    }


def execute_authorized(sources: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
    from sat_dengue.tracking.exp02 import Exp02Tracking

    receipt = sources["preflight"]
    if digest(authorize(receipt)) != sources["approval_sha256"]:
        raise PermissionError("Approval changed")

    def verify() -> None:
        for name, record in sources["fingerprints"].items():
            if fingerprint(safe_path(name)) != record:
                raise ValueError("EXP02 data changed during execution")
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
    execution_id = reserve_execution(provenance)
    tracker = Exp02Tracking(
        "exp02", execution_id, receipt["tracking"]["root"], experiment_id="EXP02"
    )
    try:
        tracker.initialize_ablation(provenance)
        result = execute(
            sources["panel"],
            sources["contract"],
            load_protocol()["design"],
            fit=native_fit,
            calibrate=native_calibration,
        )
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
