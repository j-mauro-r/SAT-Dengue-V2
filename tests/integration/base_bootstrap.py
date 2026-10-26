"""Exercise base registration/execution with model imports denied or truly absent."""

from __future__ import annotations

import importlib.abc
import json
import sys
from pathlib import Path
from typing import Any

OPTIONAL = {"sklearn", "lightgbm", "xgboost", "scipy", "threadpoolctl", "narwhals", "mlflow"}


class NoModeling(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> None:
        if fullname.split(".")[0] in OPTIONAL:
            raise ModuleNotFoundError("Modeling dependency unavailable: " + fullname)


def main() -> None:
    sys.meta_path.insert(0, NoModeling())
    from kedro.framework.startup import bootstrap_project
    from kedro.io import DataCatalog, DatasetError, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.pipeline_registry import register_pipelines

    bootstrap_project(Path.cwd())
    pipelines = register_pipelines()
    assert set(pipelines) == {
        "__default__",
        "foundation",
        "data",
        "preparation",
        "training_replay",
        "training_synthetic",
        "evaluation_replay",
        "evaluation_synthetic",
        "replay",
        "replay_synthetic",
        "exp01_synthetic",
        "exp01",
        "exp01_preflight",
    }
    assert pipelines["__default__"] is pipelines["foundation"]
    assert not OPTIONAL.intersection(sys.modules)
    catalog = DataCatalog(
        {
            "configuration_inputs": MemoryDataset(ConfigurationInputsDataset().load()),
            "parameters": MemoryDataset({"profile": "foundation", "tracking": "disabled"}),
            "resolved_configuration": MemoryDataset(),
        }
    )
    SequentialRunner().run(pipelines["foundation"], catalog)
    assert catalog.load("resolved_configuration")["operational"]["profile"] == "foundation"
    for name in (
        "training_synthetic",
        "training_replay",
        "evaluation_synthetic",
        "evaluation_replay",
        "replay",
        "replay_synthetic",
    ):
        # Node boundary and real-source dataset both fail before importing a scientific module.
        first = pipelines[name].nodes[0]
        args: list[dict[str, Any]] = (
            [{}, {}] if (name.endswith("synthetic") or name == "replay") else [{}, {}, {}]
        )
        try:
            first.func(*args)
        except RuntimeError as error:
            assert "sat-dengue-v2[modeling]" in str(error) and "sklearn" in str(error)
        else:
            raise AssertionError("Training unexpectedly ran without modeling dependencies")
    from sat_dengue.datasets.evaluation import FrozenEvaluationSourcesDataset
    from sat_dengue.datasets.training import TrainingSourcesDataset

    try:
        TrainingSourcesDataset().load()
    except DatasetError as error:
        assert "sat-dengue-v2[modeling]" in str(error)
    else:
        raise AssertionError("Native loader did not require modeling")
    try:
        FrozenEvaluationSourcesDataset().load()
    except DatasetError as error:
        assert "sat-dengue-v2[modeling]" in str(error)
    else:
        raise AssertionError("Frozen evaluation did not require modeling")
    assert not OPTIONAL.intersection(sys.modules)
    print(
        json.dumps(
            {
                "status": "PASS",
                "registered": sorted(pipelines),
                "foundation_executed": True,
                "optional_modules_imported": [],
                "training_failure": "explicit modeling extra required",
            }
        )
    )


if __name__ == "__main__":
    main()
