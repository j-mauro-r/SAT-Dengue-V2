"""Annual shared metrics and paired circular-block utility uncertainty."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.evaluation_metrics import evaluate_comparison_metrics
from scripts.model_assessment.policy import utility
from scripts.model_evaluation.decision_policy import (
    ChampionDecisionPolicy,
    load_decision_policy,
)

from .cohorts import Cohort


def metric_records(
    candidate: str, cohort: Cohort, predictions: pd.DataFrame, positions: pd.Index
) -> list[dict[str, Any]]:
    """Evaluate aligned original scientific states without rebuilding onsets.

    Args:
        candidate: Procedure name.
        cohort: Original annual keys, nullable labels and original event context.
        predictions: Aligned complete prediction frame.
        positions: Annual or subgroup row positions.

    Returns:
        Shared metrics, explicitly unavailable if selected outcomes are unknown.
    """
    y = cohort.y.loc[positions]
    context = cohort.context.loc[positions]
    # Shared event consistency uses original S. Unknown selected Y makes all
    # metric values unavailable; source event support remains explicitly reported.
    evaluation_y = context.actual_excess if y.isna().any() else y
    records = evaluate_comparison_metrics(
        candidate,
        evaluation_y,
        predictions.loc[positions],
        cohort.index.loc[positions],
        target_column="target_period",
        threshold_policy_declared=True,
        event_context=context,
    )
    if y.isna().any():
        for record in records:
            if candidate == "persistence" and record["metric"] == "brier":
                continue
            record.update(
                value=None,
                evaluable=False,
                detail="unavailable_selected_labels; source_event_support_retained",
                missing_selected_labels=int(y.isna().sum()),
            )
    return records


def circular_draws(
    months: int, *, resamples: int = 2000, block: int = 3, seed: int = 42
) -> np.ndarray:
    """Generate common circular moving blocks, independent of outcomes or candidate.

    Args:
        months: Number of original months.
        resamples: Frozen draw count.
        block: Frozen consecutive block length.
        seed: Frozen random seed.

    Returns:
        Integer month positions; entire municipal panels use each selected position.
    """
    rng = np.random.default_rng(seed)
    starts = rng.integers(0, months, size=(resamples, (months + block - 1) // block))
    return ((starts[:, :, None] + np.arange(block)) % months).reshape(resamples, -1)[:, :months]


def research_result(
    complete: bool,
    onset_gain: float,
    far_increase: float,
    lower_onset: float,
    upper_far: float,
    decision_policy: ChampionDecisionPolicy | None = None,
) -> str:
    """Apply frozen three-way acceptance without treating absent support as success.

    Args:
        complete: All required annual evidence, coverage and context are available.
        onset_gain: Annual sensitivity difference.
        far_increase: Annual false/emitted difference.
        lower_onset: Marginal lower sensitivity-gain bound.
        upper_far: Marginal upper false/emitted-increase bound.
        decision_policy: Validated policy; repository policy is loaded when omitted.

    Returns:
        Frozen research classification, never a G5 or champion decision.
    """
    if not complete or not np.isfinite([onset_gain, far_increase]).all():
        return "insufficient_evidence"
    policy = decision_policy or load_decision_policy(Path(__file__).resolve().parents[2])
    if utility(onset_gain, far_increase, policy) != "meets_point_criteria":
        return "does_not_meet"
    if not np.isfinite([lower_onset, upper_far]).all():
        return "insufficient_evidence"
    return (
        "meets_research_criteria"
        if lower_onset >= policy.knobs.min_onset_sensitivity_gain
        and upper_far <= policy.knobs.max_false_alarm_increase
        else "insufficient_evidence"
    )


def evaluate_horizon(
    cohort: Cohort, predictions: dict[str, pd.DataFrame], settings: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Evaluate the full annual cohort and common paired monthly-block resamples.

    Args:
        cohort: Fixed annual population and original event states.
        predictions: All three families plus persistence on identical keys.
        settings: Frozen uncertainty settings from the exact proposal.

    Returns:
        Comparative annual table, detailed metrics, marginal intervals and shared draws.
    """
    if set(predictions) != {"xgboost", "lightgbm", "gam", "persistence"}:
        raise ValueError("All six procedures require each horizon's three families and reference")
    if (
        settings["block_months"],
        settings["resamples"],
        settings["seed"],
        settings["percentiles"],
    ) != (3, 2000, 42, [2.5, 97.5]):
        raise ValueError("Frozen uncertainty policy changed")
    months = sorted(cohort.index.target_period.unique())
    draws = circular_draws(len(months))
    records = []
    for candidate, prediction in predictions.items():
        if not prediction.index.equals(cohort.index.index):
            raise ValueError("Candidate/reference row indices differ")
        groups = [("annual", "all", cohort.index.index)]
        for scope, codes in [
            ("period", cohort.index.target_period),
            ("department", cohort.index.municipality_code.str[:2]),
            ("municipality", cohort.index.municipality_code),
        ]:
            groups += [(scope, str(code), members.index) for code, members in codes.groupby(codes)]
        for scope, group, positions in groups:
            records += [
                dict(
                    r,
                    candidate=candidate,
                    horizon=cohort.horizon,
                    scope=scope,
                    group_id=group,
                    rows=len(positions),
                )
                for r in metric_records(candidate, cohort, prediction, positions)
            ]
    metrics = pd.DataFrame(records)
    annual = metrics[metrics.scope.eq("annual")]
    monthly = metrics[metrics.scope.eq("period")]
    sampled: dict[tuple[str, str], np.ndarray] = {}
    for candidate in predictions:
        for metric in ["onset_sensitivity", "false_alarm_ratio"]:
            rows = (
                monthly[monthly.candidate.eq(candidate) & monthly.metric.eq(metric)]
                .set_index("group_id")
                .loc[months]
            )
            numerator = rows.numerator.to_numpy(dtype=float)[draws].sum(axis=1)
            denominator = rows.denominator.to_numpy(dtype=float)[draws].sum(axis=1)
            # A month with zero alerts/onsets may become evaluable in the full draw;
            # missing predictions/labels/context may not disappear silently.
            missing = (
                cohort.y.isna().any()
                or predictions[candidate].prediction_label.isna().any()
                or not cohort.context.onset_evaluable.all()
            )
            sampled[candidate, metric] = np.divide(
                numerator, denominator, out=np.full(len(draws), np.nan), where=(denominator > 0)
            )
            if missing:
                sampled[candidate, metric][:] = np.nan
    intervals, comparison = [], []
    wide = annual.pivot(index="candidate", columns="metric", values="value").astype(float)
    for candidate in predictions:
        current = annual[annual.candidate.eq(candidate)].set_index("metric")
        row = dict(
            candidate=candidate,
            horizon=cohort.horizon,
            examples=len(cohort.index),
            municipalities=cohort.index.municipality_code.nunique(),
            target_months=len(months),
            predictions_available=int(predictions[candidate].prediction_score.notna().sum()),
            labels_available=int(cohort.y.notna().sum()),
            unknown_event_rows=int((~cohort.context.onset_evaluable).sum()),
            **wide.loc[candidate].to_dict(),
        )
        for metric in wide.columns:
            row[f"difference_{metric}_vs_persistence"] = (
                wide.loc[candidate, metric] - wide.loc["persistence", metric]
            )
        row.update(
            detected_onsets=int(current.loc["onset_sensitivity", "numerator"]),
            real_onsets=int(current.loc["onset_sensitivity", "denominator"]),
            false_alerts=int(current.loc["false_alarm_ratio", "numerator"]),
            emitted_alerts=int(current.loc["false_alarm_ratio", "denominator"]),
        )
        bounds = {}
        for metric in ["onset_sensitivity", "false_alarm_ratio"]:
            delta = sampled[candidate, metric] - sampled["persistence", metric]
            valid = np.isfinite(delta)
            lower, upper = np.quantile(delta, [0.025, 0.975]) if valid.all() else [np.nan, np.nan]
            bounds[metric] = (lower, upper)
            intervals.append(
                dict(
                    candidate=candidate,
                    horizon=cohort.horizon,
                    metric=metric,
                    lower=lower,
                    upper=upper,
                    valid_resamples=int(valid.sum()),
                    resamples=len(draws),
                    interpretation=(
                        "candidatewise_marginal; no_simultaneous_or_postselection_independence"
                    ),
                )
            )
            row[f"lower_difference_{metric}"] = lower
            row[f"upper_difference_{metric}"] = upper
        required = ["average_precision", "brier", "onset_sensitivity", "false_alarm_ratio"]
        complete = bool(
            current.loc[required, "evaluable"].all()
            and cohort.context.onset_evaluable.all()
            and cohort.y.notna().all()
            and predictions[candidate].prediction_score.notna().all()
        )
        row["result"] = (
            "reference"
            if candidate == "persistence"
            else research_result(
                complete,
                row["difference_onset_sensitivity_vs_persistence"],
                row["difference_false_alarm_ratio_vs_persistence"],
                bounds["onset_sensitivity"][0],
                bounds["false_alarm_ratio"][1],
            )
        )
        comparison.append(row)
    return pd.DataFrame(comparison), metrics, pd.DataFrame(intervals), draws
