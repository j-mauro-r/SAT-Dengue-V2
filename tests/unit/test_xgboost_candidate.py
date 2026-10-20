"""Independent temporal, preparation, selection and native inference regressions."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.model_training import candidates
from scripts.model_training.candidate_selection import (
    choose_configuration,
    internal_folds,
    select_and_fit,
)
from scripts.model_training.contract import ModelTrainingConfig, ModelTrainingError, read_json
from scripts.model_training.loading import TemporalSource, WindowDataset
from scripts.model_training.persistence import json_bytes
from scripts.model_training.pipeline import ModelTrainingResult
from scripts.model_training.xgboost_adapter import fit_candidate, restore_candidate
from scripts.training_preparation.contract import PreparationError

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = read_json(ROOT / "docs/product/stage-4/model_engineering_contract_v1.json")


def settings() -> dict[str, Any]:
    """Use a tiny computational fixture, preserving actual scientific protocol."""
    result = copy.deepcopy(CONTRACT["xgboost_candidate"])
    result["configurations"] = [dict(result["configurations"][0], n_estimators=3)]
    return result


def window(horizon: int = 1) -> WindowDataset:
    """Create two municipalities with known alternating labels and monthly linkage."""
    rows = []
    for municipality in ["05001", "05002"]:
        for i, period in enumerate(pd.period_range("2011-12", "2017-05", freq="M")):
            rows.append(
                dict(
                    municipality_code=municipality,
                    year_month=str(period),
                    target=str(period + horizon),
                    signal=float(i % 7),
                    y=i % 2,
                )
            )
    frame = pd.DataFrame(rows)
    train = frame[frame.target.between("2012-01", "2016-12")].reset_index(drop=True)
    valid = frame[(frame.year_month >= "2016-12") & (frame.target <= "2017-06")].reset_index(
        drop=True
    )

    def parts(f: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        X = f[["municipality_code", "signal"]].assign(
            zona_canal_t="EXITO", zona_canal_lag_1="SEGURIDAD"
        )
        y = f[["y"]].rename(columns={"y": f"y_t{horizon}"})
        index = f[["municipality_code", "year_month", "target"]].rename(
            columns={"target": f"target_period_t{horizon}"}
        )
        index["feature_row"] = np.arange(len(f))
        return X, y, index

    tx, ty, ti = parts(train)
    vx, vy, vi = parts(valid)
    return WindowDataset(
        f"2016-12_t{horizon}",
        "2016-12",
        horizon,
        f"target_period_t{horizon}",
        f"y_t{horizon}",
        tx,
        ty,
        ti,
        vx,
        vy,
        vi,
    )


@pytest.mark.parametrize("horizon", [1, 2])
def test_inner_calendar_boundaries_and_exact_support(horizon: int) -> None:
    """Expected key sets use explicit date predicates, not the production selector."""
    d = window(horizon)
    folds = internal_folds(d.train_index, d.train_y[d.y_column], cutoff=d.cutoff, horizon=horizon)
    for fold, cutoff, end in zip(
        folds, ["2015-12", "2016-06"], ["2016-06", "2016-12"], strict=True
    ):
        expected_train = d.train_index.index[d.train_index[d.target_column] <= cutoff].tolist()
        expected_val = d.train_index.index[
            (d.train_index.year_month >= cutoff)
            & (d.train_index[d.target_column] > cutoff)
            & (d.train_index[d.target_column] <= end)
        ].tolist()
        assert fold.train.index.tolist() == expected_train
        assert fold.validation.index.tolist() == expected_val
        assert len(fold.validation) == 2 * (7 - horizon)
        assert not set(fold.train.index) & set(fold.validation.index)
        assert fold.validation[d.target_column].max() <= "2016-12"


def test_internal_preparer_does_not_learn_later_vocabulary() -> None:
    d = window()
    later = d.train_index.year_month >= "2016-06"
    d.train_X.loc[later, "municipality_code"] = "05099"
    d.train_index.loc[later, "municipality_code"] = "05099"
    # Avoid duplicate municipality/month keys by changing only one municipality.
    changed = later & d.train_X.index.to_series().lt(len(d.train_X) // 2)
    d.train_X.loc[later & ~changed, "municipality_code"] = "05002"
    d.train_index.loc[later & ~changed, "municipality_code"] = "05002"
    r = select_and_fit(
        d.train_X,
        d.train_y[d.y_column],
        d.train_index,
        cutoff=d.cutoff,
        horizon=1,
        settings=settings(),
        policy=CONTRACT["selection_policy"],
    )
    first = r.evidence["folds"][0]["preparer"]
    assert "05099" not in first["categories"]["municipality_code"]
    assert "05099" in r.fitted.preparer["categories"]["municipality_code"]
    assert first["statistics"] == {}
    assert first["fit_rows"] < len(d.train_X)
    assert r.evidence["fit_count"] == 3


@pytest.mark.parametrize("column", ["y_t1", "target_period_t1", "feature_row", "history_available"])
def test_controls_and_labels_rejected_from_X(column: str) -> None:
    d = window()
    with pytest.raises(PreparationError, match="predictor-only"):
        fit_candidate(
            d.train_X.assign(**{column: 1}),
            d.train_y[d.y_column],
            settings()["configurations"][0],
            seed=42,
            threads=1,
        )


def test_missing_numeric_history_stays_explicit_and_reserved_rejected() -> None:
    d = window()
    d.train_X.loc[0, "signal"] = np.nan
    with pytest.raises(PreparationError, match="missingness"):
        fit_candidate(
            d.train_X, d.train_y[d.y_column], settings()["configurations"][0], seed=42, threads=1
        )
    d.train_index.loc[0, d.target_column] = "2025-01"
    with pytest.raises(ModelTrainingError, match="boundary"):
        internal_folds(d.train_index, d.train_y[d.y_column], cutoff="2025-01", horizon=1)


def test_approved_selection_tolerance_brier_then_simplicity() -> None:
    scores = [
        dict(id="deep", ap=0.7, brier=0.2, simplicity=[4, 4, 80, 128]),
        dict(id="simple", ap=0.7 - 5e-13, brier=0.2 + 5e-13, simplicity=[4, 2, 80, 128]),
        dict(id="bad_brier", ap=0.7, brier=0.3, simplicity=[4, 1, 80, 128]),
        dict(id="worse_ap", ap=0.69, brier=0.01, simplicity=[4, 1, 80, 128]),
    ]
    assert choose_configuration(scores, CONTRACT["selection_policy"]) == "simple"
    scores[0]["ap"] = 0.71
    assert choose_configuration(scores, CONTRACT["selection_policy"]) == "deep"


def test_search_budget_rejected_before_fit() -> None:
    d = window()
    s = settings()
    s["configurations"] *= 7
    with pytest.raises(ModelTrainingError, match="six"):
        select_and_fit(
            d.train_X,
            d.train_y[d.y_column],
            d.train_index,
            cutoff=d.cutoff,
            horizon=1,
            settings=s,
            policy=CONTRACT["selection_policy"],
        )


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


@pytest.mark.parametrize("column", ["actual_excess", "previous_excess", "actual_onset"])
def test_retrospective_context_rejected(column: str) -> None:
    d = window()
    with pytest.raises(ModelTrainingError, match="Retrospective"):
        fit_candidate(
            d.train_X.assign(**{column: 1}),
            d.train_y[d.y_column],
            settings()["configurations"][0],
            seed=42,
            threads=1,
        )
