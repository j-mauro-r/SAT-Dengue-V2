"""Explicit Stage 2/native-preparer inputs and immutable preparation publication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.datasets.legacy_preparation.pipeline import prepare_inputs
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, identity, local_path, verified_json
from sat_dengue.training_preparation.eligibility import policy_from_years
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes, serialize_table
from sat_dengue.training_preparation.workflow import preparation_contract

DEVELOPMENT = (
    "data/processed/training_preparation/development/"
    "2ab12a21172a1cc49ff4fe713c1ff5199f1c7569354c300ed7cb2579ff0ffe24"
)
TEMPORAL = (
    "data/processed/training_preparation/temporal/"
    "a41c1252e81090eec60db2b0bc0089aeee5c96bc645ea9766225eb45e7bc1d97"
)

# Explicit baseline identities; no directory scanning or implicit latest selection.
NATIVE_PREPARATION: dict[str, dict[str, Any]] = {
    DEVELOPMENT: {
        "bytes": 31773,
        "sha256": "08aa8682cc4d9a19f9a846c2a7d8e3d92e5a7f4815eced472ae625f04235b2a7",
    },
    TEMPORAL: {
        "bytes": 92553,
        "sha256": "d2116ebec299acc24017dc76e8f16a74496538a368404520ee89cd6de6799927",
    },
}


def verified_native_bundle(relative: str, expected: dict[str, Any]) -> dict[str, Any]:
    manifest = verified_json(relative + "/manifest.json", expected)
    folder = local_path(relative)
    if folder.is_symlink() or {p.name for p in folder.iterdir()} != {
        *manifest["files"],
        "manifest.json",
    }:
        raise DatasetError("Native preparation bundle membership changed")
    if manifest["bundle_id"] != folder.name:
        raise DatasetError("Native preparation bundle identity changed")
    for name, record in manifest["files"].items():
        if Path(name).name != name or identity(folder / name) != record:
            raise DatasetError("Native preparation payload identity changed")
    return manifest


class PreparationSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Read the explicitly identified Stage 2 products, with original typed parsing."""

    def load(self) -> dict[str, Any]:
        from sat_dengue.datasets.legacy_readiness import read_notification_year_metadata
        from sat_dengue.datasets.stage2 import NATIVE_MANIFEST

        verified_json(NATIVE_MANIFEST, NATIVE_IDENTITIES[NATIVE_MANIFEST])
        config = PreparationConfig(Path.cwd())
        prepared = prepare_inputs(config, reference_end="2024-12")
        years = read_notification_year_metadata(
            config.resolve("data/processed/dengue_y_dengue_grave.csv")
        )
        policy = policy_from_years(int(years["min_year"]), int(years["max_year"]), "2025-01")
        return {
            "panel": prepared.panel.sort_values(["municipality_code", "year_month"]).reset_index(
                drop=True
            ),
            "contract": prepared.contract,
            "policy": policy,
            "report": prepared.report,
            "provenance": prepared.report["input_fingerprints"],
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Preparation inputs are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"stage2": NATIVE_IDENTITIES, "reference_end": "2024-12"}


class SavedPreparersDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Load every verified JSON state; never invoke a fitter."""

    def load(self) -> dict[str, Any]:
        development = verified_native_bundle(DEVELOPMENT, NATIVE_PREPARATION[DEVELOPMENT])
        temporal = verified_native_bundle(TEMPORAL, NATIVE_PREPARATION[TEMPORAL])
        if (
            temporal["identity"]["development_manifest"] != NATIVE_PREPARATION[DEVELOPMENT]
            or temporal["identity"]["development_bundle"] != development["bundle_id"]
        ):
            raise DatasetError("Native development identity changed")
        states = {}
        for window, entry in temporal["windows"].items():
            states[window] = {
                profile: verified_json(
                    TEMPORAL + "/" + item["state"], temporal["files"][item["state"]]
                )
                for profile, item in entry["profiles"].items()
            }
        return {
            "states": states,
            "provenance": {
                "development": {"path": DEVELOPMENT, **NATIVE_PREPARATION[DEVELOPMENT]},
                "temporal": {"path": TEMPORAL, **NATIVE_PREPARATION[TEMPORAL]},
                "state_files": {
                    item["state"]: temporal["files"][item["state"]]
                    for entry in temporal["windows"].values()
                    for item in entry["profiles"].values()
                },
            },
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Saved preparers are read-only; refit forbidden")

    def _describe(self) -> dict[str, Any]:
        return {"native_bundles": NATIVE_PREPARATION, "mode": "saved-state replay only"}


def bundle_payloads(
    keys: Any,
    features: Any,
    controls: Any,
    audit: dict[str, Any],
    windows: dict[str, Any],
    resolved: dict[str, Any],
    producer: dict[str, str],
    consumer: dict[str, dict[str, str]],
) -> dict[str, Any]:
    contract = preparation_contract(resolved)
    payloads = {
        "keys.csv": serialize_table(keys),
        "features.csv": serialize_table(features),
        "controls.csv": serialize_table(controls),
    }
    for window, entry in windows.items():
        for split, tables in entry["splits"].items():
            for role, frame in tables.items():
                suffix = {"Y": "y", "keys": "index"}.get(role, role)
                payloads[f"{window}_{split}_{suffix}.csv"] = serialize_table(frame)
        for profile, item in entry["profiles"].items():
            payloads[f"{window}_{profile}_preparer.json"] = json_bytes(item["state"])
            for split, matrix in item["matrices"].items():
                payloads[f"{window}_{profile}_{split}_matrix.csv"] = serialize_table(matrix)
    schema = {
        "features": list(features),
        "keys": list(keys),
        "controls": list(controls),
        "raw_X": ["municipality_code", *list(features)],
        "dtypes": {n: str(d) for n, d in features.dtypes.items()},
        "profiles": contract["temporal_preparation"]["profiles"],
    }
    provenance = {
        "resolved_configuration": resolved,
        "producer_cutoffs": producer,
        "consumer_cutoffs": consumer,
        "eligibility": audit,
        "windows": {w: e["audit"] for w, e in windows.items()},
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "G2_G3": "ACCEPTED_WITH_DOCUMENTED_LIMITS (DEC-135)",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads["schema.json"] = json_bytes(schema)
    payloads["provenance.json"] = json_bytes(provenance)
    return {"payloads": payloads, "resolved": resolved}


class PreparationBundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._storage = local_path(filepath)

    def save(self, data: dict[str, Any]) -> None:
        resolved = data["resolved"]
        preparation_contract(resolved)
        for name, record in resolved["preparation"]["stage2"].items():
            if identity(local_path(name)) != record:
                raise DatasetError("Stage 2 input changed before preparation publication")
        for relative, expected in NATIVE_PREPARATION.items():
            verified_native_bundle(relative, expected)
        payloads = dict(data["payloads"])
        body = {
            "schema": "sat-dengue-preparation-engineering-v1",
            "configuration_sha256": resolved["configuration_sha256"],
            "files": {n: bytes_record(b) for n, b in payloads.items()},
            "originals": resolved["preparation"],
            "real_model_fits": 0,
            "real_preparer_refits": 0,
        }
        bundle_id = bytes_record(canonical_bytes(body))["sha256"]
        manifest = {**body, "bundle_id": bundle_id}
        payloads["manifest.json"] = json_bytes(manifest)
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
            raise DatasetError("No explicit verified preparation publication")
        manifest = json.loads((self._published / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if bytes_record(canonical_bytes(body))["sha256"] != manifest["bundle_id"]:
            raise DatasetError("Preparation engineering identity changed")
        if {p.name for p in self._published.iterdir()} != {*manifest["files"], "manifest.json"}:
            raise DatasetError("Preparation membership changed")
        for name, expected in manifest["files"].items():
            if Path(name).name != name or identity(self._published / name) != expected:
                raise DatasetError("Preparation payload identity changed")
        return {"path": str(self._published.relative_to(Path.cwd())), "manifest": manifest}

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": str(self._storage),
            "publication": "atomic immutable, explicit identity",
        }


def compatibility_main() -> None:
    """Retained CLI runs the replay-only graph, with no implicit historical refresh."""
    import argparse

    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipelines.preparation.pipeline import create_pipeline

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    if args.root.resolve() != Path.cwd().resolve():
        raise ValueError("Run from repository root")
    if args.baseline:
        from sat_dengue.datasets.legacy_preparation.development import check_preservation

        check_preservation(PreparationConfig(Path.cwd()), args.baseline)
    loader = ValidatedConfigLoader(
        "conf", base_env="base", default_run_env="base", runtime_params={"profile": "preparation"}
    )
    catalog = DataCatalog.from_config(loader["catalog"])
    catalog["parameters"] = MemoryDataset(loader["parameters"])
    # --verify checks native identities and replay; new engineering provenance is always isolated.
    SequentialRunner().run(create_pipeline(), catalog)
    print(json.dumps(catalog["preparation_bundle"].load(), indent=2))
