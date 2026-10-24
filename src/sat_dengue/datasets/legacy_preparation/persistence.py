"""Publish immutable feature bundles with explicit reuse checks and atomic visibility."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Literal

from sat_dengue.training_preparation.serialization import bytes_record as bytes_record
from sat_dengue.training_preparation.serialization import json_bytes as json_bytes

from .contract import PreparationError


def verify_bundle(directory: Path, payloads: dict[str, bytes]) -> None:
    """Require the exact expected file set and bytes before any artifact reuse.

    Args:
        directory: Immutable published bundle.
        payloads: Recomputed outputs for the current identity.

    Raises:
        PreparationError: If any file is missing, different or unexpected.
    """
    if (
        directory.is_symlink()
        or not directory.is_dir()
        or set(p.name for p in directory.iterdir()) != set(payloads)
    ):
        raise PreparationError("Existing bundle has missing or unexpected files")
    for name, payload in payloads.items():
        path = directory / name
        if path.is_symlink() or not path.is_file() or path.read_bytes() != payload:
            raise PreparationError(f"Existing bundle is stale or corrupted: {name}")


def publish_bundle(
    base: Path,
    identity: str,
    payloads: dict[str, bytes],
    *,
    existing_policy: Literal["error", "reuse_identical"] = "reuse_identical",
) -> Path:
    """Stage, fsync and atomically publish a new identity directory.

    Args:
        base: Dedicated output root, already constrained to repository scope.
        identity: SHA-256 identity directory name.
        payloads: All artifact bytes, including manifest.json.
        existing_policy: Refuse existing output or reuse only identical recomputed bytes.

    Returns:
        Bundle directory; existing artifacts are never replaced.

    Raises:
        PreparationError: If naming, policy, locking or existing bytes are unsafe.
    """
    if (
        len(identity) != 64
        or any(c not in "0123456789abcdef" for c in identity)
        or any(Path(n).name != n for n in payloads)
        or existing_policy not in ("error", "reuse_identical")
    ):
        raise PreparationError("Invalid artifact identity, filename or replacement policy")
    base.mkdir(parents=True, exist_ok=True)
    lock = base / ".publish.lock"
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PreparationError("Another publisher holds the output lock; no overwrite") from exc
    try:
        os.close(lock_fd)
        target = base / identity
        if target.exists():
            if existing_policy == "error":
                raise PreparationError("Output already exists; replacement is forbidden")
            verify_bundle(target, payloads)
            return target
        with tempfile.TemporaryDirectory(prefix=".staging-", dir=base) as staging:
            stage = Path(staging)
            for name, payload in payloads.items():
                with (stage / name).open("xb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
            os.rename(stage, target)
        return target
    finally:
        lock.unlink()
