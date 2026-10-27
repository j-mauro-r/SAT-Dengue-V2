"""Synthetic rejection tests for preparation boundaries; no private inputs required."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from preparation_test_fixtures import contract as contract

# Milestone 2: exact calendar antecedents and publication boundaries.
from sat_dengue.datasets.legacy_preparation.contract import (
    PreparationError,
)
from sat_dengue.datasets.legacy_preparation.eligibility import policy_from_years
from sat_dengue.datasets.legacy_preparation.persistence import (
    json_bytes,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def synthetic_preparation_graph(contract: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    """Small deterministic full-calendar source; saved states fit solely on train."""
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.training_preparation import workflow
    from sat_dengue.training_preparation.preprocessing import PreparerSpec

    rows = []
    for code in ("50001", "73001"):
        for period in pd.period_range("2006-06", "2024-12", freq="M"):
            row: dict[str, Any] = {
                f["name"]: None if f["nullable"] else 0 for f in contract["schema"]
            }
            row.update(municipality_code=code, year_month=str(period), zona_canal_t="ALERTA")
            for name in contract["roles"]["predictors"]:
                if name != "zona_canal_t":
                    row[name] = float(period.month)
            for h in (1, 2):
                target = str(period + h)
                row[f"target_period_t{h}"] = target
                row[f"y_evaluable_t{h}"] = "2012-01" <= target <= "2024-12"
                row[f"y_t{h}"] = period.month % 2 if row[f"y_evaluable_t{h}"] else pd.NA
            rows.append(row)
    panel = pd.DataFrame(rows)
    sources = {
        "panel": panel,
        "contract": contract,
        "policy": policy_from_years(2007, 2025, "2025-01"),
        "provenance": {},
    }
    inputs = ConfigurationInputsDataset().load()
    saved: dict[str, Any] = {"states": {}, "provenance": {}}
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": "disabled"}, sources, saved
    )
    keys, features = workflow.features(sources, resolved)
    controls, _ = workflow.eligibility(sources, resolved)
    producer, consumer = workflow.boundaries(resolved)
    windows = workflow.partitions(keys, features, controls, sources, resolved, producer, consumer)
    for window, entry in windows.items():
        saved["states"][window] = {}
        for profile, spec in contract["temporal_preparation"]["profiles"].items():
            train = entry["splits"]["train"]
            saved["states"][window][profile] = workflow.fit_training_partition(
                train["X"],
                train["controls"],
                PreparerSpec(**spec),
                list(train["X"]),
                int(window[-1]),
                producer[window],
                "train",
            )
    from sat_dengue.training_preparation.serialization import bytes_record, json_bytes

    saved["provenance"]["state_files"] = {
        f"{w}_{n}_preparer.json": bytes_record(json_bytes(state))
        for w, profiles in saved["states"].items()
        for n, state in profiles.items()
    }
    return inputs, sources, saved, windows


def test_preparation_synthetic_complete_kedro_graph(
    synthetic_preparation_graph: tuple[Any, ...],
) -> None:
    from kedro.io import DataCatalog, MemoryDataset
    from kedro.runner import SequentialRunner

    from sat_dengue.pipelines.preparation.pipeline import create_pipeline

    inputs, sources, saved, _ = synthetic_preparation_graph
    catalog = DataCatalog(
        {
            n: MemoryDataset(v)
            for n, v in {
                "configuration_inputs": inputs,
                "parameters": {"profile": "preparation", "tracking": "disabled"},
                "preparation_sources": sources,
                "saved_preparers": saved,
            }.items()
        }
    )
    output = SequentialRunner().run(create_pipeline(), catalog)["preparation_bundle"].load()
    assert len(output["payloads"]) == 117
    assert len([n for n in output["payloads"] if n.endswith("_preparer.json")]) == 16


@pytest.mark.parametrize(
    "fault", ["Y", "keys", "controls", "X", "window", "producer", "consumer", "state"]
)
def test_preparation_replay_rejects_misalignment_and_boundaries(
    synthetic_preparation_graph: tuple[Any, ...], fault: str
) -> None:
    from sat_dengue.training_preparation import workflow

    inputs, sources, saved, windows = copy.deepcopy(synthetic_preparation_graph)
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": "disabled"}, sources, saved
    )
    producer, consumer = workflow.boundaries(resolved)
    window = "2018-12_t1"
    split = windows[window]["splits"]["train"]
    if fault in ("Y", "keys", "controls", "X"):
        split[fault] = split[fault].iloc[::-1].reset_index(drop=True)
    elif fault == "window":
        windows["2025-01_t1"] = windows.pop(window)
    elif fault == "producer":
        producer[window] = "2025-01"
    elif fault == "consumer":
        consumer[window]["validation"] = "2025-01"
    else:
        saved["states"][window]["native"]["input_columns"] = list(
            reversed(saved["states"][window]["native"]["input_columns"])
        )
    with pytest.raises(PreparationError):
        workflow.replay(windows, saved, resolved, producer, consumer)


def test_preparation_atomic_persistence_and_identity_refusal(
    synthetic_preparation_graph: tuple[Any, ...],
    monkeypatch: pytest.MonkeyPatch,
    repo_tmp_path: Path,
) -> None:

    from kedro.io import DatasetError

    from sat_dengue.datasets import preparation as adapter
    from sat_dengue.training_preparation import workflow

    inputs, sources, saved, windows = synthetic_preparation_graph
    resolved = workflow.resolve_preparation_configuration(
        inputs, {"profile": "preparation", "tracking": "disabled"}, sources, saved
    )
    producer, consumer = workflow.boundaries(resolved)
    transformed = workflow.replay(windows, saved, resolved, producer, consumer)
    keys, features = workflow.features(sources, resolved)
    controls, audit = workflow.eligibility(sources, resolved)
    payload = adapter.bundle_payloads(
        keys, features, controls, audit, transformed, resolved, producer, consumer
    )
    monkeypatch.setattr(adapter, "NATIVE_PREPARATION", {})  # synthetic sources only
    directory = str(repo_tmp_path)
    dataset = adapter.PreparationBundleDataset(directory)
    with pytest.raises(DatasetError):
        dataset.load()
    dataset.save(payload)
    result = dataset.load()
    bundle = ROOT / result["path"]
    assert not list(Path(directory).glob(".staging-*"))
    with pytest.raises(DatasetError, match="already exists"):
        dataset.save(payload)
    path = bundle / "features.csv"
    path.chmod(0o600)
    path.write_bytes(path.read_bytes() + b"corrupt")
    with pytest.raises(DatasetError, match="payload identity"):
        dataset.load()


@pytest.mark.parametrize("fault", ["manifest", "payload", "membership"])
def test_preparation_native_bundle_rejects_identity_drift(fault: str, repo_tmp_path: Path) -> None:

    from kedro.io import DatasetError

    from sat_dengue.datasets import preparation as adapter
    from sat_dengue.training_preparation.serialization import bytes_record

    directory = str(repo_tmp_path)
    bundle = Path(directory) / "explicit-identity"
    bundle.mkdir()
    relative = str(bundle.relative_to(ROOT))
    (bundle / "state.json").write_bytes(b"{}")
    manifest = {"bundle_id": bundle.name, "files": {"state.json": bytes_record(b"{}")}}
    data = json_bytes(manifest)
    (bundle / "manifest.json").write_bytes(data)
    assert adapter.verified_native_bundle(relative, bytes_record(data)) == manifest
    if fault == "manifest":
        (bundle / "manifest.json").write_bytes(data + b" ")
    elif fault == "payload":
        (bundle / "state.json").write_bytes(b"changed")
    else:
        (bundle / "extra").write_bytes(b"extra")
    with pytest.raises(DatasetError):
        adapter.verified_native_bundle(relative, bytes_record(data))
