"""Aggregate-only EXP02 tracking; full validated frontiers stay in native bundles."""

from __future__ import annotations

import json
import math
import tempfile
from itertools import product
from pathlib import Path
from typing import Any

from sat_dengue.datasets.stage2 import identity
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp02 import VARIANTS, load_protocol
from sat_dengue.experiments.exp02_preflight import OUTPUT_ROOT, safe_path
from sat_dengue.tracking.local import LocalTracking


def validate_result(result: dict[str, Any], provenance: dict[str, Any]) -> None:
    p = load_protocol()
    if (
        result["schema"] != "exp02-result-v1"
        or result["experiment_id"] != "EXP02"
        or type(result["synthetic"]) is not bool
        or result["G5"] != "NOT_APPROVED"
        or result["champion"] != "not_selected"
        or provenance["protocol_sha256"] != digest(p)
    ):
        raise ValueError("Invalid EXP02 result identity")
    expected = set(
        product(
            VARIANTS, p["design"]["families"], (1, 2), [w["id"] for w in p["design"]["windows"]]
        )
    )
    actual = [(c["variant"], c["family"], c["horizon"], c["window"]) for c in result["children"]]
    if len(actual) != 108 or set(actual) != expected:
        raise ValueError("Invalid EXP02 child grid")
    count = sum(c["status"] == "evaluable" for c in result["children"])
    for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits"):
        if type(result[k]) is not int or result[k] != (0 if result["synthetic"] else count):
            raise ValueError("Invalid EXP02 fit count")
    paired: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for c in result["children"]:
        if (
            c["objective"] != "onset"
            or c["status"] not in ("evaluable", "non_evaluable")
            or c["predictors_sha256"] != digest(p["design"]["variants"][c["variant"]])
            or c["number_of_variables"] != len(p["design"]["variants"][c["variant"]])
        ):
            raise ValueError("Invalid EXP02 variant projection")
        paired.setdefault((c["family"], c["horizon"], c["window"]), []).append(c)
    for cells in paired.values():
        for c in cells[1:]:
            if any(c[k] != cells[0][k] for k in ("cohort_sha256", "role_sha256", "coverage")):
                raise ValueError("EXP02 cohort or roles diverged")
        full = next(c for c in cells if c["variant"] == "full")
        for c in cells:
            if c["status"] == "non_evaluable":
                if not c["reason"] or c["frontier"]:
                    raise ValueError("Invalid non-evaluable cell")
            elif [r["selection_false_alert_budget"] for r in c["frontier"]] != [
                r["selection_false_alert_budget"] for r in full["frontier"]
            ]:
                raise ValueError("Budget frontiers differ")


def verified_result(publication: dict[str, Any]) -> dict[str, Any]:
    folder = safe_path(publication["path"])
    if folder.parent != safe_path(OUTPUT_ROOT, OUTPUT_ROOT):
        raise ValueError("Invalid publication parent")
    manifest = json.loads((folder / "manifest.json").read_text())
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if (
        manifest != publication["manifest"]
        or digest(body) != folder.name
        or manifest["bundle_id"] != folder.name
        or set(manifest["files"]) != {"result.json", "provenance.json"}
        or {p.name for p in folder.iterdir()} != {"manifest.json", "result.json", "provenance.json"}
    ):
        raise ValueError("Invalid publication manifest")
    for name, expected in manifest["files"].items():
        if identity(safe_path(str(folder / name))) != expected:
            raise ValueError("Changed publication payload")
    result = json.loads((folder / "result.json").read_text())
    provenance = json.loads((folder / "provenance.json").read_text())
    validate_result(result, provenance)
    return {"result": result, "provenance": provenance, "manifest": manifest}


FRONTIER_FIELDS = {
    "selection_false_alert_budget",
    "onset_sensitivity",
    "paired_onset_sensitivity_difference",
    "false_alerts",
    "full_realized_false_alerts",
    "uncertainty_status",
}
CELL_FIELDS = {"variant", "family", "horizon", "window", "status", "frontier"}


def frontier_artifact(verified: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """One parent aggregate projection; no municipality dimensions or raw rows."""
    cells = []
    for child in verified["result"]["children"]:
        cells.append(
            {
                **{k: child[k] for k in CELL_FIELDS - {"frontier"}},
                "frontier": [
                    {
                        **{k: row[k] for k in FRONTIER_FIELDS - {"uncertainty_status"}},
                        "uncertainty_status": row["paired_interval"]["status"],
                    }
                    for row in child["frontier"]
                ],
            }
        )
    value = {
        "schema": "exp02-frontier-mlflow-v1",
        "parameters": parameters,
        "frontier_sha256": digest(cells),
        "cells": cells,
    }
    validate_frontier_artifact(value)
    return value


def validate_frontier_artifact(value: dict[str, Any]) -> None:
    """Closed aggregate schema enforced again by the safe artifact repository."""
    from sat_dengue.tracking.local import allowed_parameters

    p = load_protocol()
    if (
        set(value) != {"schema", "parameters", "frontier_sha256", "cells"}
        or value["schema"] != "exp02-frontier-mlflow-v1"
    ):
        raise ValueError("Invalid EXP02 aggregate schema")
    allowed_parameters(value["parameters"])
    if value["parameters"].get("protocol_sha256") != digest(p) or not value["parameters"].get(
        "bundle_id"
    ):
        raise ValueError("Unbound aggregate identity")
    cells = value["cells"]
    expected = set(
        product(
            VARIANTS, p["design"]["families"], (1, 2), [w["id"] for w in p["design"]["windows"]]
        )
    )
    if (
        not isinstance(cells, list)
        or len(cells) != 108
        or any(not isinstance(c, dict) or set(c) != CELL_FIELDS for c in cells)
    ):
        raise ValueError("Invalid aggregate cells")
    if {
        (c["variant"], c["family"], c["horizon"], c["window"]) for c in cells
    } != expected or digest(cells) != value["frontier_sha256"]:
        raise ValueError("Changed aggregate identity")
    for cell in cells:
        if cell["status"] not in {"evaluable", "non_evaluable"} or not isinstance(
            cell["frontier"], list
        ):
            raise ValueError("Invalid aggregate availability")
        if cell["status"] == "non_evaluable" and cell["frontier"]:
            raise ValueError("Non-evaluable frontier")
        for budget, row in enumerate(cell["frontier"]):
            if (
                set(row) != FRONTIER_FIELDS
                or row["selection_false_alert_budget"] != budget
                or row["uncertainty_status"] != "insufficient_cluster_support"
            ):
                raise ValueError("Invalid aggregate frontier")
            for k in ("false_alerts", "full_realized_false_alerts"):
                if type(row[k]) is not int or row[k] < 0:
                    raise ValueError("Invalid aggregate count")
            for k in ("onset_sensitivity", "paired_onset_sensitivity_difference"):
                v = row[k]
                if v is not None and (
                    type(v) not in (int, float)
                    or not math.isfinite(v)
                    or not (-1 if k.startswith("paired") else 0) <= v <= 1
                ):
                    raise ValueError("Invalid aggregate metric")


class Exp02Tracking(LocalTracking):
    def initialize_ablation(self, provenance: dict[str, Any]) -> None:
        common = {
            k: provenance[k]
            for k in (
                "protocol_sha256",
                "git_revision",
                "configuration_sha256",
                "code_sha256",
                "environment_sha256",
            )
        }
        common["input_sha256"] = provenance["data_version"]
        common["data_sha256"] = provenance["data_sha256"]
        common.update(
            cohort="non_excess_at_t",
            kind="real",
            evidence_type="authorized_retrospective_experiment",
        )
        self.params(self.parent, common)
        self.client.set_tag(self.parent, "purpose", "authorized_retrospective_experiment")

    def finish_ablation(self, publication: dict[str, Any]) -> str:
        try:
            with self._lock():
                if (
                    self.terminal
                    or self.pipeline not in {"exp02", "exp02_synthetic"}
                    or self.conceptual.get("experiment_id") != "EXP02"
                ):
                    raise ValueError("Invalid EXP02 tracking state")
                verified = verified_result(publication)
                result = verified["result"]
                provenance = verified["provenance"]
                if self.pipeline != ("exp02_synthetic" if result["synthetic"] else "exp02"):
                    raise ValueError("Synthetic/real EXP02 tracking purpose mismatch")
                common = {
                    k: provenance[k]
                    for k in (
                        "protocol_sha256",
                        "git_revision",
                        "data_version",
                        "configuration_sha256",
                        "code_sha256",
                        "environment_sha256",
                    )
                }
                common["input_sha256"] = common.pop("data_version")
                common.update(
                    protocol_version=load_protocol()["version"],
                    cohort="non_excess_at_t",
                    kind="synthetic" if result["synthetic"] else "real",
                    evidence_type="synthetic_interface_probe"
                    if result["synthetic"]
                    else "authorized_retrospective_experiment",
                    bundle_id=verified["manifest"]["bundle_id"],
                )
                previous = self.client.search_runs(
                    [self.experiment],
                    filter_string="tags.pipeline = 'exp02' and params.bundle_id = '"
                    + common["bundle_id"]
                    + "' and attributes.status = 'FINISHED'",
                )
                if previous:
                    raise ValueError("EXP02 bundle already tracked")
                self.params(self.parent, common)
                for c in result["children"]:
                    tags = {
                        **self.conceptual,
                        "pipeline": "exp02",
                        "mlflow.parentRunId": self.parent,
                        "variant": c["variant"],
                        "family": c["family"],
                        "horizon": str(c["horizon"]),
                        "window": c["window"],
                        "purpose": "synthetic_interface_probe"
                        if result["synthetic"]
                        else "authorized_retrospective_experiment",
                        "evidence_type": c["evidence_type"],
                        "status": c["status"],
                    }
                    run = self.client.create_run(self.experiment, tags=tags).info.run_id
                    self.children.append(run)
                    self.params(
                        run,
                        {
                            **common,
                            "family": c["family"],
                            "horizon": c["horizon"],
                            "window": c["window"],
                            "seed": c["seed"],
                            "objective": "onset",
                        },
                    )
                    self.metrics(
                        run,
                        {
                            k: float(c[k])
                            for k in ("average_precision", "brier")
                            if c.get(k) is not None
                        },
                    )
                    self.client.set_terminated(run, "FINISHED")
                artifact = frontier_artifact(verified, common)
                # Existing safe uploader accepts only generated parent-id receipts.
                # Remove staging after upload; the artifact lives only on the parent.
                from sat_dengue.configuration import canonical_bytes

                with tempfile.TemporaryDirectory(prefix=".exp02-frontier-", dir=self.root) as stage:
                    path = safe_path(str(Path(stage) / (self.parent + ".json")))
                    path.write_bytes(canonical_bytes(artifact))
                    self.client.log_artifact(self.parent, str(path))
                self.client.set_tag(
                    self.parent, "exp02.frontier_sha256", artifact["frontier_sha256"]
                )
                self.client.set_tag(self.parent, "status", "verified")
                self.client.set_terminated(self.parent, "FINISHED")
                self.terminal = True
                return str(self.parent)
        except BaseException:
            self.fail()
            raise
