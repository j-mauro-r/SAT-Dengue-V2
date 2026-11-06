"""Generated full Kedro execution, native replay and admission failures only."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import cast
from uuid import uuid4

import pytest
from kedro.framework.session import KedroSession
from kedro.framework.startup import bootstrap_project

from sat_dengue.datasets import exp_delta03_training as engine
from sat_dengue.datasets.exp_delta03_execution import verify_publication
from sat_dengue.experiments.exp_delta03_inputs import validate_calendar, validate_national_annex

ROOT = Path(__file__).resolve().parents[2]


def test_full_generated_kedro_and_exact_reload_without_duplicate_adjustments(monkeypatch):
    relative = "tmp/exp-delta03-phase2/synthetic/integration-" + uuid4().hex
    monkeypatch.setattr(engine, "SYNTHETIC_ROOT", relative)

    def private_forbidden(*args, **kwargs):
        raise AssertionError("Synthetic execution attempted private input loading")

    monkeypatch.setattr(engine, "read_metadata", private_forbidden)
    monkeypatch.setattr(engine, "load_authorized_inputs", private_forbidden)
    receipts = []
    original_save = engine.Delta03Phase2ReceiptDataset.save

    def record(self, data):
        receipts.append(data)
        original_save(self, data)

    monkeypatch.setattr(engine.Delta03Phase2ReceiptDataset, "save", record)
    bootstrap_project(ROOT)
    for _ in range(2):
        with KedroSession.create(
            project_path=ROOT,
            runtime_params={"profile": "exp_delta03_synthetic", "tracking": "disabled"},
        ) as session:
            cast(KedroSession, session).run(pipeline_names=["exp_delta03_synthetic"])
    first, replay = receipts
    payloads = verify_publication(ROOT, first["native_publication"], synthetic=True)
    result = json.loads(payloads["result.json"])
    plan = json.loads(payloads["execution-plan.json"])
    count = len(plan["cells"])
    assert first["invocation"] == {
        "model_fits": count,
        "calibrator_fits": count,
        "threshold_selections": count,
    }
    assert replay["invocation"] == {
        "model_fits": 0,
        "calibrator_fits": 0,
        "threshold_selections": 0,
    }
    assert first["native_publication"] == replay["native_publication"]
    assert first["tracking"] == replay["tracking"]
    assert first["tracking"]["runs"] == count + 1
    assert result["counts"]["models"] == count
    assert {c["horizon"] for c in plan["cells"]} == {1, 2}
    assert all(c["year"] < 2025 for c in plan["cells"])
    assert all(
        c["year"] == 2024 and c["variant"] in {"FULL_PLUS_SURFACE_WATER", "WATER_REFERENCE"}
        for c in plan["unsupported"]
    )
    assert any(c["reference"] == "transfer" for c in plan["cells"])
    assert any(c["reference"] == "era5" for c in plan["cells"])
    assert all(ident + ".cohort.csv" in payloads for ident in [c["id"] for c in plan["cells"]])
    assert (
        first["activity_counters"]["real_model_fits"]
        == first["activity_counters"]["real_calibrations"]
        == first["activity_counters"]["permanent_mlflow_writes"]
        == 0
    )
    comparison = json.loads(payloads["comparisons.json"])
    assert comparison["pooled_horizon_metrics"] and comparison["pairs"][0]["paired_onsets"]
    assert {g["stratum"] for g in comparison["uncertainty"]} == {"development", "stress2024"}
    assert all(c["metrics"]["comparators"]["R0"]["rows"] > 0 for c in result["cells"])
    assert first["status"] == "GENERATED_E2E_COMPLETE" and first["phase3_authorized"] is False


def test_real_registered_graph_rejects_before_private_rows_or_fit(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Unauthorized operation")

    monkeypatch.setattr(engine, "read_metadata", forbidden)
    monkeypatch.setattr(engine, "load_authorized_inputs", forbidden)
    from sat_dengue.model_training import exp_delta03_adapter

    monkeypatch.setattr(exp_delta03_adapter, "fit_native", forbidden)
    bootstrap_project(ROOT)
    with KedroSession.create(
        project_path=ROOT, runtime_params={"profile": "exp_delta03", "tracking": "enabled"}
    ) as session:
        with pytest.raises(PermissionError, match="Phase3 authorization"):
            cast(KedroSession, session).run(pipeline_names=["exp_delta03"])


def test_generated_annex_rejects_misalignment_dates_and_duplicate_exposure():
    context = engine.authorize_and_load(
        engine.training_source({"profile": "exp_delta03_synthetic", "tracking": "disabled"})
    )
    cell = next(c for c in context["plan"]["cells"] if c["reference"] == "primary")
    expected = context["national_expected"][cell["id"]]
    part = context["national_annex"][cell["id"]]
    original = context["parts"][cell["id"]]["evaluation"]["rows"]
    validate_national_annex(cell, part, expected, original)
    for mutation in ["date", "X", "keys", "department", "excess"]:
        changed = copy.deepcopy(part)
        if mutation == "date":
            changed["rows"].loc[0, "periodo_mes"] = "2025-01"
        elif mutation == "X":
            changed["X"] = changed["X"].iloc[::-1].reset_index(drop=True)
        elif mutation == "keys":
            changed["rows"].iloc[0] = changed["rows"].iloc[1]
        elif mutation == "department":
            changed["rows"].loc[0, "divipola_departamento"] = "99"
        else:
            rows = changed["rows"]
            index = rows.index[rows.divipola_departamento.isin(["50", "73"]) & rows.truth.eq(0)][0]
            excess = 1 - int(rows.loc[index, "target_excess"])
            rows.loc[index, "target_excess"] = excess
            rows.loc[index, "episode_id"] = "tampered" if excess else None
        with pytest.raises(ValueError):
            validate_national_annex(cell, changed, expected, original)
    calendar = context["calendar"]
    validate_calendar(calendar)
    import pandas as pd  # type: ignore[import-untyped]

    with pytest.raises(ValueError, match="grain"):
        validate_calendar(pd.concat([calendar, calendar.iloc[:1]]))
