"""Load and validate existing notebook 03 products; never run consolidation."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.training_preparation.validation import validate_panel

from .contract import PreparationConfig, PreparationError, read_json


def fingerprint(path: Path) -> dict[str, Any]:
    """Hash file bytes with bounded memory.

    Args:
        path: Existing input path.

    Returns:
        SHA-256 and byte count.
    """
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return {"sha256": digest.hexdigest(), "bytes": size}


def read_panel(
    path: Path, contract: dict[str, Any], *, reference_end: str | None = None
) -> pd.DataFrame:
    """Parse declared CSV types, preserving empty non-nullable trace strings.

    Args:
        path: Existing panel CSV path.
        contract: Preparation schema.
        reference_end: Optional last reference month; filter before value parsing.

    Returns:
        Typed input frame, with no imputation or filtering.

    Raises:
        PreparationError: If header or value parsing is invalid.
    """
    with path.open(newline="", encoding="utf-8") as stream:
        header = next(csv.reader(stream), [])
    if len(header) != len(set(header)):
        raise PreparationError("Duplicate CSV columns")
    frame = pd.read_csv(path, dtype="string", keep_default_na=False)
    expected = {f["name"] for f in contract["schema"]}
    if set(frame.columns) != expected:
        raise PreparationError("Schema mismatch in CSV header")
    source_rows = len(frame)
    if reference_end is not None:
        frame = frame.loc[frame["year_month"] <= reference_end].copy()
    frame.attrs["source_rows"] = source_rows
    return parse_fields(frame, contract)


def parse_fields(frame: pd.DataFrame, contract: dict[str, Any]) -> pd.DataFrame:
    """Type only the supplied schema, preserving its nullable/empty-string policy."""
    for field in contract["schema"]:
        name = field["name"]
        s = frame[name]
        if field["nullable"]:
            s = s.mask(s.eq(""))
        dtype = field["dtype"].lower()
        try:
            if dtype == "bool":
                if not s.dropna().isin(["True", "False"]).all():
                    raise ValueError("Expected True/False")
                frame[name] = s.map({"True": True, "False": False}).astype("boolean")
            elif dtype in ("float64", "int64"):
                numeric = pd.to_numeric(s, errors="raise")
                if not field["nullable"] and s.eq("").any():
                    raise ValueError("Empty required number")
                frame[name] = numeric.astype("Float64" if dtype == "float64" else "Int64")
            else:
                frame[name] = s
        except (TypeError, ValueError) as exc:
            raise PreparationError(f"Invalid CSV values: {name}") from exc
    return frame


@dataclass(frozen=True)
class PreparationResult:
    """Validated inputs and aggregate evidence for notebook review.

    Args:
        panel: Unfiltered panel preserving scientific values.
        contract: Preparation contract declaring X, Y, keys and controls.
        report: Coverage summary and verified input fingerprints.
    """

    panel: pd.DataFrame
    contract: dict[str, Any]
    report: dict[str, Any]


def prepare_inputs(
    config: PreparationConfig, *, reference_end: str | None = None
) -> PreparationResult:
    """Verify manifest fingerprints and validate the existing panel without writes.

    Args:
        config: Repository and input configuration.
        reference_end: Optional development boundary. Later rows are excluded
            before typed validation or profiling.

    Returns:
        Validated panel, role contract and input-validation evidence.

    Raises:
        PreparationError: If fingerprints, schema, catalog or panel checks fail.
    """
    contract, manifest, before = verified_sources(config)
    panel = read_panel(
        config.resolve(contract["panel_path"]), contract, reference_end=reference_end
    )
    record = manifest["outputs"]["panel_mensual_dengue_clima"]
    if (panel.attrs["source_rows"], len(panel.columns)) != (record["rows"], record["columns"]):
        raise PreparationError("Panel dimensions differ from manifest")
    catalog_path = "data/sources/Divipola-municipios.md"
    before[catalog_path] = fingerprint(config.resolve(catalog_path))
    catalog = read_json(config.resolve(catalog_path))["resultado"]
    codes = {
        str(r["CODIGO_DPTO_MPIO"]).zfill(5)
        for r in catalog
        if str(r["CODIGO_DEPARTAMENTO"]) in {"50", "73"}
    }
    if set(panel["municipality_code"]) != codes:
        raise PreparationError("Panel municipalities differ from scope catalog")
    coverage = dict(manifest["coverage"])
    if reference_end is not None:
        if reference_end >= contract["temporal_policy"]["reserved_final_block_start"]:
            raise PreparationError("Development boundary enters reserved block")
        coverage["panel_month_end"] = min(reference_end, coverage["panel_month_end"])
    report = validate_panel(panel, contract, coverage)
    for relative, value in before.items():
        if fingerprint(config.resolve(relative)) != value:
            raise PreparationError(f"Input changed while validating: {relative}")
    report["input_fingerprints"] = before
    report["contract_version"] = contract["version"]
    report["status"] = "PASS"
    return PreparationResult(panel, contract, report)


def verified_sources(
    config: PreparationConfig,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Verify complete source identities and matching schemas before semantic reads."""
    contract_path = config.resolve(config.contract_path)
    manifest_path = config.resolve(config.manifest_path)
    before = {
        str(config.contract_path): fingerprint(contract_path),
        str(config.manifest_path): fingerprint(manifest_path),
    }
    contract = read_json(contract_path)
    manifest = read_json(manifest_path)
    expected_paths = {
        "dengue_y_dengue_grave": "data/processed/dengue_y_dengue_grave.csv",
        "panel_mensual_dengue_clima": contract["panel_path"],
        "candidate_contract": contract["upstream_contract_path"],
        "y_label_history_traceability": (
            "data/interim/stage2_consolidated_dataset_pipeline/y_label_history_traceability.csv"
        ),
        "current_endemic_channel_traceability": "data/interim/stage2_consolidated_dataset_pipeline/"
        "current_endemic_channel_traceability.csv",
    }
    for key, expected_path in expected_paths.items():
        record = manifest["outputs"][key]
        if record["path"] != expected_path:
            raise PreparationError(f"Unexpected manifest output path: {key}")
        actual = fingerprint(config.resolve(record["path"]))
        if actual != {k: record[k] for k in ("sha256", "bytes")}:
            raise PreparationError(f"Input fingerprint mismatch: {key}")
        before[record["path"]] = actual
    upstream = read_json(config.resolve(contract["upstream_contract_path"]))
    if contract["schema"] != upstream["datasets"]["panel_mensual_dengue_clima"]["schema"]:
        raise PreparationError("Preparation schema differs from construction schema")
    return contract, manifest, before
