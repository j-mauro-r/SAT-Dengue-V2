"""Generated EXP01 publication checks with native fits and private reads unreachable."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.legacy_preparation.persistence import publish_bundle
from sat_dengue.experiments.exp01 import (
    digest,
    execute_paired,
    load_protocol,
    synthetic_fit,
    synthetic_inputs,
)
from sat_dengue.tracking.exp01 import Exp01Tracking, verified_result
from sat_dengue.training_preparation.serialization import bytes_record

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def generated_result() -> dict[str, Any]:
    panel, contract, design = synthetic_inputs()
    protocol = load_protocol()
    design = copy.deepcopy(design)
    for generated, frozen in zip(design["windows"], protocol["design"]["windows"], strict=True):
        generated["id"] = frozen["id"]
    calls = []

    def probe(family: Any, X: Any, y: Any, parameters: Any, seed: Any) -> Any:
        calls.append((family, X.copy(deep=True)))
        return synthetic_fit(family, X, y, parameters, seed)

    result = execute_paired(
        panel,
        contract,
        design,
        fit=probe,
        calibrate=lambda scores, truth, seed: lambda values: values,
        synthetic=True,
    )
    assert len(calls) == 36
    for left, right in zip(calls[::2], calls[1::2], strict=True):
        assert left[0] == right[0]
        assert left[1].equals(right[1])
    assert (
        result["real_model_fits"]
        == result["real_preparer_refits"]
        == result["calibrator_fits"]
        == 0
    )
    assert all(c["evidence_type"] == "synthetic_interface_probe" for c in result["children"])
    for child in result["children"]:
        reference = child["operational_reference"]
        assert reference["reference"] == "persistence"
        assert reference["emitted_alerts"] == 0
        assert reference["false_alarm_ratio"] is None
        assert reference["brier"] is None
    return result


def publication(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    provenance: dict[str, Any] = {
        "protocol_sha256": digest(load_protocol()),
        "git_revision": "a" * 40,
        "data_version": "b" * 64,
        "data_sha256": "c" * 64,
        "configuration_sha256": "d" * 64,
    }
    provenance["code"] = {"fixture.py": "e" * 64}
    provenance["runtime"] = {"fixture": "generated_only"}
    provenance["code_sha256"] = digest(provenance["code"])
    provenance["environment_sha256"] = digest(provenance["runtime"])
    payloads = {
        "result.json": canonical_bytes(result),
        "provenance.json": canonical_bytes(provenance),
    }
    body = {
        "schema": "exp01-result-manifest-v1",
        "files": {name: bytes_record(value) for name, value in payloads.items()},
    }
    manifest = {**body, "bundle_id": digest(body)}
    payloads["manifest.json"] = canonical_bytes(manifest)
    folder = publish_bundle(root, str(manifest["bundle_id"]), payloads, existing_policy="error")
    return {"path": str(folder.relative_to(ROOT)), "manifest": manifest}


def test_paired_publication_tracks_exact_parent_children_and_common_tags_without_real_fits(
    generated_result: dict[str, Any], repo_tmp_path: Path
) -> None:
    store = str((repo_tmp_path / "mlflow").relative_to(ROOT))
    record = publication(repo_tmp_path / "results", generated_result)
    tracker = Exp01Tracking(
        "exp01_synthetic", "generated-paired-probe", store, experiment_id="EXP01"
    )
    parent_id = tracker.finish_paired(record)
    parent = tracker.client.get_run(parent_id)
    assert parent.info.status == "FINISHED"
    assert parent.data.tags["purpose"] == "synthetic_interface_probe"
    assert parent.data.params["kind"] == "synthetic"
    assert parent.data.params["git_revision"] == "a" * 40
    assert parent.data.params["data_sha256"] == "c" * 64
    assert all(value == 0 for value in parent.data.metrics.values())
    runs = tracker.client.search_runs([tracker.experiment])
    children = [run for run in runs if run.data.tags.get("mlflow.parentRunId") == parent_id]
    assert len(runs) == 37 and len(children) == 36
    common = {
        "experiment_id",
        "experiment_slug",
        "hypothesis_id",
        "objective_slug",
        "experiment_type",
        "target_definition",
        "protocol_sha256",
    }
    for child in children:
        assert child.info.status == "FINISHED"
        assert {key: child.data.tags[key] for key in common} == {
            key: parent.data.tags[key] for key in common
        }
        assert child.data.tags["status"] == "verified"
        assert child.data.params["horizon"] in {"1", "2"}
        assert child.data.params["objective"] in {"onset", "excess"}
        assert child.data.params["cohort"] == "non_excess_at_t"
        assert child.data.metrics == {}
    retry = Exp01Tracking("exp01_synthetic", "duplicate", store, experiment_id="EXP01")
    with pytest.raises(ValueError, match="already has completed tracking"):
        retry.finish_paired(record)
    assert retry.client.get_run(retry.parent).info.status == "FAILED"


@pytest.mark.parametrize("mutation", ["cohort", "role", "children", "counter", "protocol"])
def test_invalid_publications_fail_closed(
    generated_result: dict[str, Any], repo_tmp_path: Path, mutation: str
) -> None:
    result = copy.deepcopy(generated_result)
    if mutation == "cohort":
        result["children"][0]["cohort_sha256"] = "0" * 64
    elif mutation == "role":
        result["children"][0]["role_sha256"] = {}
    elif mutation == "children":
        result["children"].pop()
    elif mutation == "counter":
        result["real_model_fits"] = 1
    record = publication(repo_tmp_path / "invalid", result)
    if mutation == "protocol":
        folder = ROOT / record["path"]
        value = json.loads((folder / "provenance.json").read_text())
        value["protocol_sha256"] = "0" * 64
        (folder / "provenance.json").write_text(json.dumps(value))
    with pytest.raises(ValueError):
        verified_result(record)


def test_failed_generated_probe_parent_retains_identity_and_purpose(repo_tmp_path: Path) -> None:
    provenance = {
        "protocol_sha256": digest(load_protocol()),
        "data_sha256": "a" * 64,
        "data_version": "b" * 64,
        "git_revision": "c" * 40,
        "configuration_sha256": "d" * 64,
        "code_sha256": "e" * 64,
        "environment_sha256": "f" * 64,
    }
    tracker = Exp01Tracking(
        "exp01_synthetic",
        "generated-failure",
        str((repo_tmp_path / "mlflow").relative_to(ROOT)),
        experiment_id="EXP01",
    )
    tracker.initialize_paired(provenance, synthetic=True)
    tracker.fail()
    run = tracker.client.get_run(tracker.parent)
    assert run.info.status == "FAILED"
    assert run.data.tags["purpose"] == "synthetic_interface_probe"
    assert run.data.params["git_revision"] == "c" * 40
    assert run.data.params["data_sha256"] == "a" * 64
    assert run.data.params["code_sha256"] == "e" * 64
    assert run.data.params["environment_sha256"] == "f" * 64
    assert run.data.metrics == {}  # Failure never invents zero real-fit counters.


def test_invalid_result_is_rejected_before_native_publication(
    generated_result: dict[str, Any], repo_tmp_path: Path
) -> None:
    from sat_dengue.datasets.exp01 import Exp01BundleDataset
    from sat_dengue.experiments.exp01_preflight import OUTPUT_ROOT

    class FailureObserver:
        failed = False

        def fail(self) -> None:
            self.failed = True

    tracker = FailureObserver()
    data: dict[str, Any] = {
        "result": copy.deepcopy(generated_result),
        "provenance": {},
        "tracker": tracker,
    }
    data["result"]["real_model_fits"] = 1
    dataset = Exp01BundleDataset(OUTPUT_ROOT)
    dataset._root = repo_tmp_path / "never-published"
    from kedro.io import DatasetError

    with pytest.raises(DatasetError):
        dataset.save(data)
    assert tracker.failed and not dataset._root.exists()


def test_counter_projection_preserves_security_boundary_without_real_route_runs(
    generated_result: dict[str, Any],
) -> None:
    from sat_dengue.tracking.exp01 import tracking_counters

    assert tracking_counters(generated_result) == {
        "real_model_fits": 0.0,
        "real_preparer_refits": 0.0,
        "calibrator_fits": 0.0,
    }
    future = {
        **generated_result,
        "synthetic": False,
        "real_model_fits": 36,
        "real_preparer_refits": 36,
        "calibrator_fits": 36,
    }
    assert tracking_counters(future) == {}
    assert future["real_model_fits"] == future["calibrator_fits"] == 36
    invalid = {**generated_result, "calibrator_fits": 1}
    with pytest.raises(ValueError, match="Only zero synthetic"):
        tracking_counters(invalid)
