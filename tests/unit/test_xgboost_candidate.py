"""Independent temporal, preparation, selection and native inference regressions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from candidate_test_fixtures import CONTRACT, settings, window

from sat_dengue.datasets.legacy_preparation.contract import PreparationError
from sat_dengue.datasets.legacy_training.contract import (
    ModelTrainingError,
)
from sat_dengue.model_training.candidate_selection import (
    choose_configuration,
    internal_folds,
    select_and_fit,
)
from sat_dengue.model_training.xgboost_adapter import fit_candidate

ROOT = Path(__file__).resolve().parents[2]


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
