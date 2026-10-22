"""Focused tests for the Stage 7 read-only repository and query service."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.read_only_api import (
    DEMONSTRATIVE_RESULT_PATHS,
    META_FIXTURE_PATH,
    TOLIMA_FIXTURE_PATH,
    DashboardDataNotFoundError,
    DashboardInternalError,
    DashboardQueryService,
    DashboardResponse,
    InvalidDepartmentCodeError,
    InvalidPeriodFormatError,
    InvalidPersistedResultError,
    JsonDashboardResultRepository,
    create_demonstrative_repository,
    load_dashboard_fixture,
)


class StubRepository:
    """Small repository substitute used to prove service isolation."""

    def __init__(
        self, response: DashboardResponse | None = None, failure: Exception | None = None
    ) -> None:
        self.response = response
        self.failure = failure
        self.calls: list[tuple[str, str]] = []

    def get(self, department_code: str, period: str) -> DashboardResponse | None:
        self.calls.append((department_code, period))
        if self.failure is not None:
            raise self.failure
        return self.response


def _in_memory_response(
    department_code: str = "73", department_name: str = "Tolima", period: str = "2026-09"
) -> DashboardResponse:
    return DashboardResponse.model_validate(
        {
            "metadata": {
                "result_set_id": "d1111111-1111-4111-8111-111111111111",
                "reference_period": period,
                "generated_at": "2026-10-03T14:30:00-05:00",
                "data_updated_at": None,
                "data_version": "in-memory-test",
            },
            "governance": {
                "governance_gate": "G5",
                "governance_status": "NOT_APPROVED",
                "champion_status": "NOT_SELECTED",
                "limitation": "Respuesta sintética para probar el servicio sin archivos.",
            },
            "department": {
                "department_code": department_code,
                "department_name": department_name,
                "requested_period": period,
            },
            "municipalities": [],
            "evaluation_context": {
                "demonstrative_values": True,
                "evaluation_records": [],
            },
        }
    )


@pytest.mark.parametrize(
    ("department_code", "period", "expected_path"),
    [
        ("73", "2026-09", TOLIMA_FIXTURE_PATH),
        ("50", "2026-12", META_FIXTURE_PATH),
    ],
)
def test_repository_and_service_return_exact_persisted_result(
    department_code: str, period: str, expected_path: Path
) -> None:
    response = DashboardQueryService(create_demonstrative_repository()).get_dashboard(
        department_code, period
    )

    assert response == load_dashboard_fixture(expected_path)


@pytest.mark.parametrize("department_code", [None, "", "5", "76", "730"])
def test_service_rejects_invalid_department(department_code: str | None) -> None:
    with pytest.raises(InvalidDepartmentCodeError):
        DashboardQueryService(create_demonstrative_repository()).get_dashboard(
            department_code, "2026-09"
        )


@pytest.mark.parametrize("period", [None, "", "2026-9", "2026-13", "09-2026"])
def test_service_rejects_invalid_period(period: str | None) -> None:
    with pytest.raises(InvalidPeriodFormatError):
        DashboardQueryService(create_demonstrative_repository()).get_dashboard("73", period)


def test_missing_period_does_not_fall_back_to_another_fixture() -> None:
    service = DashboardQueryService(create_demonstrative_repository())

    with pytest.raises(DashboardDataNotFoundError):
        service.get_dashboard("73", "2026-12")

    with pytest.raises(DashboardDataNotFoundError):
        service.get_dashboard("50", "2026-09")


def test_repository_distinguishes_an_invalid_persisted_file(tmp_path: Path) -> None:
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{}", encoding="utf-8")
    repository = JsonDashboardResultRepository({("73", "2026-09"): invalid_path})

    with pytest.raises(InvalidPersistedResultError):
        repository.get("73", "2026-09")

    with pytest.raises(DashboardInternalError):
        DashboardQueryService(repository).get_dashboard("73", "2026-09")


def test_service_uses_a_substitute_repository_without_file_access() -> None:
    response = _in_memory_response()
    repository = StubRepository(response=response)

    actual = DashboardQueryService(repository).get_dashboard("73", "2026-09")

    assert actual is response
    assert repository.calls == [("73", "2026-09")]


def test_service_rejects_a_repository_response_for_another_query() -> None:
    repository = StubRepository(response=_in_memory_response("50", "Meta", "2026-12"))

    with pytest.raises(DashboardInternalError):
        DashboardQueryService(repository).get_dashboard("73", "2026-09")


def test_unexpected_repository_failure_becomes_controlled_internal_error() -> None:
    repository = StubRepository(failure=RuntimeError("private /tmp/result path"))

    with pytest.raises(DashboardInternalError) as caught:
        DashboardQueryService(repository).get_dashboard("73", "2026-09")

    assert str(caught.value) == "No fue posible obtener la información del dashboard."


def test_repeated_queries_are_identical_and_do_not_modify_persisted_files() -> None:
    before = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in DEMONSTRATIVE_RESULT_PATHS.values()
    }
    service = DashboardQueryService(create_demonstrative_repository())

    first = service.get_dashboard("73", "2026-09").model_dump(mode="json")
    second = service.get_dashboard("73", "2026-09").model_dump(mode="json")

    after = {
        path: (path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
        for path in DEMONSTRATIVE_RESULT_PATHS.values()
    }
    assert first == second
    assert after == before
