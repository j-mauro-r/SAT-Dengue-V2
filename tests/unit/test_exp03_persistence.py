"""Generated-only terminal persistence and consumed-year isolation acceptance."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp03_persistence import (
    FrozenCell,
    consumed_2025_benchmark,
    fit_calibration,
    fit_native,
    freeze_terminal,
    load_cell,
    save_cell,
    verify_reload,
)


def _training() -> tuple[pd.DataFrame, pd.Series]:
    """Generate all fixture rows directly, without any scientific source reader."""
    frame = pd.DataFrame(
        {
            "municipality_code_feature": ["50001", "73001"] * 24,
            "signal": np.arange(48, dtype=float) % 7,
            "channel_excess_t": np.zeros(48),
        }
    )
    return frame, pd.Series((frame.signal > 3).astype(int), index=frame.index)


def _parameters(family: str) -> dict[str, Any]:
    if family == "gam":
        return {"n_knots": 4, "C": 0.1}
    if family == "lightgbm":
        return dict(
            n_estimators=3,
            num_leaves=7,
            max_depth=3,
            learning_rate=0.05,
            lambda_l1=0,
            lambda_l2=1,
            max_bin=128,
            min_data_in_leaf=2,
        )
    return dict(
        n_estimators=3,
        max_depth=2,
        eta=0.05,
        reg_lambda=1,
        reg_alpha=0,
        max_bin=128,
        min_child_weight=1,
    )


def _cell(family: str = "gam") -> tuple[FrozenCell, pd.DataFrame]:
    X, y = _training()
    model = fit_native(family, X, y, _parameters(family), 42)
    calibrator = fit_calibration(model.predict(X), y, 42)
    cell = FrozenCell(
        "fixture-cell",
        {
            "window": "stress_2024",
            "horizon": 2,
            "family": family,
            "variant": "V09",
            "objective": "onset",
        },
        model,
        calibrator,
        0.4,
        1.0,
        {"50001": "low", "73001": "high"},
        {"synthetic": True, "code_sha256": "fixture"},
    )
    return cell, X


@pytest.mark.parametrize("family", ["gam", "lightgbm", "xgboost"])
def test_native_generated_fit_reload_equivalence_and_support(
    family: str, repo_tmp_path: Path
) -> None:
    cell, X = _cell(family)
    path = repo_tmp_path / family
    identity = save_cell(cell, path)
    restored = load_cell(path)
    assert restored.identity() == identity
    np.testing.assert_allclose(
        cell.predict(X).score.astype(float),
        restored.predict(X).score.astype(float),
        atol=1e-12,
        rtol=0,
    )
    assert restored.predictor.model.preparer["fit_rows"] == len(X)
    assert restored.predictor.model.preparer["ablation"]["excluded_columns"] == [
        "zona_canal_t",
        "zona_canal_lag_1",
    ]
    # Stale current-state inputs may be outside training support; they are audited.
    shifted = X.copy()
    shifted.loc[0, "channel_excess_t"] = 1
    shifted.loc[1, "signal"] = 999
    shifted.loc[2, "municipality_code_feature"] = "99999"
    audit = restored.predictor.audit_support(shifted)
    assert audit.unsupported.iloc[:3].all()
    assert not audit.unsupported.iloc[3:].any()


def test_sigmoid_numeric_export_matches_existing_and_rejects_single_class() -> None:
    from sat_dengue.model_evaluation.calibration import _apply_sigmoid, _fit_sigmoid

    score = pd.Series([0.1, 0.2, 0.6, 0.7, 0.9])
    truth = pd.Series([0, 1, 0, 1, 1])
    native = fit_calibration(score, truth, 42)
    np.testing.assert_allclose(
        native(score).astype(float),
        _apply_sigmoid(score, _fit_sigmoid(score, truth, 42)).astype(float),
        atol=1e-14,
        rtol=0,
    )
    with pytest.raises(ValueError, match="binary classes"):
        fit_calibration(score, pd.Series([0] * len(score)), 42)


def test_native_adapter_strips_nested_source_attrs_and_verifies_selection_reload(
    repo_tmp_path: Path,
) -> None:
    X, y = _training()
    X.attrs["source_months"] = pd.DataFrame({"signal": ["2023-01"] * len(X)})
    model = fit_native("gam", X, y, _parameters("gam"), 42)
    assert not model.envelope(X).attrs
    cell = FrozenCell(
        "attrs-fixture",
        {"window": "stress_2024", "horizon": 2},
        model,
        fit_calibration(model.predict(X), y, 42),
        None,
        1.0,
        {},
        {"synthetic": True},
    )
    path = repo_tmp_path / "attrs-cell"
    save_cell(cell, path)
    evidence = verify_reload(cell, X, path)
    assert evidence["status"] == "pass"
    assert evidence["rows"] == len(X)
    assert evidence["maximum_probability_difference"] <= 1e-12
    frozen = freeze_terminal(
        [cell],
        repo_tmp_path / "attrs-terminal",
        [cell.cell_id],
        {},
        validation_frames={cell.cell_id: X},
    )
    assert frozen["reload_verification"] == [evidence]
    with pytest.raises(ValueError, match="every terminal selection"):
        freeze_terminal(
            [cell], repo_tmp_path / "incomplete-reload", [cell.cell_id], {}, validation_frames={}
        )


def test_consumed_benchmark_uses_frozen_structured_profile_membership(repo_tmp_path: Path) -> None:
    cell, X = _cell()
    cell.profiles = {
        "training_target_end": "2022-12",
        "boundaries": [1.0, 2.0],
        "membership": [
            {"municipality_code": "50001", "transmission_profile": "low"},
            {"municipality_code": "73001", "transmission_profile": "high"},
        ],
    }
    path = repo_tmp_path / "structured-profiles"
    manifest = freeze_terminal(
        [cell], path, [cell.cell_id], {}, validation_frames={cell.cell_id: X}
    )
    result = consumed_2025_benchmark(
        path,
        {cell.cell_id: _benchmark_frame(X)},
        {"governed_coverage": True, "maturity_verified": True, "provenance_sha256": "fixture"},
        expected_manifest_sha256=manifest["manifest_sha256"],
    )
    assert result["predictions"][cell.cell_id].profile.tolist() == ["low", "high"] * 3


def test_native_tamper_and_external_destination_fail(repo_tmp_path: Path) -> None:
    cell, _ = _cell()
    path = repo_tmp_path / "cell"
    save_cell(cell, path)
    (path / "model.native").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="bytes changed"):
        load_cell(path)
    with pytest.raises(ValueError, match="repository-local tmp"):
        save_cell(cell, Path("/tmp/exp03-external-forbidden"))


def _benchmark_frame(X: pd.DataFrame) -> pd.DataFrame:
    frame = X.iloc[:6].copy()
    frame["municipality_code"] = frame.municipality_code_feature
    frame["year_month"] = ["2023-12", "2024-01", "2024-02", "2024-11", "2024-12", "2025-01"]
    frame["target_month"] = [str(pd.Period(m, freq="M") + 2) for m in frame.year_month]
    frame["eligible_at_t"] = [True, True, False, True, True, pd.NA]
    frame["latest_source_month"] = frame.year_month
    frame["onset_target"] = [0, 1, 0, 1, 0, 1]
    return frame


def test_consumed_benchmark_cannot_fit_select_or_adapt_to_2025_labels(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cell, X = _cell()
    path = repo_tmp_path / "terminal"
    manifest = freeze_terminal([cell], path, [cell.cell_id], {"synthetic": True})
    frame = _benchmark_frame(X)
    coverage = {
        "governed_coverage": True,
        "maturity_verified": True,
        "provenance_sha256": "synthetic-fixture",
    }

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("benchmark reached a fitting/selection interface")

    monkeypatch.setattr("sat_dengue.model_training.candidate_families.fit_model", forbidden)
    monkeypatch.setattr("sat_dengue.model_evaluation.calibration._fit_sigmoid", forbidden)
    first = consumed_2025_benchmark(
        path, {cell.cell_id: frame}, coverage, expected_manifest_sha256=manifest["manifest_sha256"]
    )
    changed = frame.copy()
    changed.loc[changed.target_month.str.startswith("2025"), "onset_target"] = 0
    second = consumed_2025_benchmark(
        path,
        {cell.cell_id: changed},
        coverage,
        expected_manifest_sha256=manifest["manifest_sha256"],
    )
    pd.testing.assert_frame_equal(
        first["predictions"][cell.cell_id], second["predictions"][cell.cell_id]
    )
    assert set(first["execution_counters"].values()) == {0}
    assert first["identities_verified_before_after"]
    assert {row["year"] for row in first["annual"]} == {2024, 2025}
    assert first["predictions"][cell.cell_id].abstention.sum() == 2
    assert first["predictions"][cell.cell_id].profile.tolist() == ["low", "high"] * 3
    # No extra fitting to cover unavailable terminal cells is possible.
    with pytest.raises(ValueError, match="every frozen terminal"):
        consumed_2025_benchmark(
            path, {}, coverage, expected_manifest_sha256=manifest["manifest_sha256"]
        )


def test_freeze_completeness_identity_and_calendar_admission(repo_tmp_path: Path) -> None:
    cell, X = _cell()
    with pytest.raises(ValueError, match="Incomplete"):
        freeze_terminal([cell], repo_tmp_path / "incomplete", ["fixture-cell", "other"], {})
    invalid = copy.deepcopy(cell)
    invalid.metadata["window"] = "development_2022"
    with pytest.raises(ValueError, match="stress_2024"):
        freeze_terminal([invalid], repo_tmp_path / "wrong-window", [cell.cell_id], {})
    path = repo_tmp_path / "terminal"
    manifest = freeze_terminal([cell], path, [cell.cell_id], {})
    frame = _benchmark_frame(X)
    kwargs = {"expected_manifest_sha256": manifest["manifest_sha256"]}
    result = consumed_2025_benchmark(path, {cell.cell_id: frame}, {}, **kwargs)
    assert result["status"] == "not_evaluable"
    assert result["predictions"] == {}
    coverage = {
        "governed_coverage": True,
        "maturity_verified": True,
        "provenance_sha256": "fixture",
    }
    future = frame.copy()
    future.loc[0, "latest_source_month"] = "2024-01"
    with pytest.raises(ValueError, match="Future"):
        consumed_2025_benchmark(path, {cell.cell_id: future}, coverage, **kwargs)
    early = frame.copy()
    early.loc[0, ["year_month", "target_month", "latest_source_month"]] = [
        "2023-11",
        "2024-01",
        "2023-11",
    ]
    with pytest.raises(ValueError, match="embargo"):
        consumed_2025_benchmark(path, {cell.cell_id: early}, coverage, **kwargs)
    with pytest.raises(ValueError, match="manifest changed"):
        consumed_2025_benchmark(
            path, {cell.cell_id: frame}, coverage, expected_manifest_sha256="wrong"
        )
