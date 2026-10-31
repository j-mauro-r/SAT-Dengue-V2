"""Generated-only replay persistence and historical-format regression evidence."""

from __future__ import annotations

import copy
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from test_exp03_1_operational import _real_bundle

from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments import exp03_1_preflight as preflight
from sat_dengue.experiments import exp03_1_reporting as reporting
from sat_dengue.experiments import exp03_1_validate as validation
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import load_protocol
from sat_dengue.experiments.exp03_1_contract import cells
from sat_dengue.experiments.exp03_persistence import (
    NativePredictor,
    SigmoidCalibrator,
    fit_calibration,
    fit_native,
    load_cell,
)


def _payload(
    spec: dict[str, Any],
    predictor: Any,
    calibrator: Any,
    frame: Any,
    result: dict[str, Any],
    threshold: float | None,
) -> dict[str, Any]:
    raw = predictor.predict(frame[predictor.columns])
    scores = calibrator(raw)
    return {
        "result": result,
        "predictor": predictor,
        "calibrator": calibrator,
        "threshold_selection": {"threshold": threshold, "whole_score_ties": True},
        "window": {"id": spec["cut"]},
        "target": "onset_target",
        "parts": {role: frame for role in ("train", "calibration", "selection", "evaluation")},
        "roles": {role: frame for role in ("train", "calibration", "selection", "evaluation")},
        "cohort_ledger": pd.DataFrame(),
        "raw_scores": {role: raw for role in ("calibration", "selection", "evaluation")},
        "scores": {role: scores for role in ("calibration", "selection", "evaluation")},
        "alerts": pd.Series(False, index=frame.index)
        if threshold is None
        else scores.ge(threshold),
    }


@pytest.mark.parametrize("family", ["gam", "lightgbm", "xgboost"])
def test_native_replay_roundtrip_without_refits(
    family: str,
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Small generated input only; never enter the scientific source loader or runner.
    spec = next(row for row in cells() if row["family"] == family)
    frame = pd.DataFrame(
        {
            "municipality_code": [f"{i:05d}" for i in range(40)],
            "year_month": ["2019-10"] * 40,
            "target_month": ["2019-11"] * 40,
            "target_year": [2019] * 40,
            "onset_target": [0, 1] * 20,
            "excess_target": [0, 1] * 20,
            "eligible_at_t": [True] * 40,
            "error_type": ["no_excess", "onset"] * 20,
            "signal": [0.12345678901234566 + i / 100 for i in range(40)],
        },
        index=pd.Index(range(80, 0, -2), name="source_row"),
    )
    frame["signal__latest_source_month"] = "2019-09"
    params = dict(load_protocol()["design"]["families"][family])
    if family != "gam":
        params["n_estimators"] = 3
    predictor = fit_native(family, frame[["signal"]], frame.onset_target, params, 42)
    raw = predictor.predict(frame[["signal"]])
    calibrator = fit_calibration(raw, frame.onset_target, 42)
    threshold = None if family == "gam" else float(calibrator(raw).iloc[0])
    result = {
        **spec,
        "cell_id": digest(spec),
        "predictors": ["signal"],
        "threshold": threshold,
        "budget": 1.0,
    }
    capture = repo_tmp_path / family
    capture.mkdir()
    payload = _payload(spec, predictor, calibrator, frame, result, threshold)
    payload["source_audit"] = {
        "keys": frame[["municipality_code", "year_month"]].copy(),
        "source_months": pd.DataFrame({"signal": ["2019-09"] * len(frame)}, index=frame.index),
        "source_event_months": pd.DataFrame(
            {"signal": [("2019-09", "2018-09")] * len(frame)}, index=frame.index
        ),
    }
    reporting.capture_replay_cell(payload, capture, {"synthetic": True})
    cell_path = capture / digest(spec)

    def forbidden(*_: Any, **__: Any) -> Any:
        raise AssertionError("No fit is allowed during replay reload")

    monkeypatch.setattr("sat_dengue.model_training.candidate_families.fit_model", forbidden)
    monkeypatch.setattr("sat_dengue.experiments.exp03_persistence.fit_calibration", forbidden)
    restored = load_cell(cell_path)
    assert restored.predictor.model.preparer == predictor.model.preparer
    assert restored.calibrator == calibrator
    dates = reporting._restore_frame(
        restored.metadata["roles"]["evaluation"]["source_dates"]["source_months"]
    )
    assert dates.signal.tolist() == ["2019-09"] * len(frame)
    assert dates.index.equals(frame.index)
    events = reporting._restore_frame(
        restored.metadata["roles"]["evaluation"]["source_dates"]["source_event_months"]
    )
    assert events.signal.tolist() == [["2019-09", "2018-09"]] * len(frame)
    stored = reporting._restore_frame(restored.metadata["roles"]["evaluation"]["frame"])
    pd.testing.assert_frame_equal(stored[frame.columns], frame)
    report = reporting.verify_replay_cell(cell_path)
    assert report["status"] == "pass" and report["fits"] == 0
    pd.testing.assert_series_equal(
        restored.predict(frame[["signal"]]).alert, stored.alert, check_names=False
    )
    with pytest.raises(FileExistsError):
        reporting.capture_replay_cell(
            _payload(spec, predictor, calibrator, frame, result, threshold),
            capture,
            {"synthetic": True},
        )
    (cell_path / "model.native").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="bytes changed"):
        load_cell(cell_path)
    external = repo_tmp_path.parent.parent / "forbidden-replay-external"
    with pytest.raises(ValueError, match="repository-local tmp"):
        reporting.capture_replay_cell(
            _payload(spec, predictor, calibrator, frame, result, threshold),
            external,
            {"synthetic": True},
        )
    link = repo_tmp_path / "link"
    link.symlink_to(capture, target_is_directory=True)
    with pytest.raises(ValueError, match="repository-local tmp"):
        load_cell(link / digest(spec))


def test_comparison_enforces_numeric_and_discrete_contract() -> None:
    original = _real_bundle()
    assert (
        validation.compare_observables(original, copy.deepcopy(original))["status"]
        == "EXACT_OBSERVABLE_REPLAY"
    )
    numeric = copy.deepcopy(original)
    # Stay within the same reliability bin and preserve ties/ranking for each cell.
    numeric["predictions"][1]["score"] += 5e-13
    assert (
        validation.compare_observables(original, numeric)["status"]
        == "NUMERICALLY_COMPATIBLE_REPLAY"
    )
    changes = [
        ("prediction", "score", original["predictions"][0]["score"] - 5e-13),  # bin boundary
        ("prediction", "score", original["predictions"][0]["score"] + 2e-12),
        ("prediction", "alert", False),
        ("prediction", "truth", 0),
        ("prediction", "exposure", 1.0 + 5e-13),
        ("prediction", "error_class", "continuation"),
        ("cell", "threshold", 0.5 + 5e-13),
        ("cell", "cohort_sha256", "f" * 64),
    ]
    for kind, field, value in changes:
        changed = copy.deepcopy(original)
        changed["predictions" if kind == "prediction" else "cells"][0][field] = value
        assert validation.compare_observables(original, changed)["status"] == "REPLAY_MISMATCH"
    missing = copy.deepcopy(original)
    missing["predictions"].pop()
    assert validation.compare_observables(original, missing)["status"] == "REPLAY_MISMATCH"
    tied = copy.deepcopy(original)
    tied["predictions"].append(copy.deepcopy(tied["predictions"][0]))
    untied = copy.deepcopy(tied)
    untied["predictions"][-1]["score"] += 5e-13
    assert validation.compare_observables(tied, untied)["status"] == "REPLAY_MISMATCH"
    report = validation.compare_observables(original, original)
    assert set(report["historical_intermediates"].values()) == {"NOT_COMPARABLE"}
    assert validation.compare_observables(None, original)["status"] == "NOT_COMPARABLE"


def test_publication_compares_canonical_numeric_thresholds(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = _real_bundle()
    bundle = copy.deepcopy(original)
    bundle["cells"][0]["threshold"] = np.float64(original["cells"][0]["threshold"])
    assert validation.compare_observables(original, bundle)["differences"] == ["cells/0/threshold"]
    capture = repo_tmp_path / "capture"
    capture.mkdir()
    for row in bundle["cells"]:
        (capture / row["cell_id"]).mkdir()
    staging = repo_tmp_path / "staging"
    staging.mkdir()
    monkeypatch.setattr(validation, "read_original", lambda *_: {"bundle": original})
    monkeypatch.setattr(reporting, "verify_replay_cell", lambda *_: {"status": "pass"})
    provenance = {
        "original_bundle_path": str(repo_tmp_path / "original"),
        "replay_protocol": preflight.REPLAY_PROTOCOL,
        "original": preflight.ORIGINAL,
        "observed_environment": {},
        "environment_sha256": digest({}),
    }
    raw = canonical_bytes(bundle)
    reporting._publish_replay(
        {"cells": bundle["cells"], "replay_capture_root": str(capture)},
        provenance,
        bundle,
        staging,
        raw,
    )
    package = json.loads((staging / "replay/manifest.json").read_bytes())
    assert package["comparison"]["status"] == "EXACT_OBSERVABLE_REPLAY"
    assert package["comparison"]["differences"] == []
    assert type(bundle["cells"][0]["threshold"]) is np.float64
    assert canonical_bytes(bundle) == raw == canonical_bytes(original)


def _validate_generated_comparison(
    monkeypatch: pytest.MonkeyPatch,
    original: dict[str, Any],
    bundle: dict[str, Any],
    stored: dict[str, Any],
) -> dict[str, Any]:
    # Double only the verified reader/lineage boundary; compare real persisted JSON values.
    persisted = json.loads(canonical_bytes(bundle))
    persisted["provenance"]["original_bundle_path"] = "unused-original"
    monkeypatch.setattr(
        validation,
        "read_real_bundle",
        lambda *_: {
            "bundle": persisted,
            "manifest": {"bundle_id": "generated-only"},
            "replay": {
                "schema": "exp03-1-replay-package-v1",
                "replay_protocol": preflight.REPLAY_PROTOCOL,
                "comparison": stored,
            },
        },
    )
    monkeypatch.setattr(
        validation, "read_original", lambda *_: {"bundle": json.loads(canonical_bytes(original))}
    )
    monkeypatch.setattr(validation, "validate_real_mlflow", lambda *_: None)
    return validation.validate(Path("unused-replay"), "generated-only", "unused-tracking")


def test_validator_records_canonical_threshold_type_correction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _real_bundle()
    bundle = copy.deepcopy(original)
    for row in bundle["cells"][:2]:
        row["threshold"] = np.float64(row["threshold"])
    stored = validation.compare_observables(original, bundle)
    assert stored["status"] == "REPLAY_MISMATCH"
    assert set(stored["differences"]) == {"cells/0/threshold", "cells/1/threshold"}
    before = canonical_bytes(stored)
    result = _validate_generated_comparison(monkeypatch, original, bundle, stored)
    assert result["status"] == "verified"
    assert result["stored_comparison_status"] == "REPLAY_MISMATCH"
    assert result["comparison_correction"] == "canonical_numeric_type_normalization_v1"
    assert result["replay"] == validation.compare_observables(original, original)
    assert result["replay"]["status"] == "EXACT_OBSERVABLE_REPLAY"
    assert result["replay"]["differences"] == []
    assert canonical_bytes(stored) == before


def test_validator_rejects_additional_stored_or_recalculated_differences(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _real_bundle()
    # Two close scores in one comparison cell isolate ranking/ties within numeric tolerance.
    second = {**original["predictions"][0], "municipality_code": "01002", "score": 0.5 + 5e-13}
    original["predictions"].insert(1, second)
    stored = {
        **validation.compare_observables(original, original),
        "status": "REPLAY_MISMATCH",
        "differences": ["cells/0/threshold"],
    }
    for extra in (
        "predictions/0/alert",
        "predictions/0/score",
        "cell/ranking_bins_ties",
        "thresholds",
        "cells/0/metrics/false_alerts",
        "cells/not-an-integer/threshold",
        "cells/0/threshold/extra",
    ):
        changed = {**stored, "differences": [*stored["differences"], extra]}
        with pytest.raises(ValueError, match="Replay comparison evidence changed"):
            _validate_generated_comparison(monkeypatch, original, original, changed)
    for case in ("alert", "score", "ranking", "threshold", "discrete", "numeric", "tie", "bin"):
        bundle = copy.deepcopy(original)
        if case == "alert":
            bundle["predictions"][0]["alert"] = False
        elif case in {"score", "numeric", "bin"}:
            bundle["predictions"][0]["score"] += {
                "score": 2e-12,
                "numeric": 1e-13,
                "bin": -5e-13,
            }[case]
        elif case == "ranking":
            bundle["predictions"][0]["score"], bundle["predictions"][1]["score"] = (
                bundle["predictions"][1]["score"],
                bundle["predictions"][0]["score"],
            )
        elif case == "tie":
            bundle["predictions"][1]["score"] = bundle["predictions"][0]["score"]
        elif case == "threshold":
            bundle["cells"][0]["threshold"] += 5e-13
        else:
            bundle["cells"][0]["metrics"]["false_alerts"] += 1
        report = validation.compare_observables(original, bundle)
        assert report["status"] != "EXACT_OBSERVABLE_REPLAY", case
        if case in {"ranking", "tie", "bin"}:
            assert any(path.endswith("/ranking_bins_ties") for path in report["differences"])
        try:
            result = _validate_generated_comparison(monkeypatch, original, bundle, stored)
        except ValueError as error:
            assert str(error) == "Replay comparison evidence changed"
        else:
            assert result["status"] == "REPLAY_MISMATCH", case
            assert "comparison_correction" not in result


def test_preflight_observes_environment_without_private_reads_or_writes(
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig

    parent = preflight.source_descriptor()["parent_descriptor"]
    files = {name: {"sha256": "a" * 64, "bytes": 1} for name in parent["declared_paths"]}
    files.update(parent["expected_pinned_files"])
    files[PreparationConfig(Path.cwd()).contract_path.as_posix()] = {"sha256": "b" * 64, "bytes": 1}
    inventory = repo_tmp_path / "source-identities.json"
    inventory.write_bytes(canonical_bytes(files))
    monkeypatch.setenv("SAT_DENGUE_EXP03_1_REPLAY_SOURCES", str(inventory))
    monkeypatch.setenv("SAT_DENGUE_EXP03_1_ORIGINAL_BUNDLE", preflight.OUTPUT_ROOT + "/original")
    monkeypatch.setenv(
        "SAT_DENGUE_TRACKING_ROOT", (repo_tmp_path / "tracking").relative_to(Path.cwd()).as_posix()
    )
    before = set(repo_tmp_path.iterdir())
    original_open = Path.open

    def guarded_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert not path.absolute().is_relative_to(Path.cwd() / "data"), "Private source read"
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded_open)
    receipt = preflight.preflight(
        {"profile": "exp03_1_preflight", "tracking": "enabled", "experiment_id": "EXP031"},
        preflight.source_descriptor(),
    )
    assert receipt["original"] == preflight.ORIGINAL
    assert receipt["authorized_source_files"] == files and len(files) == 8
    assert receipt["environment_sha256"] == digest(receipt["observed_environment"])
    assert {"numpy", "pandas", "scikit-learn", "lightgbm", "xgboost"} <= receipt[
        "observed_environment"
    ]["versions"].keys()
    assert receipt["real_private_reads"] == receipt["mlflow_writes"] == 0
    assert set(repo_tmp_path.iterdir()) == before
    del files[next(iter(files))]
    inventory.write_bytes(canonical_bytes(files))
    with pytest.raises(ValueError, match="eight source identities"):
        preflight.replay_binding()


def test_versioned_companion_and_legacy_bundle_remain_readable(
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A fixed safe adapter double exercises all 96 artifact identities without fitting.
    class Model:
        preparer = {"generated": True}

        def predict(self, frame: Any) -> Any:
            return pd.Series(0.25, index=frame.index)

        def model_bytes(self) -> bytes:
            return b'{"generated":true}'

    monkeypatch.setattr(
        "sat_dengue.model_training.candidate_families.restore_model", lambda *_: Model()
    )
    monkeypatch.setattr(validation, "validate_real_mlflow", lambda *_: None)
    original = _real_bundle()
    provenance = copy.deepcopy(original["provenance"])
    provenance.update(
        replay_protocol=preflight.REPLAY_PROTOCOL,
        original=dict(preflight.ORIGINAL),
        original_bundle_path=preflight.OUTPUT_ROOT + "/original",
        authorized_source_files=provenance["source_admission"]["files"],
        observed_environment={"synthetic": True},
        environment_sha256=digest({"synthetic": True}),
    )
    approval = provenance["approval_record"]
    approval.update(
        schema=preflight.APPROVAL_SCHEMA,
        replay_only_authorized=True,
        **{name: provenance[name] for name in preflight.REPLAY_BOUND},
    )
    provenance["approval_sha256"] = digest(approval)
    value = copy.deepcopy(original)
    # Fixed scores allow the safe adapter double to reproduce this synthetic bundle.
    for row, prediction in zip(value["cells"], value["predictions"], strict=True):
        prediction["score"] = 0.5
        row["brier"] = row["metrics"]["brier"] = 0.25
        row["metrics"]["ece"] = 0.5
        row["metrics"]["reliability"] = [{"bin": 5, "rows": 1, "observed": 1.0, "predicted": 0.5}]
    for row in value["contrasts"]["paired_effects"]:
        row["score_delta"] = 0.0
    monkeypatch.setattr(validation, "read_original", lambda *_: {"bundle": value})
    capture = repo_tmp_path / "capture"
    capture.mkdir()
    for row, prediction in zip(value["cells"], value["predictions"], strict=True):
        spec = {name: row[name] for name in ("objective", "variant", "family", "horizon", "cut")}
        predictor = NativePredictor(
            spec["family"], Model(), row["predictors"], row["predictors"], {}
        )
        frame = pd.DataFrame(
            [
                {
                    **{name: 0.12345678901234566 for name in row["predictors"]},
                    "municipality_code": prediction["municipality_code"],
                    "year_month": prediction["origin_month"],
                    "target_month": prediction["target_month"],
                    "target_year": int(prediction["target_month"][:4]),
                    "onset_target": 1,
                    "excess_target": 1,
                    "eligible_at_t": True,
                    "error_type": "onset",
                }
            ]
        )
        reporting.capture_replay_cell(
            _payload(spec, predictor, SigmoidCalibrator(0, 0), frame, row, 0.5), capture, provenance
        )
    destination = Path(preflight.OUTPUT_ROOT) / ("replay-test-" + uuid.uuid4().hex)
    historical = destination.with_name(destination.name + "-legacy")
    try:
        legacy = reporting.write_real_bundle(
            original, original["provenance"], original["mlflow_receipt"], historical
        )
        assert (
            validation.validate(historical, legacy["manifest"]["bundle_id"], "unused")["replay"][
                "status"
            ]
            == "NOT_COMPARABLE"
        )
        result = {**value, "replay_capture_root": str(capture)}
        publication = reporting.write_real_bundle(
            result, provenance, value["mlflow_receipt"], destination
        )
        assert publication["manifest"]["schema"] == "exp03-1-real-manifest-v2"
        loaded = reporting.read_real_bundle(destination, publication["manifest"]["bundle_id"])
        assert loaded["replay"]["persistence_counters"]["reload_passes"] == 96
        assert (
            validation.validate(destination, publication["manifest"]["bundle_id"], "unused")[
                "replay"
            ]["status"]
            == "EXACT_OBSERVABLE_REPLAY"
        )
        assert {p.name for p in historical.iterdir()} == {"bundle.json", "manifest.json"}
        path = destination / "replay" / value["cells"][0]["cell_id"] / "state.json"
        path.write_bytes(b"{}")
        with pytest.raises(ValueError, match="integrity/linkage"):
            reporting.read_real_bundle(destination, publication["manifest"]["bundle_id"])
    finally:
        for path in (destination, historical):
            if path.exists():
                shutil.rmtree(path)
