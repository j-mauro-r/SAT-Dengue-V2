"""Reference-aligned temporal datasets and training-only preparers, without predictors."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.training_preparation.features import KEYS
from sat_dengue.training_preparation.preprocessing import (
    CATEGORICAL,
    PreparerSpec,
    fit_preparer,
    runtime_versions,
    transform_predictors,
)
from sat_dengue.training_preparation.temporal import WindowSelection
from sat_dengue.training_preparation.temporal import select_window as select_window

from .contract import PreparationConfig, PreparationError, read_json
from .development import (
    check_preservation,
    resolve_root,
    serialize_table,
)
from .persistence import json_bytes
from .pipeline import fingerprint

reference = import_module("scripts.stage2_notebook_visual_assets")


def read_artifact(bundle: Path, name: str, manifest: dict[str, Any], **kwargs: Any) -> pd.DataFrame:
    """Read a hashed immutable CSV, verifying its bytes before and after parsing.

    Args:
        bundle: Artifact bundle directory.
        name: Exact manifest-declared filename.
        manifest: Bundle manifest containing file fingerprints.
        kwargs: Explicit pandas schema/parser options.

    Returns:
        Parsed table, without trusting an unverified stale file.

    Raises:
        PreparationError: If artifact bytes differ or a filename is unsafe.
    """
    if Path(name).name != name or (bundle / name).is_symlink():
        raise PreparationError("Unsafe artifact filename")
    path = bundle / name
    expected = manifest["files"][name]
    if fingerprint(path) != expected:
        raise PreparationError(f"Artifact fingerprint mismatch: {name}")
    frame = pd.read_csv(path, float_precision="round_trip", **kwargs)
    if fingerprint(path) != expected:
        raise PreparationError(f"Artifact changed during read: {name}")
    return frame


def load_development(bundle: Path, manifest: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load separately keyed X and target controls from a verified development bundle.

    Args:
        bundle: Current deterministic development bundle.
        manifest: Verified development manifest.

    Returns:
        Raw X including explicitly authorized municipality category, and keyed controls.

    Raises:
        PreparationError: If column roles or row alignment differ.
    """
    keys = read_artifact(bundle, "keys.csv", manifest, dtype={k: "string" for k in KEYS})
    features = read_artifact(
        bundle,
        "features.csv",
        manifest,
        dtype={"zona_canal_t": "string", "zona_canal_lag_1": "string"},
    )
    dtype = {
        **{k: "string" for k in KEYS},
        **{f"y_evaluable_t{h}": "boolean" for h in (1, 2)},
        **{f"y_t{h}": "Int64" for h in (1, 2)},
    }
    controls = read_artifact(bundle, "controls.csv", manifest, dtype=dtype)
    if (
        list(features.columns) != manifest["roles"]["features"]
        or not keys.equals(controls[KEYS])
        or len(features) != len(keys)
        or keys.duplicated().any()
    ):
        raise PreparationError("Development feature/control alignment or roles differ")
    X = pd.concat([keys[["municipality_code"]], features], axis=1)
    controls["feature_row"] = controls.index
    return X, controls


def _window_payloads(
    X: pd.DataFrame, selection: WindowSelection, prefix: str, profiles: dict[str, Any]
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Separate X/Y/indices and fit each profile only on this training partition.

    Args:
        X: Raw candidate features with municipality representation.
        selection: Validated horizon-specific rows.
        prefix: Safe window/horizon filename prefix.
        profiles: Configurable future-estimator preparer specifications.

    Returns:
        All CSV/JSON payloads and the window manifest entry.
    """
    payloads: dict[str, bytes] = {}
    horizon = selection.audit["horizon"]
    target = f"target_period_t{horizon}"
    raw = {}
    for split, selected in (("train", selection.train), ("validation", selection.validation)):
        raw[split] = X.loc[selected.index].reset_index(drop=True)
        index = selected[KEYS + [target, "feature_row"]].reset_index(drop=True)
        y = selected[[f"y_t{horizon}"]].reset_index(drop=True)
        for kind, table in (("index", index), ("X", raw[split]), ("y", y)):
            payloads[f"{prefix}_{split}_{kind}.csv"] = serialize_table(table)
    metadata: dict[str, Any] = {**selection.audit, "profiles": {}}
    for name, config in profiles.items():
        if not name.replace("_", "").isalnum():
            raise PreparationError("Unsafe profile name")
        state = fit_preparer(raw["train"], PreparerSpec(**config))
        state_name = f"{prefix}_{name}_preparer.json"
        payloads[state_name] = json_bytes(state)
        for split in ("train", "validation"):
            matrix = transform_predictors(raw[split], state)
            payloads[f"{prefix}_{name}_{split}_matrix.csv"] = serialize_table(matrix)
        metadata["profiles"][name] = {
            "state": state_name,
            "spec": config,
            "input_columns": state["input_columns"],
            "output_columns": state["output_columns"],
            "parameters_fitted_from": "X_train only; no Y or validation",
        }
    return payloads, metadata


@dataclass(frozen=True)
class TemporalResult:
    """Immutable temporal artifact reference.

    Args:
        bundle: Local directory with eight window/horizon combinations.
        manifest: Complete reproducible identity and selection/preparation audit.
    """

    bundle: Path
    manifest: dict[str, Any]


def build_temporal(config: PreparationConfig, *, verify_only: bool = False) -> TemporalResult:
    """Load the explicitly identified native temporal bundle without rebuilding or fitting.

    Args:
        config: Repository and preparation contract paths.
        verify_only: Retained flag; both modes verify saved immutable artifacts without writing.

    Returns:
        Temporal bundle, distinct from original and deterministic feature data.

    Raises:
        PreparationError: If policy, reference, data identity or artifact checks fail.
    """
    from sat_dengue.datasets.preparation import NATIVE_PREPARATION, TEMPORAL, verified_native_bundle

    if config.root.resolve() != Path.cwd().resolve():
        raise PreparationError("Legacy temporal replay requires the repository root")
    manifest = verified_native_bundle(TEMPORAL, NATIVE_PREPARATION[TEMPORAL])
    return TemporalResult(config.resolve(TEMPORAL), manifest)


def run_summary(result: TemporalResult, root: Path) -> dict[str, Any]:
    """Return bounded output shared by CLI, notebook and saved-output verifier.

    Args:
        result: Verified temporal result.
        root: Repository root for portable paths.

    Returns:
        Current identities and eight actual window supports without outcome statistics.
    """
    return {
        "status": "PASS",
        "temporal_bundle": str(result.bundle.relative_to(root)),
        "development_bundle": result.manifest["development_bundle"],
        "windows": [
            {
                k: row[k]
                for k in (
                    "cutoff",
                    "horizon",
                    "train_rows",
                    "validation_rows",
                    "configured_target_start",
                    "configured_target_end",
                    "train",
                    "validation",
                )
            }
            for row in result.manifest["windows"].values()
        ],
        "profiles": {
            name: {"spec": profile["spec"], "matrix_columns": len(profile["output_columns"])}
            for name, profile in next(iter(result.manifest["windows"].values()))["profiles"].items()
        },
        "semantics": (
            "Successive forecasts at each origin; no model trained; "
            "retrospective availability unproven."
        ),
    }


def load_prepared_window(
    bundle: Path, window: str, profile: str, split: str
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Load a hashed matrix/Y/index and JSON preparer, restoring native categories.

    Args:
        bundle: Verified temporal bundle directory.
        window: Manifest window key, for example 2018-12_t1.
        profile: Configured preparer profile name.
        split: Train or validation.

    Returns:
        Model-ready matrix, separate Y, row index and reusable inference state.

    Raises:
        PreparationError: If identifiers, hashes, column order or row alignment differ.
    """
    manifest = read_json(bundle / "manifest.json")
    if split not in ("train", "validation") or window not in manifest["windows"]:
        raise PreparationError("Unknown temporal dataset")
    entry = manifest["windows"][window]["profiles"][profile]
    state_path = bundle / entry["state"]
    if fingerprint(state_path) != manifest["files"][entry["state"]]:
        raise PreparationError("Preparer fingerprint mismatch")
    state = read_json(state_path)
    matrix = read_artifact(bundle, f"{window}_{profile}_{split}_matrix.csv", manifest)
    if list(matrix.columns) != state["output_columns"] or state["versions"] != runtime_versions():
        raise PreparationError("Saved matrix schema/runtime mismatch")
    if state["spec"]["encoding"] == "native":
        for name in CATEGORICAL:
            matrix[name] = pd.Categorical(
                matrix[name].astype("string"), categories=state["categories"][name]
            )
    y = read_artifact(bundle, f"{window}_{split}_y.csv", manifest, dtype="Int64")
    index = read_artifact(
        bundle, f"{window}_{split}_index.csv", manifest, dtype={k: "string" for k in KEYS}
    )
    if len(matrix) != len(y) or len(matrix) != len(index):
        raise PreparationError("Saved matrix/Y/index row alignment mismatch")
    return matrix, y, index, state


def main() -> None:
    """Build or verify temporal artifacts; never train predictors or inspect final outcomes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()
    config = PreparationConfig(resolve_root(args.root))
    if args.baseline:
        check_preservation(config, args.baseline)
    result = build_temporal(config, verify_only=args.verify)
    if args.baseline:
        check_preservation(config, args.baseline)
    print(json_bytes(run_summary(result, config.root)).decode())
