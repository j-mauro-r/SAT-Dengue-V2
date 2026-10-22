"""Integration tests for the contracted Stage 7 dashboard endpoint."""

from __future__ import annotations

import asyncio
import hashlib
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from scripts.read_only_api import (
    DEMONSTRATIVE_RESULT_PATHS,
    META_FIXTURE_PATH,
    TOLIMA_FIXTURE_PATH,
    DashboardResponse,
    create_app,
    load_dashboard_fixture,
)


class FailingRepository:
    """Repository substitute that exposes a sensitive detail if mishandled."""

    def get(self, department_code: str, period: str) -> DashboardResponse | None:
        raise RuntimeError("private persisted path: /tmp/secret-result.json")


class EmptyRepository:
    """Falsey repository substitute that contains no persisted results."""

    def __bool__(self) -> bool:
        return False

    def get(self, department_code: str, period: str) -> DashboardResponse | None:
        return None


def _get(app: FastAPI, params: dict[str, str] | None = None) -> httpx.Response:
    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get("/api/dashboard", params=params)

    return asyncio.run(request())


@pytest.mark.parametrize(
    ("department_code", "period", "fixture_path"),
    [
        ("73", "2026-09", TOLIMA_FIXTURE_PATH),
        ("50", "2026-12", META_FIXTURE_PATH),
    ],
)
def test_dashboard_endpoint_returns_exact_validated_fixture(
    department_code: str, period: str, fixture_path: Path
) -> None:
    response = _get(
        create_app(),
        {"department_code": department_code, "period": period},
    )

    assert response.status_code == 200
    assert response.json() == load_dashboard_fixture(fixture_path).model_dump(mode="json")


@pytest.mark.parametrize(
    ("params", "status_code", "error_code", "message"),
    [
        (
            {"department_code": "76", "period": "2026-09"},
            400,
            "INVALID_DEPARTMENT_CODE",
            "El código del departamento no es válido.",
        ),
        (
            {"department_code": "73", "period": "2026-13"},
            400,
            "INVALID_PERIOD_FORMAT",
            "El periodo debe usar el formato YYYY-MM.",
        ),
        (
            {"department_code": "73", "period": "2026-12"},
            404,
            "DASHBOARD_DATA_NOT_FOUND",
            "No existen resultados para el departamento y periodo solicitados.",
        ),
    ],
)
def test_dashboard_endpoint_returns_exact_contracted_errors(
    params: dict[str, str], status_code: int, error_code: str, message: str
) -> None:
    response = _get(create_app(), params)

    assert response.status_code == status_code
    assert response.json() == {"error_code": error_code, "message": message}


def test_missing_query_parameters_use_contract_error_instead_of_422() -> None:
    response = _get(create_app())

    assert response.status_code == 400
    assert response.json() == {
        "error_code": "INVALID_DEPARTMENT_CODE",
        "message": "El código del departamento no es válido.",
    }


def test_internal_failure_returns_safe_500_without_details() -> None:
    response = _get(
        create_app(FailingRepository()),
        {"department_code": "73", "period": "2026-09"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "error_code": "INTERNAL_ERROR",
        "message": "No fue posible obtener la información del dashboard.",
    }
    assert "/tmp" not in response.text
    assert "secret-result" not in response.text
    assert "RuntimeError" not in response.text


def test_application_factory_preserves_a_falsey_repository_substitute() -> None:
    response = _get(
        create_app(EmptyRepository()),
        {"department_code": "73", "period": "2026-09"},
    )

    assert response.status_code == 404
    assert response.json()["error_code"] == "DASHBOARD_DATA_NOT_FOUND"


def test_repeated_http_queries_are_identical_and_do_not_modify_files() -> None:
    before = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in DEMONSTRATIVE_RESULT_PATHS.values()
    }
    app = create_app()

    first = _get(app, {"department_code": "73", "period": "2026-09"})
    second = _get(app, {"department_code": "73", "period": "2026-09"})

    after = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in DEMONSTRATIVE_RESULT_PATHS.values()
    }
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert after == before


def test_openapi_contains_only_contracted_endpoint_models_and_statuses() -> None:
    app = create_app()
    schema = app.openapi()
    operation = schema["paths"]["/api/dashboard"]["get"]

    assert set(schema["paths"]) == {"/api/dashboard"}
    assert {route.path for route in app.routes if isinstance(route, APIRoute)} == {"/api/dashboard"}
    assert set(operation["responses"]) == {"200", "400", "404", "500"}
    assert "422" not in operation["responses"]
    assert {"DashboardResponse", "ErrorResponse"} <= set(schema["components"]["schemas"])
    assert {"HTTPValidationError", "ValidationError"}.isdisjoint(schema["components"]["schemas"])
