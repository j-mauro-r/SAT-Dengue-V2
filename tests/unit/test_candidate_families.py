"""Independent family representation, temporal isolation and ablation regressions."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest
from sklearn.preprocessing import SplineTransformer  # type: ignore[import-untyped]
from test_xgboost_candidate import CONTRACT, settings, window

from sat_dengue.datasets.legacy_preparation.contract import PreparationError
from sat_dengue.datasets.legacy_training.contract import ModelTrainingError
from sat_dengue.metrics import average_precision_metric
from sat_dengue.model_training.candidate_families import fit_model, restore_model, simplicity
from sat_dengue.model_training.candidate_preparation import transform_representation
from sat_dengue.model_training.candidate_selection import select_and_fit
from sat_dengue.model_training.gam_adapter import spline_matrix
from sat_dengue.model_training.xgboost_adapter import fit_candidate


def family_settings(family: str) -> dict[str, Any]:
    """Retain protocol but use one small declared configuration for fixture execution."""
    result = copy.deepcopy(CONTRACT[f"{family}_candidate"])
    result["configurations"] = result["configurations"][:1]
    if family != "gam":
        result["configurations"][0]["n_estimators"] = 3
    return result


@pytest.mark.parametrize("family", ["lightgbm", "gam"])
def test_family_roundtrip_categories_and_forbidden_inputs(family: str) -> None:
    d = window()
    p = family_settings(family)["configurations"][0]
    fit = fit_model(family, d.train_X, d.train_y[d.y_column], p, seed=42, threads=1)
    restored = restore_model(family, fit.model_bytes(), json.loads(json.dumps(fit.preparer)))
    validation = d.validation_X.copy()
    validation["municipality_code"] = "unknown"
    validation.loc[0, "zona_canal_t"] = pd.NA
    np.testing.assert_array_equal(fit.predict(validation), restored.predict(validation))
    encoded = transform_representation(validation, fit.preparer)
    assert encoded["municipality_code=__UNKNOWN__"].eq(1).all()
    assert encoded.loc[0, "zona_canal_t=__MISSING__"] == 1
    assert encoded.loc[0, "zona_canal_t=SEGURIDAD"] == 0
    assert list(encoded.columns) == fit.preparer["output_columns"]
    validation.loc[0, "zona_canal_t"] = "invalid"
    with pytest.raises(PreparationError, match="Unknown"):
        fit.predict(validation)
    for forbidden in ("y_t1", "target_period_t1", "feature_row", "actual_onset"):
        with pytest.raises((PreparationError, ModelTrainingError)):
            fit_model(
                family,
                d.train_X.assign(**{forbidden: 1}),
                d.train_y[d.y_column],
                p,
                seed=42,
                threads=1,
            )
    X = d.train_X.copy()
    X.loc[0, "signal"] = np.nan
    with pytest.raises(PreparationError, match="missingness"):
        fit_model(family, X, d.train_y[d.y_column], p, seed=42, threads=1)


@pytest.mark.parametrize("family", ["lightgbm", "gam"])
@pytest.mark.parametrize("horizon", [1, 2])
def test_internal_training_only_basis_and_vocabulary(family: str, horizon: int) -> None:
    d = window(horizon)
    later = (d.train_index.year_month >= "2016-06") & d.train_index.municipality_code.eq("05001")
    d.train_X.loc[later, "municipality_code"] = "05999"
    d.train_index.loc[later, "municipality_code"] = "05999"
    d.train_X.loc[later, "signal"] = 1000
    result = select_and_fit(
        d.train_X,
        d.train_y[d.y_column],
        d.train_index,
        cutoff=d.cutoff,
        horizon=horizon,
        settings=family_settings(family),
        policy=CONTRACT["selection_policy"],
        family=family,
    )
    first = result.evidence["folds"][0]["preparer"]
    assert "05999" not in first["categories"]["municipality_code"]
    assert "05999" in result.fitted.preparer["categories"]["municipality_code"]
    if family == "gam":
        inner = next(t for t in first["gam"]["terms"] if t["column"] == "signal")
        outer = next(t for t in result.fitted.preparer["gam"]["terms"] if t["column"] == "signal")
        assert inner["knots"][-4] == 6
        assert outer["knots"][-4] == 1000
    assert result.evidence["fit_count"] == 3
    for fold in result.evidence["folds"]:
        audit = fold["boundaries"]
        assert fold["preparer"]["fit_rows"] < len(d.train_X)
        assert audit
    # External changes are not inputs to selection, including subsequent category vocabulary.
    d.validation_X["signal"] = -999
    d.validation_y[d.y_column] = 1 - d.validation_y[d.y_column]
    repeated = select_and_fit(
        d.train_X,
        d.train_y[d.y_column],
        d.train_index,
        cutoff=d.cutoff,
        horizon=horizon,
        settings=family_settings(family),
        policy=CONTRACT["selection_policy"],
        family=family,
    )
    assert repeated.fitted.model_bytes() == result.fitted.model_bytes()
    assert repeated.fitted.preparer == result.fitted.preparer
    assert repeated.selected == result.selected


def test_exported_splines_match_library_at_knots_and_outside_training_range() -> None:
    d = window()
    d.train_X["mes_sin"] = np.sin(np.arange(len(d.train_X)))
    d.train_X["constant"] = 7.0
    p = {"n_knots": 4, "C": 1.0}
    fit = fit_model("gam", d.train_X, d.train_y[d.y_column], p, seed=42, threads=1)
    v = d.train_X.iloc[:7].copy()
    v["signal"] = [-100, 0, 1, 2, 4, 6, 100]
    v["constant"] = 999
    library = SplineTransformer(
        n_knots=4, degree=3, knots="uniform", extrapolation="constant", include_bias=False
    ).fit(d.train_X[["signal"]])
    matrix = spline_matrix(v, fit.preparer)
    np.testing.assert_allclose(matrix[:, :5], library.transform(v[["signal"]]), atol=1e-14)
    names = fit.preparer["gam"]["output_columns"]
    np.testing.assert_array_equal(matrix[:, names.index("mes_sin")], v.mes_sin)
    assert np.all(matrix[:, names.index("constant")] == 0)
    assert simplicity("gam", 6, p, fit.preparer) == [0, len(names), 1, -1]
    assert average_precision_metric(pd.Series([0, 0]), pd.Series([0.2, 0.8]))["value"] is None


@pytest.mark.parametrize("excluded", [["signal"], ["zona_canal_t", "zona_canal_lag_1"]])
def test_ablation_removes_values_and_all_encodings_before_fit(excluded: list[str]) -> None:
    d = window()
    p = settings()["configurations"][0]
    fit = fit_candidate(d.train_X, d.train_y[d.y_column], p, seed=42, threads=1, excluded=excluded)
    changed = d.train_X.copy()
    for name in excluded:
        changed[name] = 999 if name == "signal" else "EXCESO"
    again = fit_candidate(changed, d.train_y[d.y_column], p, seed=42, threads=1, excluded=excluded)
    assert again.model_bytes() == fit.model_bytes()
    assert again.preparer == fit.preparer
    np.testing.assert_array_equal(fit.predict(d.train_X), fit.predict(changed))
    matrix = transform_representation(changed, fit.preparer)
    assert not any(c.split("=", 1)[0] in excluded for c in matrix)


def test_suite_budget_rejected_before_any_loading_or_fitting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A user-reduced global budget cannot be exceeded before reporting the error."""
    from sat_dengue.datasets.legacy_training import candidate_suite
    from sat_dengue.datasets.legacy_training.contract import ModelTrainingConfig

    contract = copy.deepcopy(CONTRACT)
    contract["candidate_suite"]["maximum_fits_per_run"] = 200
    (tmp_path / "contract.json").write_text(json.dumps(contract))
    monkeypatch.setattr(
        candidate_suite,
        "build_model_training",
        lambda *a, **kw: pytest.fail("budget check ran after loading/fitting"),
    )
    with pytest.raises(ModelTrainingError, match="budget"):
        candidate_suite.build_candidate_suite(
            ModelTrainingConfig(tmp_path, tmp_path / "contract.json")
        )


@pytest.mark.parametrize("family", ["unknown", "Umaña", "v1"])
def test_training_unknown_families_fail_closed(family: str) -> None:
    from sat_dengue.model_training.candidate_families import restore_model, validate_grid
    from sat_dengue.model_training.contract import ModelTrainingError

    with pytest.raises(ModelTrainingError):
        validate_grid(family, [{}])
    with pytest.raises(ModelTrainingError):
        restore_model(family, b"{}", {})


def test_training_synthetic_route_rejects_changed_or_foreign_cases() -> None:
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.model_training.workflow import (
        fit_synthetic,
        resolve_synthetic_configuration,
        synthetic_cases,
    )

    resolved = resolve_synthetic_configuration(
        ConfigurationInputsDataset().load(),
        {"profile": "training_synthetic", "tracking": "disabled"},
    )
    cases = synthetic_cases(resolved)
    cases["train_X"].iloc[0, 1] = 99999.0
    with pytest.raises(ModelTrainingError, match="synthetic"):
        fit_synthetic(cases, resolved)
