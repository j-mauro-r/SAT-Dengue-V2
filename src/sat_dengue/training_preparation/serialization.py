"""Deterministic in-memory table and JSON serialization."""

import hashlib
import json
from typing import Any

import pandas as pd  # type: ignore[import-untyped]


def json_bytes(value: dict[str, Any]) -> bytes:
    """Serialize reproducible JSON bytes.

    Args:
        value: JSON-compatible object.

    Returns:
        Sorted UTF-8 JSON without wall-clock or personal-path metadata.
    """
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def bytes_record(payload: bytes) -> dict[str, Any]:
    """Identify a payload by SHA-256 and size.

    Args:
        payload: Serialized artifact.

    Returns:
        Hash and byte length.
    """
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def serialize_table(frame: pd.DataFrame) -> bytes:
    """Serialize table bytes deterministically without inventing missing values.

    Args:
        frame: Ordered table with explicit roles and sorted rows.

    Returns:
        UTF-8 CSV with stable float formatting and empty missing cells.
    """
    return frame.to_csv(index=False, na_rep="", lineterminator="\n", float_format="%.17g").encode()
