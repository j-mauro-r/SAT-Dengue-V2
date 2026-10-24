"""Critical Stage 5 assessment boundaries and approved utility semantics."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.datasets.legacy_evaluation.model_assessment.policy import (
    proposed_calendar,
    require_development,
    utility,
)
from sat_dengue.datasets.legacy_evaluation.model_evaluation.availability import (
    availability_transition,
)
from sat_dengue.datasets.legacy_evaluation.model_evaluation.contract import ModelEvaluationError
from sat_dengue.datasets.legacy_evaluation.model_evaluation.decision_policy import (
    load_decision_policy,
)
from sat_dengue.metrics import false_alarm_ratio_metric, onset_sensitivity_metric


def test_early_t2_origin_rejects_december_component() -> None:
    """January2025 T2 cannot consume labels through December2024."""
    with pytest.raises(ModelEvaluationError, match="availability"):
        availability_transition(
            pd.Series(["2024-12"]),
            pd.Series(["2024-11"]),
            dependencies={},
            producer="outer",
            consumer="January2025_t2",
        )
    calendar = proposed_calendar(2)
    assert calendar["origins"][0] == "2024-11"
    assert calendar["training_target_end"] == "2024-11"


def test_reserved_targets_rejected_before_development_selection() -> None:
    """The boundary follows targets rather than origins or calendar years of fitting."""
    require_development(pd.Series(["2012-01", "2024-12"]))
    with pytest.raises(ValueError, match="Reserved"):
        require_development(pd.Series(["2024-12", "2025-01"]))


def test_utility_uses_onsets_and_emitted_alerts_with_fixed_knobs() -> None:
    """Continuing excess and true negatives must not inflate utility denominators."""
    y = pd.Series([1, 1, 0, 0, 0], dtype="Int64")
    alerts = pd.Series([1, 0, 1, 0, 0], dtype="Int64")
    index = pd.DataFrame(
        {
            "municipality_code": ["50001"] * 5,
            "target_period": ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        }
    )
    context = index.assign(
        actual_excess=y,
        previous_excess=pd.Series([0, 1, 1, 0, 0], dtype="Int64"),
        actual_onset=[True, False, False, False, False],
        onset_evaluable=True,
    )
    onset = onset_sensitivity_metric(
        y, alerts, index, target_column="target_period", event_context=context
    )
    far = false_alarm_ratio_metric(y, alerts)
    assert (onset["numerator"], onset["denominator"]) == (1, 1)
    assert (far["numerator"], far["denominator"]) == (1, 2)
    assert utility(0.10, 0.05) == "meets_point_criteria"
    assert utility(0.099, 0.05) == "does_not_meet_point_criteria"
    assert utility(0.10, 0.051) == "does_not_meet_point_criteria"
    assert utility(None, 0.0) == "insufficient_evidence"

    policy = load_decision_policy(Path(__file__).resolve().parents[2])
    adjusted = replace(
        policy,
        knobs=replace(
            policy.knobs,
            max_false_alarm_increase_pp=6.0,
            min_onset_sensitivity_gain_pp=9.0,
        ),
    )
    assert utility(0.09, 0.06, adjusted) == "meets_point_criteria"


@pytest.mark.parametrize("change", ["none", "science", "code", "summary", "corrupt", "missing"])
def test_reexecution_requires_exact_audited_science(tmp_path: Path, change: str) -> None:
    """Accept new provenance only; do not bless altered science or missing anchors."""
    from sat_dengue.datasets.legacy_evaluation.model_assessment.input_validation import (
        verify_equivalent_input,
    )

    def write_bundle(name: str, *, updated: bool) -> Path:
        bundle = tmp_path / name
        bundle.mkdir()
        summary = {
            "stage4_reference_bundle": "new-ref" if updated else "old-ref",
            "stage4_suite_bundle": "new-suite" if updated else "old-suite",
            "status": "PASS",
        }
        if updated and change == "summary":
            summary["status"] = "changed"
        payloads = {
            "predictions.csv": b"different" if updated and change == "science" else b"stable",
            "run_summary.json": json.dumps(summary).encode(),
        }
        manifest: dict[str, Any] = {
            "bundle_id": name,
            "schema": "stage5",
            "rules": {"horizon": 2},
            "identity": {
                "code": "changed" if updated and change == "code" else "stable",
                "stage4_reference_manifest": "new" if updated else "old",
            },
            "stage4_reference_bundle": summary["stage4_reference_bundle"],
            "stage4_candidate_suite_bundle": summary["stage4_suite_bundle"],
            "files": {},
        }
        for file, data in payloads.items():
            (bundle / file).write_bytes(data)
            manifest["files"][file] = {
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        (bundle / "manifest.json").write_text(json.dumps(manifest))
        return bundle

    anchor = write_bundle("anchor", updated=False)
    current = write_bundle("rerun", updated=True)
    if change == "corrupt":
        (current / "predictions.csv").write_bytes(b"tampered")
    if change == "missing":
        (anchor / "manifest.json").unlink()
    if change == "none":
        receipt = verify_equivalent_input(current, anchor)
        assert receipt["status"] == "scientifically_identical_rerun"
        assert receipt["human_gate_approval"] is False
        assert verify_equivalent_input(anchor, anchor)["status"] == "exact_audited_input"
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            verify_equivalent_input(current, anchor)


@pytest.mark.parametrize("scores", [[0.1, 0.4, 0.4, 0.8], [0.9, 0.3, 0.2, 0.7]])
def test_auroc_matches_independent_pairwise_reference(scores: list[float]) -> None:
    """Positive/negative pairs give ties half-credit, independently of sklearn."""
    from sat_dengue.metrics import auroc_metric

    y = pd.Series([0, 1, 0, 1], dtype="Int64")
    score = pd.Series(scores)
    expected = (
        sum(float(p > n) + 0.5 * float(p == n) for p in score[y.eq(1)] for n in score[y.eq(0)]) / 4
    )
    result = auroc_metric(y, score)
    assert result["value"] == pytest.approx(expected)
    assert (result["positive_rows"], result["negative_rows"]) == (2, 2)


def test_auroc_preserves_population_and_alignment_policy() -> None:
    """Single-class/missing populations stay unavailable; invalid alignment rejects."""
    from sat_dengue.metrics import auroc_metric

    score = pd.Series([0.1, 0.9])
    result = auroc_metric(pd.Series([1, 1]), score)
    assert result["value"] is None and result["detail"] == "insufficient_classes_or_rows"
    result = auroc_metric(pd.Series([0, 1]), pd.Series([0.1, None]))
    assert result["value"] is None and result["denominator"] == 2
    assert result["missing_predictions"] == 1
    with pytest.raises(ValueError, match="aligned"):
        auroc_metric(pd.Series([0, 1], index=[1, 0]), score)
    with pytest.raises(ValueError, match="finite"):
        auroc_metric(pd.Series([0, 1]), pd.Series([0.1, float("inf")]))


def test_auroc_equal_window_mean_never_discards_unavailable_window() -> None:
    """Window means require all four windows and cannot silently shrink coverage."""
    from sat_dengue.datasets.legacy_evaluation.model_assessment.comparison import summarize

    records = [
        dict(
            candidate=c,
            horizon=h,
            window_id=f"{w}_t{h}",
            metric=m,
            value=v,
            evaluable=True,
            numerator=1,
            denominator=2,
        )
        for c in ("xgboost", "lightgbm", "gam", "persistence")
        for h in (1, 2)
        for w, v in enumerate((0.2, 0.4, 0.6, 0.8))
        for m in ("average_precision", "brier", "onset_sensitivity", "false_alarm_ratio", "auroc")
    ]
    metrics = pd.DataFrame(records)
    summary, _, _ = summarize(metrics)
    row = summary[
        summary.candidate.eq("xgboost") & summary.horizon.eq(1) & summary.metric.eq("auroc")
    ].iloc[0]
    assert row.value == pytest.approx(0.5)
    affected = metrics.candidate.eq("xgboost") & metrics.horizon.eq(1) & metrics.metric.eq("auroc")
    metrics.loc[affected & metrics.window_id.eq("0_t1"), ["value", "evaluable"]] = [None, False]
    summary, _, _ = summarize(metrics)
    row = summary[
        summary.candidate.eq("xgboost") & summary.horizon.eq(1) & summary.metric.eq("auroc")
    ].iloc[0]
    assert pd.isna(row.value) and row.evaluable_windows == 3
    with pytest.raises(ValueError, match="four unique windows"):
        summarize(metrics.iloc[1:])


def test_six_proposals_retain_every_family_and_early_t2_origin(tmp_path: Path) -> None:
    """Six combinations survive without utility screening or final training."""
    from sat_dengue.datasets.legacy_evaluation.model_assessment.proposal import (
        FAMILIES,
        freeze_proposal,
    )
    from sat_dengue.datasets.legacy_evaluation.model_evaluation.availability import ROLES

    calibrators: list[dict[str, Any]] = []
    thresholds: list[dict[str, Any]] = []
    transitions: list[dict[str, Any]] = []
    for h in (1, 2):
        for family in FAMILIES:
            window = f"2024-06_t{h}"
            selected = f"{family}_01"
            (tmp_path / f"{family}_{window}_internal_components.json").write_text(
                json.dumps({"selected_id": selected, "selected_parameters": {"seed": 42}})
            )
            (tmp_path / f"{family}_{window}_outer_preparer.json").write_text(
                json.dumps({"spec": {"kind": "fixture"}, "input_columns": ["dengue_lag_1"]})
            )
            calibrators.append(
                dict(
                    candidate=family,
                    window_id=window,
                    selected_configuration_id=selected,
                    calibration_choice="original",
                )
            )
            thresholds.append(
                dict(
                    candidate=family,
                    window_id=window,
                    selected_configuration_id=selected,
                    selected_threshold=0.123456789012345,
                )
            )
            transitions.extend(
                dict(
                    candidate=family,
                    window_id=window,
                    producer_role=role,
                    producer_target_max="2024-03",
                    dependencies="{}",
                    effective_availability="2024-03",
                )
                for role in ROLES
            )
    (tmp_path / "calibrators.json").write_text(json.dumps({"calibrators": calibrators}))
    pd.DataFrame(thresholds).to_csv(tmp_path / "threshold_selection.csv", index=False)
    pd.DataFrame(transitions).to_csv(tmp_path / "availability_transitions.csv", index=False)
    final = dict(
        families=list(FAMILIES),
        target_start="2025-01",
        target_end="2025-12",
        outer_training_target_start="2012-01",
        outer_training_target_end={"1": "2024-12", "2": "2024-11"},
    )
    result = freeze_proposal(
        tmp_path, {"proposed_final": final}, [str(50000 + i) for i in range(76)]
    )
    assert {(p["candidate"], p["horizon"]) for p in result["procedures"]} == {
        (f, h) for f in FAMILIES for h in (1, 2)
    }
    assert result["new_fit_budget_after_explicit_acceptance"]["outer_models"] == 6
    assert result["fit_budget_consumed"] == 0
    for p in result["procedures"]:
        assert p["retained_threshold"]["selected_threshold"] == 0.123456789012345
        assert p["training_target_end"] <= p["origins"][0]
        if p["horizon"] == 2:
            assert p["origins"][0] == "2024-11" and p["targets"][0] == "2025-01"
