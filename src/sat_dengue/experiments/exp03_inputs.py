"""Manifest-backed raw admission for EXP03's consumed retrospective benchmark.

This boundary is deliberately separate from EXP01's immutable 2024 reference
cutoff. The caller owns scientific authorization, budget and terminal-freeze
verification. Coverage/maturity readiness does not itself confer authorization.
No target labels, supplied zones or channel percentiles enter the returned panel.
"""

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

REFERENCE_END = "2025-12"


def prepare_benchmark_inputs(
    config: PreparationConfig, coverage_metadata: dict[str, Any]
) -> PreparationResult:
    """Admit verified source values only after explicit provenance readiness.

    Incomplete readiness raises before resolving, opening or fingerprinting any
    source path. Future rows are dimension/hash checked but not semantically
    consumed after the bounded 2025-12 cutoff. Manifest dates establish declared
    coverage only; separately reviewed maturity evidence remains indispensable.
    """
    if (
        coverage_metadata.get("governed_coverage") is not True
        or coverage_metadata.get("maturity_verified") is not True
        or not isinstance(coverage_metadata.get("provenance_sha256"), str)
        or not coverage_metadata["provenance_sha256"].strip()
    ):
        raise PermissionError(
            "EXP03 benchmark coverage/maturity provenance unverified; private reads forbidden"
        )
    contract, manifest, before = verified_sources(config)
    validate_roles(contract)
    raw = contract["roles"]["keys"] + [
        column for column in contract["roles"]["predictors"] if column != "zona_canal_t"
    ]
    controls = [
        "department_code",
        "in_epi_coverage",
        "total_notifications_count",
        "epi_count_status",
        "expected_days_in_month",
        "climate_days_observed",
    ] + [column for column in contract["roles"]["controls"] if column.endswith("_valid_days")]
    columns = raw + controls
    schema = [field for field in contract["schema"] if field["name"] in columns]
    if {field["name"] for field in schema} != set(columns):
        raise PreparationError("EXP03 benchmark raw/control schema is incomplete")
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
    if not panel.year_month.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])").all():
        raise PreparationError("Invalid monthly keys")
    panel = panel.loc[panel.year_month.le(REFERENCE_END)].copy()
    projected_contract: dict[str, Any] = {"schema": schema}
    panel = parse_fields(panel, projected_contract)
    validate_schema(panel, projected_contract)
    catalog_path = "data/sources/Divipola-municipios.md"
    before[catalog_path] = fingerprint(config.resolve(catalog_path))
    catalog = read_json(config.resolve(catalog_path))["resultado"]
    scoped = [row for row in catalog if str(row["CODIGO_DEPARTAMENTO"]) in {"50", "73"}]
    codes = [str(row["CODIGO_DPTO_MPIO"]).zfill(5) for row in scoped]
    if (
        len(codes) != len(set(codes))
        or len(codes) != 76
        or sum(code.startswith("50") for code in codes) != 29
        or sum(code.startswith("73") for code in codes) != 47
    ):
        raise PreparationError("EXP03 benchmark requires the governed 29 Meta/47 Tolima catalog")
    if set(panel.municipality_code) != set(codes):
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
    return PreparationResult(
        result,
        contract,
        {
            "status": "PASS",
            "evidence_type": "consumed_retrospective_benchmark",
            "reference_end": REFERENCE_END,
            "contract_version": contract["version"],
            "input_fingerprints": before,
            "rows": len(result),
            "municipalities": result.municipality_code.nunique(),
            "start": str(expected[0]),
            "end": str(expected[-1]),
            "consumed_columns": raw,
            "validated_controls": controls,
            "missing_by_column": {column: int(n) for column, n in result.isna().sum().items()},
            "coverage_provenance_sha256": coverage_metadata["provenance_sha256"],
            "full_2025_calendar_coverage": all(
                str(period) in set(result.year_month)
                for period in pd.period_range("2025-01", "2025-12", freq="M")
            ),
            "scientific_authorization": "caller-owned; not established by this input adapter",
            "operational_historical_availability": "UNPROVEN; retrospective consolidated data",
        },
    )
