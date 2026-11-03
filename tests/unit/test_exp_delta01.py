"""Generated-only scientific policy, isolation and publication checks; no estimators."""

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DatasetError

from sat_dengue.datasets.exp_delta01 import DeltaBundleDataset, DeltaSourcesDataset
from sat_dengue.experiments import exp_delta01 as delta
from sat_dengue.pipeline_registry import register_pipelines


def frame(year: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["50001", "50002", "73001", "73002"],
            "department_code": ["50", "50", "73", "73"],
            "year_month": [f"{year}-01"] * 4,
            "target_month": [f"{year}-02"] * 4,
            "truth": [1, 0, 1, 0],
            "target_excess": [1, 0, 1, 0],
            "score": [0.8, 0.8, 0.6, 0.2],
            "alert": [True, True, False, False],
            "channel_alert": [True, True, False, False],
            "persistence_alert": [False] * 4,
            "threshold": [0.8] * 4,
        }
    )


def source(root: Path) -> dict[str, Any]:
    return {
        "protocol": {
            "cohort": {
                "horizons": [1],
                "evaluation_target_years": [2020],
                "expected": {"1": {"rows": 4, "onsets": 2}},
            }
        },
        "cells": [
            {
                "horizon": 1,
                "year": 2020,
                "selection": frame(2019),
                "evaluation": frame(2020),
                "model_identity": {"sha256": "generated"},
                "calibrator_sha256": "generated",
            }
        ],
        "freeze_root": str(root / "freezes"),
        "evidence_type": "synthetic_generated_data",
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }


def test_exact_margin_whole_ties_and_predeclared_tiebreak() -> None:
    assert delta.within_margin(3, 20, 2, 20)  # Exactly +5 percentage points.
    assert not delta.within_margin(4, 20, 2, 20)
    assert not delta.within_margin(0, 0, 2, 20)
    chosen, frontier = delta.choose(frame(2019))
    assert chosen["threshold"] == 0.6  # Two TP, one FP; fewer FP than threshold 0.2.
    assert next(c for c in frontier if c["threshold"] == 0.8)["alerts"] == 2
    assert frontier[0]["far_excess"] is None and not frontier[0]["feasible"]


def test_excess_false_alerts_differ_from_onset_false_alerts() -> None:
    f = frame(2020)
    f.loc[1, "target_excess"] = 1  # A continuation alert is false only for onset.
    metric = delta.counts(f)
    assert metric["false_alerts_onset"] == 1
    assert metric["false_alerts_excess"] == 0
    assert metric["far_excess"] == 0.0
    f["alert"] = False
    assert delta.counts(f)["far_excess"] is None


def test_freeze_is_independent_of_evaluation_and_precedes_application(repo_tmp_path: Path) -> None:
    original = source(repo_tmp_path)
    a = delta.select(original)
    mutated = copy.deepcopy(original)
    mutated["cells"][0]["evaluation"]["truth"] = 1
    mutated["cells"][0]["evaluation"]["score"] = 0.0
    b = delta.select(mutated)
    assert a["freeze"]["payloads"] == b["freeze"]["payloads"]
    path = Path(a["freeze"]["path"]) / "policies.json"
    assert path.exists()
    details = delta.apply(a)["details"]
    p0, p1 = (details.loc[details.arm.eq(arm)] for arm in ("P0", "P1"))
    assert p0.score.tolist() == p1.score.tolist()
    assert p0.truth.tolist() == p1.truth.tolist()
    assert p0.alert.tolist() == [True, True, False, False]
    assert p1.alert.tolist() == [True, True, True, False]


def test_no_feasible_threshold_is_unavailable_not_zero_alerts(repo_tmp_path: Path) -> None:
    s = source(repo_tmp_path)
    s["cells"][0]["selection"]["channel_alert"] = [True, False, False, False]
    chosen, _ = delta.choose(s["cells"][0]["selection"])
    assert chosen["status"] == "NO_EVALUABLE" and chosen["reason"] == "no_feasible_threshold"
    applied = delta.apply(delta.select(s))
    p1 = applied["details"].loc[applied["details"].arm.eq("P1")]
    assert len(p1) == 4 and p1.alert.isna().all()
    result = delta.evaluate(applied)
    assert json.loads(result["payloads"]["conclusions.json"])["hypothesis"] == "NO_EVALUABLE"
    for field in ("truth", "target_excess"):
        broken = frame(2019)
        broken[field] = 0
        assert delta.choose(broken)[0]["reason"] == "insufficient_support"


def test_full_generated_result_reproduces_and_cannot_overwrite(repo_tmp_path: Path) -> None:
    s = delta.prepare(source(repo_tmp_path), {"profile": "exp_delta01", "tracking": "disabled"})
    result = delta.evaluate(delta.apply(delta.select(s)))
    repeated = delta.evaluate(delta.apply(delta.select(s)))
    assert result["payloads"] == repeated["payloads"]
    publisher = DeltaBundleDataset(str(repo_tmp_path / "results"))
    publisher.save(result)
    assert publisher.load()["manifest"]["inference_calls"] == 0
    with pytest.raises(Exception, match="already exists"):
        publisher.save(repeated)
    assert register_pipelines()["exp_delta01"].inputs() == {"exp_delta01_sources", "parameters"}
    assert len(register_pipelines()["exp_delta01"].nodes) == 4


def test_chronology_and_missing_cells_fail_closed(repo_tmp_path: Path) -> None:
    s = source(repo_tmp_path)
    s["cells"][0]["selection"]["target_month"] = "2020-01"
    with pytest.raises(ValueError, match="chronological"):
        delta.prepare(s, {"profile": "exp_delta01", "tracking": "disabled"})
    s["cells"] = []
    with pytest.raises(ValueError, match="Incomplete"):
        delta.prepare(s, {"profile": "exp_delta01", "tracking": "disabled"})


def test_original_embargo_allows_selection_target_equal_to_evaluation_origin(
    repo_tmp_path: Path,
) -> None:
    s = source(repo_tmp_path)
    s["cells"][0]["selection"]["target_month"] = "2019-12"
    s["cells"][0]["evaluation"]["year_month"] = "2019-12"
    assert delta.prepare(s, {"profile": "exp_delta01", "tracking": "disabled"}) is s
    s["cells"][0]["evaluation"]["year_month"] = "2019-11"
    with pytest.raises(ValueError, match="chronological"):
        delta.prepare(s, {"profile": "exp_delta01", "tracking": "disabled"})


def test_protocol_identity_refused_before_private_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sat_dengue.datasets.exp_delta01.PROTOCOL_SHA", "0" * 64)
    with pytest.raises(DatasetError):
        DeltaSourcesDataset().load()
