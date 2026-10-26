"""Manifest-backed raw EXP01 inputs, isolated from supplied labels and channel."""

from __future__ import annotations

import csv
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_preparation.contract import (
    PreparationConfig,
    PreparationError,
    read_json,
)
from sat_dengue.datasets.legacy_preparation.pipeline import (
    PreparationResult,
    fingerprint,
    parse_fields,
    verified_sources,
)
from sat_dengue.training_preparation.validation import (
    validate_climate_coverage,
    validate_counts,
    validate_monthly_support,
    validate_roles,
    validate_schema,
)

REFERENCE_END = "2024-12"


def prepare_exp01_inputs(config: PreparationConfig) -> PreparationResult:
    """Verify byte identity, then validate only EXP01's consumed raw input values.

    Header/dimension and full-file hashes still describe the original source.
    Supplied target/channel values are never typed or semantically validated.
    Coverage controls are used for validation only and are not passed to science.
    """
    contract, manifest, before = verified_sources(config)
    validate_roles(contract)
    if REFERENCE_END >= contract["temporal_policy"]["reserved_final_block_start"]:
        raise PreparationError("EXP01 reference boundary enters reserved block")
    raw = contract["roles"]["keys"] + [
        c for c in contract["roles"]["predictors"] if c != "zona_canal_t"
    ]
    controls = [
        "department_code",
        "in_epi_coverage",
        "total_notifications_count",
        "epi_count_status",
        "expected_days_in_month",
        "climate_days_observed",
    ] + [c for c in contract["roles"]["controls"] if c.endswith("_valid_days")]
    columns = raw + controls
    schema = [field for field in contract["schema"] if field["name"] in columns]
    if {field["name"] for field in schema} != set(columns):
        raise PreparationError("EXP01 raw/control schema is incomplete")
    path = config.resolve(contract["panel_path"])
    with path.open(newline="", encoding="utf-8") as stream:
        header = next(csv.reader(stream), [])
    if len(header) != len(set(header)) or set(header) != {
        field["name"] for field in contract["schema"]
    }:
        raise PreparationError("Schema mismatch in CSV header")
    panel = pd.read_csv(path, usecols=columns, dtype="string", keep_default_na=False)
    record = manifest["outputs"]["panel_mensual_dengue_clima"]
    if (len(panel), len(header)) != (record["rows"], record["columns"]):
        raise PreparationError("Panel dimensions differ from manifest")
    # Validate the cutoff key before comparison so malformed keys cannot disappear.
    if not panel.year_month.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise PreparationError("Invalid monthly keys")
    panel = panel.loc[panel.year_month.le(REFERENCE_END)].copy()
    projected_contract: dict[str, Any] = {"schema": schema}
    panel = parse_fields(panel, projected_contract)
    validate_schema(panel, projected_contract)
    catalog_path = "data/sources/Divipola-municipios.md"
    before[catalog_path] = fingerprint(config.resolve(catalog_path))
    catalog = read_json(config.resolve(catalog_path))["resultado"]
    codes = {
        str(row["CODIGO_DPTO_MPIO"]).zfill(5)
        for row in catalog
        if str(row["CODIGO_DEPARTAMENTO"]) in {"50", "73"}
    }
    if set(panel.municipality_code) != codes:
        raise PreparationError("Panel municipalities differ from scope catalog")
    coverage = dict(manifest["coverage"])
    coverage["panel_month_end"] = min(REFERENCE_END, coverage["panel_month_end"])
    periods, expected, covered = validate_monthly_support(panel, coverage)
    for column, allowed in contract["categories"].items():
        if column in columns and not panel[column].dropna().isin(allowed).all():
            raise PreparationError(f"Invalid category: {column}")
    validate_counts(panel, covered)
    validate_climate_coverage(panel, periods, coverage)
    for relative, value in before.items():
        if fingerprint(config.resolve(relative)) != value:
            raise PreparationError(f"Input changed while validating: {relative}")
    result = panel[raw].copy()
    report = {
        "status": "PASS",
        "contract_version": contract["version"],
        "input_fingerprints": before,
        "rows": len(result),
        "municipalities": result.municipality_code.nunique(),
        "start": str(expected[0]),
        "end": str(expected[-1]),
        "consumed_columns": raw,
        "validated_controls": controls,
        "missing_by_column": {c: int(n) for c, n in result.isna().sum().items()},
        "operational_historical_availability": "UNPROVEN; retrospective consolidated data",
    }
    return PreparationResult(result, contract, report)
