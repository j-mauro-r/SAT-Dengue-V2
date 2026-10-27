"""Focused tests for the Stage 7 read-only repository and query service."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.read_only_api import (
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


def _fixture_response(
    department_code: str = "73", department_name: str = "Tolima", period: str = "2026-09"
) -> DashboardResponse:
    path = TOLIMA_FIXTURE_PATH if department_code == "73" else META_FIXTURE_PATH
    response = load_dashboard_fixture(path)
    assert response.department.department_name == department_name
    assert response.department.requested_period == period
    return response


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


def test_service_uses_a_substitute_repository() -> None:
    response = _fixture_response()
    repository = StubRepository(response=response)

    actual = DashboardQueryService(repository).get_dashboard("73", "2026-09")

    assert actual is response
    assert repository.calls == [("73", "2026-09")]


def test_service_rejects_a_repository_response_for_another_query() -> None:
    repository = StubRepository(response=_fixture_response("50", "Meta", "2026-12"))

    with pytest.raises(DashboardInternalError):
        DashboardQueryService(repository).get_dashboard("73", "2026-09")


def test_unexpected_repository_failure_becomes_controlled_internal_error() -> None:
    repository = StubRepository(failure=RuntimeError("private /tmp/result path"))

    with pytest.raises(DashboardInternalError) as caught:
        DashboardQueryService(repository).get_dashboard("73", "2026-09")

    assert str(caught.value) == "No fue posible obtener la información del dashboard."
