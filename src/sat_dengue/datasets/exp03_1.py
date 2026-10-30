"""EXP03.1 descriptor-only inputs and atomic real-result publication."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.experiments.exp03_1_preflight import (
    OUTPUT_ROOT,
    source_descriptor,
)


class Exp03_1SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        return source_descriptor()

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("EXP03.1 source descriptor is read-only")

    def _describe(self) -> dict[str, Any]:
        return {"mode": "descriptor_only_no_private_reads"}


class Exp03_1BundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        path = Path(filepath)
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.as_posix() != OUTPUT_ROOT
            or any(parent.is_symlink() for parent in (path, *path.parents))
        ):
            raise ValueError("EXP03.1 bundle output must be a protected repository tmp path")
        self._root = path
        self._publication: dict[str, Any] | None = None

    def save(self, data: dict[str, Any]) -> None:
        from sat_dengue.experiments.exp03_1_reporting import (
            read_real_bundle,
            validate_real_mlflow,
            write_real_bundle,
        )

        tracker = data["tracker"]
        result = data["result"]
        try:
            receipt = tracker.start_children(
                result["cells"], result["protocol_sha256"]
            )
            execution_id = Path(data["reservation"]).name.removesuffix(".reservation")
            destination = self._root / execution_id
            publication = write_real_bundle(
                result,
                data["provenance"],
                receipt,
                destination,
            )
            read_real_bundle(
                destination,
                publication["manifest"]["bundle_id"],
            )
            tracker.finish(
                receipt,
                result["cells"],
                publication["manifest"],
            )
            validate_real_mlflow(
                publication["bundle"],
                data["provenance"]["tracking_root"],
                publication["manifest"]["bundle_id"],
            )
            tracker.mark_verified(receipt)
            self._publication = {
                "path": str(destination),
                "manifest": publication["manifest"],
            }
            print(
                json.dumps(
                    {
                        "status": "verified",
                        "bundle_path": str(destination),
                        "bundle_id": publication["manifest"]["bundle_id"],
                    },
                    sort_keys=True,
                )
            )
        except BaseException:
            tracker.fail()
            raise

    def load(self) -> dict[str, Any]:
        from sat_dengue.experiments.exp03_1_reporting import read_real_bundle

        if self._publication is None:
            raise DatasetError("No complete EXP03.1 real publication")
        return read_real_bundle(
            Path(self._publication["path"]),
            self._publication["manifest"]["bundle_id"],
        )

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._root), "mode": "atomic_no_overwrite_real_only"}
