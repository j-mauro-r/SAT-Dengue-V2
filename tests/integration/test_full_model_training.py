"""Stage 4 reference-pipeline regressions without private datasets."""

from __future__ import annotations


def test_training_synthetic_graph_fits_every_authorized_family() -> None:
    import json

    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.pipelines.training.pipeline import create_synthetic_pipeline

    catalog = DataCatalog(
        {
            "configuration_inputs": MemoryDataset(ConfigurationInputsDataset().load()),
            "parameters": MemoryDataset({"profile": "training_synthetic", "tracking": "disabled"}),
            "training_bundle": MemoryDataset(),
        }
    )
    SequentialRunner().run(create_synthetic_pipeline(), catalog)
    result = catalog.load("training_bundle")
    audit = json.loads(result["payloads"]["audit.json"])
    assert audit["synthetic_model_fits"] == 31
    assert audit["real_model_fits"] == audit["real_preparer_refits"] == 0
    assert audit["G5"] == "NOT_APPROVED" and audit["champion"] == "not_selected"
    for family in ("xgboost", "lightgbm", "gam"):
        model = result["payloads"][family + "_model.json"]
        state = json.loads(result["payloads"][family + "_preparer.json"])
        assert model and len(state["input_columns"]) == 29
        search = json.loads(result["payloads"][family + "_search.json"])
        assert len(search["folds"]) == search["fit_count"] - 1
        assert all(f["boundaries"]["train"]["target_end"] < "2025-01" for f in search["folds"])

    # A second independent bounded search must produce identical native state and predictions.
    SequentialRunner().run(create_synthetic_pipeline(), catalog)
    repeated = catalog.load("training_bundle")
    for family in ("xgboost", "lightgbm", "gam"):
        for suffix in ("_model.json", "_preparer.json", "_predictions.csv"):
            assert result["payloads"][family + suffix] == repeated["payloads"][family + suffix]
