"""Controlled repository and application errors for dashboard queries."""

from __future__ import annotations

from .schemas import ErrorCode


class DashboardQueryError(Exception):
    """A controlled application error with a contracted consumer message."""

    error_code: ErrorCode
    message: str

    def __init__(self) -> None:
        super().__init__(self.message)


class InvalidDepartmentCodeError(DashboardQueryError):
    """The requested department is outside the contracted catalog."""

    error_code = ErrorCode.INVALID_DEPARTMENT_CODE
    message = "El código del departamento no es válido."


class InvalidPeriodFormatError(DashboardQueryError):
    """The requested period is not a valid contracted calendar month."""

    error_code = ErrorCode.INVALID_PERIOD_FORMAT
    message = "El periodo debe usar el formato YYYY-MM."


class DashboardDataNotFoundError(DashboardQueryError):
    """No persisted response exists for a valid query."""

    error_code = ErrorCode.DASHBOARD_DATA_NOT_FOUND
    message = "No existen resultados para el departamento y periodo solicitados."


class DashboardInternalError(DashboardQueryError):
    """A query failed without exposing internal implementation details."""

    error_code = ErrorCode.INTERNAL_ERROR
    message = "No fue posible obtener la información del dashboard."


class InvalidPersistedResultError(Exception):
    """A configured persisted result cannot be read or violates the contract."""
