"""Exact proposal integrity and explicit human authorization before reserved access."""

from __future__ import annotations

import json
from importlib.metadata import version
from pathlib import Path
from typing import Any

from sat_dengue.datasets.legacy_evaluation.model_assessment.pipeline import CONTRACT, NOTEBOOK
from scripts.model_training.persistence import bytes_record, json_bytes
from scripts.training_preparation.pipeline import fingerprint

PROPOSAL_SHA = "66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09"
PROPOSAL_BUNDLE = Path(
    "artifacts/model_assessment/0f26a4eb97ad37075f3fba2d8da0afd55cf3450db945e8f9cb86d7dccac2f257"
)
PROTOCOL_DIR = Path("artifacts/model_final_protocol") / PROPOSAL_SHA
AUTHORIZATION = PROTOCOL_DIR / "human_authorization.json"


def checked_manifest(bundle: Path) -> dict[str, Any]:
    """Verify every declared local payload without repair or fitting.

    Args:
        bundle: Existing trusted local bundle.

    Returns:
        Verified manifest.
    """
    manifest = json.loads((bundle / "manifest.json").read_text())
    for name, record in manifest["files"].items():
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Unsafe manifest payload path")
        if fingerprint(bundle / name) != record:
            raise ValueError(f"Corrupt or incompatible payload: {name}")
    return manifest


def load_archived_proposal(root: Path) -> dict[str, Any]:
    """Verify the immutable proposal bundle without requiring unchanged live code.

    Args:
        root: Repository root.

    Returns:
        Original proposal, never a regenerated or substituted identity.

    Raises:
        ValueError: If the proposal or its assessment bundle is corrupt.
    """
    path = root / PROPOSAL_BUNDLE / "freeze_proposal.json"
    if fingerprint(path)["sha256"] != PROPOSAL_SHA:
        raise ValueError("Exact frozen proposal hash mismatch")
    proposal = json.loads(path.read_text())
    manifest = checked_manifest(root / PROPOSAL_BUNDLE)
    identity = proposal["identity_inputs"]
    if manifest["identity"] != identity:
        raise ValueError("Proposal and assessment identities disagree")
    return proposal


def load_proposal(root: Path) -> dict[str, Any]:
    """Verify the fixed proposal and all its live scientific implementation dependencies.

    Args:
        root: Repository root.

    Returns:
        Original proposal when live dependencies still match its frozen identity.

    Raises:
        ValueError: If any frozen live dependency changed.
    """
    proposal = load_archived_proposal(root)
    identity = proposal["identity_inputs"]
    if fingerprint(root / CONTRACT) != identity["contract"]:
        raise ValueError("Frozen scientific contract changed")
    for name, expected in identity["code"].items():
        # Only the orchestrator migrates. The original code is pinned, not waived.
        path = (
            root / PROTOCOL_DIR / "development_notebook_code.json"
            if name == str(NOTEBOOK)
            else root / name
        )
        if fingerprint(path) != expected:
            raise ValueError(f"Frozen dependency changed: {name}")
    for name, expected in identity["versions"].items():
        if version(name) != expected:
            raise ValueError(f"Frozen runtime changed: {name}")
    source = root / identity["input_bundle"]
    if fingerprint(source / "manifest.json") != identity["input_manifest"]:
        raise ValueError("Frozen input manifest changed")
    checked_manifest(source)
    for procedure in proposal["procedures"]:
        for name, expected in procedure["provenance"].items():
            if fingerprint(source / name) != expected:
                raise ValueError("Retained component lineage changed")
    return proposal


def require_authorization(root: Path) -> dict[str, Any]:
    """Require a recorded human decision bound to the exact proposal before any access.

    Args:
        root: Repository root containing an externally recorded human decision.

    Returns:
        Accepted decision record with its immutable source fingerprint.

    Raises:
        PermissionError: If G4, protocol or execution acceptance is absent.
    """
    path = root / AUTHORIZATION
    if not path.is_file():
        raise PermissionError(
            "Explicit human G4, exact protocol and final execution acceptance required"
        )
    decision = json.loads(path.read_text())
    if (
        decision.get("authority") != "Mauricio"
        or decision.get("proposal_sha256") != PROPOSAL_SHA
        or any(
            decision.get(k) is not True
            for k in ("accept_G4", "accept_exact_protocol", "authorize_final_execution")
        )
    ):
        raise PermissionError("Incomplete or mismatched human authorization")
    evidence = decision.get("decision_source", {})
    source = (root / evidence.get("path", "")).resolve()
    if not source.is_relative_to(root.resolve()) or not source.is_file():
        raise PermissionError("Missing local human decision evidence")
    if fingerprint(source) != evidence.get("fingerprint") or not source.read_text().strip():
        raise PermissionError("Human decision evidence changed or is empty")
    return decision


def code_fingerprints(root: Path) -> dict[str, Any]:
    """Identify final implementation and migrated notebook code separately from the proposal.

    Args:
        root: Repository root.

    Returns:
        Reproducible file identities including code-only notebook cells.
    """
    records = {
        str(p.relative_to(root)): fingerprint(p)
        for p in sorted((root / "scripts/final_evaluation").glob("*.py"))
    }
    notebook = json.loads((root / NOTEBOOK).read_text())
    if any(c["cell_type"] != "code" for c in notebook["cells"]):
        raise ValueError("Notebook08 must remain code-only")
    records[str(NOTEBOOK)] = bytes_record(
        json_bytes({"cells": ["".join(c["source"]) for c in notebook["cells"]]})
    )
    return records
