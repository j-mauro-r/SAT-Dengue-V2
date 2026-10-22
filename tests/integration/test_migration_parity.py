"""Session 1 protection and native replay; default CI needs only synthetic data.

Later stage parity tests retain baseline/preparation/training/evaluation selectors.
The protected inventory is deliberately external to Git and pinned by its digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from migration_support import (
    BASELINE_SHA256,
    FINAL_ID,
    FINAL_PATH,
    compare_frames,
    fingerprint,
    require_records,
    safe_path,
    verify_native_bundle,
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
    required = set()
    for name in protected_baseline["bundles"]:
        identity = json.loads((ROOT / name).read_text()).get("identity", {})
        for group in ("code", "stage4_code"):
            for path, record in identity.get(group, {}).items():
                if isinstance(record, dict) and "sha256" in record:
                    required.add((path, record["sha256"]))
    assert required, "Zero eligible historical source comparisons"
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
    # Derive missing coverage from immutable manifests, never a report's status field.
    missing = sorted(required - recovered)
    assert not missing, f"Unrecovered historical source records: {missing}"


@pytest.mark.migration_evidence
@pytest.mark.parametrize("runtime,version", [("historical46", "4.6.0"), ("candidate47", "4.7.0")])
def test_compatibility_saved_components_without_fitting(runtime: str, version: str) -> None:
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
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.strip().splitlines()[-1])
    assert report["models"] == 6 and report["predictions"] == 5472
    assert report["new_fits"] == 0
    assert report["version"] == version
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
