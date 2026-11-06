"""Validate native scientific artifact shapes against the public artifact catalogue."""

from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd  # type: ignore[import-untyped]


def validate_payloads(payloads: dict[str, bytes], catalogue: dict[str, Any]) -> None:
    schemas = catalogue["schemas"]
    for name, raw in payloads.items():
        if name.endswith(".ubj"):
            metadata_name = name.removesuffix(".ubj") + ".json"
            if metadata_name not in payloads or not raw:
                raise ValueError("Missing native model metadata")
            continue
        if name.endswith(".csv"):
            kind = "cohort" if name.endswith(".cohort.csv") else "predictions"
            schema = schemas[f"exp-delta03-{kind}-v1"]
            columns = list(pd.read_csv(io.BytesIO(raw), nrows=0))
            if len(set(columns)) != len(columns) or not set(schema["columns"]) <= set(columns):
                raise ValueError("Protected table schema mismatch")
            continue
        value = json.loads(raw)
        schema = schemas.get(value.get("schema"))
        if schema is None or not set(schema["required"]) <= set(value):
            raise ValueError("Unknown or incomplete native artifact schema")
