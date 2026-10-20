"""Temporal causality, fit isolation and stable inference using small synthetic inputs."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.training_preparation.contract import CONTRACT_PATH, PreparationError, read_json
from scripts.training_preparation.development import code_fingerprints, serialize_table
from scripts.training_preparation.eligibility import policy_from_years
from scripts.training_preparation.notebook_execution import extract_saved_summary
from scripts.training_preparation.persistence import json_bytes
from scripts.training_preparation.preprocessing import (
    MISSING,
    ZONES,
    PreparerSpec,
    fit_preparer,
    transform_predictors,
)
from scripts.training_preparation.temporal import (
    _window_payloads,
    load_prepared_window,
    reference,
    select_window,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def policy() -> dict[str, Any]:
    return policy_from_years(2007, 2025, "2025-01")


@pytest.fixture
def temporal_history() -> pd.DataFrame:
    rows = []
    for municipality in ("50001", "73001"):
        for period in pd.period_range("2006-06", "2024-12", freq="M"):
            row: dict[str, Any] = {"municipality_code": municipality, "year_month": str(period)}
            for h in (1, 2):
                target = str(period + h)
                evaluable = "2012-01" <= target <= "2024-12"
                row.update(
                    {
                        f"target_period_t{h}": target,
                        f"y_evaluable_t{h}": evaluable,
                        f"y_t{h}": (period.month % 2 if evaluable else pd.NA),
                    }
                )
            rows.append(row)
    frame = pd.DataFrame(rows)
    frame["feature_row"] = frame.index
    return frame


@pytest.fixture
def X_train() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": pd.Series(["50001", "73001", "50001", "73001"], dtype="string"),
            "dengue_notifications_count": [0.0, 2.0, 4.0, 6.0],
            "zona_canal_t": pd.Series(["EXITO", "SEGURIDAD", "ALERTA", "EXCESO"], dtype="string"),
            "zona_canal_lag_1": pd.Series([None, "SEGURIDAD", "EXITO", "ALERTA"], dtype="string"),
            "lluvia_lag_1": [-2.0, -2.0, -2.0, -2.0],
        }
    )


@pytest.mark.parametrize("cutoff", ["2018-12", "2020-12", "2022-12", "2024-06"])
@pytest.mark.parametrize("horizon", [1, 2])
def test_eight_reference_selections_have_observable_train_and_sequential_validation(
    temporal_history: pd.DataFrame,
    policy: dict[str, Any],
    cutoff: str,
    horizon: int,
) -> None:
    result = select_window(temporal_history, policy, cutoff, horizon)
    target = f"target_period_t{horizon}"
    assert (result.train[target] <= cutoff).all()
    assert (result.validation.year_month >= cutoff).all()
    assert result.train[target].between("2012-01", "2024-12").all()
    assert result.validation[target].between("2012-01", "2024-12").all()
    assert len(result.validation) == (12 if horizon == 1 else 10)
    expected_target_start = str(pd.Period(cutoff, freq="M") + horizon)
    assert result.audit["configured_target_start"] == str(pd.Period(cutoff, freq="M") + 1)
    assert result.audit["validation"]["target_start"] == expected_target_start
    assert result.audit["validation"]["origin_start"] == cutoff
    assert set(result.train.index).isdisjoint(result.validation.index)
    old = reference.build_temporal_validation_audit(
        temporal_history,
        temporal_history.head(0),
        [cutoff],
        [],
        development_target_min="2012-01",
        development_target_max="2024-12",
    )
    old_row = old.loc[old.horizon == f"t{horizon}"].iloc[0]
    assert int(old_row.validation_rows) == len(result.validation)
    assert int(old_row.train_rows) == len(result.train)


def test_reserved_and_non_evaluable_labels_never_enter_selection(
    temporal_history: pd.DataFrame,
    policy: dict[str, Any],
) -> None:
    base = select_window(temporal_history, policy, "2024-06", 2)
    # Drop evaluability for one in-window example; counts change honestly, not coerced.
    idx = base.validation.index[0]
    temporal_history.loc[idx, "y_evaluable_t2"] = False
    temporal_history.loc[idx, "y_t2"] = pd.NA
    after = select_window(temporal_history, policy, "2024-06", 2)
    assert len(after.validation) == len(base.validation) - 1
    assert (after.validation.target_period_t2 < "2025-01").all()
    extra = temporal_history.iloc[[0]].copy()
    extra["year_month"] = "2025-01"
    with pytest.raises(PreparationError, match="Reserved origins"):
        select_window(pd.concat([temporal_history, extra]), policy, "2024-06", 2)


def test_target_alignment_and_duplicate_keys_fail_closed(
    temporal_history: pd.DataFrame,
    policy: dict[str, Any],
) -> None:
    changed = temporal_history.copy()
    changed.loc[0, "target_period_t1"] = "2020-01"
    with pytest.raises(PreparationError, match="Target calendar"):
        select_window(changed, policy, "2018-12", 1)
    with pytest.raises(PreparationError, match="duplicate"):
        select_window(
            pd.concat([temporal_history, temporal_history.iloc[[0]]]), policy, "2018-12", 1
        )


@pytest.mark.parametrize("encoding", ["native", "onehot", "ordinal"])
@pytest.mark.parametrize("scaling", ["none", "standard"])
def test_stable_encoding_json_roundtrip_and_train_only_scaling(
    X_train: pd.DataFrame,
    encoding: Any,
    scaling: Any,
) -> None:
    spec = PreparerSpec(encoding=encoding, numeric_scaling=scaling)
    state = fit_preparer(X_train, spec)
    restored = json.loads(json_bytes(state))
    first = transform_predictors(X_train, state)
    second = transform_predictors(X_train, restored)
    pd.testing.assert_frame_equal(first, second)
    assert list(first) == state["output_columns"]
    assert state["categories"]["zona_canal_t"] == [*ZONES, MISSING]
    if scaling == "standard":
        assert state["statistics"]["dengue_notifications_count"]["mean"] == 3
        assert state["statistics"]["dengue_notifications_count"]["scale"] == pytest.approx(5**0.5)
        assert first.dengue_notifications_count.mean() == pytest.approx(0)
        assert state["statistics"]["lluvia_lag_1"]["scale"] == 1
    else:
        assert state["statistics"] == {}
    if encoding == "native":
        assert isinstance(first.zona_canal_t.dtype, pd.CategoricalDtype)


def test_changing_validation_cannot_change_fitted_training_state(X_train: pd.DataFrame) -> None:
    state = fit_preparer(X_train, PreparerSpec(encoding="onehot", numeric_scaling="standard"))
    saved = json_bytes(state)
    validation = X_train.copy()
    validation["dengue_notifications_count"] = 1000000
    validation["municipality_code"] = "99999"
    transformed = transform_predictors(validation, state)
    assert json_bytes(state) == saved
    assert "99999" not in state["categories"]["municipality_code"]
    assert transformed["municipality_code=__UNKNOWN__"].eq(1).all()
    assert state["statistics"]["dengue_notifications_count"]["mean"] == 3


@pytest.mark.parametrize("encoding", ["native", "onehot", "ordinal"])
def test_absence_never_means_seguridad_and_unknown_zones_rejected(
    X_train: pd.DataFrame,
    encoding: Any,
) -> None:
    state = fit_preparer(X_train, PreparerSpec(encoding=encoding))
    validation = X_train.iloc[[0]].copy()
    validation["zona_canal_t"] = pd.NA
    result = transform_predictors(validation, state)
    if encoding == "native":
        assert result.zona_canal_t.iloc[0] == MISSING
    elif encoding == "ordinal":
        assert result.zona_canal_t.iloc[0] != ZONES.index("SEGURIDAD")
    else:
        assert result["zona_canal_t=__MISSING__"].iloc[0] == 1
        assert result["zona_canal_t=SEGURIDAD"].iloc[0] == 0
    validation["zona_canal_t"] = "INVALID_ZONE"
    with pytest.raises(PreparationError, match="Unknown categorical"):
        transform_predictors(validation, state)


def test_unknown_municipality_can_fail_and_order_is_enforced(X_train: pd.DataFrame) -> None:
    state = fit_preparer(X_train, PreparerSpec(unknown_municipality="error"))
    validation = X_train.copy()
    validation["municipality_code"] = "99999"
    with pytest.raises(PreparationError, match="Unknown categorical"):
        transform_predictors(validation, state)
    with pytest.raises(PreparationError, match="order"):
        transform_predictors(X_train[list(reversed(X_train.columns))], state)
    state["versions"]["python"] = "invalid-version"
    with pytest.raises(PreparationError, match="version"):
        transform_predictors(X_train, state)


def test_insufficient_numeric_history_stays_explicit_without_imputation(
    X_train: pd.DataFrame,
) -> None:
    missing = X_train.copy()
    missing["dengue_notifications_count"] = np.nan
    with pytest.raises(PreparationError, match="missingness"):
        fit_preparer(missing, PreparerSpec())
    state = fit_preparer(missing, PreparerSpec(numeric_missing="preserve"))
    assert transform_predictors(missing, state).dengue_notifications_count.isna().all()
    with pytest.raises(PreparationError, match="Insufficient training history"):
        fit_preparer(missing, PreparerSpec(numeric_scaling="standard", numeric_missing="preserve"))


@pytest.mark.parametrize(
    "control",
    [
        "y_t1",
        "target_period_t2",
        "history_valid_years_t1",
        "in_epi_coverage",
        "p75_canal_t",
        "future_count",
    ],
)
def test_Y_and_controls_are_rejected_from_preparer_X(X_train: pd.DataFrame, control: str) -> None:
    X_train[control] = 1
    with pytest.raises(PreparationError, match="predictor-only"):
        fit_preparer(X_train, PreparerSpec())


def test_window_payloads_and_model_loader_roundtrip(
    temporal_history: pd.DataFrame,
    policy: dict[str, Any],
    tmp_path: Path,
) -> None:
    selected = select_window(temporal_history, policy, "2018-12", 1)
    frame = temporal_history
    X = pd.DataFrame(
        {
            "municipality_code": frame.municipality_code,
            "dengue_notifications_count": np.arange(len(frame), dtype=float),
            "zona_canal_t": "ALERTA",
            "zona_canal_lag_1": "SEGURIDAD",
        }
    )
    profiles = {"native": {"encoding": "native"}, "onehot": {"encoding": "onehot"}}
    payloads, metadata = _window_payloads(X, selected, "2018-12_t1", profiles)
    from scripts.training_preparation.persistence import bytes_record

    manifest = {
        "windows": {"2018-12_t1": metadata},
        "files": {n: bytes_record(b) for n, b in payloads.items()},
    }
    for name, content in payloads.items():
        (tmp_path / name).write_bytes(content)
    (tmp_path / "manifest.json").write_bytes(json_bytes(manifest))
    matrix, y, index, state = load_prepared_window(tmp_path, "2018-12_t1", "native", "validation")
    assert len(matrix) == len(y) == len(index) == 12
    assert isinstance(matrix.zona_canal_t.dtype, pd.CategoricalDtype)
    expected = transform_predictors(X.loc[selected.validation.index].reset_index(drop=True), state)
    assert serialize_table(matrix) == serialize_table(expected)
    (tmp_path / "2018-12_t1_native_preparer.json").write_text("{}")
    with pytest.raises(PreparationError, match="fingerprint"):
        load_prepared_window(tmp_path, "2018-12_t1", "native", "validation")


def test_notebook_output_identity_excludes_results_but_includes_code(tmp_path: Path) -> None:
    # Build the minimal fingerprinted repository surface, without private scientific data.
    for relative in (
        "scripts/training_preparation/a.py",
        "scripts/validate_stage2_training_readiness.py",
        "scripts/stage2_notebook_visual_assets.py",
        "pyproject.toml",
    ):
        p = tmp_path / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# synthetic\n")
    p = tmp_path / "notebooks/04_training_preparation_pipeline.ipynb"
    p.parent.mkdir()
    notebook: dict[str, Any] = {
        "nbformat": 4,
        "cells": [
            {"cell_type": "code", "source": ["x = 1\n"], "outputs": [], "execution_count": None}
        ],
    }
    p.write_text(json.dumps(notebook))
    before = code_fingerprints(tmp_path)
    notebook["cells"][0]["outputs"] = [{"output_type": "stream", "text": "result"}]
    notebook["cells"][0]["execution_count"] = 1
    p.write_text(json.dumps(notebook))
    assert code_fingerprints(tmp_path) == before
    notebook["cells"][0]["source"] = ["x = 2\n"]
    p.write_text(json.dumps(notebook))
    assert code_fingerprints(tmp_path) != before


def test_saved_notebook_summary_requires_real_complete_outputs() -> None:
    notebook: dict[str, Any] = {
        "cells": [
            {
                "cell_type": "code",
                "id": "run-summary",
                "execution_count": 1,
                "outputs": [
                    {
                        "output_type": "stream",
                        "name": "stdout",
                        "text": json.dumps({"preparation_run": {"status": "PASS"}}),
                    }
                ],
            }
        ]
    }
    assert extract_saved_summary(notebook) == {"status": "PASS"}
    altered = copy.deepcopy(notebook)
    altered["cells"][0]["execution_count"] = None
    with pytest.raises(PreparationError, match="execution"):
        extract_saved_summary(altered)
    altered = copy.deepcopy(notebook)
    altered["cells"][0]["outputs"] = [{"output_type": "error", "ename": "Error"}]
    with pytest.raises(PreparationError, match="execution"):
        extract_saved_summary(altered)


def test_contract_has_exact_reference_cutoffs_and_separate_profiles() -> None:
    contract = read_json(ROOT / CONTRACT_PATH)
    settings = contract["temporal_preparation"]
    assert settings["cutoffs"] == ["2018-12", "2020-12", "2022-12", "2024-06"]
    assert settings["profiles"]["native"]["numeric_scaling"] == "none"
    assert settings["profiles"]["onehot_standard"]["numeric_scaling"] == "standard"
    assert contract["temporal_policy"]["reserved_final_block_start"] == "2025-01"
    assert set(settings["known_zones"]) == set(ZONES)


def test_window_fitting_parameters_are_unchanged_when_validation_values_change(
    temporal_history: pd.DataFrame,
    policy: dict[str, Any],
) -> None:
    selected = select_window(temporal_history, policy, "2018-12", 2)
    X = pd.DataFrame(
        {
            "municipality_code": temporal_history.municipality_code,
            "dengue_notifications_count": np.arange(len(temporal_history), dtype=float),
            "zona_canal_t": "EXITO",
            "zona_canal_lag_1": "ALERTA",
        }
    )
    profiles = {"scaled": {"encoding": "onehot", "numeric_scaling": "standard"}}
    before, _ = _window_payloads(X, selected, "2018-12_t2", profiles)
    X.loc[selected.validation.index, "dengue_notifications_count"] = 999999.0
    X.loc[selected.validation.index, "zona_canal_t"] = "EXCESO"
    after, _ = _window_payloads(X, selected, "2018-12_t2", profiles)
    assert before["2018-12_t2_scaled_preparer.json"] == after["2018-12_t2_scaled_preparer.json"]
    assert (
        before["2018-12_t2_scaled_train_matrix.csv"] == after["2018-12_t2_scaled_train_matrix.csv"]
    )
    assert (
        before["2018-12_t2_scaled_validation_matrix.csv"]
        != after["2018-12_t2_scaled_validation_matrix.csv"]
    )
