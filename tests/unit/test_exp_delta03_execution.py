"""Generated filesystem/authorization fixtures; no scientific fitting or real publication."""

import copy
from datetime import UTC, datetime, timedelta

import pytest

from sat_dengue.datasets.exp_delta03_execution import ExecutionStore, authorize, verify_publication
from sat_dengue.experiments.exp_delta03_contract import canonical, digest


def test_reservation_resume_checkpoints_tampering_and_atomic_reuse(tmp_path):
    identity = {"generated_only": True, "contract": "a" * 64}
    relative = "tmp/exp-delta03-phase2/synthetic"
    with ExecutionStore(tmp_path, relative, identity, synthetic=True) as store:
        store.save_stage("cell", "trained", {"model.ubj": b"generated"})
        assert store.read_stage("cell", "trained") == {"model.ubj": b"generated"}
        with pytest.raises(BlockingIOError):
            with ExecutionStore(tmp_path, relative, identity, synthetic=True, resume=True):
                pass
        with pytest.raises(ValueError, match="overwrite"):
            store.save_stage("cell", "trained", {"model.ubj": b"changed"})
    with pytest.raises(ValueError, match="explicit resume"):
        with ExecutionStore(tmp_path, relative, identity, synthetic=True):
            pass
    with ExecutionStore(tmp_path, relative, identity, synthetic=True, resume=True) as store:
        # Simulate a death after phase visibility but before the state pointer update.
        del store.state["stages"]["cell.trained"]
        store._save_state()
        assert store.read_stage("cell", "trained") == {"model.ubj": b"generated"}
        publication = store.publish({"result.json": canonical({"generated_only": True})})
    assert verify_publication(tmp_path, publication, synthetic=True)["result.json"]
    with ExecutionStore(tmp_path, relative, identity, synthetic=True) as store:
        assert store.state["status"] == "COMPLETE"
        assert store.publish({"result.json": canonical({"generated_only": True})}) == publication
    (tmp_path / publication["path"] / "result.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        verify_publication(tmp_path, publication, synthetic=True)


def test_paths_symlinks_and_real_storage_require_grant_before_writes(tmp_path):
    with pytest.raises(PermissionError):
        ExecutionStore(tmp_path, "data/processed/exp_delta03", {}, synthetic=False)
    assert not (tmp_path / "data").exists()
    with pytest.raises(ValueError):
        ExecutionStore(tmp_path, "tmp/exp-delta03-phase2/../escape", {}, synthetic=True)
    link = tmp_path / "tmp"
    link.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        ExecutionStore(tmp_path, "tmp/exp-delta03-phase2/run", {}, synthetic=True)


def authorization_fixture(tmp_path):
    contract = {
        "regime": "RETROSPECTIVE_CONSOLIDATED",
        "operational_PIT": False,
        "decision_status": "APPROVED",
        "phase3_authorized": False,
        "training_authorized": False,
        "seed": 1729,
        "model": {
            "objective": "binary:logistic",
            "tree_method": "hist",
            "random_state": 1729,
            "n_jobs": 1,
        },
        "calibration": {"method": "regularized_intercept", "penalty": 1},
        "policy": {"B": 1, "unit": "false_onset_alerts_per_eligible_municipality_year"},
        "uncertainty": {
            "method": "paired municipality and episode-preserving connected calendar-year blocks",
            "confidence": 0.95,
            "draws": 10,
            "minimum_municipalities": 2,
            "minimum_temporal_blocks": 2,
            "minimum_valid_fraction": 0.8,
            "seed": 1729,
        },
    }
    context = {"contract": contract, "plan": {"counts": {"models": 2, "calibrators": 2}}}
    current = {
        "commit": "a" * 40,
        "dirty": False,
        "runtime": {"generated_fixture_runtime": "1"},
        "roots": {"publication": "data/processed/exp_delta03", "tracking": "tmp/isolated-fixture"},
    }
    now = datetime(2026, 11, 5, tzinfo=UTC)
    grant = {
        "schema": "exp-delta03-phase3-authorization-v1",
        "phase": 3,
        "approved_by": "Mauricio",
        "identity": current,
        "identity_sha256": digest(current),
        "issued_at": (now - timedelta(hours=1)).isoformat(),
        "expires_at": (now + timedelta(hours=1)).isoformat(),
        "allow_resume": True,
        "limits": {
            "max_models": 2,
            "max_calibrators": 2,
            "threads_per_model": 1,
            "wall_seconds": 30,
        },
        "acknowledgements": [
            "retrospective_only",
            "no_PIT_or_deployment",
            "2025_excluded",
            "2024_stress_separate",
            "manual_execution",
        ],
    }
    relative = "tmp/exp-delta03-phase3/generated-authorization.json"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_bytes(canonical(grant))
    return context, current, grant, now, relative


def test_real_authorization_identity_caps_scope_and_expiry_are_checked_before_output(tmp_path):
    context, current, grant, now, relative = authorization_fixture(tmp_path)
    assert authorize(tmp_path, context, current, authorization_relative=relative, now=now)[
        "allow_resume"
    ]
    for mutation in ["identity", "caps", "expired", "dirty", "scope"]:
        altered = copy.deepcopy(grant)
        actual = copy.deepcopy(current)
        if mutation == "identity":
            altered["identity_sha256"] = "changed"
        if mutation == "caps":
            altered["limits"]["max_models"] = 3
        if mutation == "expired":
            altered["expires_at"] = (now - timedelta(minutes=1)).isoformat()
        if mutation == "dirty":
            actual["dirty"] = True
        if mutation == "scope":
            altered["acknowledgements"] = []
        (tmp_path / relative).write_bytes(canonical(altered))
        with pytest.raises(PermissionError):
            authorize(tmp_path, context, actual, authorization_relative=relative, now=now)
    assert not (tmp_path / "data").exists()
    context["contract"]["decision_status"] = "PENDING_HUMAN_FREEZE"
    with pytest.raises(ValueError, match="freeze"):
        authorize(tmp_path, context, current, authorization_relative=relative, now=now)
