"""Generated-only policy, chronology, integrity and Kedro acceptance checks."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from kedro.io import DataCatalog, DatasetError, MemoryDataset
from kedro.runner import SequentialRunner
from test_canonical_model_table import panel as panel

from sat_dengue.canonical.table import build_table
from sat_dengue.configuration import validate_parameters
from sat_dengue.datasets import exp_beta03 as datasets
from sat_dengue.experiments import exp_beta03 as beta
from sat_dengue.experiments.exp03_1_evaluation import select_threshold
from sat_dengue.experiments.exp_beta01 import prepare as canonical_cohorts
from sat_dengue.pipeline_registry import register_pipelines

ROOT = Path(__file__).resolve().parents[2]
PARAMETERS = {"profile": "exp_beta03", "tracking": "disabled"}


def protocol() -> dict[str, Any]:
    return json.loads((ROOT / datasets.PROTOCOL_PATH).read_text())


def source(panel: pd.DataFrame) -> dict[str, Any]:
    table, columns = build_table(panel)
    original = json.loads(
        (ROOT / "docs/product/experiments/EXP-BETA01/protocol.phase2.json").read_text()
    )
    result: dict[str, Any] = {
        "table": table,
        "columns": columns,
        "protocol": original,
        "evidence_type": "synthetic_generated_data",
        "provenance": {"sources": {}, "execution": {"code": {}}},
    }
    cohorts = canonical_cohorts(result, {"profile": "exp_beta01", "tracking": "disabled"})[
        "cohorts"
    ]
    p = protocol()
    p["evaluation_years"] = [2022]
    cells, references = [], []
    rng = np.random.default_rng(42)
    for horizon in p["horizons"]:
        window = {
            "train": ["2012-01", "2020-12"],
            "calibration": ["2021-01", "2021-06"],
            "selection": ["2021-07", "2021-12"],
            "evaluation": ["2022-01", "2022-12"],
        }
        parts, previous = {}, None
        for role, (start, end) in window.items():
            f = cohorts[horizon]
            mask = f.target_month.between(start, end)
            if previous:
                mask &= f.year_month.ge(previous)
            parts[role] = f.loc[mask].copy()
            parts[role]["score"] = rng.uniform(0.01, 0.99, mask.sum())
            previous = end
        old = (
            parts["evaluation"]
            .rename(columns={"year_month": "origin_month", "onset_target": "truth"})
            .copy()
        )
        old["horizon"], old["alert"] = horizon, old.score.ge(0.6)
        references.append(old)
        cells.append(
            {
                "cell_id": f"generated-h{horizon}",
                "horizon": horizon,
                "year": 2022,
                "window": window,
                "parts": parts,
                "reference_threshold": 0.6,
                "reference_selection": {"threshold": 0.6},
            }
        )
    return {
        **result,
        "protocol": p,
        "canonical_protocol": original,
        "cells": cells,
        "reference": pd.concat(references, ignore_index=True),
    }


def selection_frame() -> pd.DataFrame:
    # Identical score ordering with heterogeneous local FP support.
    return pd.DataFrame(
        {
            "municipality_code": [f"{d}{i:03d}" for d in ("50", "73") for i in range(36)],
            "department_code": ["50"] * 36 + ["73"] * 36,
            "year_month": ["2021-08"] * 72,
            "target_month": ["2021-09"] * 72,
            "truth": ([1] * 6 + [0] * 30) * 2,
            "score": [0.9] * 6 + [0.85] * 3 + [0.1] * 27 + [0.8] * 6 + [0.2] * 30,
        }
    )


def test_global_whole_ties_match_existing_native_selector_and_eligible_cap() -> None:
    frame, p = selection_frame(), protocol()
    result = beta.select_policy(frame, p)["global"]
    expected = select_threshold(frame.truth, frame.score, exposure=len(frame) / 12)
    assert result["threshold"] == expected["threshold"]
    assert result["detected"] == expected["detected_onsets"]
    assert result["false_alerts"] == expected["false_alerts"] <= result["false_alert_limit"]
    # The historical broader monitored denominator permits extra tied negatives.
    frame.loc[6:14, "score"] = 0.85
    broad = select_threshold(frame.truth, frame.score, exposure=100)
    narrow = beta.select_policy(frame, p)["global"]
    assert broad["false_alerts"] > narrow["false_alerts"]


def test_department_shrinkage_keeps_local_cap_and_unsupported_falls_back() -> None:
    frame, p = selection_frame(), protocol()
    policy = beta.select_policy(frame, p)
    assert policy["department_status"] == "EVALUATE"
    for code, local in policy["departments"].items():
        g = frame.loc[frame.department_code.eq(code)]
        assert not local["fallback"] and 0 < local["weight"] < 1
        assert int((beta.alerts(g.score, local["threshold"]) & g.truth.eq(0)).sum()) <= len(g) // 12
    small = beta.select_policy(frame.loc[frame.department_code.eq("50")], p)
    assert small["department_status"] == "NO_EVALUABLE"
    assert all(d["fallback"] for d in small["departments"].values())
    assert all(
        d["threshold"] == small["global"]["threshold"] for d in small["departments"].values()
    )


def test_hard_negative_diagnostic_never_implies_retraining_support() -> None:
    result = beta.select_policy(selection_frame(), protocol())["fp_aware"]
    assert result["hard_false_positives"] == 3
    assert result["independent_oof_selection_blocks_per_predictor"] == 1
    assert result["status"] == "CONDICIONAL_NO_JUSTIFICADO"


def test_evaluation_mutations_cannot_change_selected_policy(panel: pd.DataFrame) -> None:
    prepared = beta.prepare(source(panel), PARAMETERS)
    expected = beta.select(copy.deepcopy(prepared))
    changed = copy.deepcopy(prepared)
    for cell in changed["cells"]:
        cell["evaluation"]["truth"] = 1 - cell["evaluation"].truth
        cell["evaluation"]["score"] = 1 - cell["evaluation"].score
    actual = beta.select(changed)
    assert [c["policies"] for c in actual["cells"]] == [c["policies"] for c in expected["cells"]]


def test_exact_canonical_pairing_and_temporal_boundaries_fail_closed(panel: pd.DataFrame) -> None:
    original = source(panel)
    mutations = []
    missing = copy.deepcopy(original)
    missing["cells"][0]["parts"]["evaluation"] = missing["cells"][0]["parts"]["evaluation"].iloc[1:]
    mutations.append(missing)
    leaked = copy.deepcopy(original)
    leaked["cells"][0]["parts"]["selection"].iloc[
        0, leaked["cells"][0]["parts"]["selection"].columns.get_loc("year_month")
    ] = "2020-01"
    mutations.append(leaked)
    mislabeled = copy.deepcopy(original)
    f = mislabeled["cells"][1]["parts"]["evaluation"]
    f.loc[f.index[0], "onset_target"] = 1 - f.iloc[0].onset_target
    mutations.append(mislabeled)
    for bad in mutations:
        with pytest.raises(ValueError, match="pairing|embargo"):
            beta.prepare(bad, PARAMETERS)


def test_real_graph_publication_pairing_reproduction_and_no_overwrite(
    panel: pd.DataFrame, repo_tmp_path: Path
) -> None:
    inputs = source(panel)
    output = datasets.PolicyBundleDataset(str(repo_tmp_path))
    catalog = DataCatalog(
        {
            "parameters": MemoryDataset(PARAMETERS),
            "exp_beta03_sources": MemoryDataset(inputs),
            "exp_beta03_bundle": output,
        }
    )
    graph = register_pipelines()["exp_beta03"]
    SequentialRunner().run(graph, catalog)
    published = output.load()
    result = beta.evaluate(beta.apply(beta.select(beta.prepare(copy.deepcopy(inputs), PARAMETERS))))
    folder = Path(published["path"])
    assert all((folder / name).read_bytes() == raw for name, raw in result["payloads"].items())
    manifest = json.loads(result["payloads"]["manifest.json"])
    assert manifest["real_model_fits"] == 0
    with pytest.raises((DatasetError, ValueError), match="exist|overwrite"):
        output.save(result)
    f = pd.read_csv(__import__("io").BytesIO(result["payloads"]["predictions.csv"]))
    for (_, _), group in f.groupby(["horizon", "year"]):
        old = group.loc[group.arm.eq("R0")].sort_values(beta.KEYS)
        for _, arm in group.groupby("arm"):
            arm = arm.sort_values(beta.KEYS)
            assert (
                arm[[*beta.KEYS, "target_month", "truth", "score"]].to_records(index=False).tolist()
                == old[[*beta.KEYS, "target_month", "truth", "score"]]
                .to_records(index=False)
                .tolist()
            )
    path = repo_tmp_path / manifest["bundle_id"] / "metrics.csv"
    path.chmod(0o600)
    path.write_bytes(b"tampered")
    with pytest.raises(DatasetError, match="changed|mismatch"):
        output.load()


def test_protocol_pin_and_additive_kedro_bindings(monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.config_loader import CATALOG

    monkeypatch.setattr(datasets, "PROTOCOL_SHA256", "0" * 64)
    with pytest.raises(DatasetError, match="Unapproved"):
        datasets.PolicySourcesDataset().load()
    pipelines = register_pipelines()
    assert len(pipelines["exp_beta03"].nodes) == 4
    assert pipelines["exp_beta03"].inputs() == {"parameters", "exp_beta03_sources"}
    assert pipelines["exp_beta03"].outputs() == {"exp_beta03_bundle"}
    assert not {n.name for n in pipelines["exp_beta03"].nodes} & {
        n.name for n in pipelines["replay"].nodes
    }
    assert "exp_beta03_sources" in CATALOG
    assert validate_parameters(PARAMETERS) == PARAMETERS
    for extra in ({"tracking": "enabled"}, {"experiment_id": "EXP-BETA03"}, {"threshold": 0.5}):
        with pytest.raises(ValueError):
            validate_parameters({**PARAMETERS, **extra})
