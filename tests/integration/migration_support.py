"""Strict, read-only comparators shared by synthetic CI and protected replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

RTOL = 1e-8
ATOL = 1e-10
BASELINE_SHA256 = "d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3"
SCOPE_SHA256 = "5f16db6458a771fd2ee32197247b3331ecd5f57b148319e7ba99ba806cc9165f"
FINAL_ID = "768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35"
FINAL_PATH = Path("artifacts/model_final_evaluation") / FINAL_ID


def fingerprint(path: Path) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise AssertionError(f"Required regular evidence file missing or symlinked: {path.name}")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"sha256": digest, "bytes": path.stat().st_size}


def safe_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise AssertionError("Unsafe evidence path")
    resolved = root / path
    if not resolved.resolve().is_relative_to(root.resolve()):
        raise AssertionError("Evidence escapes repository")
    return resolved


def require_records(root: Path, records: dict[str, Any]) -> int:
    if not records:
        raise AssertionError("Zero eligible evidence records")
    for relative, expected in records.items():
        if fingerprint(safe_path(root, relative)) != expected:
            raise AssertionError(f"Protected fingerprint mismatch: {relative}")
    return len(records)


def verify_native_bundle(bundle: Path) -> dict[str, Any]:
    manifest = json.loads((bundle / "manifest.json").read_text())
    files = manifest.get("files", {})
    require_records(bundle, files)
    if {p.name for p in bundle.iterdir()} != {*files, "manifest.json"}:
        raise AssertionError("Unexpected native bundle payload set")
    return manifest


def approved_scope(root: Path) -> dict[str, Any]:
    """Pinned implementation of Mauricio's PLAN_030 revision-2 exception boundary."""
    path = root / "docs/operations/kedro-baseline-scope.json"
    assert fingerprint(path)["sha256"] == SCOPE_SHA256, "Approved scope changed"
    return json.loads(path.read_text())


def source_records(identity: dict[str, Any]) -> set[tuple[str, str]]:
    return {
        (path, record["sha256"])
        for group in ("code", "stage4_code")
        for path, record in identity.get(group, {}).items()
        if isinstance(record, dict) and "sha256" in record
    }


def active_chain(root: Path, baseline: dict[str, Any], final: str) -> set[str]:
    """Derive dependencies from protected native identities, not coverage receipts."""
    records = {name: baseline["protected"][name] for name in baseline["bundles"]}
    require_records(root, records)
    index = {record["sha256"]: name for name, record in records.items()}
    assert len(index) == len(records), "Ambiguous manifest identity"
    visited: set[str] = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        assert name in records, "Unknown dependency manifest"
        visited.add(name)
        identity = json.loads(safe_path(root, name).read_text()).get("identity", {})

        def dependencies(value: Any) -> None:
            if isinstance(value, dict):
                sha = value.get("sha256")
                if isinstance(sha, str) and sha in index:
                    visit(index[sha])
                for child in value.values():
                    dependencies(child)
            elif isinstance(value, list):
                for child in value:
                    dependencies(child)

        dependencies(identity)

    visit(final)
    return visited


def verify_source_scope(
    root: Path,
    baseline: dict[str, Any],
    recovered: set[tuple[str, str]],
    scope: dict[str, Any],
    coverage: dict[str, Any],
    *,
    final: str = str(FINAL_PATH / "manifest.json"),
) -> dict[str, Any]:
    chain = active_chain(root, baseline, final)
    assert sorted(chain) == scope["active_chain"], "Active dependency chain changed"
    by_bundle = {
        name: source_records(json.loads(safe_path(root, name).read_text()).get("identity", {}))
        for name in baseline["bundles"]
    }
    required = set().union(*by_bundle.values())
    active_required = set().union(*(by_bundle[name] for name in chain))
    assert active_required, "Zero eligible active source comparisons"
    assert not active_required - recovered, "Missing active source"
    missing = required - recovered
    exceptions = {(r["path"], r["sha256"]) for r in scope["historical_only_missing"]}
    assert len(exceptions) == len(scope["historical_only_missing"]), "Duplicate exception"
    assert missing == exceptions, "Closed historical source exceptions changed"
    affected = {name for name, records in by_bundle.items() if records & exceptions}
    assert affected == set(scope["historical_bundles"]), "Affected historical bundles changed"
    assert not affected & chain, "Unverified historical bundle used for equivalence"
    for name in affected:
        assert scope["historical_bundles"][name] == {
            "action": "KEEP",
            "source_status": "UNVERIFIED",
            "equivalence_evidence": False,
            "modification_allowed": False,
            "manifest": baseline["protected"][name],
        }, "Historical bundle must remain immutable KEEP / UNVERIFIED"
    observed = {
        "active_chain": sorted(chain),
        "active_missing": [],
        "historical_only_missing": [{"path": p, "sha256": s} for p, s in sorted(missing)],
    }
    assert coverage == observed, "Source coverage receipt disagrees with reconstructed evidence"
    assert scope["active_missing"] == [], "Approved active_missing must remain empty"
    verify_equivalence_scope(scope, {**scope, "equivalence_bundles": sorted(chain)})
    return observed


def verify_equivalence_scope(scope: dict[str, Any], report: dict[str, Any]) -> None:
    assert report["equivalence_bundles"] == scope["active_chain"], (
        "Equivalence must use exactly the approved active chain"
    )
    assert report["full_historical_reproducibility"] is False, (
        "Full historical reproducibility cannot be claimed"
    )
    assert report["G5"] == "NOT_APPROVED" and report["champion"] == "not_selected"
    assert report["consumed_2025"] is True
    assert report["allow_2025_selection_tuning_training"] is False
    assert report["new_real_fits"] == 0


def verify_protected_inventory(root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    """Independent disk scan: catches rename/unlink/native writes beyond open hooks."""
    records = baseline["protected"]
    count = require_records(root, records)
    for name, original in baseline["bundles"].items():
        bundle = safe_path(root, name).parent
        prefix = str(Path(name).parent) + "/"
        expected = {p.removeprefix(prefix) for p in records if p.startswith(prefix)}
        expected_entries = expected | {
            str(parent) for path in expected for parent in Path(path).parents if parent != Path(".")
        }
        entries = list(bundle.rglob("*"))
        assert not bundle.is_symlink() and not any(p.is_symlink() for p in entries)
        assert {str(p.relative_to(bundle)) for p in entries} == expected_entries, (
            f"Protected bundle membership changed: {name}"
        )
        manifest = json.loads(safe_path(root, name).read_text())
        assert manifest["bundle_id"] == original["bundle_id"], "Bundle identity changed"
        assert fingerprint(safe_path(root, name)) == original["manifest"], (
            "Protected manifest identity changed"
        )
    return {
        "status": "PASS",
        "protected_files": count,
        "protected_bytes": sum(r["bytes"] for r in records.values()),
        "bundles": len(baseline["bundles"]),
        "baseline_sha256": BASELINE_SHA256,
        "method": "independent post-replay disk size/SHA-256 and bundle membership/identity scan",
    }


def compare_frames(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    numeric: tuple[str, ...] = (),
    exact_numeric: bool = False,
) -> None:
    """Require the full ordered cohort and masks; only declared floats use tolerance."""
    if expected.empty or actual.empty:
        raise AssertionError("Zero eligible comparison rows")
    pd.testing.assert_index_equal(expected.index, actual.index, exact=True)
    pd.testing.assert_index_equal(expected.columns, actual.columns, exact=True)
    if not set(numeric).issubset(expected.columns):
        raise AssertionError("Unknown numeric comparison column")
    pd.testing.assert_frame_equal(expected.isna(), actual.isna(), check_exact=True)
    for name in expected.columns:
        if name in numeric:
            left = expected[name].to_numpy(dtype=float, na_value=np.nan)
            right = actual[name].to_numpy(dtype=float, na_value=np.nan)
            if np.isinf(left).any() or np.isinf(right).any():
                raise AssertionError("Infinite numeric evidence")
            np.testing.assert_allclose(
                right,
                left,
                rtol=0 if exact_numeric else RTOL,
                atol=0 if exact_numeric else ATOL,
                equal_nan=True,
            )
        else:
            pd.testing.assert_series_equal(expected[name], actual[name], check_exact=True)
