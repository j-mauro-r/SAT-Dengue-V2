"""Stage 2 graph contracts and independent negative input/publication cases."""

from __future__ import annotations

import ast
import copy
import json
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
import pytest
from data_graph_fixture import synthetic_resolved
from kedro.io import DatasetError

from sat_dengue.data.validation import validate_panel_keys, validate_stage2_configuration
from sat_dengue.datasets.stage2 import Stage2BundleDataset
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


def test_data_graph_has_explicit_snapshot_and_stage_outputs() -> None:
    graph = register_pipelines()["data"]
    assert {
        "configuration_inputs",
        "parameters",
        "stage2_sources",
        "stage2_epi_raw",
        "stage2_climate_raw",
    } == graph.inputs()
    assert graph.outputs() == {"stage2_bundle"}
    assert len(graph.nodes) >= 8
    scientific = [n for n in graph.nodes if n.name != "resolve_data_configuration"]
    assert all("resolved_configuration" in n.inputs for n in scientific)


def test_data_domain_has_no_filesystem_or_framework_dependencies() -> None:
    for path in (ROOT / "src/sat_dengue/data").glob("*.py"):
        tree = ast.parse(path.read_text())
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                assert not {x.name.split(".")[0] for x in item.names} & {
                    "kedro",
                    "mlflow",
                    "pathlib",
                    "os",
                    "subprocess",
                }
            if isinstance(item, ast.ImportFrom):
                assert (item.module or "").split(".")[0] not in {
                    "kedro",
                    "mlflow",
                    "pathlib",
                    "os",
                    "subprocess",
                }
            if isinstance(item, ast.Call):
                assert not (
                    isinstance(item.func, ast.Attribute)
                    and item.func.attr in {"fit", "fit_transform", "partial_fit"}
                )
                assert not (isinstance(item.func, ast.Name) and item.func.id == "open")
                assert not (
                    isinstance(item.func, ast.Attribute)
                    and item.func.attr
                    in {"read_csv", "read_text", "read_bytes", "write_text", "write_bytes"}
                )


@pytest.mark.parametrize("mutation", ["duplicate", "gap", "month", "schema"])
def test_data_rejects_invalid_monthly_panel(mutation: str) -> None:
    frame = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 3,
            "year_month": ["2020-01", "2020-02", "2020-03"],
            "dengue_notifications_count": [0.0, 1.0, 2.0],
        }
    )
    if mutation == "duplicate":
        frame.loc[1, "year_month"] = "2020-01"
    elif mutation == "gap":
        frame = frame.drop(index=1)
    elif mutation == "month":
        frame.loc[1, "year_month"] = "2020-13"
    else:
        frame = frame.drop(columns="dengue_notifications_count")
    with pytest.raises(ValueError):
        validate_panel_keys(frame)


def test_data_rejects_contradictory_scientific_configuration() -> None:

    resolved = synthetic_resolved()
    validate_stage2_configuration(resolved)
    altered = copy.deepcopy(resolved)
    altered["stage2"]["construction"]["target_labeling_policy"]["reference_years"] = 7
    with pytest.raises(ValueError):
        validate_stage2_configuration(altered)


def test_data_bundle_refuses_existing_publication(repo_tmp_path: Path) -> None:
    directory = str(repo_tmp_path)
    dataset = Stage2BundleDataset(directory)

    resolved = synthetic_resolved()
    folder = Path(directory) / resolved["execution"]["run_id"] / "bundle"
    folder.mkdir(parents=True)
    (folder / "manifest.json").write_text("{}")
    with pytest.raises(DatasetError, match="exists"):
        dataset.save({"resolved": resolved})
    assert json.loads((folder / "manifest.json").read_text()) == {}


def test_data_rejects_wrong_source_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.datasets.stage2 import NATIVE_MANIFEST, Stage2SourcesDataset

    path = tmp_path / NATIVE_MANIFEST
    path.parent.mkdir(parents=True)
    path.write_text('{"inputs": "wrong"}')
    monkeypatch.chdir(tmp_path)
    with pytest.raises(DatasetError, match="Incorrect source or manifest"):
        Stage2SourcesDataset().load()


@pytest.mark.parametrize("mutation", ["schema", "source"])
def test_data_consolidation_rejects_wrong_input(mutation: str) -> None:
    from sat_dengue.data.workflow import consolidate

    resolved = synthetic_resolved()
    columns = ["COD_DPTO_R", "COD_MUN_R", "INI_SIN", "ANO"] + [f"f{i}" for i in range(65)]
    resolved["stage2"]["native_manifest"] = {"headers": {"epi_columns": columns}}
    import hashlib

    from sat_dengue.configuration import canonical_bytes

    resolved["configuration_sha256"] = hashlib.sha256(
        canonical_bytes({k: v for k, v in resolved.items() if k != "configuration_sha256"})
    ).hexdigest()
    frame = pd.DataFrame([dict.fromkeys(columns, "")], columns=columns)
    source = "dengue.csv"
    if mutation == "schema":
        frame = frame[list(reversed(columns))]
    else:
        source = "unapproved.csv"
    result = consolidate(
        iter([(source, frame)]),
        pd.DataFrame(),
        pd.DataFrame({"municipality_code": ["50001"]}),
        resolved,
    )
    with pytest.raises(ValueError, match="source/schema"):
        list(result["chunks"])


def test_data_source_drift_fails_before_streaming(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sat_dengue.datasets.stage2 import Stage2RawCsvDataset

    source = tmp_path / "data/raw/dengue.csv"
    source.parent.mkdir(parents=True)
    source.write_text("wrong,header\n1,2\n")
    monkeypatch.chdir(tmp_path)
    with pytest.raises(DatasetError, match="source identity"):
        list(Stage2RawCsvDataset(["data/raw/dengue.csv"], 10, epidemiology=True).load())


def test_data_stream_failure_is_atomic_and_does_not_overwrite(repo_tmp_path: Path) -> None:
    from sat_dengue.datasets.stage2 import Stage2ConsolidatedDataset

    resolved = synthetic_resolved()

    def failing():
        yield pd.DataFrame({"a": [1]})
        raise ValueError("source contract failed")

    directory = str(repo_tmp_path)
    dataset = Stage2ConsolidatedDataset(directory)
    folder = Path(directory) / resolved["execution"]["run_id"]
    with pytest.raises(DatasetError, match="contract failed"):
        dataset.save({"resolved": resolved, "chunks": failing()})
    assert not (folder / "consolidated.csv").exists()
    assert not list(folder.glob(".consolidated-*"))
    dataset.save({"resolved": resolved, "chunks": iter([pd.DataFrame({"a": [1]})])})
    before = (folder / "consolidated.csv").read_bytes()
    with pytest.raises(DatasetError, match="exists"):
        dataset.save({"resolved": resolved, "chunks": iter([pd.DataFrame({"a": [2]})])})
    assert (folder / "consolidated.csv").read_bytes() == before


@pytest.mark.parametrize("mutation", ["original", "engineering", "revision", "expanded"])
def test_data_preservation_mapping_is_closed(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    import subprocess

    from cleanup_support import PRE_CLEANUP
    from migration_support import DATA_ORIGINALS, verify_data_preservation

    tmp_path = repo_tmp_path
    ledger = json.loads((ROOT / "docs/operations/kedro-data-identities.json").read_text())
    for relative in DATA_ORIGINALS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        # This fixture exercises the earlier CLOSED mapping, independently of
        # the live cleanup overlay and its separately authorized current bytes.
        destination.write_bytes(
            subprocess.check_output(["git", "show", f"{PRE_CLEANUP}:{relative}"], cwd=ROOT)
        )
    original = subprocess.check_output

    def git_blob(*args, **kwargs):
        kwargs["cwd"] = ROOT
        return original(*args, **kwargs)

    monkeypatch.setattr(subprocess, "check_output", git_blob)
    path = tmp_path / "docs/operations/kedro-data-identities.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(ledger))
    assert verify_data_preservation(tmp_path, DATA_ORIGINALS) == 2
    name = next(iter(DATA_ORIGINALS))
    if mutation == "original":
        ledger["files"][name]["original"]["sha256"] = "0" * 64
    elif mutation == "engineering":
        (tmp_path / name).write_text("changed")
    elif mutation == "revision":
        ledger["original_revision"] = "HEAD"
    else:
        ledger["files"]["scripts/other.py"] = ledger["files"][name]
    path.write_text(json.dumps(ledger))
    with pytest.raises(AssertionError):
        verify_data_preservation(tmp_path, DATA_ORIGINALS)
