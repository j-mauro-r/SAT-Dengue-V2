"""Verified national/V1 inputs and isolated EXP-BETA01 V2 artifact publication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.canonical import CanonicalBundleDataset, execution_identity, verify_records
from sat_dengue.datasets.exp_beta01 import BetaSourcesDataset
from sat_dengue.datasets.legacy_preparation.pipeline import read_panel
from sat_dengue.datasets.stage2 import identity, local_path, verified_json
from sat_dengue.experiments.exp_beta01_v2 import FEATURES, summarize
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

PROTOCOL = "docs/product/experiments/EXP-BETA01-V2/protocol.json"
PROTOCOL_IDENTITY = {
    "sha256": "2ebfcc7060cdd39926cb6ff9f6cdf301e436bdd4c067bb0ca8533863b7c950bb",
    "bytes": 5353,
}


def _bundle(relative: str, expected_sha: str, records: dict[str, Any]) -> dict[str, Any]:
    fp = identity(local_path(relative + "/manifest.json"))
    if fp["sha256"] != expected_sha:
        raise DatasetError("V2 pinned source manifest changed")
    manifest = verified_json(relative + "/manifest.json", fp)
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if (
        bytes_record(canonical_bytes(body))["sha256"] != Path(relative).name
        or manifest["bundle_id"] != Path(relative).name
    ):
        raise DatasetError("V2 source bundle identity mismatch")
    if {p.name for p in local_path(relative).iterdir()} != {*manifest["files"], "manifest.json"}:
        raise DatasetError("V2 source bundle membership changed")
    records[relative + "/manifest.json"] = fp
    records.update(manifest["sources"])
    for name, expected in manifest["files"].items():
        if Path(name).name != name:
            raise DatasetError("Unsafe V2 source payload")
        records[relative + "/" + name] = expected
    verify_records(records)
    return manifest


def published_fields(dictionary: dict[str, Any]) -> list[dict[str, Any]]:
    """Interpret serialized Arrow boolean fields strictly as True/False tokens."""
    return [
        {**f, "dtype": {"boolean": "bool", "bool[pyarrow]": "bool"}.get(f["dtype"], f["dtype"])}
        for f in dictionary["columns"]
    ]


class NationalBetaSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    """Read fixed national and frozen historical populations; no fits or rebuilding."""

    def load(self) -> dict[str, Any]:
        protocol = verified_json(PROTOCOL, PROTOCOL_IDENTITY)
        regional = BetaSourcesDataset().load()
        if regional["reference"] is None:
            raise DatasetError("Frozen native R0 is unavailable")
        records = {**regional["provenance"]["sources"], PROTOCOL: PROTOCOL_IDENTITY}
        spec = protocol["sources"]
        national = "data/processed/canonical_model_table_national_v1/" + spec["national_bundle"]
        _bundle(national, spec["national_manifest_sha256"], records)
        dictionary = json.loads(local_path(national + "/columns.json").read_text())
        fields = published_fields(dictionary)
        table = read_panel(
            local_path(national + "/canonical_model_table_national_v1.csv"), {"schema": fields}
        )
        if len(table) != 182886 or table.municipality_code.nunique() != 1122:
            raise DatasetError("National publication coverage changed")
        comparison = pd.read_csv(local_path(national + "/comparison.csv"))
        if comparison.material_unexplained_rows.sum() or comparison.paired_rows.ne(12388).any():
            raise DatasetError("National/BETA scientific reconciliation is blocked")
        historical = "tmp/kedro-migration/exp-beta01-runs/" + spec["g0_bundle"]
        _bundle(historical, spec["g0_manifest_sha256"], records)
        predictions = pd.read_csv(
            local_path(historical + "/predictions.csv"),
            dtype={"municipality_code": str, "department_code": str},
            float_precision="round_trip",
        )
        verify_records(records)
        execution = execution_identity()
        for relative in (
            "src/sat_dengue/experiments/exp_beta01_v2.py",
            "src/sat_dengue/datasets/exp_beta01_v2.py",
            "src/sat_dengue/pipelines/exp_beta01_v2/pipeline.py",
            "src/sat_dengue/canonical/national.py",
            "src/sat_dengue/experiments/exp_beta01.py",
            "src/sat_dengue/experiments/onset.py",
        ):
            execution["code"][relative] = identity(local_path(relative))
        execution["packages"].update(regional["provenance"]["execution"]["packages"])
        return {
            "evidence_type": "authorized_retrospective",
            "protocol": protocol,
            "regional": regional,
            "table": table,
            "national_contract": json.loads(local_path(national + "/contract.json").read_text()),
            "frozen_predictions": predictions,
            "provenance": {"sources": records, "execution": execution},
        }

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("V2 inputs are read-only")

    def _describe(self) -> dict[str, Any]:
        return {
            "protocol": PROTOCOL,
            "identity": PROTOCOL_IDENTITY,
            "selection": "fixed national/G0/R0 identities",
        }


def evaluate(predicted: dict[str, Any]) -> dict[str, Any]:
    """Write native scores, fixed policies and data/code-bound models and metrics."""
    metrics, comparisons, conclusions = summarize(predicted["predictions"], predicted["protocol"])
    payloads = {
        "predictions.csv": serialize_table(
            predicted["predictions"].sort_values(
                ["arm", "horizon", "year", "municipality_code", "year_month"]
            )
        ),
        "metrics.csv": serialize_table(metrics),
        "comparisons.csv": serialize_table(comparisons),
        "conclusions.json": canonical_bytes(conclusions),
        "protocol.json": canonical_bytes(predicted["protocol"]),
        "preflight.json": canonical_bytes({"cells": predicted["preflight"]}),
        "provenance.json": canonical_bytes(predicted["provenance"]),
    }
    ledger = []
    for cell in predicted["cells"]:
        name = f"G1-h{cell['horizon']}-{cell['year']}-OFF.ubj"
        payloads[name] = cell["model_bytes"]
        roles = {}
        for role in ("calibration", "selection", "evaluation"):
            frame = cell["parts"][role][["municipality_code", "year_month", "onset_target"]].copy()
            frame["raw_score"] = cell["raw_scores"][role]
            output = f"scores-h{cell['horizon']}-{cell['year']}-{role}.csv"
            payloads[output] = serialize_table(frame)
            roles[role] = output
        ledger.append(
            {
                "horizon": cell["horizon"],
                "year": cell["year"],
                "model_file": name,
                "predictors": FEATURES,
                "offset": cell["offset"],
                "policy": cell["policy"],
                "scores": roles,
                "audit": cell["audit"],
            }
        )
    payloads["cells.json"] = canonical_bytes({"cells": ledger})
    body = {
        "schema": "exp-beta01-v2-publication-v1",
        "experiment_id": "EXP-BETA01-V2",
        "evidence_type": predicted["evidence_type"],
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "sources": predicted["provenance"]["sources"],
        "real_model_fits": len(ledger)
        if predicted["evidence_type"] == "authorized_retrospective"
        else 0,
        "global_calibrations": len(ledger),
        "historical_model_fits": 0,
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": bytes_record(canonical_bytes(body))["sha256"]}
    )
    return {"payloads": payloads, "provenance": predicted["provenance"]}


class NationalBetaBundleDataset(CanonicalBundleDataset):
    """Use existing atomic hash-verified publication with replacement forbidden."""
