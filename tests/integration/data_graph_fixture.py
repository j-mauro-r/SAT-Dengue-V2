"""Stage 2 graph contracts and independent negative input/publication cases."""

from __future__ import annotations

from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets import ConfigurationInputsDataset

ROOT = Path(__file__).resolve().parents[2]


def synthetic_resolved() -> dict:
    from sat_dengue.data.consolidation import compute_schema_contract
    from sat_dengue.pipelines.data.nodes import resolve_data_configuration

    construction = compute_schema_contract([], pd.DataFrame(), version="candidate-construction-v1")
    return resolve_data_configuration(
        ConfigurationInputsDataset().load(),
        {"profile": "data", "tracking": "disabled"},
        {"construction": construction},
    )
