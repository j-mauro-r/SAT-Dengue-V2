"""Kedro node boundaries with whole-branch real-fit denial for replay."""

from typing import Any

from sat_dengue.datasets.training import assemble_training_payloads
from sat_dengue.datasets.training_legacy import no_fitting
from sat_dengue.model_training.workflow import (
    fit_synthetic,
    replay_components,
    resolve_replay_configuration,
    resolve_synthetic_configuration,
    synthetic_cases,
)


def replay(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    with no_fitting():
        return replay_components(sources, resolved)


__all__ = [
    "assemble_training_payloads",
    "fit_synthetic",
    "resolve_replay_configuration",
    "resolve_synthetic_configuration",
    "synthetic_cases",
    "replay",
]
