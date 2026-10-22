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
    verify_preservation_records,
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
    assert verify_preservation_records(ROOT, protected_baseline["protected"]) == 2553
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


@pytest.mark.migration_evidence
def test_data_kedro_complete_stage2_parity(protected_baseline: dict) -> None:
    """Run actual Kedro over all protected Stage 2 inputs; compare every output row."""
    import sys

    from migration_support import verify_data_preservation

    assert (
        verify_data_preservation(
            ROOT,
            {k: v for k, v in protected_baseline["protected"].items() if k.startswith("scripts/")},
        )
        > 0
    )
    before = verify_protected_inventory(ROOT, protected_baseline)
    storage = EVIDENCE / "data-runs"
    previous = set(storage.iterdir()) if storage.exists() else set()
    env = dict(os.environ, KEDRO_DISABLE_TELEMETRY="yes")
    for name in ("PYTEST_DEBUG_TEMPROOT", "PYTEST_ADDOPTS"):
        env.pop(name, None)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "sat_dengue", "--pipeline=data", "--params=profile=data"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode == 0, result.stdout[-8000:] + result.stderr[-8000:]
        created = set(storage.iterdir()) - previous
        assert len(created) == 1, "Expected a unique isolated execution"
        run = created.pop()
        bundle = run / "bundle"
        manifest = json.loads((bundle / "manifest.json").read_text())
        assert manifest["real_fits"] == 0
        native_dir = ROOT / "data/interim/stage2_consolidated_dataset_pipeline"
        native = json.loads((native_dir / "execution_manifest.json").read_text())
        assert (
            manifest["provenance"]["inputs"]
            == native["input_fingerprints_before"]
            == native["input_fingerprints_after"]
        )
        comparisons = {}
        pairs = {
            "panel.csv": ROOT / "data/processed/panel_mensual_dengue_clima.csv",
            "y_history.csv": native_dir / "y_label_history_traceability.csv",
            "channel_history.csv": native_dir / "current_endemic_channel_traceability.csv",
        }
        for name, old in pairs.items():
            assert fingerprint(old) == fingerprint(bundle / name), f"Byte parity failed: {name}"
            left = pd.read_csv(old, dtype={"municipality_code": str})
            right = pd.read_csv(bundle / name, dtype={"municipality_code": str})
            compare_frames(left, right, numeric=tuple(left.select_dtypes(include="number").columns))
            comparisons[name] = {
                "rows": len(left),
                "columns": len(left.columns),
                "missingness": "exact",
                "keys_order_dtypes": "exact",
                "values": "PASS",
                "byte_exact": True,
                "original": fingerprint(old),
                "engineering": fingerprint(bundle / name),
            }
        original_contract = json.loads(
            (native_dir / "candidate_construction_contract_v1.json").read_text()
        )
        migrated_contract = json.loads((bundle / "construction.json").read_text())
        for key in original_contract:
            if key != "generated_utc":
                assert migrated_contract[key] == original_contract[key], key
        # Full individual cohort, including original dates and assignment reasons. No sampling.
        old_individual = ROOT / "data/processed/dengue_y_dengue_grave.csv"
        new_individual = run / "consolidated.csv"
        assert fingerprint(old_individual) == fingerprint(new_individual), (
            "Consolidated CSV byte identity changed"
        )
        rows = 0
        for left, right in zip(
            pd.read_csv(old_individual, dtype=str, keep_default_na=False, chunksize=200_000),
            pd.read_csv(new_individual, dtype=str, keep_default_na=False, chunksize=200_000),
            strict=True,
        ):
            compare_frames(left, right)
            rows += len(left)
        assert rows == native["reconciliation"]["consolidated_rows"] == 1755705
        panel = pd.read_csv(bundle / "panel.csv", dtype={"municipality_code": str})
        jan = panel[panel["year_month"].eq("2020-01")]
        assert len(jan) == 76 and jan["climate_days_observed"].eq(31).all()
        assert panel["year_month"].str.startswith("2013-").sum() == 76 * 12
        assert panel.loc[panel["year_month"].eq("2024-11"), "target_period_t2"].eq("2025-01").all()
        import types

        from migration_support import DATA_ORIGINALS, DATA_REVISION

        original_readiness = types.ModuleType("stage2_parity_original_readiness")
        sys.modules[original_readiness.__name__] = original_readiness
        source_name = "scripts/validate_stage2_training_readiness.py"
        source_bytes = subprocess.check_output(
            ["git", "show", f"{DATA_REVISION}:{source_name}"], cwd=ROOT
        )
        assert hashlib.sha256(source_bytes).hexdigest() == DATA_ORIGINALS[source_name]["sha256"]
        original_readiness.__file__ = str(ROOT / source_name)
        exec(compile(source_bytes, str(ROOT / source_name), "exec"), original_readiness.__dict__)
        readiness = original_readiness

        consolidated_years = pd.read_csv(
            old_individual, usecols=["ANO"], dtype=str, keep_default_na=False
        )["ANO"]
        years = pd.to_numeric(consolidated_years.str.strip(), errors="coerce").dropna().astype(int)
        expected_policy = readiness.build_model_eligibility_policy(
            int(years.min()), int(years.max())
        )
        audit = json.loads((bundle / "readiness.json").read_text())
        assert audit["policy"] == expected_policy
        eligibility = pd.read_csv(bundle / "eligibility.csv", dtype={"municipality_code": str})
        bounds = expected_policy["development_target_eligibility"]
        for h in (1, 2):
            selected = readiness.independent_select_supervised_rows(
                panel,
                h,
                target_min_period=bounds["target_min"],
                target_max_period=bounds["target_max"],
            )
            actual = eligibility.loc[
                eligibility[f"eligible_t{h}"], ["municipality_code", "year_month"]
            ]
            pd.testing.assert_frame_equal(
                actual.reset_index(drop=True),
                selected[["municipality_code", "year_month"]].reset_index(drop=True),
            )
            assert audit["eligible_rows"][f"t{h}"] == len(selected) > 0
            target = panel[f"target_period_t{h}"]
            reasons = panel[f"y_status_t{h}"].astype("string").copy()
            allowed = target.between(bounds["target_min"], bounds["target_max"])
            reasons.loc[allowed & panel[f"y_evaluable_t{h}"]] = "eligible"
            reasons.loc[target < bounds["target_min"]] = "before_backed_history"
            reasons.loc[target > bounds["target_max"]] = "outside_development_target"
            pd.testing.assert_series_equal(
                eligibility[f"exclusion_reason_t{h}"].astype("string"), reasons, check_names=False
            )
            for endpoint in readiness.TEMPORAL_WINDOW_TRAIN_ENDPOINTS:
                cohort = readiness.independent_select_supervised_rows(
                    panel,
                    h,
                    target_min_period=bounds["target_min"],
                    target_max_period=min(bounds["target_max"], endpoint),
                    reference_max_period=endpoint,
                )
                keys = eligibility.loc[
                    eligibility[f"eligible_t{h}"]
                    & panel["year_month"].le(endpoint)
                    & target.le(endpoint),
                    ["municipality_code", "year_month"],
                ]
                pd.testing.assert_frame_equal(
                    keys.reset_index(drop=True),
                    cohort[["municipality_code", "year_month"]].reset_index(drop=True),
                )
            assert (
                eligibility.loc[~eligibility[f"eligible_t{h}"], f"exclusion_reason_t{h}"]
                .notna()
                .all()
            )
        summary = json.loads((bundle / "summary.json").read_text())
        assert summary["source_rows"] == native["reconciliation"]["source_rows"]
        assert summary["climate"] == native["climate_daily_summary"]
        assert summary["targets"] == {
            k: v for k, v in native["target_labeling"].items() if k != "retrospective_assumption"
        }
        assert summary["channel"] == {
            k: v
            for k, v in native["current_endemic_channel"].items()
            if k != "retrospective_assumption"
        }
        for key, value in summary["reconciliation"].items():
            assert native["reconciliation"][key] == value
        for name, record in manifest["files"].items():
            assert fingerprint(bundle / name) == record
        comparisons["consolidated.csv"] = {
            "rows": rows,
            "columns": len(original_contract["datasets"]["dengue_y_dengue_grave"]["schema"]),
            "comparison": "byte-exact and all ordered chunks",
            "original": fingerprint(old_individual),
            "engineering": fingerprint(new_individual),
        }
        del sys.modules[original_readiness.__name__]
        report = {
            "status": "PASS",
            "run_id": run.name,
            "bundle_id": manifest["bundle_id"],
            "comparisons": comparisons,
            "eligibility": audit,
            "January_2020": "76 municipalities / 31 days",
            "2013": "complete cohort and all original individual date bytes",
            "cross_year": "complete November 2024 to January 2025 cohort",
            "provenance": "exact original source identities; separate engineering outputs",
            "real_fits": 0,
        }
        (run / "parity.json").write_text(json.dumps(report, indent=2) + "\n")
    finally:
        after = verify_protected_inventory(ROOT, protected_baseline)
        assert before == after


@pytest.mark.migration_evidence
def test_data_extracted_scientific_functions_match_protected_originals() -> None:
    """Source equivalence prevents a style rewrite hidden behind successful examples."""
    import ast

    from migration_support import DATA_ORIGINALS, DATA_REVISION

    count = 0
    for relative, destination in [
        ("scripts/stage2_consolidated_dataset_pipeline.py", "src/sat_dengue/data/consolidation.py"),
        ("scripts/validate_stage2_training_readiness.py", "src/sat_dengue/data/readiness.py"),
    ]:
        raw = subprocess.check_output(["git", "show", f"{DATA_REVISION}:{relative}"], cwd=ROOT)
        assert hashlib.sha256(raw).hexdigest() == DATA_ORIGINALS[relative]["sha256"]
        old = {
            n.name: n for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        }
        new = {
            n.name: n
            for n in ast.parse((ROOT / destination).read_text()).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        }
        for name in set(old) & set(new) - {"compute_schema_contract"}:
            assert ast.dump(old[name]) == ast.dump(new[name]), name
            count += 1
    assert count >= 35


@pytest.mark.migration_evidence
def test_preparation_kedro_complete_cohorts_and_saved_replay(protected_baseline: dict) -> None:
    """Compare every development row, eight cohorts and all saved state/matrix bytes."""
    import ast
    import inspect
    import sys

    from sat_dengue.datasets.legacy_preparation.pipeline import read_panel
    from sat_dengue.datasets.preparation import DEVELOPMENT, TEMPORAL
    from sat_dengue.training_preparation import eligibility as eligibility_domain
    from sat_dengue.training_preparation import features as feature_domain
    from sat_dengue.training_preparation import preprocessing as prep_domain
    from sat_dengue.training_preparation import validation as validation_domain
    from sat_dengue.training_preparation.features import derive_features

    equivalent = []
    for old_name, module, names in (
        ("features", feature_domain, ["calendar_lookup", "derive_features"]),
        (
            "preprocessing",
            prep_domain,
            [
                "PreparerSpec",
                "runtime_versions",
                "_check_numeric",
                "_category_values",
                "fit_preparer",
            ],
        ),
        ("eligibility", eligibility_domain, ["build_controls", "policy_from_years"]),
        (
            "validation",
            validation_domain,
            [
                "validate_roles",
                "validate_schema",
                "validate_panel",
                "validate_monthly_support",
                "validate_counts",
                "validate_climate_coverage",
                "validate_target_metadata",
            ],
        ),
    ):
        original_source = subprocess.check_output(
            [
                "git",
                "show",
                f"925a784eb20d082efd7e166ab1b6fa35c8505a57:scripts/training_preparation/{old_name}.py",
            ],
            cwd=ROOT,
            text=True,
        )
        definitions = {
            n.name: n
            for n in ast.parse(original_source).body
            if isinstance(n, (ast.FunctionDef, ast.ClassDef))
        }
        for name in names:
            current = ast.parse(inspect.getsource(getattr(module, name))).body[0]
            assert ast.dump(current, include_attributes=False) == ast.dump(
                definitions[name], include_attributes=False
            ), name
            equivalent.append(f"{old_name}.{name}")
    before = verify_protected_inventory(ROOT, protected_baseline)
    storage = EVIDENCE / "preparation-runs"
    previous = set(storage.iterdir()) if storage.exists() else set()
    env = dict(os.environ, KEDRO_DISABLE_TELEMETRY="yes", PYTHONDONTWRITEBYTECODE="1")
    for name in ("PYTEST_DEBUG_TEMPROOT", "PYTEST_ADDOPTS"):
        env.pop(name, None)
    result = subprocess.run(
        [sys.executable, "tests/integration/preparation_cli.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    evidence = ROOT / ".dwp/plans/PLAN_030_kedro_architecture_migration/analysis_results/session4"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "kedro-no-fit.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout[-6000:] + result.stderr[-6000:]
    created = set(storage.iterdir()) - previous
    assert len(created) == 1
    bundle = created.pop()
    manifest = verify_native_bundle(bundle)
    assert manifest["schema"] == "sat-dengue-preparation-engineering-v1"
    assert manifest["real_model_fits"] == manifest["real_preparer_refits"] == 0
    dev = verify_native_bundle(ROOT / DEVELOPMENT)
    temporal = verify_native_bundle(ROOT / TEMPORAL)
    compared = {}
    # Byte equality covers every ordered value and missingness cell across the full cohorts.
    for relative, original in ((DEVELOPMENT, dev), (TEMPORAL, temporal)):
        for name, record in original["files"].items():
            assert fingerprint(bundle / name) == record, name
            assert (bundle / name).read_bytes() == (ROOT / relative / name).read_bytes(), name
            compared[name] = record
    schema = json.loads((bundle / "schema.json").read_text())
    assert schema["features"] == dev["roles"]["features"]
    assert schema["raw_X"] == temporal["raw_X_columns"]
    assert len(schema["features"]) == 28 and len(schema["raw_X"]) == 29
    provenance = json.loads((bundle / "provenance.json").read_text())
    assert provenance["eligibility"] == dev["eligibility_audit"]
    assert provenance["G5"] == "NOT_APPROVED" and provenance["champion"] == "not_selected"
    assert provenance["windows"] == {
        w: {k: v for k, v in entry.items() if k != "profiles"}
        for w, entry in temporal["windows"].items()
    }
    contract = json.loads(
        (ROOT / "docs/product/stage-3/training_preparation_contract_v1.json").read_text()
    )
    panel = read_panel(ROOT / contract["panel_path"], contract, reference_end="2024-12")
    rebuilt = derive_features(panel, contract).drop(columns=["municipality_code", "year_month"])
    assert {n: str(d) for n, d in rebuilt.dtypes.items()} == schema["dtypes"]
    assert len(rebuilt) == 16948
    windows = []
    for window, entry in temporal["windows"].items():
        for split in ("train", "validation"):
            controls = pd.read_csv(bundle / f"{window}_{split}_controls.csv", dtype="string")
            index = pd.read_csv(bundle / f"{window}_{split}_index.csv", dtype="string")
            pd.testing.assert_frame_equal(controls[list(index)], index)
            assert controls[f"target_period_t{entry['horizon']}"].lt("2025-01").all()
        for profile in ("native", "onehot_standard"):
            from sat_dengue.datasets.legacy_preparation.temporal import load_prepared_window

            # Both loaders restore saved categorical order and compare complete matrices/Y/keys.
            for split in ("train", "validation"):
                new = load_prepared_window(ROOT / TEMPORAL, window, profile, split)
                state = json.loads((bundle / f"{window}_{profile}_preparer.json").read_text())
                assert state == new[3]
                matrix = pd.read_csv(
                    bundle / f"{window}_{profile}_{split}_matrix.csv", float_precision="round_trip"
                )
                if profile == "native":
                    for name, categories in state["categories"].items():
                        matrix[name] = pd.Categorical(
                            matrix[name].astype("string"), categories=categories
                        )
                pd.testing.assert_frame_equal(matrix, new[0], check_exact=True)
                assert len(matrix.columns) == (29 if profile == "native" else 114)
        windows.append(
            {
                k: entry[k]
                for k in (
                    "cutoff",
                    "horizon",
                    "train_rows",
                    "validation_rows",
                    "train",
                    "validation",
                )
            }
        )
    after = verify_protected_inventory(ROOT, protected_baseline)
    assert before == after
    (evidence / "complete-parity.json").write_text(
        json.dumps(
            {
                "engineering_bundle": str(bundle.relative_to(ROOT)),
                "manifest": fingerprint(bundle / "manifest.json"),
                "original_development": DEVELOPMENT,
                "original_temporal": TEMPORAL,
                "complete_compared_payloads": compared,
                "ast_identical_scientific_definitions": equivalent,
                "windows": windows,
                "development_rows": 16948,
                "real_model_fits": 0,
                "real_preparer_refits": 0,
                "before": before,
                "after": after,
            },
            indent=2,
        )
        + "\n"
    )


@pytest.mark.parametrize("mutation", ["extra", "original", "engineering", "revision"])
def test_preparation_baseline_closed_mapping_rejects_drift(mutation: str) -> None:
    from copy import deepcopy
    from tempfile import TemporaryDirectory

    from migration_support import PREPARATION_MAPPING, verify_preparation_preservation

    mapping = deepcopy(PREPARATION_MAPPING)
    records = {n: e["original"] for n, e in mapping["files"].items()}
    name = next(iter(mapping["files"]))
    if mutation == "extra":
        mapping["files"]["scripts/unapproved.py"] = mapping["files"][name]
    elif mutation == "revision":
        mapping["original_revision"] = "0" * 40
    else:
        mapping["files"][name][mutation]["sha256"] = "0" * 64
    with TemporaryDirectory(dir=ROOT / "tmp", prefix="preparation-mapping-") as directory:
        root = Path(directory)
        path = root / "docs/operations/kedro-preparation-identities.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(mapping))
        with pytest.raises(AssertionError, match="Closed preparation mapping"):
            verify_preparation_preservation(root, records)
