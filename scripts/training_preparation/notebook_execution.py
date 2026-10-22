"""Compatibility import adapter; retire after consumers migrate in T-cleanup."""

import importlib
import sys
from typing import Any

_implementation = importlib.import_module(
    "sat_dengue.datasets.legacy_preparation.notebook_execution"
)


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)


if __name__ == "__main__":
    _implementation.main()
else:
    sys.modules[__name__] = _implementation
