"""Catalog adapters for verified native model inputs and immutable engineering outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.datasets.stage2 import identity, local_path
from sat_dengue.datasets.training_legacy import (
    BUNDLES,
    LegacyTrainingLoader,
    checked_bundle,
    no_fitting,
)
from sat_dengue.model_training.workflow import training_contract
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes, serialize_table


class TrainingSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        if not hasattr(self, "_cached"):
            self._cached = LegacyTrainingLoader().load()
        return self._cached

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Native training sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"explicit_native_manifests": BUNDLES, "mode": "replay only"}


def assemble_training_payloads(result: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    training_contract(resolved, result["mode"])
    payloads = {n: serialize_table(frame) for n, frame in result["tables"].items()}
    payloads.update(result["payloads"])
    audit = {k: v for k, v in result.items() if k not in {"tables", "payloads"}}
    audit.update(
        G5="NOT_APPROVED", champion="not_selected", consumed_2025_cannot_fit_tune_select=True
    )
    payloads["audit.json"] = json_bytes(audit)
    payloads["provenance.json"] = json_bytes(resolved)
    return {"payloads": payloads, "resolved": resolved, "mode": result["mode"]}


class TrainingBundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._storage = local_path(filepath)

    def save(self, data: dict[str, Any]) -> None:
        resolved = data["resolved"]
        mode = data["mode"]
        training_contract(resolved, mode)
        if mode == "replay":
            with no_fitting():
                for relative in BUNDLES:
                    checked_bundle(relative)
                for name, expected in resolved["training"]["source_provenance"][
                    "stage2_inputs"
                ].items():
                    if identity(local_path(name)) != expected:
                        raise DatasetError("Replay source identity changed before publication")
        payloads = dict(data["payloads"])
        body = {
            "schema": "sat-dengue-training-engineering-v1",
            "mode": mode,
            "configuration_sha256": resolved["configuration_sha256"],
            "files": {n: bytes_record(raw) for n, raw in payloads.items()},
            "real_model_fits": 0,
            "real_preparer_refits": 0,
        }
        bundle_id = bytes_record(canonical_bytes(body))["sha256"]
        payloads["manifest.json"] = json_bytes({**body, "bundle_id": bundle_id})
        self._published = publish_bundle(
            self._storage, bundle_id, payloads, existing_policy="error"
        )
        self._expected = identity(self._published / "manifest.json")
        for path in self._published.iterdir():
            path.chmod(0o444)

    def load(self) -> dict[str, Any]:
        if (
            not hasattr(self, "_published")
            or identity(self._published / "manifest.json") != self._expected
        ):
            raise DatasetError("No explicit verified training publication")
        manifest = json.loads((self._published / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if bytes_record(canonical_bytes(body))["sha256"] != manifest["bundle_id"] or {
            p.name for p in self._published.iterdir()
        } != {*manifest["files"], "manifest.json"}:
            raise DatasetError("Training publication identity/membership changed")
        for name, expected in manifest["files"].items():
            if Path(name).name != name or identity(self._published / name) != expected:
                raise DatasetError("Training publication payload changed")
        return {"path": str(self._published.relative_to(Path.cwd())), "manifest": manifest}

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": str(self._storage),
            "publication": "atomic immutable; no implicit latest",
        }
