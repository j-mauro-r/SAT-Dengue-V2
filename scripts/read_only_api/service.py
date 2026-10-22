"""Application service for read-only dashboard queries."""

from __future__ import annotations

import re

from .errors import (
    DashboardDataNotFoundError,
    DashboardInternalError,
    InvalidDepartmentCodeError,
    InvalidPeriodFormatError,
    InvalidPersistedResultError,
)
from .repository import DashboardResultRepository
from .schemas import DashboardResponse

_SUPPORTED_DEPARTMENTS = frozenset({"50", "73"})
_PERIOD_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class DashboardQueryService:
    """Validate a query and coordinate read-only persisted-result retrieval."""

    def __init__(self, repository: DashboardResultRepository) -> None:
        """Create the service around a repository boundary.

        Args:
            repository: Read-only source of validated dashboard responses.
        """
        self._repository = repository

    def get_dashboard(self, department_code: str | None, period: str | None) -> DashboardResponse:
        """Return the exact dashboard response for a valid query.

        Args:
            department_code: Requested DANE department code.
            period: Requested reference month in ``YYYY-MM`` format.

        Returns:
            The validated persisted dashboard response.

        Raises:
            InvalidDepartmentCodeError: If the department is unsupported.
            InvalidPeriodFormatError: If the period is malformed.
            DashboardDataNotFoundError: If the exact query has no result.
            DashboardInternalError: If persistence fails or returns a mismatch.
        """
        if department_code not in _SUPPORTED_DEPARTMENTS:
            raise InvalidDepartmentCodeError
        if period is None or _PERIOD_PATTERN.fullmatch(period) is None:
            raise InvalidPeriodFormatError

        try:
            response = self._repository.get(department_code, period)
        except InvalidPersistedResultError as error:
            raise DashboardInternalError from error
        except Exception as error:
            raise DashboardInternalError from error

        if response is None:
            raise DashboardDataNotFoundError
        if (
            response.department.department_code != department_code
            or response.department.requested_period != period
            or response.metadata.reference_period != period
        ):
            raise DashboardInternalError
        return response
