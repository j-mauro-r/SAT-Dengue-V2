"""Safe native EXP03.1 bundle validation and repository-local publication."""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import quote

from sat_dengue.configuration import canonical_bytes


def validate_bundle(bundle: dict[str, Any]) -> None:
    from sat_dengue.experiments.exp03_1_contract import counts, digest, protocol
    from sat_dengue.experiments.exp03_1_engine import execution_plan

    required = {
        "schema",
        "experiment_id",
        "scientific_id",
        "protocol_sha256",
        "reuse_decision",
        "execution_plan",
        "predictions",
        "thresholds",
        "metrics",
        "diagnostics",
        "execution_counters",
        "G5",
        "champion",
        "synthetic",
    }
    if set(bundle) != required or bundle["schema"] != "exp03-1-scientific-bundle-v1":
        raise ValueError("Invalid EXP03.1 bundle schema")
    if bundle["experiment_id"] != "EXP031" or bundle["scientific_id"] != "EXP03.1":
        raise ValueError("Invalid EXP03.1 identity")
    if bundle["protocol_sha256"] != digest(protocol()):
        raise ValueError("EXP03.1 protocol identity changed")
    if bundle["G5"] != "NOT_APPROVED" or bundle["champion"] != "not_selected":
        raise ValueError("EXP03.1 cannot approve G5 or select champion")
    if bundle["synthetic"] is not True:
        raise PermissionError("Real EXP03.1 publication is not authorized")
    decision = bundle["reuse_decision"].get("decision")
    expected_counts = counts()
    expected_execution = (
        {
            "total": expected_counts["maximum_refit_cells"],
            "reused": expected_counts["maximum_reused_m00_cells"],
            "new_fits": expected_counts["maximum_new_fit_cells_with_complete_reuse"],
        }
        if decision == "reused"
        else {
            "total": expected_counts["maximum_refit_cells"],
            "reused": 0,
            "new_fits": expected_counts["maximum_refit_cells"],
        }
        if decision == "refitted"
        else None
    )
    execution = bundle["execution_plan"]
    if (
        expected_execution is None
        or execution.get("counts") != expected_execution
        or execution.get("searches") != 0
        or len(execution.get("cells", ())) != expected_execution["total"]
        or execution != execution_plan(bundle["reuse_decision"])
    ):
        raise ValueError("Invalid EXP03.1 execution plan")
    counters = bundle["execution_counters"]
    forbidden = (
        "real_private_reads",
        "real_reservations",
        "real_fits",
        "real_calibrations",
        "real_searches",
        "permanent_mlflow_writes",
    )
    if set(counters) != set(forbidden) or any(counters[name] != 0 for name in forbidden):
        raise ValueError("Real-science counters must remain zero")
    prediction_keys = []
    cell_ids = set()
    for row in bundle["predictions"]:
        if not {"cell_id", "municipality_code", "target_month", "score", "alert"} <= set(row):
            raise ValueError("Invalid native prediction row")
        try:
            year, month = (int(value) for value in row["target_month"].split("-"))
            score = float(row["score"])
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError("Invalid native prediction values") from error
        if (
            year > 2024
            or month not in range(1, 13)
            or not math.isfinite(score)
            or not 0 <= score <= 1
        ):
            raise ValueError("EXP03.1 predictions reject post-2024 or invalid values")
        if not isinstance(row["alert"], bool):
            raise ValueError("EXP03.1 alerts must be boolean")
        key = (row["cell_id"], row["municipality_code"], row["target_month"])
        prediction_keys.append(key)
        cell_ids.add(row["cell_id"])
    if len(prediction_keys) != len(set(prediction_keys)):
        raise ValueError("Duplicate native EXP03.1 prediction key")
    threshold_cells = []
    for row in bundle["thresholds"]:
        if not {"cell_id", "threshold", "budget"} <= set(row) or row["cell_id"] not in cell_ids:
            raise ValueError("Invalid EXP03.1 threshold row")
        if row["budget"] != protocol()["budget"]["B_primary"]:
            raise ValueError("EXP03.1 threshold budget differs from the frozen protocol")
        threshold = row["threshold"]
        if threshold is not None and (
            not isinstance(threshold, (int, float)) or not 0 <= threshold <= 1
        ):
            raise ValueError("Invalid EXP03.1 threshold")
        threshold_cells.append(row["cell_id"])
    if len(threshold_cells) != len(set(threshold_cells)):
        raise ValueError("Duplicate EXP03.1 threshold cell")


def write_bundle(bundle: dict[str, Any], path: Path) -> str:
    validate_bundle(bundle)
    root = (Path.cwd() / "tmp").resolve()
    resolved = path.resolve()
    if (
        not resolved.is_relative_to(root)
        or path.exists()
        or any(parent.is_symlink() for parent in [path, *path.parents])
    ):
        raise ValueError("EXP03.1 bundles require a new repository-local tmp path")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(bundle)
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def read_bundle(path: Path, expected_sha256: str) -> dict[str, Any]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("EXP03.1 bundle changed")
    value: dict[str, Any] = json.loads(raw)
    validate_bundle(value)
    return value


def validate_real_bundle(bundle: dict[str, Any]) -> None:
    """Close the real-result schema separately from the source-free demo schema."""
    import pandas as pd  # type: ignore[import-untyped]

    from sat_dengue.experiments.exp03 import load_protocol as load_exp03_protocol
    from sat_dengue.experiments.exp03_1_contract import (
        cells,
        counts,
        digest,
        matrix,
        protocol,
    )
    from sat_dengue.experiments.exp03_1_engine import variant_predictors
    from sat_dengue.experiments.exp03_1_evaluation import metrics

    required = {
        "schema",
        "experiment_id",
        "scientific_id",
        "protocol_sha256",
        "matrix_sha256",
        "cells",
        "predictions",
        "thresholds",
        "contrasts",
        "execution_plan",
        "reuse_decision",
        "provenance",
        "mlflow_receipt",
        "execution_counters",
        "G5",
        "champion",
        "evidence_type",
    }
    if set(bundle) != required or bundle["schema"] != "exp03-1-real-scientific-bundle-v1":
        raise ValueError("Invalid real EXP03.1 bundle schema")
    p = protocol()
    if (
        bundle["experiment_id"] != "EXP031"
        or bundle["scientific_id"] != "EXP03.1"
        or bundle["protocol_sha256"] != digest(p)
        or bundle["matrix_sha256"] != digest(matrix(p))
        or bundle["matrix_sha256"] != bundle["provenance"].get("matrix_sha256")
        or bundle["G5"] != "NOT_APPROVED"
        or bundle["champion"] != "not_selected"
        or bundle["evidence_type"] != "authorized_retrospective"
    ):
        raise ValueError("Real EXP03.1 bundle identity or governance boundary changed")
    provenance = bundle["provenance"]
    if any(
        not isinstance(provenance.get(name), str)
        or len(provenance[name]) != 64
        or any(character not in "0123456789abcdef" for character in provenance[name])
        for name in (
            "configuration_sha256",
            "source_descriptor_sha256",
            "authorization_receipt_sha256",
            "approval_sha256",
            "code_sha256",
        )
    ):
        raise ValueError("Real EXP03.1 provenance identity is incomplete")
    if (
        not isinstance(provenance.get("git_revision"), str)
        or len(provenance["git_revision"]) not in {40, 64}
        or any(character not in "0123456789abcdef" for character in provenance["git_revision"])
    ):
        raise ValueError("Real EXP03.1 source revision identity is incomplete")
    from sat_dengue.experiments.exp03_1_preflight import (
        APPROVAL_SCHEMA,
        ORIGINAL,
        REPLAY_BOUND,
        REPLAY_PROTOCOL,
    )

    replay = "replay_protocol" in provenance
    if replay and (
        provenance["replay_protocol"] != REPLAY_PROTOCOL
        or provenance.get("original") != ORIGINAL
        or provenance.get("environment_sha256") != digest(provenance.get("observed_environment"))
        or provenance.get("authorized_source_files")
        != provenance.get("source_admission", {}).get("files")
    ):
        raise ValueError("Replay provenance binding changed")
    approval = provenance.get("approval_record")
    approved_fields: tuple[str, ...] = (
        "protocol_sha256",
        "matrix_sha256",
        "source_descriptor_sha256",
        "configuration_sha256",
        "data_version",
        "git_revision",
    )
    if replay:
        approved_fields = (*approved_fields, *REPLAY_BOUND)
    if (
        not isinstance(approval, dict)
        or approval.get("schema")
        != (APPROVAL_SCHEMA if replay else "exp03-1-execution-approval-v1")
        or (replay and approval.get("replay_only_authorized") is not True)
        or approval.get("experiment_id") != "EXP031"
        or approval.get("authority") != "Mauricio"
        or not isinstance(approval.get("independent_reviewer"), str)
        or approval.get("independent_reviewer") in {"", "Mauricio"}
        or approval.get("preflight_sha256") != provenance["authorization_receipt_sha256"]
        or any(approval.get(name) != provenance.get(name) for name in approved_fields)
        or any(
            approval.get(name) is not True
            for name in (
                "real_execution_authorized",
                "m00_refit_authorized",
                "variant_refits_authorized",
                "retrospective_availability_acknowledged",
            )
        )
        or approval.get("G5_approval") is not False
        or approval.get("champion_selection") is not False
        or digest(approval) != provenance["approval_sha256"]
    ):
        raise ValueError("Real EXP03.1 bundle does not retain its bound execution approval")
    expected_cells = cells()
    expected_windows = {row["id"]: row for row in load_exp03_protocol()["design"]["windows"]}

    def identity(row: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(row[name] for name in ("objective", "variant", "family", "horizon", "cut"))

    actual_cells = bundle["cells"]
    if (
        len(actual_cells) != counts()["maximum_refit_cells"]
        or {identity(row) for row in actual_cells} != {identity(row) for row in expected_cells}
        or len(actual_cells) != len({identity(row) for row in actual_cells})
        or any(row.get("status") != "evaluable" or row.get("rows", 0) <= 0 for row in actual_cells)
    ):
        raise ValueError("Real EXP03.1 bundle does not contain 96 complete evaluated cells")
    expected_by_identity = {identity(row): row for row in expected_cells}
    cohort_hashes: dict[tuple[str, int], set[str]] = {}
    for row in actual_cells:
        spec = expected_by_identity[identity(row)]
        predictors = variant_predictors(
            load_exp03_protocol()["design"]["variants"]["V09"], spec["variant"]
        )
        if (
            row.get("cell_id") != digest(spec)
            or row.get("predictors") != predictors
            or row.get("predictors_sha256") != digest({"predictors": predictors})
            or not isinstance(row.get("cohort_sha256"), str)
            or len(row["cohort_sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in row["cohort_sha256"])
        ):
            raise ValueError("Real EXP03.1 cell identity or paired cohort hash changed")
        cohort_hashes.setdefault((row["objective"], row["horizon"]), set()).add(
            row["cohort_sha256"]
        )
    if any(len(values) != 1 for values in cohort_hashes.values()):
        raise ValueError("Real EXP03.1 variants do not share their objective/horizon cohort")
    if len(bundle["thresholds"]) != 96 or {row.get("cell_id") for row in bundle["thresholds"]} != {
        row.get("cell_id") for row in actual_cells
    }:
        raise ValueError("Real EXP03.1 threshold grid is incomplete")
    threshold_by_cell = {row["cell_id"]: row for row in bundle["thresholds"]}
    if any(
        row.get("budget") != p["budget"]["B_primary"]
        or row.get("threshold") != threshold_by_cell[row["cell_id"]].get("threshold")
        or row.get("false_alert_limit")
        != threshold_by_cell[row["cell_id"]].get("false_alert_limit")
        or threshold_by_cell[row["cell_id"]].get("false_alert_limit")
        != math.floor(
            float(threshold_by_cell[row["cell_id"]].get("selection_exposure", -1))
            * p["budget"]["B_primary"]
        )
        or threshold_by_cell[row["cell_id"]].get("selection_exposure", 0) <= 0
        for row in actual_cells
    ):
        raise ValueError("Real EXP03.1 threshold differs from its frozen cell budget")
    cell_ids = {row["cell_id"] for row in actual_cells}
    cells_by_id = {row["cell_id"]: row for row in actual_cells}
    prediction_keys = []
    for row in bundle["predictions"]:
        if (
            set(row)
            != {
                "cell_id",
                "municipality_code",
                "origin_month",
                "target_month",
                "score",
                "alert",
                "truth",
                "error_class",
                "objective",
                "variant",
                "family",
                "horizon",
                "cut",
                "exposure",
            }
            or row["cell_id"] not in cell_ids
            or not isinstance(row["alert"], bool)
            or row["truth"] not in (0, 1)
            or not math.isfinite(float(row["score"]))
            or not 0 <= float(row["score"]) <= 1
            or not math.isfinite(float(row["exposure"]))
            or float(row["exposure"]) < 0
            or pd.Period(row["target_month"], freq="M")
            != pd.Period(row["origin_month"], freq="M") + int(row["horizon"])
            or not pd.Period(row["target_month"], freq="M").strftime("%Y-%m") == row["target_month"]
            or not pd.Period(row["origin_month"], freq="M").strftime("%Y-%m") == row["origin_month"]
            or not expected_windows[row["cut"]]["evaluation"][0]
            <= row["target_month"]
            <= expected_windows[row["cut"]]["evaluation"][1]
            or any(
                row[key] != cells_by_id[row["cell_id"]][key]
                for key in ("objective", "variant", "family", "horizon", "cut")
            )
        ):
            raise ValueError("Invalid real EXP03.1 prediction row")
        prediction_keys.append((row["cell_id"], row["municipality_code"], row["target_month"]))
    if not prediction_keys or len(prediction_keys) != len(set(prediction_keys)):
        raise ValueError("Real EXP03.1 prediction rows are empty or duplicated")
    predictions_by_cell: dict[str, list[dict[str, Any]]] = {}
    for prediction in bundle["predictions"]:
        predictions_by_cell.setdefault(prediction["cell_id"], []).append(prediction)
    for row in actual_cells:
        cell_predictions = predictions_by_cell.get(row["cell_id"], [])
        threshold = threshold_by_cell[row["cell_id"]]["threshold"]
        if len(cell_predictions) != row["rows"] or any(
            prediction["alert"]
            != (False if threshold is None else prediction["score"] >= threshold)
            for prediction in cell_predictions
        ):
            raise ValueError("Real EXP03.1 predictions do not match cell metrics or threshold")
        prediction_frame = pd.DataFrame(
            [
                {
                    "truth": prediction["truth"],
                    "score": prediction["score"],
                    "alert": prediction["alert"],
                    "municipality_code": prediction["municipality_code"],
                    "target_year": int(prediction["target_month"][:4]),
                    "origin_month": prediction["origin_month"],
                    "error_class": prediction["error_class"],
                }
                for prediction in cell_predictions
            ]
        )
        exposure_frame = pd.DataFrame(
            [
                {
                    "municipality_code": prediction["municipality_code"],
                    "target_year": int(prediction["target_month"][:4]),
                    "exposure": prediction["exposure"],
                }
                for prediction in cell_predictions
            ]
        )
        if (
            exposure_frame.groupby(["municipality_code", "target_year"])["exposure"]
            .nunique()
            .gt(1)
            .any()
        ):
            raise ValueError("Real EXP03.1 exposure differs within a municipality-year")
        exposure_frame = exposure_frame.drop_duplicates()
        recalculated = metrics(
            prediction_frame,
            exposure=float(exposure_frame["exposure"].sum()),
        )
        for key in ("rows", "false_alerts", "alerts_emitted", "average_precision", "brier"):
            expected_value = recalculated[key]
            actual_value = row["metrics"].get(key)
            if expected_value is None:
                if actual_value is not None:
                    raise ValueError("Real EXP03.1 cell metrics differ from its predictions")
            elif actual_value is None or not math.isclose(
                float(actual_value), float(expected_value), rel_tol=1e-12, abs_tol=1e-12
            ):
                raise ValueError("Real EXP03.1 cell metrics differ from its predictions")
    expected_contrasts = p["contrasts"]
    contrasts = bundle["contrasts"]
    if (
        contrasts.get("definitions") != expected_contrasts
        or not isinstance(contrasts.get("paired_effects"), list)
        or not contrasts["paired_effects"]
        or any(
            row.get("contrast") not in expected_contrasts
            or row.get("left_variant") != expected_contrasts[row["contrast"]][0]
            or row.get("right_variant") != expected_contrasts[row["contrast"]][1]
            for row in contrasts["paired_effects"]
        )
    ):
        raise ValueError("Real EXP03.1 contrasts differ from the frozen protocol")
    expected_effect_rows: set[tuple[str, str, str, int, str, str, str]] = set()
    for name, pair in expected_contrasts.items():
        left_cells = {
            (
                row["objective"],
                row["family"],
                row["horizon"],
                row["cut"],
            ): row
            for row in actual_cells
            if row["variant"] == pair[0]
        }
        right_cells = {
            (
                row["objective"],
                row["family"],
                row["horizon"],
                row["cut"],
            ): row
            for row in actual_cells
            if row["variant"] == pair[1]
        }
        for group in left_cells.keys() & right_cells.keys():
            left_keys = {
                (row["municipality_code"], row["target_month"])
                for row in predictions_by_cell[left_cells[group]["cell_id"]]
            }
            right_keys = {
                (row["municipality_code"], row["target_month"])
                for row in predictions_by_cell[right_cells[group]["cell_id"]]
            }
            expected_effect_rows.update(
                (name, *group, municipality, target_month)
                for municipality, target_month in left_keys & right_keys
            )
    observed_effect_rows = [
        (
            row["contrast"],
            row["objective"],
            row["family"],
            row["horizon"],
            row["cut"],
            row["municipality_code"],
            row["target_month"],
        )
        for row in contrasts["paired_effects"]
    ]
    if (
        len(observed_effect_rows) != len(set(observed_effect_rows))
        or set(observed_effect_rows) != expected_effect_rows
    ):
        raise ValueError("Real EXP03.1 paired contrasts do not cover the frozen cell pairs")
    indexed_predictions = {
        (row["cell_id"], row["municipality_code"], row["target_month"]): row
        for row in bundle["predictions"]
    }
    for effect in contrasts["paired_effects"]:
        left_cell = next(
            row
            for row in actual_cells
            if all(row[name] == effect[name] for name in ("objective", "family", "horizon", "cut"))
            and row["variant"] == effect["left_variant"]
        )
        right_cell = next(
            row
            for row in actual_cells
            if all(row[name] == effect[name] for name in ("objective", "family", "horizon", "cut"))
            and row["variant"] == effect["right_variant"]
        )
        left_prediction = indexed_predictions.get(
            (left_cell["cell_id"], effect["municipality_code"], effect["target_month"])
        )
        right_prediction = indexed_predictions.get(
            (right_cell["cell_id"], effect["municipality_code"], effect["target_month"])
        )
        if (
            left_prediction is None
            or right_prediction is None
            or effect["alert_delta"]
            != int(left_prediction["alert"]) - int(right_prediction["alert"])
            or not math.isclose(
                float(effect["score_delta"]),
                float(left_prediction["score"]) - float(right_prediction["score"]),
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        ):
            raise ValueError("Real EXP03.1 paired contrast differs from its predictions")
    plan = bundle["execution_plan"]
    reuse = bundle["reuse_decision"]
    expected_plan = [{**row, "origin": "new_fit"} for row in expected_cells]
    if (
        reuse.get("schema") != "exp03-1-reuse-decision-v1"
        or reuse.get("decision") != "refitted"
        or reuse.get("reason") != "missing_or_mismatched_contract_hash"
        or plan.get("counts") != {"total": 96, "reused": 0, "new_fits": 96}
        or plan.get("searches") != 0
        or plan.get("cells") != expected_plan
    ):
        raise ValueError("Real EXP03.1 execution plan is incomplete or inconsistent")
    admission = bundle["provenance"].get("source_admission", {})
    if (
        admission.get("schema") != "exp03-admission-v1"
        or admission.get("status") != "verified"
        or admission.get("source_identity_status") != "verified"
        or not admission.get("files")
        or admission.get("source_kind") != "manifest_root_of_trust"
    ):
        raise ValueError("Real EXP03.1 bundle lacks verified source admission")
    from sat_dengue.experiments.exp03_admission import validate_admission

    validate_admission(bundle["provenance"])
    counters = bundle["execution_counters"]
    if (
        not isinstance(counters, dict)
        or type(counters.get("real_private_reads")) is not int
        or counters.get("real_private_reads", 0) <= 0
        or {
            key: counters.get(key)
            for key in (
                "real_reservations",
                "real_model_fits",
                "real_calibrator_fits",
                "real_threshold_selections",
                "permanent_mlflow_writes",
            )
        }
        != {
            "real_reservations": 1,
            "real_model_fits": 96,
            "real_calibrator_fits": 96,
            "real_threshold_selections": 96,
            "permanent_mlflow_writes": 0,
        }
    ):
        raise ValueError("Real EXP03.1 execution counters do not match the frozen grid")
    tracking = bundle["mlflow_receipt"]
    if (
        tracking.get("schema") != "exp03-1-mlflow-receipt-v1"
        or tracking.get("protocol_sha256") != digest(p)
        or tracking.get("child_count") != 96
        or len(tracking.get("child_run_ids", [])) != 96
        or len(tracking.get("cell_run_ids", {})) != 96
        or set(tracking["cell_run_ids"]) != cell_ids
        or set(tracking["cell_run_ids"].values()) != set(tracking["child_run_ids"])
        or len(set(tracking["child_run_ids"])) != 96
        or not isinstance(tracking.get("parent_run_id"), str)
    ):
        raise ValueError("Real EXP03.1 MLflow receipt does not match the complete grid")


def write_real_bundle(
    result: dict[str, Any],
    provenance: dict[str, Any],
    tracking_receipt: dict[str, Any],
    path: Path,
) -> dict[str, Any]:
    """Atomically publish a real-only bundle and a closed integrity manifest."""
    bundle = {
        "schema": "exp03-1-real-scientific-bundle-v1",
        "experiment_id": "EXP031",
        "scientific_id": "EXP03.1",
        "protocol_sha256": result["protocol_sha256"],
        "matrix_sha256": result["matrix_sha256"],
        "cells": result["cells"],
        "predictions": result["predictions"],
        "thresholds": result["thresholds"],
        "contrasts": result["contrasts"],
        "execution_plan": result["execution_plan"],
        "reuse_decision": result["reuse_decision"],
        "provenance": provenance,
        "mlflow_receipt": tracking_receipt,
        "execution_counters": result["execution_counters"],
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "evidence_type": "authorized_retrospective",
    }
    validate_real_bundle(bundle)
    root = (Path.cwd() / "tmp/kedro-migration/exp03-1-runs").resolve()
    resolved = path.resolve()
    if (
        not resolved.is_relative_to(root)
        or resolved.exists()
        or any(parent.is_symlink() for parent in (path, *path.parents))
    ):
        raise ValueError("Real EXP03.1 bundles require a new protected repository tmp path")
    resolved.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    lock = resolved.parent / ".exp03-1-publish.lock"
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError("Another EXP03.1 publisher holds the output lock") from error
    raw = canonical_bytes(bundle)
    body = {
        "schema": "exp03-1-real-manifest-v1",
        "protocol_sha256": bundle["protocol_sha256"],
        "matrix_sha256": bundle["matrix_sha256"],
        "configuration_sha256": provenance["configuration_sha256"],
        "tracking_receipt_sha256": hashlib.sha256(canonical_bytes(tracking_receipt)).hexdigest(),
        "files": {"bundle.json": {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}},
    }
    if "replay_protocol" in provenance and "replay_capture_root" not in result:
        os.close(lock_fd)
        lock.unlink()
        raise ValueError("Replay publication requires captured native artifacts")
    try:
        os.close(lock_fd)
        staging = Path(tempfile.mkdtemp(prefix=".exp03-1-staging-", dir=resolved.parent))
        try:
            if "replay_protocol" in provenance:
                body["schema"] = "exp03-1-real-manifest-v2"
                body["replay"] = _publish_replay(result, provenance, bundle, staging, raw)
            manifest = {**body, "bundle_id": hashlib.sha256(canonical_bytes(body)).hexdigest()}
            for name, value in (("bundle.json", raw), ("manifest.json", canonical_bytes(manifest))):
                destination = staging / name
                with destination.open("xb") as stream:
                    os.chmod(destination, 0o600)
                    stream.write(value)
                    stream.flush()
                    os.fsync(stream.fileno())
            directory_fd = os.open(staging, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            os.rename(staging, resolved)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    finally:
        lock.unlink()
    return {"path": str(resolved), "manifest": manifest, "bundle": bundle}


def read_real_bundle(path: Path, expected_bundle_id: str) -> dict[str, Any]:
    root = (Path.cwd() / "tmp/kedro-migration/exp03-1-runs").resolve()
    folder = path.resolve()
    if not folder.is_relative_to(root) or any(
        parent.is_symlink() for parent in (path, *path.parents)
    ):
        raise ValueError("Real EXP03.1 bundle path escapes protected storage")
    if any(entry.is_symlink() for entry in folder.iterdir()):
        raise ValueError("Symlink in real EXP03.1 bundle")
    manifest = json.loads((folder / "manifest.json").read_bytes())
    replay = manifest.get("schema") == "exp03-1-real-manifest-v2"
    membership = (
        {"bundle.json", "manifest.json", "replay"} if replay else {"bundle.json", "manifest.json"}
    )
    if {entry.name for entry in folder.iterdir()} != membership:
        raise ValueError("Real EXP03.1 bundle membership changed")
    raw = (folder / "bundle.json").read_bytes()
    bundle = json.loads(raw)
    if not isinstance(manifest, dict) or not isinstance(bundle, dict):
        raise ValueError("Invalid EXP03.1 manifest or bundle document")
    body = {key: value for key, value in manifest.items() if key != "bundle_id"}
    if (
        manifest.get("schema") not in {"exp03-1-real-manifest-v1", "exp03-1-real-manifest-v2"}
        or manifest.get("bundle_id") != expected_bundle_id
        or hashlib.sha256(canonical_bytes(body)).hexdigest() != expected_bundle_id
        or manifest.get("files")
        != {"bundle.json": {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}}
        or manifest.get("protocol_sha256") != bundle.get("protocol_sha256")
        or manifest.get("matrix_sha256") != bundle.get("matrix_sha256")
        or manifest.get("configuration_sha256")
        != bundle.get("provenance", {}).get("configuration_sha256")
        or manifest.get("tracking_receipt_sha256")
        != hashlib.sha256(canonical_bytes(bundle.get("mlflow_receipt"))).hexdigest()
    ):
        raise ValueError("Real EXP03.1 bundle manifest or payload hash changed")
    validate_real_bundle(bundle)
    if replay != ("replay_protocol" in bundle["provenance"]):
        raise ValueError("Replay artifacts cannot be omitted or attached to a historical execution")
    publication = {"bundle": bundle, "manifest": manifest}
    if replay:
        publication["replay"] = read_replay_package(folder, manifest, bundle)
    return publication


def validate_real_mlflow(
    bundle: dict[str, Any], tracking_root: str, expected_bundle_id: str | None = None
) -> None:
    """Read-only check that every receipt run exists, is complete, and has matching tags."""
    import sqlite3

    from sat_dengue.experiments.exp03_1_contract import digest, protocol
    from sat_dengue.experiments.exp03_preflight import safe_path

    root = safe_path(tracking_root)
    database = root / "tracking.sqlite"
    if not database.is_file():
        raise ValueError("EXP03.1 MLflow database is missing")
    uri = "file:" + quote(str(database.resolve()), safe="/") + "?mode=ro&immutable=1"
    receipt = bundle["mlflow_receipt"]
    with sqlite3.connect(uri, uri=True) as connection:
        experiment = connection.execute(
            "SELECT experiment_id FROM experiments WHERE name = ?",
            (protocol()["mlflow"]["experiment_name"],),
        ).fetchone()
        if experiment is None:
            raise ValueError("EXP03.1 MLflow experiment is missing")
        experiment_id = experiment[0]
        protocol_tag = connection.execute(
            "SELECT value FROM experiment_tags WHERE experiment_id = ? AND key = ?",
            (experiment_id, "protocol.EXP031"),
        ).fetchone()
        if protocol_tag is None or protocol_tag[0] != digest(protocol()):
            raise ValueError("EXP03.1 MLflow experiment protocol pin is missing or changed")
        child_run_ids = receipt["child_run_ids"]
        if (
            len(child_run_ids) != 96
            or len(set(child_run_ids)) != 96
            or receipt.get("child_count") != 96
        ):
            raise ValueError("EXP03.1 MLflow receipt must identify exactly 96 unique children")
        children = connection.execute(
            "SELECT runs.run_uuid, runs.experiment_id FROM runs "
            "JOIN tags ON tags.run_uuid = runs.run_uuid "
            "WHERE tags.key = ? AND tags.value = ?",
            ("mlflow.parentRunId", receipt["parent_run_id"]),
        ).fetchall()
        if (
            len(children) != 96
            or {run_id for run_id, _ in children} != set(child_run_ids)
            or any(actual_experiment != experiment_id for _, actual_experiment in children)
        ):
            raise ValueError("EXP03.1 MLflow parent must have exactly the 96 receipted children")
        run_ids = [receipt["parent_run_id"], *receipt["child_run_ids"]]
        placeholders = ",".join("?" for _ in run_ids)
        runs = connection.execute(
            f"SELECT run_uuid, status, experiment_id FROM runs WHERE run_uuid IN ({placeholders})",
            run_ids,
        ).fetchall()
        if len(runs) != 97 or any(
            actual_experiment != experiment_id for _, _, actual_experiment in runs
        ):
            raise ValueError("EXP03.1 MLflow runs are missing or cross-experiment")
        run_statuses = {run_id: status for run_id, status, _ in runs}
        if set(run_statuses.values()) == {"RUNNING"}:
            expected_run_status = "RUNNING"
            expected_tag_status = "pending_validation"
        elif set(run_statuses.values()) == {"FINISHED"}:
            expected_run_status = "FINISHED"
            expected_tag_status = "verified"
        else:
            raise ValueError("EXP03.1 MLflow runs have inconsistent or incomplete states")
        tags_rows = connection.execute(
            f"SELECT run_uuid, key, value FROM tags WHERE run_uuid IN ({placeholders})",
            run_ids,
        ).fetchall()
        params_rows = connection.execute(
            f"SELECT run_uuid, key, value FROM params WHERE run_uuid IN ({placeholders})",
            run_ids,
        ).fetchall()
        metrics_rows = connection.execute(
            f"SELECT run_uuid, key, value FROM metrics WHERE run_uuid IN ({placeholders})",
            run_ids,
        ).fetchall()
    tags: dict[str, dict[str, str]] = {}
    for run_id, key, value in tags_rows:
        tags.setdefault(run_id, {})[key] = value
    params: dict[str, dict[str, str]] = {}
    for run_id, key, value in params_rows:
        params.setdefault(run_id, {})[key] = value
    logged_metrics: dict[str, dict[str, float]] = {}
    for run_id, key, value in metrics_rows:
        logged_metrics.setdefault(run_id, {})[key] = float(value)
    p = protocol()
    parent_tags = tags[receipt["parent_run_id"]]
    if (
        parent_tags.get("experiment_id") != "EXP031"
        or parent_tags.get("protocol_sha256") != digest(p)
        or parent_tags.get("mlflow_receipt_sha256") != digest(receipt)
        or parent_tags.get("status") != expected_tag_status
        or (expected_bundle_id is not None and parent_tags.get("bundle_id") != expected_bundle_id)
    ):
        raise ValueError("EXP03.1 MLflow parent tags differ from the bundle receipt")
    expected_tags = p["mlflow"]["required_conceptual_tags"]
    rows_by_id = {row["cell_id"]: row for row in bundle["cells"]}
    metric_names = {
        "average_precision": "average_precision",
        "brier": "brier",
        "false_alerts": "false_alerts",
        "rows": "evaluable_rows",
    }
    for cell_id, run_id in receipt["cell_run_ids"].items():
        actual = tags[run_id]
        row = rows_by_id[cell_id]
        actual_params = params.get(run_id, {})
        actual_metrics = logged_metrics.get(run_id, {})
        if (
            actual.get("mlflow.parentRunId") != receipt["parent_run_id"]
            or actual.get("status") != expected_tag_status
            or run_statuses[run_id] != expected_run_status
            or any(actual.get(key) != value for key, value in expected_tags.items())
            or any(
                actual.get(key) != str(value)
                for key, value in {
                    "experiment_id": "EXP031",
                    "protocol_sha256": digest(p),
                    "cell_id": cell_id,
                    "variant": row["variant"],
                    "objective": row["objective"],
                    "family": row["family"],
                    "horizon": row["horizon"],
                    "cut": row["cut"],
                }.items()
            )
            or any(
                actual_params.get(key) != str(value)
                for key, value in {
                    "family": row["family"],
                    "horizon": row["horizon"],
                    "objective": row["objective"],
                    "window": row["cut"],
                }.items()
            )
            or any(
                (
                    metric_names[key] in actual_metrics
                    if row["metrics"].get(key) is None
                    else metric_names[key] not in actual_metrics
                    or not math.isclose(
                        actual_metrics[metric_names[key]],
                        float(row["metrics"][key]),
                        rel_tol=1e-12,
                        abs_tol=1e-12,
                    )
                )
                for key in metric_names
            )
        ):
            raise ValueError("EXP03.1 MLflow cell identity differs from bundle")


def _frame_state(frame: Any) -> dict[str, Any]:
    """Lossless JSON scalars, ordered columns/index and pandas dtypes; no CSV rounding."""
    import numpy as np
    import pandas as pd

    def scalar(value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            return [scalar(item) for item in value]
        if pd.isna(value):
            return None
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, (pd.Period, pd.Timestamp)):
            return str(value)
        return value

    return {
        "columns": list(frame.columns),
        "dtypes": {name: str(frame[name].dtype) for name in frame},
        "categories": {
            name: {
                "values": [scalar(v) for v in frame[name].cat.categories],
                "ordered": frame[name].cat.ordered,
            }
            for name in frame
            if isinstance(frame[name].dtype, pd.CategoricalDtype)
        },
        "index": [scalar(value) for value in frame.index],
        "index_dtype": str(frame.index.dtype),
        "index_name": frame.index.name,
        "rows": [[scalar(v) for v in row] for row in frame.itertuples(index=False, name=None)],
    }


def _restore_frame(state: dict[str, Any]) -> Any:
    import pandas as pd

    frame = pd.DataFrame(state["rows"], columns=state["columns"])
    for name, dtype in state["dtypes"].items():
        if name in state["categories"]:
            category = state["categories"][name]
            dtype = pd.CategoricalDtype(category["values"], ordered=category["ordered"])
        frame[name] = frame[name].astype(dtype)
    frame.index = pd.Index(state["index"], dtype=state["index_dtype"], name=state["index_name"])
    return frame


def capture_replay_cell(payload: dict[str, Any], root: Path, provenance: dict[str, Any]) -> None:
    """Persist already fitted objects and already computed scores through EXP03 utilities."""
    import pandas as pd

    from sat_dengue.experiments.exp03_persistence import FrozenCell, save_cell

    result = payload["result"]
    columns = result["predictors"]
    roles = {}
    for role, frame in payload["roles"].items():
        names = list(
            dict.fromkeys(
                [
                    "municipality_code",
                    "year_month",
                    "target_month",
                    "target_year",
                    "onset_target",
                    "excess_target",
                    "eligible_at_t",
                    "error_type",
                    *columns,
                    *[
                        name + "__latest_source_month"
                        for name in columns
                        if name + "__latest_source_month" in frame
                    ],
                ]
            )
        )
        rows = frame[[name for name in names if name in frame]].copy()
        if role != "train":
            rows["raw_score"] = payload["raw_scores"][role]
            rows["score"] = payload["scores"][role]
        if role == "evaluation":
            rows["alert"] = payload["alerts"]
        source_dates = {}
        for name in ("source_months", "source_event_months"):
            audit = frame.attrs.get(name)
            source_audit = payload.get("source_audit", {})
            if not isinstance(audit, pd.DataFrame) and isinstance(
                source_audit.get(name), pd.DataFrame
            ):
                keys = ["municipality_code", "year_month"]
                keyed = source_audit["keys"][keys].copy()
                dates = source_audit[name]
                for column in dates:
                    keyed[column] = dates[column]
                audit = keyed.set_index(keys).reindex(pd.MultiIndex.from_frame(frame[keys]))
                audit.index = frame.index
            source_dates[name] = (
                _frame_state(audit.loc[frame.index]) if isinstance(audit, pd.DataFrame) else None
            )
        roles[role] = {
            "frame": _frame_state(rows),
            "source_dates": source_dates,
            "effective_label_dtype": str(frame[payload["target"]].astype(int).dtype),
            "label_available_at": None,
            "availability_status": "historical_availability_unverified",
            "score_origin": "frozen_EXP03.1_roles_no_additional_OOF",
        }
    memberships = {}
    for role, part in payload["parts"].items():
        membership = part[["municipality_code", "year_month", "target_month"]].copy()
        membership["selected"] = part.index.isin(payload["roles"][role].index)
        memberships[role] = _frame_state(membership)
    cell = FrozenCell(
        cell_id=result["cell_id"],
        metadata={
            "schema": "exp03-1-replay-cell-v1",
            "scientific_cell": result,
            "target": payload["target"],
            "window": payload["window"],
            "roles": roles,
            "role_membership": memberships,
            "cohort_ledger": _frame_state(payload["cohort_ledger"]),
            "threshold_selection": payload["threshold_selection"],
            "alert_rule": "score >= threshold; null => no alerts; whole score ties",
        },
        predictor=payload["predictor"],
        calibrator=payload["calibrator"],
        threshold=result["threshold"],
        budget=result["budget"],
        profiles={},
        provenance=provenance,
    )
    save_cell(cell, root / cell.cell_id)


def verify_replay_cell(path: Path) -> dict[str, Any]:
    """Replay raw/calibrated scores and alerts from native state, with zero fits."""
    import numpy as np

    from sat_dengue.experiments.exp03_persistence import load_cell

    cell = load_cell(path)
    if cell.metadata.get("schema") != "exp03-1-replay-cell-v1" or path.name != cell.cell_id:
        raise ValueError("Invalid replay cell identity")
    scientific = cell.metadata["scientific_cell"]
    from sat_dengue.experiments.exp03_1_contract import digest

    spec = {name: scientific[name] for name in ("objective", "variant", "family", "horizon", "cut")}
    if (
        digest(spec) != cell.cell_id
        or scientific["cell_id"] != cell.cell_id
        or scientific["predictors"] != cell.predictor.columns
        or scientific["threshold"] != cell.threshold
    ):
        raise ValueError("Replay scientific identity changed")
    checks = []
    for role in ("calibration", "selection", "evaluation"):
        frame = _restore_frame(cell.metadata["roles"][role]["frame"])
        prediction = cell.predict(frame[cell.predictor.columns])
        exact = True
        maximum = 0.0
        for name in ("raw_score", "score"):
            before, after = (
                frame[name].to_numpy(dtype=float),
                prediction[name].to_numpy(dtype=float),
            )
            if (
                not np.isfinite(before).all()
                or not np.isfinite(after).all()
                or not np.allclose(before, after, atol=1e-12, rtol=0)
            ):
                raise ValueError("Replay reload score mismatch: " + role + "/" + name)
            # Changes to ranking, bins or tie membership are never numeric-only differences.
            from sat_dengue.experiments.exp03_1_validate import score_structure

            if score_structure(before) != score_structure(after):
                raise ValueError("Replay reload ranking/bin/tie mismatch")
            exact = exact and np.array_equal(before, after)
            maximum = max(maximum, float(np.max(np.abs(before - after))))
        expected_alert = (
            np.zeros(len(frame), dtype=bool)
            if cell.threshold is None
            else frame.score.to_numpy(dtype=float) >= cell.threshold
        )
        if not np.array_equal(expected_alert, prediction.alert.to_numpy(dtype=bool)):
            raise ValueError("Replay reload alert mismatch")
        if role == "evaluation" and not np.array_equal(
            expected_alert, frame.alert.to_numpy(dtype=bool)
        ):
            raise ValueError("Captured evaluation alerts differ")
        checks.append(
            {
                "role": role,
                "rows": len(frame),
                "exact": exact,
                "maximum_probability_difference": maximum,
            }
        )
    return {
        "cell_id": cell.cell_id,
        "identity": cell.identity(),
        "status": "pass",
        "roles": checks,
        "atol": 1e-12,
        "rtol": 0,
        "fits": 0,
    }


def _replay_inventory(root: Path) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_persistence import _safe_directory

    root = _safe_directory(root)
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_relative_to(root):
            raise ValueError("Symlink or external replay artifact")
        if path.is_file() and path != root / "manifest.json":
            raw = path.read_bytes()
            files[path.relative_to(root).as_posix()] = {
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
    return files


def _publish_replay(
    result: dict[str, Any],
    provenance: dict[str, Any],
    bundle: dict[str, Any],
    staging: Path,
    raw: bytes,
) -> dict[str, Any]:
    from sat_dengue.experiments.exp03_1_validate import compare_observables, read_original
    from sat_dengue.experiments.exp03_persistence import _safe_directory

    source = _safe_directory(Path(result["replay_capture_root"]))
    expected = {row["cell_id"] for row in result["cells"]}
    if {p.name for p in source.iterdir()} != expected or any(
        p.is_symlink() for p in source.rglob("*")
    ):
        raise ValueError("Incomplete or unsafe replay capture")
    root = staging / "replay"
    shutil.copytree(source, root)
    reloads = [verify_replay_cell(root / cell_id) for cell_id in sorted(expected)]
    original = read_original(Path(provenance["original_bundle_path"]))
    comparison = compare_observables(original["bundle"], json.loads(canonical_bytes(bundle)))
    if comparison["status"] == "REPLAY_MISMATCH":
        # Publish the mismatch evidence too; it never replaces the original reference.
        comparison["scientific_reference_replacement"] = False
    manifest = {
        "schema": "exp03-1-replay-package-v1",
        "replay_protocol": provenance["replay_protocol"],
        "original": provenance["original"],
        "replay_bundle_sha256": hashlib.sha256(raw).hexdigest(),
        "observed_environment": provenance["observed_environment"],
        "environment_sha256": provenance["environment_sha256"],
        "cells": sorted(expected),
        "files": _replay_inventory(root),
        "reload_verification": reloads,
        "comparison": comparison,
        "persistence_counters": {
            "cells": len(expected),
            "native_models": len(expected),
            "preparers": len(expected),
            "calibrators": len(expected),
            "reload_passes": len(reloads),
            "additional_fits": 0,
        },
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    (root / "manifest.json").write_bytes(canonical_bytes(manifest))
    return {
        "path": "replay",
        "manifest_sha256": hashlib.sha256(canonical_bytes(manifest)).hexdigest(),
    }


def read_replay_package(
    folder: Path, manifest: dict[str, Any], bundle: dict[str, Any]
) -> dict[str, Any]:
    """Verify companion inventory, then reproduce and bind each evaluation row to the bundle."""
    from sat_dengue.experiments.exp01 import digest
    from sat_dengue.experiments.exp03_1_preflight import ORIGINAL, REPLAY_PROTOCOL
    from sat_dengue.experiments.exp03_persistence import _safe_directory, load_cell

    reference = manifest["replay"]
    if set(reference) != {"path", "manifest_sha256"} or reference["path"] != "replay":
        raise ValueError("Invalid replay package path")
    root = _safe_directory(folder / "replay")
    if (root / "manifest.json").is_symlink():
        raise ValueError("Symlink replay manifest")
    raw = (root / "manifest.json").read_bytes()
    package = json.loads(raw)
    expected = sorted(row["cell_id"] for row in bundle["cells"])
    if (
        hashlib.sha256(raw).hexdigest() != reference["manifest_sha256"]
        or package.get("schema") != "exp03-1-replay-package-v1"
        or package.get("original") != ORIGINAL
        or package.get("replay_protocol") != REPLAY_PROTOCOL
        or package.get("cells") != expected
        or package.get("replay_bundle_sha256")
        != hashlib.sha256(canonical_bytes(bundle)).hexdigest()
        or package.get("environment_sha256") != digest(package.get("observed_environment"))
        or package.get("files") != _replay_inventory(root)
        or {p.name for p in root.iterdir()} != {*expected, "manifest.json"}
    ):
        raise ValueError("Replay package integrity/linkage changed")
    checks = [verify_replay_cell(root / cell_id) for cell_id in expected]
    if checks != package["reload_verification"]:
        raise ValueError("Replay reload evidence differs")
    by_cell: dict[str, list[Any]] = {}
    for row in bundle["predictions"]:
        by_cell.setdefault(row["cell_id"], []).append(row)
    cells_by_id = {row["cell_id"]: row for row in bundle["cells"]}
    for cell_id in expected:
        cell = load_cell(root / cell_id)
        if cell.metadata["scientific_cell"] != cells_by_id[cell_id]:
            raise ValueError("Replay cell summary differs from bundle")
        frame = _restore_frame(cell.metadata["roles"]["evaluation"]["frame"])
        rows = by_cell[cell_id]
        if len(frame) != len(rows):
            raise ValueError("Replay evaluation membership differs")
        for (_, captured), row in zip(frame.iterrows(), rows, strict=True):
            if (
                str(captured.municipality_code) != row["municipality_code"]
                or str(captured.year_month) != row["origin_month"]
                or str(captured.target_month) != row["target_month"]
                or int(captured[cell.metadata["target"]]) != row["truth"]
                or str(captured.error_type) != row["error_class"]
                or float(captured.score) != row["score"]
                or bool(captured.alert) != row["alert"]
            ):
                raise ValueError("Replay captured evaluation differs from published prediction")
    return package
