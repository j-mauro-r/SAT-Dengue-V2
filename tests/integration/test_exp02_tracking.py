"""Isolated EXP02 MLflow summaries and no-fit export from immutable generated bundles."""

import copy
import json
from pathlib import Path

import pytest

from sat_dengue.datasets.exp02 import publish_native
from sat_dengue.tracking.exp02 import Exp02Tracking, safe_receipt, validate_safe_receipt

ROOT = Path(__file__).resolve().parents[2]


def test_closed_projection_rejects_private_fields_and_nonfinite_values(
    exp02_generated_bundle, repo_tmp_path
):
    publication = publish_native(
        exp02_generated_bundle, str((repo_tmp_path / "native").relative_to(ROOT))
    )
    receipt = safe_receipt(publication)
    assert len(receipt["children"]) == 63 and len(receipt["comparisons"]) == 9
    serialized = json.dumps(receipt)
    assert all(f'"{key}"' not in serialized for key in ("municipality_code", "predictions"))
    assert '"50001"' not in serialized and '"by_group"' not in serialized
    assert str(ROOT) not in serialized
    for mutation in ("private", "secret", "nonfinite", "unknown_tag"):
        changed = copy.deepcopy(receipt)
        if mutation == "private":
            changed["children"][0]["municipality_code"] = "50001"
        elif mutation == "secret":
            changed["parameters"]["profile"] = "ghp_" + "A" * 36
        elif mutation == "nonfinite":
            changed["children"][0]["metrics"]["rows"] = float("nan")
        else:
            changed["children"][0]["window"] = "private/source.csv"
        with pytest.raises(ValueError):
            validate_safe_receipt(changed)


def test_export_generated_bundle_without_fits_into_isolated_parent_children(
    exp02_generated_bundle, repo_tmp_path, monkeypatch
):
    pytest.importorskip("mlflow")
    from sat_dengue.experiments import exp02_runner as runner

    def forbidden(*args, **kwargs):
        raise AssertionError("Export cannot fit, calibrate or read scientific sources")

    for name in ("native_fit", "native_calibration", "synthetic_fit", "prepare_exp01_inputs"):
        monkeypatch.setattr(runner, name, forbidden)
    publication = publish_native(
        exp02_generated_bundle, str((repo_tmp_path / "native").relative_to(ROOT))
    )
    root = str((repo_tmp_path / "tracking").relative_to(ROOT))
    tracker = Exp02Tracking("exp02_synthetic", "generated", root, experiment_id="EXP02")
    parent = tracker.finish_exp02(publication)
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 64
    assert tracker.client.get_run(parent).data.tags["status"] == "success"
    assert len([r for r in runs if r.data.tags.get("mlflow.parentRunId") == parent]) == 63
    assert all(r.info.status == "FINISHED" for r in runs)
    assert all(r.data.tags["experiment_id"] == "EXP02" for r in runs)
    assert {r.data.tags.get("history_years") for r in runs if r.info.run_id != parent} == {
        "5",
        "7",
        "9",
    }
    artifacts = tracker.client.list_artifacts(parent)
    assert len(artifacts) == 1
    value = json.loads((Path(root) / "receipts" / (parent + ".json")).read_text())
    validate_safe_receipt(value)
    duplicate = Exp02Tracking("exp02_synthetic", "duplicate", root, experiment_id="EXP02")
    with pytest.raises(ValueError, match="already registered"):
        duplicate.finish_exp02(publication)
    assert tracker.client.get_run(duplicate.parent).info.status == "FAILED"


def test_tracking_protocol_pin_is_exp02_specific(exp02_generated_bundle, repo_tmp_path):
    pytest.importorskip("mlflow")
    from sat_dengue.experiments.exp02_preflight import storage_preflight

    root = str((repo_tmp_path / "tracking").relative_to(ROOT))
    tracker = Exp02Tracking("exp02_synthetic", "generated-pin", root, experiment_id="EXP02")
    tracker.client.set_experiment_tag(tracker.experiment, "protocol.EXP01", "a" * 64)
    assert storage_preflight(root)["state"] == "existing_read_only_verified"
    tracker.client.set_experiment_tag(tracker.experiment, "protocol.EXP02", "b" * 64)
    with pytest.raises(ValueError, match="protocol pin differs"):
        storage_preflight(root)
    tracker.fail()
