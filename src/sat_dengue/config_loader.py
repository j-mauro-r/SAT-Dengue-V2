"""Validate merged YAML and runtime overrides before Kedro creates datasets."""

from __future__ import annotations

from typing import Any

from kedro.config import OmegaConfigLoader

from sat_dengue.configuration import validate_parameters

CATALOG = {
    "configuration_inputs": {"type": "sat_dengue.datasets.ConfigurationInputsDataset"},
    "resolved_configuration": {
        "type": "sat_dengue.datasets.stage2.PublishedConfigurationDataset",
        "filepath": "tmp/kedro-migration/runs",
    },
    "stage2_sources": {"type": "sat_dengue.datasets.stage2.Stage2SourcesDataset"},
    "stage2_epi_raw": {
        "type": "sat_dengue.datasets.stage2.Stage2RawCsvDataset",
        "filepaths": ["data/raw/dengue.csv", "data/raw/dengue_grave.csv"],
        "chunksize": 200000,
        "epidemiology": True,
    },
    "stage2_climate_raw": {
        "type": "sat_dengue.datasets.stage2.Stage2RawCsvDataset",
        "filepaths": ["data/raw/google_earth_engine.csv"],
        "chunksize": 250000,
    },
    "stage2_consolidated": {
        "type": "sat_dengue.datasets.stage2.Stage2ConsolidatedDataset",
        "filepath": "tmp/kedro-migration/data-runs",
    },
    "stage2_bundle": {
        "type": "sat_dengue.datasets.stage2.Stage2BundleDataset",
        "filepath": "tmp/kedro-migration/data-runs",
    },
}


class ValidatedConfigLoader(OmegaConfigLoader):
    """Allow only the operational catalog exercised by implemented pipelines."""

    def __getitem__(self, key: str) -> dict[str, Any]:
        value = super().__getitem__(key)
        if key == "parameters":
            return validate_parameters(value)
        if key == "catalog" and value != CATALOG:
            raise ValueError(
                "Catalog overrides cannot replace authority inputs or snapshot storage"
            )
        return value
