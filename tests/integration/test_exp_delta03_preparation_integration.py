"""Real Kedro lifecycle and catalog materialization using generated data only."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from sat_dengue.configuration import validate_parameters
from sat_dengue.datasets import exp_delta03 as adapter
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


def test_real_kedro_synthetic_catalog_and_repeat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = adapter.publish
    monkeypatch.setattr(
        adapter, "publish", lambda root, relative, payloads: original(tmp_path, relative, payloads)
    )
    bootstrap_project(ROOT)
    for _ in range(2):
        with KedroSession.create(
            project_path=ROOT,
            runtime_params={"profile": "exp_delta03_synthetic", "tracking": "disabled"},
        ) as session:
            cast(KedroSession, session).run(
                pipeline_names=["exp_delta03_synthetic"], node_names=["exp_delta03_generated_probe"]
            )
    products = list((tmp_path / "tmp/exp-delta03-phase1/synthetic").glob("*/manifest.json"))
    assert len(products) == 1
    receipt = json.loads((products[0].parent / "synthetic.json").read_text())
    assert receipt["fits"] == receipt["calibrations"] == receipt["mlflow_writes"] == 0


@pytest.mark.parametrize(
    "profile", ["exp_delta03_preflight", "exp_delta03_preparation", "exp_delta03_synthetic"]
)
def test_tracking_and_scientific_ids_are_rejected(profile: str) -> None:
    for changes in [{"tracking": "enabled"}, {"experiment_id": "EXP03"}]:
        with pytest.raises(ValueError):
            validate_parameters({"profile": profile, "tracking": "disabled", **changes})


def test_historical_graphs_and_source_boundaries_preserved() -> None:
    graphs = register_pipelines()
    assert "exp_delta03" in graphs
    assert graphs["exp_delta03"].inputs() == {"parameters"}
    assert graphs["__default__"] is graphs["foundation"]
    assert not any(
        "exp_delta03" in n.name
        for key in ["replay", "exp01", "exp02", "exp03"]
        for n in graphs[key].nodes
    )
    assert graphs["exp_delta03_synthetic"].inputs() == {"parameters"}
    assert graphs["exp_delta03_preflight"].outputs() == {"exp_delta03_admission"}


def test_real_kedro_preparation_on_generated_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib.util

    from sat_dengue.data.exp_delta03 import normalize

    spec = importlib.util.spec_from_file_location(
        "delta03_generated_support", ROOT / "tests/unit/test_exp_delta03_preparation.py"
    )
    assert spec and spec.loader
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    frame, contract, dictionary = support.fixture()
    sources = {
        "frame": normalize(frame),
        "contract": contract,
        "dictionary": dictionary,
        "receipt": {"sha256": "generated", "rows": len(frame)},
    }
    monkeypatch.setattr(adapter.Delta03SourcesDataset, "load", lambda self: sources)
    original = adapter.publish
    monkeypatch.setattr(
        adapter, "publish", lambda root, relative, payloads: original(tmp_path, relative, payloads)
    )
    bootstrap_project(ROOT)
    with KedroSession.create(
        project_path=ROOT,
        runtime_params={"profile": "exp_delta03_preparation", "tracking": "disabled"},
    ) as session:
        cast(KedroSession, session).run(pipeline_names=["exp_delta03_preparation"])
    products = list((tmp_path / "tmp/exp-delta03-phase1/products").glob("*/manifest.json"))
    assert len(products) == 1
    ready = json.loads((products[0].parent / "readiness.json").read_text())
    assert ready["matrix_files_published"] == 0 and ready["phase1_complete"] is False
    assert (products[0].parent / "quality.json").is_file()


def test_real_kedro_authorized_retrospective_matrix_and_immutable_repeat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "delta03_retrospective_support", ROOT / "tests/unit/test_exp_delta03_retrospective.py"
    )
    assert spec and spec.loader
    support = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    sources = support.retrospective_fixture()
    monkeypatch.setattr(adapter.Delta03SourcesDataset, "load", lambda self: sources)
    original = adapter.publish
    monkeypatch.setattr(
        adapter, "publish", lambda root, relative, payloads: original(tmp_path, relative, payloads)
    )
    bootstrap_project(ROOT)
    for _ in range(2):
        with KedroSession.create(
            project_path=ROOT,
            runtime_params={"profile": "exp_delta03_preparation", "tracking": "disabled"},
        ) as session:
            cast(KedroSession, session).run(pipeline_names=["exp_delta03_preparation"])
    products = list((tmp_path / "tmp/exp-delta03-phase1/products").glob("*/manifest.json"))
    assert len(products) == 1
    ready = json.loads((products[0].parent / "readiness.json").read_text())
    assert ready["scientific_preparation_ready"] and not ready["operational_PIT"]
    assert ready["matrix_files_published"] == 1 and ready["fits"] == 0
    assert (products[0].parent / "prepared_features.csv").is_file()
