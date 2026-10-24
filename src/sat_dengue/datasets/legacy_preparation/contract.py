"""Preparation configuration and predictor boundary, separate from source definitions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sat_dengue.training_preparation.contract import PreparationError as PreparationError
from sat_dengue.training_preparation.contract import validate_predictors as validate_predictors

CONTRACT_PATH = Path("docs/product/stage-3/training_preparation_contract_v1.json")
UPSTREAM_DIR = Path("data/interim/stage2_consolidated_dataset_pipeline")


@dataclass(frozen=True)
class PreparationConfig:
    """Configure read-only preparation.

    Args:
        root: Repository root containing existing notebook 03 products.
        contract_path: Repository-relative preparation contract path.
        manifest_path: Repository-relative construction manifest path.
    """

    root: Path
    contract_path: Path = CONTRACT_PATH
    manifest_path: Path = UPSTREAM_DIR / "execution_manifest.json"

    def resolve(self, relative: str | Path) -> Path:
        """Resolve an input within the repository, rejecting escapes.

        Args:
            relative: Repository-relative path.

        Returns:
            Resolved input path.

        Raises:
            PreparationError: If the path escapes the repository.
        """
        root = self.root.resolve()
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise PreparationError(f"Input outside repository: {relative}")
        return path


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object without changing its file.

    Args:
        path: Existing JSON path.

    Returns:
        Parsed object.

    Raises:
        PreparationError: If the root is not an object.
    """
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise PreparationError(f"Expected JSON object: {path}")
    return value
