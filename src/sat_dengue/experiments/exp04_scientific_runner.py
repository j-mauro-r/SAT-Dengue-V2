"""EXP04 scientific preflight, explicit authorization, one execution and read-only reload."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
from importlib.metadata import version
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp01_preflight import git_identity
from sat_dengue.experiments.exp01_runner import reserve_execution
from sat_dengue.experiments.exp03_1_reporting import _frame_state, _restore_frame
from sat_dengue.experiments.exp03_preflight import safe_path
from sat_dengue.experiments.exp04_contract import ROOT, digest
from sat_dengue.experiments.exp04_execution import reference_role, references
from sat_dengue.experiments.exp04_oof import calendar, configuration, history, reload_bundle
from sat_dengue.experiments.exp04_runner import _provenance, write_result
from sat_dengue.experiments.exp04_scientific import (
    DIMENSIONS,
    group_id,
    run_phases,
    validate_science,
)
from sat_dengue.tracking.experiments import unique_object

SCIENTIFIC_PROTOCOL_SHA256 = "3f53615740281522f7efb2f124e810366c738acd11611a0905dbf9c27e1a599d"
PROTOCOL = ROOT / "scientific-protocol.json"
RESERVATIONS = "tmp/exp04-scientific-reservations"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(safe_path(str(path)).read_bytes(), object_pairs_hook=unique_object)


def scientific_protocol() -> dict[str, Any]:
    p = read_json(PROTOCOL)
    if (
        p.get("protocol_sha256") != SCIENTIFIC_PROTOCOL_SHA256
        or digest({k: v for k, v in p.items() if k != "protocol_sha256"})
        != SCIENTIFIC_PROTOCOL_SHA256
        or p["design_sha256"] != hashlib.sha256((ROOT / "DESING.md").read_bytes()).hexdigest()
        or p["experiment_scope_sha256"]
        != hashlib.sha256(Path("docs/product/experiments/experimentos.md").read_bytes()).hexdigest()
        or p["technical_protocol_sha256"]
        != hashlib.sha256((ROOT / "protocol.json").read_bytes()).hexdigest()
    ):
        raise ValueError("EXP04 scientific protocol or immutable authority changed")
    cfg = configuration()
    if any(cfg[name] != identity for name, identity in p["baseline"].items()):
        raise ValueError("EXP04 frozen original or replay baseline identity changed")
    return p


def local_tmp(path: Path) -> Path:
    resolved = safe_path(str(path))
    if not resolved.is_relative_to(Path.cwd().resolve() / "tmp"):
        raise ValueError("EXP04 scientific artifacts require repository-local tmp")
    return resolved


def output_path(path: Path, oof_path: Path) -> Path:
    target = local_tmp(path)
    protected = (
        local_tmp(oof_path),
        safe_path(configuration()["reconstruction_identity"]["bundle_path"]),
    )
    if (
        target.exists()
        or not target.name.startswith("exp04-")
        or any(target.is_relative_to(root) or root.is_relative_to(target) for root in protected)
    ):
        raise ValueError("Scientific output needs a new disjoint tmp/exp04-* directory")
    return target


def load_inputs(
    oof_path: Path, oof_id: str, p: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if oof_id != p["oof"]["bundle_id"]:
        raise ValueError("OOF identity differs from frozen scientific protocol")
    oof = reload_bundle(local_tmp(oof_path), oof_id)
    if oof["calendar"] != calendar() or any(
        oof["counts"].get(name) != count for name, count in p["oof"]["counts"].items()
    ):
        raise ValueError("OOF counts or calendar differ from scientific protocol")
    if oof["bundle_id"] != oof_id:
        raise ValueError("OOF identity changed")
    cells = references()
    inputs = {}
    for group in oof["calendar"]["groups"]:
        cell = cells[group["reference_cell_id"]]
        full = _restore_frame(cell.metadata["roles"]["evaluation"]["frame"])
        inputs[group_id(group)] = {
            "group": group,
            "history": _frame_state(history(oof, group, 36)),
            "selection": _frame_state(reference_role(cell, group, "selection")),
            "evaluation": _frame_state(reference_role(cell, group, "evaluation")),
            "reference_calibrator": {
                "method": "sigmoid",
                "coefficient": cell.calibrator.coefficient,
                "intercept": cell.calibrator.intercept,
            },
            "reference_threshold": cell.threshold,
            "historical_exposure": len(full) / 12,
            "historical_roles": cell.metadata["window"],
        }
    return inputs, {
        "oof_bundle_id": oof_id,
        "counts": oof["counts"],
        "oof_sha256": digest(oof),
        "baseline": configuration()["reconstruction_identity"],
        "inputs_sha256": digest(inputs),
    }


def inventory(inputs: dict[str, Any], p: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for source in inputs.values():
        group = source["group"]
        for arm, definition in p["arms"].items():
            if group["objective"] == "excess_control" and arm != "A0":
                continue
            if arm == "D" and int(group["cut"][-4:]) != 2024:
                continue
            result.append(
                {**{k: group[k] for k in DIMENSIONS}, "arm": arm, "status": definition["status"]}
            )
    return result


def preflight(oof_path: Path, oof_id: str, output: Path) -> dict[str, Any]:
    p = scientific_protocol()
    git = git_identity()
    if git["git_dirty"] or re.fullmatch(r"[0-9a-f]{40}", git["git_revision"]) is None:
        raise ValueError("Scientific preflight requires a clean committed revision")
    target = output_path(output, oof_path)
    oof_root = local_tmp(oof_path)
    inputs, source = load_inputs(oof_path, oof_id, p)
    receipt = {
        "schema": "exp04-scientific-preflight-v1",
        "experiment_id": "EXP04",
        "status": "VERIFIED",
        "scientific_protocol_sha256": p["protocol_sha256"],
        "git": git,
        "code_sha256": _provenance()["code_sha256"],
        "environment": {
            "python": platform.python_version(),
            "packages": {n: version(n) for n in ("numpy", "pandas", "scipy", "scikit-learn")},
        },
        "oof_path": str(oof_root.relative_to(Path.cwd().resolve())),
        "output": str(target.relative_to(Path.cwd().resolve())),
        "source": source,
        "cells": inventory(inputs, p),
        "predictor_fits": 0,
        "calibrator_fits": 0,
        "threshold_selections": 0,
        "mlflow_writes": 0,
        "scientific_execution_authorized": False,
        "2025": "NOT_EVALUABLE",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    return {**receipt, "receipt_sha256": digest(receipt)}


def approval_record(receipt: dict[str, Any], authority: str, reviewer: str) -> dict[str, Any]:
    if (
        authority != "Mauricio"
        or reviewer == authority
        or re.fullmatch(r"[A-Za-z][A-Za-z0-9_. -]{1,79}", reviewer) is None
    ):
        raise PermissionError("Mauricio and an independent named reviewer are required")
    return {
        "schema": "exp04-scientific-approval-v1",
        "experiment_id": "EXP04",
        "authority": authority,
        "independent_reviewer": reviewer,
        "receipt_sha256": receipt["receipt_sha256"],
        "git_revision": receipt["git"]["git_revision"],
        "scientific_protocol_sha256": receipt["scientific_protocol_sha256"],
        "oof_bundle_id": receipt["source"]["oof_bundle_id"],
        "calibration_selection_evaluation_authorized": True,
        "predictor_refits_authorized": False,
        "OOF_regeneration_authorized": False,
        "G5_approval": False,
        "champion_selection": False,
    }


def authorize(receipt: dict[str, Any], approval: dict[str, Any]) -> None:
    if receipt.get("receipt_sha256") != digest(
        {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    ):
        raise PermissionError("Scientific receipt integrity differs")
    expected = approval_record(
        receipt, approval.get("authority", ""), approval.get("independent_reviewer", "")
    )
    if canonical_bytes(approval) != canonical_bytes(expected):
        raise PermissionError("Invalid or stale policy-only authorization")
    fresh = preflight(
        Path(receipt["oof_path"]), receipt["source"]["oof_bundle_id"], Path(receipt["output"])
    )
    if canonical_bytes(fresh) != canonical_bytes(receipt):
        raise PermissionError("Scientific preflight or reviewed commit changed")


def write_record(record: dict[str, Any], path: Path, receipt: dict[str, Any] | None = None) -> None:
    target = local_tmp(path)
    if receipt is not None:
        protected = (
            local_tmp(Path(receipt["oof_path"])),
            local_tmp(Path(receipt["output"])),
            safe_path(configuration()["reconstruction_identity"]["bundle_path"]),
        )
        if any(target.is_relative_to(root) for root in protected):
            raise ValueError("Receipt/approval cannot write inside scientific inputs or output")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(canonical_bytes(record))


def publish(result: dict[str, Any], destination: Path) -> str:
    if local_tmp(destination).exists():
        raise FileExistsError(destination)
    output_path(destination, Path(result["preflight"]["oof_path"]))
    body = {**result, "bundle_id": digest(result)}
    write_result(body, destination)
    raw = (local_tmp(destination) / "result.json").read_bytes()
    manifest = {
        "schema": "exp04-scientific-manifest-v1",
        "bundle_id": body["bundle_id"],
        "scientific_protocol_sha256": result["scientific_protocol"]["protocol_sha256"],
        "files": {"result.json": hashlib.sha256(raw).hexdigest()},
    }
    write_record(manifest, destination / "manifest.json")
    return body["bundle_id"]


def execute(receipt: dict[str, Any], approval: dict[str, Any]) -> dict[str, Any]:
    authorize(receipt, approval)
    p = scientific_protocol()
    inputs, source = load_inputs(Path(receipt["oof_path"]), receipt["source"]["oof_bundle_id"], p)
    if source != receipt["source"]:
        raise ValueError("Scientific inputs changed before reservation")
    provenance = {
        "experiment_id": "EXP04",
        "scientific_protocol_sha256": p["protocol_sha256"],
        "git": receipt["git"],
        "code_sha256": receipt["code_sha256"],
        "source": source,
    }
    execution_id = reserve_execution(provenance, RESERVATIONS)
    output = run_phases(inputs, p)
    output.update(
        schema="exp04-scientific-bundle-v1",
        experiment_id="EXP04",
        scientific_protocol=p,
        provenance={
            **provenance,
            "execution_id": execution_id,
            "environment": receipt["environment"],
        },
        inputs=inputs,
        preflight=receipt,
        approval=approval,
        approval_sha256=digest(approval),
        G5="NOT_APPROVED",
        champion="not_selected",
        uncertainty="UNAVAILABLE",
        evidence="DESCRIPTIVE_ONLY",
        year_2025="NOT_EVALUABLE",
    )
    validate_science(output, p)
    # Recheck all admitted bytes and code before the first publication.
    authorize(receipt, approval)
    identity = publish(output, Path(receipt["output"]))
    validate_bundle(Path(receipt["output"]), identity)
    return {
        "status": "GENERATED_NOT_APPROVED",
        "bundle_id": identity,
        "output": receipt["output"],
        "counts": {"cells": len(output["cells"]), **output["execution_counters"]},
    }


def validate_bundle(path: Path, expected_id: str) -> dict[str, Any]:
    root = local_tmp(path)
    if {p.name for p in root.iterdir()} != {"manifest.json", "result.json"}:
        raise ValueError("Scientific file membership differs")
    manifest, result = read_json(root / "manifest.json"), read_json(root / "result.json")
    raw = safe_path(str(root / "result.json")).read_bytes()
    p = scientific_protocol()
    if (
        manifest.get("schema") != "exp04-scientific-manifest-v1"
        or manifest.get("files") != {"result.json": hashlib.sha256(raw).hexdigest()}
        or manifest.get("bundle_id") != expected_id
        or result.get("bundle_id") != expected_id
        or digest({k: v for k, v in result.items() if k != "bundle_id"}) != expected_id
        or manifest.get("scientific_protocol_sha256") != p["protocol_sha256"]
        or result.get("scientific_protocol") != p
    ):
        raise ValueError("Scientific bundle integrity or protocol differs")
    receipt, approval = result["preflight"], result["approval"]
    if (
        receipt["receipt_sha256"]
        != digest({k: v for k, v in receipt.items() if k != "receipt_sha256"})
        or canonical_bytes(approval)
        != canonical_bytes(
            approval_record(receipt, approval["authority"], approval["independent_reviewer"])
        )
        or result["approval_sha256"] != digest(approval)
    ):
        raise ValueError("Scientific authorization linkage differs")
    inputs, source = load_inputs(Path(receipt["oof_path"]), receipt["source"]["oof_bundle_id"], p)
    provenance = result["provenance"]
    if (
        source != receipt["source"]
        or provenance["source"] != source
        or digest(inputs) != digest(result["inputs"])
        or provenance["scientific_protocol_sha256"] != p["protocol_sha256"]
        or provenance["git"] != receipt["git"]
        or receipt["git"]["git_dirty"]
        or git_identity() != receipt["git"]
        or _provenance()["code_sha256"] != receipt["code_sha256"]
        or provenance["code_sha256"] != receipt["code_sha256"]
        or provenance["environment"] != receipt["environment"]
    ):
        raise ValueError("Scientific source, code or clean commit identity differs")
    validate_science(result, p)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--authorize", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--validate", type=Path)
    parser.add_argument("--oof", type=Path)
    parser.add_argument("--oof-id")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--authority")
    parser.add_argument("--reviewer")
    parser.add_argument("--permit-policy-only", action="store_true")
    parser.add_argument("--bundle-id")
    args = parser.parse_args()
    if args.preflight:
        if not all((args.oof, args.oof_id, args.destination, args.receipt)):
            parser.error("--preflight requires --oof --oof-id --destination --receipt")
        result = preflight(args.oof, args.oof_id, args.destination)
        write_record(result, args.receipt, result)
    elif args.authorize:
        if not all(
            (args.receipt, args.approval, args.authority, args.reviewer, args.permit_policy_only)
        ):
            parser.error(
                "--authorize requires --receipt --approval --authority "
                "--reviewer --permit-policy-only"
            )
        receipt = read_json(local_tmp(args.receipt))
        result = approval_record(receipt, args.authority, args.reviewer)
        authorize(receipt, result)
        write_record(result, args.approval, receipt)
    elif args.execute:
        if not args.receipt or not args.approval:
            parser.error("--execute requires --receipt and --approval")
        result = execute(read_json(local_tmp(args.receipt)), read_json(local_tmp(args.approval)))
    else:
        if not args.bundle_id:
            parser.error("--validate requires --bundle-id")
        checked = validate_bundle(args.validate, args.bundle_id)
        result = {
            "status": "VERIFIED",
            "bundle_id": checked["bundle_id"],
            "execution_counters": checked["execution_counters"],
        }
    print(canonical_bytes(result).decode(), end="")


if __name__ == "__main__":
    main()
