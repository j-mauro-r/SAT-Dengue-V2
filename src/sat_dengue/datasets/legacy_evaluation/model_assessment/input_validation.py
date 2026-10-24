"""Accept verified reexecutions without changing the audited scientific result."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

# Only upstream manifest references may change when scientific payloads stay exact.
PROVENANCE_FIELDS = frozenset(
    {"stage4_candidate_manifests", "stage4_candidate_suite_manifest", "stage4_reference_manifest"}
)
SUMMARY_REFERENCES = {
    "stage4_reference_bundle": "stage4_reference_bundle",
    "stage4_suite_bundle": "stage4_candidate_suite_bundle",
}


def _verified_manifest(bundle: Path) -> dict[str, Any]:
    """Read a manifest and check every declared payload before comparing results."""
    manifest: dict[str, Any] = json.loads((bundle / "manifest.json").read_text())
    if manifest["bundle_id"] != bundle.name:
        raise ValueError("Stage5 bundle identity does not match its directory")
    for name, record in manifest["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Invalid Stage5 payload path")
        data = (bundle / relative).read_bytes()
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"Stage5 payload integrity failure: {name}")
    return manifest


def verify_equivalent_input(bundle: Path, approved: Path) -> dict[str, Any]:
    """Require exact scientific equivalence to the retained audited input.

    Args:
        bundle: Current input already verified against the live Stage5 pipeline.
        approved: Retained audited anchor, required even for an equivalent rerun.

    Returns:
        Traceable compatibility receipt; never a scientific or human gate approval.

    Raises:
        ValueError: If rules, code, runtime, scientific payloads or summary change.
        OSError: If an input or the audited anchor is absent; never triggers fitting.
    """
    actual = _verified_manifest(bundle)
    anchor = _verified_manifest(approved)
    for field in ("schema", "rules"):
        if actual[field] != anchor[field]:
            raise ValueError(f"Stage5 rerun changed {field}; review required")
    stable_actual = {k: v for k, v in actual["identity"].items() if k not in PROVENANCE_FIELDS}
    stable_anchor = {k: v for k, v in anchor["identity"].items() if k not in PROVENANCE_FIELDS}
    if stable_actual != stable_anchor:
        raise ValueError(
            "Stage5 rerun changed scientific code/configuration/runtime; review required"
        )
    if actual["files"].keys() != anchor["files"].keys():
        raise ValueError("Stage5 rerun changed payload inventory; review required")
    for name in actual["files"]:
        if name != "run_summary.json" and actual["files"][name] != anchor["files"][name]:
            raise ValueError(f"Stage5 rerun changed scientific payload {name}; review required")
    summaries = []
    for path, manifest in ((bundle, actual), (approved, anchor)):
        summary = json.loads((path / "run_summary.json").read_text())
        for summary_key, manifest_key in SUMMARY_REFERENCES.items():
            if summary.pop(summary_key) != manifest[manifest_key]:
                raise ValueError("Stage5 summary provenance disagrees with manifest")
        summaries.append(summary)
    if summaries[0] != summaries[1]:
        raise ValueError("Stage5 rerun changed scientific summary; review required")
    return {
        "status": "exact_audited_input" if bundle == approved else "scientifically_identical_rerun",
        "actual_bundle": bundle.name,
        "audited_anchor": approved.name,
        "verified_scientific_files": len(actual["files"]) - 1,
        "allowed_changes": "upstream manifest references and matching summary paths only",
        "human_gate_approval": False,
    }
