"""Contract tests for the Stage 7 executable read-only API schemas."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.read_only_api import (
    DEFAULT_FIXTURE_PATH,
    AlertStatus,
    AvailabilityStatus,
    ChampionStatus,
    DashboardResponse,
    EndemicZone,
    ErrorCode,
    ErrorResponse,
    FixtureValidationError,
    GovernanceStatus,
    Horizon,
    ModelRole,
    load_dashboard_fixture,
)


@pytest.fixture
def fixture_payload() -> dict[str, Any]:
    return json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_demonstrative_fixture_loads_and_round_trips() -> None:
    raw = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
    response = load_dashboard_fixture()

    assert response.model_dump(mode="json") == raw
    assert response.evaluation_context.demonstrative_values is True
    assert ErrorResponse(
        error_code=ErrorCode.INVALID_PERIOD_FORMAT,
        message="El periodo debe usar el formato YYYY-MM.",
    ).model_dump(mode="json") == {
        "error_code": "INVALID_PERIOD_FORMAT",
        "message": "El periodo debe usar el formato YYYY-MM.",
    }


def test_fixture_loader_reports_contract_failure_clearly(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid-dashboard.json"
    invalid.write_text('{"metadata": {}}', encoding="utf-8")

    with pytest.raises(FixtureValidationError, match="Invalid dashboard fixture"):
        load_dashboard_fixture(invalid)


def test_closed_enums_match_the_product_contract() -> None:
    assert {item.value for item in Horizon} == {"T1", "T2"}
    assert {item.value for item in EndemicZone} == {
        "EXITO",
        "SEGURIDAD",
        "ALERTA",
        "EXCESO",
        "UNAVAILABLE",
    }
    assert {item.value for item in AlertStatus} == {"ALERT", "NO_ALERT", "UNAVAILABLE"}
    assert {item.value for item in AvailabilityStatus} == {
        "AVAILABLE",
        "INSUFFICIENT_HISTORY",
        "MISSING_DATA",
        "NOT_CALCULATED",
    }
    assert {item.value for item in GovernanceStatus} == {"APPROVED", "NOT_APPROVED"}
    assert {item.value for item in ChampionStatus} == {"SELECTED", "NOT_SELECTED"}
    assert {item.value for item in ModelRole} == {"PROVISIONAL_CANDIDATE", "CHAMPION"}


def test_available_result_requires_result_id(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["results"][0]["result_id"] = None

    with pytest.raises(ValidationError, match="AVAILABLE result requires: result_id"):
        DashboardResponse.model_validate(payload)


def test_unavailable_result_rejects_probability(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][1]["results"][0]["probability"] = 0.2

    with pytest.raises(
        ValidationError, match="requires result_id, probability, and threshold null"
    ):
        DashboardResponse.model_validate(payload)


def test_available_alert_must_match_probability_and_threshold(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["results"][0]["alert_status"] = "NO_ALERT"

    with pytest.raises(ValidationError, match="alert_status must match"):
        DashboardResponse.model_validate(payload)


def test_available_result_ids_are_unique(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    results = payload["municipalities"][0]["results"]
    results[1]["result_id"] = results[0]["result_id"]

    with pytest.raises(ValidationError, match="result_id values must be unique"):
        DashboardResponse.model_validate(payload)


def test_result_set_id_is_not_an_individual_result_id(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["results"][0]["result_id"] = payload["metadata"]["result_set_id"]

    with pytest.raises(ValidationError, match="result_set_id must differ"):
        DashboardResponse.model_validate(payload)


def test_not_approved_g5_rejects_champion_role(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["results"][0]["model_role"] = "CHAMPION"

    with pytest.raises(ValidationError, match="only permits PROVISIONAL_CANDIDATE"):
        DashboardResponse.model_validate(payload)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (("metadata", "reference_period", "2026-13"), "string_pattern_mismatch"),
        (("metadata", "generated_at", "2026-10-03T14:30:00"), "timezone_aware"),
        (("department", "department_code", "76"), "literal_error"),
        (("municipalities", 0, "municipality_code", "7301"), "string_pattern_mismatch"),
    ],
)
def test_invalid_period_or_territorial_code_fails(
    fixture_payload: dict[str, Any], mutation: tuple[object, ...], expected: str
) -> None:
    payload = copy.deepcopy(fixture_payload)
    target: Any = payload
    for key in mutation[:-2]:
        target = target[key]
    target[mutation[-2]] = mutation[-1]

    with pytest.raises(ValidationError, match=expected):
        DashboardResponse.model_validate(payload)
