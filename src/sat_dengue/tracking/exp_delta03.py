"""Idempotent aggregate-only EXP-DELTA03 mirror of an already verified native bundle."""

from __future__ import annotations

import fcntl
import importlib
import json
import math
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlsplit

from sat_dengue.datasets.exp_delta03 import safe_path
from sat_dengue.datasets.exp_delta03_execution import verify_publication
from sat_dengue.experiments.exp_delta03_contract import canonical, digest
from sat_dengue.tracking.experiments import MLFLOW_EXPERIMENT_NAME

METRICS = {
    "rows",
    "positive_support",
    "negative_support",
    "onsets_observed",
    "onsets_detected",
    "onsets_missed",
    "alerts_emitted",
    "false_onset_alerts",
    "false_excess_alerts",
    "sensitivity",
    "precision",
    "academic_excess_FAR",
    "eligible_exposure_municipality_years",
    "monitored_exposure_municipality_years",
    "false_onset_alerts_per_eligible_municipality_year",
    "false_onset_alerts_per_monitored_municipality_year",
    "average_precision",
    "auroc_secondary",
    "brier",
    "coverage",
    "municipalities",
    "target_months",
    "anticipation_months_detected",
}
CELL_FIELDS = {
    "id",
    "variant",
    "horizon",
    "year",
    "training_scope",
    "evaluation_scope",
    "status",
    "metrics",
    "model_sha256",
    "calibrator_sha256",
    "policy_sha256",
    "cohort_sha256",
    "parameters_sha256",
    "predictors_sha256",
    "parameters",
}
RESULT_FIELDS = {
    "schema",
    "identity",
    "identity_sha256",
    "regime",
    "operational_PIT",
    "cells",
    "comparisons",
    "activity_counters",
    "counts",
    "unsupported",
}


def safe_token(value: Any) -> str:
    text = str(value)
    if text == "binary:logistic":
        return text
    if re.fullmatch(r"[A-Za-z0-9_.+-]{1,200}", text) is None or ".." in text:
        raise ValueError("Private/unsafe tracking value")
    if re.search(r"gh[pousr]_|AKIA|PRIVATE.KEY|AIza", text):
        raise ValueError("Credential-shaped tracking value")
    return text


def validate_lineage(value: dict[str, Any]) -> None:
    if set(value) != {
        "schema",
        "identity_sha256",
        "native_manifest_sha256",
        "parent_run_id",
        "children",
        "real_model_fits",
        "synthetic_model_fits",
        "parameters",
    }:
        raise ValueError("Unexpected EXP-DELTA03 lineage fields")
    if value["schema"] != "exp-delta03-mlflow-lineage-v1":
        raise ValueError("Unknown lineage schema")
    for key in ("identity_sha256", "native_manifest_sha256"):
        if re.fullmatch(r"[0-9a-f]{64}", value[key]) is None:
            raise ValueError("Invalid lineage hash")
    ids = [value["parent_run_id"], *value["children"].values()]
    if len(ids) != len(set(ids)) or any(re.fullmatch(r"[0-9a-f]{32}", r) is None for r in ids):
        raise ValueError("Invalid/duplicate lineage run identity")
    for key in value["children"]:
        safe_token(key)
    if any(
        type(value[k]) is not int or value[k] < 0
        for k in ["real_model_fits", "synthetic_model_fits"]
    ):
        raise ValueError("Invalid lineage activity")
    if value["real_model_fits"] and value["synthetic_model_fits"]:
        raise ValueError("Mixed scientific and generated activity")
    from sat_dengue.tracking.local import allowed_parameters

    allowed_parameters(value["parameters"])


def projection(cell: dict[str, Any]) -> dict[str, float]:
    if set(cell) != CELL_FIELDS:
        raise ValueError("Unexpected cell fields; rows/paths may not enter MLflow")
    output = {}
    for role, values in cell["metrics"]["roles"].items():
        if role not in {"train", "calibration", "selection", "evaluation"}:
            raise ValueError("Unexpected metric role")
        for key, value in values.items():
            if key in METRICS and type(value) in (int, float) and math.isfinite(value):
                output[role + "." + key] = float(value)
    for scope, values in cell["metrics"]["scopes"].items():
        if scope not in {"national", "Meta", "Tolima", "Meta_Tolima"}:
            raise ValueError("Municipal metric scopes are forbidden in MLflow")
        for key, value in values.items():
            if key in METRICS and type(value) in (int, float) and math.isfinite(value):
                output["scope." + scope + "." + key] = float(value)
    return output


def client_for(root: Path, relative: str):
    """Reuse the repository's logical satlocal artifact namespace and telemetry opt-out."""
    os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
    client_module = importlib.import_module("mlflow.tracking")
    from sat_dengue.tracking.artifacts import register_local_artifacts

    register_local_artifacts()
    location = "satlocal:/" + quote(relative + "/artifacts", safe="/")
    previous = os.environ.get("_MLFLOW_SERVER_ARTIFACT_ROOT")
    os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = location
    try:
        client = client_module.MlflowClient(
            tracking_uri="sqlite:///" + quote(relative + "/tracking.sqlite", safe="/")
        )
    finally:
        if previous is None:
            os.environ.pop("_MLFLOW_SERVER_ARTIFACT_ROOT", None)
        else:
            os.environ["_MLFLOW_SERVER_ARTIFACT_ROOT"] = previous
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENT_NAME)
    eid = (
        experiment.experiment_id
        if experiment
        else client.create_experiment(MLFLOW_EXPERIMENT_NAME, artifact_location=location)
    )
    if client.get_experiment(eid).artifact_location != location:
        raise ValueError("Tracking artifact root identity changed")
    return client, eid


def mirror(
    root: Path,
    publication: dict[str, Any],
    tracking_relative: str,
    *,
    synthetic: bool,
    permission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if root.resolve() != Path.cwd().resolve():
        raise ValueError("Tracking root must be the active repository root")
    payloads = verify_publication(root, publication, synthetic=synthetic)
    result = json.loads(payloads["result.json"])
    if set(result) != RESULT_FIELDS or result["schema"] != "exp-delta03-results-v1":
        raise ValueError("Unexpected aggregate tracking source")
    if result["regime"] != "RETROSPECTIVE_CONSOLIDATED" or result["operational_PIT"] is not False:
        raise ValueError("Retrospective-only tracking source required")
    if synthetic and result["identity"].get("input_source") != "generated_only":
        raise ValueError("Synthetic mirror requires generated-only input identity")
    execution = result["identity_sha256"]
    if (
        execution != digest(result["identity"])
        or publication["execution_identity_sha256"] != execution
    ):
        raise ValueError("Native execution identity changed")
    if not synthetic and (
        permission is None
        or permission["identity"] != result["identity"]
        or tracking_relative != permission["identity"]["roots"]["tracking"]
    ):
        raise PermissionError("Scientific tracking requires bound Phase3 authority")
    if synthetic and (
        result["activity_counters"]["real_model_fits"] != 0
        or result["activity_counters"]["real_calibrations"] != 0
    ):
        raise ValueError("Generated tracking cannot contain real adjustments")
    prefix = "tmp/exp-delta03-phase2/synthetic" if synthetic else "tmp"
    store = safe_path(root, tracking_relative, prefix)
    cells = result["cells"]
    expected = {c["id"] for c in cells}
    if len(expected) != len(cells) or len(cells) != result["counts"]["models"]:
        raise ValueError("Derived tracking cell count mismatch")
    projected = {c["id"]: projection(c) for c in cells}
    for c in cells:
        for key in CELL_FIELDS - {"metrics", "parameters"}:
            safe_token(c[key])
        for key, value in c["parameters"].items():
            safe_token(key)
            safe_token(value)
    if any(p.is_symlink() for p in store.rglob("*")):
        raise ValueError("Symlink tracking member")
    common = {
        "experiment_id": "EXP-DELTA03",
        "experiment_concept": "monthly_dengue_climate_ablation",
        "hypothesis_id": "EXP-DELTA03-H1",
        "protocol_sha256": result["identity"]["protocol_sha256"],
        "matrix_bundle_sha256": result["identity"]["matrix_manifest_sha256"],
        "git_commit": result["identity"]["commit"],
        "model_family": "xgboost",
        "preparation_regime": "RETROSPECTIVE_CONSOLIDATED",
        "operational_PIT": "false",
        "execution_identity_sha256": execution,
        "native_manifest_sha256": publication["manifest_sha256"],
        "evidence_type": "generated_only" if synthetic else "authorized_retrospective",
    }
    for value in common.values():
        safe_token(value)
    store.mkdir(parents=True, exist_ok=True, mode=0o700)
    lock = safe_path(root, tracking_relative + "/.mirror.lock", prefix)
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    client: Any = None
    parent: str | None = None
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        client, experiment = client_for(root, tracking_relative)
        query = (
            f"tags.execution_identity_sha256 = '{execution}' and "
            f"tags.native_manifest_sha256 = '{publication['manifest_sha256']}'"
        )
        existing = client.search_runs([experiment], filter_string=query, max_results=len(cells) + 2)
        parents = [r for r in existing if r.data.tags.get("run_kind") == "parent"]
        if len(parents) > 1:
            raise ValueError("Duplicate EXP-DELTA03 parent runs")
        if not parents and existing:
            raise ValueError("Orphaned tracking runs require inspection")
        parent_tags = {
            **common,
            "run_kind": "parent",
            "mlflow.runName": "EXP-DELTA03:" + execution[:12],
            "variant": "all_declared",
            "horizon": "all",
            "period": "all",
            "scope": "execution",
            "training_scope": "declared",
            "evaluation_scope": "declared",
        }
        parent = (
            parents[0].info.run_id
            if parents
            else client.create_run(experiment, tags=parent_tags).info.run_id
        )
        parent_run = client.get_run(parent)
        if any(parent_run.data.tags.get(k) != v for k, v in parent_tags.items()):
            raise ValueError("Parent lineage changed")
        completed = parent_run.info.status == "FINISHED"
        if completed and not parent_run.data.tags.get("lineage_sha256"):
            raise ValueError("Completed tracking completion evidence missing")
        if (
            parents
            and not completed
            and not synthetic
            and (permission is None or not permission["allow_resume"])
        ):
            raise PermissionError("Incomplete scientific tracking requires explicit resume")
        attached = client.search_runs(
            [experiment],
            filter_string=f"tags.mlflow.parentRunId = '{parent}'",
            max_results=len(cells) + 1,
        )
        combined = {r.info.run_id: r for r in [*existing, *attached]}
        existing = list(combined.values())
        if parent_run.info.status == "FINISHED":
            if parent_run.data.tags.get("execution_state") != "complete":
                raise ValueError("Completed tracking status changed")
            if {
                r.data.tags.get("cell_id")
                for r in existing
                if r.data.tags.get("run_kind") == "child"
            } != expected:
                raise ValueError("Completed tracking child inventory changed")
        child_runs = {}
        for cell in cells:
            found = [r for r in existing if r.data.tags.get("cell_id") == cell["id"]]
            if len(found) > 1:
                raise ValueError("Duplicate child run")
            tags = {
                **common,
                "run_kind": "child",
                "cell_id": cell["id"],
                "mlflow.parentRunId": parent,
                "mlflow.runName": "EXP-DELTA03:" + cell["id"],
                "variant": cell["variant"],
                "horizon": str(cell["horizon"]),
                "period": str(cell["year"]),
                "scope": cell["evaluation_scope"],
                "cell_status": cell["status"],
                "training_scope": cell["training_scope"],
                "evaluation_scope": cell["evaluation_scope"],
            }
            run = (
                found[0].info.run_id
                if found
                else client.create_run(experiment, tags=tags).info.run_id
            )
            child_runs[cell["id"]] = run
            stored = client.get_run(run)
            if any(stored.data.tags.get(k) != v for k, v in tags.items()):
                raise ValueError("Child lineage/parent tags changed")
            if completed and stored.info.status != "FINISHED":
                raise ValueError("Completed tracking child status changed")
            expected_sha = digest(
                {"metrics": projected[cell["id"]], "parameters": cell["parameters"]}
            )
            prior = client.get_run(run).data.tags.get("aggregate_sha256")
            if completed and prior is None:
                raise ValueError("Completed tracking completion evidence missing")
            if prior is not None and prior != expected_sha:
                raise ValueError("Tracking aggregate changed")
            if prior is not None:
                expected_params = {k: safe_token(v) for k, v in cell["parameters"].items()}
                if (
                    stored.data.params != expected_params
                    or stored.data.metrics != projected[cell["id"]]
                ):
                    raise ValueError("Stored tracking metrics/parameters changed")
                for key in (
                    "model_sha256",
                    "calibrator_sha256",
                    "policy_sha256",
                    "cohort_sha256",
                    "predictors_sha256",
                ):
                    if stored.data.tags.get(key) != cell[key]:
                        raise ValueError("Stored model/cohort lineage changed")
            if prior is None:
                for key, value in cell["parameters"].items():
                    client.log_param(run, key, safe_token(value))
                for key, value in projected[cell["id"]].items():
                    client.log_metric(run, key, value)
                for key in (
                    "model_sha256",
                    "calibrator_sha256",
                    "policy_sha256",
                    "cohort_sha256",
                    "predictors_sha256",
                ):
                    client.set_tag(run, key, cell[key])
                client.set_tag(run, "aggregate_sha256", expected_sha)
            if client.get_run(run).info.status != "FINISHED":
                client.set_terminated(run, "FINISHED")
        if any(
            r.data.tags.get("run_kind") == "child" and r.data.tags.get("cell_id") not in expected
            for r in existing
        ):
            raise ValueError("Unexpected tracked cell")
        pairs = []
        for pair in result["comparisons"]:
            a, b = pair["left"], pair["right"]
            prior_reference = client.get_run(child_runs[a]).data.tags.get("reference_run_id")
            if completed and prior_reference is None:
                raise ValueError("Completed tracking reference completion evidence missing")
            if prior_reference is not None and prior_reference != child_runs[b]:
                raise ValueError("Tracked comparison reference changed")
            if prior_reference is None:
                client.set_tag(child_runs[a], "reference_run_id", child_runs[b])
            pairs.append({**pair, "left_run_id": child_runs[a], "right_run_id": child_runs[b]})
        lineage = {
            "schema": "exp-delta03-mlflow-lineage-v1",
            "identity_sha256": execution,
            "native_manifest_sha256": publication["manifest_sha256"],
            "parent_run_id": parent,
            "children": child_runs,
            "real_model_fits": result["activity_counters"]["real_model_fits"],
            "synthetic_model_fits": result["activity_counters"]["synthetic_model_fits"],
        }
        lineage["parameters"] = {
            "protocol_sha256": common["protocol_sha256"],
            "input_sha256": common["matrix_bundle_sha256"],
            "git_revision": common["git_commit"],
            "bundle_id": publication["bundle_id"],
            "manifest_sha256": publication["manifest_sha256"],
        }
        validate_lineage(lineage)
        lineage_sha = digest(lineage)
        recorded = client.get_run(parent).data.tags.get("lineage_sha256")
        if recorded is not None and recorded != lineage_sha:
            raise ValueError("Tracked lineage changed")
        if recorded is None:
            receipt_dir = store / ".receipts"
            receipt_dir.mkdir(exist_ok=True)
            artifact = receipt_dir / (lineage_sha[:32] + ".json")
            artifact.write_bytes(canonical(lineage))
            try:
                client.log_artifact(parent, str(artifact))
                client.set_tag(parent, "lineage_sha256", lineage_sha)
            finally:
                artifact.unlink(missing_ok=True)
        uri = urlsplit(client.get_run(parent).info.artifact_uri)
        relative_artifact = unquote(uri.path).lstrip("/") + "/" + lineage_sha[:32] + ".json"
        if uri.scheme != "satlocal" or uri.netloc or uri.query or uri.fragment:
            raise ValueError("Tracking artifact URI changed")
        artifact_path = safe_path(root, relative_artifact, tracking_relative + "/artifacts")
        if artifact_path.read_bytes() != canonical(lineage):
            raise ValueError("Stored lineage artifact changed")
        if client.get_run(parent).data.tags.get("execution_state") != "complete":
            client.set_tag(parent, "execution_state", "complete")
        if client.get_run(parent).info.status != "FINISHED":
            client.set_terminated(parent, "FINISHED")
        return {
            **lineage,
            "schema": "exp-delta03-tracking-receipt-v1",
            "pairs": pairs,
            "runs": len(child_runs) + 1,
            "permanent_writes": 0 if synthetic else len(child_runs) + 1,
        }
    except BaseException:
        if client is not None and parent is not None:
            try:
                if client.get_run(parent).info.status != "FINISHED":
                    client.set_tag(parent, "execution_state", "incomplete_tracking")
                    client.set_terminated(parent, "FAILED")
            except Exception:
                pass
        raise
    finally:
        os.close(fd)
