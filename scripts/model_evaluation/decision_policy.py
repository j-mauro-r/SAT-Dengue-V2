"""Validated single source for Stage 5 champion-decision policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

POLICY_PATH = Path("docs/product/stage-5/champion_decision_policy_v1.json")


class DecisionPolicyError(ValueError):
    """The human-owned Stage 5 decision policy is invalid."""


@dataclass(frozen=True)
class Stage5Knobs:
    """Human-adjustable utility tolerances expressed in percentage points.

    Args:
        max_false_alarm_increase_pp: Allowed false-alert-ratio increase versus persistence.
        min_onset_sensitivity_gain_pp: Required onset-sensitivity gain versus persistence.
        seed: Reproducibility seed for deterministic evaluation components.
    """

    max_false_alarm_increase_pp: float
    min_onset_sensitivity_gain_pp: float
    seed: int

    @property
    def max_false_alarm_increase(self) -> float:
        """Return maximum false-alarm increase in proportion units."""
        return self.max_false_alarm_increase_pp / 100.0

    @property
    def min_onset_sensitivity_gain(self) -> float:
        """Return minimum onset-sensitivity gain in proportion units."""
        return self.min_onset_sensitivity_gain_pp / 100.0


@dataclass(frozen=True)
class ChampionDecisionPolicy:
    """Validated human-owned Stage 5 decision configuration."""

    raw: dict[str, Any]
    knobs: Stage5Knobs
    path: Path


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
    if not isinstance(raw, dict) or raw.get("schema") != "stage5-champion-decision-policy-v1":
        raise DecisionPolicyError("Unsupported Stage 5 decision-policy schema")

    utility = raw.get("utility")
    if not isinstance(utility, dict):
        raise DecisionPolicyError("Decision policy requires utility settings")
    max_far = utility.get("max_false_alarm_increase_pp")
    min_onset = utility.get("min_onset_sensitivity_gain_pp")
    seed = utility.get("seed")
    if isinstance(max_far, bool) or not isinstance(max_far, (int, float)):
        raise DecisionPolicyError("max_false_alarm_increase_pp must be numeric")
    if isinstance(min_onset, bool) or not isinstance(min_onset, (int, float)):
        raise DecisionPolicyError("min_onset_sensitivity_gain_pp must be numeric")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise DecisionPolicyError("seed must be an integer")
    if not 0.0 <= float(max_far) <= 100.0:
        raise DecisionPolicyError("max_false_alarm_increase_pp must be within [0, 100]")
    if not 0.0 <= float(min_onset) <= 100.0:
        raise DecisionPolicyError("min_onset_sensitivity_gain_pp must be within [0, 100]")

    ranking = raw.get("ranking")
    expected_ranking = {
        "scope": "separate_by_horizon",
        "eligible_candidates_only": True,
        "primary_metric": "average_precision",
        "population": "full_declared_annual_reserved_cohort",
        "tie_rule": "exact_ties_require_human_decision",
        "auroc_role": "complementary_only",
        "none_eligible": "no_champion",
    }
    if ranking != expected_ranking:
        raise DecisionPolicyError("Unsupported champion ranking policy")

    thresholds = raw.get("alert_thresholds")
    if not isinstance(thresholds, dict) or thresholds.get("source") != (
        "retained_procedure_artifacts"
    ):
        raise DecisionPolicyError("Alert thresholds must come from retained artifacts")
    if thresholds.get("manual_override_allowed_for_scientific_reclassification") is not False:
        raise DecisionPolicyError(
            "Manual threshold overrides cannot reclassify scientific evidence"
        )

    disposition = raw.get("human_disposition")
    if not isinstance(disposition, dict):
        raise DecisionPolicyError("Decision policy requires human_disposition")
    if disposition.get("G5") != "NOT_APPROVED" or disposition.get("champion") != ("not_selected"):
        raise DecisionPolicyError("Current human disposition must preserve no approved champion")
    if disposition.get("authority") != "Mauricio" or not disposition.get("decided_on"):
        raise DecisionPolicyError("Human disposition requires authority and date")

    mvp = raw.get("mvp_boundary")
    if not isinstance(mvp, dict) or (
        mvp.get("champion_required_for_read_only_mvp") is not False
        or mvp.get("operational_model_integration_allowed") is not False
        or mvp.get("required_display_status") != "NOT_APPROVED"
    ):
        raise DecisionPolicyError("Read-only MVP boundary cannot imply champion approval")

    return ChampionDecisionPolicy(
        raw=raw,
        knobs=Stage5Knobs(
            max_false_alarm_increase_pp=float(max_far),
            min_onset_sensitivity_gain_pp=float(min_onset),
            seed=seed,
        ),
        path=resolved,
    )
