from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments.exp04 import (
    apply_calibrator,
    calibration_window,
    evaluate_frozen,
    fit_calibrator,
    temporal_roles,
    threshold_policy,
)
from sat_dengue.experiments.exp04_baseline import audit_baseline, common_exposure, paired_support


def score_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": ["50001", "73001", "50001", "73001"],
            "target_month": ["2019-01", "2019-01", "2019-02", "2019-02"],
            "raw_score": [0.1, 0.3, 0.6, 0.8],
            "truth": [0, 0, 1, 1],
            "error_class": ["no_excess", "no_excess", "onset", "onset"],
        }
    )


def test_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Control 2: preserve mandatory M00 and identical common-cohort exposure."""
    monkeypatch.chdir(tmp_path)
    missing = audit_baseline()
    assert missing["status"] == "BLOCKED_BASELINE"
    assert missing["reconstruction_identity"] is None
    directory = Path("tmp/baseline")
    directory.mkdir(parents=True)
    (directory / "bundle.json").write_text(json.dumps({"source_variant": "M00"}))
    (directory / "manifest.json").write_text("{}")
    with pytest.raises(ValueError, match="exact original"):
        audit_baseline(directory)
    with pytest.raises(ValueError, match="repository-local"):
        audit_baseline(Path("/etc"))
    frame = score_frame()
    assert common_exposure(frame) == 4 / 12
    assert paired_support(frame, frame.iloc[::-1])["common_exposure"] == 4 / 12
    assert paired_support(frame, frame.iloc[:3])["status"] == "NOT_EVALUABLE"
    changed = frame.copy()
    changed.loc[0, "truth"] = 1
    assert paired_support(frame, changed)["status"] == "NOT_EVALUABLE"
    changed = frame.copy()
    changed.loc[0, "raw_score"] = 0.2
    assert paired_support(frame, changed)["reason"] == "base_predictor_scores_differ"
    with pytest.raises(ValueError, match="duplicate"):
        common_exposure(pd.concat([frame, frame]))
    later = frame.copy()
    later.loc[0, "target_month"] = "2025-01"
    with pytest.raises(ValueError, match="2025"):
        common_exposure(later)


def temporal_frame(start: str, end: str, horizon: int = 2) -> pd.DataFrame:
    rows = []
    for i, month in enumerate(pd.period_range(start, end, freq="M")):
        for j, code in enumerate(("50001", "50002", "73001", "73002")):
            truth = int((i + j) % 3 == 0)
            rows.append(
                {
                    "municipality_code": code,
                    "target_month": str(month),
                    "forecast_issue_date": str((month - horizon).start_time.date()),
                    "target_date": str(month.start_time.date()),
                    "label_available_date": str((month.start_time + pd.Timedelta(days=14)).date()),
                    "training_cutoff": "2014-01-01",
                    "raw_score": float(((i * 3 + j * 7) % 19 + 1) / 21),
                    "truth": truth,
                    "error_class": "onset" if truth else "no_excess",
                    "selection_block": str(month.year) + ("a" if month.month < 7 else "b"),
                }
            )
    return pd.DataFrame(rows)


def test_temporal() -> None:
    """Control 3: mature OOF roles, fixed policies and whole ties with adversarial cases."""
    cal = temporal_frame("2016-01", "2018-12")
    sel = temporal_frame("2019-04", "2019-12")
    ev = temporal_frame("2020-03", "2020-12")
    kwargs: dict[str, Any] = {
        "horizon": 2,
        "calibration_cutoff": "2019-01-15",
        "decision_date": "2019-12-31",
    }
    assert temporal_roles(cal, sel, ev, **kwargs)["status"] == "evaluable"
    for change, message in (
        ({"training_cutoff": "2020-01-01"}, "In-sample"),
        ({"label_available_date": "2020-01-01"}, "Immature"),
    ):
        corrupt = cal.copy()
        for key, value in change.items():
            corrupt.loc[0, key] = value
        with pytest.raises(ValueError, match=message):
            temporal_roles(corrupt, sel, ev, **kwargs)
    with pytest.raises(ValueError, match="horizon drift"):
        temporal_roles(cal, sel, ev, **{**kwargs, "horizon": 1})
    with pytest.raises(ValueError, match="Evaluation precedes"):
        temporal_roles(cal, sel, ev, **{**kwargs, "decision_date": "2020-02-01"})
    for months in (None, 12, 24, 36):
        chosen, support = calibration_window(
            cal, months=months, last_mature_month="2018-12", cutoff="2019-01-15"
        )
        assert support["status"] == "evaluable"
        assert chosen.target_month.nunique() == (months or 36)
    gap = cal.loc[cal.target_month.ne("2018-06")]
    assert (
        calibration_window(gap, months=12, last_mature_month="2018-12", cutoff="2019-01-15")[1][
            "status"
        ]
        == "NOT_EVALUABLE"
    )
    assert fit_calibrator(cal, method="isotonic", seed=1)["status"] == "NOT_EVALUABLE"
    for method in ("sigmoid", "isotonic", "identity"):
        state = fit_calibrator(cal, method=method, seed=1, minimum_class_support=2)
        scored = sel.copy()
        scored["score"] = apply_calibrator(sel, state)
        for policy in ("C0", "C1", "C2"):
            threshold = threshold_policy(scored, policy=policy)
            assert threshold.get("status") != "NOT_EVALUABLE"
            assert threshold["false_alerts"] / common_exposure(sel) <= 1
            if policy == "C2":
                alerts = (
                    pd.Series(False, index=scored.index)
                    if threshold["threshold"] is None
                    else scored.score.ge(threshold["threshold"])
                )
                for _, block in scored.groupby("selection_block"):
                    assert (
                        int((alerts.loc[block.index] & block.truth.eq(0)).sum())
                        / common_exposure(block)
                        <= 1
                    )
        assert (
            threshold_policy(scored, policy="C0")["threshold"]
            == threshold_policy(scored, policy="C1")["threshold"]
        )
        before = json.dumps(state, sort_keys=True)
        rows, metrics = evaluate_frozen(
            ev, state, threshold["threshold"], bins=10, objective="onset", historical_exposure=10
        )
        assert json.dumps(state, sort_keys=True) == before
        assert metrics["common_exposure"] == len(ev) / 12
        assert metrics["historical_FA_rate"] == metrics["false_alerts"] / 10
        assert metrics["common_FA_rate"] == metrics["false_alerts"] / (len(ev) / 12)
        assert metrics["uncertainty"]["status"] == "UNAVAILABLE"
        assert len(rows) == len(ev)
    one = scored.assign(selection_block="one")
    assert threshold_policy(one, policy="C2")["status"] == "NOT_EVALUABLE"
    tied = scored.copy()
    tied["score"] = 0.5
    selected = threshold_policy(tied, policy="C1")
    assert selected["threshold"] is None  # Cannot split a tied group to meet the budget.
    assert selected["alerts"] == 0
    interleaved = scored.assign(selection_block=[i % 2 for i in range(len(scored))])
    with pytest.raises(ValueError, match="chronological"):
        threshold_policy(interleaved, policy="C2")
    with pytest.raises(ValueError, match="excess-control"):
        threshold_policy(scored, policy="C1", objective="excess_control")
