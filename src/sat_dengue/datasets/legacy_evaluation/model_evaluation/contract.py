"""Stage 5 configuration helpers for calibration and threshold selection."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sat_dengue.datasets.legacy_training.contract import ModelTrainingConfig
from sat_dengue.model_evaluation.contract import ModelEvaluationError as ModelEvaluationError
from sat_dengue.model_evaluation.contract import Stage5Contract as Stage5Contract
from sat_dengue.model_evaluation.contract import _as_month_list as _as_month_list
from sat_dengue.model_evaluation.contract import _as_month_range as _as_month_range
from sat_dengue.model_evaluation.contract import (
    _validate_window_role_calendar as _validate_window_role_calendar,
)

from .decision_policy import ChampionDecisionPolicy as ChampionDecisionPolicy
from .decision_policy import Stage5Knobs as Stage5Knobs
from .decision_policy import load_decision_policy

CONTRACT_PATH = Path("docs/product/stage-5/probability_calibration_thresholds_contract_v1.json")
STAGE4_CONTRACT_PATH = Path("docs/product/stage-4/model_engineering_contract_v1.json")
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")
WINDOW_RE = re.compile(r"^\d{4}-\d{2}_t[12]$")


@dataclass(frozen=True)
class ModelEvaluationConfig:
    """Repository-scoped Stage 5 configuration.

    Args:
        root: Repository root containing AGENTS.md and pyproject.toml.
        contract_path: Stage 5 calibration/threshold contract path.
    """

    root: Path
    contract_path: Path = CONTRACT_PATH

    def resolve(self, relative: str | Path) -> Path:
        """Resolve a repository-relative path while rejecting escapes."""
        root = self.root.resolve()
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ModelEvaluationError(f"Path outside repository: {relative}")
        return path

    def stage4_config(self) -> ModelTrainingConfig:
        """Return the Stage 4 configuration anchored at this repository root."""
        return ModelTrainingConfig(self.root, contract_path=STAGE4_CONTRACT_PATH)


def resolve_root(start: Path | None = None) -> Path:
    """Locate repository root from current or provided anchor path."""
    anchor = (start or Path.cwd()).resolve()
    for candidate in (anchor, *anchor.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise ModelEvaluationError("Run from within the repository")


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ModelEvaluationError(f"Expected JSON object: {path}")
    return value


def load_contract(config: ModelEvaluationConfig) -> Stage5Contract:
    """Load and validate Stage 5 contract knobs and temporal partitions."""
    raw = read_json(config.resolve(config.contract_path))
    policy_path = raw.get("decision_policy_path")
    if not isinstance(policy_path, str):
        raise ModelEvaluationError("Stage5 contract requires decision_policy_path")
    decision_policy = load_decision_policy(config.root, policy_path)

    reserved_start = raw.get("reserved_final_block_start")
    if not isinstance(reserved_start, str) or MONTH_RE.match(reserved_start) is None:
        raise ModelEvaluationError("reserved_final_block_start must be YYYY-MM")

    candidate_families = raw.get("candidate_families")
    if candidate_families != ["xgboost", "lightgbm", "gam"]:
        raise ModelEvaluationError(
            "candidate_families must be exactly ['xgboost', 'lightgbm', 'gam'] for delivery1"
        )

    _validate_window_role_calendar(raw, reserved_start)

    return Stage5Contract(
        raw=raw,
        knobs=decision_policy.knobs,
        decision_policy=decision_policy,
    )
