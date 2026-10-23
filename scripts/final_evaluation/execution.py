"""Compatibility import adapter; retain observed consumers until T-cleanup."""

import importlib
from typing import Any

_implementation = importlib.import_module(
    "sat_dengue.datasets.legacy_evaluation.final_evaluation.execution"
)


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)


if __name__ == "__main__":
    _implementation.main()
