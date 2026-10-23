"""Lazy read-only frozen sources and atomic, immutable evaluation publications."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.datasets.stage2 import identity, local_path
from sat_dengue.datasets.training import require_modeling
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes, serialize_table


class FrozenEvaluationSourcesDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def load(self) -> dict[str, Any]:
        require_modeling()
        from .evaluation_legacy import FrozenEvaluationLoader

        if not hasattr(self, "_cached"):
            self._cached = FrozenEvaluationLoader().load()
        return self._cached

    def save(self, data: dict[str, Any]) -> None:
        raise DatasetError("Frozen evaluation sources are read-only")

    def _describe(self) -> dict[str, Any]:
        return {"mode": "explicit frozen identities; inference only"}


def assemble_payloads(
    result: dict[str, Any],
    development: dict[str, Any],
    sources: dict[str, Any],
    resolved: dict[str, Any],
) -> dict[str, Any]:
    from sat_dengue.final_evaluation.parity import assert_table_parity
    from sat_dengue.final_evaluation.workflow import apply_decision_policy, validate_sources

    validate_sources(sources, resolved)
    if sources["mode"] == "replay":
        if set(sources["reference"]) != set(result["tables"]):
            raise ValueError("Frozen evaluation tables incomplete")
        for name, expected in sources["reference"].items():
            try:
                assert_table_parity(
                    expected, result["tables"][name], exact_floats=name == "predictions.csv"
                )
            except (ValueError, AssertionError) as error:
                raise ValueError("Frozen output parity failed: " + name) from error
    expected_decisions = apply_decision_policy(result, resolved, sources)
    if any(result[n] != expected_decisions[n] for n in ("decisions", "G5", "champion")):
        raise ValueError("Decision/metrics/policy inconsistency")
    tables = {
        **result["tables"],
        **{"development_" + n: f for n, f in development.get("tables", {}).items()},
    }
    payloads = {n: serialize_table(frame) for n, frame in tables.items()}
    audit = {k: v for k, v in result.items() if k != "tables"}
    audit["development"] = {k: v for k, v in development.items() if k != "tables"}
    audit["consumed_2025_cannot_fit_tune_select"] = True
    payloads.update({"audit.json": json_bytes(audit), "provenance.json": json_bytes(resolved)})
    return {"payloads": payloads, "resolved": resolved, "mode": sources["mode"]}


class EvaluationBundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, filepath: str) -> None:
        self._storage = local_path(filepath)

    def save(self, data: dict[str, Any]) -> None:
        require_modeling()
        from sat_dengue.final_evaluation.workflow import evaluation_contract

        mode = data["mode"]
        resolved = data["resolved"]
        evaluation_contract(resolved, mode)
        if mode == "replay":
            from .evaluation_legacy import NATIVE, checked_evaluation_bundle, no_adjustment

            with no_adjustment():
                for name in NATIVE:
                    checked_evaluation_bundle(name)
                for name, expected in resolved["evaluation"]["source_provenance"][
                    "source_inputs"
                ].items():
                    if identity(local_path(name)) != expected:
                        raise DatasetError("Frozen source changed before publication")
        payloads = dict(data["payloads"])
        audit = json.loads(payloads["audit.json"])
        if (
            any(
                audit[k] != 0
                for k in (
                    "real_model_fits",
                    "real_preparer_refits",
                    "calibrator_fits",
                    "threshold_selection",
                    "hyperparameter_search",
                )
            )
            or audit["G5"] != "NOT_APPROVED"
            or audit["champion"] != "not_selected"
        ):
            raise DatasetError("Scientific fitting/decision boundary changed")
        body = {
            "schema": "sat-dengue-evaluation-engineering-v1",
            "mode": mode,
            "configuration_sha256": resolved["configuration_sha256"],
            "files": {n: bytes_record(raw) for n, raw in payloads.items()},
            "real_model_fits": 0,
            "real_preparer_refits": 0,
        }
        bundle_id = bytes_record(canonical_bytes(body))["sha256"]
        payloads["manifest.json"] = json_bytes({**body, "bundle_id": bundle_id})
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
            raise DatasetError("No explicit verified evaluation publication")
        manifest = json.loads((self._published / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if bytes_record(canonical_bytes(body))["sha256"] != manifest["bundle_id"] or {
            p.name for p in self._published.iterdir()
        } != {*manifest["files"], "manifest.json"}:
            raise DatasetError("Evaluation publication identity/membership changed")
        for name, expected in manifest["files"].items():
            if Path(name).name != name or identity(self._published / name) != expected:
                raise DatasetError("Evaluation publication payload changed")
        return {"path": str(self._published.relative_to(Path.cwd())), "manifest": manifest}

    def _describe(self) -> dict[str, Any]:
        return {
            "filepath": str(self._storage),
            "publication": "atomic immutable; no implicit latest",
        }
