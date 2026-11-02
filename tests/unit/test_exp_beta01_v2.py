"""Generated-only national transfer controls; no real fits or private metrics."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DatasetError
from test_exp_beta01 import cohort
from test_exp_beta01 import protocol as old_protocol

from sat_dengue.canonical.table import PREDICTORS
from sat_dengue.configuration import validate_parameters
from sat_dengue.datasets import exp_beta01_v2 as datasets
from sat_dengue.datasets.legacy_preparation.pipeline import read_panel
from sat_dengue.experiments import exp_beta01_v2 as v2
from sat_dengue.experiments.exp_beta01 import prepare as old_prepare
from sat_dengue.experiments.exp_beta01 import role_parts
from sat_dengue.experiments.onset import KEYS, labels
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def sources() -> dict[str, Any]:
    protocol = json.loads((ROOT / datasets.PROTOCOL).read_text())
    regional = cohort()[[*KEYS, "department_code", *PREDICTORS]].copy()
    regional["zona_canal_t"] = [
        "EXCESO" if i % 4 == 0 else "SEGURIDAD" for i in range(len(regional))
    ]
    columns = {
        "column_roles": {"feature": PREDICTORS, "key": KEYS, "metadata": ["department_code"]}
    }
    base = {"table": regional, "columns": columns, "protocol": old_protocol()}
    old = old_prepare(base, {"profile": "exp_beta01", "tracking": "disabled"})
    frozen = []
    for h, frame in old["cohorts"].items():
        for year in protocol["evaluation_years"]:
            evaluate = role_parts(frame, year, protocol)["parts"]["evaluation"]
            for arm, climate in (("G0", "OFF"), ("R0", "historical")):
                f = (
                    evaluate[
                        [*KEYS, "department_code", "target_month", "target_year", "onset_target"]
                    ]
                    .rename(columns={"onset_target": "truth"})
                    .copy()
                )
                f["arm"], f["climate"], f["horizon"], f["year"] = arm, climate, h, year
                f["score"], f["alert"] = 0.2, False
                frozen.append(f)
    added = regional.loc[regional.department_code.eq("50")].copy()
    added["municipality_code"], added["department_code"] = "05001", "05"
    added.loc[added.year_month.lt("2016-06"), v2.FEATURES] = pd.NA
    table = pd.concat([regional, added], ignore_index=True)
    table["requires_record_review"] = False
    states = table[KEYS].copy()
    states["excess"] = table.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[table.zona_canal_t.isna(), "excess"] = pd.NA
    for h in (1, 2):
        outcomes = labels(states, h)
        table[f"onset_T{h}"] = outcomes.onset_target
        table[f"g1_no_climate_t{h}"] = (
            outcomes.eligible_at_t
            & outcomes.onset_target.notna()
            & table[v2.FEATURES].notna().all(axis=1)
        )
    return {
        "protocol": protocol,
        "regional": base,
        "table": table,
        "national_contract": json.loads(
            (ROOT / "docs/data/canonical_model_table_national_v1.json").read_text()
        ),
        "frozen_predictions": pd.concat(frozen, ignore_index=True),
        "evidence_type": "synthetic_generated_data",
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }


def test_preflight_exact_roles_and_national_training_only(sources: dict[str, Any]) -> None:
    prepared = v2.prepare(sources, {"profile": "exp_beta01_v2", "tracking": "disabled"})
    assert len(prepared["cells"]) == 8
    for cell in prepared["cells"]:
        assert cell["audit"]["G0_MATCHED"] == "NOT_REQUIRED_EXACT_REGIONAL_SUPPORT"
        assert cell["train"].department_code.nunique() == 3
        assert cell["train"].target_month.max() <= f"{cell['year'] - 4}-12"
        extra = cell["train"].loc[cell["train"].department_code.eq("05")]
        assert extra.year_month.min() >= "2016-06"
        assert (
            0
            < extra.year_month.nunique()
            <= ((6 if cell["horizon"] == 1 else 5) + (cell["year"] - 2020) * 12)
        )
        assert (
            extra.year_month.max() <= f"{cell['year'] - 4}-{'11' if cell['horizon'] == 1 else '10'}"
        )
        for part in cell["parts"].values():
            assert set(part.department_code) == {"50", "73"}
    changed = copy.deepcopy(sources)
    changed["frozen_predictions"] = changed["frozen_predictions"].iloc[1:]
    with pytest.raises(ValueError, match="key mismatch"):
        v2.prepare(changed, {"profile": "exp_beta01_v2", "tracking": "disabled"})
    poisoned = copy.deepcopy(sources)
    poisoned["table"].loc[0, "onset_T1"] = 1
    with pytest.raises(ValueError, match="label mismatch"):
        v2.prepare(poisoned, {"profile": "exp_beta01_v2", "tracking": "disabled"})


def test_only_eight_g1_fits_and_selection_does_not_use_evaluation(
    sources: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    class Model:
        def __init__(self, **kwargs: Any):
            if "n_estimators" in kwargs:
                assert kwargs["n_estimators"] == 80 and kwargs["max_depth"] == 2

        def load_model(self, raw: bytearray) -> None:
            assert raw == b"generated-model"

        def fit(self, x: Any, y: Any) -> None:
            calls.append(len(x))
            assert list(x) == v2.FEATURES

        def predict_proba(self, x: Any) -> np.ndarray:
            p = np.where(x.iloc[:, 0].to_numpy() % 2 == 0, 0.6, 0.1)
            return np.c_[1 - p, p]

        def get_booster(self) -> Any:
            return self

        def save_raw(self, raw_format: str) -> bytes:
            return b"generated-model"

    monkeypatch.setitem(sys.modules, "xgboost", SimpleNamespace(XGBClassifier=Model))
    prepared = v2.prepare(sources, {"profile": "exp_beta01_v2", "tracking": "disabled"})
    trained = v2.train(prepared)
    first = v2.calibrate(copy.deepcopy(trained))
    altered = copy.deepcopy(trained)
    for cell in altered["cells"]:
        cell["parts"]["evaluation"]["onset_target"] = 1 - cell["parts"]["evaluation"].onset_target
        cell["raw_scores"]["evaluation"][:] = 0.999
    second = v2.calibrate(altered)
    assert [c["policy"] for c in first["cells"]] == [c["policy"] for c in second["cells"]]
    assert len(calls) == 8
    result = datasets.evaluate(v2.predict(first))
    manifest = json.loads(result["payloads"]["manifest.json"])
    assert manifest["real_model_fits"] == 0 and manifest["historical_model_fits"] == 0
    assert sum(n.endswith(".ubj") for n in result["payloads"]) == 8
    assert v2.reproduce(prepared, result["payloads"])["new_model_fits"] == 0
    assert len(calls) == 8


def test_missing_national_support_is_not_evaluable(sources: dict[str, Any]) -> None:
    sources["table"] = sources["table"].loc[sources["table"].department_code.isin(["50", "73"])]
    prepared = v2.prepare(sources, {"profile": "exp_beta01_v2", "tracking": "disabled"})
    assert not prepared["cells"]
    assert all(r["status"] == "NO_EVALUABLE" for r in prepared["preflight"])


def test_hypothesis_requires_joint_horizon_and_stratum_controls() -> None:
    records = []
    for h in (1, 2):
        for year in (2020, 2021, 2022, 2024):
            for code in ("50001", "73001"):
                for i, truth in enumerate((0, 1, 0, 1)):
                    for arm in ("G1", "G0", "R0"):
                        records.append(
                            {
                                "arm": arm,
                                "horizon": h,
                                "year": year,
                                "department_code": code[:2],
                                "municipality_code": code,
                                "truth": truth,
                                "score": 0.8 if truth else 0.1,
                                "alert": bool(truth and (arm == "G1" or i == 1)),
                            }
                        )
    frame = pd.DataFrame(records)
    protocol = json.loads((ROOT / datasets.PROTOCOL).read_text())
    assert v2.summarize(frame, protocol)[2]["national_expansion"] == "RESPALDADA"
    frame.loc[frame.arm.eq("G1") & frame.horizon.eq(2), "alert"] = False
    assert v2.summarize(frame, protocol)[2]["national_expansion"] == "PARCIALMENTE_RESPALDADA"
    frame.loc[frame.arm.eq("G1"), "alert"] = False
    assert v2.summarize(frame, protocol)[2]["national_expansion"] == "NO_RESPALDADA"


def test_arrow_booleans_are_read_strictly(repo_tmp_path: Path) -> None:
    p = repo_tmp_path / "national.csv"
    p.write_text("eligible\nTrue\nFalse\n")
    fields = datasets.published_fields(
        {"columns": [{"name": "eligible", "dtype": "bool[pyarrow]", "nullable": False}]}
    )
    assert read_panel(p, {"schema": fields}).eligible.tolist() == [True, False]
    p.write_text("eligible\nanything\n")
    with pytest.raises(ValueError):
        read_panel(p, {"schema": fields})


def test_protocol_tamper_and_route_isolation(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = repo_tmp_path / "protocol.json"
    p.write_text("{}")
    monkeypatch.setattr(datasets, "PROTOCOL", str(p))
    with pytest.raises(DatasetError, match="Incorrect source"):
        datasets.NationalBetaSourcesDataset().load()
    graph = register_pipelines()["exp_beta01_v2"]
    assert len(graph.nodes) == 5
    assert graph.inputs() == {"exp_beta01_v2_sources", "parameters"}
    assert graph.outputs() == {"exp_beta01_v2_bundle"}
    assert register_pipelines()["exp_beta01"].outputs() == {"exp_beta01_bundle"}
    assert "exp_beta01_v2_bundle" not in register_pipelines()["replay"].outputs()
    with pytest.raises(ValueError):
        validate_parameters({"profile": "exp_beta01_v2", "tracking": "enabled"})
