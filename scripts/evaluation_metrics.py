"""Compatibility metric imports; the single owner is sat_dengue.metrics."""

from typing import Any

from sat_dengue import metrics as _implementation


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)
