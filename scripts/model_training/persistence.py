"""Deterministic serialization and immutable publication for Stage 4 artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from scripts.training_preparation.development import serialize_table
from scripts.training_preparation.persistence import (
    bytes_record,
    json_bytes,
    publish_bundle,
    verify_bundle,
)


def publish_artifacts(
    base: Path,
    identity: str,
    payloads: dict[str, bytes],
    *,
    existing_policy: Literal["error", "reuse_identical"] = "reuse_identical",
) -> Path:
    """Publish immutable Stage 4 artifacts under a content-addressed identity.

    Args:
        base: Artifact base directory.
        identity: 64-hex bundle identifier.
        payloads: Serialized artifact bytes.
        existing_policy: Existing-output handling policy.

    Returns:
        Published bundle path.
    """
    return publish_bundle(base, identity, payloads, existing_policy=existing_policy)


def verify_artifacts(bundle: Path, payloads: dict[str, bytes]) -> None:
    """Verify an existing immutable bundle matches recomputed bytes.

    Args:
        bundle: Existing bundle path.
        payloads: Recomputed payloads.
    """
    verify_bundle(bundle, payloads)


__all__ = [
    "bytes_record",
    "json_bytes",
    "publish_artifacts",
    "serialize_table",
    "verify_artifacts",
]
