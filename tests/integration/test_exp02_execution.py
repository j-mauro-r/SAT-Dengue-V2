"""Generated-only authorization, identity drift, reservations and atomic publication."""

import copy
import json
from pathlib import Path

import pytest

from sat_dengue.datasets.exp02 import publish_native
from sat_dengue.experiments import exp02_preflight as checks
from sat_dengue.experiments import exp02_runner as runner
from sat_dengue.experiments.exp01_runner import reserve_execution
from sat_dengue.tracking.exp02 import verified_result

ROOT = Path(__file__).resolve().parents[2]


def approval_for(receipt):
    return {
        "schema": "exp02-execution-approval-v1",
        "experiment_id": "EXP02",
        "authority": "Mauricio",
        "independent_reviewer": "generated-reviewer",
        "independent_reviewer_approved": True,
        "real_execution_authorized": True,
        "retrospective_availability_acknowledged": True,
        "refits_authorized": True,
        "max_model_fits": 54,
        "max_calibrator_fits": 54,
        **{k: receipt[k] for k in checks.BINDINGS},
    }


def install_generated_approval(receipt, folder, monkeypatch, mutation=None):
    approval = approval_for(receipt)
    if mutation:
        approval[mutation] = False if isinstance(approval[mutation], bool) else "changed"
    path = folder / "generated-approval.json"
    path.write_text(json.dumps(approval))
    monkeypatch.setenv("SAT_DENGUE_EXP02_APPROVAL", str(path.relative_to(ROOT)))
    return approval


def test_absent_approval_precedes_private_loader_and_fit(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Private loader or fitter reached")

    monkeypatch.delenv("SAT_DENGUE_EXP02_APPROVAL", raising=False)
    monkeypatch.setattr(runner, "prepare_exp01_inputs", forbidden)
    monkeypatch.setattr(runner, "native_fit", forbidden)
    with pytest.raises(PermissionError, match="separate human"):
        runner.load_authorized_sources({})


@pytest.mark.parametrize(
    "field",
    [
        *checks.BINDINGS,
        "real_execution_authorized",
        "independent_reviewer_approved",
        "retrospective_availability_acknowledged",
        "refits_authorized",
        "authority",
        "independent_reviewer",
        "max_model_fits",
        "max_calibrator_fits",
    ],
)
def test_stale_or_incomplete_approval_rejected(exp02_receipt, repo_tmp_path, monkeypatch, field):
    install_generated_approval(exp02_receipt, repo_tmp_path, monkeypatch, field)
    # A different syntactically valid reviewer is still an identity, not a missing approval.
    if field == "independent_reviewer":
        path = Path(__import__("os").environ["SAT_DENGUE_EXP02_APPROVAL"])
        value = json.loads(path.read_text())
        value[field] = "Mauricio"
        path.write_text(json.dumps(value))
    with pytest.raises((PermissionError, ValueError)):
        checks.authorize(exp02_receipt)


@pytest.mark.parametrize(
    "change",
    ["commit", "dirty", "code", "runtime", "metadata", "root", "configuration", "protocol"],
)
def test_valid_approval_invalidated_by_fresh_identity_drift(
    exp02_receipt, repo_tmp_path, monkeypatch, change
):
    install_generated_approval(exp02_receipt, repo_tmp_path, monkeypatch)
    assert checks.authorize(exp02_receipt)["authority"] == "Mauricio"
    if change in {"commit", "dirty"}:
        monkeypatch.setattr(
            checks,
            "git_identity",
            lambda: {
                "git_revision": "f" * 40 if change == "commit" else "a" * 40,
                "git_dirty": change == "dirty",
            },
        )
    elif change in {"code", "runtime"}:
        metadata = copy.deepcopy(checks.execution_metadata())
        metadata["code_sha256" if change == "code" else "environment_sha256"] = "f" * 64
        monkeypatch.setattr(checks, "execution_metadata", lambda: metadata)
    elif change == "metadata":
        monkeypatch.setattr(checks, "source_metadata", lambda: {"changed": True})
    elif change == "root":
        monkeypatch.setenv(
            "SAT_DENGUE_TRACKING_ROOT", str((repo_tmp_path / "other").relative_to(ROOT))
        )
    elif change == "configuration":
        monkeypatch.setattr(checks, "configuration_identity", lambda *args: "f" * 64)
    else:
        protocol = copy.deepcopy(checks.load_protocol())
        protocol["version"] = "changed"
        monkeypatch.setattr(checks, "load_protocol", lambda: protocol)
    with pytest.raises(PermissionError, match="stale"):
        checks.authorize(exp02_receipt)


def test_reservation_persists_and_approval_changes_do_not_allow_duplicate(repo_tmp_path):
    root = str((repo_tmp_path / "reservations").relative_to(ROOT))
    provenance = {"generated": True, "approval_sha256": "a" * 64}
    execution = reserve_execution(provenance, root)
    assert (ROOT / root / (execution + ".reservation")).exists()
    with pytest.raises(ValueError, match="duplicate or interrupted"):
        reserve_execution({**provenance, "approval_sha256": "b" * 64}, root)


def test_atomic_no_overwrite_and_postpublication_tampering(exp02_generated_bundle, repo_tmp_path):
    root = str((repo_tmp_path / "native").relative_to(ROOT))
    publication = publish_native(exp02_generated_bundle, root)
    verified_result(publication)
    with pytest.raises(ValueError, match="replacement is forbidden"):
        publish_native(exp02_generated_bundle, root)
    payload = Path(publication["path"]) / "result.json"
    payload.write_bytes(payload.read_bytes() + b" ")
    with pytest.raises(ValueError, match="payload changed"):
        verified_result(publication)


@pytest.mark.parametrize("path", ["/tmp/external", "tmp/../outside", "data/out", ""])
def test_output_roots_are_bounded(path):
    with pytest.raises(ValueError):
        checks.safe_path(path, temporary=True)


def test_symlink_publication_and_tracking_rejected(exp02_generated_bundle, repo_tmp_path):
    link = repo_tmp_path / "link"
    link.symlink_to(ROOT)
    with pytest.raises(ValueError, match="symlink"):
        publish_native(exp02_generated_bundle, str(link.relative_to(ROOT)))
    with pytest.raises(ValueError, match="symlink"):
        checks.storage_preflight(str(link.relative_to(ROOT)))


def test_guard_detects_authorization_change_before_any_scientific_node(
    exp02_receipt, repo_tmp_path, monkeypatch
):
    approval = install_generated_approval(exp02_receipt, repo_tmp_path, monkeypatch)
    context = {
        "preflight": exp02_receipt,
        "approval_sha256": runner.digest(approval),
        "input_fingerprints": {},
    }
    runner.guard(context)
    context["approval_sha256"] = "f" * 64
    for operation in (
        runner.construct_authorized,
        runner.compare_authorized,
        runner.predictive_authorized,
        runner.publication_authorized,
    ):
        with pytest.raises(PermissionError, match="approval changed"):
            operation(context)


@pytest.mark.parametrize("interrupt", [False, True])
def test_protected_graph_generated_admission_publication_and_interruption(
    exp02_receipt, repo_tmp_path, monkeypatch, interrupt
):
    from types import SimpleNamespace

    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
    from sat_dengue.experiments.exp01 import synthetic_fit
    from sat_dengue.pipeline_registry import register_pipelines
    from sat_dengue.tracking.exp02 import export_authorized

    root = str((repo_tmp_path / "generated-real-route").relative_to(ROOT))
    generated_source = repo_tmp_path / "generated-manifest.json"
    generated_source.write_text('{"generated":true}')
    relative = str(generated_source.relative_to(ROOT))
    pinned = {relative: fingerprint(generated_source)}
    for module in (checks, runner):
        monkeypatch.setattr(module, "NATIVE_MANIFEST", relative)
        monkeypatch.setattr(module, "NATIVE_IDENTITIES", pinned)
    monkeypatch.setattr(checks, "OUTPUT_ROOT", root)
    # Actual catalog path materialization has a separate test; this graph owns
    # MemoryDatasets so the immutable production output directory is never used.
    monkeypatch.setattr(checks, "materialize_publication_dataset", lambda: None)
    params = {"profile": "exp02", "tracking": "enabled", "experiment_id": "EXP02"}
    receipt = checks.preflight(params, checks.source_metadata())
    install_generated_approval(receipt, repo_tmp_path, monkeypatch)
    panel, contract, _ = runner.synthetic_inputs()
    protocol = copy.deepcopy(checks.load_protocol())
    protocol["population"]["municipalities"] = 6
    monkeypatch.setattr(runner, "load_protocol", lambda: protocol)
    calls = []

    def generated_admission(config):
        assert checks.authorize(receipt)
        calls.append("admission")
        return SimpleNamespace(
            panel=panel, contract=contract, report={"input_fingerprints": pinned}
        )

    def generated_fit(*args):
        assert list(Path(root).glob("*.reservation"))
        calls.append("fit_interface")
        if interrupt:
            raise RuntimeError("generated interruption")
        return synthetic_fit(*args)

    def generated_calibration(scores, truth, seed):
        calls.append("calibration_interface")
        return lambda values: values

    monkeypatch.setattr(runner, "prepare_exp01_inputs", generated_admission)
    monkeypatch.setattr(runner, "native_fit", generated_fit)
    monkeypatch.setattr(runner, "native_calibration", generated_calibration)
    catalog = DataCatalog(
        {
            "parameters": MemoryDataset(params),
            "exp02_sources": MemoryDataset(checks.source_metadata()),
            "exp02_bundle": MemoryDataset(),
        }
    )
    if interrupt:
        with pytest.raises(RuntimeError, match="generated interruption"):
            SequentialRunner().run(register_pipelines()["exp02"], catalog)
        assert len(list(Path(root).glob("*.reservation"))) == 1
        assert not Path(receipt["tracking_root"]).exists()
        return
    SequentialRunner().run(register_pipelines()["exp02"], catalog)
    data = catalog.load("exp02_bundle")
    assert calls[0] == "admission"
    assert calls.count("fit_interface") == calls.count("calibration_interface") == 54
    publication = publish_native(data, root)
    # This fixture exercises native orchestration with fixed generated adapters;
    # these 54 interface calls are zero estimator/calibrator fits.
    run_id = export_authorized(publication, receipt)
    assert len(run_id) == 32
    generated_source.write_text('{"generated":"changed"}')
    with pytest.raises(ValueError, match="contents changed"):
        runner.guard(data["context"], contents=True)


def test_invalid_output_or_overlapping_roots_fail_before_store_inspection(
    repo_tmp_path, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Store inspection before output validation")

    monkeypatch.setattr(checks.shared, "storage_preflight", forbidden)
    path = repo_tmp_path / "occupied"
    path.write_text("generated")
    monkeypatch.setattr(checks, "OUTPUT_ROOT", str(path.relative_to(ROOT)))
    with pytest.raises(ValueError, match="directory"):
        checks.storage_preflight(str((repo_tmp_path / "tracking").relative_to(ROOT)))
    with pytest.raises(ValueError, match="separate"):
        checks.storage_preflight(str(repo_tmp_path.relative_to(ROOT)))


def test_export_cannot_read_bundle_outside_approved_output(
    exp02_receipt, repo_tmp_path, monkeypatch
):
    from sat_dengue.tracking import exp02 as tracking

    install_generated_approval(exp02_receipt, repo_tmp_path, monkeypatch)

    def forbidden(*args, **kwargs):
        raise AssertionError("Unapproved bundle read")

    monkeypatch.setattr(tracking, "verified_result", forbidden)
    with pytest.raises(PermissionError, match="export path"):
        tracking.export_authorized(
            {"path": str((repo_tmp_path / ("a" * 64)).relative_to(ROOT))}, exp02_receipt
        )
