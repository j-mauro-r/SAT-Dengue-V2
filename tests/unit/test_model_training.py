"""Stage 4 reference-pipeline regressions without private datasets."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.model_training.loading import WindowDataset, _validate_alignment
from scripts.model_training.metrics import (
    average_precision_metric,
    brier_metric,
    evaluate_metrics,
    false_alarm_ratio_metric,
    onset_sensitivity_metric,
)
from scripts.model_training.persistence import publish_artifacts, verify_artifacts
from scripts.model_training.pipeline import _enforce_window_rules
from scripts.model_training.references import persistence_reference, train_prevalence_reference


def _index(target_column: str, targets: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": pd.Series(["50001"] * len(targets), dtype="string"),
            "year_month": pd.Series(["2024-01"] * len(targets), dtype="string"),
            target_column: pd.Series(targets, dtype="string"),
            "feature_row": pd.Series(range(len(targets)), dtype="Int64"),
        }
    )


def test_alignment_requires_row_and_key_consistency() -> None:
    X = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001"],
            "zona_canal_t": ["EXCESO", "ALERTA"],
        }
    )
    y = pd.DataFrame({"y_t1": pd.Series([1, 0], dtype="Int64")})
    index = _index("target_period_t1", ["2024-02", "2024-03"])
    development_X = X.copy(deep=True).reset_index(drop=True)
    _validate_alignment(
        X,
        y,
        index,
        y_column="y_t1",
        target_column="target_period_t1",
        development_X=development_X,
    )

    bad_X = X.iloc[[0]].reset_index(drop=True)
    with pytest.raises(ValueError, match="row counts"):
        _validate_alignment(
            bad_X,
            y,
            index,
            y_column="y_t1",
            target_column="target_period_t1",
            development_X=development_X,
        )

    permuted = X.iloc[[1, 0]].reset_index(drop=True)
    with pytest.raises(ValueError, match="feature_row linkage order"):
        _validate_alignment(
            permuted,
            y,
            index,
            y_column="y_t1",
            target_column="target_period_t1",
            development_X=development_X,
        )


class _Dataset:
    def __init__(self, target_column: str, targets: list[str]) -> None:
        self.window_id = "2024-06_t1"
        self.target_column = target_column
        self.train_index = _index(target_column, ["2024-06", "2024-07"])
        self.validation_index = _index(target_column, targets)


def test_future_targets_are_rejected_before_evaluation() -> None:
    ok = cast(WindowDataset, _Dataset("target_period_t1", ["2024-07", "2024-08"]))
    _enforce_window_rules(ok, reserved_start="2025-01")

    leaking = cast(WindowDataset, _Dataset("target_period_t1", ["2024-12", "2025-01"]))
    with pytest.raises(ValueError, match="reserved targets"):
        _enforce_window_rules(leaking, reserved_start="2025-01")

    train_leak = cast(WindowDataset, _Dataset("target_period_t1", ["2024-11", "2024-12"]))
    train_leak.train_index.loc[1, "target_period_t1"] = "2025-01"
    with pytest.raises(ValueError, match="reserved training targets"):
        _enforce_window_rules(train_leak, reserved_start="2025-01")


def test_train_prevalence_uses_train_only_and_is_constant() -> None:
    train_y = pd.Series([1, 0, 1, 1], dtype="Int64")
    predictions, prevalence = train_prevalence_reference(train_y, rows=3)
    assert prevalence == pytest.approx(0.75)
    assert predictions["prediction_probability"].tolist() == [0.75, 0.75, 0.75]
    assert predictions["prediction_label"].isna().all()


def test_persistence_reference_is_horizon_specific_and_deterministic() -> None:
    X = pd.DataFrame(
        {
            "zona_canal_t": pd.Series(["EXCESO", "ALERTA", pd.NA], dtype="string"),
            "municipality_code": pd.Series(["50001", "50001", "50001"], dtype="string"),
        }
    )
    t1 = persistence_reference(X, horizon=1)
    t2 = persistence_reference(X, horizon=2)
    assert t1["horizon"].tolist() == [1, 1, 1]
    assert t2["horizon"].tolist() == [2, 2, 2]
    assert t1["prediction_label"].tolist() == [1, 0, pd.NA]
    assert t1["prediction_kind"].eq("deterministic").all()


def test_metrics_with_empty_denominators_are_non_evaluable() -> None:
    y_all_zero = pd.Series([0, 0, 0], dtype="Int64")
    y_all_one = pd.Series([1, 1], dtype="Int64")
    scores = pd.Series([0.1, 0.2, 0.3], dtype="Float64")
    probs = pd.Series([pd.NA, pd.NA], dtype="Float64")
    labels = pd.Series([0, 0], dtype="Int64")
    index = _index("target_period_t1", ["2024-02", "2024-03"])

    ap = average_precision_metric(y_all_zero, scores)
    assert not ap["evaluable"]

    onset = onset_sensitivity_metric(y_all_one, labels, index, target_column="target_period_t1")
    assert not onset["evaluable"]

    far = false_alarm_ratio_metric(
        pd.Series([0, 0], dtype="Int64"),
        pd.Series([0, 0], dtype="Int64"),
    )
    assert not far["evaluable"]

    brier = brier_metric(y_all_one, probs)
    assert not brier["evaluable"]


def test_probabilistic_reference_needs_threshold_policy_for_event_metrics() -> None:
    y = pd.Series([0, 1, 1], dtype="Int64")
    index = _index("target_period_t1", ["2024-02", "2024-03", "2024-04"])
    predictions = pd.DataFrame(
        {
            "prediction_kind": ["probabilistic"] * 3,
            "prediction_score": pd.Series([0.2, 0.6, 0.6], dtype="Float64"),
            "prediction_probability": pd.Series([0.2, 0.6, 0.6], dtype="Float64"),
            "prediction_label": pd.Series([pd.NA, pd.NA, pd.NA], dtype="Int64"),
        }
    )
    metrics = evaluate_metrics(
        "train_prevalence",
        y,
        predictions,
        index,
        target_column="target_period_t1",
        threshold_policy_declared=False,
    )
    by_name = {row["metric"]: row for row in metrics}
    assert by_name["average_precision"]["evaluable"]
    assert by_name["brier"]["evaluable"]
    assert not by_name["onset_sensitivity"]["evaluable"]
    assert not by_name["false_alarm_ratio"]["evaluable"]


def test_empty_prediction_frame_returns_non_evaluable_metrics() -> None:
    y = pd.Series([], dtype="Int64")
    index = pd.DataFrame(
        {
            "municipality_code": pd.Series([], dtype="string"),
            "year_month": pd.Series([], dtype="string"),
            "target_period_t1": pd.Series([], dtype="string"),
            "feature_row": pd.Series([], dtype="Int64"),
        }
    )
    predictions = pd.DataFrame(
        {
            "prediction_kind": pd.Series([], dtype="string"),
            "prediction_score": pd.Series([], dtype="Float64"),
            "prediction_probability": pd.Series([], dtype="Float64"),
            "prediction_label": pd.Series([], dtype="Int64"),
        }
    )
    metrics = evaluate_metrics(
        "train_prevalence",
        y,
        predictions,
        index,
        target_column="target_period_t1",
        threshold_policy_declared=False,
    )
    assert len(metrics) == 4
    assert all(not row["evaluable"] for row in metrics)


def test_artifact_verification_detects_tampering(tmp_path: Path) -> None:
    payloads = {
        "predictions.csv": b"a,b\n1,2\n",
        "manifest.json": b"{}\n",
    }
    bundle = publish_artifacts(tmp_path, "a" * 64, payloads)
    verify_artifacts(bundle, payloads)

    (bundle / "predictions.csv").write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="stale|corrupted"):
        verify_artifacts(bundle, payloads)
