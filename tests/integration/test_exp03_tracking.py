"""Generated EXP03 v2 publication in an isolated, disposable tracking store."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from kedro.io import DatasetError

from sat_dengue.datasets.exp03 import Exp03BundleDataset
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import VARIANTS, load_protocol
from sat_dengue.experiments.exp03_preflight import OUTPUT_ROOT
from sat_dengue.tracking.exp03 import Exp03Tracking, validate_result, verified_result

ROOT = Path(__file__).resolve().parents[2]


def generated_provenance() -> dict[str, Any]:
    """Explicit artificial identity, never a scientific approval or receipt."""
    return {
        **{
            key: "b" * 64
            for key in (
                "data_version",
                "data_sha256",
                "configuration_sha256",
                "code_sha256",
                "environment_sha256",
                "scope_sha256",
                "matrix_sha256",
            )
        },
        "protocol_sha256": digest(load_protocol()),
        "git_revision": "a" * 40,
        "synthetic": True,
    }


def test_result_rejects_counters_pairing_and_duplicate_objective(
    exp03_generated_result: dict[str, Any],
) -> None:
    provenance = generated_provenance()
    result = copy.deepcopy(exp03_generated_result)
    validate_result(result, provenance)
    altered = copy.deepcopy(result)
    altered["children"][0]["cohort_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="cohort"):
        validate_result(altered, provenance)
    altered = copy.deepcopy(result)
    altered["real_model_fits"] = 1
    with pytest.raises(ValueError, match="fit count"):
        validate_result(altered, provenance)
    altered = copy.deepcopy(result)
    del altered["calibrator_fits"]
    with pytest.raises(ValueError, match="fit count"):
        validate_result(altered, provenance)
    altered = copy.deepcopy(result)
    control = next(c for c in altered["children"] if c["objective"] == "excess")
    control["horizon"] = 1
    with pytest.raises(ValueError, match="grid"):
        validate_result(altered, provenance)


def test_atomic_publication_tracking_privacy_tamper_and_duplicate(
    exp03_generated_result: dict[str, Any],
    repo_tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = copy.deepcopy(exp03_generated_result)
    provenance = generated_provenance()
    # Work only in an isolated repository-local workspace, with public contracts.
    shutil.copytree(ROOT / "docs/product/experiments", repo_tmp_path / "docs/product/experiments")
    monkeypatch.chdir(repo_tmp_path)
    root = "tmp/generated-exp03-v2-tracking"
    tracker = Exp03Tracking("exp03_synthetic", "generated-v2", root, experiment_id="EXP03")
    dataset = Exp03BundleDataset(str(repo_tmp_path / OUTPUT_ROOT))
    dataset.save({"result": result, "provenance": provenance, "tracker": tracker})
    publication = dataset.load()
    native = verified_result(publication)
    assert native["result"]["schema"] == "exp03-result-v2"
    assert len(native["result"]["children"]) == 408
    assert "model_artifacts" not in native["result"]
    assert len(native["result"]["native_model_artifacts"]) > 102
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 409
    children = [run for run in runs if "mlflow.parentRunId" in run.data.tags]
    assert len(children) == 408
    assert {run.data.tags["variant"] for run in children} == set(VARIANTS)
    assert sum(run.data.tags["objective"] == "excess" for run in children) == 24
    assert not any(
        run.data.tags["objective"] == "excess" and run.data.tags["horizon"] == "1"
        for run in children
    )
    assert all(run.data.tags["purpose"] == "synthetic_interface_probe" for run in children)
    assert all(not run.data.metrics for run in children)
    assert all(not tracker.client.list_artifacts(run.info.run_id) for run in children)
    artifacts = tracker.client.list_artifacts(tracker.parent)
    assert [a.path for a in artifacts] == [tracker.parent + ".json"]
    download = repo_tmp_path / "tmp/download"
    download.mkdir()
    downloaded = tracker.client.download_artifacts(
        tracker.parent, tracker.parent + ".json", str(download)
    )
    text = Path(downloaded).read_text()
    aggregate = json.loads(text)
    assert aggregate["schema"] == "exp03-frontier-mlflow-v2"
    assert len(aggregate["cells"]) == 408 and len(aggregate["contrasts"]) == 204
    assert "municipality_code" not in text and "oof_predictions" not in text
    assert "selection_predictions" not in text and "model_artifacts" not in text
    assert aggregate["counters"]["real_model_fits"] == 0
    assert aggregate["counters"]["synthetic_interface_fits"] == 408
    by_cell = {run.data.tags["cell_id"]: run for run in children}
    assert len(by_cell) == 408
    for contrast in aggregate["contrasts"]:
        for side in ("left", "right"):
            assert all(
                by_cell[cell].data.tags["variant"] == contrast[side + "_variant"]
                and by_cell[cell].data.tags["objective"] == contrast[side + "_objective"]
                for cell in contrast[side + "_cells"]
            )
    from sat_dengue.tracking.exp03 import validate_frontier_artifact

    malicious = copy.deepcopy(aggregate)
    malicious["cells"][0]["metrics"]["municipality_code"] = "forbidden"
    malicious["frontier_sha256"] = digest(malicious["cells"])
    with pytest.raises(ValueError, match="metric"):
        validate_frontier_artifact(malicious)
    incomplete = copy.deepcopy(aggregate)
    incomplete["contrasts"].pop()
    incomplete["contrasts_sha256"] = digest(incomplete["contrasts"])
    with pytest.raises(ValueError, match="Incomplete"):
        validate_frontier_artifact(incomplete)
    assert not list(Path(root).glob(".exp03-frontier-*"))
    with pytest.raises(DatasetError, match="already exists"):
        dataset.save({"result": result, "provenance": provenance, "tracker": tracker})
    second = Exp03Tracking("exp03_synthetic", "generated-v2-duplicate", root, experiment_id="EXP03")
    with pytest.raises(ValueError, match="already tracked"):
        second.finish_ablation(publication)
    assert len(list(Path(OUTPUT_ROOT).glob("*/manifest.json"))) == 1
    payload = Path(publication["path"]) / "selection_predictions.csv"
    payload.write_text("tampered\n")
    with pytest.raises(DatasetError):
        dataset.load()
