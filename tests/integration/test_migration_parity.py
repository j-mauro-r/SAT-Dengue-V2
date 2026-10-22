"""Session 1 protection and native replay; default CI needs only synthetic data.

Later stage parity tests retain baseline/preparation/training/evaluation selectors.
The protected inventory is deliberately external to Git and pinned by its digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from migration_support import (
    BASELINE_SHA256,
    FINAL_ID,
    FINAL_PATH,
    approved_scope,
    compare_frames,
    fingerprint,
    require_records,
    safe_path,
    verify_equivalence_scope,
    verify_native_bundle,
    verify_protected_inventory,
    verify_source_scope,
)

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "tmp/kedro-migration"


def synthetic_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "key": ["A:2024-01", "A:2024-02"],
            "zone": pd.Categorical(["ALERTA", "EXCESO"], ordered=True),
            "label": pd.Series([0, 1], dtype="Int64"),
            "alert": [False, True],
            "decision": ["does_not_meet", "does_not_meet"],
            "probability": [0.125, 0.75],
        }
    )


def test_baseline_comparator_accepts_declared_numeric_tolerance() -> None:
    expected = synthetic_frame()
    actual = expected.copy()
    actual["probability"] += 1e-11
    compare_frames(expected, actual, numeric=("probability",))
    with pytest.raises(AssertionError):
        compare_frames(expected, actual, numeric=("probability",), exact_numeric=True)


@pytest.mark.parametrize(
    "mutation",
    [
        "key",
        "zone",
        "label",
        "alert",
        "decision",
        "mask",
        "order",
        "columns",
        "numeric",
        "infinite",
        "empty",
    ],
)
def test_baseline_comparator_rejects_scientific_drift(mutation: str) -> None:
    expected = synthetic_frame()
    actual = expected.copy()
    if mutation in {"key", "decision"}:
        actual.loc[0, mutation] = "changed"
    elif mutation == "zone":
        actual["zone"] = actual.zone.cat.reorder_categories(["EXCESO", "ALERTA"], ordered=True)
    elif mutation == "label":
        actual.loc[0, "label"] = 1
    elif mutation == "alert":
        actual.loc[0, "alert"] = True
    elif mutation == "mask":
        actual.loc[0, "probability"] = float("nan")
    elif mutation == "order":
        actual = actual.iloc[::-1].reset_index(drop=True)
    elif mutation == "columns":
        actual = actual[list(reversed(actual.columns))]
    elif mutation == "numeric":
        actual.loc[0, "probability"] += 1e-5
    elif mutation == "infinite":
        actual.loc[0, "probability"] = float("inf")
    elif mutation == "empty":
        actual = actual.iloc[:0]
    with pytest.raises(AssertionError):
        compare_frames(expected, actual, numeric=("probability",))


def test_baseline_requires_payload_hashes_and_nonempty_evidence(tmp_path: Path) -> None:
    path = tmp_path / "payload.txt"
    path.write_text("synthetic immutable payload")
    records = {path.name: fingerprint(path)}
    assert require_records(tmp_path, records) == 1
    path.write_text("tampered")
    with pytest.raises(AssertionError, match="fingerprint mismatch"):
        require_records(tmp_path, records)
    with pytest.raises(AssertionError, match="Zero eligible"):
        require_records(tmp_path, {})
    with pytest.raises(AssertionError, match="missing"):
        require_records(tmp_path, {"missing.txt": records[path.name]})


@pytest.mark.parametrize("path", ["../outside", "/outside", "nested/../../outside", ""])
def test_baseline_rejects_unsafe_evidence_paths(tmp_path: Path, path: str) -> None:
    with pytest.raises(AssertionError, match="Unsafe"):
        safe_path(tmp_path, path)


def test_baseline_bundle_rejects_corruption_and_extra_payloads(tmp_path: Path) -> None:
    payload = tmp_path / "model.txt"
    payload.write_text("synthetic native component")
    (tmp_path / "manifest.json").write_text(
        json.dumps({"files": {payload.name: fingerprint(payload)}})
    )
    verify_native_bundle(tmp_path)
    (tmp_path / "unexpected.txt").write_text("extra")
    with pytest.raises(AssertionError, match="payload set"):
        verify_native_bundle(tmp_path)
    payload.write_text("corrupted")
    with pytest.raises(AssertionError, match="fingerprint mismatch"):
        verify_native_bundle(tmp_path)


def synthetic_source_scope(root: Path) -> tuple[dict, dict, dict, set[tuple[str, str]]]:
    """Two linked active bundles plus one incomplete historical bundle."""
    names = ["upstream/manifest.json", "final/manifest.json", "historical/manifest.json"]
    baseline: dict = {"protected": {}, "bundles": {}}
    for name, sources in zip(
        names, [("active",), ("active",), ("old", "available-old")], strict=True
    ):
        path = root / name
        path.parent.mkdir()
        payload = path.parent / "component.txt"
        payload.write_text("native synthetic component")
        identity: dict = {"code": {s: {"sha256": s} for s in sources}}
        if name == names[1]:
            identity["upstream"] = baseline["protected"][names[0]]
        path.write_text(
            json.dumps(
                {
                    "bundle_id": path.parent.name,
                    "identity": identity,
                    "files": {payload.name: fingerprint(payload)},
                }
            )
        )
        baseline["protected"][name] = fingerprint(path)
        baseline["protected"][str(payload.relative_to(root))] = fingerprint(payload)
        baseline["bundles"][name] = {
            "bundle_id": path.parent.name,
            "manifest": fingerprint(path),
        }
    coverage = {
        "active_chain": sorted(names[:2]),
        "active_missing": [],
        "historical_only_missing": [{"path": "old", "sha256": "old"}],
    }
    scope = {
        **coverage,
        "historical_bundles": {
            names[2]: {
                "action": "KEEP",
                "source_status": "UNVERIFIED",
                "modification_allowed": False,
                "equivalence_evidence": False,
                "manifest": baseline["protected"][names[2]],
            }
        },
        "full_historical_reproducibility": False,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "consumed_2025": True,
        "allow_2025_selection_tuning_training": False,
        "new_real_fits": 0,
    }
    return baseline, scope, coverage, {("active", "active"), ("available-old", "available-old")}


@pytest.mark.parametrize(
    "mutation",
    [
        "none",
        "active_missing",
        "additional_historical_missing",
        "exception_path",
        "exception_hash",
        "retire",
        "verified",
        "modify",
        "equivalence",
        "full_history",
        "coverage_lie",
        "chain",
        "G5",
        "champion",
        "consumed",
        "selection",
        "fit",
    ],
)
def test_baseline_closed_source_scope(tmp_path: Path, mutation: str) -> None:
    baseline, scope, coverage, recovered = synthetic_source_scope(tmp_path)
    # Independent copy: changing the proposed scope must never change observed coverage.
    scope = json.loads(json.dumps(scope))
    historical = scope["historical_bundles"]["historical/manifest.json"]
    if mutation == "active_missing":
        recovered.remove(("active", "active"))
    elif mutation == "additional_historical_missing":
        recovered.remove(("available-old", "available-old"))
    elif mutation in {"exception_path", "exception_hash"}:
        key = "path" if mutation == "exception_path" else "sha256"
        scope["historical_only_missing"][0][key] = "changed"
    elif mutation == "retire":
        historical["action"] = "RETIRE"
    elif mutation == "verified":
        historical["source_status"] = "VERIFIED"
    elif mutation == "modify":
        historical["modification_allowed"] = True
    elif mutation == "equivalence":
        historical["equivalence_evidence"] = True
    elif mutation == "full_history":
        scope["full_historical_reproducibility"] = True
    elif mutation == "coverage_lie":
        coverage["historical_only_missing"] = []
    elif mutation == "chain":
        scope["active_chain"] = ["final/manifest.json"]
    elif mutation == "G5":
        scope["G5"] = "APPROVED"
    elif mutation == "champion":
        scope["champion"] = "lightgbm"
    elif mutation == "consumed":
        scope["consumed_2025"] = False
    elif mutation == "selection":
        scope["allow_2025_selection_tuning_training"] = True
    elif mutation == "fit":
        scope["new_real_fits"] = 1

    def check() -> dict:
        return verify_source_scope(
            tmp_path, baseline, recovered, scope, coverage, final="final/manifest.json"
        )

    if mutation == "none":
        assert check() == coverage
    else:
        with pytest.raises(AssertionError):
            check()


def test_baseline_replay_rejects_historical_equivalence(tmp_path: Path) -> None:
    _, scope, _, _ = synthetic_source_scope(tmp_path)
    report = {**scope, "equivalence_bundles": scope["active_chain"]}
    verify_equivalence_scope(scope, report)
    report["equivalence_bundles"] = [*scope["active_chain"], "historical/manifest.json"]
    with pytest.raises(AssertionError, match="Equivalence"):
        verify_equivalence_scope(scope, report)


@pytest.mark.parametrize(
    "mutation", ["none", "replace", "delete", "extra", "nested_extra", "identity", "symlink"]
)
def test_baseline_post_replay_disk_scan(tmp_path: Path, mutation: str) -> None:
    baseline, _, _, _ = synthetic_source_scope(tmp_path)
    component = tmp_path / "historical/component.txt"
    if mutation == "replace":
        replacement = tmp_path / "replacement.txt"
        # Same size: SHA-256, not just size, must discriminate native replacement.
        replacement.write_bytes(b"X" * component.stat().st_size)
        os.replace(replacement, component)
    elif mutation == "delete":
        component.unlink()
    elif mutation == "extra":
        (component.parent / "extra.txt").write_text("extra")
    elif mutation == "nested_extra":
        (component.parent / "extra").mkdir()
        (component.parent / "extra/hidden.txt").write_text("extra")
    elif mutation == "identity":
        manifest = component.parent / "manifest.json"
        doc = json.loads(manifest.read_text())
        doc["bundle_id"] = "different"
        manifest.write_text(json.dumps(doc))
    elif mutation == "symlink":
        component.unlink()
        component.symlink_to(tmp_path / "final/component.txt")
    if mutation == "none":
        report = verify_protected_inventory(tmp_path, baseline)
        assert report["status"] == "PASS" and report["protected_files"] == 6
        assert report["bundles"] == 3
    else:
        with pytest.raises(AssertionError):
            verify_protected_inventory(tmp_path, baseline)


@pytest.fixture(scope="session")
def protected_baseline() -> dict:
    path = EVIDENCE / "baseline.json"
    assert fingerprint(path)["sha256"] == BASELINE_SHA256, "Baseline inventory changed"
    baseline = json.loads(path.read_text())
    assert baseline["schema"] == "migration-baseline-v1"
    assert baseline["initial_git_status"] == ""
    return baseline


@pytest.mark.migration_evidence
def test_baseline_protected_inputs_and_scientific_contracts(protected_baseline: dict) -> None:
    assert require_records(ROOT, protected_baseline["protected"]) == 2553
    summary = json.loads((ROOT / FINAL_PATH / "run_summary.json").read_text())
    assert summary["G5"] == "NOT_APPROVED"
    assert summary["champion"] == "not_selected"
    assert {(r["candidate"], r["horizon"]) for r in summary["comparison"]} == {
        (family, h) for family in ("persistence", "xgboost", "lightgbm", "gam") for h in (1, 2)
    }
    assert len(summary["comparison"]) == 8


@pytest.mark.migration_evidence
def test_baseline_all_native_bundles(protected_baseline: dict) -> None:
    assert len(protected_baseline["bundles"]) == 45
    for relative in protected_baseline["bundles"]:
        verify_native_bundle(safe_path(ROOT, relative).parent)


@pytest.mark.migration_evidence
def test_baseline_historical_source_reconstruction(protected_baseline: dict) -> None:
    report = json.loads((EVIDENCE / "reconstruction-local.json").read_text())
    assert report["engineering_base"] == protected_baseline["engineering_base"]
    recovered = set()
    for record in report["recovered"]:
        path = EVIDENCE / "objects" / record["raw_record"]["sha256"]
        assert fingerprint(path) == record["raw_record"]
        payload = path.read_bytes()
        representation = record["representation"]
        if representation in {"code_cells", "nbformat_code_cells", "sources"}:
            notebook = json.loads(payload)
            cells = ["".join(c["source"]) for c in notebook["cells"]]
            content = (
                {"cells": cells}
                if representation == "sources"
                else {
                    "cells": [
                        {"cell_type": c["cell_type"], "source": "".join(c["source"])}
                        for c in notebook["cells"]
                    ]
                }
            )
            if representation == "nbformat_code_cells":
                content["nbformat"] = notebook["nbformat"]
            payload = (json.dumps(content, sort_keys=True, indent=2) + "\n").encode()
        assert hashlib.sha256(payload).hexdigest() == record["expected_sha256"]
        recovered.add((record["path"], record["expected_sha256"]))
    # Still inspect every historical source; the exception set is closed, never a skip.
    scope = approved_scope(ROOT)
    coverage = json.loads((EVIDENCE / "source-coverage.json").read_text())
    observed = verify_source_scope(ROOT, protected_baseline, recovered, scope, coverage)
    assert len(observed["active_chain"]) == 12
    assert len(observed["historical_only_missing"]) == 13
    assert len(scope["historical_bundles"]) == 17
    (EVIDENCE / "source-coverage-observed.json").write_text(json.dumps(observed, indent=2) + "\n")


@pytest.mark.migration_evidence
@pytest.mark.parametrize("runtime,version", [("historical46", "4.6.0"), ("candidate47", "4.7.0")])
def test_compatibility_saved_components_without_fitting(
    runtime: str, version: str, protected_baseline: dict
) -> None:
    interpreter = EVIDENCE / runtime / "bin/python"
    assert interpreter.is_file(), f"Required runtime missing: {runtime}"
    snapshot = EVIDENCE / "snapshots" / FINAL_ID
    assert (snapshot / "scripts/final_evaluation/pipeline.py").is_file(), "Historical code missing"
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    paths = [str(snapshot), str(Path(__file__).parent)]
    if version == "4.7.0":
        assert (EVIDENCE / "lightgbm47/lightgbm").is_dir(), "Candidate LightGBM missing"
        paths.insert(0, str(EVIDENCE / "lightgbm47"))
    env["PYTHONPATH"] = os.pathsep.join(paths)
    postcheck = None
    replay_started_at = datetime.now(UTC).isoformat()
    try:
        result = subprocess.run(
            [
                str(interpreter),
                str(Path(__file__).with_name("migration_replay.py")),
                str(ROOT),
                str(snapshot),
                version,
            ],
            cwd=snapshot,
            env=env,
            text=True,
            capture_output=True,
            timeout=600,
        )
    finally:
        # Always run after the candidate process, even on replay failure or timeout.
        # This independent scan also catches writes that bypass Python's open audit hook.
        if version == "4.7.0":
            receipt = EVIDENCE / "post-replay-4.7.0.json"
            postcheck = {
                "status": "FAIL",
                "replay_started_at": replay_started_at,
                "scan_started_at": datetime.now(UTC).isoformat(),
            }
            try:
                assert fingerprint(EVIDENCE / "baseline.json")["sha256"] == BASELINE_SHA256
                postcheck.update(verify_protected_inventory(ROOT, protected_baseline))
                assert postcheck["protected_files"] == 2553
            except Exception as error:
                postcheck["status"] = "FAIL"
                postcheck["error"] = str(error)
                raise
            finally:
                postcheck["scan_finished_at"] = datetime.now(UTC).isoformat()
                receipt.write_text(json.dumps(postcheck, indent=2) + "\n")
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report["models"] == 6 and report["predictions"] == 5472
    assert report["new_fits"] == 0
    assert report["version"] == version
    verify_equivalence_scope(approved_scope(ROOT), report)
    if version == "4.7.0":
        assert postcheck is not None and postcheck["status"] == "PASS"
        report["post_replay_verification"] = postcheck
    (EVIDENCE / f"compatibility-{version}.json").write_text(json.dumps(report, indent=2) + "\n")


def test_compatibility_guard_rejects_fit_and_preserves_artifacts(tmp_path: Path) -> None:
    """Exercise the worker guard in a disposable process without installing a global hook."""
    artifact = tmp_path / "immutable.txt"
    artifact.write_text("unchanged synthetic evidence")
    program = """
import pathlib, sys
from migration_replay import deny_fitting, deny_writes
sys.setprofile(deny_fitting)
def fit_estimator():
    raise RuntimeError('fit body must never execute')
try:
    fit_estimator()
except AssertionError as error:
    assert 'Forbidden fit' in str(error)
else:
    raise AssertionError('fit guard did not fire')
sys.setprofile(None)
sys.addaudithook(deny_writes)
try:
    pathlib.Path(sys.argv[1]).write_text('changed')
except AssertionError as error:
    assert 'must not write' in str(error)
else:
    raise AssertionError('write guard did not fire')
"""
    import sys

    result = subprocess.run(
        [sys.executable, "-c", program, str(artifact)],
        cwd=Path(__file__).parent,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert artifact.read_text() == "unchanged synthetic evidence"


def test_baseline_required_gate_rejects_zero_selected_evidence() -> None:
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(Path(__file__)),
            "-k",
            "nonexistent_migration_comparison",
            "--require-migration-evidence",
            "-q",
        ],
        cwd=ROOT,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 4
    assert "zero eligible migration comparisons" in result.stderr
