"""Preparation boundaries and replay of explicitly saved training-only states."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import AUTHORITIES, canonical_bytes, resolve_configuration

from .contract import PreparationError
from .eligibility import build_controls
from .features import DERIVED_COLUMNS, KEYS, derive_features
from .preprocessing import (
    CATEGORICAL,
    MISSING,
    UNKNOWN,
    ZONES,
    PreparerSpec,
    fit_preparer,
    runtime_versions,
    transform_predictors,
)
from .serialization import bytes_record, json_bytes, serialize_table
from .temporal import select_window


def preparation_contract(resolved: dict[str, Any]) -> dict[str, Any]:
    body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
    if hashlib.sha256(canonical_bytes(body)).hexdigest() != resolved["configuration_sha256"]:
        raise PreparationError("Resolved configuration identity changed")
    entry = resolved["authorities"]["training_preparation_contract_v1"]
    if (
        resolved["operational"]["profile"] != "preparation"
        or resolved["operational"]["tracking"] not in ("disabled", "enabled")
        or entry["sha256"] != AUTHORITIES["training_preparation_contract_v1"]["sha256"]
    ):
        raise PreparationError("Unapproved preparation configuration")
    # Compare semantic document with the pinned envelope captured by ConfigurationInputsDataset.
    if (
        entry["document"] != resolved["preparation"]["contract"]
        or hashlib.sha256(canonical_bytes(entry["document"])).hexdigest()
        != "b44883fbe5f2f128168b3e9c5c8f770d1894303f364f4c6214170241a1ebb00f"
    ):
        raise PreparationError("Contradictory preparation contract")
    return entry["document"]


def resolve_preparation_configuration(
    inputs: dict[str, Any],
    parameters: dict[str, Any],
    sources: dict[str, Any],
    saved: dict[str, Any],
) -> dict[str, Any]:
    resolved = resolve_configuration(inputs, parameters)
    resolved["preparation"] = {
        "contract": sources["contract"],
        "stage2": sources["provenance"],
        "saved_preparers": saved["provenance"],
    }
    body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
    resolved["configuration_sha256"] = hashlib.sha256(canonical_bytes(body)).hexdigest()
    preparation_contract(resolved)
    return resolved


def features(
    sources: dict[str, Any], resolved: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    contract = preparation_contract(resolved)
    candidates = derive_features(sources["panel"], contract)
    return candidates[KEYS], candidates.drop(columns=KEYS)


def eligibility(
    sources: dict[str, Any], resolved: dict[str, Any]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    return build_controls(sources["panel"], preparation_contract(resolved), sources["policy"])


def boundaries(resolved: dict[str, Any]) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    settings = preparation_contract(resolved)["temporal_preparation"]
    producer, consumer = {}, {}
    for cutoff in settings["cutoffs"]:
        for h in (1, 2):
            window = f"{cutoff}_t{h}"
            producer[window] = cutoff
            consumer[window] = {
                "train": cutoff,
                "validation": str(pd.Period(cutoff, freq="M") + 6 - h),
            }
    return producer, consumer


def validate_partition(
    X: pd.DataFrame,
    controls: pd.DataFrame,
    columns: list[str],
    horizon: int,
    producer_cutoff: str,
    consumer_cutoff: str,
    split: str,
) -> None:
    """Reject role/order/alignment violations and unavailable labels or origins."""
    if (
        split not in ("train", "validation")
        or horizon not in (1, 2)
        or list(X) != columns
        or len(X) != len(controls)
        or X.empty
        or not X.index.equals(controls.index)
        or controls.duplicated(KEYS).any()
        or not X.municipality_code.astype(str).equals(controls.municipality_code.astype(str))
    ):
        raise PreparationError("Partition role/schema/order or alignment mismatch")
    origins = controls.year_month
    targets = controls[f"target_period_t{horizon}"]
    expected = pd.Series(
        (pd.PeriodIndex(origins, freq="M") + horizon).astype(str), index=controls.index
    )
    label_cutoff = (
        producer_cutoff if split == "train" else str(pd.Period(consumer_cutoff, freq="M") + horizon)
    )
    if (
        producer_cutoff >= "2025-01"
        or consumer_cutoff >= "2025-01"
        or (origins > consumer_cutoff).any()
        or (origins >= "2025-01").any()
        or (targets > label_cutoff).any()
        or (targets >= "2025-01").any()
        or not targets.eq(expected).all()
        or (split == "train" and consumer_cutoff != producer_cutoff)
        or (split == "validation" and (origins < producer_cutoff).any())
    ):
        raise PreparationError("Future label/origin or reserved temporal boundary")


def validate_saved_state(X_train: pd.DataFrame, state: dict[str, Any], columns: list[str]) -> None:
    """Bind saved state to the entire ordered training cohort without fitting."""
    numeric = [n for n in columns if n not in CATEGORICAL]
    expected_categories = {
        "municipality_code": sorted(X_train.municipality_code.dropna().astype(str).unique())
        + [MISSING, UNKNOWN],
        "zona_canal_t": [*ZONES, MISSING],
        "zona_canal_lag_1": [*ZONES, MISSING],
    }
    if state["categories"] != expected_categories:
        raise PreparationError("Saved categorical schema/order incompatible with training")
    spec = PreparerSpec(**state["spec"])
    spec.validate()
    outputs = (
        numeric + [f"{n}={v}" for n in CATEGORICAL for v in expected_categories[n]]
        if spec.encoding == "onehot"
        else columns
    )
    if (
        state["input_columns"] != columns
        or list(X_train) != columns
        or state["numeric_columns"] != numeric
        or state["output_columns"] != outputs
        or state["fit_rows"] != len(X_train)
        or state["fit_X_fingerprint"] != bytes_record(serialize_table(X_train))
        or state["versions"] != runtime_versions()
    ):
        raise PreparationError("Saved preparer schema or training identity mismatch")


def fit_training_partition(
    X: pd.DataFrame,
    controls: pd.DataFrame,
    spec: PreparerSpec,
    columns: list[str],
    horizon: int,
    cutoff: str,
    split: str,
) -> dict[str, Any]:
    """Explicit fit seam used only with deterministic synthetic data in tests."""
    if split != "train":
        raise PreparationError("Preparer fit requires train role")
    validate_partition(X, controls, columns, horizon, cutoff, cutoff, split)
    return fit_preparer(X, spec)


def partitions(
    keys: pd.DataFrame,
    candidates: pd.DataFrame,
    controls: pd.DataFrame,
    sources: dict[str, Any],
    resolved: dict[str, Any],
    producer: dict[str, str],
    consumer: dict[str, dict[str, str]],
) -> dict[str, Any]:
    contract = preparation_contract(resolved)
    expected_features = [*contract["roles"]["predictors"], *DERIVED_COLUMNS]
    if list(candidates) != expected_features or not keys.equals(controls[KEYS]):
        raise PreparationError("Deterministic feature order or control alignment mismatch")
    # Preserve the historical persisted-development parser boundary exactly.
    parsed = pd.read_csv(
        BytesIO(serialize_table(candidates)),
        float_precision="round_trip",
        dtype={"zona_canal_t": "string", "zona_canal_lag_1": "string"},
    )
    X = pd.concat([keys[["municipality_code"]], parsed], axis=1)
    controls = controls.copy()
    controls["feature_row"] = controls.index
    expected_windows = {
        f"{c}_t{h}" for c in contract["temporal_preparation"]["cutoffs"] for h in (1, 2)
    }
    if set(producer) != expected_windows or set(consumer) != expected_windows:
        raise PreparationError("Only the eight approved windows are permitted")
    if (producer, consumer) != boundaries(resolved):
        raise PreparationError("Cutoff boundaries differ from approved windows")
    result = {}
    for window in sorted(expected_windows):
        cutoff = producer[window]
        h = int(window[-1])
        selection = select_window(controls, sources["policy"], cutoff, h)
        splits = {}
        for split, selected in (("train", selection.train), ("validation", selection.validation)):
            raw = X.loc[selected.index].reset_index(drop=True)
            control = selected.reset_index(drop=True)
            validate_partition(raw, control, list(X), h, cutoff, consumer[window][split], split)
            splits[split] = {
                "X": raw,
                "Y": control[[f"y_t{h}"]],
                "keys": control[KEYS + [f"target_period_t{h}", "feature_row"]],
                "controls": control,
            }
        result[window] = {"splits": splits, "audit": selection.audit}
    return result


def replay(
    windows: dict[str, Any],
    saved: dict[str, Any],
    resolved: dict[str, Any],
    producer: dict[str, str],
    consumer: dict[str, dict[str, str]],
) -> dict[str, Any]:
    contract = preparation_contract(resolved)
    columns = ["municipality_code", *contract["roles"]["predictors"], *DERIVED_COLUMNS]
    if set(windows) != set(producer) or (producer, consumer) != boundaries(resolved):
        raise PreparationError("Replay window/cutoff mismatch")
    if set(saved["states"]) != set(windows):
        raise PreparationError("Saved preparers do not cover the eight windows")
    result = {}
    for window, entry in windows.items():
        profiles = {}
        expected_profiles = contract["temporal_preparation"]["profiles"]
        if set(saved["states"][window]) != set(expected_profiles):
            raise PreparationError("Saved preparer profiles differ")
        for name, state in saved["states"][window].items():
            if state["spec"] != expected_profiles[name]:
                raise PreparationError("Saved preparer profile schema differs")
            state_name = f"{window}_{name}_preparer.json"
            if bytes_record(json_bytes(state)) != saved["provenance"]["state_files"].get(
                state_name
            ):
                raise PreparationError("Saved preparer state identity changed")
            validate_saved_state(entry["splits"]["train"]["X"], state, columns)
            matrices = {}
            for split, tables in entry["splits"].items():
                control = tables["controls"]
                h = int(window[-1])
                if not tables["Y"].equals(control[[f"y_t{h}"]]) or not tables["keys"].equals(
                    control[KEYS + [f"target_period_t{h}", "feature_row"]]
                ):
                    raise PreparationError("X/Y/keys/controls alignment mismatch")
                validate_partition(
                    tables["X"],
                    tables["controls"],
                    columns,
                    int(window[-1]),
                    producer[window],
                    consumer[window][split],
                    split,
                )
                matrices[split] = transform_predictors(tables["X"], state)
            profiles[name] = {"state": state, "matrices": matrices}
        result[window] = {**entry, "profiles": profiles}
    return result
