"""Authorized EXP03 identity admission; no reservations, fitting or tracking.

The expected root hash names the manifest, not the CSV. Its verified output
records authenticate payloads; separately pinned files include the scope catalog.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, BinaryIO

from sat_dengue.configuration import AUTHORITIES
from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_preflight import safe_path
from sat_dengue.tracking.experiments import unique_object

ZERO_EFFECTS = dict(
    reservations=0, mlflow_writes=0, real_model_fits=0, calibrator_fits=0, publications=0
)


class AdmissionError(ValueError):
    """Admission failed before any scientific side effects."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.receipt = {
            "status": "rejected",
            "source_identity_status": "unverified",
            **ZERO_EFFECTS,
        }


def verified_file(
    relative: str, expected: dict[str, Any], *, read: bool = False, copy_to: BinaryIO | None = None
) -> bytes:
    """Check a regular canonical file before/after reading the same descriptor."""
    if (
        set(expected) != {"sha256", "bytes"}
        or not isinstance(expected["sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", expected["sha256"]) is None
        or type(expected["bytes"]) is not int
        or expected["bytes"] <= 0
    ):
        raise ValueError("Invalid EXP03 expected file identity")
    path = safe_path(relative)
    if not path.is_file():
        raise ValueError("Required EXP03 source is missing")
    before = path.stat()
    hasher = hashlib.sha256()
    size = 0
    content = bytearray()
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise ValueError("EXP03 source replaced before read")
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            hasher.update(block)
            size += len(block)
            if read:
                content.extend(block)
            if copy_to is not None:
                copy_to.write(block)
        after = os.fstat(stream.fileno())
    current = safe_path(relative).stat()

    def signature(st: os.stat_result) -> tuple[int, ...]:
        return (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)

    if signature(opened) != signature(after) or signature(after) != signature(current):
        raise ValueError("EXP03 source changed while reading")
    if {"sha256": hasher.hexdigest(), "bytes": size} != expected:
        raise ValueError("EXP03 source fingerprint mismatch")
    return bytes(content)


def admit_sources(receipt: dict[str, Any], config: PreparationConfig) -> dict[str, Any]:
    """Called only by the runner after authorize; verify before scientific preparation."""
    sources = receipt["sources"]
    manifest_path = sources["manifest_path"]
    pinned = sources["expected_pinned_files"]
    expected = receipt["expected_source_sha256"]
    if expected != sources["expected_source_sha256"] or expected != pinned[manifest_path]["sha256"]:
        raise ValueError("Contradictory EXP03 expected source identity")
    manifest_bytes = verified_file(manifest_path, pinned[manifest_path], read=True)
    manifest = json.loads(manifest_bytes, object_pairs_hook=unique_object)
    contract_path = str((config.root / config.contract_path).absolute().relative_to(Path.cwd()))
    contract_bytes = safe_path(contract_path).read_bytes()
    contract = json.loads(contract_bytes, object_pairs_hook=unique_object)
    authority = safe_path(AUTHORITIES["training_preparation_contract_v1"]["path"])
    if contract != json.loads(authority.read_text()):
        raise ValueError("Preparation authority changed")
    # Same governed output map as the unchanged shared raw-input validator.
    names = {
        "dengue_y_dengue_grave": "data/processed/dengue_y_dengue_grave.csv",
        "panel_mensual_dengue_clima": contract["panel_path"],
        "candidate_contract": contract["upstream_contract_path"],
        "y_label_history_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/y_label_history_traceability.csv"
        ),
        "current_endemic_channel_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/"
            "current_endemic_channel_traceability.csv"
        ),
    }
    records = dict(pinned)
    for key, relative in names.items():
        record = manifest["outputs"][key]
        if record["path"] != relative:
            raise ValueError("Unexpected EXP03 manifest output path")
        path = str((config.root / relative).absolute().relative_to(Path.cwd()))
        identity = {key: record[key] for key in ("sha256", "bytes")}
        if path in records and records[path] != identity:
            raise ValueError("Contradictory EXP03 pinned payload identity")
        records[path] = identity
    if set(records) != set(sources["declared_paths"]):
        raise ValueError("EXP03 declared sources differ from verified manifest")
    for path, identity in records.items():
        verified_file(path, identity)
    records[contract_path] = {
        "sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "bytes": len(contract_bytes),
    }
    return {
        "schema": "exp03-admission-v1",
        "status": "identity_verified",
        "source_identity_status": "verified",
        "source_kind": "manifest_root_of_trust",
        "expected_source_sha256": expected,
        "observed_source_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "manifest_path": manifest_path,
        "structural_receipt_sha256": digest(receipt),
        "files": records,
        **ZERO_EFFECTS,
    }


def reverify(admission: dict[str, Any]) -> None:
    """Fresh bytes/path checks at consumption and side-effect boundaries."""
    for path, identity in admission["files"].items():
        verified_file(path, identity)


@contextmanager
def verified_snapshot(
    config: PreparationConfig, admission: dict[str, Any]
) -> Iterator[PreparationConfig]:
    """Parse only verified copies; source replacement cannot alter consumed bytes.

    Copies are bounded-memory streams under ignored tmp, created only after
    authorization and removed on success/failure. No snapshot is a publication.
    The unchanged raw-input adapter operates on this isolated root.
    """
    parent = safe_path("tmp/exp03-admission-snapshots")
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.TemporaryDirectory(dir=parent) as directory:
        root = Path(directory)
        for name, identity in admission["files"].items():
            relative = (Path.cwd() / name).relative_to(config.root)
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open("xb") as stream:
                target.chmod(0o600)
                verified_file(name, identity, copy_to=stream)
        yield PreparationConfig(root, config.contract_path, config.manifest_path)


def validate_admission(provenance: dict[str, Any]) -> None:
    """Real publication must carry the verified observed identities, not only pins."""
    a = provenance.get("source_admission", {})
    if not isinstance(a, dict):
        raise ValueError("Invalid EXP03 verified admission lineage")
    expected = a.get("expected_source_sha256")
    files = a.get("files")
    manifest = a.get("manifest_path")
    if (
        a.get("schema") != "exp03-admission-v1"
        or a.get("status") != "verified"
        or a.get("source_identity_status") != "verified"
        or not isinstance(expected, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected) is None
        or a.get("source_kind") != "manifest_root_of_trust"
        or not isinstance(a.get("structural_receipt_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", a["structural_receipt_sha256"]) is None
        or any(type(a.get(k)) is not int or a[k] != 0 for k in ZERO_EFFECTS)
        or a.get("observed_source_sha256") != expected
        or provenance.get("data_version") != expected
        or not isinstance(files, dict)
        or not isinstance(manifest, str)
        or manifest not in files
        or not isinstance(files[manifest], dict)
        or files[manifest].get("sha256") != expected
        or provenance.get("data_sha256") != digest(a["files"])
        or provenance.get("admission_sha256") != digest(a)
    ):
        raise ValueError("Invalid EXP03 verified admission lineage")
