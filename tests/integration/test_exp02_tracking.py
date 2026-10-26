"""Generated publication metadata only; isolated temporary MLflow, never private science."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
from typing import Any

import pytest
from kedro.io import DatasetError

from sat_dengue.datasets.exp02 import Exp02BundleDataset
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp02 import VARIANTS, load_protocol
from sat_dengue.experiments.exp02_preflight import OUTPUT_ROOT
from sat_dengue.tracking.exp02 import Exp02Tracking, validate_result, verified_result

ROOT = Path(__file__).resolve().parents[2]


def generated_metadata() -> dict[str, Any]:
    # Structural fixture, NOT predictions or scientific evidence. All fits zero.
    p = load_protocol()
    children = []
    for v in VARIANTS:
        for f in p["design"]["families"]:
            for h in (1, 2):
                for w in p["design"]["windows"]:
                    children.append(
                        {
                            "variant": v,
                            "objective": "onset",
                            "family": f,
                            "horizon": h,
                            "window": w["id"],
                            "status": "non_evaluable",
                            "reason": "generated_metadata_only",
                            "seed": 42,
                            "cohort": "non_excess_at_t",
                            "cohort_sha256": "a" * 64,
                            "role_sha256": {"train": "b" * 64},
                            "predictors_sha256": digest(p["design"]["variants"][v]),
                            "number_of_variables": len(p["design"]["variants"][v]),
                            "coverage": {},
                            "frontier": [],
                            "evidence_type": "synthetic_interface_probe",
                        }
                    )
    return {
        "schema": "exp02-result-v1",
        "experiment_id": "EXP02",
        "synthetic": True,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "calibrator_fits": 0,
        "synthetic_interface_fits": 0,
        "children": children,
    }


def test_result_rejects_counters_and_pairing() -> None:
    p = {"protocol_sha256": digest(load_protocol())}
    r = generated_metadata()
    validate_result(r, p)
    altered = copy.deepcopy(r)
    altered["children"][0]["cohort_sha256"] = "c" * 64
    with pytest.raises(ValueError, match="cohort"):
        validate_result(altered, p)
    altered = copy.deepcopy(r)
    altered["real_model_fits"] = 1
    with pytest.raises(ValueError, match="fit count"):
        validate_result(altered, p)
    altered = copy.deepcopy(r)
    altered["children"].pop()
    with pytest.raises(ValueError, match="grid"):
        validate_result(altered, p)


def test_atomic_publication_tracking_and_duplicate(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = generated_metadata()
    # Artificial aggregate upload fixture, never a scientific experiment/result.
    for c in result["children"]:
        c["status"] = "evaluable"
        c["municipality_code"] = "forbidden-source-dimension"
        c["frontier"] = [
            {
                "selection_false_alert_budget": b,
                "onset_sensitivity": 0.5,
                "paired_onset_sensitivity_difference": 0.0,
                "false_alerts": b,
                "full_realized_false_alerts": b,
                "paired_interval": {"status": "insufficient_cluster_support", "interval": None},
            }
            for b in range(3)
        ]
    p = load_protocol()
    target = repo_tmp_path / "docs/product/experiments"
    shutil.copytree(ROOT / "docs/product/experiments", target)
    monkeypatch.chdir(repo_tmp_path)
    root = "tmp/generated-exp02-tracking"
    tracker = Exp02Tracking("exp02_synthetic", "generated-metadata", root, experiment_id="EXP02")
    provenance = {
        k: "b" * 64
        for k in (
            "data_version",
            "data_sha256",
            "configuration_sha256",
            "code_sha256",
            "environment_sha256",
        )
    }
    provenance.update(protocol_sha256=digest(p), git_revision="a" * 40)
    dataset = Exp02BundleDataset(str(repo_tmp_path / OUTPUT_ROOT))
    dataset.save({"result": result, "provenance": provenance, "tracker": tracker})
    publication = dataset.load()
    assert verified_result(publication)["result"] == result
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 109
    children = [r for r in runs if "mlflow.parentRunId" in r.data.tags]
    assert len(children) == 108
    assert {r.data.tags["variant"] for r in children} == set(VARIANTS)
    assert all(r.data.tags["purpose"] == "synthetic_interface_probe" for r in children)
    assert all("/" not in value for r in runs for value in r.data.params.values())
    parent = tracker.client.get_run(tracker.parent)
    artifacts = tracker.client.list_artifacts(tracker.parent)
    assert [a.path for a in artifacts] == [tracker.parent + ".json"]
    assert all(not tracker.client.list_artifacts(r.info.run_id) for r in children)
    destination = repo_tmp_path / "tmp" / "download"
    destination.mkdir()
    downloaded = tracker.client.download_artifacts(
        tracker.parent, tracker.parent + ".json", str(destination)
    )
    aggregate = json.loads(Path(downloaded).read_text())
    assert aggregate["parameters"]["bundle_id"] == publication["manifest"]["bundle_id"]
    assert aggregate["frontier_sha256"] == parent.data.tags["exp02.frontier_sha256"]
    assert aggregate["frontier_sha256"] == digest(aggregate["cells"])
    assert all(
        [r["selection_false_alert_budget"] for r in c["frontier"]] == [0, 1, 2]
        for c in aggregate["cells"]
    )
    assert "municipality_code" not in Path(downloaded).read_text()
    assert not list(Path(root).glob(".exp02-frontier-*"))
    from sat_dengue.tracking.exp02 import validate_frontier_artifact

    malicious = copy.deepcopy(aggregate)
    malicious["cells"][0]["frontier"][0]["municipality_code"] = "not-allowed"
    malicious["frontier_sha256"] = digest(malicious["cells"])
    with pytest.raises(ValueError):
        validate_frontier_artifact(malicious)

    with pytest.raises(DatasetError):
        dataset.save({"result": result, "provenance": provenance, "tracker": tracker})
    assert len(list(Path(OUTPUT_ROOT).glob("*/manifest.json"))) == 1
    (Path(publication["path"]) / "result.json").chmod(0o600)
    (Path(publication["path"]) / "result.json").write_text("{}")
    with pytest.raises(DatasetError, match="payload"):
        dataset.load()
