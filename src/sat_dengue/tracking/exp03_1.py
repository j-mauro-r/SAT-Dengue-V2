"""Aggregate-only EXP03.1 tracking projection with no MLflow side effects."""

from __future__ import annotations

import math
import re
from typing import Any

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp01 import digest


def aggregate_projection(bundle: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_1_reporting import validate_bundle

    validate_bundle(bundle)
    aggregate = {
        "schema": "exp03-1-aggregate-tracking-v1",
        "experiment_id": bundle["experiment_id"],
        "scientific_id": bundle["scientific_id"],
        "protocol_sha256": bundle["protocol_sha256"],
        "reuse_decision": bundle["reuse_decision"]["decision"],
        "execution_counts": bundle["execution_plan"]["counts"],
        "metrics": bundle["metrics"],
        "diagnostics": bundle["diagnostics"],
        "G5": bundle["G5"],
        "champion": bundle["champion"],
        "evidence_type": "synthetic_generated_data",
    }
    text = repr(aggregate).lower()
    if "municipality_code" in text or "/users/" in text or "private" in text:
        raise ValueError("Municipal rows or private paths cannot enter EXP03.1 tracking")
    return aggregate


class Exp03_1Tracking:
    """Create one EXP03.1 parent and its complete cell children in local tracking."""

    def __init__(
        self,
        execution: str,
        root: str,
        protocol: dict[str, Any],
        provenance: dict[str, Any] | None = None,
    ) -> None:
        from sat_dengue.tracking.experiments import conceptual_tags
        from sat_dengue.tracking.local import LocalTracking

        self.protocol = protocol
        self.tags = conceptual_tags(protocol["mlflow"]["required_conceptual_tags"])
        self.local = LocalTracking("exp03_1", execution, root)
        self.parent = self.local.parent
        self.children: list[str] = []
        self.cell_run_ids: dict[str, str] = {}
        try:
            expected = protocol["mlflow"]["experiment_name"]
            if self.local.client.get_experiment(self.local.experiment).name != expected:
                raise ValueError("EXP03.1 tracking experiment name differs from protocol")
            key = "protocol." + protocol["experiment_id"]
            pinned = self.local.client.get_experiment(self.local.experiment).tags.get(key)
            if pinned not in (None, digest(protocol)):
                raise ValueError("EXP03.1 protocol is already frozen differently in tracking")
            self.local.client.set_experiment_tag(self.local.experiment, key, digest(protocol))
            for name, value in {
                **self.tags,
                "experiment_id": protocol["experiment_id"],
                "protocol_sha256": digest(protocol),
                "status": "authorized_running",
                "G5": "NOT_APPROVED",
                "champion": "not_selected",
            }.items():
                self.local.client.set_tag(self.parent, name, value)
            provenance = provenance or {}
            self.local.params(
                self.parent,
                {
                    key: provenance[key]
                    for key in (
                        "protocol_sha256",
                        "git_revision",
                        "configuration_sha256",
                        "code_sha256",
                        "data_sha256",
                    )
                    if key in provenance
                }
                | {
                    "profile": "exp03_1",
                    "kind": "real",
                    "evidence_type": "authorized_retrospective",
                    "protocol_version": protocol["version"],
                    "G5": "NOT_APPROVED",
                    "champion": "not_selected",
                },
            )
        except BaseException:
            self.fail()
            raise

    def start_children(self, cells: list[dict[str, Any]], protocol_sha256: str) -> dict[str, Any]:
        from sat_dengue.experiments.exp03_1_contract import cells as frozen_cells

        expected = frozen_cells()
        identity = lambda row: tuple(
            row[name] for name in ("objective", "variant", "family", "horizon", "cut")
        )
        if (
            len(cells) != len(expected)
            or {identity(row) for row in cells} != {identity(row) for row in expected}
            or len(cells) != len({identity(row) for row in cells})
            or protocol_sha256 != digest(self.protocol)
        ):
            raise ValueError("EXP03.1 tracking requires the complete frozen cell grid")
        try:
            for cell in cells:
                cell_id = cell["cell_id"]
                if re.fullmatch(r"[0-9a-f]{64}", cell_id) is None:
                    raise ValueError("Invalid EXP03.1 cell identity")
                tags = {
                    **self.tags,
                    "experiment_id": self.protocol["experiment_id"],
                    "protocol_sha256": protocol_sha256,
                    "pipeline": "exp03_1",
                    "status": "running",
                    "cell_id": cell_id,
                    "variant": cell["variant"],
                    "objective": cell["objective"],
                    "family": cell["family"],
                    "horizon": str(cell["horizon"]),
                    "cut": cell["cut"],
                }
                child = self.local.client.create_run(
                    self.local.experiment,
                    tags={
                        "mlflow.parentRunId": self.parent,
                        "mlflow.runName": (
                            f"EXP031:{cell['objective']}:{cell['variant']}:"
                            f"{cell['family']}:t{cell['horizon']}:{cell['cut']}"
                        ),
                        **tags,
                    },
                ).info.run_id
                self.children.append(child)
                self.local.children.append(child)
                self.cell_run_ids[cell_id] = child
                self.local.params(
                    child,
                    {
                        "family": cell["family"],
                        "horizon": cell["horizon"],
                        "objective": cell["objective"],
                        "window": cell["cut"],
                    },
                )
            return {
                "schema": "exp03-1-mlflow-receipt-v1",
                "parent_run_id": self.parent,
                "child_run_ids": self.children.copy(),
                "cell_run_ids": dict(self.cell_run_ids),
                "child_count": len(self.children),
                "protocol_sha256": protocol_sha256,
            }
        except BaseException:
            self.fail()
            raise

    def finish(
        self,
        receipt: dict[str, Any],
        cells: list[dict[str, Any]],
        manifest: dict[str, Any],
    ) -> None:
        if (
            receipt.get("parent_run_id") != self.parent
            or receipt.get("child_run_ids") != self.children
            or receipt.get("cell_run_ids") != self.cell_run_ids
            or receipt.get("child_count") != len(cells)
            or len(self.children) != 96
        ):
            raise ValueError("EXP03.1 MLflow receipt does not match the complete grid")
        try:
            artifact_root = self.local.root / "receipts"
            artifact_root.mkdir(parents=True, exist_ok=True, mode=0o700)
            artifact = artifact_root / (self.parent + ".json")
            artifact.write_bytes(
                canonical_bytes(
                    {
                        "schema": "bounded-mlflow-lineage-v1",
                        "parameters": {
                            "profile": "exp03_1",
                            "kind": "real",
                            "protocol_sha256": receipt["protocol_sha256"],
                            "bundle_id": manifest["bundle_id"],
                            "manifest_sha256": digest(manifest),
                        },
                        "real_adjustments": 0,
                    }
                )
            )
            self.local.client.log_artifact(self.parent, str(artifact))
            for run_id, cell in zip(self.children, cells, strict=True):
                metric_values = {
                    "average_precision": cell.get("average_precision"),
                    "brier": cell.get("brier"),
                    "false_alerts": cell.get("false_alerts"),
                    "evaluable_rows": cell.get("rows"),
                }
                metrics = {
                    name: float(value)
                    for name, value in metric_values.items()
                    if value is not None and math.isfinite(float(value))
                }
                self.local.metrics(run_id, metrics)
                self.local.client.set_tag(run_id, "status", "pending_validation")
            self.local.client.set_tag(self.parent, "status", "pending_validation")
            self.local.client.set_tag(self.parent, "mlflow_receipt_sha256", digest(receipt))
            self.local.client.set_tag(self.parent, "bundle_id", manifest["bundle_id"])
        except BaseException:
            self.fail()
            raise

    def mark_verified(self, receipt: dict[str, Any]) -> None:
        if (
            receipt.get("parent_run_id") != self.parent
            or receipt.get("child_run_ids") != self.children
            or receipt.get("cell_run_ids") != self.cell_run_ids
            or receipt.get("child_count") != 96
            or self.local.terminal
        ):
            raise ValueError("EXP03.1 cannot verify an incomplete or terminal MLflow receipt")
        try:
            for run_id in self.children:
                self.local.client.set_tag(run_id, "status", "verified")
                self.local.client.set_terminated(run_id, "FINISHED")
            self.local.client.set_tag(self.parent, "status", "verified")
            self.local.client.set_terminated(self.parent, "FINISHED")
            self.local.terminal = True
        except BaseException:
            self.fail()
            raise

    def fail(self) -> None:
        self.local.fail()
