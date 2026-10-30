"""Validate merged YAML and runtime overrides before Kedro creates datasets."""

from __future__ import annotations

from typing import Any

from kedro.config import OmegaConfigLoader

from sat_dengue.configuration import validate_parameters

CATALOG: dict[str, dict[str, Any]] = {
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
    "preparation_sources": {"type": "sat_dengue.datasets.preparation.PreparationSourcesDataset"},
    "saved_preparers": {"type": "sat_dengue.datasets.preparation.SavedPreparersDataset"},
    "preparation_bundle": {
        "type": "sat_dengue.datasets.preparation.PreparationBundleDataset",
        "filepath": "tmp/kedro-migration/preparation-runs",
    },
    "training_sources": {"type": "sat_dengue.datasets.training.TrainingSourcesDataset"},
    "training_bundle": {
        "type": "sat_dengue.datasets.training.TrainingBundleDataset",
        "filepath": "tmp/kedro-migration/training-runs",
    },
    "evaluation_sources": {"type": "sat_dengue.datasets.evaluation.FrozenEvaluationSourcesDataset"},
    "evaluation_bundle": {
        "type": "sat_dengue.datasets.evaluation.EvaluationBundleDataset",
        "filepath": "tmp/kedro-migration/evaluation-runs",
    },
}


# Composed replay retains the existing stage interfaces under explicit namespaces.
for _stage in ("data", "preparation", "training", "evaluation"):
    CATALOG[_stage + ".resolved_configuration"] = {
        "type": "sat_dengue.datasets.replay.ReplayConfigurationDataset"
    }
    _output = {
        "data": "stage2_bundle",
        "preparation": "preparation_bundle",
        "training": "training_bundle",
        "evaluation": "evaluation_bundle",
    }[_stage]
    CATALOG[_stage + "." + _output] = {
        "type": "sat_dengue.datasets.replay.ReplayStageDataset",
        "stage": _stage,
    }
CATALOG["data.stage2_consolidated"] = {
    "type": "sat_dengue.datasets.replay.ReplayConsolidatedDataset"
}
CATALOG["data.stage2_epi_raw"] = {"type": "MemoryDataset", "copy_mode": "assign"}
CATALOG["data.stage2_climate_raw"] = {"type": "MemoryDataset", "copy_mode": "assign"}
CATALOG["replay_bundle"] = {"type": "sat_dengue.datasets.replay.ReplayBundleDataset"}
CATALOG["exp01_sources"] = {"type": "sat_dengue.datasets.exp01.Exp01SourcesDataset"}
CATALOG["exp01_bundle"] = {
    "type": "sat_dengue.datasets.exp01.Exp01BundleDataset",
    "filepath": "tmp/kedro-migration/exp01-runs",
}

CATALOG["exp02_sources"] = {"type": "sat_dengue.datasets.exp02.Exp02SourcesDataset"}
CATALOG["exp02_bundle"] = {
    "type": "sat_dengue.datasets.exp02.Exp02BundleDataset",
    "filepath": "tmp/kedro-migration/exp02-runs",
}

CATALOG["exp03_sources"] = {"type": "sat_dengue.datasets.exp03.Exp03SourcesDataset"}
CATALOG["exp03_bundle"] = {
    "type": "sat_dengue.datasets.exp03.Exp03BundleDataset",
    "filepath": "tmp/kedro-migration/exp03-runs",
}
CATALOG["exp03_1_sources"] = {"type": "sat_dengue.datasets.exp03_1.Exp03_1SourcesDataset"}
CATALOG["exp03_1_bundle"] = {
    "type": "sat_dengue.datasets.exp03_1.Exp03_1BundleDataset",
    "filepath": "tmp/kedro-migration/exp03-1-runs",
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
