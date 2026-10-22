"""Read-only persistence boundary for validated dashboard results."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Protocol

from .errors import InvalidPersistedResultError
from .loader import META_FIXTURE_PATH, TOLIMA_FIXTURE_PATH, FixtureValidationError
from .loader import load_dashboard_fixture as load_persisted_result
from .schemas import DashboardResponse

ResultKey = tuple[str, str]

DEMONSTRATIVE_RESULT_PATHS: Mapping[ResultKey, Path] = MappingProxyType(
    {
        ("50", "2026-12"): META_FIXTURE_PATH,
        ("73", "2026-09"): TOLIMA_FIXTURE_PATH,
    }
)


class DashboardResultRepository(Protocol):
    """Retrieve one persisted dashboard response without modifying storage."""

    def get(self, department_code: str, period: str) -> DashboardResponse | None:
        """Return the exact persisted response for a query, if present."""


class JsonDashboardResultRepository:
    """Read and validate dashboard responses indexed by department and period."""

    def __init__(self, result_paths: Mapping[ResultKey, Path]) -> None:
        """Create a repository from an immutable copy of the result index.

        Args:
            result_paths: Mapping from ``(department_code, reference_period)``
                to a persisted JSON response.
        """
        self._result_paths = MappingProxyType(dict(result_paths))

    def get(self, department_code: str, period: str) -> DashboardResponse | None:
        """Load the exact persisted result for a department-period query.

        Args:
            department_code: Contracted two-digit department code.
            period: Contracted reference month in ``YYYY-MM`` format.

        Returns:
            A validated response, or ``None`` when the exact key is absent.

        Raises:
            InvalidPersistedResultError: If the indexed file cannot be read,
                violates the schema, or contradicts its repository key.
        """
        path = self._result_paths.get((department_code, period))
        if path is None:
            return None

        try:
            response = load_persisted_result(path)
        except FixtureValidationError as error:
            raise InvalidPersistedResultError("Persisted dashboard result is invalid") from error

        if (
            response.department.department_code != department_code
            or response.department.requested_period != period
            or response.metadata.reference_period != period
        ):
            raise InvalidPersistedResultError(
                "Persisted dashboard result does not match its repository key"
            )
        return response


def create_demonstrative_repository() -> JsonDashboardResultRepository:
    """Create the read-only repository over the versioned Stage 7 results."""
    return JsonDashboardResultRepository(DEMONSTRATIVE_RESULT_PATHS)
