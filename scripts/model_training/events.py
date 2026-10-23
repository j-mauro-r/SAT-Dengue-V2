"""Compatibility import adapter; retire after consumers migrate in T-cleanup."""

import importlib
from typing import Any

_implementation = importlib.import_module("sat_dengue.datasets.legacy_training.events")


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)
