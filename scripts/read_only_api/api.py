"""FastAPI transport for the contracted read-only dashboard query."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from .errors import (
    DashboardDataNotFoundError,
    DashboardInternalError,
    DashboardQueryError,
    InvalidDepartmentCodeError,
    InvalidPeriodFormatError,
)
from .repository import DashboardResultRepository, create_demonstrative_repository
from .schemas import DashboardResponse, ErrorResponse
from .service import DashboardQueryService

_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {"model": ErrorResponse, "description": "Invalid query parameter"},
    404: {"model": ErrorResponse, "description": "Persisted result not found"},
    500: {"model": ErrorResponse, "description": "Safe internal error"},
}


class ContractFastAPI(FastAPI):
    """FastAPI application whose schema exposes only contracted responses."""

    def openapi(self) -> dict[str, Any]:
        """Build OpenAPI without FastAPI's uncontracted default 422 response."""
        schema = super().openapi()
        for path_item in schema.get("paths", {}).values():
            for operation in path_item.values():
                if isinstance(operation, dict):
                    operation.get("responses", {}).pop("422", None)
        component_schemas = schema.get("components", {}).get("schemas", {})
        component_schemas.pop("HTTPValidationError", None)
        component_schemas.pop("ValidationError", None)
        return schema


def _error_response(status_code: int, error: DashboardQueryError) -> JSONResponse:
    body = ErrorResponse(error_code=error.error_code, message=error.message)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def create_app(
    repository: DashboardResultRepository | None = None,
) -> FastAPI:
    """Create the Stage 7 HTTP application without starting a server.

    Args:
        repository: Optional read-only repository substitute. The versioned
            JSON repository is used when omitted.

    Returns:
        A configured FastAPI application with the single product endpoint.
    """
    query_service = DashboardQueryService(repository or create_demonstrative_repository())
    app = ContractFastAPI(
        title="SAT Dengue Read-Only API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get(
        "/api/dashboard",
        response_model=DashboardResponse,
        responses=_ERROR_RESPONSES,
        summary="Get persisted dashboard results",
    )
    def get_dashboard(
        department_code: str | None = Query(
            default=None,
            description="DANE department code: 50 for Meta or 73 for Tolima",
        ),
        period: str | None = Query(
            default=None,
            description="Reference period in YYYY-MM format",
        ),
    ) -> DashboardResponse | JSONResponse:
        try:
            return query_service.get_dashboard(department_code, period)
        except (InvalidDepartmentCodeError, InvalidPeriodFormatError) as error:
            return _error_response(400, error)
        except DashboardDataNotFoundError as error:
            return _error_response(404, error)
        except DashboardInternalError as error:
            return _error_response(500, error)
        except Exception:
            return _error_response(500, DashboardInternalError())

    return app
