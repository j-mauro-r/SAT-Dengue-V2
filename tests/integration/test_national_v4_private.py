"""Opt-in private Kedro V4 acceptance; default CI deselects this construction."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import FrameType
from typing import Any

import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project
from kedro.io import DatasetError

from sat_dengue.canonical.national_v4 import DATASET
from sat_dengue.configuration import canonical_bytes
from sat_dengue.datasets.canonical import verify_records
from sat_dengue.datasets.national_v4 import (
    V4BundleDataset,
    V4SourcesDataset,
    assemble_v4,
    read_reference,
)
from sat_dengue.datasets.stage2 import identity
from sat_dengue.training_preparation.serialization import bytes_record

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.migration_evidence
def test_private_v4_kedro_publication_and_fresh_raw_reproduction(repo_tmp_path: Path) -> None:
    """Publish once, independently reconstruct raw sources, verify bytes and refuse replacement."""
    os.environ["KEDRO_DISABLE_TELEMETRY"] = "1"
    output = ROOT / "data/processed" / DATASET
    before = set(output.iterdir()) if output.exists() else set()
    denied: list[str] = []

    def no_adjustments(frame: FrameType, event: str, arg: Any) -> None:
        if event != "call":
            return
        name = frame.f_code.co_name
        module = frame.f_globals.get("__name__", "")
        if name in {
            "fit",
            "fit_transform",
            "partial_fit",
            "train",
            "fit_training_partition",
            "fit_preparer",
            "fit_calibrator",
            "select_threshold",
            "choose_champion",
        } or (
            module.startswith("mlflow")
            and name
            in {
                "start_run",
                "create_run",
                "set_experiment",
                "create_experiment",
                "log_artifact",
                "log_artifacts",
                "log_model",
                "log_metric",
                "log_metrics",
                "log_param",
                "log_params",
                "log_batch",
            }
        ):
            denied.append(f"{module}.{name}")
            raise AssertionError(f"V4 attempted a forbidden scientific/tracking call: {denied[-1]}")

    old_profile = sys.getprofile()
    try:
        # Call-level guard covers the actual Kedro graph and the independent raw rebuild.
        sys.setprofile(no_adjustments)
        bootstrap_project(ROOT)
        session = KedroSession.create(
            project_path=ROOT,
            save_on_close=False,
            runtime_params={"profile": DATASET, "tracking": "disabled"},
        )
        with session:
            session.run(pipeline_names=[DATASET])
        created = set(output.iterdir()) - before
        assert len(created) == 1
        published = created.pop()
        manifest = json.loads((published / "manifest.json").read_text())
        body = {k: v for k, v in manifest.items() if k != "bundle_id"}
        assert (
            bytes_record(canonical_bytes(body))["sha256"] == published.name == manifest["bundle_id"]
        )
        for name, expected in manifest["files"].items():
            assert identity(published / name) == expected
        sources = V4SourcesDataset().load()
        recomputed = assemble_v4(sources, {"profile": DATASET, "tracking": "disabled"})
        for name in (
            DATASET + ".csv",
            "columns.json",
            "contract.json",
            "parity.json",
            "temporal_roles.csv",
        ):
            assert (published / name).read_bytes() == recomputed["payloads"][name], name
        table, columns = read_reference(str(published.relative_to(ROOT)), DATASET)
        assert table.shape == (196350, 95) and len(columns) == 95
        assert not table.duplicated(["municipality_code", "year_month"]).any()
        assert table.groupby("municipality_code").year_month.nunique().eq(175).all()
        assert table.year_month.min() == "2011-06" and table.year_month.max() == "2025-12"
        assert not {"INI_SIN", "COD_DPTO_R", "COD_MUN_R", "patient_id"} & set(table)
        for h in (1, 2):
            assert table.loc[table[f"target_period_t{h}"].gt("2025-12"), f"y_t{h}"].isna().all()
        publisher = V4BundleDataset(str(repo_tmp_path / "no-overwrite"))
        publisher.save(recomputed)
        assert publisher.load()["manifest"]["table"] == manifest["table"]
        with pytest.raises(DatasetError, match="already exists"):
            publisher.save(recomputed)
        verify_records(sources["provenance"]["sources"])
        verify_records(sources["provenance"]["execution"]["code"])
        assert denied == []
        evidence = {
            "status": "PASS",
            "publication": str(published.relative_to(ROOT)),
            "manifest": manifest,
            "fresh_raw_reproduction": "five deterministic payloads byte-identical",
            "source_and_reference_preservation": "PASS",
            "atomic_no_overwrite": "PASS",
            "real_model_fits": 0,
            "mlflow_writes": 0,
            "forbidden_calls": denied,
        }
        receipt = ROOT / "tmp/canonical-v4/private-acceptance.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_bytes(canonical_bytes(evidence))
    finally:
        sys.setprofile(old_profile)
