"""Compatibility import adapter; retire after consumers migrate in T-cleanup."""

import importlib
import sys
from typing import Any

_implementation = importlib.import_module("sat_dengue.datasets.legacy_preparation.pipeline")


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)


sys.modules[__name__] = _implementation
