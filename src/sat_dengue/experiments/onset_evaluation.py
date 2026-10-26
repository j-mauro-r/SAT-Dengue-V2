"""Paired onset utility at a shared development false-alert budget."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


def _probabilities(scores: np.ndarray) -> None:
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("Expected finite probabilities in [0,1]")


def calibration_summary(truth: np.ndarray, scores: np.ndarray, *, bins: int = 10) -> dict[str, Any]:
    """Equal-width reliability bins and expected calibration error."""
    if len(truth) != len(scores) or not np.isin(truth, [0, 1]).all() or bins < 1:
        raise ValueError("Calibration requires aligned binary outcomes and probabilities")
    _probabilities(scores)
    edges = np.linspace(0.0, 1.0, bins + 1)
    index = np.minimum(np.digitize(scores, edges[1:-1], right=False), bins - 1)
    summaries = []
    ece = 0.0
    for i in range(bins):
        mask = index == i
        count = int(mask.sum())
        observed = float(truth[mask].mean()) if count else None
        predicted = float(scores[mask].mean()) if count else None
        if count and observed is not None and predicted is not None:
            ece += count / max(len(truth), 1) * abs(observed - predicted)
        summaries.append(
            {
                "lower": float(edges[i]),
                "upper": float(edges[i + 1]),
                "count": count,
                "mean_probability": predicted,
                "observed_frequency": observed,
            }
        )
    return {"bins": summaries, "expected_calibration_error": float(ece) if len(truth) else None}


def stratified_episode_metrics(frame: pd.DataFrame, alerts: np.ndarray) -> dict[str, Any]:
    """Summarize predeclared municipality/year/department groups where present."""
    result: dict[str, Any] = {}
    groups: dict[str, pd.Series] = {}
    if "municipality_code" in frame:
        municipality = frame.municipality_code.astype(str).str.zfill(5)
        groups["municipality"] = municipality
        if "department" not in frame:
            groups["department"] = municipality.str[:2]
    if "department" in frame:
        groups["department"] = frame.department.astype(str)
    if "target_month" in frame:
        groups["target_year"] = frame.target_month.astype(str).str[:4]
    for dimension, values in groups.items():
        result[dimension] = {}
        for value in sorted(values.dropna().unique()):
            mask = values.eq(value).to_numpy()
            result[dimension][str(value)] = episode_metrics(frame.loc[mask], alerts[mask])
    return result


def matched_thresholds(
    truth: np.ndarray, excess: np.ndarray, onset: np.ndarray, budget: int
) -> dict[str, float | None]:
    """Same integer false-onset-alert cap, whole score ties, selection rows only.

    No alert policy is represented by None, not an invented probability >1.
    Ties favor fewer false alerts, fewer total alerts, then the higher threshold.
    Each arm can underspend; equality of caps is not equality of realized burden.
    """
    if not (len(truth) == len(excess) == len(onset)) or not np.isin(truth, [0, 1]).all():
        raise ValueError("Paired selection rows and binary truth required")
    if not isinstance(budget, int) or budget < 0:
        raise ValueError("Invalid false-alert budget")
    output: dict[str, float | None] = {}
    for name, scores in (("excess", excess), ("onset", onset)):
        _probabilities(scores)
        choices: list[tuple[int, int, int, float | None]] = [(0, 0, 0, None)]
        for threshold in np.unique(scores):
            alerts = scores >= threshold
            fp = int((alerts & (truth == 0)).sum())
            tp = int((alerts & (truth == 1)).sum())
            if fp <= budget:
                choices.append((tp, -fp, -int(alerts.sum()), float(threshold)))
        best = max(choices, key=lambda x: (x[0], x[1], x[2], x[3] if x[3] is not None else 2))
        output[name] = best[3]
    return output


def episode_metrics(frame: pd.DataFrame, alerts: np.ndarray) -> dict[str, Any]:
    """One onset per municipality/target month, missing predictions are missed.

    Retrospective unavailable labels never become negatives. Missing predictions
    cannot remove real onsets from the denominator. An alert at a continuing
    episode is false for onset, even when it correctly predicts monthly excess.
    """
    if len(alerts) != len(frame) or frame.duplicated(["municipality_code", "target_month"]).any():
        raise ValueError("Misaligned or duplicate episode keys")
    known = frame.onset_target.notna().to_numpy()
    truth = frame.onset_target.fillna(0).to_numpy(dtype=int)
    emitted = np.asarray(pd.Series(alerts).fillna(False), dtype=bool)
    tp = int((emitted & known & (truth == 1)).sum())
    real = int((known & (truth == 1)).sum())
    fp = int((emitted & known & (truth == 0)).sum())
    evaluable_alerts = int((emitted & known).sum())
    exposure = frame.loc[known, ["municipality_code", "target_month"]].drop_duplicates()
    municipality_years = len(exposure) / 12
    leads = None
    if tp and {"year_month", "target_month"} <= set(frame):
        detected = frame.loc[emitted & known & (truth == 1), ["year_month", "target_month"]]
        leads = float(
            np.mean(
                [
                    pd.Period(target, freq="M").ordinal - pd.Period(origin, freq="M").ordinal
                    for origin, target in detected.itertuples(index=False, name=None)
                ]
            )
        )
    return {
        "real_onsets": real,
        "detected_onsets": tp,
        "missed_episodes": real - tp,
        "detected_episodes": tp,
        "false_alerts": fp,
        "emitted_alerts": int(emitted.sum()),
        "onset_sensitivity": tp / real if real else None,
        "onset_precision": tp / evaluable_alerts if evaluable_alerts else None,
        "false_alarm_ratio": fp / evaluable_alerts if evaluable_alerts else None,
        "false_alerts_per_municipality_year": fp / municipality_years
        if municipality_years
        else None,
        "evaluable_rows": int(known.sum()),
        "unavailable_outcomes": int((~known).sum()),
        "missing_predictions": int(pd.isna(alerts).sum()),
        "useful_lead_months": leads,
    }


def assert_paired(
    left: pd.DataFrame, right: pd.DataFrame, predictors: list[str] | None = None
) -> None:
    """Require identical rows and predictor values, allowing the target to differ."""
    columns = ["municipality_code", "year_month", "target_month"]
    if predictors is not None:
        columns.extend(predictors)
    if not set(columns) <= set(left) or not set(columns) <= set(right):
        raise ValueError("Paired inputs are missing keys or frozen predictors")
    if not left[columns].reset_index(drop=True).equals(right[columns].reset_index(drop=True)):
        raise ValueError("Comparator rows, predictors or cohorts differ")


def paired_block_interval(
    frame: pd.DataFrame, left: np.ndarray, right: np.ndarray, *, seed: int, repeats: int = 1000
) -> dict[str, Any]:
    """Municipality cluster x calendar-year block bootstrap, identical paired draws.

    Entire contiguous years keep within-year serial dependence. Single-year or
    municipality support is explicitly insufficient, never an IID confidence claim.
    """
    if len(frame) != len(left) or len(frame) != len(right) or repeats < 1:
        raise ValueError("Misaligned paired uncertainty inputs")
    municipalities = frame.municipality_code.unique()
    years = frame.target_month.str[:4].unique()
    if len(municipalities) < 2 or len(years) < 2:
        return {"status": "insufficient_cluster_support", "interval": None}
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        positions: list[int] = []
        for municipality in rng.choice(municipalities, len(municipalities), replace=True):
            for year in rng.choice(years, len(years), replace=True):
                positions.extend(
                    np.flatnonzero(
                        (frame.municipality_code == municipality)
                        & frame.target_month.str.startswith(year)
                    )
                )
        sample = frame.iloc[positions].copy()
        # Repeated clusters are legitimate bootstrap copies, assigned unique keys.
        sample["municipality_code"] = [str(i) for i in range(len(sample))]
        a, b = episode_metrics(sample, left[positions]), episode_metrics(sample, right[positions])
        if a["onset_sensitivity"] is not None:
            values.append(b["onset_sensitivity"] - a["onset_sensitivity"])
    return {
        "status": "retrospective_paired",
        "interval": np.quantile(values, [0.025, 0.975]).tolist() if values else None,
    }
