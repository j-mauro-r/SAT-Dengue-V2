"""Independent scientific regressions for tied scores and calendar event context."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from scripts.model_training.contract import ModelTrainingConfig
from scripts.model_training.events import build_event_context, load_event_context
from scripts.model_training.loading import TemporalSource, WindowDataset
from scripts.model_training.metrics import (
    average_precision_metric,
    brier_metric,
    onset_sensitivity_metric,
)
from scripts.model_training.persistence import bytes_record, json_bytes, serialize_table
from scripts.model_training.pipeline import _build_window_outputs


@pytest.mark.parametrize(
    ("labels", "scores", "expected"),
    [
        ([1, 0], [0.5, 0.5], 0.5),
        ([1, 0, 1, 0, 1], [0.9, 0.7, 0.7, 0.2, 0.2], 34 / 45),
        ([1, 0, 1, 0], [1.0, 1.0, 0.0, 0.0], 0.5),
        ([1, 0, 1, 0, 1], [0.3] * 5, 0.6),
        ([0, 1, 1, 0], [0.2, 0.8, 0.9, 0.1], 1.0),
    ],
)
def test_ap_threshold_groups_and_every_permutation(
    labels: list[int], scores: list[float], expected: float
) -> None:
    # Expected fractions above are hand-derived from grouped precision/recall steps.
    for order in permutations(range(len(labels))):
        result = average_precision_metric(
            pd.Series([labels[i] for i in order]), pd.Series([scores[i] for i in order])
        )
        assert result["value"] == pytest.approx(expected)
        assert result["denominator"] == len(labels)


@pytest.mark.parametrize("labels", [[], [0, 0], [1, 1]])
def test_ap_empty_or_insufficient_classes(labels: list[int]) -> None:
    result = average_precision_metric(
        pd.Series(labels, dtype="Int64"), pd.Series([0.5] * len(labels))
    )
    assert not result["evaluable"] and result["value"] is None


@pytest.mark.parametrize("scores", [[np.inf, 0.5], [-np.inf, 0.5], ["broken", 0.5]])
def test_ap_invalid_scores_rejected(scores: list[object]) -> None:
    with pytest.raises((ValueError, TypeError)):
        average_precision_metric(pd.Series([1, 0]), pd.Series(scores))


@pytest.mark.parametrize("labels", [[2, 0], [0.5, 0], [np.inf, 0]])
def test_ap_invalid_labels_rejected(labels: list[float]) -> None:
    with pytest.raises(ValueError):
        average_precision_metric(pd.Series(labels), pd.Series([0.5, 0.5]))


def test_missing_prediction_or_label_never_silently_selects_a_subset() -> None:
    for labels, scores in [([1, 0, 1], [0.7, 0.2, np.nan]), ([1, 0, None], [0.7, 0.2, 0.4])]:
        ap = average_precision_metric(pd.Series(labels), pd.Series(scores))
        brier = brier_metric(pd.Series(labels), pd.Series(scores))
        assert ap["value"] is None and brier["value"] is None
        assert ap["denominator"] == brier["denominator"] == 3
    with pytest.raises(ValueError, match="aligned"):
        average_precision_metric(
            pd.Series([1, 0], index=[0, 1]), pd.Series([0.5, 0.5], index=[1, 0])
        )


def _states(rows: Sequence[tuple[str, str, int | None]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["municipality_code", "target_period", "excess"])


def _selected(rows: list[tuple[str, str]], horizon: int = 1) -> pd.DataFrame:
    frame = pd.DataFrame(rows, columns=["municipality_code", f"target_period_t{horizon}"]).astype(
        "string"
    )
    frame["year_month"] = (
        pd.PeriodIndex(frame[f"target_period_t{horizon}"], freq="M") - horizon
    ).astype(str)
    frame["feature_row"] = range(len(frame))
    return frame


def test_first_validation_month_and_december_january_boundary() -> None:
    index = _selected([("A", "2019-01")])
    context = build_event_context(
        index, _states([("A", "2018-12", 0), ("A", "2019-01", 1)]), target_column="target_period_t1"
    )
    result = onset_sensitivity_metric(
        pd.Series([1], dtype="Int64"),
        pd.Series([1]),
        index,
        target_column="target_period_t1",
        event_context=context,
    )
    assert result["denominator"] == result["numerator"] == 1
    assert result["value"] == 1
    assert context.previous_target_period.tolist() == ["2018-12"]


@pytest.mark.parametrize("previous", [[], [("A", "2018-12", None)]])
def test_absent_or_unknown_calendar_predecessor_not_last_available(
    previous: list[tuple[str, str, int | None]],
) -> None:
    index = _selected([("A", "2019-01")])
    context = build_event_context(
        index,
        _states([("A", "2018-11", 0), *previous, ("A", "2019-01", 1)]),
        target_column="target_period_t1",
    )
    assert context.actual_onset.isna().all()
    result = onset_sensitivity_metric(
        pd.Series([1], dtype="Int64"),
        pd.Series([1]),
        index,
        target_column="target_period_t1",
        event_context=context,
    )
    assert result["denominator"] == 0 and result["unknown_previous_periods"] == 1


def test_t2_uses_t1_observed_state_not_prediction_origin() -> None:
    states = _states([("A", "2018-12", 0), ("A", "2019-01", 1), ("A", "2019-02", 1)])
    t1, t2 = _selected([("A", "2019-01")], 1), _selected([("A", "2019-02")], 2)
    assert t1.year_month.tolist() == t2.year_month.tolist() == ["2018-12"]
    assert build_event_context(
        t1, states, target_column="target_period_t1"
    ).actual_onset.tolist() == [True]
    assert build_event_context(
        t2, states, target_column="target_period_t2"
    ).actual_onset.tolist() == [False]


def test_unavailable_prediction_keeps_real_onset_denominator() -> None:
    index = _selected([("A", "2019-01"), ("B", "2019-01")])
    context = build_event_context(
        index,
        _states(
            [("A", "2018-12", 0), ("B", "2018-12", 0), ("A", "2019-01", 1), ("B", "2019-01", 1)]
        ),
        target_column="target_period_t1",
    )
    result = onset_sensitivity_metric(
        pd.Series([1, 1], dtype="Int64"),
        pd.Series([1, None]),
        index,
        target_column="target_period_t1",
        event_context=context,
    )
    assert result["real_onsets"] == result["denominator"] == 2
    assert result["detected_onsets"] == 1 and result["onsets_without_prediction"] == 1
    assert result["value"] is None and result["detection_fraction_lower_bound"] == 0.5


def test_context_keys_and_target_state_must_match_selected_y() -> None:
    index = _selected([("A", "2019-01")])
    context = build_event_context(
        index, _states([("A", "2018-12", 0), ("A", "2019-01", 1)]), target_column="target_period_t1"
    )
    with pytest.raises(ValueError, match="disagrees"):
        onset_sensitivity_metric(
            pd.Series([0]),
            pd.Series([1]),
            index,
            target_column="target_period_t1",
            event_context=context,
        )
    context.loc[0, "municipality_code"] = "B"
    with pytest.raises(ValueError, match="keys"):
        onset_sensitivity_metric(
            pd.Series([1]),
            pd.Series([1]),
            index,
            target_column="target_period_t1",
            event_context=context,
        )
    with pytest.raises(ValueError, match="development"):
        build_event_context(
            _selected([("A", "2025-01")]), _states([]), target_column="target_period_t1"
        )


def test_verified_context_pipeline_against_independent_calendar_oracle(tmp_path: Path) -> None:
    # Two municipalities; missing Feb at A must not turn March into a known onset.
    raw = [
        ("A", "2018-12", 0),
        ("A", "2019-01", 1),
        ("A", "2019-03", 1),
        ("B", "2018-12", 1),
        ("B", "2019-01", 1),
        ("B", "2019-02", 0),
        ("B", "2019-03", 1),
    ]
    source_states = _states(raw)
    keys = source_states[["municipality_code", "target_period"]].rename(
        columns={"target_period": "year_month"}
    )
    features = pd.DataFrame(
        {"zona_canal_t": source_states.excess.map({0: "SEGURIDAD", 1: "EXCESO"})}
    )
    development = tmp_path / "development"
    development.mkdir()
    payloads = {"keys.csv": serialize_table(keys), "features.csv": serialize_table(features)}
    for name, data in payloads.items():
        (development / name).write_bytes(data)
    (development / "manifest.json").write_bytes(
        json_bytes({"files": {n: bytes_record(b) for n, b in payloads.items()}})
    )
    source = TemporalSource(
        tmp_path,
        {
            "development_bundle": "development",
            "identity": {"configuration": {"target_start": "2012-01"}},
        },
        pd.DataFrame(),
    )
    index = _selected([("B", "2019-03"), ("A", "2019-01"), ("A", "2019-03"), ("B", "2019-01")])
    context = load_event_context(
        ModelTrainingConfig(tmp_path), source, index, target_column="target_period_t1"
    )
    # Independent oracle uses dictionary lookup + timestamp subtraction, no production helper.
    oracle = {(m, month): excess for m, month, excess in raw}
    expected = []
    for m, target in index[["municipality_code", "target_period_t1"]].itertuples(
        index=False, name=None
    ):
        previous = (pd.Timestamp(target + "-01") - pd.DateOffset(months=1)).strftime("%Y-%m")
        before = oracle.get((m, previous))
        expected.append(None if before is None else oracle[(m, target)] == 1 and before == 0)
    assert context.actual_onset.fillna(False).tolist() == [bool(x) for x in expected]
    assert context.actual_onset.isna().tolist() == [x is None for x in expected]
    assert context.municipality_code.tolist() == index.municipality_code.tolist()
    X = pd.DataFrame({"zona_canal_t": ["EXCESO", "SEGURIDAD", "EXCESO", "SEGURIDAD"]})
    y = pd.DataFrame({"y_t1": pd.Series([1, 1, 1, 1], dtype="Int64")})
    dataset = WindowDataset(
        "2018-12_t1",
        "2018-12",
        1,
        "target_period_t1",
        "y_t1",
        X.copy(),
        pd.DataFrame({"y_t1": [1, 0]}),
        index.copy(),
        X,
        y,
        index,
    )
    before_X = X.copy(deep=True)
    predictions, metrics, _ = _build_window_outputs(
        dataset,
        {
            "persistence": {"threshold_policy": "deterministic"},
            "train_prevalence": {"threshold_policy": None},
        },
        context,
    )
    result = next(
        m for m in metrics if m["reference"] == "persistence" and m["metric"] == "onset_sensitivity"
    )
    assert result["denominator"] == 2 and result["numerator"] == 1
    assert result["excluded_unknown_context"] == 1
    pd.testing.assert_frame_equal(X, before_X)
    assert not {"actual_excess", "previous_excess", "actual_onset"}.intersection(
        predictions.columns
    )
    probability_onset = next(
        m
        for m in metrics
        if m["reference"] == "train_prevalence" and m["metric"] == "onset_sensitivity"
    )
    assert probability_onset["real_onsets"] == 2
    assert probability_onset["value"] is None
    changed_states = source_states.copy()
    changed_states.loc[
        (changed_states.municipality_code == "B") & (changed_states.target_period == "2018-12"),
        "excess",
    ] = 0
    changed_context = build_event_context(index, changed_states, target_column="target_period_t1")
    replay_predictions, replay_metrics, _ = _build_window_outputs(
        dataset,
        {
            "persistence": {"threshold_policy": "deterministic"},
            "train_prevalence": {"threshold_policy": None},
        },
        changed_context,
    )
    pd.testing.assert_frame_equal(predictions, replay_predictions)
    assert (
        next(
            m
            for m in replay_metrics
            if m["reference"] == "persistence" and m["metric"] == "onset_sensitivity"
        )["denominator"]
        == 3
    )
    # A context-file mutation must fail its declared scientific fingerprint.
    (development / "features.csv").write_text("zona_canal_t\nEXCESO\n")
    with pytest.raises(ValueError, match="fingerprint"):
        load_event_context(
            ModelTrainingConfig(tmp_path), source, index, target_column="target_period_t1"
        )
