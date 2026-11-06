"""Generated local-only MLflow integration; native detailed rows never enter tracking."""

import copy
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.datasets.exp_delta03_execution import ExecutionStore
from sat_dengue.experiments.exp_delta03_contract import canonical, digest
from sat_dengue.model_training.exp_delta03_adapter import fit_native
from sat_dengue.tracking.exp_delta03 import mirror, validate_lineage


def fixture(root):
    identity = {
        "input_source": "generated_only",
        "protocol_sha256": "a" * 64,
        "matrix_manifest_sha256": "b" * 64,
        "commit": "c" * 40,
    }
    params = {
        "objective": "binary:logistic",
        "tree_method": "hist",
        "n_jobs": 1,
        "random_state": 1729,
        "n_estimators": 2,
        "max_depth": 1,
        "learning_rate": 0.1,
        "device": "cpu",
    }
    x = pd.DataFrame({"signal": np.tile([0.0, 1.0, 2.0, 3.0], 8)})
    y = pd.Series(np.tile([0, 0, 1, 1], 8))
    cells = []
    for name in ["FULL_COMMON", "FULL_MINUS_NDVI"]:
        m = fit_native(x, y, params, cohort_sha256="d" * 64)
        cells.append(
            {
                "id": name,
                "variant": name,
                "horizon": 1,
                "year": 2020,
                "training_scope": "national",
                "evaluation_scope": "Meta_Tolima",
                "status": "GENERATED_ADAPTER_FIXTURE",
                "metrics": {
                    "roles": {
                        "train": {"rows": len(x), "brier": float(np.mean((m.predict(x) - y) ** 2))}
                    },
                    "scopes": {},
                },
                "model_sha256": m.metadata["model_sha256"],
                "calibrator_sha256": "e" * 64,
                "policy_sha256": "f" * 64,
                "cohort_sha256": "d" * 64,
                "parameters_sha256": digest(params),
                "predictors_sha256": digest(list(x)),
                "parameters": params,
            }
        )
    result = {
        "schema": "exp-delta03-results-v1",
        "identity": identity,
        "identity_sha256": digest(identity),
        "regime": "RETROSPECTIVE_CONSOLIDATED",
        "operational_PIT": False,
        "cells": cells,
        "comparisons": [
            {"left": "FULL_MINUS_NDVI", "right": "FULL_COMMON", "cohort_sha256": "d" * 64}
        ],
        "activity_counters": {
            "real_model_fits": 0,
            "real_calibrations": 0,
            "synthetic_model_fits": len(cells),
        },
        "counts": {"models": len(cells)},
        "unsupported": [],
    }
    with ExecutionStore(
        root, "tmp/exp-delta03-phase2/synthetic/native", identity, synthetic=True
    ) as store:
        publication = store.publish(
            {
                "result.json": canonical(result),
                "protected_predictions.csv": b"divipola_municipio\n50001\n",
            }
        )
    return result, publication


def test_isolated_parent_children_tags_lineage_idempotence_and_no_private_rows(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", "tmp/permanent-must-not-be-used")
    result, publication = fixture(tmp_path)
    relative = "tmp/exp-delta03-phase2/synthetic/mlflow"
    receipt = mirror(tmp_path, publication, relative, synthetic=True)
    assert receipt["runs"] == len(result["cells"]) + 1 and receipt["permanent_writes"] == 0
    repeated = mirror(tmp_path, publication, relative, synthetic=True)
    assert receipt == repeated
    assert receipt["pairs"][0]["right_run_id"] == receipt["children"]["FULL_COMMON"]
    from sat_dengue.tracking.exp_delta03 import client_for

    client, experiment = client_for(tmp_path, relative)
    runs = client.search_runs([experiment], max_results=100)
    assert len(runs) == receipt["runs"] and all(r.info.status == "FINISHED" for r in runs)
    for run in runs:
        assert run.data.tags["experiment_id"] == "EXP-DELTA03"
        assert run.data.tags["operational_PIT"] == "false"
        assert run.data.tags["preparation_regime"] == "RETROSPECTIVE_CONSOLIDATED"
        assert "protocol_sha256" in run.data.tags and "matrix_bundle_sha256" in run.data.tags
    db = (tmp_path / relative / "tracking.sqlite").read_bytes()
    assert b"divipola_municipio" not in db and str(tmp_path).encode() not in db
    assert not (tmp_path / "tmp/permanent-must-not-be-used").exists()
    with pytest.raises(ValueError):
        mirror(tmp_path, publication, "tmp/permanent-must-not-be-used", synthetic=True)
    child = receipt["children"]["FULL_COMMON"]
    aggregate = client.get_run(child).data.tags["aggregate_sha256"]
    client.delete_tag(child, "aggregate_sha256")
    with pytest.raises(ValueError, match="completion evidence"):
        mirror(tmp_path, publication, relative, synthetic=True)
    client.set_tag(child, "aggregate_sha256", aggregate)
    client.set_terminated(child, "FAILED")
    with pytest.raises(ValueError, match="child status"):
        mirror(tmp_path, publication, relative, synthetic=True)
    client.set_terminated(child, "FINISHED")
    client.log_metric(child, "train.brier", 0.987654321)
    with pytest.raises(ValueError, match="metrics/parameters"):
        mirror(tmp_path, publication, relative, synthetic=True)
    original = next(r for r in runs if r.info.run_id == child).data.metrics["train.brier"]
    client.log_metric(child, "train.brier", original)
    client.set_tag(child, "mlflow.parentRunId", "f" * 32)
    with pytest.raises(ValueError, match="lineage/parent"):
        mirror(tmp_path, publication, relative, synthetic=True)


def test_unknown_row_payload_is_rejected_before_mlflow_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result, publication = fixture(tmp_path)
    result["cells"][0]["private_rows"] = [{"municipality": "secret"}]
    with ExecutionStore(
        tmp_path, "tmp/exp-delta03-phase2/synthetic/bad", result["identity"], synthetic=True
    ) as store:
        altered = store.publish({"result.json": canonical(result)})
    relative = "tmp/exp-delta03-phase2/synthetic/forbidden"
    with pytest.raises(ValueError, match="cell fields"):
        mirror(tmp_path, altered, relative, synthetic=True)
    assert not (tmp_path / relative).exists()


def test_lineage_is_a_closed_hash_and_run_id_surface():
    value: dict[str, Any] = {
        "schema": "exp-delta03-mlflow-lineage-v1",
        "identity_sha256": "a" * 64,
        "native_manifest_sha256": "b" * 64,
        "parent_run_id": "c" * 32,
        "children": {"cell": "d" * 32},
        "real_model_fits": 0,
        "synthetic_model_fits": 1,
        "parameters": {"protocol_sha256": "e" * 64},
    }
    validate_lineage(value)
    bad = copy.deepcopy(value)
    bad["predictions"] = [1]
    with pytest.raises(ValueError):
        validate_lineage(bad)
    bad = copy.deepcopy(value)
    bad["parameters"]["native_pointer"] = "/private/secret"
    with pytest.raises(ValueError):
        validate_lineage(bad)


def test_interrupted_tracking_resumes_without_duplicate_runs(tmp_path, monkeypatch):
    import sat_dengue.tracking.exp_delta03 as adapter

    monkeypatch.chdir(tmp_path)
    result, publication = fixture(tmp_path)
    relative = "tmp/exp-delta03-phase2/synthetic/interrupted"
    (tmp_path / relative).mkdir(parents=True)
    client, experiment = adapter.client_for(tmp_path, relative)
    original = client.log_metric

    def fail(*args, **kwargs):
        raise RuntimeError("generated interruption")

    monkeypatch.setattr(client, "log_metric", fail)
    monkeypatch.setattr(adapter, "client_for", lambda root, relative: (client, experiment))
    with pytest.raises(RuntimeError, match="generated interruption"):
        adapter.mirror(tmp_path, publication, relative, synthetic=True)
    parents = [
        r for r in client.search_runs([experiment]) if r.data.tags.get("run_kind") == "parent"
    ]
    assert len(parents) == 1 and parents[0].info.status == "FAILED"
    monkeypatch.setattr(client, "log_metric", original)
    receipt = adapter.mirror(tmp_path, publication, relative, synthetic=True)
    assert len(client.search_runs([experiment])) == len(result["cells"]) + 1
    assert receipt["parent_run_id"] == parents[0].info.run_id
