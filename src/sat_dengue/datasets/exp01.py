"""EXP01 metadata-only inputs and atomic result publication; no implicit private load."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.development import resolve_root
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp01_preflight import OUTPUT_ROOT, safe_path, source_metadata
from sat_dengue.training_preparation.serialization import bytes_record


def _publication_root(filepath: str) -> Path:
    """Accept the fixed catalog path or Kedro's canonical absolute equivalent."""
    root = resolve_root()
    path = Path(filepath)
    if (
        Path.cwd().resolve() != root
        or ".." in path.parts
        or any(part.is_symlink() for part in (path, *path.parents))
        or (not path.is_absolute() and filepath != OUTPUT_ROOT)
        or path.resolve() != root / OUTPUT_ROOT
    ):
        raise ValueError("EXP01 publication path must match the fixed catalog")
    # Preserve the relative internal representation used by global safe_path.
    return safe_path(OUTPUT_ROOT, temporary=True)


class Exp01SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """The source descriptor connects pinned existing inputs without opening contents."""

    def load(self) -> dict[str, Any]:
        return source_metadata()

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("EXP01 sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"mode": "metadata_only_until_explicit_authorization"}


class Exp01BundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._root = _publication_root(filepath)

    def save(self, data: dict[str, Any]) -> None:
        tracker = data["tracker"]
        try:
            from sat_dengue.tracking.exp01 import validate_result

            validate_result(data["result"], data["provenance"])
            safe_path(str(self._root), temporary=True)
            payloads = {
                name + ".json": canonical_bytes(data[name]) for name in ("result", "provenance")
            }
            body = {
                "schema": "exp01-result-manifest-v1",
                "files": {name: bytes_record(value) for name, value in payloads.items()},
            }
            manifest: dict[str, Any] = {**body, "bundle_id": digest(body)}
            payloads["manifest.json"] = canonical_bytes(manifest)
            folder = publish_bundle(
                self._root, manifest["bundle_id"], payloads, existing_policy="error"
            )
            self._publication = {"path": str(folder), "manifest": manifest}
            from sat_dengue.tracking.exp01 import verified_result

            verified_result(self._publication)
            tracker.finish_paired(self._publication)
        except BaseException:
            tracker.fail()
            raise

    def load(self) -> dict[str, Any]:
        from sat_dengue.tracking.exp01 import verified_result

        if not hasattr(self, "_publication"):
            raise DatasetError("No explicit EXP01 publication")
        verified_result(self._publication)
        return dict(self._publication)

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._root), "publication": "atomic_no_overwrite"}
