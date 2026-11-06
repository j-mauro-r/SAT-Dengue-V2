"""EXP-DELTA03 Phase2 adapters; metadata admission never parses private table rows."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.datasets.exp_delta03 import ROOT, canonical, identity, safe_path
from sat_dengue.experiments.exp_delta03_contract import derive_plan

TRAINING_CONTRACT = "docs/product/experiments/EXP-DELTA03/training-contract.json"


def read_metadata(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    """Bind all immutable input bytes but read only JSON descriptors, not real rows."""
    spec = contract["matrix_bundle"]
    folder = safe_path(root, spec["path"], "tmp/exp-delta03-phase1/products")
    manifest_path = safe_path(
        root, spec["path"] + "/manifest.json", "tmp/exp-delta03-phase1/products"
    )
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != spec["manifest_sha256"]:
        raise ValueError("Phase1 manifest identity changed")
    manifest = json.loads(manifest_bytes)
    if hashlib.sha256(canonical(manifest["files"])).hexdigest() != folder.name or spec[
        "matrices"
    ] != manifest["files"].get("matrices.json"):
        raise ValueError("Prepared content identity changed")
    if manifest["files"] != spec["files"]:
        raise ValueError("Declared prepared artifacts changed")
    for name, record in manifest["files"].items():
        if Path(name).name != name:
            raise ValueError("Unsafe prepared member")
        path = safe_path(root, spec["path"] + "/" + name, "tmp/exp-delta03-phase1/products")
        if identity(path) != record:
            raise ValueError("Prepared matrix member changed")
    source = contract["source_contract"]
    if identity(safe_path(root, source["path"], "docs/product/experiments/EXP-DELTA03")) != {
        "sha256": source["sha256"],
        "bytes": source["bytes"],
    }:
        raise ValueError("Preparation source contract changed")
    metadata_path = safe_path(
        root, spec["path"] + "/matrices.json", "tmp/exp-delta03-phase1/products"
    )
    metadata_bytes = metadata_path.read_bytes()
    if {"sha256": hashlib.sha256(metadata_bytes).hexdigest(), "bytes": len(metadata_bytes)} != spec[
        "matrices"
    ]:
        raise ValueError("Parsed metadata snapshot identity changed")
    metadata = json.loads(metadata_bytes)
    return {
        "metadata": metadata,
        "plan": derive_plan(metadata, metadata_sha256=spec["matrices"]["sha256"]),
        "contract": contract,
        "real_table_rows_parsed": 0,
    }


class Delta03TrainingMetadataDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        path = safe_path(ROOT, TRAINING_CONTRACT, "docs/product/experiments/EXP-DELTA03")
        raw = path.read_bytes()
        return {
            **read_metadata(ROOT, json.loads(raw)),
            "training_contract_sha256": hashlib.sha256(raw).hexdigest(),
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Read-only training metadata")

    def _describe(self) -> dict[str, Any]:
        return {"contract": TRAINING_CONTRACT, "real_rows": "never loaded by metadata adapter"}
