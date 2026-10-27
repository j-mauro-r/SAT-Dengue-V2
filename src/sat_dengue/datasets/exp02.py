"""EXP02 metadata-only catalog input and atomic immutable native publication."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.development import resolve_root
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp02_preflight import OUTPUT_ROOT, safe_path, source_metadata
from sat_dengue.training_preparation.serialization import bytes_record


def publication_root(filepath: str) -> Path:
    root, path = resolve_root(), Path(filepath)
    if (
        Path.cwd().resolve() != root
        or ".." in path.parts
        or any(p.is_symlink() for p in (path, *path.parents))
        or (not path.is_absolute() and filepath != OUTPUT_ROOT)
        or path.resolve() != root / OUTPUT_ROOT
    ):
        raise ValueError("EXP02 publication must match its fixed catalog path")
    return safe_path(OUTPUT_ROOT, temporary=True)


def publish_native(data: dict[str, Any], root: str) -> dict[str, Any]:
    from sat_dengue.experiments.exp02_runner import guard
    from sat_dengue.tracking.exp02 import validate_result, verified_result

    synthetic = data["result"]["evidence_type"] == "synthetic_interface_probe"
    if synthetic:
        from sat_dengue.tracking.exp02 import require_isolated_generated_root

        require_isolated_generated_root(root)
    else:
        guard(data["context"], contents=True)
        if root != data["context"]["preflight"]["output_root"]:
            raise ValueError("EXP02 publication root changed")
    base = safe_path(root, temporary=True)
    if any(p.is_symlink() for p in base.rglob("*")):
        raise ValueError("EXP02 publication contains symlinks")
    validate_result(data["result"], data["provenance"])
    payloads = {name + ".json": canonical_bytes(data[name]) for name in ("result", "provenance")}
    body = {
        "schema": "exp02-result-manifest-v1",
        "files": {name: bytes_record(value) for name, value in payloads.items()},
    }
    manifest = {**body, "bundle_id": digest(body)}
    payloads["manifest.json"] = canonical_bytes(manifest)
    folder = publish_bundle(base, str(manifest["bundle_id"]), payloads, existing_policy="error")
    publication = {"path": str(folder), "manifest": manifest}
    verified_result(publication)
    return publication


class Exp02SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        return source_metadata()

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("EXP02 sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"mode": "metadata_only_until_explicit_authorization"}


class Exp02BundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._root = publication_root(filepath)

    def save(self, data: dict[str, Any]) -> None:
        from sat_dengue.experiments.exp02_runner import guard
        from sat_dengue.tracking.exp02 import export_authorized

        guard(data["context"], contents=True)
        self._publication = publish_native(data, str(self._root))
        guard(data["context"], contents=True)
        export_authorized(self._publication, data["context"]["preflight"])

    def load(self) -> dict[str, Any]:
        from sat_dengue.tracking.exp02 import verified_result

        if not hasattr(self, "_publication"):
            raise DatasetError("No explicit EXP02 publication")
        verified_result(self._publication)
        return dict(self._publication)

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._root), "publication": "atomic_no_overwrite"}
