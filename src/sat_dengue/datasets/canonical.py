"""Verified curated Stage 2 input and immutable canonical table publication."""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.canonical.table import build_table, coverage_report
from sat_dengue.configuration import CANONICAL_AUTHORITY, canonical_bytes, validate_parameters
from sat_dengue.data.consolidation import compute_schema_contract
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.datasets.legacy_preparation.pipeline import read_panel
from sat_dengue.datasets.stage2 import (
    CONSTRUCTION,
    NATIVE_IDENTITIES,
    NATIVE_MANIFEST,
    identity,
    local_path,
    verified_json,
)
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

PANEL = "data/processed/panel_mensual_dengue_clima.csv"


def verify_records(records: dict[str, Any]) -> None:
    for relative, expected in records.items():
        if identity(local_path(relative)) != expected:
            raise DatasetError(f"Canonical input changed: {relative}")


def execution_identity() -> dict[str, Any]:
    paths = [
        *Path("src/sat_dengue/canonical").glob("*.py"),
        *Path("src/sat_dengue/pipelines/canonical").glob("*.py"),
        Path("src/sat_dengue/datasets/canonical.py"),
        Path("src/sat_dengue/configuration.py"),
        Path("src/sat_dengue/config_loader.py"),
        Path("src/sat_dengue/pipeline_registry.py"),
        Path("src/sat_dengue/data/consolidation.py"),
        Path("src/sat_dengue/datasets/stage2.py"),
        Path("src/sat_dengue/datasets/legacy_preparation/pipeline.py"),
        Path("src/sat_dengue/datasets/legacy_preparation/persistence.py"),
        Path("src/sat_dengue/training_preparation/serialization.py"),
        Path("conf/base/catalog.yml"),
        Path("conf/base/parameters.yml"),
        Path("pyproject.toml"),
    ]
    return {
        "git_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "python": sys.version,
        "git_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], text=True)),
        "code": {str(p): identity(local_path(str(p))) for p in sorted(paths)},
        "packages": {
            n: importlib.metadata.version(n) for n in ("pandas", "numpy", "kedro", "kedro-datasets")
        },
    }


class CanonicalSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Read the pinned native publication, without raw sources or model artifacts."""

    def load(self) -> dict[str, Any]:
        for relative in (CANONICAL_AUTHORITY["path"], NATIVE_MANIFEST, CONSTRUCTION, PANEL):
            if not local_path(relative).is_file():
                raise DatasetError(f"Required canonical source is missing: {relative}")
        authority = verified_json(CANONICAL_AUTHORITY["path"], CANONICAL_AUTHORITY["identity"])
        manifest = verified_json(NATIVE_MANIFEST, NATIVE_IDENTITIES[NATIVE_MANIFEST])
        construction = verified_json(CONSTRUCTION, NATIVE_IDENTITIES[CONSTRUCTION])
        approved = compute_schema_contract([], pd.DataFrame(), version="candidate-construction-v1")
        for section in (
            "target_labeling_policy",
            "current_endemic_channel_policy",
            "climate_monthly_aggregation",
        ):
            if construction.get(section) != approved[section]:
                raise DatasetError(f"Incompatible Stage 2 policy: {section}")
        record = manifest["outputs"]["panel_mensual_dengue_clima"]
        if record["path"] != PANEL:
            raise DatasetError("Unexpected curated Stage 2 panel path")
        records = {
            NATIVE_MANIFEST: NATIVE_IDENTITIES[NATIVE_MANIFEST],
            CONSTRUCTION: NATIVE_IDENTITIES[CONSTRUCTION],
            PANEL: {k: record[k] for k in ("sha256", "bytes")},
            CANONICAL_AUTHORITY["path"]: CANONICAL_AUTHORITY["identity"],
        }
        verify_records(records)
        schema = construction["datasets"]["panel_mensual_dengue_clima"]["schema"]
        panel = read_panel(local_path(PANEL), {"schema": schema})
        if panel.shape != (record["rows"], record["columns"]):
            raise DatasetError("Stage 2 panel dimensions differ from manifest")
        verify_records(records)
        return {
            "panel": panel,
            "contract": authority,
            "provenance": {
                "sources": records,
                "execution": execution_identity(),
            },
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Canonical sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {
            "panel": PANEL,
            "manifest": NATIVE_IDENTITIES[NATIVE_MANIFEST],
            "selection": "explicit pinned native source",
        }


def assemble_canonical(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Build one table and its inspectable contract, dictionary and coverage evidence."""
    operational = validate_parameters(parameters)
    if operational != {"profile": "canonical_model_table_v1", "tracking": "disabled"}:
        raise ValueError("Canonical table requires its independent profile and disabled tracking")
    table, schema = build_table(sources["panel"])
    payloads = {
        "canonical_model_table_v1.csv": serialize_table(table),
        "contract.json": canonical_bytes(sources["contract"]),
        "columns.json": canonical_bytes(schema),
        "coverage.json": canonical_bytes(coverage_report(table, schema)),
        "provenance.json": canonical_bytes({**sources["provenance"], "operational": operational}),
    }
    body = {
        "schema": "canonical-model-table-publication-v1",
        "dataset": "canonical_model_table_v1",
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": sources["provenance"]["sources"],
        "real_model_fits": 0,
    }
    manifest = {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    payloads["manifest.json"] = canonical_bytes(manifest)
    return {"payloads": payloads, "provenance": sources["provenance"]}


class CanonicalBundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Publish once and read only this instance's verified publication."""

    def __init__(self, filepath: str) -> None:
        self._root = local_path(filepath)

    def save(self, data: dict[str, Any]) -> None:
        verify_records(data["provenance"]["sources"])
        verify_records(data["provenance"]["execution"]["code"])
        payloads = data["payloads"]
        manifest = json.loads(payloads["manifest.json"])
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if bytes_record(canonical_bytes(body))["sha256"] != manifest["bundle_id"]:
            raise DatasetError("Invalid canonical manifest identity")
        if set(payloads) != {*manifest["files"], "manifest.json"} or any(
            bytes_record(payloads[n]) != record for n, record in manifest["files"].items()
        ):
            raise DatasetError("Canonical payloads disagree with manifest")
        self._published = publish_bundle(
            self._root, manifest["bundle_id"], payloads, existing_policy="error"
        )
        self._expected = identity(self._published / "manifest.json")
        for path in self._published.iterdir():
            path.chmod(0o444)

    def load(self) -> dict[str, Any]:
        if (
            not hasattr(self, "_published")
            or identity(self._published / "manifest.json") != self._expected
        ):
            raise DatasetError("No explicit verified canonical publication")
        manifest = json.loads((self._published / "manifest.json").read_text())
        if {p.name for p in self._published.iterdir()} != {*manifest["files"], "manifest.json"}:
            raise DatasetError("Canonical publication membership changed")
        for name, expected in manifest["files"].items():
            if Path(name).name != name or identity(self._published / name) != expected:
                raise DatasetError("Canonical payload changed")
        return {"path": str(self._published.relative_to(Path.cwd())), "manifest": manifest}

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": str(self._root),
            "publication": "atomic no overwrite; no implicit latest",
        }
