"""Read-only loader for the Stage 7 demonstrative response fixture."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from .schemas import DashboardResponse

DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "tests/fixtures/stage7/dashboard_tolima.json"
)


class FixtureValidationError(ValueError):
    """The demonstrative fixture cannot be read or violates the contract."""


def load_dashboard_fixture(path: Path = DEFAULT_FIXTURE_PATH) -> DashboardResponse:
    """Load and validate a demonstrative dashboard response without modifying it.

    Args:
        path: JSON fixture to read. Defaults to the versioned Tolima fixture.

    Returns:
        A typed, contract-valid dashboard response.

    Raises:
        FixtureValidationError: If the file cannot be read, is not valid JSON, or
            contradicts the executable Product Contract.
    """
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return DashboardResponse.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise FixtureValidationError(f"Invalid dashboard fixture {path}: {error}") from error
