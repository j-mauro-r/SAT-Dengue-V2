"""Independent temporal, preparation, selection and native inference regressions."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from candidate_test_fixtures import CONTRACT as CONTRACT
from candidate_test_fixtures import settings as settings
from candidate_test_fixtures import window as window

from sat_dengue.datasets.legacy_preparation.contract import PreparationError
from sat_dengue.datasets.legacy_training import candidates
from sat_dengue.datasets.legacy_training.contract import (
    ModelTrainingConfig,
    ModelTrainingError,
    read_json,
)
from sat_dengue.datasets.legacy_training.loading import TemporalSource
from sat_dengue.datasets.legacy_training.persistence import json_bytes
from sat_dengue.datasets.legacy_training.pipeline import ModelTrainingResult
from sat_dengue.model_training.xgboost_adapter import fit_candidate, restore_candidate

ROOT = Path(__file__).resolve().parents[2]


def test_native_model_and_preparer_roundtrip(tmp_path: Path) -> None:
    d = window()
    fitted = fit_candidate(
        d.train_X, d.train_y[d.y_column], settings()["configurations"][0], seed=42, threads=1
    )
    (tmp_path / "model.json").write_bytes(fitted.model_bytes())
    (tmp_path / "preparer.json").write_bytes(json_bytes(fitted.preparer))
    restored = restore_candidate(
        (tmp_path / "model.json").read_bytes(), read_json(tmp_path / "preparer.json")
    )
    np.testing.assert_array_equal(fitted.predict(d.validation_X), restored.predict(d.validation_X))
    with pytest.raises(PreparationError, match="schema/order"):
        restored.predict(d.validation_X.iloc[:, ::-1])


@pytest.mark.parametrize("family", ["xgboost", "lightgbm", "gam"])
def test_pipeline_external_perturbation_cannot_change_fitting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, family: str
) -> None:
    """Run actual candidate orchestration twice with changed external data and lineage."""
    d = window()
    contract = copy.deepcopy(CONTRACT)
    contract["windows"] = [d.window_id]
    candidate_settings = copy.deepcopy(CONTRACT[f"{family}_candidate"])
    candidate_settings["configurations"] = candidate_settings["configurations"][:1]
    if family != "gam":
        candidate_settings["configurations"][0]["n_estimators"] = 3
    contract[f"{family}_candidate"] = candidate_settings
    (tmp_path / "contract.json").write_bytes(json_bytes(contract))
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "manifest.json").write_bytes(json_bytes({"input": "original"}))
    reference_dir = tmp_path / "references"
    reference_dir.mkdir()
    (reference_dir / "manifest.json").write_bytes(json_bytes({"reference": "fixture"}))
    pd.DataFrame(
        [
            dict(
                window_id=d.window_id,
                horizon=1,
                reference="train_prevalence",
                metric="average_precision",
                value=0.5,
            )
        ]
    ).to_csv(reference_dir / "metrics.csv", index=False)
    source = TemporalSource(source_dir, {}, d.train_X)
    monkeypatch.setattr(candidates, "load_temporal_source", lambda config: source)
    monkeypatch.setattr(candidates, "load_window_dataset", lambda source, window_id: d)
    monkeypatch.setattr(
        candidates,
        "build_model_training",
        lambda config, verify_only=False: ModelTrainingResult(reference_dir, {}),
    )
    monkeypatch.setattr(candidates, "candidate_code", lambda root: {"code": "fixture"})

    def context(config: Any, source: Any, index: Any, *, target_column: str) -> pd.DataFrame:
        # Explicit evaluation fixture; independent of adapter/search inputs.
        return pd.DataFrame(
            dict(
                municipality_code=index.municipality_code,
                target_period=index[target_column],
                previous_target_period=(pd.PeriodIndex(index[target_column], freq="M") - 1).astype(
                    str
                ),
                actual_excess=d.validation_y[d.y_column],
                previous_excess=0,
                actual_onset=d.validation_y[d.y_column].eq(1),
                onset_evaluable=True,
            )
        )

    monkeypatch.setattr(candidates, "load_event_context", context)
    config = ModelTrainingConfig(tmp_path, Path("contract.json"))
    first = candidates.build_candidates(config, family=family)
    old_model = (first.bundle / f"{d.window_id}_model.json").read_bytes()
    old_prep = (first.bundle / f"{d.window_id}_preparer.json").read_bytes()
    old_search = read_json(first.bundle / f"{d.window_id}_search.json")
    # Change labels, values AND categories in external validation only.
    d.validation_y[d.y_column] = 1 - d.validation_y[d.y_column]
    d.validation_X["signal"] = 999.0
    d.validation_X["municipality_code"] = "05999"
    (source_dir / "manifest.json").write_bytes(json_bytes({"input": "perturbed external"}))
    second = candidates.build_candidates(config, family=family)
    assert first.bundle != second.bundle
    assert old_model == (second.bundle / f"{d.window_id}_model.json").read_bytes()
    assert old_prep == (second.bundle / f"{d.window_id}_preparer.json").read_bytes()
    new_search = read_json(second.bundle / f"{d.window_id}_search.json")
    assert old_search["selected"] == new_search["selected"]
    assert old_search["candidates"] == new_search["candidates"]
    assert old_search["training_fingerprint"] == new_search["training_fingerprint"]
    assert (
        "05999"
        not in read_json(second.bundle / f"{d.window_id}_preparer.json")["categories"][
            "municipality_code"
        ]
    )
    # Reuse/verification cannot dispatch a fit.
    monkeypatch.setattr(
        candidates, "select_and_fit", lambda *a, **kw: pytest.fail("reuse attempted fitting")
    )
    assert (
        candidates.build_candidates(config, verify_only=True, family=family).bundle == second.bundle
    )
    monkeypatch.setattr(candidates, "candidate_code", lambda root: {"code": "changed"})
    with pytest.raises(FileNotFoundError):
        candidates.build_candidates(config, verify_only=True, family=family)
    monkeypatch.setattr(candidates, "candidate_code", lambda root: {"code": "fixture"})
    contract[f"{family}_candidate"]["seed"] = 43
    (tmp_path / "contract.json").write_bytes(json_bytes(contract))
    with pytest.raises(FileNotFoundError):
        candidates.build_candidates(config, verify_only=True, family=family)
    contract[f"{family}_candidate"]["seed"] = 42
    (tmp_path / "contract.json").write_bytes(json_bytes(contract))
    (second.bundle / f"{d.window_id}_model.json").write_text("{}")
    with pytest.raises(ModelTrainingError, match="payload"):
        candidates.build_candidates(config, verify_only=True, family=family)
