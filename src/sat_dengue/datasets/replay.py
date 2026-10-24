"""Narrow replay persistence: delegate stage publishers, verify checkpoints, commit once."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from kedro.io import AbstractDataset, DatasetError

from sat_dengue.configuration import canonical_bytes, resolve_configuration
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.datasets.replay_identity import (
    CACHED,
    STAGES,
    checkpoint,
    digest,
    immutable_json,
    stage_inputs,
    verify_publication,
)
from sat_dengue.datasets.stage2 import (
    PublishedConfigurationDataset,
    Stage2BundleDataset,
    Stage2ConsolidatedDataset,
    identity,
    local_path,
)


def from_resolved(resolved: dict[str, Any]) -> dict[str, Any]:
    entry = resolved["execution"]["e2e"]
    return {"identity": entry["identity"], "folder": entry["folder"], "mode": entry["mode"]}


class ReplayConfigurationDataset(AbstractDataset[Any, Any]):
    def save(self, data: Any) -> None:
        self._delegate = None
        if data != CACHED:
            entry = data["execution"]["e2e"]
            folder = local_path(entry["folder"]) / "configuration" / entry["stage"]
            self._delegate = PublishedConfigurationDataset(str(folder))
            self._delegate.save(data)

    def load(self) -> Any:
        return CACHED if self._delegate is None else self._delegate.load()

    def _describe(self) -> dict[str, Any]:
        return {"mode": "explicit context-bound immutable snapshot"}


class ReplayConsolidatedDataset(AbstractDataset[Any, Any]):
    def save(self, data: Any) -> None:
        self._delegate = None
        if data == CACHED:
            return
        resolved = data["resolved"]
        context = from_resolved(resolved)
        base = local_path(context["folder"]) / "stages/data"
        self._delegate = Stage2ConsolidatedDataset(str(base))
        receipt = local_path(context["folder"]) / "consolidated-checkpoint.json"
        if receipt.exists():
            old = json.loads(receipt.read_text())
            if (
                old["context_sha256"] != context["identity"]
                or old["configuration_sha256"] != resolved["configuration_sha256"]
                or identity(local_path(old["file"]["path"]))
                != {k: v for k, v in old["file"].items() if k != "path"}
            ):
                raise ValueError("Consolidated checkpoint is stale or corrupted")
            self._delegate._path = local_path(old["file"]["path"])
            self._delegate._identity = old["file"]
        else:
            self._delegate.save(data)
            value = self._delegate.load()["identity"]
            immutable_json(
                receipt,
                {
                    "context_sha256": context["identity"],
                    "configuration_sha256": resolved["configuration_sha256"],
                    "file": value,
                },
            )

    def load(self) -> Any:
        return CACHED if self._delegate is None else self._delegate.load()

    def _describe(self) -> dict[str, Any]:
        return {"mode": "verified consolidated checkpoint; no overwrite"}


class ReplayStageDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def __init__(self, stage: str) -> None:
        if stage not in STAGES:
            raise ValueError("Unknown replay stage")
        self.stage = stage

    def save(self, data: dict[str, Any]) -> None:
        if "reuse" in data:
            self._record = verify_publication(data["reuse"], data["context"])
            return
        resolved = data["resolved"]
        context = from_resolved(resolved)
        base = local_path(context["folder"]) / "stages" / self.stage
        if self.stage == "data":
            delegate: Any = Stage2BundleDataset(str(base))
            delegate.save(data)
            manifest = delegate.load()
            folder = base / manifest["run_id"] / "bundle"
        elif self.stage == "preparation" and context["mode"] == "synthetic":
            from sat_dengue.training_preparation.serialization import bytes_record, json_bytes
            from sat_dengue.training_preparation.workflow import preparation_contract

            preparation_contract(resolved)
            payloads = dict(data["payloads"])
            body = {
                "schema": "sat-dengue-preparation-engineering-v1",
                "configuration_sha256": resolved["configuration_sha256"],
                "files": {n: bytes_record(b) for n, b in payloads.items()},
                "originals": resolved["preparation"],
                "real_model_fits": 0,
                "real_preparer_refits": 0,
            }
            manifest = {**body, "bundle_id": digest(body)}
            payloads["manifest.json"] = json_bytes(manifest)
            folder = publish_bundle(base, manifest["bundle_id"], payloads, existing_policy="error")
            for f in folder.iterdir():
                f.chmod(0o444)
        else:
            from sat_dengue.datasets.evaluation import EvaluationBundleDataset
            from sat_dengue.datasets.preparation import PreparationBundleDataset
            from sat_dengue.datasets.training import TrainingBundleDataset

            publisher: Any = {
                "preparation": PreparationBundleDataset,
                "training": TrainingBundleDataset,
                "evaluation": EvaluationBundleDataset,
            }[self.stage]
            delegate = publisher(str(base))
            delegate.save(data)
            published = delegate.load()
            manifest = published["manifest"]
            folder = local_path(published["path"])
        self._record = {
            "path": str(folder.relative_to(Path.cwd())),
            "manifest": manifest,
            "stage": self.stage,
            "context_sha256": context["identity"],
        }
        checkpoint(self._record, context)

    def load(self) -> dict[str, Any]:
        if not hasattr(self, "_record"):
            raise DatasetError("No explicit replay stage publication")
        return verify_publication(self._record)

    def _describe(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "mode": "immutable native publisher plus complete identity checkpoint",
        }


def assemble_replay(
    context: dict[str, Any],
    data: dict[str, Any],
    preparation: dict[str, Any],
    training: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    records = dict(zip(STAGES, (data, preparation, training, evaluation), strict=True))
    for record in records.values():
        verify_publication(record, context)
    folder = local_path(evaluation["path"])
    audit = json.loads((folder / "audit.json").read_text())
    if (
        audit["G5"] != "NOT_APPROVED"
        or audit["champion"] != "not_selected"
        or any(
            audit[k] != 0
            for k in (
                "real_model_fits",
                "real_preparer_refits",
                "calibrator_fits",
                "threshold_selection",
                "hyperparameter_search",
            )
        )
    ):
        raise ValueError("E2E scientific fitting/decision boundary changed")
    if context["mode"] == "replay":
        from sat_dengue.datasets.replay_parity import evaluation_parity

        evaluation_parity(evaluation)
    resolved = resolve_configuration(stage_inputs(context, "pipeline"), context["operational"])
    return {"context": context, "stages": records, "resolved": resolved, "audit": audit}


class ReplayBundleDataset(AbstractDataset[dict[str, Any], dict[str, Any]]):
    def save(self, data: dict[str, Any]) -> None:
        context = data["context"]
        resolved = data["resolved"]
        records = data["stages"]
        for record in records.values():
            verify_publication(record, context)
        audit = {
            k: data["audit"][k]
            for k in (
                "G5",
                "champion",
                "decisions",
                "real_model_fits",
                "real_preparer_refits",
                "calibrator_fits",
                "threshold_selection",
                "hyperparameter_search",
            )
        }
        audit.update(
            mode=context["mode"],
            synthetic_only=context["mode"] == "synthetic",
            not_historical_reproducibility=True,
        )
        payloads = {
            "audit.json": canonical_bytes(audit),
            "lineage.json": canonical_bytes(records),
            "provenance.json": canonical_bytes(resolved),
        }
        body = {
            "schema": "sat-dengue-composed-replay-v1",
            "mode": context["mode"],
            "context_sha256": context["identity"],
            "configuration_sha256": resolved["configuration_sha256"],
            "files": {
                n: {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}
                for n, b in payloads.items()
            },
            "real_model_fits": 0,
            "real_preparer_refits": 0,
        }
        manifest = {**body, "bundle_id": digest(body)}
        payloads["manifest.json"] = canonical_bytes(manifest)
        self._folder = publish_bundle(
            local_path(context["folder"]) / "publication",
            manifest["bundle_id"],
            payloads,
            existing_policy="reuse_identical",
        )
        self._expected = identity(self._folder / "manifest.json")
        for f in self._folder.iterdir():
            f.chmod(0o444)

    def load(self) -> dict[str, Any]:
        if (
            not hasattr(self, "_folder")
            or identity(self._folder / "manifest.json") != self._expected
        ):
            raise DatasetError("No verified final replay publication")
        manifest = json.loads((self._folder / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        if digest(body) != manifest["bundle_id"] or set(p.name for p in self._folder.iterdir()) != {
            *manifest["files"],
            "manifest.json",
        }:
            raise DatasetError("Final replay identity/membership changed")
        for n, fp in manifest["files"].items():
            if Path(n).name != n or identity(self._folder / n) != fp:
                raise DatasetError("Final replay payload changed")
        resolved = json.loads((self._folder / "provenance.json").read_text())
        if (
            digest({k: v for k, v in resolved.items() if k != "configuration_sha256"})
            != manifest["configuration_sha256"]
            or resolved["execution"]["e2e"]["identity"] != manifest["context_sha256"]
        ):
            raise DatasetError("Final replay configuration binding changed")
        context = from_resolved(resolved)
        stages = json.loads((self._folder / "lineage.json").read_text())
        if set(stages) != set(STAGES):
            raise DatasetError("Final replay stage lineage incomplete")
        for record in stages.values():
            if record["context_sha256"] != manifest["context_sha256"]:
                raise DatasetError("Final replay lineage changed")
            verify_publication(record, context)
        return {
            "path": str(self._folder.relative_to(Path.cwd())),
            "manifest": manifest,
            "stages": stages,
        }

    def _describe(self) -> dict[str, Any]:
        return {"mode": "verified final commit receipt; no implicit latest or bundle copies"}
