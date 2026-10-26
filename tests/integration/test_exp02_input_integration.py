"""Generated EXP02 admission and catalog connection probe; no real execution."""

from __future__ import annotations

import builtins
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from exp01_inputs_fixture import ROOT, generated_panel, write_sources
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.pipeline import node, pipeline
from kedro.runner import SequentialRunner

from sat_dengue.datasets import exp02 as datasets
from sat_dengue.datasets import stage2
from sat_dengue.datasets.legacy_preparation import contract as preparation
from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.experiments import exp01, exp02
from sat_dengue.experiments import exp02_preflight as checks
from sat_dengue.experiments import exp02_runner as runner
from sat_dengue.pipeline_registry import register_pipelines
from sat_dengue.tracking import exp02 as tracking


def generated_sources(root: Path, *, full_history: bool = False) -> preparation.PreparationConfig:
    """Reuse PR31's source fixture, expanded to EXP02's frozen 76 municipalities."""
    source = generated_panel("2010-01" if full_history else "2024-01", "2025-02")
    codes = [f"{department}{n:03d}" for department in ("50", "73") for n in range(1, 39)]
    panel = pd.concat(
        [
            source.loc[source.department_code.eq(code[:2])].assign(municipality_code=code)
            for code in codes
        ],
        ignore_index=True,
    )
    for column in ("y_t1", "y_t2", "zona_canal_t", "p75_canal_t", "p75_t2"):
        panel[column] = "invalid-unused-legacy-value"
    panel["rain_mm_month_sum"] = panel.rain_mm_month_sum.astype(object)
    panel.loc[panel.year_month.ge("2025-01"), "rain_mm_month_sum"] = "invalid-future-value"
    config = write_sources(root, panel)
    manifest_path = config.resolve(config.manifest_path)
    manifest = json.loads(manifest_path.read_text())
    manifest["coverage"]["scope_municipalities"] = len(codes)
    manifest_path.write_text(json.dumps(manifest))
    config.resolve("data/sources/Divipola-municipios.md").write_text(
        json.dumps(
            {
                "resultado": [
                    {"CODIGO_DPTO_MPIO": code, "CODIGO_DEPARTAMENTO": code[:2]} for code in codes
                ]
            }
        )
    )
    return config


def bind_generated_sources(
    config: preparation.PreparationConfig, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    manifest = str(config.resolve(config.manifest_path).relative_to(ROOT))
    record = fingerprint(ROOT / manifest)
    monkeypatch.setattr(stage2, "NATIVE_MANIFEST", manifest)
    monkeypatch.setattr(stage2, "NATIVE_IDENTITIES", {manifest: record})
    monkeypatch.setattr(checks, "NATIVE_MANIFEST", manifest)
    monkeypatch.setattr(checks, "NATIVE_IDENTITIES", {manifest: record})
    monkeypatch.setattr(
        checks,
        "SOURCE_PATHS",
        tuple(
            str(path.relative_to(ROOT))
            for path in (config.root / "data").rglob("*")
            if path.is_file()
        ),
    )
    monkeypatch.setattr(preparation, "PreparationConfig", lambda root: config)
    return {"sources": checks.descriptor(), "data_version": record["sha256"]}


@pytest.mark.parametrize("fault", [None, "consumed_predictor", "unconsumed_tamper"])
def test_exp02_admission_uses_raw_inputs_and_full_identity(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str | None
) -> None:
    config = generated_sources(repo_tmp_path / "sources")
    if fault:
        path = config.resolve("data/processed/panel_mensual_dengue_clima.csv")
        panel = pd.read_csv(path, dtype="string", keep_default_na=False)
        column = "rain_mm_month_sum" if fault == "consumed_predictor" else "y_t1"
        panel.loc[0, column] = "tampered-value"
        panel.to_csv(path, index=False)
        if fault == "consumed_predictor":
            manifest_path = config.resolve(config.manifest_path)
            manifest = json.loads(manifest_path.read_text())
            manifest["outputs"]["panel_mensual_dengue_clima"].update(fingerprint(path))
            manifest_path.write_text(json.dumps(manifest))
    receipt = bind_generated_sources(config, monkeypatch)
    monkeypatch.setattr(runner, "authorize", lambda value: {"data_version": value["data_version"]})
    if fault:
        match = "rain_mm_month_sum" if fault == "consumed_predictor" else "fingerprint mismatch"
        with pytest.raises(preparation.PreparationError, match=match):
            runner.load_authorized_sources(receipt)
        return
    sources = runner.load_authorized_sources(receipt)
    panel = sources["panel"]
    assert panel.municipality_code.nunique() == 76
    assert panel.year_month.max() == "2024-12"
    assert len(panel.loc[panel.year_month.isin(["2024-11", "2024-12"])]) == 152
    assert not panel.year_month.ge("2025-01").any()
    assert not {"y_t1", "y_t2", "zona_canal_t", "p75_canal_t", "p75_t2"} & set(panel)
    assert all(
        fingerprint(config.resolve(name)) == value
        for name, value in sources["fingerprints"].items()
    )


def test_generated_catalog_admission_ablation_publication_and_tracking(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = generated_sources(repo_tmp_path / "sources", full_history=True)
    bind_generated_sources(config, monkeypatch)
    root = str((repo_tmp_path / "tracking").relative_to(ROOT))
    output = str((repo_tmp_path / "publication").relative_to(ROOT))
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", root)
    monkeypatch.delenv("SAT_DENGUE_EXP02_APPROVAL", raising=False)
    monkeypatch.setattr(checks, "runtime_versions", lambda: {"fixture": "generated"})
    monkeypatch.setattr(checks, "execution_metadata", lambda: {})
    monkeypatch.setattr(tracking, "OUTPUT_ROOT", output)
    events: list[str] = []
    trackers: list[tracking.Exp02Tracking] = []
    original_open, original_path_open = builtins.open, Path.open

    def guard(path: Any) -> None:
        if isinstance(path, (str, Path)):
            resolved = Path(path).resolve()
            assert not resolved.is_relative_to(ROOT / "data"), "Private read forbidden"
            assert not resolved.is_relative_to(ROOT / checks.TRACKING_ROOT), (
                "Permanent MLflow forbidden"
            )
            if resolved.is_relative_to(config.root / "data"):
                assert "authorized_fixture" in events

    def guarded_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        guard(file)
        return original_open(file, *args, **kwargs)

    def guarded_path_open(path: Path, *args: Any, **kwargs: Any) -> Any:
        guard(path)
        return original_path_open(path, *args, **kwargs)

    def authorize_fixture(receipt: dict[str, Any]) -> dict[str, str]:
        assert receipt["tracking"]["root"] == root
        assert receipt["execution_ready"] is False
        assert all(
            receipt[k] == 0 for k in ("private_reads", "writes", "reservations", "mlflow_writes")
        )
        events.append("authorized_fixture")
        # Catalog/preflight constructors already checked the real canonical path.
        # Redirect only the subsequent fixture publication, without relaxing safe_path.
        monkeypatch.setattr(datasets, "OUTPUT_ROOT", output)
        return {"data_version": receipt["data_version"], "fixture": "not an execution approval"}

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Real adjustment or reservation route reached")

    def generated_computation(sources: dict[str, Any]) -> dict[str, Any]:
        assert events == ["authorized_fixture"]
        receipt = sources["preflight"]
        provenance = {
            key: receipt[key]
            for key in ("protocol_sha256", "configuration_sha256", "git_revision", "data_version")
        }
        provenance.update(
            data_sha256=exp01.digest(sources["fingerprints"]),
            code_sha256=exp01.digest({"fixture": "generated"}),
            environment_sha256=exp01.digest({"fixture": "controlled_substitutes"}),
        )
        tracker = tracking.Exp02Tracking(
            "exp02_synthetic", "generated-raw-admission", root, experiment_id="EXP02"
        )
        trackers.append(tracker)
        assert sources["panel"].municipality_code.nunique() == 76
        # Admission above validates all 76; retain PR31's two generated series for
        # the synthetic connection probe to bound frontier computation in CI.
        panel = sources["panel"].loc[sources["panel"].municipality_code.isin(["50001", "73001"])]
        result = exp02.execute(
            panel,
            sources["contract"],
            exp02.load_protocol()["design"],
            fit=exp01.synthetic_fit,
            calibrate=lambda scores, truth, seed: lambda values: values,
            synthetic=True,
        )
        return {"result": result, "provenance": provenance, "tracker": tracker}

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    # Real denial precedes source reads; no approval document is created.
    with pytest.raises(PermissionError):
        runner.load_authorized_sources({})
    assert not events and not (ROOT / root).exists()
    monkeypatch.setattr(runner, "authorize", authorize_fixture)
    monkeypatch.setattr(runner, "reserve_execution", forbidden)
    monkeypatch.setattr(runner, "native_fit", forbidden)
    monkeypatch.setattr(runner, "native_calibration", forbidden)
    monkeypatch.setattr(exp02, "native_fit", forbidden)
    monkeypatch.setattr(exp01, "native_fit", forbidden)
    monkeypatch.setattr(exp01, "native_calibration", forbidden)
    bootstrap_project(ROOT)
    session = KedroSession.create(
        project_path=ROOT,
        save_on_close=False,
        runtime_params={"profile": "exp02", "tracking": "enabled", "experiment_id": "EXP02"},
    )
    with session:
        catalog = session.load_context().catalog
        assert isinstance(catalog.get("exp02_sources"), datasets.Exp02SourcesDataset)
        bundle = catalog.get("exp02_bundle")
        assert isinstance(bundle, datasets.Exp02BundleDataset)
        assert bundle._describe()["filepath"] == str(ROOT / checks.OUTPUT_ROOT)
        bundle._root = ROOT / output
        # Keep the real catalog/preflight/loader; substitute only real execution.
        graph = pipeline(
            [
                *register_pipelines()["exp02"]
                .only_nodes("exp02_preflight", "exp02_authorize_and_load")
                .nodes,
                node(generated_computation, "exp02_authorized_sources", "exp02_bundle"),
            ]
        )
        SequentialRunner().run(graph, catalog)
        publication = catalog.load("exp02_bundle")
    result = tracking.verified_result(publication)["result"]
    assert len(result["children"]) == result["synthetic_interface_fits"] == 108
    assert all(c["status"] == "evaluable" for c in result["children"])
    assert all(
        result[k] == 0 for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits")
    )
    assert result["G5"] == "NOT_APPROVED" and result["champion"] == "not_selected"
    tracker = trackers[0]
    runs = tracker.client.search_runs([tracker.experiment])
    assert len(runs) == 109 and all(r.info.status == "FINISHED" for r in runs)
    children = [r for r in runs if r.data.tags.get("mlflow.parentRunId") == tracker.parent]
    assert len(children) == 108
    assert all(r.data.params["kind"] == "synthetic" for r in runs)
    artifacts = tracker.client.list_artifacts(tracker.parent)
    assert [a.path for a in artifacts] == [tracker.parent + ".json"]
    assert all(not tracker.client.list_artifacts(r.info.run_id) for r in children)
    destination = repo_tmp_path / "download"
    destination.mkdir()
    path = tracker.client.download_artifacts(tracker.parent, artifacts[0].path, str(destination))
    aggregate = json.loads(Path(path).read_text())
    tracking.validate_frontier_artifact(aggregate)
    assert aggregate["parameters"]["bundle_id"] == publication["manifest"]["bundle_id"]
    assert not {"municipality_code", "predictions"} & set(aggregate)
    assert all(set(cell) == tracking.CELL_FIELDS for cell in aggregate["cells"])
    assert not list(repo_tmp_path.rglob("*.reservation"))
