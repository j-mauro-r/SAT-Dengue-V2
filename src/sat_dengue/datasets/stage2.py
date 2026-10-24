"""Read-only Stage 2 sources, streaming CSV and atomic isolated bundle publication."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.data.validation import validate_stage2_configuration
from sat_dengue.datasets import ImmutableConfigurationDataset

SOURCE_IDENTITIES: dict[str, dict[str, Any]] = {
    "data/raw/dengue.csv": {
        "sha256": "58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b",
        "bytes": 875694283,
    },
    "data/raw/dengue_grave.csv": {
        "sha256": "3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70",
        "bytes": 24537734,
    },
    "data/raw/google_earth_engine.csv": {
        "sha256": "dfe20fa02b6d6068c04744b5c86f44112048400a7fde637368c0d4effc88cb3f",
        "bytes": 1714544311,
    },
    "data/sources/Divipola-municipios.md": {
        "sha256": "72eabcea0ff26370d23b9688e8d8f2246946cc815c040ccf1a6966b37a1de9f3",
        "bytes": 209867,
    },
    "data/sources/divipola-provenance.json": {
        "sha256": "92091306f0130910f27de999776b5cf4ed36b7dd7c89bd724d58caeb74f8c158",
        "bytes": 925,
    },
}
NATIVE_MANIFEST = "data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json"
CONSTRUCTION = (
    "data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json"
)
NATIVE_IDENTITIES: dict[str, dict[str, Any]] = {
    "data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json": {
        "bytes": 10686,
        "sha256": "241aa320e2df20d1d4613c50c61d32b60f161a10d76931721131c93a544a213a",
    },
    "data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json": {
        "bytes": 20525,
        "sha256": "aaec877adf9f576cf357e3ca20b783933c3f0f4225ca1482f053c388bc8869de",
    },
}


def identity(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise DatasetError("Required regular source or payload is missing")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size}


def local_path(relative: str) -> Path:
    root = Path.cwd().resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise DatasetError("Dataset path must remain inside repository")
    return path


def verified_json(relative: str, expected: dict[str, Any]) -> Any:
    path = local_path(relative)
    if identity(path) != expected:
        raise DatasetError(f"Incorrect source or manifest: {relative}")
    result = json.loads(path.read_text())
    if identity(path) != expected:
        raise DatasetError("Source changed during reading")
    return result


class PublishedConfigurationDataset(ImmutableConfigurationDataset):
    """Read exactly the snapshot this instance published, never an implicit latest."""

    def save(self, data: dict[str, Any]) -> None:
        super().save(data)
        self._published = self._root / data["execution"]["run_id"] / "resolved.json"
        self._identity = identity(self._published)

    def load(self) -> dict[str, Any]:
        if not hasattr(self, "_published") or identity(self._published) != self._identity:
            raise DatasetError("No verified explicit published configuration")
        return json.loads(self._published.read_text())


class Stage2SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        manifest = verified_json(NATIVE_MANIFEST, NATIVE_IDENTITIES[NATIVE_MANIFEST])
        construction = verified_json(CONSTRUCTION, NATIVE_IDENTITIES[CONSTRUCTION])
        if (
            manifest["input_fingerprints_before"] != SOURCE_IDENTITIES
            or manifest["input_fingerprints_after"] != SOURCE_IDENTITIES
        ):
            raise DatasetError("Incorrect source manifest fingerprints")
        for relative, expected in SOURCE_IDENTITIES.items():
            if identity(local_path(relative)) != expected:
                raise DatasetError(f"Incorrect source identity: {relative}")
        divipola = verified_json(
            "data/sources/Divipola-municipios.md",
            SOURCE_IDENTITIES["data/sources/Divipola-municipios.md"],
        )
        return {
            "construction": construction,
            "native_manifest": manifest,
            "divipola": divipola,
            "provenance": {"inputs": SOURCE_IDENTITIES, "native_documents": NATIVE_IDENTITIES},
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Stage 2 sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"source_identities": SOURCE_IDENTITIES, "native_documents": NATIVE_IDENTITIES}


class Stage2RawCsvDataset(AbstractDataset[Any, Any]):
    def __init__(self, filepaths: list[str], chunksize: int, epidemiology: bool = False) -> None:
        if not filepaths or chunksize <= 0 or any(p not in SOURCE_IDENTITIES for p in filepaths):
            raise ValueError("Invalid Stage 2 source dataset configuration")
        self._paths = filepaths
        self._chunksize = chunksize
        self._epi = epidemiology

    def load(self) -> Iterator[Any]:
        for relative in self._paths:
            path = local_path(relative)
            if identity(path) != SOURCE_IDENTITIES[relative]:
                raise DatasetError("Incorrect source identity")
            for chunk in pd.read_csv(
                path, dtype=str, chunksize=self._chunksize, keep_default_na=False
            ):
                yield (path.name, chunk) if self._epi else chunk
            if identity(path) != SOURCE_IDENTITIES[relative]:
                raise DatasetError("Source changed during streaming")

    def save(self, data: Any) -> None:
        raise DatasetError("Raw sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"filepaths": self._paths, "chunksize": self._chunksize}


def run_folder(storage: Path, resolved: dict[str, Any]) -> Path:
    run_id = resolved["execution"]["run_id"]
    if not isinstance(run_id, str) or re.fullmatch("[0-9a-f]{32}", run_id) is None:
        raise DatasetError("Invalid execution identity")
    folder = storage / run_id
    if not folder.resolve().is_relative_to(storage):
        raise DatasetError("Execution folder escapes storage")
    return folder


class Stage2ConsolidatedDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._storage = local_path(filepath)

    def save(self, data: dict[str, Any]) -> None:
        resolved = data["resolved"]
        validate_stage2_configuration(resolved)
        folder = run_folder(self._storage, resolved)
        folder.mkdir(parents=True, exist_ok=True)
        destination = folder / "consolidated.csv"
        if destination.exists():
            raise DatasetError("Consolidated publication already exists")
        descriptor, temporary = tempfile.mkstemp(dir=folder, prefix=".consolidated-")
        try:
            rows = 0
            with os.fdopen(descriptor, "w") as stream:
                for chunk in data["chunks"]:
                    chunk.to_csv(stream, index=False, header=rows == 0)
                    rows += len(chunk)
                if not rows:
                    raise DatasetError("Cannot publish empty consolidated dataset")
                stream.flush()
                os.fsync(stream.fileno())
                os.fchmod(stream.fileno(), 0o444)
            os.link(temporary, destination)
            self._path = destination
            self._identity = {
                "path": str(destination.relative_to(Path.cwd())),
                **identity(destination),
            }
        finally:
            Path(temporary).unlink(missing_ok=True)

    def load(self) -> dict[str, Any]:
        if not hasattr(self, "_path") or identity(self._path) != {
            k: v for k, v in self._identity.items() if k != "path"
        }:
            raise DatasetError("No verified consolidated publication")
        # Original text, missing strings and codes are preserved. Aggregation consumes text helpers.
        return {
            "chunks": pd.read_csv(self._path, dtype=str, keep_default_na=False, chunksize=200_000),
            "identity": self._identity,
        }

    def _describe(self) -> dict[str, Any]:
        return {"filepath": str(self._storage), "publication": "atomic no-replace streaming CSV"}


class Stage2BundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._storage = local_path(filepath)

    def save(self, data: dict[str, Any]) -> None:
        resolved = data["resolved"]
        folder = run_folder(self._storage, resolved)
        destination = folder / "bundle"
        if destination.exists():
            raise DatasetError("Stage 2 bundle already exists")
        validate_stage2_configuration(resolved)
        provenance = resolved["stage2"]["provenance"]
        for relative, expected in {
            **provenance["inputs"],
            **provenance["native_documents"],
        }.items():
            if identity(local_path(relative)) != expected:
                raise DatasetError("Source or native manifest changed before publication")
        consolidated = data["consolidated_identity"]
        if identity(local_path(consolidated["path"])) != {
            k: v for k, v in consolidated.items() if k != "path"
        }:
            raise DatasetError("Consolidated identity changed before publication")
        folder.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(dir=folder, prefix=".bundle-"))
        try:
            for name, frame in data["tables"].items():
                if Path(name).name != name:
                    raise DatasetError("Invalid bundle payload name")
                frame.to_csv(temporary / name, index=False)
            for name, document in data["documents"].items():
                if Path(name).name != name:
                    raise DatasetError("Invalid bundle payload name")
                (temporary / name).write_bytes(canonical_bytes(document))
            payloads = {p.name: identity(p) for p in sorted(temporary.iterdir())}
            body = {
                "schema": "sat-dengue-stage2-engineering-v1",
                "run_id": resolved["execution"]["run_id"],
                "configuration_sha256": resolved["configuration_sha256"],
                "provenance": resolved["stage2"]["provenance"],
                "consolidated": data["consolidated_identity"],
                "files": payloads,
                "real_fits": 0,
            }
            manifest = {**body, "bundle_id": hashlib.sha256(canonical_bytes(body)).hexdigest()}
            (temporary / "manifest.json").write_bytes(canonical_bytes(manifest))
            for p in temporary.iterdir():
                with p.open("rb") as stream:
                    os.fsync(stream.fileno())
                p.chmod(0o444)
            # An exclusive sibling lock closes the cooperating-writer collision window.
            lock = folder / ".publish.lock"
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                if destination.exists():
                    raise DatasetError("Stage 2 bundle already exists")
                temporary.rename(destination)
            finally:
                os.close(fd)
                lock.unlink()
            self._published = destination
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)

    def load(self) -> dict[str, Any]:
        if not hasattr(self, "_published"):
            raise DatasetError("No explicit Stage 2 bundle selected")
        manifest = json.loads((self._published / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if hashlib.sha256(canonical_bytes(body)).hexdigest() != manifest["bundle_id"]:
            raise DatasetError("Bundle identity mismatch")
        if {p.name for p in self._published.iterdir()} != {*manifest["files"], "manifest.json"}:
            raise DatasetError("Unexpected bundle membership")
        for name, expected in manifest["files"].items():
            if identity(self._published / name) != expected:
                raise DatasetError("Bundle payload fingerprint mismatch")
        consolidated = manifest["consolidated"]
        if identity(local_path(consolidated["path"])) != {
            k: v for k, v in consolidated.items() if k != "path"
        }:
            raise DatasetError("Consolidated identity mismatch")
        return manifest

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": str(self._storage),
            "publication": "atomic immutable engineering bundle",
        }


def run_compatibility(root: Path, config: Any) -> Any:
    """Keep the old CLI/result shape while executing exactly the new Kedro graph."""
    from copy import deepcopy

    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.datasets.legacy_consolidation import PipelineResult
    from sat_dengue.pipelines.data.pipeline import create_pipeline

    if root.resolve() != Path.cwd().resolve():
        raise ValueError("Run the Stage 2 compatibility entrypoint from the repository root")
    if config.contract_version != "candidate-construction-v1":
        raise ValueError("Unapproved scientific construction contract")
    if config.chunksize_epi <= 0 or config.chunksize_climate <= 0:
        raise ValueError("Chunksizes must be positive")
    loader = ValidatedConfigLoader(
        str(root / "conf"),
        base_env="base",
        default_run_env="base",
        runtime_params={"profile": "data"},
    )
    configuration = deepcopy(loader["catalog"])
    configuration["stage2_epi_raw"]["chunksize"] = config.chunksize_epi
    configuration["stage2_climate_raw"]["chunksize"] = config.chunksize_climate
    # Optional chunk sizes affect I/O only and are preserved in the engineering snapshot.
    with tempfile.TemporaryDirectory(dir=root / "tmp", prefix="stage2-dry-run-") as directory:
        if not config.perform_safe_write:
            for key in ("stage2_consolidated", "stage2_bundle"):
                configuration[key]["filepath"] = directory
        catalog = DataCatalog.from_config(configuration)
        inputs = catalog["configuration_inputs"].load()
        inputs["execution"]["compatibility_io"] = {
            "chunksize_epi": config.chunksize_epi,
            "chunksize_climate": config.chunksize_climate,
            "reuse_existing_outputs": config.reuse_existing_outputs,
            "dry_run": not config.perform_safe_write,
        }
        catalog["configuration_inputs"] = MemoryDataset(inputs)
        catalog["parameters"] = MemoryDataset(loader["parameters"])
        SequentialRunner().run(create_pipeline(), catalog)
        manifest = catalog["stage2_bundle"].load()
        consolidated = root / manifest["consolidated"]["path"]
        folder = consolidated.parent / "bundle"
        summary = json.loads((folder / "summary.json").read_text())
        construction = json.loads((folder / "construction.json").read_text())
        panel = pd.read_csv(folder / "panel.csv", nrows=0)
        return PipelineResult(
            consolidated_path=consolidated,
            panel_path=folder / "panel.csv",
            consolidated_rows=summary["consolidated_rows"],
            panel_rows=sum(1 for _ in (folder / "panel.csv").open()) - 1,
            consolidated_columns=len(construction["datasets"]["dengue_y_dengue_grave"]["schema"]),
            panel_columns=len(panel.columns),
            manifest_path=folder / "manifest.json",
            contract_path=folder / "construction.json",
            y_traceability_path=folder / "y_history.csv",
        )
