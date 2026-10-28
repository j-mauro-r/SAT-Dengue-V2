"""Prediction-native metrics and persistence diagnostics for EXP03.1."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


def select_threshold(
    truth: pd.Series, score: pd.Series, *, exposure: float, budget: float = 1.0
) -> dict[str, Any]:
    """Select one whole-tie threshold without consulting evaluation rows."""
    if not truth.index.equals(score.index) or truth.isna().any() or score.isna().any():
        raise ValueError("Threshold selection requires aligned complete rows")
    if exposure < 0 or budget < 0 or not np.isfinite(score.to_numpy(dtype=float)).all():
        raise ValueError("Invalid threshold selection inputs")
    y = truth.astype(int).to_numpy()
    s = score.astype(float).to_numpy()
    if not set(y) <= {0, 1} or ((s < 0) | (s > 1)).any():
        raise ValueError("Invalid threshold truth or probabilities")
    limit = int(np.floor(exposure * budget))
    candidates = [None, *sorted(set(s), reverse=True)]
    feasible = []
    for threshold in candidates:
        alert = np.zeros(len(s), dtype=bool) if threshold is None else s >= threshold
        tp = int((alert & (y == 1)).sum())
        fp = int((alert & (y == 0)).sum())
        if fp <= limit:
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
        "threshold": best[-1],
        "detected_onsets": best[0],
        "false_alerts": -best[1],
        "alerts": -best[2],
        "false_alert_limit": limit,
        "whole_score_ties": True,
    }


def error_class(excess_t1: Any, excess_t2: Any, onset_t2: Any) -> str:
    if any(pd.isna(value) for value in (excess_t1, excess_t2, onset_t2)):
        return "unknown"
    if int(onset_t2) == 1:
        return "onset"
    if int(excess_t2) == 1:
        return "continuation"
    if int(excess_t1) == 1:
        return "onset_previously_at_t1"
    return "no_excess"


def metrics(frame: pd.DataFrame, *, exposure: float, bins: int = 10) -> dict[str, Any]:
    required = {"truth", "score", "alert", "municipality_code", "target_year"}
    if not required.issubset(frame) or exposure < 0 or bins < 1:
        raise ValueError("Invalid EXP03.1 prediction metric inputs")
    known = frame.loc[frame.truth.notna() & frame.score.notna() & frame.alert.notna()].copy()
    if known.empty:
        return {"status": "insufficient_support", "rows": 0, "abstentions": len(frame)}
    truth = known.truth.astype(int).to_numpy()
    score = known.score.astype(float).to_numpy()
    alert = known.alert.astype(bool).to_numpy()
    if (
        not np.isfinite(score).all()
        or ((score < 0) | (score > 1)).any()
        or not set(truth) <= {0, 1}
    ):
        raise ValueError("Invalid EXP03.1 probabilities or truth")
    tp = int((alert & (truth == 1)).sum())
    fp = int((alert & (truth == 0)).sum())
    fn = int((~alert & (truth == 1)).sum())
    tn = int((~alert & (truth == 0)).sum())
    positives = tp + fn
    negatives = fp + tn
    alerts = tp + fp
    order = np.argsort(-score, kind="stable")
    ranked = truth[order]
    precision_curve = np.cumsum(ranked) / np.arange(1, len(ranked) + 1)
    ap = float((precision_curve * ranked).sum() / positives) if positives else None
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    reliability = []
    for index in range(bins):
        mask = (score >= edges[index]) & (
            score <= edges[index + 1] if index == bins - 1 else score < edges[index + 1]
        )
        if not mask.any():
            continue
        observed = float(truth[mask].mean())
        predicted = float(score[mask].mean())
        ece += float(mask.mean()) * abs(observed - predicted)
        reliability.append(
            {"bin": index, "rows": int(mask.sum()), "observed": observed, "predicted": predicted}
        )
    return {
        "status": "evaluable",
        "rows": len(known),
        "onsets": positives,
        "detected": tp,
        "missed": fn,
        "sensitivity": tp / positives if positives else None,
        "precision": tp / alerts if alerts else None,
        "false_alerts": fp,
        "far": fp / alerts if alerts else None,
        "fpr": fp / negatives if negatives else None,
        "false_alerts_per_monitored_municipality_year": fp / exposure if exposure else None,
        "alerts_emitted": alerts,
        "months_under_alert": int(alert.sum()),
        "average_precision": ap,
        "brier": float(np.mean((score - truth) ** 2)),
        "ece": ece,
        "reliability": reliability,
        "abstentions": len(frame) - len(known),
        "support": {
            "municipalities": int(known.municipality_code.nunique()),
            "years": int(known.target_year.nunique()),
            "onsets": positives,
        },
    }


def paired_effect(left: pd.DataFrame, right: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if left.duplicated(keys).any() or right.duplicated(keys).any():
        raise ValueError("Paired predictions require unique keys")
    if left[keys].to_records(index=False).tolist() != right[keys].to_records(index=False).tolist():
        raise ValueError("EXP03.1 contrasts require identical ordered rows")
    result = left[keys].copy()
    result["alert_delta"] = left.alert.astype(int).to_numpy() - right.alert.astype(int).to_numpy()
    result["score_delta"] = left.score.to_numpy(dtype=float) - right.score.to_numpy(dtype=float)
    return result


def grouped_metrics(
    frame: pd.DataFrame, *, exposure_column: str = "exposure"
) -> list[dict[str, Any]]:
    """Report every family/horizon/year/department/profile group, including adverse rows."""
    groups = ["family", "horizon", "target_year", "department_code", "transmission_profile"]
    if not {*groups, exposure_column}.issubset(frame):
        raise ValueError("EXP03.1 grouped metrics require all reporting dimensions")
    output = []
    for key, part in frame.groupby(groups, dropna=False, sort=True):
        value = metrics(part, exposure=float(part[exposure_column].sum()))
        output.append({**dict(zip(groups, key, strict=True)), **value})
    return output


def paired_interval(frame: pd.DataFrame, *, repeats: int = 200, seed: int = 42) -> dict[str, Any]:
    """Two-way municipality/year paired interval for development only."""
    required = {"municipality_code", "target_year", "window", "left_value", "right_value"}
    if not required.issubset(frame) or repeats < 1:
        raise ValueError("Invalid paired interval inputs")
    if frame.window.astype(str).str.contains("stress_2024").any():
        raise ValueError("Stress 2024 is excluded from development intervals")
    municipalities = sorted(frame.municipality_code.unique())
    years = sorted(frame.target_year.unique())
    if len(municipalities) < 2 or len(years) < 2:
        return {"status": "insufficient_cluster_support", "interval": None}
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(repeats):
        m_weights = pd.Series(
            np.bincount(
                rng.integers(0, len(municipalities), len(municipalities)),
                minlength=len(municipalities),
            ),
            index=municipalities,
        )
        y_weights = pd.Series(
            np.bincount(rng.integers(0, len(years), len(years)), minlength=len(years)),
            index=years,
        )
        weights = (
            frame.municipality_code.map(m_weights).to_numpy()
            * frame.target_year.map(y_weights).to_numpy()
        )
        if weights.sum():
            draws.append(float(np.average(frame.left_value - frame.right_value, weights=weights)))
    if not draws:
        return {"status": "insufficient_cluster_support", "interval": None}
    return {
        "status": "evaluable",
        "interval": np.quantile(draws, [0.025, 0.975]).tolist(),
        "valid_draws": len(draws),
        "paired_weights_shared": True,
        "development_years": years,
    }
