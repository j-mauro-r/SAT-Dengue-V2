"""Validate merged YAML and runtime overrides before Kedro creates datasets."""

from __future__ import annotations

from typing import Any

from kedro.config import OmegaConfigLoader

from sat_dengue.configuration import validate_parameters

CATALOG = {
    "configuration_inputs": {"type": "sat_dengue.datasets.ConfigurationInputsDataset"},
    "resolved_configuration": {
        "type": "sat_dengue.datasets.ImmutableConfigurationDataset",
        "filepath": "tmp/kedro-migration/runs",
    },
}


class ValidatedConfigLoader(OmegaConfigLoader):
    """Allow only the configuration exercised by the foundation pipeline."""

    def __getitem__(self, key: str) -> dict[str, Any]:
        value = super().__getitem__(key)
        if key == "parameters":
            return validate_parameters(value)
        if key == "catalog" and value != CATALOG:
            raise ValueError(
                "Catalog overrides cannot replace authority inputs or snapshot storage"
            )
        return value
