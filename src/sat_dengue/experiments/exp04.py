"""Independent EXP04 temporal policies over explicitly supplied probability scores.

This module has no source loader, predictor fitting, model search or tracking.
Callers supply already-eligible OOF rows and explicit maturity/role dates. Real
scientific execution is gated separately; generated exercises prove behavior only.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03_1_evaluation import metrics, select_threshold
from sat_dengue.experiments.exp03_persistence import SigmoidCalibrator, fit_calibration
from sat_dengue.experiments.exp04_baseline import KEYS, common_exposure, validate_scores

DATES = ["forecast_issue_date", "target_date", "label_available_date", "training_cutoff"]


def temporal_roles(
    calibration: pd.DataFrame,
    selection: pd.DataFrame,
    evaluation: pd.DataFrame,
    *,
    horizon: int,
    calibration_cutoff: str,
    decision_date: str,
) -> dict[str, Any]:
    """Fail on immature labels, in-sample scores, crossed roles or horizon drift.

    training_cutoff is the latest label-availability date used by the predictor,
    not merely a training-row issue date. OOF provenance must be supplied; it
    cannot be reconstructed from final scores alone.
    """
    if horizon not in (1, 2):
        raise ValueError("EXP04 supports T+1/T+2 only")
    fitted = pd.Timestamp(calibration_cutoff)
    decided = pd.Timestamp(decision_date)
    if pd.isna(fitted) or pd.isna(decided) or fitted >= decided:
        raise ValueError("Calibration must freeze before threshold selection")
    prior: set[tuple[Any, ...]] = set()
    metadata = {}
    for role, frame in (
        ("calibration", calibration),
        ("selection", selection),
        ("evaluation", evaluation),
    ):
        validate_scores(frame)
        if not set(DATES) <= set(frame) or frame[DATES].isna().any().any():
            raise ValueError("Explicit OOF and label-maturity dates required")
        dates = {name: pd.to_datetime(frame[name], errors="coerce") for name in DATES}
        if any(value.isna().any() for value in dates.values()):
            raise ValueError("Invalid temporal provenance date")
        issue, target, mature, train = (dates[name] for name in DATES)
        gap = target.dt.year * 12 + target.dt.month - issue.dt.year * 12 - issue.dt.month
        if (
            not gap.eq(horizon).all()
            or not target.dt.strftime("%Y-%m").eq(frame.target_month).all()
            or (target <= issue).any()
            or (train >= issue).any()
            or (mature < target).any()
        ):
            raise ValueError("In-sample score, horizon drift or invalid maturity provenance")
        keys = set(frame[KEYS].itertuples(index=False, name=None))
        if keys & prior:
            raise ValueError("Target event overlaps temporal roles")
        prior |= keys
        if role == "calibration" and (mature > fitted).any():
            raise ValueError("Immature calibration labels")
        if role == "selection" and ((issue <= fitted).any() or (mature > decided).any()):
            raise ValueError("Selection precedes calibration freeze or uses immature labels")
        if role == "evaluation" and (issue <= decided).any():
            raise ValueError("Evaluation precedes frozen decision")
        if role != "evaluation" and target.dt.year.ge(2024).any():
            raise ValueError("2024 stress cannot fit or select")
        metadata[role] = {
            "rows": len(frame),
            "first_issue": str(issue.min().date()),
            "last_target": str(target.max().date()),
            "latest_label_available": str(mature.max().date()),
        }
    return {
        "status": "evaluable",
        "horizon": horizon,
        "calibration_cutoff": calibration_cutoff,
        "decision_date": decision_date,
        "roles": metadata,
    }


def calibration_window(
    history: pd.DataFrame, *, months: int | None, last_mature_month: str, cutoff: str
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Select exact contiguous target-month history; never fill gaps with future rows."""
    validate_scores(history)
    if months not in (None, 12, 24, 36):
        raise ValueError("EXP04 window grid is 12/24/36 months or expanding")
    if "label_available_date" not in history:
        raise ValueError("Window selection requires label maturity")
    availability = pd.to_datetime(history.label_available_date, errors="coerce")
    if availability.isna().any():
        raise ValueError("Unknown label maturity")
    last = pd.Period(last_mature_month, freq="M")
    first = last - (months - 1) if months else pd.Period(history.target_month.min(), freq="M")
    selected = history.loc[
        history.target_month.between(str(first), str(last)) & availability.le(pd.Timestamp(cutoff))
    ].copy()
    expected = {str(p) for p in pd.period_range(first, last, freq="M")}
    observed = set(selected.target_month)
    support = {
        "rows": len(selected),
        "positives": int(selected.truth.sum()),
        "negatives": int(len(selected) - selected.truth.sum()),
        "first_target": str(first),
        "last_target": str(last),
        "missing_months": sorted(expected - observed),
    }
    if not expected or expected != observed or set(selected.truth) != {0, 1}:
        return selected, {"status": "NOT_EVALUABLE", "reason": "window_or_class_support", **support}
    return selected, {"status": "evaluable", **support}


def fit_calibrator(
    frame: pd.DataFrame, *, method: str, seed: int, minimum_class_support: int | None = None
) -> dict[str, Any]:
    """Reuse M00 sigmoid; isotonic support must be explicitly predeclared by caller."""
    validate_scores(frame)
    if method == "identity":
        return {"method": method, "diagnostic_only": True}
    if method == "sigmoid":
        if set(frame.truth) != {0, 1}:
            return {"status": "NOT_EVALUABLE", "reason": "calibration_class_support"}
        fitted = fit_calibration(frame.raw_score, frame.truth.astype(int), seed)
        return {"method": method, "coefficient": fitted.coefficient, "intercept": fitted.intercept}
    if method != "isotonic":
        raise ValueError("Unsupported EXP04 calibration method")
    if minimum_class_support is None:
        return {"status": "NOT_EVALUABLE", "reason": "isotonic_support_not_predeclared"}
    if minimum_class_support < 1:
        raise ValueError("Positive predeclared isotonic class support required")
    support = frame.truth.value_counts()
    if any(int(support.get(label, 0)) < minimum_class_support for label in (0, 1)):
        return {"status": "NOT_EVALUABLE", "reason": "isotonic_class_support"}
    from sklearn.isotonic import IsotonicRegression  # type: ignore[import-untyped]

    fitted_iso = IsotonicRegression(increasing=True, out_of_bounds="clip").fit(
        frame.raw_score, frame.truth
    )
    return {
        "method": method,
        "x": fitted_iso.X_thresholds_.tolist(),
        "y": fitted_iso.y_thresholds_.tolist(),
    }


def apply_calibrator(frame: pd.DataFrame, state: dict[str, Any]) -> pd.Series:
    validate_scores(frame)
    method = state.get("method")
    if method == "sigmoid":
        if not np.isfinite([state["coefficient"], state["intercept"]]).all():
            raise ValueError("Nonfinite calibrator state")
        return SigmoidCalibrator(state["coefficient"], state["intercept"])(frame.raw_score)
    if method == "identity":
        return frame.raw_score.astype("Float64")
    if method == "isotonic":
        x, y = np.asarray(state["x"], dtype=float), np.asarray(state["y"], dtype=float)
        if (
            len(x) != len(y)
            or not len(x)
            or not np.isfinite(x).all()
            or not np.isfinite(y).all()
            or (np.diff(x) <= 0).any()
            or (np.diff(y) < 0).any()
            or (x < 0).any()
            or (x > 1).any()
            or (y < 0).any()
            or (y > 1).any()
        ):
            raise ValueError("Invalid monotone isotonic state")
        return pd.Series(np.interp(frame.raw_score, x, y), index=frame.index, dtype="Float64")
    raise ValueError("Calibrator is unavailable; fallback is forbidden")


def threshold_policy(
    frame: pd.DataFrame, *, policy: str, objective: str = "onset"
) -> dict[str, Any]:
    """C0's original selector and C1 coincide on unchanged common support.

    Historical A0 replay uses its persisted threshold, not reselection here.
    C2 additionally requires two or more chronological, noninterleaved blocks.
    """
    validate_scores(frame)
    if objective != "onset":
        raise ValueError("The onset budget cannot select an excess-control threshold")
    if "score" not in frame or frame.score.isna().any() or not frame.score.between(0, 1).all():
        raise ValueError("Complete calibrated selection scores required")
    if policy in ("C0", "C1"):
        return {
            **select_threshold(frame.truth, frame.score, exposure=common_exposure(frame)),
            "policy": policy,
            "exposure_definition": "common_eligible_months/12",
        }
    if policy != "C2":
        raise ValueError("Unknown threshold policy")
    if (
        "selection_block" not in frame
        or frame.selection_block.isna().any()
        or frame.selection_block.nunique() < 2
    ):
        return {"status": "NOT_EVALUABLE", "reason": "C2_requires_two_supported_blocks"}
    blocks = [block for _, block in frame.groupby("selection_block", sort=True)]
    blocks.sort(key=lambda block: block.target_month.min())
    for previous, current in zip(blocks, blocks[1:], strict=False):
        if previous.target_month.max() >= current.target_month.min():
            raise ValueError("C2 blocks must be chronological and nonoverlapping")
    if any(set(b.truth) != {0, 1} for b in blocks):
        return {"status": "NOT_EVALUABLE", "reason": "C2_block_class_support"}
    feasible = []
    for threshold in [None, *sorted(set(frame.score), reverse=True)]:
        alert = (
            pd.Series(False, index=frame.index) if threshold is None else frame.score.ge(threshold)
        )
        if all(
            int((alert.loc[b.index] & b.truth.eq(0)).sum()) / common_exposure(b) <= 1.0
            for b in blocks
        ):
            tp, fp = int((alert & frame.truth.eq(1)).sum()), int((alert & frame.truth.eq(0)).sum())
            feasible.append(
                (
                    tp,
                    -fp,
                    -int(alert.sum()),
                    float("inf") if threshold is None else threshold,
                    threshold,
                )
            )
    best = max(feasible, key=lambda row: row[:4])
    return {
        "policy": policy,
        "threshold": best[-1],
        "detected_onsets": best[0],
        "false_alerts": -best[1],
        "alerts": -best[2],
        "selection_blocks": len(blocks),
        "exposure_definition": "common_eligible_months/12",
    }


def evaluate_frozen(
    frame: pd.DataFrame,
    state: dict[str, Any],
    threshold: float | None,
    *,
    bins: int,
    objective: str,
    historical_exposure: float | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Score supplied rows without adjusting any state; expose both rates by name."""
    validate_scores(frame)
    if objective not in ("onset", "excess_control"):
        raise ValueError("Unknown objective")
    if "objective" in frame and not frame.objective.eq(objective).all():
        raise ValueError("Objective differs from prediction provenance")
    if objective == "excess_control" and ("horizon" not in frame or not frame.horizon.eq(2).all()):
        raise ValueError("Excess control requires its separate T+2 support")
    if threshold is not None and (not np.isfinite(threshold) or not 0 <= threshold <= 1):
        raise ValueError("Threshold must be a finite probability or no-alert null")
    if historical_exposure is not None and (
        not np.isfinite(historical_exposure) or historical_exposure <= 0
    ):
        raise ValueError("Invalid original historical exposure")
    result = frame.copy()
    result["score"] = apply_calibrator(frame, state)
    result["alert"] = False if threshold is None else result.score.ge(threshold)
    result["target_year"] = result.target_month.str[:4].astype(int)
    exposure = common_exposure(result)
    summary = metrics(result, exposure=exposure, bins=bins)
    summary["objective"] = objective
    summary["positives"] = summary.pop("onsets")
    summary["support"]["positives"] = summary["support"].pop("onsets")
    summary["common_exposure"] = exposure
    summary["common_FA_rate"] = summary.pop("false_alerts_per_monitored_municipality_year")
    summary["historical_exposure"] = historical_exposure
    summary["historical_FA_rate"] = (
        summary["false_alerts"] / historical_exposure if historical_exposure else None
    )
    summary["budget_excess"] = (
        max(0.0, summary["common_FA_rate"] - 1.0) if objective == "onset" else None
    )
    summary["municipal_macro_sensitivity"] = _municipal_sensitivity(result)
    summary["prevalence"] = float(result.truth.mean())
    summary["score_distribution"] = {
        "min": float(result.score.min()),
        "max": float(result.score.max()),
        "mean": float(result.score.mean()),
    }
    summary["false_alerts_by_error_class"] = {
        name: int((result.error_class.eq(name) & result.truth.eq(0) & result.alert).sum())
        for name in ("onset", "continuation", "no_excess")
    }
    summary["uncertainty"] = {
        "status": "UNAVAILABLE",
        "reason": "no_approved_block_resampling_protocol",
    }
    summary["transmission_profiles"] = "NOT_EVALUABLE"
    return result, summary


def _municipal_sensitivity(frame: pd.DataFrame) -> float | None:
    rates = []
    for _, municipality in frame.groupby("municipality_code"):
        positives = int(municipality.truth.sum())
        if positives:
            rates.append(float((municipality.alert & municipality.truth.eq(1)).sum()) / positives)
    return float(np.mean(rates)) if rates else None
