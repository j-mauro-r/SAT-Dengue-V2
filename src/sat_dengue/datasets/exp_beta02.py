"""Explicit count-experiment authority and reuse of verified immutable readers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.canonical import CanonicalBundleDataset, verify_records
from sat_dengue.datasets.exp_beta01 import BetaSourcesDataset
from sat_dengue.datasets.stage2 import identity, local_path, verified_json

PROTOCOL_PATH = "docs/product/experiments/EXP-BETA02/protocol.json"
PROTOCOL_SHA256 = "6a7697f0011680e59b697422b35a3f928fbe5a8a9dc6e74431548ad2581baef1"


class CountSourcesDataset(BetaSourcesDataset):
    """Reuse the canonical/R0 loader, never a previous estimator or fitted pipeline."""

    def load(self) -> dict[str, Any]:
        fp = identity(local_path(PROTOCOL_PATH))
        if fp["sha256"] != PROTOCOL_SHA256:
            raise DatasetError("Unapproved Beta02 protocol identity")
        protocol = verified_json(PROTOCOL_PATH, fp)
        source = super().load()
        for field in ("canonical_bundle_id", "canonical_manifest_sha256"):
            if protocol[field] != source["protocol"][field]:
                raise DatasetError("Beta02 canonical binding mismatch")
        provenance = source["provenance"]
        records = provenance["sources"]
        records[PROTOCOL_PATH] = fp
        secondary = None
        spec = protocol["secondary_beta01"]
        folder = local_path(spec["path"])
        if folder.exists():
            manifest_fp = identity(folder / "manifest.json")
            if manifest_fp["sha256"] != spec["manifest_sha256"]:
                raise DatasetError("Incorrect secondary Beta01 manifest")
            manifest = json.loads((folder / "manifest.json").read_text())
            body = {k: v for k, v in manifest.items() if k != "bundle_id"}
            if (
                manifest["experiment_id"] != "EXP-BETA01"
                or manifest["canonical_bundle_id"] != protocol["canonical_bundle_id"]
                or manifest["bundle_id"] != folder.name
                or hashlib.sha256(canonical_bytes(body)).hexdigest() != folder.name
                or {p.name for p in folder.iterdir()} != {*manifest["files"], "manifest.json"}
                or any(Path(name).name != name for name in manifest["files"])
            ):
                raise DatasetError("Invalid secondary Beta01 publication")
            verify_records(manifest["sources"])
            records[f"{spec['path']}/manifest.json"] = manifest_fp
            records.update({f"{spec['path']}/{n}": v for n, v in manifest["files"].items()})
            verify_records(records)
            secondary = pd.read_csv(
                folder / "predictions.csv",
                dtype={
                    "municipality_code": "string",
                    "department_code": "string",
                    "year_month": "string",
                    "target_month": "string",
                },
            )
        execution = provenance["execution"]
        paths = [
            *Path("src/sat_dengue/experiments").glob("exp_beta02*.py"),
            *Path("src/sat_dengue/pipelines/exp_beta02").glob("*.py"),
            Path("src/sat_dengue/datasets/exp_beta02.py"),
        ]
        execution["code"].update({str(p): identity(p) for p in paths})
        execution["packages"].update(
            {name: importlib.metadata.version(name) for name in ("scipy", "threadpoolctl")}
        )
        verify_records(records)
        return {**source, "protocol": protocol, "secondary": secondary}

    def _describe(self) -> dict[str, Any]:
        return {
            "protocol": PROTOCOL_PATH,
            "sha256": PROTOCOL_SHA256,
            "publication": "explicit canonical/R0 identities; optional pinned Beta01 context",
        }


class CountBundleDataset(CanonicalBundleDataset):
    """Existing atomic no-overwrite publisher under a separate count destination."""
