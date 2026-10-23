"""Six reviewable final procedures, without training or reserved authorization."""

from __future__ import annotations

import json
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_evaluation.model_evaluation.availability import (
    ROLES,
    availability_transition,
)
from scripts.training_preparation.pipeline import fingerprint

from .policy import proposed_calendar

FAMILIES = ("xgboost", "lightgbm", "gam")


def _retained_procedure(
    bundle: Path,
    candidate: str,
    horizon: int,
    contract: dict[str, Any],
    calibrators: list[dict[str, Any]],
    thresholds: pd.DataFrame,
    transitions: pd.DataFrame,
) -> dict[str, Any]:
    """Bind one procedure to exact saved decisions and their verified availability."""
    calendar = proposed_calendar(horizon, contract["proposed_final"])
    window = calendar["retained_internal_window"]
    component_path = bundle / f"{candidate}_{window}_internal_components.json"
    preparer_path = bundle / f"{candidate}_{window}_outer_preparer.json"
    components = json.loads(component_path.read_text())
    preparer = json.loads(preparer_path.read_text())
    calibrator = [
        r for r in calibrators if r["candidate"] == candidate and r["window_id"] == window
    ]
    threshold = thresholds[thresholds.candidate.eq(candidate) & thresholds.window_id.eq(window)]
    retained = transitions[transitions.candidate.eq(candidate) & transitions.window_id.eq(window)]
    if len(calibrator) != 1 or len(threshold) != 1:
        raise ValueError("Unambiguous retained calibrator and threshold required")
    if len(retained) != 4 or set(retained.producer_role) != set(ROLES):
        raise ValueError("All four retained availability transitions are required")
    future_checks = []
    for row in retained.itertuples():
        future_checks.append(
            availability_transition(
                pd.Series([row.producer_target_max]),
                pd.Series(calendar["origins"]),
                dependencies={
                    **json.loads(row.dependencies),
                    "retained_effective": row.effective_availability,
                },
                producer=row.producer_role,
                consumer="proposed_reserved_prediction",
            )
        )
    if components["selected_id"] != calibrator[0]["selected_configuration_id"] or (
        components["selected_id"] != threshold.iloc[0].selected_configuration_id
    ):
        raise ValueError("Retained configuration, calibration and threshold disagree")
    return dict(
        calendar,
        candidate=candidate,
        retained_internal_components=components,
        retained_internal_components_fingerprint=fingerprint(component_path),
        retained_calibrator=calibrator[0],
        retained_threshold=threshold.astype(object)
        .where(threshold.notna(), None)
        .to_dict("records")[0],
        retained_component_availability_checks=future_checks,
        future_outer_model="refit_same_family_and_selected_parameters_on_permitted_training_rows",
        future_preparer={
            "spec": preparer["spec"],
            "input_columns": preparer["input_columns"],
            "policy": (
                "fit_same_approved_spec_on_final_training_X_only; "
                "never_reuse_old_learned_statistics"
            ),
        },
        provenance={
            name: fingerprint(bundle / name)
            for name in (
                component_path.name,
                preparer_path.name,
                "calibrators.json",
                "threshold_selection.csv",
                "availability_transitions.csv",
            )
        },
    )


def freeze_proposal(
    bundle: Path,
    contract: dict[str, Any],
    municipality_codes: list[str],
) -> dict[str, Any]:
    """Specify all six procedures independently of development ranking or utility.

    Args:
        bundle: Current scientifically verified development input.
        contract: Owned evaluation protocol, including pending final scientific rules.
        municipality_codes: Exact common population derived from verified development keys.

    Returns:
        Immutable proposal with six component lineages and zero executed final fits.

    Raises:
        ValueError: For missing combinations, ambiguous components or late availability.
    """
    if sorted(contract["proposed_final"]["families"]) != sorted(FAMILIES):
        raise ValueError("All three unchanged approved families are required")
    if (
        len(municipality_codes) != 76
        or len(set(municipality_codes)) != 76
        or any(len(code) != 5 or not code.isdigit() for code in municipality_codes)
    ):
        raise ValueError("Exactly76 unique canonical municipality codes required")
    calibrators = json.loads((bundle / "calibrators.json").read_text())["calibrators"]
    thresholds = pd.read_csv(bundle / "threshold_selection.csv", float_precision="round_trip")
    transitions = pd.read_csv(bundle / "availability_transitions.csv", dtype="string")
    procedures = [
        _retained_procedure(bundle, family, horizon, contract, calibrators, thresholds, transitions)
        for horizon, family in product((1, 2), FAMILIES)
    ]
    return {
        "schema": "stage5-six-procedure-proposal-v2",
        "status": "pending_human_authorization",
        "gates": {"G4": "OPEN", "G5": "NOT_APPROVED", "reserved_access": "NOT_AUTHORIZED"},
        "rules": contract,
        "procedures": procedures,
        "common_population": sorted(municipality_codes),
        "expected_target_rows_per_procedure": 912,
        "reference": "persistence_on_the_same76_municipality_origin_target_keys_per_horizon",
        "new_fit_budget_after_explicit_acceptance": {
            "outer_models": 6,
            "preparers": 6,
            "hyperparameter_search": 0,
            "calibrators": 0,
            "threshold_selection": 0,
        },
        "fit_budget_consumed": 0,
        "reserved_rows_read": 0,
        "transfer_limitation": (
            "Retained calibration and threshold transfer to newly fitted outer models; "
            "no production calibration claim."
        ),
        "required_human_decision": (
            "Accept G4 and the exact proposed final recommendation/acceptance/uncertainty/"
            "cohort rules before reserved access; authorize future fits separately. "
            "No automatic G5."
        ),
    }
