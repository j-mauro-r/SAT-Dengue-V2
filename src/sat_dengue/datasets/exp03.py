"""Protected native EXP03 evidence, atomically published without overwriting."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.experiments.exp03_preflight import OUTPUT_ROOT, descriptor, safe_path


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
        from sat_dengue.experiments.exp03 import load_protocol
        from sat_dengue.experiments.exp03_reporting import validate_bundle, write_bundle
        from sat_dengue.tracking.exp03 import validate_result, verified_result

        tracker = data["tracker"]
        try:
            safe_path(str(self._root), OUTPUT_ROOT)
            validate_result(data["result"], data["provenance"])
            self._root.mkdir(parents=True, exist_ok=True, mode=0o700)
            lock = self._root / ".publish.lock"
            try:
                lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError as exc:
                raise ValueError("Another EXP03 publisher holds the output lock") from exc
            try:
                os.close(lock_fd)
                staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=self._root))
                try:
                    artifacts = data.get("model_artifacts_path")
                    if artifacts is not None:
                        source = safe_path(str(artifacts))
                        if not source.is_relative_to(Path.cwd().resolve() / "tmp"):
                            raise ValueError("Model artifacts must be protected repository tmp")
                        if any(p.is_symlink() for p in source.rglob("*")):
                            raise ValueError("Symlink model artifact")
                        shutil.copytree(source, staging / "model_artifacts")
                    manifest = write_bundle(
                        staging, data["result"], data["provenance"], load_protocol()["design"]
                    )
                    validate_bundle(staging)
                    destination = self._root / manifest["bundle_id"]
                    if destination.exists():
                        raise ValueError("EXP03 output already exists; replacement is forbidden")
                    # All nested evidence is closed by the manifest before visibility.
                    for path in staging.rglob("*"):
                        if path.is_file():
                            path.chmod(0o600)
                            with path.open("rb") as stream:
                                os.fsync(stream.fileno())
                        elif path.is_dir():
                            path.chmod(0o700)
                    os.rename(staging, destination)
                    self._publication = {"path": str(destination), "manifest": manifest}
                finally:
                    if staging.exists():
                        shutil.rmtree(staging)
            finally:
                lock.unlink()
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
