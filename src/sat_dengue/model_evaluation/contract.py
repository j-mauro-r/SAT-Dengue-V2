"""Pure scientific calendar validation; JSON reading belongs to the dataset adapter."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .decision_policy import ChampionDecisionPolicy, Stage5Knobs

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
WINDOW_RE = re.compile(r"^\d{4}-\d{2}_t[12]$")


class ModelEvaluationError(ValueError):
    """A Stage 5 precondition is violated."""


@dataclass(frozen=True)
class Stage5Contract:
    """Parsed Stage 5 contract fields used by the execution pipeline."""

    raw: dict[str, Any]
    knobs: Stage5Knobs
    decision_policy: ChampionDecisionPolicy


def _as_month_list(value: Any, *, label: str) -> list[str]:
    """Validate month arrays in YYYY-MM format."""
    if not isinstance(value, list) or not value:
        raise ModelEvaluationError(f"{label} must be a non-empty list")
    parsed = []
    for item in value:
        if not isinstance(item, str) or MONTH_RE.match(item) is None:
            raise ModelEvaluationError(f"{label} contains invalid month: {item!r}")
        parsed.append(item)
    return parsed


def _as_month_range(value: Any, *, label: str) -> dict[str, str]:
    """Validate a month range object with inclusive start/end."""
    if not isinstance(value, dict):
        raise ModelEvaluationError(f"{label} must be an object")
    start = value.get("start")
    end = value.get("end")
    if not isinstance(start, str) or MONTH_RE.match(start) is None:
        raise ModelEvaluationError(f"{label}.start must be YYYY-MM")
    if not isinstance(end, str) or MONTH_RE.match(end) is None:
        raise ModelEvaluationError(f"{label}.end must be YYYY-MM")
    if start > end:
        raise ModelEvaluationError(f"{label} has descending range")
    return {"start": start, "end": end}


def _validate_window_role_calendar(raw: dict[str, Any], reserved_start: str) -> None:
    """Validate explicit role calendars and chronology for each Stage 4 window."""
    calendar = raw.get("window_role_calendar")
    if not isinstance(calendar, dict) or not calendar:
        raise ModelEvaluationError("Stage5 contract requires window_role_calendar")

    support = raw.get("support_requirements")
    if not isinstance(support, dict):
        raise ModelEvaluationError("Stage5 contract requires support_requirements")
    required_minimums = {
        "min_hyperparameter_selection_months",
        "min_calibration_fit_months",
        "min_calibration_selection_months",
        "min_threshold_selection_months",
    }
    missing_minimums = sorted(required_minimums - set(support.keys()))
    if missing_minimums:
        raise ModelEvaluationError(f"Missing support requirements: {missing_minimums}")
    minimums: dict[str, int] = {}
    for key in required_minimums:
        value = support[key]
        if not isinstance(value, int) or value <= 0:
            raise ModelEvaluationError(f"{key} must be a positive integer")
        minimums[key] = value

    for window, roles in calendar.items():
        if not isinstance(window, str) or WINDOW_RE.match(window) is None:
            raise ModelEvaluationError(f"Invalid window id in calendar: {window!r}")
        if not isinstance(roles, dict):
            raise ModelEvaluationError(f"Calendar entry for {window} must be an object")

        hp = _as_month_list(
            roles.get("hyperparameter_selection_targets"),
            label=f"{window}.hyperparameter_selection_targets",
        )
        cal_fit = _as_month_list(
            roles.get("calibration_fit_targets"), label=f"{window}.calibration_fit_targets"
        )
        cal_sel = _as_month_list(
            roles.get("calibration_selection_targets"),
            label=f"{window}.calibration_selection_targets",
        )
        thr_sel = _as_month_list(
            roles.get("threshold_selection_targets"), label=f"{window}.threshold_selection_targets"
        )

        if len(hp) < minimums["min_hyperparameter_selection_months"]:
            raise ModelEvaluationError(f"Insufficient hyperparameter-selection months for {window}")
        if len(cal_fit) < minimums["min_calibration_fit_months"]:
            raise ModelEvaluationError(f"Insufficient calibration-fit months for {window}")
        if len(cal_sel) < minimums["min_calibration_selection_months"]:
            raise ModelEvaluationError(f"Insufficient calibration-selection months for {window}")
        if len(thr_sel) < minimums["min_threshold_selection_months"]:
            raise ModelEvaluationError(f"Insufficient threshold-selection months for {window}")

        role_sets = {
            "hyperparameter_selection_targets": set(hp),
            "calibration_fit_targets": set(cal_fit),
            "calibration_selection_targets": set(cal_sel),
            "threshold_selection_targets": set(thr_sel),
        }
        overlap = (
            (role_sets["hyperparameter_selection_targets"] & role_sets["calibration_fit_targets"])
            | (
                role_sets["hyperparameter_selection_targets"]
                & role_sets["calibration_selection_targets"]
            )
            | (
                role_sets["hyperparameter_selection_targets"]
                & role_sets["threshold_selection_targets"]
            )
            | (role_sets["calibration_fit_targets"] & role_sets["calibration_selection_targets"])
            | (role_sets["calibration_fit_targets"] & role_sets["threshold_selection_targets"])
            | (
                role_sets["calibration_selection_targets"]
                & role_sets["threshold_selection_targets"]
            )
        )
        if overlap:
            raise ModelEvaluationError(f"Role month overlap for {window}: {sorted(overlap)}")

        if max(hp) >= min(cal_fit):
            raise ModelEvaluationError(f"Role chronology broken before calibration_fit in {window}")
        if max(cal_fit) >= min(cal_sel):
            raise ModelEvaluationError(
                f"Role chronology broken before calibration_selection in {window}"
            )
        if max(cal_sel) >= min(thr_sel):
            raise ModelEvaluationError(
                f"Role chronology broken before threshold_selection in {window}"
            )

        if any(month >= reserved_start for month in hp + cal_fit + cal_sel + thr_sel):
            raise ModelEvaluationError(f"Reserved block month entered role calendar for {window}")

        origin_range = _as_month_range(
            roles.get("external_evaluation_origin_range"),
            label=f"{window}.external_evaluation_origin_range",
        )
        _as_month_range(
            roles.get("external_evaluation_target_range"),
            label=f"{window}.external_evaluation_target_range",
        )
        available = roles.get("component_available_by_origin")
        if not isinstance(available, str) or MONTH_RE.match(available) is None:
            raise ModelEvaluationError(f"{window}.component_available_by_origin must be YYYY-MM")
        if max(thr_sel) > available:
            raise ModelEvaluationError(
                f"{window} threshold selection extends beyond component availability cutoff"
            )
        if available > origin_range["start"]:
            raise ModelEvaluationError(
                f"{window} component availability is after external evaluation origin start"
            )
