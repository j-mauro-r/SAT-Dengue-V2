"""Read-only loader for the Stage 7 demonstrative response fixture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from pydantic import ValidationError

from .schemas import DashboardResponse, DepartmentCode

FIXTURES_DIRECTORY = Path(__file__).resolve().parent / "fixtures"
META_FIXTURE_PATH = FIXTURES_DIRECTORY / "dashboard_meta.json"
TOLIMA_FIXTURE_PATH = FIXTURES_DIRECTORY / "dashboard_tolima.json"
DEMONSTRATIVE_FIXTURE_PATHS: dict[DepartmentCode, Path] = {
    "50": META_FIXTURE_PATH,
    "73": TOLIMA_FIXTURE_PATH,
}


class FixtureValidationError(ValueError):
    """The demonstrative fixture cannot be read or violates the contract."""


def resolve_demonstrative_fixture_path(department_code: str) -> Path:
    """Resolve the runtime-owned demonstrative fixture for a department.

    Args:
        department_code: Supported two-digit DANE department code.

    Returns:
        Absolute path to the department's demonstrative response fixture.

    Raises:
        FixtureValidationError: If no demonstrative fixture exists for the code.
    """
    path = DEMONSTRATIVE_FIXTURE_PATHS.get(cast(DepartmentCode, department_code))
    if path is None:
        raise FixtureValidationError(
            f"Unsupported demonstrative department code: {department_code}"
        )
    return path


def load_dashboard_fixture(path: Path) -> DashboardResponse:
    """Load and validate a demonstrative dashboard response without modifying it.

    Args:
        path: JSON fixture to read.

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


def load_demonstrative_fixture(department_code: str) -> DashboardResponse:
    """Resolve, load, and validate one department's demonstrative fixture.

    Args:
        department_code: Supported two-digit DANE department code.

    Returns:
        A typed, contract-valid demonstrative dashboard response.

    Raises:
        FixtureValidationError: If the code is unsupported or its fixture is invalid.
    """
    return load_dashboard_fixture(resolve_demonstrative_fixture_path(department_code))
