"""Closed aggregate-only tracking for revised EXP03; native evidence stays protected."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path
from typing import Any

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import load_protocol
from sat_dengue.experiments.exp03_preflight import OUTPUT_ROOT, safe_path
from sat_dengue.tracking.local import LocalTracking

COUNTER_FIELDS = {
    "real_model_fits",
    "real_preparer_refits",
    "calibrator_fits",
    "synthetic_interface_fits",
}
AGGREGATE_CELL_FIELDS = {
    "variant",
    "objective",
    "family",
    "horizon",
    "window",
    "cell_id",
    "status",
    "model_fitted",
    "metrics",
}
METRIC_FIELDS = {
    "known_outcomes",
    "unknown_outcomes",
    "alerts_with_unknown_outcomes",
    "abstentions",
    "false_positive_rate",
    "onsets",
    "real_onsets",
    "covered_onsets",
    "eligible_onsets",
    "detected_onsets",
    "missed_onsets",
    "missed_episodes",
    "detected_episodes",
    "false_alerts",
    "emitted_alerts",
    "true_positives",
    "false_positives",
    "true_negatives",
    "false_negatives",
    "tp",
    "fp",
    "tn",
    "fn",
    "onset_sensitivity",
    "sensitivity",
    "precision",
    "onset_precision",
    "false_alarm_ratio",
    "far",
    "fpr",
    "false_alerts_per_monitored_municipality_year",
    "false_alerts_per_eligible_municipality_year",
    "false_alerts_per_municipality_year",
    "alert_month_fraction",
    "monitored_exposure",
    "eligible_exposure",
    "common_exposure",
    "average_precision",
    "auroc",
    "brier",
    "prevalence",
    "ece",
    "calibration_slope",
    "calibration_intercept",
    "evaluable_rows",
    "rows",
    "unavailable_outcomes",
    "missing_predictions",
    "coverage_adjusted_sensitivity",
    "nominal_lead_months",
    "actual_lead_months",
}


def expected_grid(design: dict[str, Any]) -> set[tuple[str, str, str, int, str]]:
    """Objective is part of every identity; T+1 excess is never admitted."""
    onset = {
        (v, "onset", f, h, w["id"])
        for v in design["variants"]
        for f in design["families"]
        for h in design["horizons"]
        for w in design["windows"]
    }
    controls = {
        (v, "excess", f, 2, w["id"])
        for v in ("V00", "V09")
        for f in design["families"]
        for w in design["windows"]
    }
    return onset | controls


def cell_identity(row: dict[str, Any]) -> tuple[str, str, str, int, str]:
    return tuple(row[k] for k in ("variant", "objective", "family", "horizon", "window"))


def _number(value: Any) -> bool:
    return value is None or (type(value) in (int, float) and math.isfinite(value))


def metric_projection(values: dict[str, Any]) -> dict[str, Any]:
    """Only named scalars; nested calibration/group/row payloads never escape."""
    return {k: v for k, v in values.items() if k in METRIC_FIELDS and _number(v)}


def validate_execution_counters(result: dict[str, Any], design: dict[str, Any]) -> None:
    """Actual work is counted by phase, independently of evaluation support."""
    children = result["children"]
    counts = result.get("execution_counters")
    if counts is None:
        if not result["synthetic"] and any(c["model_fitted"] for c in children):
            raise ValueError("Scientific EXP03 requires phase execution counters")
        return
    phases = {"development_oof", "terminal_stress_2024", "consumed_2025_benchmark"}
    fields = {
        "model_fits",
        "preparer_fits",
        "calibrator_fits",
        "searches",
        "threshold_selections",
        "kind",
    }
    if not isinstance(counts, dict) or set(counts) != phases:
        raise ValueError("Invalid EXP03 phase execution counters")
    development = {
        w["id"] for w in design["windows"] if w["evidence_type"] == "retrospective_development"
    }
    terminal = {w["id"] for w in design["windows"] if w["evidence_type"] == "retrospective_stress"}
    expected_kind = (
        "synthetic_generated_data" if result["synthetic"] else "authorized_retrospective"
    )
    for phase, windows in (
        ("development_oof", development),
        ("terminal_stress_2024", terminal),
        ("consumed_2025_benchmark", set()),
    ):
        executed = sum(c["model_fitted"] for c in children if c["window"] in windows)
        record = counts[phase]
        if not isinstance(record, dict) or set(record) != fields:
            raise ValueError("Invalid EXP03 phase counter fields")
        if record["kind"] != (
            "inference_only" if phase == "consumed_2025_benchmark" else expected_kind
        ):
            raise ValueError("Invalid EXP03 phase execution kind")
        for key in fields - {"kind"}:
            expected = 0 if key == "searches" else executed
            if type(record[key]) is not int or record[key] != expected:
                raise ValueError(
                    "EXP03 phase counter disagrees with fitted cells: " + phase + "/" + key
                )
    if "searches" in result and (type(result["searches"]) is not int or result["searches"] != 0):
        raise ValueError("EXP03 does not permit hyperparameter searches")
    if "threshold_selections" in result and (
        type(result["threshold_selections"]) is not int
        or result["threshold_selections"] != sum(c["model_fitted"] for c in children)
    ):
        raise ValueError("EXP03 threshold policy counter disagrees with fitted cells")


def validate_result(result: dict[str, Any], provenance: dict[str, Any]) -> None:
    p = load_protocol()
    if result.get("schema") != "exp03-result-v2":
        raise ValueError("Legacy EXP03 result cannot certify revised scope")
    if (
        result.get("experiment_id") != "EXP03"
        or type(result.get("synthetic")) is not bool
        or result.get("G5") != "NOT_APPROVED"
        or result.get("champion") != "not_selected"
        or provenance.get("protocol_sha256") != digest(p)
    ):
        raise ValueError("Invalid EXP03 result identity")
    if result["synthetic"] is False:
        from sat_dengue.experiments.exp03_admission import validate_admission

        validate_admission(provenance)
    expected = expected_grid(p["design"])
    children = result.get("children", [])
    actual = [cell_identity(c) for c in children]
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError("Invalid EXP03 objective-aware child grid")
    if any(type(c.get("model_fitted")) is not bool for c in children):
        raise ValueError("EXP03 requires explicit boolean model_fitted evidence")
    count = sum(c["model_fitted"] for c in children)
    validate_execution_counters(result, p["design"])
    if count and not result.get("contrasts"):
        raise ValueError("Missing revised scientific contrasts")
    for key in COUNTER_FIELDS:
        value = result.get(key)
        target = count if (key == "synthetic_interface_fits") == result["synthetic"] else 0
        if type(value) is not int or value != target:
            raise ValueError("Invalid EXP03 fit count: " + key)
    paired: dict[tuple[Any, ...], list[Any]] = {}
    for c in children:
        columns = p["design"]["variants"][c["variant"]]
        if (
            c["status"] not in {"evaluable", "non_evaluable"}
            or (c["status"] == "evaluable" and not c["model_fitted"])
            or c.get("cell_id")
            != digest(
                dict(
                    zip(
                        ("variant", "objective", "family", "horizon", "window"),
                        cell_identity(c),
                        strict=True,
                    )
                )
            )
            or c.get("predictors_sha256") != digest(columns)
            or c.get("number_of_variables") != len(columns)
        ):
            raise ValueError("Invalid EXP03 variant projection or cell identity")
        if c["status"] == "non_evaluable" and not c.get("reason"):
            raise ValueError("Missing non-evaluable reason")
        paired.setdefault((c["family"], c["horizon"], c["window"]), []).append(c)
    for cells in paired.values():
        if any(
            any(c.get(k) != cells[0].get(k) for k in ("cohort_sha256", "role_sha256", "coverage"))
            for c in cells[1:]
        ):
            raise ValueError("EXP03 cohort or roles diverged")
    from sat_dengue.tracking.exp03_contrasts import projection, validate

    validate(projection(result.get("contrasts", [])), p["design"])


def verified_result(publication: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_reporting import validate_bundle

    folder = safe_path(publication["path"])
    if folder.parent != safe_path(OUTPUT_ROOT, OUTPUT_ROOT):
        raise ValueError("Invalid publication parent")
    manifest = validate_bundle(folder)
    if manifest != publication["manifest"] or manifest.get("bundle_id") != folder.name:
        raise ValueError("Invalid publication manifest identity")
    result = json.loads((folder / "result.json").read_text())
    provenance = json.loads((folder / "provenance.json").read_text())
    validate_result(result, provenance)
    return {"result": result, "provenance": provenance, "manifest": manifest}


def frontier_artifact(verified: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.tracking.exp03_contrasts import projection

    result = verified["result"]
    cells = [
        {
            **{k: c[k] for k in AGGREGATE_CELL_FIELDS - {"metrics"}},
            "metrics": metric_projection(c.get("metrics", {})),
        }
        for c in result["children"]
    ]
    contrasts = projection(result.get("contrasts", []))
    value = {
        "schema": "exp03-frontier-mlflow-v2",
        "parameters": parameters,
        "cells": cells,
        "frontier_sha256": digest(cells),
        "contrasts": contrasts,
        "contrasts_sha256": digest(contrasts),
        "counters": {k: result[k] for k in COUNTER_FIELDS if k in result},
    }
    validate_frontier_artifact(value)
    return value


def validate_frontier_artifact(value: dict[str, Any]) -> None:
    from sat_dengue.tracking.exp03_contrasts import validate
    from sat_dengue.tracking.local import allowed_parameters

    if (
        set(value)
        != {
            "schema",
            "parameters",
            "cells",
            "frontier_sha256",
            "contrasts",
            "contrasts_sha256",
            "counters",
        }
        or value["schema"] != "exp03-frontier-mlflow-v2"
    ):
        raise ValueError("Invalid EXP03 aggregate schema")
    allowed_parameters(value["parameters"])
    p = load_protocol()
    if value["parameters"].get("protocol_sha256") != digest(p) or not value["parameters"].get(
        "bundle_id"
    ):
        raise ValueError("Unbound aggregate identity")
    cells = value["cells"]
    if not isinstance(cells, list) or any(
        not isinstance(c, dict) or set(c) != AGGREGATE_CELL_FIELDS for c in cells
    ):
        raise ValueError("Invalid aggregate cells")
    if (
        len(cells) != len(expected_grid(p["design"]))
        or {cell_identity(c) for c in cells} != expected_grid(p["design"])
        or digest(cells) != value["frontier_sha256"]
    ):
        raise ValueError("Changed aggregate grid identity")
    for c in cells:
        if type(c["model_fitted"]) is not bool or (
            c["status"] == "evaluable" and not c["model_fitted"]
        ):
            raise ValueError("Invalid aggregate model_fitted evidence")
        if c["cell_id"] != digest(
            dict(
                zip(
                    ("variant", "objective", "family", "horizon", "window"),
                    cell_identity(c),
                    strict=True,
                )
            )
        ) or c["status"] not in {
            "evaluable",
            "non_evaluable",
        }:
            raise ValueError("Invalid aggregate cell identity")
        metrics = c["metrics"]
        if (
            not isinstance(metrics, dict)
            or not set(metrics) <= METRIC_FIELDS
            or any(not _number(v) for v in metrics.values())
        ):
            raise ValueError("Unapproved aggregate metric")
    if (
        not isinstance(value["counters"], dict)
        or not set(value["counters"]) <= COUNTER_FIELDS
        or any(type(v) is not int or v < 0 for v in value["counters"].values())
    ):
        raise ValueError("Invalid aggregate execution counters")
    kind = value["parameters"].get("kind")
    if kind not in {"real", "synthetic"}:
        raise ValueError("Aggregate execution kind is required")
    count = sum(c["model_fitted"] for c in cells)
    for key, actual in value["counters"].items():
        expected = count if (key == "synthetic_interface_fits") == (kind == "synthetic") else 0
        if actual != expected:
            raise ValueError("Aggregate fit counter does not match execution kind")
    validate(value["contrasts"], p["design"])
    if digest(value["contrasts"]) != value["contrasts_sha256"]:
        raise ValueError("Changed contrast identity")


class Exp03Tracking(LocalTracking):
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
                    or self.pipeline not in {"exp03", "exp03_synthetic"}
                    or self.conceptual.get("experiment_id") != "EXP03"
                ):
                    raise ValueError("Invalid EXP03 tracking state")
                verified = verified_result(publication)
                result = verified["result"]
                provenance = verified["provenance"]
                if self.pipeline != ("exp03_synthetic" if result["synthetic"] else "exp03"):
                    raise ValueError("Synthetic/real EXP03 tracking purpose mismatch")
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
                    filter_string="tags.pipeline = 'exp03' and params.bundle_id = '"
                    + common["bundle_id"]
                    + "' and attributes.status = 'FINISHED'",
                )
                if previous:
                    raise ValueError("EXP03 bundle already tracked")
                self.params(self.parent, common)
                for c in result["children"]:
                    tags = {
                        **self.conceptual,
                        "pipeline": "exp03",
                        "mlflow.parentRunId": self.parent,
                        "variant": c["variant"],
                        "objective": c["objective"],
                        "cell_id": c.get(
                            "cell_id",
                            digest([c["variant"], c["family"], c["horizon"], c["window"]]),
                        ),
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
                            "objective": c["objective"],
                        },
                    )
                    if not result["synthetic"]:
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

                with tempfile.TemporaryDirectory(prefix=".exp03-frontier-", dir=self.root) as stage:
                    path = safe_path(str(Path(stage) / (self.parent + ".json")))
                    path.write_bytes(canonical_bytes(artifact))
                    self.client.log_artifact(self.parent, str(path))
                self.client.set_tag(
                    self.parent, "exp03.frontier_sha256", artifact["frontier_sha256"]
                )
                self.client.set_tag(self.parent, "status", "verified")
                self.client.set_terminated(self.parent, "FINISHED")
                self.terminal = True
                return str(self.parent)
        except BaseException:
            self.fail()
            raise
