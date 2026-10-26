"""Authorization, source loading and execution orchestration for future EXP01 runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sat_dengue.configuration import AUTHORITIES
from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, NATIVE_MANIFEST
from sat_dengue.experiments.exp01 import (
    digest,
    execute_paired,
    load_protocol,
    native_calibration,
    native_fit,
)
from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs
from sat_dengue.experiments.exp01_preflight import (
    authorize,
    git_identity,
    safe_path,
    source_metadata,
    storage_preflight,
)


def load_authorized_sources(receipt: dict[str, Any]) -> dict[str, Any]:
    """Approval precedes every private-content read and any tracking creation."""
    approval = authorize(receipt)
    if receipt["sources"] != source_metadata():
        raise ValueError("EXP01 source metadata changed after preflight")
    if fingerprint(safe_path(NATIVE_MANIFEST)) != NATIVE_IDENTITIES[NATIVE_MANIFEST]:
        raise ValueError("EXP01 data version differs from approved manifest")
    prepared = prepare_exp01_inputs(PreparationConfig(Path.cwd()))
    panel = prepared.panel
    if panel.year_month.ge("2025-01").any():
        raise ValueError("Consumed 2025 cannot enter EXP01")
    protocol = load_protocol()
    if len(panel.municipality_code.unique()) != protocol["population"]["municipalities"]:
        raise ValueError("EXP01 population differs from frozen protocol")
    expected_contract = json.loads(
        Path(AUTHORITIES["training_preparation_contract_v1"]["path"]).read_text()
    )
    if prepared.contract != expected_contract:
        raise ValueError("EXP01 preparation contract changed")
    return {
        "panel": panel,
        "contract": prepared.contract,
        "input_fingerprints": prepared.report["input_fingerprints"],
        "preflight": receipt,
        "approval_sha256": digest(approval),
    }


def reserve_execution(provenance: dict[str, Any], output_root: str) -> str:
    """Atomically reserve scientific identity independently of approval metadata."""
    execution_id = digest({k: v for k, v in provenance.items() if k != "approval_sha256"})
    root = safe_path(output_root, temporary=True)
    root.mkdir(parents=True, exist_ok=True)
    reservation = safe_path(str(root / (execution_id + ".reservation")), temporary=True)
    try:
        with reservation.open("x") as stream:
            stream.write(execution_id + "\n")
    except FileExistsError as error:
        raise ValueError(
            "EXP01 duplicate or interrupted execution; explicit human recovery required"
        ) from error
    return execution_id


def execute_authorized(sources: dict[str, Any]) -> dict[str, Any]:
    """Reserve an execution identity before fitting; failures require human recovery."""
    from sat_dengue.tracking.exp01 import Exp01Tracking

    receipt = sources["preflight"]
    approval = authorize(receipt)
    if digest(approval) != sources["approval_sha256"]:
        raise ValueError("EXP01 approval changed")
    provenance = {
        key: receipt[key]
        for key in (
            "protocol_sha256",
            "data_version",
            "configuration_sha256",
            "git_revision",
            "code_sha256",
            "environment_sha256",
            "code",
            "runtime",
            "versions",
        )
    }
    provenance["data_sha256"] = digest(sources["input_fingerprints"])
    provenance["approval_sha256"] = sources["approval_sha256"]
    provenance["operational_reference"] = receipt["operational_reference"]
    provenance["historical_predictions"] = receipt["historical_predictions"]
    for relative, expected in sources["input_fingerprints"].items():
        if fingerprint(safe_path(relative)) != expected:
            raise ValueError("EXP01 source changed before execution")
    storage_preflight(receipt["tracking"]["root"])
    execution_id = reserve_execution(provenance, receipt["output_root"])
    tracker = Exp01Tracking(
        "exp01", execution_id, receipt["tracking"]["root"], experiment_id="EXP01"
    )
    try:
        tracker.initialize_paired(provenance, synthetic=False)
        protocol = load_protocol()
        result = execute_paired(
            sources["panel"],
            sources["contract"],
            protocol["design"],
            fit=native_fit,
            calibrate=native_calibration,
        )
        for relative, expected in sources["input_fingerprints"].items():
            if fingerprint(safe_path(relative)) != expected:
                raise ValueError("EXP01 source changed during execution")
        if digest(load_protocol()) != receipt["protocol_sha256"] or git_identity() != {
            "git_revision": receipt["git_revision"],
            "git_dirty": False,
        }:
            raise ValueError("EXP01 protocol/code changed during execution")
        if digest(authorize(receipt)) != sources["approval_sha256"]:
            raise ValueError("EXP01 approval/code/runtime changed during execution")
        if result["real_model_fits"] != protocol["design"]["expected_model_fits"]:
            raise ValueError("EXP01 fit budget differs from frozen design")
        return {"result": result, "provenance": provenance, "tracker": tracker}
    except BaseException as error:
        tracker.fail(aborted=isinstance(error, (KeyboardInterrupt, SystemExit)))
        raise
