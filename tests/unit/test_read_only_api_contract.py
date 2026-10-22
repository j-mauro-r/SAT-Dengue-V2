"""Contract tests for the Stage 7 executable read-only API schemas."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scripts.read_only_api import (
    DEMONSTRATIVE_FIXTURE_PATHS,
    META_FIXTURE_PATH,
    TOLIMA_FIXTURE_PATH,
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
    load_demonstrative_fixture,
    resolve_demonstrative_fixture_path,
)


@pytest.fixture
def fixture_payload() -> dict[str, Any]:
    return json.loads(TOLIMA_FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("department_code", "fixture_path", "department_name"),
    [
        ("50", META_FIXTURE_PATH, "Meta"),
        ("73", TOLIMA_FIXTURE_PATH, "Tolima"),
    ],
)
def test_demonstrative_fixtures_load_and_round_trip(
    department_code: str, fixture_path: Path, department_name: str
) -> None:
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    response = load_demonstrative_fixture(department_code)

    assert response.model_dump(mode="json") == raw
    assert response.evaluation_context.demonstrative_values is True
    assert response.department.department_name == department_name


def test_error_response_round_trip() -> None:
    assert ErrorResponse(
        error_code=ErrorCode.INVALID_PERIOD_FORMAT,
        message="El periodo debe usar el formato YYYY-MM.",
    ).model_dump(mode="json") == {
        "error_code": "INVALID_PERIOD_FORMAT",
        "message": "El periodo debe usar el formato YYYY-MM.",
    }


def test_runtime_fixture_paths_are_explicit_and_outside_tests() -> None:
    assert DEMONSTRATIVE_FIXTURE_PATHS == {
        "50": META_FIXTURE_PATH,
        "73": TOLIMA_FIXTURE_PATH,
    }
    for path in DEMONSTRATIVE_FIXTURE_PATHS.values():
        assert path.is_absolute()
        assert "tests" not in path.parts
        assert path.parent.name == "fixtures"


@pytest.mark.parametrize(
    ("department_code", "expected"),
    [("50", META_FIXTURE_PATH), ("73", TOLIMA_FIXTURE_PATH)],
)
def test_fixture_resolution_by_department(department_code: str, expected: Path) -> None:
    assert resolve_demonstrative_fixture_path(department_code) == expected


def test_unsupported_fixture_department_fails_clearly() -> None:
    with pytest.raises(
        FixtureValidationError, match="Unsupported demonstrative department code: 76"
    ):
        resolve_demonstrative_fixture_path("76")


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
        "INELIGIBLE",
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


@pytest.mark.parametrize(
    ("horizon_index", "invalid_period", "expected"),
    [
        (0, "2026-11", "T1 target_period must be 2026-10"),
        (1, "2026-12", "T2 target_period must be 2026-11"),
    ],
)
def test_target_period_must_match_reference_and_horizon(
    fixture_payload: dict[str, Any],
    horizon_index: int,
    invalid_period: str,
    expected: str,
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["results"][horizon_index]["target_period"] = invalid_period

    with pytest.raises(ValidationError, match=expected):
        DashboardResponse.model_validate(payload)


def test_december_reference_rolls_targets_into_january_and_february() -> None:
    response = load_demonstrative_fixture("50")

    for municipality in response.municipalities:
        targets = {result.horizon: result.target_period for result in municipality.results}
        assert targets[Horizon.T1] == "2027-01"
        assert targets[Horizon.T2] == "2027-02"


def test_november_reference_rolls_targets_into_december_and_january(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["metadata"]["reference_period"] = "2026-11"
    payload["department"]["requested_period"] = "2026-11"
    for municipality in payload["municipalities"]:
        municipality["results"][0]["target_period"] = "2026-12"
        municipality["results"][1]["target_period"] = "2027-01"
        if municipality["endemic_channel_series"]:
            municipality["endemic_channel_series"][8]["cases"] = None
            november = municipality["endemic_channel_series"][10]
            november["cases"] = municipality["cases_t"]
            november["p25"] = municipality["p25"]
            november["median"] = municipality["median"]
            november["p75"] = municipality["p75"]

    response = DashboardResponse.model_validate(payload)

    assert response.metadata.reference_period == "2026-11"


def test_municipality_must_belong_to_response_department(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["municipality_code"] = "50001"

    with pytest.raises(ValidationError, match="must belong to the response department"):
        DashboardResponse.model_validate(payload)


def test_municipality_codes_are_unique(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][1]["municipality_code"] = payload["municipalities"][0][
        "municipality_code"
    ]

    with pytest.raises(ValidationError, match="municipality_code values must be unique"):
        DashboardResponse.model_validate(payload)


def test_fixtures_match_the_versioned_dane_divipola_inventory() -> None:
    source = json.loads(Path("data/sources/Divipola-municipios.md").read_text(encoding="utf-8"))
    expected = {
        department: {
            row["CODIGO_DPTO_MPIO"]: row["NOMBRE_MUNICIPIO"]
            for row in source["resultado"]
            if row["CODIGO_DEPARTAMENTO"] == department
        }
        for department in ("50", "73")
    }
    responses = {department: load_demonstrative_fixture(department) for department in ("50", "73")}

    assert {department: len(inventory) for department, inventory in expected.items()} == {
        "50": 29,
        "73": 47,
    }
    assert sum(len(response.municipalities) for response in responses.values()) == 76
    for department, response in responses.items():
        actual = {
            municipality.municipality_code: municipality.municipality_name.upper()
            for municipality in response.municipalities
        }
        assert actual == expected[department]
        assert all(code.startswith(department) for code in actual)
        assert all(
            {result.horizon for result in municipality.results} == set(Horizon)
            for municipality in response.municipalities
        )


def test_demonstrative_fixtures_cover_every_availability_state() -> None:
    statuses = {
        result.availability_status
        for department in ("50", "73")
        for municipality in load_demonstrative_fixture(department).municipalities
        for result in municipality.results
    }

    assert statuses == set(AvailabilityStatus)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("result_id", "a1111111-1111-4111-8111-111111111111", "requires result_id"),
        ("probability", 0.2, "requires result_id, probability, and threshold null"),
        ("threshold", 0.5, "requires result_id, probability, and threshold null"),
        ("alert_status", "NO_ALERT", "requires alert_status UNAVAILABLE"),
    ],
)
def test_ineligible_rejects_available_result_shape(
    fixture_payload: dict[str, Any], field: str, value: object, expected: str
) -> None:
    payload = copy.deepcopy(fixture_payload)
    result = payload["municipalities"][2]["results"][0]
    assert result["availability_status"] == "INELIGIBLE"
    result[field] = value

    with pytest.raises(ValidationError, match=expected):
        DashboardResponse.model_validate(payload)


def test_endemic_series_rejects_duplicate_periods(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    series = payload["municipalities"][0]["endemic_channel_series"]
    series[1]["period"] = series[0]["period"]

    with pytest.raises(ValidationError, match="periods must be unique"):
        DashboardResponse.model_validate(payload)


def test_endemic_series_rejects_unsorted_periods(fixture_payload: dict[str, Any]) -> None:
    payload = copy.deepcopy(fixture_payload)
    series = payload["municipalities"][0]["endemic_channel_series"]
    series[0], series[1] = series[1], series[0]

    with pytest.raises(ValidationError, match="chronologically ordered"):
        DashboardResponse.model_validate(payload)


def test_endemic_series_rejects_observed_cases_after_t(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["endemic_channel_series"][9]["cases"] = 1

    with pytest.raises(ValidationError, match="Observed cases after reference_period"):
        DashboardResponse.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [("p25", 36.0), ("median", 48.0)],
)
def test_endemic_series_rejects_unordered_percentiles(
    fixture_payload: dict[str, Any], field: str, value: float
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["endemic_channel_series"][0][field] = value

    with pytest.raises(ValidationError, match="p25 <= median <= p75"):
        DashboardResponse.model_validate(payload)


def test_reference_endemic_point_must_match_summary(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["endemic_channel_series"][8]["cases"] = 49

    with pytest.raises(ValidationError, match="must match municipal summary"):
        DashboardResponse.model_validate(payload)


def test_empty_endemic_series_requires_unavailable_observed_context(
    fixture_payload: dict[str, Any],
) -> None:
    payload = copy.deepcopy(fixture_payload)
    payload["municipalities"][0]["endemic_channel_series"] = []

    with pytest.raises(ValidationError, match="requires unavailable observed context"):
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
