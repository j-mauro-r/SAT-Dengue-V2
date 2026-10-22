"""Typed executable schemas for the Stage 6 Product Contract."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


def _require_rfc3339_string(value: object) -> object:
    """Reject non-string timestamp inputs before Pydantic parses RFC 3339."""
    if not isinstance(value, str) or len(value) > 35:
        raise ValueError("Timestamp must be an RFC 3339 string of at most 35 characters")
    return value


Month = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$", strict=True)]
MunicipalityCode = Annotated[str, StringConstraints(pattern=r"^\d{5}$", strict=True)]
DepartmentCode = Literal["50", "73"]
Probability = Annotated[float, Field(strict=True, ge=0.0, le=1.0)]
NonNegativeCount = Annotated[int, Field(strict=True, ge=0, le=2_147_483_647)]
NonNegativeMeasure = Annotated[float, Field(strict=True, ge=0.0, le=2_147_483_647)]
RFC3339DateTime = Annotated[AwareDatetime, BeforeValidator(_require_rfc3339_string)]


class ContractModel(BaseModel):
    """Base configuration shared by every executable contract model."""

    model_config = ConfigDict(extra="forbid")


class Horizon(StrEnum):
    """Supported monthly forecast horizons."""

    T1 = "T1"
    T2 = "T2"


class EndemicZone(StrEnum):
    """Observed endemic-channel states."""

    EXITO = "EXITO"
    SEGURIDAD = "SEGURIDAD"
    ALERTA = "ALERTA"
    EXCESO = "EXCESO"
    UNAVAILABLE = "UNAVAILABLE"


class AlertStatus(StrEnum):
    """Derived predictive alert states."""

    ALERT = "ALERT"
    NO_ALERT = "NO_ALERT"
    UNAVAILABLE = "UNAVAILABLE"


class AvailabilityStatus(StrEnum):
    """Contractual result-availability states."""

    AVAILABLE = "AVAILABLE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    MISSING_DATA = "MISSING_DATA"
    NOT_CALCULATED = "NOT_CALCULATED"


class GovernanceStatus(StrEnum):
    """Scientific-governance decision states."""

    APPROVED = "APPROVED"
    NOT_APPROVED = "NOT_APPROVED"


class ChampionStatus(StrEnum):
    """Champion-selection states."""

    SELECTED = "SELECTED"
    NOT_SELECTED = "NOT_SELECTED"


class ModelRole(StrEnum):
    """Governance roles assignable to model artifacts."""

    PROVISIONAL_CANDIDATE = "PROVISIONAL_CANDIDATE"
    CHAMPION = "CHAMPION"


class ErrorCode(StrEnum):
    """Error codes defined by the Product Contract."""

    INVALID_DEPARTMENT_CODE = "INVALID_DEPARTMENT_CODE"
    INVALID_PERIOD_FORMAT = "INVALID_PERIOD_FORMAT"
    DASHBOARD_DATA_NOT_FOUND = "DASHBOARD_DATA_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class Metadata(ContractModel):
    """Traceability and freshness for one department-period result set."""

    result_set_id: UUID
    reference_period: Month
    generated_at: RFC3339DateTime
    data_updated_at: RFC3339DateTime | None
    data_version: Annotated[str, Field(min_length=1, max_length=128)]


class Governance(ContractModel):
    """Scientific governance exposed to the read-only consumer."""

    governance_gate: Annotated[str, Field(min_length=1, max_length=16)]
    governance_status: GovernanceStatus
    champion_status: ChampionStatus
    limitation: Annotated[str, Field(min_length=1, max_length=500)]

    @model_validator(mode="after")
    def validate_not_approved_champion(self) -> Self:
        """Keep an unapproved G5 response from claiming a selected Champion."""
        if (
            self.governance_gate == "G5"
            and self.governance_status is GovernanceStatus.NOT_APPROVED
            and self.champion_status is not ChampionStatus.NOT_SELECTED
        ):
            raise ValueError("G5 NOT_APPROVED requires champion_status NOT_SELECTED")
        return self


class Department(ContractModel):
    """Department selected by the dashboard request."""

    department_code: DepartmentCode
    department_name: Annotated[str, Field(min_length=1, max_length=100)]
    requested_period: Month


class Result(ContractModel):
    """One municipality, horizon, and target-period result."""

    result_id: UUID | None
    horizon: Horizon
    target_period: Month
    probability: Probability | None
    threshold: Probability | None
    alert_status: AlertStatus
    availability_status: AvailabilityStatus
    availability_reason: Annotated[str, Field(min_length=1, max_length=300)] | None
    model_family: Annotated[str, Field(min_length=1, max_length=32)] | None
    model_role: ModelRole | None
    model_version: Annotated[str, Field(min_length=1, max_length=128)] | None
    procedure_id: Annotated[str, Field(min_length=1, max_length=128)] | None

    @model_validator(mode="after")
    def validate_availability(self) -> Self:
        """Enforce the Product Contract's available and unavailable shapes."""
        if self.availability_status is AvailabilityStatus.AVAILABLE:
            required = {
                "result_id": self.result_id,
                "probability": self.probability,
                "threshold": self.threshold,
                "model_family": self.model_family,
                "model_role": self.model_role,
                "model_version": self.model_version,
                "procedure_id": self.procedure_id,
            }
            missing = sorted(name for name, value in required.items() if value is None)
            if missing:
                raise ValueError(f"AVAILABLE result requires: {', '.join(missing)}")
            if self.availability_reason is not None:
                raise ValueError("AVAILABLE result requires availability_reason null")
            probability = self.probability
            threshold = self.threshold
            assert probability is not None and threshold is not None
            expected = AlertStatus.ALERT if probability >= threshold else AlertStatus.NO_ALERT
            if self.alert_status is not expected:
                raise ValueError("alert_status must match probability >= threshold")
            return self

        if self.result_id is not None or self.probability is not None or self.threshold is not None:
            raise ValueError(
                "Unavailable result requires result_id, probability, and threshold null"
            )
        if self.alert_status is not AlertStatus.UNAVAILABLE:
            raise ValueError("Unavailable result requires alert_status UNAVAILABLE")
        if self.availability_reason is None:
            raise ValueError("Unavailable result requires availability_reason")
        return self


class Municipality(ContractModel):
    """Observed municipal context and exactly one result per horizon."""

    municipality_code: MunicipalityCode
    municipality_name: Annotated[str, Field(min_length=1, max_length=150)]
    cases_t: NonNegativeCount | None
    endemic_zone_t: EndemicZone
    p25: NonNegativeMeasure | None
    median: NonNegativeMeasure | None
    p75: NonNegativeMeasure | None
    results: Annotated[list[Result], Field(min_length=2, max_length=2)]

    @model_validator(mode="after")
    def validate_horizons(self) -> Self:
        """Require T1 and T2 exactly once for every municipality."""
        horizons = [result.horizon for result in self.results]
        if len(set(horizons)) != 2 or set(horizons) != set(Horizon):
            raise ValueError("Municipality results must contain T1 and T2 exactly once")
        return self


class EvaluationRecord(ContractModel):
    """Historically scoped Stage 5 evaluation metrics."""

    horizon: Horizon
    procedure_id: Annotated[str, Field(min_length=1, max_length=128)]
    evaluation_period_start: Month
    evaluation_period_end: Month
    evaluation_geography: Annotated[str, Field(min_length=1, max_length=300)]
    auroc: Probability | None
    average_precision: Probability | None
    brier: Probability | None
    false_alerts: NonNegativeCount | None
    alerts_emitted: NonNegativeCount | None
    false_alert_ratio: Probability | None
    onsets_detected: NonNegativeCount | None
    actual_onsets: NonNegativeCount | None
    onset_sensitivity: Probability | None


class EvaluationContext(ContractModel):
    """Historically scoped context, separate from current results."""

    demonstrative_values: Annotated[bool, Field(strict=True)]
    evaluation_records: list[EvaluationRecord]


class DashboardResponse(ContractModel):
    """Successful response for one department and reference period."""

    metadata: Metadata
    governance: Governance
    department: Department
    municipalities: list[Municipality]
    evaluation_context: EvaluationContext

    @model_validator(mode="after")
    def validate_response_invariants(self) -> Self:
        """Enforce set-wide traceability and G5 model-role invariants."""
        if self.metadata.reference_period != self.department.requested_period:
            raise ValueError("reference_period must equal requested_period")

        expected_target_periods = {
            Horizon.T1: _shift_month(self.metadata.reference_period, 1),
            Horizon.T2: _shift_month(self.metadata.reference_period, 2),
        }
        municipality_codes = [
            municipality.municipality_code for municipality in self.municipalities
        ]
        if len(municipality_codes) != len(set(municipality_codes)):
            raise ValueError("municipality_code values must be unique within a response")

        department_code = self.department.department_code
        for municipality in self.municipalities:
            if not municipality.municipality_code.startswith(department_code):
                raise ValueError("municipality_code must belong to the response department")
            for result in municipality.results:
                expected_period = expected_target_periods[result.horizon]
                if result.target_period != expected_period:
                    raise ValueError(
                        f"{result.horizon.value} target_period must be {expected_period} "
                        f"for reference_period {self.metadata.reference_period}"
                    )

        available_ids = [
            result.result_id
            for municipality in self.municipalities
            for result in municipality.results
            if result.availability_status is AvailabilityStatus.AVAILABLE
        ]
        if len(available_ids) != len(set(available_ids)):
            raise ValueError("Available result_id values must be unique within a result set")
        if self.metadata.result_set_id in available_ids:
            raise ValueError("result_set_id must differ from every individual result_id")

        if (
            self.governance.governance_gate == "G5"
            and self.governance.governance_status is GovernanceStatus.NOT_APPROVED
        ):
            invalid_roles = [
                result.model_role
                for municipality in self.municipalities
                for result in municipality.results
                if result.model_role is not None
                and result.model_role is not ModelRole.PROVISIONAL_CANDIDATE
            ]
            if invalid_roles:
                raise ValueError("G5 NOT_APPROVED only permits PROVISIONAL_CANDIDATE models")
        return self


def _shift_month(period: str, months: int) -> str:
    """Shift a validated ``YYYY-MM`` period by a non-negative month count."""
    year_text, month_text = period.split("-")
    month_index = int(year_text) * 12 + int(month_text) - 1 + months
    year, zero_based_month = divmod(month_index, 12)
    return f"{year:04d}-{zero_based_month + 1:02d}"


class ErrorResponse(ContractModel):
    """Contracted error response body."""

    error_code: ErrorCode
    message: Annotated[str, Field(min_length=1)]
