"""Explicit canonical identity consumption and isolated Beta publication."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import CANONICAL_AUTHORITY, canonical_bytes
from sat_dengue.datasets.canonical import (
    CanonicalBundleDataset,
    execution_identity,
    verify_records,
)
from sat_dengue.datasets.legacy_preparation.pipeline import parse_fields
from sat_dengue.datasets.stage2 import identity, local_path, verified_json

PROTOCOL_PATH = "docs/product/experiments/EXP-BETA01/protocol.phase2.json"
PROTOCOL_SHA256 = "88e05dc69a64fa443f60ab29a135216c300b82e8efd8715d450a6787a55964da"


class BetaSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Load one frozen bundle, never search/latest/rebuild the canonical source."""

    def load(self) -> dict[str, Any]:
        protocol_path = local_path(PROTOCOL_PATH)
        protocol_identity = identity(protocol_path)
        if protocol_identity["sha256"] != PROTOCOL_SHA256:
            raise DatasetError("Unapproved Beta protocol identity")
        protocol = verified_json(PROTOCOL_PATH, protocol_identity)
        if (
            protocol["policy"]["formal_adoption"]
            != "Mauricio, explicit instruction 2026-11-01 before fitting"
        ):
            raise DatasetError("Beta criteria require formal adoption before execution")
        folder = (
            local_path("data/processed/canonical_model_table_v1") / protocol["canonical_bundle_id"]
        )
        manifest_fp = identity(folder / "manifest.json")
        if manifest_fp["sha256"] != protocol["canonical_manifest_sha256"]:
            raise DatasetError("Incorrect pinned canonical manifest")
        manifest = json.loads((folder / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if (
            manifest["schema"] != "canonical-model-table-publication-v1"
            or hashlib.sha256(canonical_bytes(body)).hexdigest() != folder.name
            or manifest["bundle_id"] != folder.name
            or set(p.name for p in folder.iterdir()) != {*manifest["files"], "manifest.json"}
        ):
            raise DatasetError("Invalid canonical bundle identity/membership")
        records = {
            PROTOCOL_PATH: protocol_identity,
            str(folder.relative_to(Path.cwd()) / "manifest.json"): manifest_fp,
            **manifest["sources"],
        }
        for name, fp in manifest["files"].items():
            if Path(name).name != name:
                raise DatasetError("Unsafe canonical payload")
            records[str(folder.relative_to(Path.cwd()) / name)] = fp
        verify_records(records)
        contract = verified_json(CANONICAL_AUTHORITY["path"], CANONICAL_AUTHORITY["identity"])
        if json.loads((folder / "contract.json").read_text()) != contract:
            raise DatasetError("Canonical contract snapshot mismatch")
        columns = json.loads((folder / "columns.json").read_text())
        fields = [
            {**f, "dtype": {"boolean": "bool"}.get(f["dtype"], f["dtype"])}
            for f in columns["columns"]
        ]
        raw = pd.read_csv(
            folder / "canonical_model_table_v1.csv", dtype="string", keep_default_na=False
        )
        if raw.columns.tolist() != [f["name"] for f in fields]:
            raise DatasetError("Canonical columns/order mismatch")
        table = parse_fields(raw, {"schema": fields})
        reference = None
        spec = protocol["reference"]
        native = local_path(spec["path"])
        if native.exists():
            fp = identity(native / "manifest.json")
            if fp["sha256"] != spec["manifest_sha256"]:
                raise DatasetError("Incorrect frozen R0 manifest")
            old_manifest = json.loads((native / "manifest.json").read_text())
            records[f"{spec['path']}/manifest.json"] = fp
            records[f"{spec['path']}/bundle.json"] = old_manifest["files"]["bundle.json"]
            verify_records(records)
            old = json.loads((native / "bundle.json").read_text())
            if (
                old["protocol_sha256"] != old_manifest["protocol_sha256"]
                or old["experiment_id"] != "EXP031"
            ):
                raise DatasetError("Frozen R0 lineage mismatch")
            reference = pd.DataFrame(old["predictions"])
            reference = reference.loc[
                reference.variant.eq(spec["variant"])
                & reference.family.eq(spec["family"])
                & reference.objective.eq(spec["objective"])
            ].copy()
        execution = execution_identity()
        paths = [
            *Path("src/sat_dengue/experiments").glob("exp_beta01*.py"),
            *Path("src/sat_dengue/pipelines/exp_beta01").glob("*.py"),
            Path("src/sat_dengue/datasets/exp_beta01.py"),
            Path("src/sat_dengue/experiments/onset.py"),
        ]
        execution["code"].update({str(p): identity(p) for p in paths})
        execution["packages"].update(
            {n: importlib.metadata.version(n) for n in ("xgboost", "scikit-learn")}
        )
        verify_records(records)
        return {
            "evidence_type": "authorized_retrospective",
            "protocol": protocol,
            "table": table,
            "columns": columns,
            "reference": reference,
            "provenance": {"sources": records, "execution": execution},
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Beta inputs are read-only")

    def _describe(self) -> dict[str, Any]:
        return {
            "protocol": PROTOCOL_PATH,
            "protocol_sha256": PROTOCOL_SHA256,
            "selection": "explicit canonical bundle identity; optional explicitly pinned frozen R0",
        }


class BetaBundleDataset(CanonicalBundleDataset):
    """Reuse verified atomic no-overwrite publication for the new Beta destination."""
