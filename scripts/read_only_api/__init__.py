"""Executable contracts for the future read-only Stage 7 API."""

from .errors import (
    DashboardDataNotFoundError,
    DashboardInternalError,
    DashboardQueryError,
    InvalidDepartmentCodeError,
    InvalidPeriodFormatError,
    InvalidPersistedResultError,
)
from .loader import (
    DEMONSTRATIVE_FIXTURE_PATHS,
    FIXTURES_DIRECTORY,
    META_FIXTURE_PATH,
    TOLIMA_FIXTURE_PATH,
    FixtureValidationError,
    load_dashboard_fixture,
    load_demonstrative_fixture,
    resolve_demonstrative_fixture_path,
)
from .repository import (
    DEMONSTRATIVE_RESULT_PATHS,
    DashboardResultRepository,
    JsonDashboardResultRepository,
    create_demonstrative_repository,
)
from .schemas import (
    AlertStatus,
    AvailabilityStatus,
    ChampionStatus,
    DashboardResponse,
    DepartmentCode,
    EndemicZone,
    ErrorCode,
    ErrorResponse,
    GovernanceStatus,
    Horizon,
    ModelRole,
)
from .service import DashboardQueryService

__all__ = [
    "DEMONSTRATIVE_FIXTURE_PATHS",
    "DEMONSTRATIVE_RESULT_PATHS",
    "FIXTURES_DIRECTORY",
    "META_FIXTURE_PATH",
    "TOLIMA_FIXTURE_PATH",
    "AlertStatus",
    "AvailabilityStatus",
    "ChampionStatus",
    "DashboardResponse",
    "DashboardDataNotFoundError",
    "DashboardInternalError",
    "DashboardQueryError",
    "DashboardQueryService",
    "DashboardResultRepository",
    "DepartmentCode",
    "EndemicZone",
    "ErrorCode",
    "ErrorResponse",
    "FixtureValidationError",
    "GovernanceStatus",
    "Horizon",
    "InvalidDepartmentCodeError",
    "InvalidPeriodFormatError",
    "InvalidPersistedResultError",
    "JsonDashboardResultRepository",
    "ModelRole",
    "load_dashboard_fixture",
    "load_demonstrative_fixture",
    "resolve_demonstrative_fixture_path",
    "create_demonstrative_repository",
]
