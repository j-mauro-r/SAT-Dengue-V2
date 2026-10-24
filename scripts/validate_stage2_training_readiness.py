"""Compatibility import/CLI adapter; retire after consumers move in T-cleanup."""

from typing import Any

import sat_dengue.datasets.legacy_readiness as _implementation


def __getattr__(name: str) -> Any:
    return getattr(_implementation, name)


if __name__ == "__main__":
    raise SystemExit(_implementation.main())
