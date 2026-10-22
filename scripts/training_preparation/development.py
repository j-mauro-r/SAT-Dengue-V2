"""Compatibility import adapter; retire after consumers migrate in T-cleanup."""

import importlib
import sys
from typing import Any

_implementation = importlib.import_module("sat_dengue.datasets.legacy_preparation.development")


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)


if __name__ == "__main__":
    from sat_dengue.datasets.preparation import compatibility_main

    compatibility_main()
else:
    sys.modules[__name__] = _implementation
