"""Generated publication metadata only; isolated temporary MLflow, never private science."""

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
        "schema": "exp03-result-v1",
        "experiment_id": "EXP03",
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
    from sat_dengue.tracking.exp03_contrasts import METRICS

    # Closed aggregate metadata only, not probabilities, fits or scientific evidence.
    result["contrasts"] = []
    for c in p["design"]["contrasts"]:
        for family in p["design"]["families"]:
            for h in (1, 2):
                for w in [v["id"] for v in p["design"]["windows"]] + ["development_oof"]:
                    cuts = (
                        [
                            v["id"]
                            for v in p["design"]["windows"]
                            if v["evidence_type"] == "retrospective_development"
                        ]
                        if w == "development_oof"
                        else [w]
                    )
                    for budget in range(3):
                        result["contrasts"].append(
                            {
                                "contrast_id": c["id"],
                                "family": family,
                                "horizon": h,
                                "window": w,
                                "left_variant": c["left"],
                                "right_variant": c["right"],
                                "semantic_roles": c["semantic_roles"],
                                "source_cuts": cuts,
                                "left_cells": [digest([c["left"], family, h, v]) for v in cuts],
                                "right_cells": [digest([c["right"], family, h, v]) for v in cuts],
                                "left_metrics": dict.fromkeys(METRICS, 0),
                                "right_metrics": dict.fromkeys(METRICS, 0),
                                "selection_false_alert_budget": budget,
                                "paired_sensitivity_difference": None,
                                "paired_interval": {
                                    "status": "insufficient_cluster_support",
                                    "interval": None,
                                    "valid_replicates": 0,
                                },
                            }
                        )
    target = repo_tmp_path / "docs/product/experiments"
    shutil.copytree(ROOT / "docs/product/experiments", target)
    monkeypatch.chdir(repo_tmp_path)
    root = "tmp/generated-exp03-tracking"
    tracker = Exp03Tracking("exp03_synthetic", "generated-metadata", root, experiment_id="EXP03")
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
    dataset = Exp03BundleDataset(str(repo_tmp_path / OUTPUT_ROOT))
    dataset.save({"result": result, "provenance": provenance, "tracker": tracker})
    publication = dataset.load()
    assert verified_result(publication)["result"] == result
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 241
    children = [r for r in runs if "mlflow.parentRunId" in r.data.tags]
    assert len(children) == 240
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
    by_cell = {r.data.tags["cell_id"]: r for r in children}
    assert len(by_cell) == len(children) == 240
    assert not any(r.data.tags["variant"] == "full_without_climate" for r in children)
    for contrast in aggregate["contrasts"]:
        if contrast["contrast_id"] == "full_without_climate":
            assert contrast["right_variant"] == "baseline_plus_complete_channel"
            assert all(
                by_cell[cell].data.tags["variant"] == "baseline_plus_complete_channel"
                for cell in contrast["right_cells"]
            )
    assert aggregate["parameters"]["bundle_id"] == publication["manifest"]["bundle_id"]
    assert aggregate["frontier_sha256"] == parent.data.tags["exp03.frontier_sha256"]
    assert aggregate["frontier_sha256"] == digest(aggregate["cells"])
    assert all(
        [r["selection_false_alert_budget"] for r in c["frontier"]] == [0, 1, 2]
        for c in aggregate["cells"]
    )
    assert "municipality_code" not in Path(downloaded).read_text()
    assert not list(Path(root).glob(".exp03-frontier-*"))
    from sat_dengue.tracking.exp03 import validate_frontier_artifact

    malicious = copy.deepcopy(aggregate)
    malicious["cells"][0]["frontier"][0]["municipality_code"] = "not-allowed"
    malicious["frontier_sha256"] = digest(malicious["cells"])
    with pytest.raises(ValueError):
        validate_frontier_artifact(malicious)

    for remove in ("contrast", "budget"):
        incomplete = copy.deepcopy(aggregate)
        incomplete["contrasts"] = [
            r
            for r in incomplete["contrasts"]
            if not (
                r["contrast_id"] == p["design"]["contrasts"][0]["id"]
                and (remove == "contrast" or r["selection_false_alert_budget"] == 1)
            )
        ]
        incomplete["contrasts_sha256"] = digest(incomplete["contrasts"])
        with pytest.raises(ValueError, match="Incomplete eleven"):
            validate_frontier_artifact(incomplete)

    with pytest.raises(DatasetError):
        dataset.save({"result": result, "provenance": provenance, "tracker": tracker})
    assert len(list(Path(OUTPUT_ROOT).glob("*/manifest.json"))) == 1
    (Path(publication["path"]) / "result.json").chmod(0o600)
    (Path(publication["path"]) / "result.json").write_text("{}")
    with pytest.raises(DatasetError, match="payload"):
        dataset.load()
