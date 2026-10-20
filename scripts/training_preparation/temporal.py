"""Reference-aligned temporal datasets and training-only preparers, without predictors."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationConfig, PreparationError, read_json
from .development import (
    build_development,
    check_preservation,
    code_fingerprints,
    resolve_root,
    serialize_table,
)
from .eligibility import readiness
from .features import KEYS
from .persistence import bytes_record, json_bytes, publish_bundle, verify_bundle
from .pipeline import fingerprint
from .preprocessing import (
    CATEGORICAL,
    PreparerSpec,
    fit_preparer,
    runtime_versions,
    transform_predictors,
)

reference = import_module("scripts.stage2_notebook_visual_assets")


@dataclass(frozen=True)
class WindowSelection:
    """Selected rows and auditable configured/effective time boundaries.

    Args:
        train: Training rows selected by existing target-aware selector.
        validation: Sequential validation-origin rows selected by the same reference.
        audit: Actual support, configured target interval and independent agreement.
    """

    train: pd.DataFrame
    validation: pd.DataFrame
    audit: dict[str, Any]


def select_window(
    frame: pd.DataFrame, policy: dict[str, Any], cutoff: str, horizon: int
) -> WindowSelection:
    """Reuse the existing selectors and enforce training/validation causal boundaries.

    Args:
        frame: Development keys and target controls, with no reserved reference rows.
        policy: Current notification-year-backed policy.
        cutoff: Fit cutoff, inclusive for observable training targets.
        horizon: One or two calendar months.

    Returns:
        Reference row selections and audit distinguishing configured/effective periods.

    Raises:
        PreparationError: If calendar, labels or independent key sets disagree.
    """
    if horizon not in (1, 2) or frame.duplicated(KEYS).any():
        raise PreparationError("Invalid horizon or duplicate temporal keys")
    bounds = policy["development_target_eligibility"]
    if (frame["year_month"] >= bounds["reserved_block_start"]).any():
        raise PreparationError("Reserved origins cannot enter temporal preparation")
    target_column, label_column = f"target_period_t{horizon}", f"y_t{horizon}"
    expected = pd.Series(
        (pd.PeriodIndex(frame["year_month"], freq="M") + horizon).astype(str), index=frame.index
    )
    if not frame[target_column].eq(expected).all():
        raise PreparationError("Target calendar contradicts prediction origin/horizon")
    configured_start = str(pd.Period(cutoff, freq="M") + 1)
    configured_end = str(pd.Period(cutoff, freq="M") + 6)
    target_end = min(
        configured_end,
        bounds["target_max"],
        str(pd.Period(bounds["reserved_block_start"], freq="M") - 1),
    )
    target_start = max(configured_start, bounds["target_min"])
    selections = []
    for split, kwargs in (
        (
            "train",
            dict(
                reference_max_period=cutoff,
                target_min_period=bounds["target_min"],
                target_max_period=min(cutoff, bounds["target_max"]),
            ),
        ),
        (
            "validation",
            dict(
                reference_min_period=cutoff,
                reference_max_period=configured_end,
                target_min_period=target_start,
                target_max_period=target_end,
            ),
        ),
    ):
        selected = reference.select_supervised_rows(frame, horizon, **kwargs)
        independent = readiness.independent_select_supervised_rows(frame, horizon, **kwargs)
        if list(selected[KEYS].itertuples(index=False, name=None)) != list(
            independent[KEYS].itertuples(index=False, name=None)
        ):
            raise PreparationError(f"Independent temporal selection differs: {split}")
        if (
            selected.empty
            or selected[label_column].isna().any()
            or not selected[label_column].isin([0, 1]).all()
        ):
            raise PreparationError(f"Empty or non-evaluable temporal selection: {split}")
        if (selected[target_column] >= bounds["reserved_block_start"]).any():
            raise PreparationError("Reserved target entered development")
        selections.append(selected)
    train, validation = selections
    if (
        (train[target_column] > cutoff).any()
        or (validation["year_month"] < cutoff).any()
        or not validation[target_column].between(target_start, target_end).all()
        or set(train.index) & set(validation.index)
    ):
        raise PreparationError("Temporal causal boundary or partition overlap violated")
    audit = {
        "cutoff": cutoff,
        "horizon": horizon,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "configured_target_start": configured_start,
        "configured_target_end": configured_end,
        "reference_selector_agrees": True,
        "validation_semantics": (
            "Sequential predictions at each origin using information at that origin; "
            "not a single forecast at fit cutoff."
        ),
    }
    for split, selected in (("train", train), ("validation", validation)):
        audit[split] = {
            "origin_start": str(selected["year_month"].min()),
            "origin_end": str(selected["year_month"].max()),
            "target_start": str(selected[target_column].min()),
            "target_end": str(selected[target_column].max()),
        }
    return WindowSelection(train, validation, audit)


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
    """Build or verify eight temporal partitions and fitted preparers without models.

    Args:
        config: Repository and preparation contract paths.
        verify_only: Require current matching immutable artifacts without writing.

    Returns:
        Temporal bundle, distinct from original and deterministic feature data.

    Raises:
        PreparationError: If policy, reference, data identity or artifact checks fail.
    """
    development = build_development(config, verify_only=verify_only)
    contract = read_json(config.resolve(config.contract_path))
    settings = contract["temporal_preparation"]
    policy = development.manifest["eligibility_policy"]
    bounds = policy["development_target_eligibility"]
    if (
        tuple(settings["cutoffs"]) != tuple(readiness.TEMPORAL_WINDOW_TRAIN_ENDPOINTS)
        or bounds["target_min"] != settings["target_start"]
        or bounds["target_max"] != settings["target_end"]
    ):
        raise PreparationError("Configured temporal policy differs from current reference")
    X, controls = load_development(development.bundle, development.manifest)
    expected_X = ["municipality_code", *development.manifest["roles"]["features"]]
    if list(X.columns) != expected_X:
        raise PreparationError("Unexpected controls or labels in X")
    reference_audit = reference.build_temporal_validation_audit(
        controls,
        controls.head(0),
        settings["cutoffs"],
        expected_X,
        development_target_min=bounds["target_min"],
        development_target_max=bounds["target_max"],
    )
    payloads: dict[str, bytes] = {}
    windows = {}
    for cutoff in settings["cutoffs"]:
        for h in (1, 2):
            prefix = f"{cutoff}_t{h}"
            selected = select_window(controls, policy, cutoff, h)
            old = reference_audit.loc[
                (reference_audit["window_id"] == f"window_until_{cutoff}")
                & (reference_audit["horizon"] == f"t{h}")
            ].iloc[0]
            if (
                int(old["train_rows"]) != len(selected.train)
                or int(old["validation_rows"]) != len(selected.validation)
                or old["temporal_validation_result"] != "PASS"
            ):
                raise PreparationError(f"Existing temporal audit disagrees: {prefix}")
            files, metadata = _window_payloads(X, selected, prefix, settings["profiles"])
            payloads.update(files)
            windows[prefix] = metadata
    identity = {
        "development_bundle": development.manifest["bundle_id"],
        "development_manifest": fingerprint(development.bundle / "manifest.json"),
        "configuration": settings,
        "code": code_fingerprints(config.root),
        "runtime": runtime_versions(),
    }
    bundle_id = hashlib.sha256(json_bytes(identity)).hexdigest()
    manifest = {
        "schema": "temporal-preparation-v1",
        "bundle_id": bundle_id,
        "identity": identity,
        "windows": windows,
        "raw_X_columns": expected_X,
        "development_bundle": str(development.bundle.relative_to(config.root)),
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "interpretation": (
            "Sequential-origin retrospective validation; no predictors trained; "
            "G2/G3 and performance not approved."
        ),
    }
    payloads["manifest.json"] = json_bytes(manifest)
    if identity["code"] != code_fingerprints(config.root):
        raise PreparationError("Code changed during temporal preparation")
    for relative, record in development.manifest["identity"]["data"].items():
        if fingerprint(config.resolve(relative)) != record:
            raise PreparationError(f"Input changed during temporal preparation: {relative}")
    base = config.resolve(settings["base_dir"])
    if verify_only:
        bundle = base / bundle_id
        verify_bundle(bundle, payloads)
    else:
        bundle = publish_bundle(
            base,
            bundle_id,
            payloads,
            existing_policy=contract["development_output"]["existing_policy"],
        )
    return TemporalResult(bundle, manifest)


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


if __name__ == "__main__":
    main()
