"""Closed EXP02 aggregate projection; complete private outputs stay in the native bundle."""

from __future__ import annotations

import json
import math
import re
from itertools import product
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.stage2 import identity
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp02_preflight import BINDINGS, authorize, load_protocol, safe_path
from sat_dengue.tracking.local import LocalTracking, allowed_parameters

LABEL_METRICS = {
    "rows",
    "state_evaluable_rows",
    "onset_evaluable_rows",
    "common_state_rows",
    "common_onset_rows",
    "excess_positive_rows",
    "onset_count",
    "episode_count",
    "p75_zero_rows",
}
PROBABILITY_METRICS = {
    "own_average_precision",
    "own_brier",
    "anchor_average_precision",
    "anchor_brier",
    "own_calibration_error",
    "anchor_calibration_error",
}
CHANGE_METRICS = {
    "excess_paired_rows",
    "excess_changed",
    "excess_zero_to_one",
    "excess_one_to_zero",
    "onset_paired_rows",
    "onset_changed",
    "onset_zero_to_one",
    "onset_one_to_zero",
    "fragmented_reference_episodes",
    "merged_variant_episodes",
    "ambiguous_fragmentation",
    "ambiguous_merging",
}


def validate_result(result: dict[str, Any], provenance: dict[str, Any]) -> None:
    design = load_protocol()["design"]
    windows = [w["id"] for w in design["windows"]]
    labels, predictive = result["stability"]["children"], result["predictive"]["children"]
    if (
        result["schema"] != "exp02-result-v1"
        or result["experiment_id"] != "EXP02"
        or result["G5"] != "NOT_APPROVED"
        or result["champion"] != "not_selected"
        or result["evidence_type"] not in {"synthetic_interface_probe", "authorized_retrospective"}
        or provenance["protocol_sha256"] != digest(load_protocol())
        or provenance["code_sha256"] != digest(provenance["code"])
        or provenance["environment_sha256"] != digest(provenance["runtime"])
        or len(labels) != 9
        or {(c["history_years"], c["window"]) for c in labels} != set(product((5, 7, 9), windows))
        or len(predictive) != 54
        or {(c["history_years"], c["window"], c["family"], c["horizon"]) for c in predictive}
        != set(product((5, 7, 9), windows, design["families"], (1, 2)))
    ):
        raise ValueError("EXP02 result identity or child grid differs")
    synthetic = result["evidence_type"] == "synthetic_interface_probe"
    fitted = sum(c["status"] == "evaluable" for c in predictive)
    if any(
        result["predictive"][k] != (0 if synthetic else fitted)
        for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits")
    ):
        raise ValueError("EXP02 actual adjustment counters differ")
    if result["predictive"]["synthetic_interface_fits"] != (fitted if synthetic else 0):
        raise ValueError("EXP02 synthetic counters differ")
    for window, family, horizon in product(windows, design["families"], (1, 2)):
        arms = [
            c
            for c in predictive
            if (c["window"], c["family"], c["horizon"]) == (window, family, horizon)
        ]
        if any(
            c[k] != arms[0][k]
            for c in arms
            for k in ("cohort_sha256", "role_sha256", "coverage", "status")
        ):
            raise ValueError("EXP02 paired support or predictors differ")
    if set(result["labels"]) != {"5", "7", "9"} or set(result["episodes"]) != {"5", "7", "9"}:
        raise ValueError("EXP02 native labels/episodes missing")
    if any(row["year_month"] >= "2025-01" for rows in result["labels"].values() for row in rows):
        raise ValueError("EXP02 cannot publish consumed 2025")
    canonical_bytes(result)


def verified_result(publication: dict[str, Any]) -> dict[str, Any]:
    folder = safe_path(publication["path"], temporary=True)
    manifest = json.loads(safe_path(str(folder / "manifest.json")).read_text())
    body = {k: v for k, v in manifest.items() if k != "bundle_id"}
    if (
        manifest != publication["manifest"]
        or manifest["schema"] != "exp02-result-manifest-v1"
        or digest(body) != manifest["bundle_id"]
        or folder.name != manifest["bundle_id"]
        or set(manifest["files"]) != {"result.json", "provenance.json"}
        or {p.name for p in folder.iterdir()} != {"manifest.json", *manifest["files"]}
    ):
        raise ValueError("EXP02 manifest changed")
    for name, expected in manifest["files"].items():
        if identity(safe_path(str(folder / name))) != expected:
            raise ValueError("EXP02 publication payload changed")
    result = json.loads(safe_path(str(folder / "result.json")).read_text())
    provenance = json.loads(safe_path(str(folder / "provenance.json")).read_text())
    validate_result(result, provenance)
    return {"result": result, "provenance": provenance, "manifest": manifest}


def _metrics(values: Any, allowed: set[str]) -> None:
    if (
        not isinstance(values, dict)
        or not set(values) <= allowed
        or any(type(v) not in {int, float} or not math.isfinite(v) for v in values.values())
    ):
        raise ValueError("EXP02 tracking accepts only closed finite aggregates")


EPISODE_METRICS = {
    "real_onsets",
    "detected_onsets",
    "useful_lead_months",
    "missed_episodes",
    "detected_episodes",
    "false_alerts",
    "emitted_alerts",
    "onset_sensitivity",
    "onset_precision",
    "false_alarm_ratio",
    "false_alerts_per_municipality_year",
    "evaluable_rows",
    "unavailable_outcomes",
    "missing_predictions",
}


def _nullable_metrics(value: Any, fields: set[str]) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("EXP02 aggregate fields differ")
    _metrics({k: v for k, v in value.items() if v is not None}, fields)


def _interval(value: Any) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"status", "interval"}
        or value["status"] not in {"insufficient_cluster_support", "retrospective_paired"}
    ):
        raise ValueError("EXP02 uncertainty fields differ")
    interval = value["interval"]
    if interval is not None:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError("EXP02 interval differs")
        _metrics({str(k): v for k, v in enumerate(interval)}, {"0", "1"})
    elif value["status"] == "insufficient_cluster_support":
        return


def _calibration(value: Any) -> None:
    if (
        not isinstance(value, dict)
        or set(value) != {"bins", "expected_calibration_error"}
        or len(value["bins"]) != 10
    ):
        raise ValueError("EXP02 calibration fields differ")
    _nullable_metrics(
        {"expected_calibration_error": value["expected_calibration_error"]},
        {"expected_calibration_error"},
    )
    for item in value["bins"]:
        _nullable_metrics(
            item, {"lower", "upper", "count", "mean_probability", "observed_frequency"}
        )


def _predictive_summary(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {"reason", "calibration", "frontier"}:
        raise ValueError("EXP02 predictive summary differs")
    if value["reason"] not in {None, "empty_common_role", "single_class_training_or_calibration"}:
        raise ValueError("EXP02 reason must be a frozen token")
    if value["calibration"] is not None:
        if set(value["calibration"]) != {"own_definition", "fixed_anchor"}:
            raise ValueError("EXP02 calibration target differs")
        for calibration in value["calibration"].values():
            _calibration(calibration)
    for frontier in value["frontier"]:
        if set(frontier) != {
            "selection_false_alert_budget",
            "threshold",
            "own_definition",
            "fixed_anchor",
            "paired_anchor_sensitivity_difference",
            "paired_interval",
        }:
            raise ValueError("EXP02 frontier fields differ")
        _nullable_metrics(
            {
                k: frontier[k]
                for k in (
                    "selection_false_alert_budget",
                    "threshold",
                    "paired_anchor_sensitivity_difference",
                )
            },
            {"selection_false_alert_budget", "threshold", "paired_anchor_sensitivity_difference"},
        )
        for key in ("own_definition", "fixed_anchor"):
            _nullable_metrics(frontier[key], EPISODE_METRICS)
        _interval(frontier["paired_interval"])


def validate_safe_receipt(value: dict[str, Any]) -> None:
    if (
        set(value) != {"schema", "parameters", "children", "comparisons"}
        or value["schema"] != "exp02-aggregate-lineage-v1"
    ):
        raise ValueError("EXP02 tracking schema differs")
    allowed_parameters(value["parameters"])
    design = load_protocol()["design"]
    windows = {w["id"] for w in design["windows"]}
    expected = {("labels", h, w, "none", 0) for h, w in product((5, 7, 9), windows)} | {
        ("predictive", h, w, f, k)
        for h, w, f, k in product((5, 7, 9), windows, design["families"], (1, 2))
    }
    children = value["children"]
    if not isinstance(children, list) or len(children) != len(expected):
        raise ValueError("EXP02 tracking child count differs")
    actual = set()
    for c in children:
        if not isinstance(c, dict) or set(c) != {
            "layer",
            "history_years",
            "window",
            "family",
            "horizon",
            "status",
            "metrics",
            "cohort_sha256",
            "predictive_summary",
        }:
            raise ValueError("EXP02 child fields are not allowlisted")
        actual.add((c["layer"], c["history_years"], c["window"], c["family"], c["horizon"]))
        if c["status"] not in {"evaluable", "not_evaluable"} or not re.fullmatch(
            r"[0-9a-f]{64}", c["cohort_sha256"]
        ):
            raise ValueError("EXP02 child identity differs")
        _metrics(c["metrics"], LABEL_METRICS if c["layer"] == "labels" else PROBABILITY_METRICS)
        if c["layer"] == "predictive":
            _predictive_summary(c["predictive_summary"])
        elif c["predictive_summary"] is not None:
            raise ValueError("Label children cannot contain predictive results")
    if actual != expected:
        raise ValueError("EXP02 tracking child grid differs")
    comparisons = value["comparisons"]
    expected_pairs = {(a, b, w) for a, b in ((5, 7), (5, 9), (7, 9)) for w in windows}
    if not isinstance(comparisons, list) or len(comparisons) != 9:
        raise ValueError("EXP02 comparison count differs")
    actual_pairs = set()
    for pair in comparisons:
        if set(pair) != {"reference_years", "variant_years", "window", "metrics"}:
            raise ValueError("EXP02 comparison fields are not allowlisted")
        actual_pairs.add((pair["reference_years"], pair["variant_years"], pair["window"]))
        _metrics(pair["metrics"], CHANGE_METRICS)
    if actual_pairs != expected_pairs:
        raise ValueError("EXP02 comparison grid differs")


def safe_receipt(publication: dict[str, Any]) -> dict[str, Any]:
    data = verified_result(publication)
    result, provenance = data["result"], data["provenance"]
    parameters = {
        k: provenance[k]
        for k in (
            "protocol_sha256",
            "git_revision",
            "data_sha256",
            "configuration_sha256",
            "code_sha256",
            "environment_sha256",
        )
    }
    parameters.update(
        {
            "bundle_id": data["manifest"]["bundle_id"],
            "manifest_sha256": digest(data["manifest"]),
            "native_pointer": publication["path"],
            "evidence_type": result["evidence_type"],
            "G5": "NOT_APPROVED",
            "champion": "not_selected",
            "cohort": "fixed_five_year_origin",
        }
    )
    children = []
    for child in result["stability"]["children"]:
        children.append(
            {
                "layer": "labels",
                "history_years": child["history_years"],
                "window": child["window"],
                "family": "none",
                "horizon": 0,
                "status": "evaluable" if child["common_state_rows"] else "not_evaluable",
                "cohort_sha256": child["common_keys_sha256"],
                "metrics": {k: child[k] for k in LABEL_METRICS},
                "predictive_summary": None,
            }
        )
    for child in result["predictive"]["children"]:
        metrics = {}
        if child["status"] == "evaluable":
            for name, key in (("own", "own_definition"), ("anchor", "fixed_anchor")):
                for metric in ("average_precision", "brier"):
                    if child[key][metric] is not None:
                        metrics[name + "_" + metric] = child[key][metric]
                value = child[key]["calibration"]["expected_calibration_error"]
                if value is not None:
                    metrics[name + "_calibration_error"] = value
        children.append(
            {
                k: child[k]
                for k in (
                    "layer",
                    "history_years",
                    "window",
                    "family",
                    "horizon",
                    "status",
                    "cohort_sha256",
                )
            }
            | {
                "metrics": metrics,
                "predictive_summary": {
                    "reason": child["reason"],
                    "calibration": {
                        key: child[key]["calibration"] for key in ("own_definition", "fixed_anchor")
                    }
                    if child["status"] == "evaluable"
                    else None,
                    "frontier": [
                        {
                            **{
                                k: v
                                for k, v in row.items()
                                if k not in {"by_group", "own_definition", "fixed_anchor"}
                            },
                            **{
                                key: {k: row[key][k] for k in EPISODE_METRICS}
                                for key in ("own_definition", "fixed_anchor")
                            },
                        }
                        for row in child["frontier"]
                    ],
                },
            }
        )
    pairs = []
    for pair in result["stability"]["pairs"]:
        metrics = {
            label + "_" + k: pair[label][k]
            for label in ("excess", "onset")
            for k in ("paired_rows", "changed", "zero_to_one", "one_to_zero")
        }
        metrics.update({k: pair["episodes"][k] for k in CHANGE_METRICS if k in pair["episodes"]})
        pairs.append(
            {k: pair[k] for k in ("reference_years", "variant_years", "window")}
            | {"metrics": metrics}
        )
    receipt = {
        "schema": "exp02-aggregate-lineage-v1",
        "parameters": parameters,
        "children": children,
        "comparisons": pairs,
    }
    validate_safe_receipt(receipt)
    return receipt


class Exp02Tracking(LocalTracking):
    """Successful native publication is required before recording scientific cells."""

    def __init__(self, pipeline: str, execution: str, root: str, *, experiment_id: str) -> None:
        if pipeline == "exp02_synthetic":
            require_isolated_generated_root(root)
        super().__init__(pipeline, execution, root, experiment_id=experiment_id)

    def finish_exp02(self, publication: dict[str, Any]) -> str:
        try:
            receipt = safe_receipt(publication)
            expected = (
                "exp02_synthetic"
                if receipt["parameters"]["evidence_type"] == "synthetic_interface_probe"
                else "exp02"
            )
            if self.pipeline != expected or self.conceptual.get("experiment_id") != "EXP02":
                raise ValueError("EXP02 tracking purpose mismatch")
            with self._lock():
                if self.terminal:
                    raise ValueError("EXP02 tracker is terminal")
                bundle_id = receipt["parameters"]["bundle_id"]
                previous = self.client.search_runs(
                    [self.experiment],
                    filter_string=f"params.bundle_id = '{bundle_id}' and tags.status = 'success'",
                )
                if previous:
                    raise ValueError("EXP02 bundle already registered")
                self.params(self.parent, receipt["parameters"])
                self.client.set_tag(self.parent, "epidemic_policy", "include_all_years")
                for cell in receipt["children"]:
                    tags = {
                        **self.conceptual,
                        "mlflow.parentRunId": self.parent,
                        "epidemic_policy": "include_all_years",
                        "mlflow.runName": (
                            f"EXP02:H{cell['history_years']}:{cell['layer']}:"
                            f"{cell['window']}:{cell['family']}:h{cell['horizon']}"
                        ),
                        **{
                            k: str(cell[k])
                            for k in (
                                "layer",
                                "history_years",
                                "window",
                                "family",
                                "horizon",
                                "status",
                            )
                        },
                    }
                    run = self.client.create_run(self.experiment, tags=tags).info.run_id
                    self.children.append(run)
                    self.params(
                        run,
                        {"cohort": "fixed_five_year_origin", "input_sha256": cell["cohort_sha256"]},
                    )
                    for key, value in cell["metrics"].items():
                        self.client.log_metric(run, key, float(value))
                    self.client.set_terminated(run, "FINISHED")
                directory = safe_path(str(self.root / "receipts"), temporary=True)
                directory.mkdir(exist_ok=True)
                path = safe_path(str(directory / (self.parent + ".json")), temporary=True)
                with path.open("xb") as stream:
                    stream.write(canonical_bytes(receipt))
                self.client.log_artifact(self.parent, str(path))
                self.client.set_tag(self.parent, "status", "success")
                self.client.set_terminated(self.parent, "FINISHED")
                self.terminal = True
                return self.parent
        except BaseException:
            self.fail()
            raise


def require_isolated_generated_root(root: str) -> None:
    path = safe_path(root, temporary=True).resolve()
    for protected in ("tmp/kedro-migration/replay-mlflow", "tmp/kedro-migration/exp02-runs"):
        destination = Path.cwd() / protected
        if path.is_relative_to(destination) or destination.is_relative_to(path):
            raise ValueError("Generated EXP02 operations require isolated storage")


def export_authorized(publication: dict[str, Any], receipt: dict[str, Any]) -> str:
    """Future explicit no-fit re-export, still bound to the approved native identities."""
    approval = authorize(receipt)
    folder = safe_path(publication["path"], temporary=True)
    if folder.parent != safe_path(receipt["output_root"], temporary=True):
        raise PermissionError("EXP02 export path differs from the authorized output root")
    data = verified_result(publication)
    if data["result"]["evidence_type"] != "authorized_retrospective" or any(
        data["provenance"][k] != receipt[k] for k in BINDINGS
    ):
        raise PermissionError("EXP02 export identity differs from authorization")
    if digest(authorize(receipt)) != digest(approval):
        raise PermissionError("EXP02 export approval changed")
    tracker = Exp02Tracking(
        "exp02", data["manifest"]["bundle_id"], receipt["tracking_root"], experiment_id="EXP02"
    )
    return tracker.finish_exp02(publication)
