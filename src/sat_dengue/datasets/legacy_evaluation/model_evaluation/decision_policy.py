"""Validated single source for Stage 5 champion-decision policy."""

from __future__ import annotations

import json
from pathlib import Path

from sat_dengue.model_evaluation.decision_policy import (
    ChampionDecisionPolicy as ChampionDecisionPolicy,
)
from sat_dengue.model_evaluation.decision_policy import DecisionPolicyError as DecisionPolicyError
from sat_dengue.model_evaluation.decision_policy import Stage5Knobs as Stage5Knobs
from sat_dengue.model_evaluation.decision_policy import validate_decision_policy

POLICY_PATH = Path("docs/product/stage-5/champion_decision_policy_v1.json")


def _repository_path(root: Path, relative: str | Path) -> Path:
    """Resolve a repository-relative policy path and reject path escapes."""
    repository = root.resolve()
    path = (repository / relative).resolve()
    if not path.is_relative_to(repository):
        raise DecisionPolicyError(f"Decision policy path outside repository: {relative}")
    return path


def load_decision_policy(root: Path, path: str | Path = POLICY_PATH) -> ChampionDecisionPolicy:
    """Load and validate the single Stage 5 champion-decision policy.

    Args:
        root: Repository root.
        path: Repository-relative policy path.

    Returns:
        Validated decision policy and its human-adjustable utility knobs.

    Raises:
        DecisionPolicyError: If fields, values, or governance boundaries are invalid.
    """
    resolved = _repository_path(root, path)
    try:
        raw = json.loads(resolved.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DecisionPolicyError(f"Cannot read decision policy: {resolved}") from exc
    return validate_decision_policy(raw, resolved)
