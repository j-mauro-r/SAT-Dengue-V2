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
