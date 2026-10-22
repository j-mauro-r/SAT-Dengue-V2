"""Read approved JSON authorities and publish atomic immutable run configuration."""

from __future__ import annotations

import hashlib
import importlib.metadata
import os
import re
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from kedro.io import AbstractDataset, DatasetError
from kedro_datasets.json import JSONDataset  # type: ignore[import-untyped]

from sat_dengue.configuration import AUTHORITIES, canonical_bytes


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ConfigurationInputsDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Load fixed read-only authorities and non-private execution provenance."""

    def load(self) -> dict[str, Any]:
        root = Path.cwd().resolve()
        authorities = {}
        for name, identity in AUTHORITIES.items():
            path = root / identity["path"]
            if path.is_symlink() or not path.resolve().is_relative_to(root):
                raise DatasetError("Scientific authority must be a repository-local regular file")
            if _sha256(path) != identity["sha256"]:
                raise DatasetError(f"Scientific authority changed: {identity['path']}")
            document = JSONDataset(filepath=str(path)).load()
            if _sha256(path) != identity["sha256"]:
                raise DatasetError("Scientific authority changed while loading")
            authorities[name] = {**identity, "document": document}
        paths = sorted(
            [
                *root.joinpath("src/sat_dengue").rglob("*.py"),
                *root.joinpath("conf/base").rglob("*.yml"),
                root / "pyproject.toml",
                root / "docs/operations/kedro-foundation-constraints.txt",
            ]
        )
        code = {str(path.relative_to(root)): _sha256(path) for path in paths}
        loaded_code = {
            str(path.relative_to(Path(__file__).resolve().parents[1])): _sha256(path)
            for path in sorted(Path(__file__).resolve().parents[1].rglob("*.py"))
        }
        packages: dict[str, str | None] = {}
        for name in ("sat-dengue-v2", "kedro", "kedro-datasets", "mlflow", "lightgbm"):
            try:
                packages[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                packages[name] = None
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True))
        return {
            "authorities": authorities,
            "execution": {
                "run_id": uuid4().hex,
                "created_at": datetime.now(UTC).isoformat(),
                "git_revision": revision,
                "git_dirty": dirty,
                "code": code,
                "packages": packages,
                "python": sys.version,
                "loaded_package_code": loaded_code,
                "environment": dict(
                    sorted(
                        (distribution.metadata["Name"], distribution.version)
                        for distribution in importlib.metadata.distributions()
                    )
                ),
            },
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Scientific authorities are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"authorities": [entry["path"] for entry in AUTHORITIES.values()]}


class ImmutableConfigurationDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Publish a content-verified snapshot once, with a unique execution identity."""

    def __init__(self, filepath: str) -> None:
        self._root = Path(filepath).resolve()
        if not self._root.resolve().is_relative_to(Path.cwd().resolve()):
            raise ValueError("Snapshot storage must remain inside the repository")

    def save(self, data: dict[str, Any]) -> None:
        body = {key: value for key, value in data.items() if key != "configuration_sha256"}
        if hashlib.sha256(canonical_bytes(body)).hexdigest() != data.get("configuration_sha256"):
            raise DatasetError("Resolved configuration fingerprint mismatch")
        run_id = data["execution"]["run_id"]
        if not isinstance(run_id, str) or re.fullmatch(r"[0-9a-f]{32}", run_id) is None:
            raise DatasetError("Invalid execution identity")
        folder = self._root / run_id
        folder.mkdir(parents=True, exist_ok=True)
        if not folder.resolve().is_relative_to(self._root):
            raise DatasetError("Snapshot path escapes storage")
        destination = folder / "resolved.json"
        payload = canonical_bytes(data)
        if destination.exists():
            if destination.is_symlink() or destination.read_bytes() != payload:
                raise DatasetError("Immutable configuration already exists with different bytes")
            return
        descriptor, temporary = tempfile.mkstemp(dir=folder, prefix=".resolved-")
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
                os.fchmod(stream.fileno(), 0o444)
            # Atomic create without replacing any existing execution evidence.
            os.link(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def load(self) -> dict[str, Any]:
        raise DatasetError("Select an explicit run snapshot for reading; no implicit latest")

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._root), "versioning": "run identity and content SHA-256"}
