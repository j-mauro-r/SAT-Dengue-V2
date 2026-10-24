"""Pure preparation errors and predictor allowlist."""

from typing import Any


class PreparationError(ValueError):
    """An input violates the preparation contract; no repair is attempted."""


def validate_predictors(columns: list[str], contract: dict[str, Any]) -> None:
    """Reject labels, controls and undeclared predictors using an allowlist.

    Args:
        columns: Proposed predictor names.
        contract: Preparation contract.

    Raises:
        PreparationError: If a predictor is duplicated or not explicitly allowed.
    """
    forbidden = sorted(set(columns) - set(contract["roles"]["predictors"]))
    if forbidden or len(columns) != len(set(columns)):
        raise PreparationError(f"Forbidden or duplicate predictor columns: {forbidden}")
