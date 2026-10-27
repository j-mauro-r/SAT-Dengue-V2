"""Explicit EXP03 descriptor and canonical atomic output, accepting Kedro paths."""

from __future__ import annotations

from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_preflight import OUTPUT_ROOT, descriptor, safe_path
from sat_dengue.training_preparation.serialization import bytes_record


class Exp03SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        return descriptor()

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("EXP03 source descriptor is read-only")

    def _describe(self) -> dict[str, Any]:
        return {"mode": "descriptor_only_no_private_reads"}


class Exp03BundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._root = safe_path(filepath, OUTPUT_ROOT)

    def save(self, data: dict[str, Any]) -> None:
        from sat_dengue.tracking.exp03 import validate_result, verified_result

        tracker = data["tracker"]
        try:
            safe_path(str(self._root), OUTPUT_ROOT)
            validate_result(data["result"], data["provenance"])
            payloads = {k + ".json": canonical_bytes(data[k]) for k in ("result", "provenance")}
            body = {
                "schema": "exp03-result-manifest-v1",
                "files": {k: bytes_record(v) for k, v in payloads.items()},
            }
            manifest: dict[str, Any] = {**body, "bundle_id": digest(body)}
            payloads["manifest.json"] = canonical_bytes(manifest)
            folder = publish_bundle(
                self._root, manifest["bundle_id"], payloads, existing_policy="error"
            )
            self._publication = {"path": str(folder), "manifest": manifest}
            verified_result(self._publication)
            tracker.finish_ablation(self._publication)
        except BaseException:
            tracker.fail()
            raise

    def load(self) -> dict[str, Any]:
        from sat_dengue.tracking.exp03 import verified_result

        if not hasattr(self, "_publication"):
            raise DatasetError("No EXP03 publication")
        verified_result(self._publication)
        return dict(self._publication)

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._root), "mode": "atomic_no_overwrite"}
