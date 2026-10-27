"""Synthetic rejection tests for preparation boundaries; no private inputs required."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

# Milestone 2: exact calendar antecedents and publication boundaries.
from sat_dengue.datasets.legacy_preparation.contract import (
    CONTRACT_PATH,
    read_json,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def contract() -> dict[str, Any]:
    return read_json(ROOT / CONTRACT_PATH)
