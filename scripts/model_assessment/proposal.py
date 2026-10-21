"""Reviewable final-procedure proposal, deliberately without gate authorization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.training_preparation.pipeline import fingerprint

from .policy import proposed_calendar


def freeze_proposal(
    bundle: Path, decisions: pd.DataFrame, contract: dict[str, Any]
) -> dict[str, Any]:
    """Bind deterministic component reuse to a pending human scientific decision.

    Args:
        bundle: Verified corrected development input.
        decisions: Separate AP ranking and fixed point utility results.
        contract: Proposed final rules, not authorization.

    Returns:
        Complete proposal with exact source configurations and no invented final fits.
    """
    procedures = []
    calibrators = json.loads((bundle / "calibrators.json").read_text())["calibrators"]
    thresholds = pd.read_csv(bundle / "threshold_selection.csv", float_precision="round_trip")
    for horizon in (1, 2):
        eligible = decisions[
            decisions.horizon.eq(horizon)
            & decisions.point_utility.eq("meets_point_criteria")
            & np.isfinite(decisions.descriptive_ap_rank)
        ]
        eligible = eligible.sort_values(["descriptive_ap_rank", "candidate"])
        calendar = proposed_calendar(horizon, contract["proposed_final"])
        if eligible.empty:
            procedures.append(
                dict(
                    calendar,
                    candidate=None,
                    reason="no_candidate_has_evaluable_AP_and_meets_point_criteria",
                )
            )
            continue
        if (
            len(eligible) > 1
            and eligible.iloc[0].descriptive_ap_rank == eligible.iloc[1].descriptive_ap_rank
        ):
            procedures.append(
                dict(calendar, candidate=None, reason="exact_AP_tie_requires_human_choice")
            )
            continue
        candidate = str(eligible.iloc[0].candidate)
        window = calendar["retained_internal_window"]
        component_path = bundle / f"{candidate}_{window}_internal_components.json"
        components = json.loads(component_path.read_text())
        calibrator = [
            r for r in calibrators if r["candidate"] == candidate and r["window_id"] == window
        ]
        threshold = thresholds[thresholds.candidate.eq(candidate) & thresholds.window_id.eq(window)]
        if len(calibrator) != 1 or len(threshold) != 1:
            raise ValueError("Unambiguous retained calibrator and threshold required")
        procedures.append(
            dict(
                calendar,
                candidate=candidate,
                retained_internal_components=components,
                retained_internal_components_fingerprint=fingerprint(component_path),
                retained_calibrator=calibrator[0],
                retained_threshold=threshold.astype(object)
                .where(threshold.notna(), None)
                .to_dict(orient="records")[0],
                future_outer_model="refit_same_family_and_selected_parameters_on_permitted_training_rows",
                future_preparer="fit_same_approved_profile_on_outer_training_X_only",
            )
        )
    return {
        "schema": "stage5-final-procedure-proposal-v1",
        "status": "pending_human_authorization",
        "gates": {"G4": "OPEN", "G5": "NOT_APPROVED", "reserved_access": "NOT_AUTHORIZED"},
        "rules": contract,
        "procedures": procedures,
        "new_fit_budget_after_explicit_acceptance": {
            "outer_models": sum(p["candidate"] is not None for p in procedures),
            "preparers": sum(p["candidate"] is not None for p in procedures),
            "hyperparameter_search": 0,
            "calibrators": 0,
            "threshold_selection": 0,
        },
        "fit_budget_consumed": 0,
        "reserved_rows_read": 0,
        "transfer_limitation": (
            "Retained calibration and threshold transfer to a newly fitted "
            "outer model; no production calibration claim."
        ),
        "required_human_decision": (
            "Accept G4, exact proposal identity, candidate/acceptance/uncertainty/"
            "calendar/cohort rules and reserved access; no automatic G5 approval."
        ),
    }
