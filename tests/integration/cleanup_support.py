"""Verify the separate, explicitly authorized cleanup correspondence without repairs."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

CEILING_SHA256 = "a1ee1c0a09507957bb884ab0e0a0da98dc7266c4efa76f15cad4bb2fd9c82037"
PRE_CLEANUP = "861b36966cec26d1d2b36edee4d6ada6d5bc0930"
BASELINE_REVISION = "89d538c93ff20824c96c7fe0929baaa9d900e999"
MAPPING = "docs/operations/kedro-cleanup-identities.json"


def byte_record(raw: bytes) -> dict[str, Any]:
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def git_record(root: Path, revision: str, name: str) -> dict[str, Any]:
    assert revision in {PRE_CLEANUP, BASELINE_REVISION}
    path = Path(name)
    assert not path.is_absolute() and ".." not in path.parts
    raw = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=root)
    oid = subprocess.check_output(
        ["git", "rev-parse", f"{revision}:{name}"], cwd=root, text=True
    ).strip()
    return {"revision": revision, "path": name, "blob": oid, **byte_record(raw)}


def load_cleanup(root: Path) -> dict[str, Any] | None:
    path = root / MAPPING
    if not path.exists():
        return None
    assert not path.is_symlink()
    value: dict[str, Any] = json.loads(path.read_text())
    assert value["schema"] == "kedro-cleanup-preservation-v1"
    assert value["task_id"] == "T-cleanup"
    assert value["authorization"]["authority"] == "Mauricio"
    assert value["authorization"]["ceiling_sha256"] == CEILING_SHA256
    raw = (json.dumps(value["ceiling"], indent=2, sort_keys=True) + "\n").encode()
    assert hashlib.sha256(raw).hexdigest() == CEILING_SHA256, "Cleanup ceiling changed"
    ceiling = {r["path"]: r for r in value["ceiling"]["paths"]}
    assert len(ceiling) == 67 and set(value["files"]) == set(ceiling)
    assert value["pre_cleanup_revision"] == PRE_CLEANUP
    for name, row in value["files"].items():
        assert row["original"] == ceiling[name]["baseline_original"]
        assert {k: row["pre_cleanup_git"][k] for k in ("bytes", "sha256")} == ceiling[name][
            "current"
        ]
    return value


def verify_cleanup(root: Path) -> None:
    """Check original/pre-cleanup Git blobs AND actual final presence/identity."""
    value = load_cleanup(root)
    if value is None:
        return
    for name, row in value["files"].items():
        assert git_record(root, BASELINE_REVISION, name) == row["original_git"]
        assert git_record(root, PRE_CLEANUP, name) == row["pre_cleanup_git"]
        assert {k: row["original_git"][k] for k in ("bytes", "sha256")} == row["original"]
        path = root / name
        assert not path.is_symlink()
        assert row["owner"] and row["reason"] and row["retirement_condition"]
        assert row["disposition"] in {"KEEP", "ADAPT", "RETIRE"}
        if row["disposition"] == "RETIRE":
            assert not path.exists(), f"Retired path reappeared: {name}"
            assert row["final"] == {"present": False}
        else:
            assert path.is_file(), f"Kept/adapted path missing: {name}"
            assert row["final"] == {"present": True, **byte_record(path.read_bytes())}
            if row["disposition"] == "KEEP":
                assert byte_record(path.read_bytes()) == {
                    k: row["pre_cleanup_git"][k] for k in ("bytes", "sha256")
                }
        assert row["replacement"]
        assert all((root / target).is_file() for target in row["replacement"])


def previous_engineering(root: Path, name: str) -> dict[str, Any]:
    """Earlier closed mappings still verify their exact pre-cleanup bytes."""
    value = load_cleanup(root)
    if value is not None and name in value["files"]:
        row = value["files"][name]
        actual = git_record(root, PRE_CLEANUP, name)
        assert actual == row["pre_cleanup_git"]
        return {key: actual[key] for key in ("bytes", "sha256")}
    path = root / name
    assert path.is_file() and not path.is_symlink()
    return byte_record(path.read_bytes())


def verify_cleanup_originals(root: Path, records: dict[str, Any]) -> int:
    """Unmapped originals stay on disk, except exact authorized retired sources."""
    value = load_cleanup(root)
    files = value["files"] if value else {}
    assert records
    for name, expected in records.items():
        if name in files:
            row = files[name]
            assert expected == row["original"]
            actual = git_record(root, BASELINE_REVISION, name)
            assert actual == row["original_git"]
            assert {key: actual[key] for key in ("bytes", "sha256")} == expected
        else:
            path = root / name
            assert path.is_file() and not path.is_symlink()
            assert byte_record(path.read_bytes()) == expected, name
    return len(records)
