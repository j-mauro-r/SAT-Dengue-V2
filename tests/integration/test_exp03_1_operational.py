from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.configuration import validate_parameters
from sat_dengue.experiments import exp03_1_runner
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import load_protocol as load_exp03_protocol
from sat_dengue.experiments.exp03_1_contract import (
    cells,
    counts,
    matrix,
    protocol,
)
from sat_dengue.experiments.exp03_1_contract import (
    digest as protocol_digest,
)
from sat_dengue.experiments.exp03_1_engine import execution_plan, reuse_decision, variant_predictors
from sat_dengue.experiments.exp03_1_evaluation import metrics
from sat_dengue.experiments.exp03_1_preflight import (
    APPROVAL_ENV,
    APPROVAL_SCHEMA,
    _tracking_root,
    authorize,
)
from sat_dengue.experiments.exp03_1_reporting import (
    read_real_bundle,
    validate_real_bundle,
    validate_real_mlflow,
    write_real_bundle,
)
from sat_dengue.experiments.exp03_admission import verified_file
from sat_dengue.hooks import TrackingHooks
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.tracking.experiments import resolve_experiment


def _approval(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": APPROVAL_SCHEMA,
        "experiment_id": "EXP031",
        "authority": "Mauricio",
        "independent_reviewer": "Reviewer_1",
        "preflight_sha256": digest(receipt),
        **{
            name: receipt[name]
            for name in (
                "protocol_sha256",
                "matrix_sha256",
                "source_descriptor_sha256",
                "configuration_sha256",
                "data_version",
                "git_revision",
            )
        },
        "real_execution_authorized": True,
        "m00_refit_authorized": True,
        "variant_refits_authorized": True,
        "retrospective_availability_acknowledged": True,
        "G5_approval": False,
        "champion_selection": False,
    }


def _write_approval(
    monkeypatch: pytest.MonkeyPatch, receipt: dict[str, Any], repo_tmp_path: Path
) -> Path:
    path = repo_tmp_path / "approval.json"
    path.write_text(json.dumps(_approval(receipt)))
    monkeypatch.setenv(APPROVAL_ENV, str(path))
    return path


def _real_bundle() -> dict[str, Any]:
    p = protocol()
    parent = load_exp03_protocol()["design"]
    grid = cells()
    cell_results: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    thresholds: list[dict[str, Any]] = []
    predictions_by_id: dict[str, dict[str, Any]] = {}
    for spec in grid:
        window = next(row for row in parent["windows"] if row["id"] == spec["cut"])
        target_month = window["evaluation"][0]
        origin_month = str(pd.Period(target_month, freq="M") - int(spec["horizon"]))
        cell_id = protocol_digest(spec)
        predictor_names = variant_predictors(parent["variants"]["V09"], spec["variant"])
        score = {"M00": 0.5, "M01": 0.6, "M02": 0.7}[spec["variant"]]
        prediction = {
            "cell_id": cell_id,
            "municipality_code": "01001",
            "origin_month": origin_month,
            "target_month": target_month,
            "score": score,
            "alert": True,
            "truth": 1,
            "error_class": "onset",
            **spec,
            "exposure": 1.0,
        }
        summary = metrics(
            pd.DataFrame(
                [
                    {
                        "truth": 1,
                        "score": score,
                        "alert": True,
                        "municipality_code": "01001",
                        "target_year": int(target_month[:4]),
                        "error_class": "onset",
                    }
                ]
            ),
            exposure=1.0,
        )
        result = {
            **spec,
            "cell_id": cell_id,
            "status": "evaluable",
            "rows": summary["rows"],
            "average_precision": summary["average_precision"],
            "brier": summary["brier"],
            "sensitivity": summary["sensitivity"],
            "false_alerts": summary["false_alerts"],
            "alerts_emitted": summary["alerts_emitted"],
            "threshold": 0.5,
            "budget": p["budget"]["B_primary"],
            "false_alert_limit": 100,
            "metrics": summary,
            "predictors": predictor_names,
            "predictors_sha256": protocol_digest({"predictors": predictor_names}),
            "cohort_sha256": "a" * 64,
        }
        cell_results.append(result)
        predictions.append(prediction)
        predictions_by_id[cell_id] = prediction
        thresholds.append(
            {
                "cell_id": cell_id,
                "threshold": 0.5,
                "budget": p["budget"]["B_primary"],
                "selection_exposure": 100.0,
                "false_alert_limit": 100,
            }
        )

    paired_effects = []
    contrast_definitions = p["contrasts"]
    for name, pair in contrast_definitions.items():
        left_cells = {
            (row["objective"], row["family"], row["horizon"], row["cut"]): row
            for row in cell_results
            if row["variant"] == pair[0]
        }
        right_cells = {
            (row["objective"], row["family"], row["horizon"], row["cut"]): row
            for row in cell_results
            if row["variant"] == pair[1]
        }
        for key in left_cells.keys() & right_cells.keys():
            left = predictions_by_id[left_cells[key]["cell_id"]]
            right = predictions_by_id[right_cells[key]["cell_id"]]
            paired_effects.append(
                {
                    "contrast": name,
                    "left_variant": pair[0],
                    "right_variant": pair[1],
                    "objective": key[0],
                    "family": key[1],
                    "horizon": key[2],
                    "cut": key[3],
                    "municipality_code": left["municipality_code"],
                    "target_month": left["target_month"],
                    "alert_delta": int(left["alert"]) - int(right["alert"]),
                    "score_delta": left["score"] - right["score"],
                }
            )

    from sat_dengue.experiments.exp03_admission import ZERO_EFFECTS

    source_hash = "b" * 64
    files = {"manifest.json": {"sha256": source_hash, "bytes": 1}}
    admission = {
        "schema": "exp03-admission-v1",
        "status": "verified",
        "source_identity_status": "verified",
        "source_kind": "manifest_root_of_trust",
        "expected_source_sha256": source_hash,
        "observed_source_sha256": source_hash,
        "manifest_path": "manifest.json",
        "structural_receipt_sha256": "c" * 64,
        "files": files,
        **ZERO_EFFECTS,
    }
    provenance: dict[str, Any] = {
        "source_admission": admission,
        "protocol_sha256": protocol_digest(p),
        "matrix_sha256": protocol_digest(matrix(p)),
        "configuration_sha256": "d" * 64,
        "source_descriptor_sha256": "e" * 64,
        "code_sha256": "2" * 64,
        "git_revision": "3" * 40,
        "data_version": source_hash,
        "data_sha256": digest(files),
        "admission_sha256": digest(admission),
    }
    approval_record = {
        "schema": "exp03-1-execution-approval-v1",
        "experiment_id": "EXP031",
        "authority": "Mauricio",
        "independent_reviewer": "Reviewer_1",
        "preflight_sha256": "f" * 64,
        "protocol_sha256": protocol_digest(p),
        "matrix_sha256": protocol_digest(matrix(p)),
        "source_descriptor_sha256": provenance["source_descriptor_sha256"],
        "configuration_sha256": provenance["configuration_sha256"],
        "data_version": source_hash,
        "git_revision": provenance["git_revision"],
        "real_execution_authorized": True,
        "m00_refit_authorized": True,
        "variant_refits_authorized": True,
        "retrospective_availability_acknowledged": True,
        "G5_approval": False,
        "champion_selection": False,
    }
    provenance["authorization_receipt_sha256"] = approval_record["preflight_sha256"]
    provenance["approval_record"] = approval_record
    provenance["approval_sha256"] = digest(approval_record)
    reuse = reuse_decision({}, {})
    cell_run_ids = {row["cell_id"]: "child-" + row["cell_id"][:12] for row in cell_results}
    receipt = {
        "schema": "exp03-1-mlflow-receipt-v1",
        "parent_run_id": "parent-test",
        "child_run_ids": list(cell_run_ids.values()),
        "cell_run_ids": cell_run_ids,
        "child_count": 96,
        "protocol_sha256": protocol_digest(p),
    }
    return {
        "schema": "exp03-1-real-scientific-bundle-v1",
        "experiment_id": "EXP031",
        "scientific_id": "EXP03.1",
        "protocol_sha256": protocol_digest(p),
        "matrix_sha256": protocol_digest(matrix(p)),
        "cells": cell_results,
        "predictions": predictions,
        "thresholds": thresholds,
        "contrasts": {
            "definitions": contrast_definitions,
            "paired_effects": paired_effects,
        },
        "execution_plan": execution_plan(reuse),
        "reuse_decision": reuse,
        "provenance": provenance,
        "mlflow_receipt": receipt,
        "execution_counters": {
            "real_private_reads": 1,
            "real_reservations": 1,
            "real_model_fits": 96,
            "real_calibrator_fits": 96,
            "real_threshold_selections": 96,
            "permanent_mlflow_writes": 0,
        },
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "evidence_type": "authorized_retrospective",
    }


def test_authorization_is_explicit_bound_and_separate_from_g5(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt = {
        "git_dirty": False,
        "protocol_sha256": "a" * 64,
        "matrix_sha256": "b" * 64,
        "source_descriptor_sha256": "c" * 64,
        "configuration_sha256": "d" * 64,
        "data_version": "e" * 64,
        "git_revision": "f" * 40,
    }
    monkeypatch.setattr("sat_dengue.experiments.exp03_1_preflight.preflight", lambda *_: receipt)
    monkeypatch.chdir(Path.cwd())
    with pytest.raises(PermissionError):
        authorize(receipt, {})
    _write_approval(monkeypatch, receipt, repo_tmp_path)
    assert authorize(receipt, {})["G5_approval"] is False
    altered = {**receipt, "matrix_sha256": "0" * 64}
    with pytest.raises(PermissionError):
        authorize(altered, {})


def test_sources_are_not_admitted_before_authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    def deny(*_: Any, **__: Any) -> Any:
        raise PermissionError("denied")

    monkeypatch.setattr(exp03_1_runner, "authorize", deny)
    monkeypatch.setattr(
        "sat_dengue.experiments.exp03_admission.admit_sources",
        lambda *_: pytest.fail("source admission happened before authorization"),
    )
    with pytest.raises(PermissionError):
        exp03_1_runner.load_authorized_sources({}, {})


def test_official_coverage_controls_zero_case_imputation() -> None:
    panel = pd.DataFrame(
        {
            "municipality_code": ["A", "B", "C"],
            "year_month": ["2020-01", "2020-02", "2020-03"],
            "dengue_notifications_count": [pd.NA, 7.0, 2.0],
            "dengue_grave_notifications_count": [pd.NA, 1.0, 0.0],
            "climate_value": [1.0, 2.0, 3.0],
        }
    )
    coverage = pd.DataFrame(
        {
            "municipality_code": ["A", "B", "D"],
            "year_month": ["2020-01", "2020-02", "2020-04"],
            "covered": [True, False, True],
        }
    )
    result = exp03_1_runner._apply_coverage(panel, coverage).set_index(
        ["municipality_code", "year_month"]
    )
    assert result.loc[("A", "2020-01"), "dengue_notifications_count"] == 0
    assert result.loc[("D", "2020-04"), "dengue_notifications_count"] == 0
    assert pd.isna(result.loc[("B", "2020-02"), "dengue_notifications_count"])
    assert pd.isna(result.loc[("C", "2020-03"), "dengue_notifications_count"])
    assert pd.isna(result.loc[("D", "2020-04"), "climate_value"])


def test_source_manifest_payload_hash_tampering_is_rejected(
    repo_tmp_path: Path,
) -> None:
    path = repo_tmp_path / "manifest.json"
    raw = b'{"fixture":"generated"}'
    path.write_bytes(raw)
    relative = path.relative_to(Path.cwd()).as_posix()
    expected = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    assert verified_file(relative, expected, read=True) == raw
    path.write_bytes(b'{"fixture":"altered"}')
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        verified_file(relative, expected)


def test_frozen_grid_and_m00_refit_fallback_are_exact() -> None:
    assert len(cells()) == counts()["maximum_refit_cells"] == 96
    identities = protocol()["reuse_identity_fields"]
    matching = {name: "a" * 64 for name in identities}
    reused = reuse_decision(matching, matching)
    assert reused["decision"] == "reused"
    assert execution_plan(reused)["counts"] == {"total": 96, "reused": 36, "new_fits": 60}
    mismatched = {**matching, "budget": "b" * 64}
    refitted = reuse_decision(matching, mismatched)
    assert refitted["decision"] == "refitted"
    assert execution_plan(refitted)["counts"] == {"total": 96, "reused": 0, "new_fits": 96}


def test_executor_walks_96_cells_with_fit_and_calibration_doubles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = load_exp03_protocol()["design"]
    base_predictors = parent["variants"]["V09"]
    all_predictors = [
        *base_predictors,
        *protocol()["predictors"]["recent"],
        *protocol()["predictors"]["change"],
    ]
    common = pd.DataFrame(
        {
            "municipality_code": ["01001", "01002"],
            "year_month": ["2019-10", "2019-10"],
            "target_month": ["2019-12", "2019-12"],
            "target_year": [2019, 2019],
            "onset_target": [0, 1],
            "excess_target": [0, 1],
            "eligible_at_t": [True, True],
            "error_type": ["no_excess", "onset"],
            **{
                name: (["base", "base"] if name == "zona_canal_t" else [0.1, 0.9])
                for name in all_predictors
            },
        }
    )
    monkeypatch.setattr(exp03_1_runner, "_prepare", lambda *_: common.copy())
    monkeypatch.setattr(
        exp03_1_runner,
        "paired_cohort",
        lambda frame, **_: (frame.copy(), pd.DataFrame()),
    )

    def role_parts(frame: pd.DataFrame, window: dict[str, Any]) -> dict[str, pd.DataFrame]:
        target_month = window["evaluation"][0]
        rows = frame.copy()
        rows["target_month"] = target_month
        rows["target_year"] = int(target_month[:4])
        rows["year_month"] = [
            str(pd.Period(target_month, freq="M") - 1),
            str(pd.Period(target_month, freq="M") - 1),
        ]
        return {name: rows.copy() for name in ("train", "calibration", "selection", "evaluation")}

    def exposure_table(parts: dict[str, pd.DataFrame]) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "role": role,
                    "monitored_exposure": 10.0,
                    "municipality_code": municipality,
                    "target_year": int(part.target_year.iloc[0]),
                }
                for role in ("selection", "evaluation")
                for part in [parts[role]]
                for municipality in ("01001", "01002")
            ]
        )

    monkeypatch.setattr("sat_dengue.experiments.exp03_features.role_parts", role_parts)
    monkeypatch.setattr("sat_dengue.experiments.exp03_features.exposure_table", exposure_table)
    calls = {"fit": 0, "calibration": 0, "threshold": 0}

    class Model:
        def predict(self, frame: pd.DataFrame) -> pd.Series:
            return pd.Series([0.2, 0.8], index=frame.index)

    def fit(*_: Any) -> Model:
        calls["fit"] += 1
        return Model()

    def calibrate(scores: pd.Series, *_: Any) -> Any:
        calls["calibration"] += 1
        return lambda values: values

    real_select = exp03_1_runner.select_threshold

    def select(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls["threshold"] += 1
        return real_select(*args, **kwargs)

    monkeypatch.setattr(exp03_1_runner, "select_threshold", select)
    result = exp03_1_runner.execute_matrix(common, {}, fit=fit, calibrate=calibrate)
    assert len(result["cells"]) == 96
    assert result["execution_plan"]["counts"] == {
        "total": 96,
        "reused": 0,
        "new_fits": 96,
    }
    assert result["execution_counters"] == {
        "real_private_reads": 0,
        "real_reservations": 0,
        "real_model_fits": 0,
        "real_calibrator_fits": 0,
        "real_threshold_selections": 0,
        "permanent_mlflow_writes": 0,
    }
    assert calls == {"fit": 96, "calibration": 96, "threshold": 96}


def test_real_bundle_closes_grid_predictions_contrasts_and_manifest() -> None:
    bundle = _real_bundle()
    validate_real_bundle(bundle)
    incomplete = {**bundle, "predictions": bundle["predictions"][:-1]}
    with pytest.raises(ValueError):
        validate_real_bundle(incomplete)


def test_real_bundle_manifest_hash_is_verified() -> None:
    bundle = _real_bundle()
    root = Path("tmp/kedro-migration/exp03-1-runs")
    root.mkdir(parents=True, exist_ok=True)
    destination = root / ("focused-test-" + uuid.uuid4().hex)
    try:
        publication = write_real_bundle(
            {
                "protocol_sha256": bundle["protocol_sha256"],
                "matrix_sha256": bundle["matrix_sha256"],
                "cells": bundle["cells"],
                "predictions": bundle["predictions"],
                "thresholds": bundle["thresholds"],
                "contrasts": bundle["contrasts"],
                "execution_plan": bundle["execution_plan"],
                "reuse_decision": bundle["reuse_decision"],
                "execution_counters": bundle["execution_counters"],
            },
            bundle["provenance"],
            bundle["mlflow_receipt"],
            destination,
        )
        read_real_bundle(destination, publication["manifest"]["bundle_id"])
        (destination / "bundle.json").write_bytes(b"{}")
        with pytest.raises(ValueError):
            read_real_bundle(destination, publication["manifest"]["bundle_id"])
    finally:
        if destination.exists():
            shutil.rmtree(destination)


def test_mlflow_lineage_is_read_only_verified_and_bound_to_results() -> None:
    bundle = _real_bundle()
    root = Path(tempfile.mkdtemp(prefix="exp03-1-mlflow-", dir=Path.cwd() / "tmp"))
    database = root / "tracking.sqlite"
    bundle_id = "f" * 64
    p = protocol()
    receipt = bundle["mlflow_receipt"]
    try:
        with sqlite3.connect(database) as connection:
            connection.executescript(
                """
                CREATE TABLE experiments (experiment_id TEXT, name TEXT);
                CREATE TABLE experiment_tags (experiment_id TEXT, key TEXT, value TEXT);
                CREATE TABLE runs (run_uuid TEXT, status TEXT, experiment_id TEXT);
                CREATE TABLE tags (run_uuid TEXT, key TEXT, value TEXT);
                CREATE TABLE params (run_uuid TEXT, key TEXT, value TEXT);
                CREATE TABLE metrics (run_uuid TEXT, key TEXT, value REAL);
                """
            )
            connection.execute(
                "INSERT INTO experiments VALUES (?, ?)",
                ("1", p["mlflow"]["experiment_name"]),
            )
            connection.execute(
                "INSERT INTO experiment_tags VALUES (?, ?, ?)",
                ("1", "protocol.EXP031", protocol_digest(p)),
            )
            parent_tags = {
                "experiment_id": "EXP031",
                "protocol_sha256": protocol_digest(p),
                "mlflow_receipt_sha256": digest(receipt),
                "status": "verified",
                "bundle_id": bundle_id,
            }
            for key, value in parent_tags.items():
                connection.execute("INSERT INTO tags VALUES (?, ?, ?)", ("parent-test", key, value))
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?)", ("parent-test", "FINISHED", "1")
            )
            for cell in bundle["cells"]:
                run_id = receipt["cell_run_ids"][cell["cell_id"]]
                connection.execute("INSERT INTO runs VALUES (?, ?, ?)", (run_id, "FINISHED", "1"))
                tags = {
                    **p["mlflow"]["required_conceptual_tags"],
                    "mlflow.parentRunId": "parent-test",
                    "status": "verified",
                    "experiment_id": "EXP031",
                    "protocol_sha256": protocol_digest(p),
                    "cell_id": cell["cell_id"],
                    "variant": cell["variant"],
                    "objective": cell["objective"],
                    "family": cell["family"],
                    "horizon": str(cell["horizon"]),
                    "cut": cell["cut"],
                }
                connection.executemany(
                    "INSERT INTO tags VALUES (?, ?, ?)",
                    [(run_id, key, value) for key, value in tags.items()],
                )
                params = {
                    "family": cell["family"],
                    "horizon": str(cell["horizon"]),
                    "objective": cell["objective"],
                    "window": cell["cut"],
                }
                connection.executemany(
                    "INSERT INTO params VALUES (?, ?, ?)",
                    [(run_id, key, value) for key, value in params.items()],
                )
                for key, metric_name in (
                    ("average_precision", "average_precision"),
                    ("brier", "brier"),
                    ("false_alerts", "false_alerts"),
                    ("rows", "evaluable_rows"),
                ):
                    value = cell["metrics"].get(key)
                    if value is not None:
                        connection.execute(
                            "INSERT INTO metrics VALUES (?, ?, ?)",
                            (run_id, metric_name, float(value)),
                        )
        validate_real_mlflow(bundle, str(root.relative_to(Path.cwd())), bundle_id)
        with sqlite3.connect(database) as connection:
            connection.execute(
                "UPDATE tags SET value = ? WHERE run_uuid = ? AND key = ?",
                ("wrong", receipt["child_run_ids"][0], "variant"),
            )
        with pytest.raises(ValueError):
            validate_real_mlflow(bundle, str(root.relative_to(Path.cwd())), bundle_id)
    finally:
        shutil.rmtree(root)


def test_flat_cells_publish_and_finish_against_temporary_mlflow() -> None:
    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset
    from sat_dengue.experiments.exp03_1_reporting import validate_real_bundle
    from sat_dengue.tracking.exp03_1 import Exp03_1Tracking

    fixture = _real_bundle()
    tracking_dir = Path(tempfile.mkdtemp(prefix="exp03-1-finish-", dir=Path.cwd() / "tmp"))
    tracking_root = tracking_dir.relative_to(Path.cwd()).as_posix()
    bundle_root = Path("tmp/kedro-migration/exp03-1-runs")
    execution_id = uuid.uuid4().hex
    bundle_path = bundle_root / execution_id
    provenance = {**fixture["provenance"], "tracking_root": tracking_root}
    result = {
        name: fixture[name]
        for name in (
            "protocol_sha256",
            "matrix_sha256",
            "cells",
            "predictions",
            "thresholds",
            "contrasts",
            "execution_plan",
            "reuse_decision",
            "execution_counters",
        )
    }
    tracker = None
    try:
        tracker = Exp03_1Tracking(
            execution_id,
            tracking_root,
            protocol(),
            provenance,
        )
        dataset = Exp03_1BundleDataset(str(bundle_root))
        dataset.save(
            {
                "tracker": tracker,
                "result": result,
                "provenance": provenance,
                "reservation": f"tmp/{execution_id}.reservation",
            }
        )

        assert len(result["cells"]) == 96
        assert all("result" not in cell for cell in result["cells"])
        publication = dataset._publication
        assert publication is not None
        validated = read_real_bundle(
            Path(publication["path"]),
            publication["manifest"]["bundle_id"],
        )
        validate_real_bundle(validated["bundle"])
        validate_real_mlflow(
            validated["bundle"],
            tracking_root,
            publication["manifest"]["bundle_id"],
        )

        receipt = validated["bundle"]["mlflow_receipt"]
        connection = sqlite3.connect(tracking_dir / "tracking.sqlite")
        try:
            runs = connection.execute(
                "SELECT run_uuid, status FROM runs WHERE run_uuid IN (?, "
                + ",".join("?" for _ in receipt["child_run_ids"])
                + ")",
                [receipt["parent_run_id"], *receipt["child_run_ids"]],
            ).fetchall()
            assert len(runs) == 97
            assert {status for _, status in runs} == {"FINISHED"}
            run_ids = {run_id for run_id, _ in runs}
            assert receipt["parent_run_id"] in run_ids
            assert set(receipt["child_run_ids"]) <= run_ids

            for cell in result["cells"]:
                run_id = receipt["cell_run_ids"][cell["cell_id"]]
                logged = dict(
                    connection.execute(
                        "SELECT key, value FROM metrics WHERE run_uuid = ?",
                        (run_id,),
                    ).fetchall()
                )
                expected = {
                    "average_precision": cell["average_precision"],
                    "brier": cell["brier"],
                    "false_alerts": cell["false_alerts"],
                    "evaluable_rows": cell["rows"],
                }
                for name, value in expected.items():
                    assert logged[name] == pytest.approx(float(value))
        finally:
            connection.close()
    finally:
        if tracker is not None and not tracker.local.terminal:
            tracker.fail()
        if bundle_path.exists():
            shutil.rmtree(bundle_path)
        shutil.rmtree(tracking_dir)
        if bundle_root.exists() and not any(bundle_root.iterdir()):
            bundle_root.rmdir()


def test_failed_post_validation_marks_all_temporary_runs_failed(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from kedro.io import DatasetError

    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset
    from sat_dengue.tracking.exp03_1 import Exp03_1Tracking

    fixture = _real_bundle()
    tracking_dir = Path(
        tempfile.mkdtemp(prefix="exp03-1-validation-failure-", dir=Path.cwd() / "tmp")
    )
    tracking_root = tracking_dir.relative_to(Path.cwd()).as_posix()
    bundle_root = Path("tmp/kedro-migration/exp03-1-runs")
    execution_id = uuid.uuid4().hex
    bundle_path = bundle_root / execution_id
    provenance = {**fixture["provenance"], "tracking_root": tracking_root}
    result = {
        name: fixture[name]
        for name in (
            "protocol_sha256",
            "matrix_sha256",
            "cells",
            "predictions",
            "thresholds",
            "contrasts",
            "execution_plan",
            "reuse_decision",
            "execution_counters",
        )
    }

    def reject_validation(*args: Any, **kwargs: Any) -> None:
        raise ValueError("forced post-publication validation failure")

    monkeypatch.setattr(
        "sat_dengue.experiments.exp03_1_reporting.validate_real_mlflow",
        reject_validation,
    )
    tracker = None
    try:
        tracker = Exp03_1Tracking(execution_id, tracking_root, protocol(), provenance)
        dataset = Exp03_1BundleDataset(str(bundle_root))
        with pytest.raises(DatasetError, match="forced post-publication"):
            dataset.save(
                {
                    "tracker": tracker,
                    "result": result,
                    "provenance": provenance,
                    "reservation": f"tmp/{execution_id}.reservation",
                }
            )

        assert dataset._publication is None
        assert tracker.local.terminal
        assert "verified" not in capsys.readouterr().out
        with sqlite3.connect(tracking_dir / "tracking.sqlite") as connection:
            run_ids = [tracker.parent, *tracker.children]
            placeholders = ",".join("?" for _ in run_ids)
            runs = connection.execute(
                f"SELECT run_uuid, status FROM runs WHERE run_uuid IN ({placeholders})",
                run_ids,
            ).fetchall()
            assert len(runs) == 97
            assert {status for _, status in runs} == {"FAILED"}
            tags = connection.execute(
                f"SELECT run_uuid, value FROM tags "
                f"WHERE key = 'status' AND run_uuid IN ({placeholders})",
                run_ids,
            ).fetchall()
            assert len(tags) == 97
            assert {status for _, status in tags} == {"failed"}
    finally:
        if tracker is not None and not tracker.local.terminal:
            tracker.fail()
        if bundle_path.exists():
            shutil.rmtree(bundle_path)
        shutil.rmtree(tracking_dir)
        if bundle_root.exists() and not any(bundle_root.iterdir()):
            bundle_root.rmdir()


def test_mlflow_rejects_unreceipted_additional_child() -> None:
    bundle = _real_bundle()
    root = Path(tempfile.mkdtemp(prefix="exp03-1-extra-child-", dir=Path.cwd() / "tmp"))
    database = root / "tracking.sqlite"
    receipt = bundle["mlflow_receipt"]
    try:
        with sqlite3.connect(database) as connection:
            connection.executescript(
                """
                CREATE TABLE experiments (experiment_id TEXT, name TEXT);
                CREATE TABLE experiment_tags (experiment_id TEXT, key TEXT, value TEXT);
                CREATE TABLE runs (run_uuid TEXT, status TEXT, experiment_id TEXT);
                CREATE TABLE tags (run_uuid TEXT, key TEXT, value TEXT);
                """
            )
            connection.execute(
                "INSERT INTO experiments VALUES (?, ?)",
                ("1", protocol()["mlflow"]["experiment_name"]),
            )
            connection.execute(
                "INSERT INTO experiment_tags VALUES (?, ?, ?)",
                ("1", "protocol.EXP031", protocol_digest(protocol())),
            )
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?)",
                (receipt["parent_run_id"], "RUNNING", "1"),
            )
            for run_id in receipt["child_run_ids"]:
                connection.execute(
                    "INSERT INTO runs VALUES (?, ?, ?)",
                    (run_id, "RUNNING", "1"),
                )
                connection.execute(
                    "INSERT INTO tags VALUES (?, ?, ?)",
                    (run_id, "mlflow.parentRunId", receipt["parent_run_id"]),
                )
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?)",
                ("unreceipted-extra-child", "RUNNING", "1"),
            )
            connection.execute(
                "INSERT INTO tags VALUES (?, ?, ?)",
                (
                    "unreceipted-extra-child",
                    "mlflow.parentRunId",
                    receipt["parent_run_id"],
                ),
            )
        with pytest.raises(ValueError, match="exactly the 96 receipted children"):
            validate_real_mlflow(
                bundle,
                str(root.relative_to(Path.cwd())),
            )
    finally:
        shutil.rmtree(root)


def test_exp03_1_preflight_pipeline_receives_its_source_descriptor() -> None:
    assert register_pipelines()["exp03_1_preflight"].inputs() == {
        "parameters",
        "exp03_1_sources",
    }


@pytest.mark.parametrize(
    "root",
    [
        "tmp/kedro-migration/exp03-1-runs",
        "tmp/kedro-migration/exp03-1-runs/tracking",
        "tmp/../external",
        "/tmp/scientific-mlflow",
    ],
)
def test_tracking_root_is_local_and_separate(monkeypatch: pytest.MonkeyPatch, root: str) -> None:
    monkeypatch.setattr(
        "sat_dengue.experiments.exp03_1_preflight.exp03_tracking_root",
        lambda: root,
    )
    with pytest.raises(ValueError, match="separate repository-local tmp root"):
        _tracking_root()


@pytest.mark.parametrize("profile", ["exp03_1", "exp03_1_preflight"])
def test_exp03_1_parameters_are_registered_and_unknown_identities_rejected(
    profile: str,
) -> None:
    params = {
        "profile": profile,
        "tracking": "enabled",
        "experiment_id": "EXP031",
    }
    assert validate_parameters(params) == params
    assert resolve_experiment("EXP031")["pipeline"] == "exp03_1"
    with pytest.raises(ValueError, match="EXP03.1 requires"):
        validate_parameters({**params, "experiment_id": "EXP999"})
    with pytest.raises(ValueError, match="Unregistered experiment_id"):
        resolve_experiment("EXP999")
    with pytest.raises(ValueError, match="Unknown profile"):
        validate_parameters({**params, "profile": "exp03_999"})


@pytest.mark.parametrize("pipeline", ["exp03_1", "exp03_1_preflight"])
def test_exp03_1_tracking_is_delegated_to_its_dedicated_infrastructure(
    monkeypatch: pytest.MonkeyPatch, pipeline: str
) -> None:
    from kedro.io import DataCatalog, MemoryDataset

    def reject_global_tracker(*_: Any, **__: Any) -> Any:
        pytest.fail("EXP03.1 must not create the global tracker")

    monkeypatch.setattr("sat_dengue.tracking.local.LocalTracking", reject_global_tracker)
    catalog = DataCatalog(
        {
            "parameters": MemoryDataset(
                {
                    "profile": pipeline,
                    "tracking": "enabled",
                    "experiment_id": "EXP031",
                }
            )
        }
    )
    hooks = TrackingHooks()
    hooks.before_pipeline_run({"pipeline_name": pipeline}, catalog)

    assert hooks.tracker is None


def test_exp03_1_tracking_rejects_pipeline_profile_mismatch() -> None:
    from kedro.io import DataCatalog, MemoryDataset

    catalog = DataCatalog(
        {
            "parameters": MemoryDataset(
                {
                    "profile": "exp03_1_preflight",
                    "tracking": "enabled",
                    "experiment_id": "EXP031",
                }
            )
        }
    )

    with pytest.raises(ValueError, match="EXP03.1 profile must match its exact pipeline"):
        TrackingHooks().before_pipeline_run({"pipeline_name": "exp03_1"}, catalog)


def test_training_tracking_still_uses_the_global_tracker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from kedro.io import DataCatalog, MemoryDataset

    class FakeTracking:
        def __init__(self, pipeline: str, run_id: str, *, experiment_id: str | None = None) -> None:
            self.pipeline = pipeline
            self.run_id = run_id
            self.experiment_id = experiment_id

    monkeypatch.setattr("sat_dengue.tracking.local.LocalTracking", FakeTracking)
    catalog = DataCatalog(
        {"parameters": MemoryDataset({"profile": "training_synthetic", "tracking": "enabled"})}
    )
    hooks = TrackingHooks()
    hooks.before_pipeline_run(
        {"pipeline_name": "training_synthetic", "session_id": "training-test"},
        catalog,
    )

    assert isinstance(hooks.tracker, FakeTracking)
    assert hooks.tracker.pipeline == "training_synthetic"
    assert hooks.tracker.run_id == "training-test"


def test_exp03_1_bundle_dataset_accepts_exact_relative_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset
    from sat_dengue.experiments.exp03_1_preflight import OUTPUT_ROOT

    monkeypatch.chdir(tmp_path)

    dataset = Exp03_1BundleDataset(OUTPUT_ROOT)

    assert dataset._root == Path(OUTPUT_ROOT)


def test_exp03_1_bundle_dataset_accepts_exact_repository_absolute_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset
    from sat_dengue.experiments.exp03_1_preflight import OUTPUT_ROOT

    monkeypatch.chdir(tmp_path)
    absolute_root = tmp_path / OUTPUT_ROOT

    dataset = Exp03_1BundleDataset(str(absolute_root))

    assert dataset._root == Path(OUTPUT_ROOT)


@pytest.mark.parametrize(
    "filepath",
    ["tmp/kedro-migration/exp03-1-runs/other", "/tmp/scientific-mlflow"],
)
def test_exp03_1_bundle_dataset_rejects_other_absolute_roots(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, filepath: str
) -> None:
    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset

    monkeypatch.chdir(tmp_path)
    absolute_path = filepath if Path(filepath).is_absolute() else str(tmp_path / filepath)

    with pytest.raises(ValueError, match="protected repository tmp path"):
        Exp03_1BundleDataset(absolute_path)


@pytest.mark.parametrize(
    "symlink_component",
    ["tmp", "tmp/kedro-migration", "tmp/kedro-migration/exp03-1-runs"],
)
def test_exp03_1_bundle_dataset_rejects_symlink_components(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, symlink_component: str
) -> None:
    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset
    from sat_dengue.experiments.exp03_1_preflight import OUTPUT_ROOT

    repository_root = tmp_path / "repository"
    repository_root.mkdir()
    link = repository_root / symlink_component
    link.parent.mkdir(parents=True, exist_ok=True)
    target = tmp_path / f"target-{Path(symlink_component).name}"
    target.mkdir()
    link.symlink_to(target, target_is_directory=True)
    monkeypatch.chdir(repository_root)

    with pytest.raises(ValueError, match="protected repository tmp path"):
        Exp03_1BundleDataset(str(repository_root / OUTPUT_ROOT))


def test_exp03_1_bundle_dataset_materialized_kedro_filepath_constructs_without_writing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from sat_dengue.datasets.exp03_1 import Exp03_1BundleDataset
    from sat_dengue.experiments.exp03_1_preflight import OUTPUT_ROOT

    monkeypatch.chdir(tmp_path)
    filepath = str(tmp_path / OUTPUT_ROOT)

    dataset = Exp03_1BundleDataset(filepath)

    assert dataset._describe() == {
        "filepath": OUTPUT_ROOT,
        "mode": "atomic_no_overwrite_real_only",
    }
    assert not (tmp_path / OUTPUT_ROOT).exists()
