"""Configuration helpers for Stage 4 bounded model-engineering runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONTRACT_PATH = Path("docs/product/stage-4/model_engineering_contract_v1.json")
STAGE3_CONTRACT_PATH = Path("docs/product/stage-3/training_preparation_contract_v1.json")


class ModelTrainingError(ValueError):
    """A Stage 4 model-engineering precondition is violated."""


@dataclass(frozen=True)
class ModelTrainingConfig:
    """Repository-scoped model-training configuration.

    Args:
        root: Repository root containing AGENTS.md and pyproject.toml.
        contract_path: Stage 4 model-engineering contract.
        stage3_contract_path: Stage 3 preparation contract to verify sources.
    """

    root: Path
    contract_path: Path = CONTRACT_PATH
    stage3_contract_path: Path = STAGE3_CONTRACT_PATH

    def resolve(self, relative: str | Path) -> Path:
        """Resolve a repository-relative path while rejecting escapes.

        Args:
            relative: Repository-relative path.

        Returns:
            Absolute normalized path inside the repository.

        Raises:
            ModelTrainingError: If the path escapes the repository.
        """
        root = self.root.resolve()
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ModelTrainingError(f"Path outside repository: {relative}")
        return path


def resolve_root(start: Path | None = None) -> Path:
    """Locate repository root from a working directory anchor.

    Args:
        start: Optional search anchor; defaults to current working directory.

    Returns:
        Repository root path.

    Raises:
        ModelTrainingError: If root markers are not found.
    """
    anchor = (start or Path.cwd()).resolve()
    for candidate in (anchor, *anchor.parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "pyproject.toml").is_file():
            return candidate
    raise ModelTrainingError("Run from within the repository")


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk.

    Args:
        path: Existing JSON file.

    Returns:
        Parsed object.

    Raises:
        ModelTrainingError: If the root is not an object.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ModelTrainingError(f"Expected JSON object: {path}")
    return value
