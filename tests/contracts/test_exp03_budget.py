"""Source-free contracts for the human-approved EXP03 budget; no fits or approvals."""

from __future__ import annotations

import copy
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml  # type: ignore[import-untyped]

from sat_dengue.experiments import exp03
from sat_dengue.experiments import exp03_preflight as pf
from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_contract import matrix
from sat_dengue.experiments.exp03_engine import require_budget
from sat_dengue.experiments.exp03_revision import cell_counts
from sat_dengue.tracking.experiments import resolve_experiment

OLD_SHA = "f806f3897a8dbef2bea01333626ee943e45aec9892f91607ca899f003e55beaf"
BASE = "4f43482c5fd25e64df73c0396c1fef183f95c39a"


def test_patch_preserves_historical_protocol_and_scientific_scope() -> None:
    old_path = exp03.PROTOCOL.with_name("protocol.v2.0.0.json")
    original = subprocess.check_output(["git", "show", f"{BASE}:{exp03.PROTOCOL}"])
    assert old_path.read_bytes() == original
    old = json.loads(original)
    current = exp03.load_protocol()
    assert digest(old) == OLD_SHA
    assert current["version"] == "2.0.1"
    assert current["scope_revision"]["previous_protocol_sha256"] == OLD_SHA
    assert current["scope_revision"]["scientific_budget_pending"] is False
    assert (
        current["scope_revision"]["scientific_budget_decision"] == "human_approved_before_execution"
    )
    assert current["design"]["B_primary"] == current["alert_policy"]["B_primary"] == 1.0
    assert cell_counts(current["design"]) == dict(onset=384, excess=24, total=408, terminal=102)
    assert (
        current["alert_policy"]["monitored_exposure"] == old["alert_policy"]["monitored_exposure"]
    )
    assert math.floor(require_budget(current["design"])["value"] * (76 * 6 / 12)) == 38
    normalized = copy.deepcopy(current)
    for key in ("version", "comparison", "scope_revision", "alert_policy"):
        normalized[key] = old[key]
    for key in ("B_primary", "budget_rationale"):
        normalized["design"][key] = old["design"][key]
    assert normalized == old
    assert current["acceptance"]["G5"] == "NOT_APPROVED"
    assert current["acceptance"]["champion"] == "not_selected"
    assert current["execution"]["real_execution_authorized"] is False
    assert resolve_experiment("EXP03")["protocol_sha256"] == digest(current)
    assert yaml.safe_load(
        exp03.PROTOCOL.with_name("ablation-matrix.frozen.yml").read_text()
    ) == matrix(current)


@pytest.mark.parametrize("value", [None, 0, -1, float("nan"), float("inf"), True, "1.0"])
def test_budget_rejects_missing_nonfinite_nonpositive(value: Any) -> None:
    design = copy.deepcopy(exp03.load_protocol()["design"])
    design["B_primary"] = value
    with pytest.raises((ValueError, PermissionError)):
        require_budget(design)


@pytest.mark.parametrize("rationale", [None, "", " \n", 42])
def test_budget_requires_text_rationale(rationale: Any) -> None:
    design = copy.deepcopy(exp03.load_protocol()["design"])
    design["budget_rationale"] = rationale
    with pytest.raises(PermissionError):
        require_budget(design)


@pytest.mark.parametrize("mutation", ["policy", "pending", "decision", "version"])
def test_loader_rejects_inconsistent_decision(
    mutation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.tracking import experiments

    protocol = exp03.load_protocol()
    exp01_identity = experiments.resolve_experiment("EXP01")
    if mutation == "policy":
        protocol["alert_policy"]["B_primary"] = 2.0
    elif mutation == "pending":
        protocol["scope_revision"]["scientific_budget_pending"] = True
    elif mutation == "decision":
        protocol["scope_revision"].pop("scientific_budget_decision")
    else:
        protocol["version"] = "2.0.0"
    original = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: (
            json.dumps(protocol) if path == exp03.PROTOCOL else original(path, *a, **kw)
        ),
    )
    monkeypatch.setattr(
        experiments,
        "resolve_experiment",
        lambda identifier: (
            {"protocol_sha256": digest(protocol)} if identifier == "EXP03" else exp01_identity
        ),
    )
    with pytest.raises(ValueError, match="budget decision"):
        exp03.load_protocol()


def test_loader_rejects_budget_hash_tampering(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = exp03.load_protocol()
    protocol["design"]["B_primary"] = 2.0
    original = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: (
            json.dumps(protocol) if path == exp03.PROTOCOL else original(path, *a, **kw)
        ),
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        exp03.load_protocol()


@pytest.mark.parametrize("changed", ["protocol_sha256", "configuration_sha256", "fresh_budget"])
def test_authorization_rejects_identity_or_budget_substitution(
    changed: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    protocol = exp03.load_protocol()
    receipt = {
        "protocol_sha256": digest(protocol),
        "configuration_sha256": "c" * 64,
        "git_revision": "a" * 40,
        "data_version": "d" * 64,
        "tracking": {"state": "not_initialized"},
        "git_dirty": False,
        "B_primary": 1.0,
        "status": "structural_pass",
        "source_identity_status": "pending_authorized_verification",
        "execution_ready": False,
    }
    approval = {
        "schema": "exp03-execution-approval-v2",
        "structural_receipt_sha256": digest(receipt),
        "experiment_id": "EXP03",
        "authority": "Mauricio",
        "independent_reviewer": "FixtureReviewer",
        **{
            k: receipt[k]
            for k in ("protocol_sha256", "configuration_sha256", "git_revision", "data_version")
        },
        "real_execution_authorized": True,
        "comparator_refit_authorized": True,
        "variant_refits_authorized": True,
        "retrospective_availability_acknowledged": True,
    }
    if changed != "fresh_budget":
        approval[changed] = "0" * 64
    fresh = {**receipt, "B_primary": 2.0}
    monkeypatch.setattr(pf, "load_protocol", lambda: protocol)
    monkeypatch.setattr(pf, "preflight", lambda *a: fresh)
    monkeypatch.setattr(pf, "git_identity", lambda: {"git_dirty": False})
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: json.dumps(approval))
    monkeypatch.setenv("SAT_DENGUE_EXP03_APPROVAL", "tmp/in-memory-exp03-record.json")
    with pytest.raises(PermissionError, match="authorization"):
        pf.authorize(receipt)


def test_stale_protocol_rejected_before_approval_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAT_DENGUE_EXP03_APPROVAL", raising=False)
    with pytest.raises(PermissionError, match="protocol mismatch"):
        pf.authorize({"protocol_sha256": OLD_SHA})
