"""Explicit V2 source admission and no-fit, immutable national V4 publication."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.canonical.national import aggregate_view
from sat_dengue.canonical.national_v4 import (
    DATASET,
    aggregate_notifications,
    build_v4,
    cast_common,
)
from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.datasets.canonical import CanonicalBundleDataset, execution_identity, verify_records
from sat_dengue.datasets.legacy_preparation.pipeline import read_panel
from sat_dengue.datasets.national import PINS, STEP2
from sat_dengue.datasets.stage2 import identity, local_path, verified_json
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

REFERENCES = {
    "national": (
        "canonical_model_table_national_v1",
        "c2267f61c7624f19ea7056c2d891512b12e85d81214145df1d31815d28fc3c29",
        "e801cf9b36b84ff0e0c8f336a88799d47f6e6bce9a6d1b155a1a37e20594afb4",
    ),
    "regional": (
        "canonical_model_table_v1",
        "ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98",
        "037445487086f7123ee2bf4b97b9af06b96716e2f24e9ff5160177c59da261d8",
    ),
}
LIMITATIONS = [
    (
        "SIVIGILA hashes establish snapshot identity; official extraction completeness "
        "and redistribution rights remain unverified."
    ),
    (
        "Counts are residence/INI_SIN notifications, "
        "not deduplicated persons, episodes or confirmed cases."
    ),
    "Unresolved geography remains excluded and accounted for; no invented territorial crosswalk.",
    "Current territory membership does not establish historical applicability.",
    "Retrospective SIVIGILA/GEE snapshots do not establish operational point-in-time availability.",
    (
        "Original GEE collection vintages, geometry correspondence "
        "and universal retrieval remain unverified."
    ),
    "Only the original 76 regional municipalities have approved pre-2011 H5 context.",
    "Island climate missingness remains explicit; climate is never zero-filled.",
    "2025 is consumed retrospective evidence and cannot enter any learned role.",
    "January 2026 source records are excluded by the explicit December 2025 panel boundary.",
    "Redistribution and Hugging Face sat-dengue-v3-through-2025-v1 remain pending license review.",
]


def read_reference(root: str, dataset: str) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Use the published schema, including pandas/Arrow booleans and empty trace strings."""
    columns = json.loads(local_path(root + "/columns.json").read_text())["columns"]
    fields = [
        {**f, "dtype": "bool" if f["dtype"].startswith(("bool", "boolean")) else f["dtype"]}
        for f in columns
    ]
    return cast_common(
        read_panel(local_path(root + "/" + dataset + ".csv"), {"schema": fields}), columns
    ), columns


class V4SourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Admit only the two fixed V1 publications and their authorized V2 raw sources."""

    def load(self) -> dict[str, Any]:
        records: dict[str, Any] = {}
        roots = {}
        for role, (dataset, bundle, manifest_sha) in REFERENCES.items():
            root = f"data/processed/{dataset}/{bundle}"
            roots[role] = root
            record = identity(local_path(root + "/manifest.json"))
            if record["sha256"] != manifest_sha:
                raise DatasetError(f"Pinned {role} V1 manifest changed")
            manifest = verified_json(root + "/manifest.json", record)
            body = {k: v for k, v in manifest.items() if k != "bundle_id"}
            if bytes_record(canonical_bytes(body))["sha256"] != bundle:
                raise DatasetError("Invalid historical publication identity")
            records[root + "/manifest.json"] = record
            for name, expected in manifest["files"].items():
                if Path(name).name != name:
                    raise DatasetError("Unsafe reference payload")
                records[root + "/" + name] = expected
            records.update(manifest["sources"])
        verify_records(records)
        step2 = verified_json(STEP2, PINS[STEP2])
        climate_paths = step2["view"]["sources"]
        if climate_paths != [
            "data/raw/google_earth_engine.csv",
            "data/sources/google_earth_engine_2020_national_gap/google_earth_engine_2020_01_national_gap.csv",
        ]:
            raise DatasetError("V4 requires the unchanged approved climate union")
        national, columns = read_reference(roots["national"], REFERENCES["national"][0])
        regional, _ = read_reference(roots["regional"], REFERENCES["regional"][0])
        contract = json.loads(local_path(roots["national"] + "/contract.json").read_text())
        contract["dataset"] = DATASET
        contract["window"].update(end="2025-12", months=175, rows=196350)
        catalog = national[
            ["municipality_code", "department_code", "municipality_name"]
        ].drop_duplicates()
        if len(catalog) != 1122 or catalog.municipality_code.duplicated().any():
            raise DatasetError("National V1 territory universe changed")

        def epi_chunks() -> Any:
            for name, event in (("dengue", "210"), ("dengue_grave", "220")):
                yield from (
                    (event, frame)
                    for frame in pd.read_csv(
                        local_path(f"data/raw/{name}.csv"),
                        dtype=str,
                        keep_default_na=False,
                        usecols=["COD_DPTO_R", "COD_MUN_R", "INI_SIN", "COD_EVE"],
                        chunksize=200000,
                    )
                )

        calendar, reconciliation = aggregate_notifications(epi_chunks(), catalog)

        def climate_chunks() -> Any:
            for path in climate_paths:
                for frame in pd.read_csv(
                    local_path(path), dtype=str, keep_default_na=False, chunksize=250000
                ):
                    if list(frame) != step2["columns"]:
                        raise DatasetError("Climate schema changed")
                    yield frame

        monthly = aggregate_view(climate_chunks(), "2011-06", "2025-12")
        if len(monthly) != 196350:
            raise DatasetError("National climate municipality-month grid changed")
        verify_records(records)
        execution = execution_identity()
        for relative in (
            "src/sat_dengue/datasets/national_v4.py",
            "src/sat_dengue/canonical/national.py",
            "src/sat_dengue/data/national_diagnostics.py",
            "src/sat_dengue/experiments/onset.py",
            "src/sat_dengue/pipelines/national_v4/pipeline.py",
        ):
            execution["code"][relative] = identity(local_path(relative))
        return {
            "calendar": calendar,
            "monthly": monthly,
            "regional": regional,
            "national": national,
            "contract": contract,
            "columns": columns,
            "reconciliation": reconciliation,
            "provenance": {
                "sources": records,
                "execution": execution,
                "generated_at": datetime.now(UTC).isoformat(),
                "climate_union": step2,
                "limitations": LIMITATIONS,
            },
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("V4 sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {
            "references": REFERENCES,
            "source_selection": "explicit V2 identities; external V3 excluded",
        }


def assemble_v4(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Gate the full raw reconstruction and both parities before exposing publishable bytes."""
    if validate_parameters(parameters) != {"profile": DATASET, "tracking": "disabled"}:
        raise ValueError("V4 requires its independent disabled-tracking profile")
    result = build_v4(
        *(
            sources[n]
            for n in ("calendar", "monthly", "regional", "national", "contract", "columns")
        )
    )
    table = result["table"]
    table_bytes = serialize_table(table)
    coverage: dict[str, Any] = {
        "rows": len(table),
        "columns": len(table.columns),
        "municipalities": int(table.municipality_code.nunique()),
        "origin_months": int(table.year_month.nunique()),
        "origin_range": [str(table.year_month.min()), str(table.year_month.max())],
        "horizons": {},
        "origin_role_counts": table.origin_scientific_role.value_counts().to_dict(),
    }
    for h in (1, 2):
        coverage["horizons"][str(h)] = {
            "target_range": [
                str(table[f"target_period_t{h}"].min()),
                str(table[f"target_period_t{h}"].max()),
            ],
            "maturity_counts": table[f"maturity_t{h}"].value_counts().to_dict(),
            "evaluability_counts": table[f"y_status_t{h}"].value_counts().to_dict(),
            "role_counts": table[f"scientific_role_t{h}"].value_counts().to_dict(),
            "onset_counts": table[f"onset_status_t{h}"].value_counts().to_dict(),
        }
    payloads = {
        DATASET + ".csv": table_bytes,
        "columns.json": canonical_bytes({"schema": DATASET, "columns": result["columns"]}),
        "contract.json": canonical_bytes(
            {
                **sources["contract"],
                "schema": "canonical-model-table-national-contract-v4",
                "schema_version": "4.0.0",
                "columns": result["columns"],
                "construction": "raw V2 source recomputation; inherited V1 scientific rules",
                "parent_publications": REFERENCES,
                "sources": sources["provenance"]["sources"],
                "history": (
                    "Only original regional V1 municipalities supply pre-2011-06 counts. "
                    "All other history is reconstructed from raw V2 sources through 2025-12; "
                    "no January 2026 observation enters any calculation."
                ),
                "absence": {
                    "rule": (
                        "V2 residence/INI_SIN admission and D2/D3 calendar zeros; no deduplication"
                    ),
                    "actual_reconciliation": sources["reconciliation"],
                },
                "eligibility": (
                    "V2 technical masks use complete predictors, known exact-calendar onset, "
                    "current non-excess, no record-review flags and targets inside this panel. "
                    "WITH_CLIMATE also requires all nine monthly variables. These masks "
                    "do not authorize learning. Every learned role requires both origin "
                    "and target before 2025 and must pass require_learnable."
                ),
                "comparison": (
                    "Every national V1 column/key/type/null under the original window, plus "
                    "unchanged extended-window common fields. Regional V1 common-key values "
                    "and nulls are compared with only explicit 2026 target exclusion; known "
                    "numeric container types are reported. Climate tolerance is 1e-10."
                ),
                "limitations": LIMITATIONS,
                "temporal_metadata": {
                    "consumed_year": 2025,
                    "learned_role_admission": "fail_closed",
                    "outside_panel_status": "target_outside_panel",
                },
            }
        ),
        "parity.json": canonical_bytes(
            {
                "comparisons": result["parity"],
                "edge_changes": result["edge_changes"],
                "interpretation": (
                    "Original-window parity is complete; only explicitly listed 2025 "
                    "target maturity changes on extended-window common rows. Regional "
                    "January 2026 target exclusions are separately classified, never imputed."
                ),
            }
        ),
        "temporal_roles.csv": serialize_table(result["temporal_roles"]),
        "provenance.json": canonical_bytes(
            {
                **sources["provenance"],
                "reconciliation": sources["reconciliation"],
                "transformations": [
                    "V2 classify_notifications",
                    "V2 build_review_calendar",
                    "V2 approved climate UNION ALL + aggregate_view",
                    "V2 build_national/compute_y_labels/H5/onset",
                    "V4 maturity and scientific role metadata",
                    "national original-window and regional common-key parity",
                ],
                "real_model_fits": 0,
                "mlflow_writes": 0,
            }
        ),
    }
    body = {
        "schema": "canonical-model-table-national-publication-v4",
        "schema_version": "4.0.0",
        "dataset": DATASET,
        "table": bytes_record(table_bytes),
        **coverage,
        "files": {name: bytes_record(raw) for name, raw in payloads.items()},
        "sources": sources["provenance"]["sources"],
        "generated_at": sources["provenance"]["generated_at"],
        "git_commit": sources["provenance"]["execution"]["git_revision"],
        "parity": {
            "status": "PASS",
            "unexplained_material_differences": 0,
            "national_paired_rows": len(sources["national"]),
            "regional_paired_rows": next(
                r["paired_rows"]
                for r in result["parity"]
                if r["reference"] == "regional_v1_Meta_Tolima"
            ),
            "edge_changes": result["edge_changes"],
        },
        "limitations": LIMITATIONS,
        "redistribution": "pending_license_review",
        "real_model_fits": 0,
        "mlflow_writes": 0,
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    )
    return {"payloads": payloads, "provenance": sources["provenance"]}


class V4BundleDataset(CanonicalBundleDataset):
    """Existing atomic/fsync, hash verification, read-only payload and no-overwrite policy."""
