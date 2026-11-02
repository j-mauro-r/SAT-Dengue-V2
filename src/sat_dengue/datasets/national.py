"""Pinned national sources and independent immutable canonical publication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.canonical.national import (
    aggregate_view,
    build_national,
    compare_baseline,
    eligibility_report,
)
from sat_dengue.configuration import NATIONAL_AUTHORITY, canonical_bytes, validate_parameters
from sat_dengue.datasets.canonical import CanonicalBundleDataset, execution_identity, verify_records
from sat_dengue.datasets.exp_beta01 import PROTOCOL_PATH, PROTOCOL_SHA256
from sat_dengue.datasets.legacy_preparation.pipeline import read_panel
from sat_dengue.datasets.stage2 import identity, local_path, verified_json
from sat_dengue.experiments.exp_beta01 import role_parts
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

STEP1 = "data/interim/canonical-nacional-data/aa25e8cee5fd9cdaa4bf/execution_summary.json"
STEP2 = "data/interim/canonical-nacional-data/climate_step2_v1/climate_union_manifest.json"
PINS = {
    STEP1: {
        "sha256": "a6728996e29fb47830da56ec6b0537b58887c14d6455dc0c95fc736bfb93f2d6",
        "bytes": 7946,
    },
    STEP2: {
        "sha256": "f4daa2141147a33078616cb537b99b295911885d71bbf6bd465e017342d5a92c",
        "bytes": 8427,
    },
}


def _record(record: dict[str, Any]) -> dict[str, Any]:
    return {k: record[k] for k in ("sha256", "bytes")}


class NationalSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Verify exactly the approved executions; never select a newest local folder."""

    def load(self) -> dict[str, Any]:
        contract = verified_json(NATIONAL_AUTHORITY["path"], NATIONAL_AUTHORITY["identity"])
        step1 = verified_json(STEP1, PINS[STEP1])
        step2 = verified_json(STEP2, PINS[STEP2])
        if (
            step1["execution_id"] != contract["sources"]["step1_execution"]
            or step1["source_preservation"] != "PASS"
            or step1["status"] != "READY_WITH_LIMITATIONS"
            or step2["status"] != "STEP2_APPROVED_WITH_LIMITATIONS"
            or step2["view"]["operation"] != "UNION ALL"
            or step2["counts"]["logical_union"] != 7786680
            or step2["counts"]["overlapping_keys"] != 0
        ):
            raise DatasetError("National source execution contract changed")
        records = {**PINS, NATIONAL_AUTHORITY["path"]: NATIONAL_AUTHORITY["identity"]}
        protocol_record = identity(local_path(PROTOCOL_PATH))
        if protocol_record["sha256"] != PROTOCOL_SHA256:
            raise DatasetError("BETA chronology protocol changed")
        records[PROTOCOL_PATH] = protocol_record
        for entry in step1["sources"]:
            records[entry["source"]] = _record(entry)
        for meta in step1["outputs"].values():
            records[meta["path"]] = _record(meta)
        for relative, meta in step2["sources"].items():
            records[relative] = _record(meta)
        for meta in step2["outputs"].values():
            records[meta["path"]] = _record(meta)
        root = "data/processed/canonical_model_table_v1/" + contract["sources"]["beta_bundle"]
        beta_manifest = identity(local_path(root + "/manifest.json"))
        if beta_manifest["sha256"] != contract["sources"]["beta_manifest_sha256"]:
            raise DatasetError("BETA reference manifest changed")
        manifest = verified_json(root + "/manifest.json", beta_manifest)
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if bytes_record(canonical_bytes(body))["sha256"] != contract["sources"]["beta_bundle"]:
            raise DatasetError("Invalid BETA reference publication")
        if {p.name for p in local_path(root).iterdir()} != {*manifest["files"], "manifest.json"}:
            raise DatasetError("BETA reference publication membership changed")
        records[root + "/manifest.json"] = beta_manifest
        records.update(manifest["sources"])
        for name, fp in manifest["files"].items():
            if Path(name).name != name:
                raise DatasetError("Unsafe BETA payload name")
            records[root + "/" + name] = fp
        verify_records(records)
        dictionary = json.loads(local_path(root + "/columns.json").read_text())
        fields = [
            {**f, "dtype": {"boolean": "bool"}.get(f["dtype"], f["dtype"])}
            for f in dictionary["columns"]
        ]
        baseline = read_panel(
            local_path(root + "/canonical_model_table_v1.csv"), {"schema": fields}
        )
        calendar = pd.read_csv(
            local_path(step1["outputs"]["municipality_month"]["path"]),
            dtype={"municipality_code": str, "department_code": str},
        )
        reconciliation = pd.read_csv(local_path(step1["outputs"]["record_reconciliation"]["path"]))
        accepted = int(reconciliation.loc[reconciliation.accepted, "notifications"].sum())
        unresolved = int(
            reconciliation.loc[
                reconciliation.invalid_territory & ~reconciliation.outside_review_window,
                "notifications",
            ].sum()
        )
        if accepted != 1328152 or unresolved != 5663:
            raise DatasetError("Approved national notification reconciliation changed")
        climate_sources = step2["view"]["sources"]
        if climate_sources != [
            "data/raw/google_earth_engine.csv",
            "data/sources/google_earth_engine_2020_national_gap/google_earth_engine_2020_01_national_gap.csv",
        ]:
            raise DatasetError("Unexpected climate union source")

        def chunks() -> Any:
            for relative in climate_sources:
                for frame in pd.read_csv(
                    local_path(relative), dtype=str, keep_default_na=False, chunksize=250000
                ):
                    if list(frame) != step2["columns"]:
                        raise DatasetError("Climate source schema changed")
                    yield frame

        monthly = aggregate_view(chunks(), contract["window"]["start"], contract["window"]["end"])
        if len(monthly) != contract["window"]["rows"]:
            raise DatasetError("Monthly climate grid does not cover the national calendar")
        verify_records(records)
        execution = execution_identity()
        for relative in (
            "src/sat_dengue/canonical/national.py",
            "src/sat_dengue/datasets/national.py",
            "src/sat_dengue/pipelines/national/pipeline.py",
            "src/sat_dengue/experiments/onset.py",
            "src/sat_dengue/experiments/exp_beta01.py",
        ):
            execution["code"][relative] = identity(local_path(relative))
        return {
            "calendar": calendar,
            "monthly": monthly,
            "baseline": baseline,
            "contract": contract,
            "protocol": verified_json(PROTOCOL_PATH, protocol_record),
            "provenance": {
                "sources": records,
                "execution": execution,
                "accepted_notifications": accepted,
                "unassigned_territorial_notifications": unresolved,
            },
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("National sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"executions": list(PINS), "selection": "explicit identities, no latest"}


def assemble_national(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Publish only after scientific reconciliation and horizon-specific eligibility."""
    operational = validate_parameters(parameters)
    if operational != {"profile": "canonical_model_table_national_v1", "tracking": "disabled"}:
        raise ValueError("National construction requires its own disabled-tracking profile")
    table, schema = build_national(
        sources["calendar"], sources["monthly"], sources["baseline"], sources["contract"]
    )
    comparison = compare_baseline(table, sources["baseline"])
    if comparison.material_unexplained_rows.sum():
        bad = comparison.loc[comparison.material_unexplained_rows.gt(0)]
        raise DatasetError(f"STEP3_BLOCKED: unexplained BETA differences: {bad.to_dict('records')}")
    eligibility = eligibility_report(table)
    role_coverage = []
    protocol = sources["protocol"]
    for h in (1, 2):
        for view in ("g1_no_climate", "g1_with_climate"):
            cohort = table.loc[table[f"{view}_t{h}"]].copy()
            cohort["target_month"] = cohort[f"target_period_t{h}"]
            cohort["onset_target"] = cohort[f"onset_T{h}"]
            for year in protocol["evaluation_years"]:
                audit = role_parts(cohort, year, protocol)["audit"]
                for role, values in audit.items():
                    role_coverage.append(
                        {
                            "horizon": h,
                            "view": view,
                            "evaluation_year": year,
                            "role": role,
                            **values,
                        }
                    )
    payloads = {
        "canonical_model_table_national_v1.csv": serialize_table(table),
        "contract.json": canonical_bytes(sources["contract"]),
        "columns.json": canonical_bytes(schema),
        "coverage.json": canonical_bytes(eligibility),
        "comparison.csv": serialize_table(comparison),
        "temporal_roles.csv": serialize_table(pd.DataFrame(role_coverage)),
        "eligibility_by_department_year.csv": serialize_table(
            table.assign(origin_year=table.year_month.str[:4])
            .groupby(["department_code", "origin_year"], as_index=False)[
                [
                    "climate_eligible",
                    *(
                        f"{n}_t{h}"
                        for h in (1, 2)
                        for n in ("epidemiologically_eligible", "g1_no_climate", "g1_with_climate")
                    ),
                ]
            ]
            .sum()
        ),
        "provenance.json": canonical_bytes({**sources["provenance"], "operational": operational}),
    }
    body = {
        "schema": "canonical-model-table-national-publication-v1",
        "dataset": "canonical_model_table_national_v1",
        "status": "STEP3_APPROVED_WITH_LIMITATIONS",
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": sources["provenance"]["sources"],
        "real_model_fits": 0,
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    )
    return {"payloads": payloads, "provenance": sources["provenance"]}


class NationalBundleDataset(CanonicalBundleDataset):
    """Reuse the existing atomic publication, integrity and no-overwrite controls."""
