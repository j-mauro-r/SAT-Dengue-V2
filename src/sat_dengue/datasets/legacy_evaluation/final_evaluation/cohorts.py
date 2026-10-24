"""Complete final cohorts from unchanged deterministic preparation and scientific labels."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.datasets.legacy_preparation.pipeline import prepare_inputs
from sat_dengue.final_evaluation.cohorts import Cohort as Cohort
from sat_dengue.final_evaluation.cohorts import build_cohorts as build_cohorts
from sat_dengue.final_evaluation.cohorts import expected_index as expected_index
from sat_dengue.final_evaluation.cohorts import validate_cohort as validate_cohort

from .protocol import require_authorization


def load_cohorts(root: Path, proposal: dict[str, Any]) -> tuple[dict[int, Cohort], dict[str, Any]]:
    """Open scientific source values only after explicit authorization succeeds.

    Args:
        root: Repository root.
        proposal: Verified fixed proposal.

    Returns:
        Preflighted cohorts and source fingerprints, without changing inputs.
    """
    require_authorization(root)
    prepared = prepare_inputs(PreparationConfig(root))
    return build_cohorts(prepared.panel, prepared.contract, proposal), prepared.report[
        "input_fingerprints"
    ]
