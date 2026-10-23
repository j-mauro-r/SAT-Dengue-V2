"""Compatibility import adapter; retire after consumers migrate in T-cleanup."""

import importlib
from typing import Any

_implementation = importlib.import_module("sat_dengue.model_training.references")


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)
