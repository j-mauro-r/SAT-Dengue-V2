"""Bounded Beta comparison: pure cohort, temporal, adaptation and scoring rules."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, PREDICTORS, predictor_matrix
from sat_dengue.experiments.onset import labels, validate_keys

KEYS = ["municipality_code", "year_month"]


def prepare(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Select a common ON/OFF cohort; future outcome fields never become X."""
    from sat_dengue.configuration import validate_parameters

    if validate_parameters(parameters) != {"profile": "exp_beta01", "tracking": "disabled"}:
        raise ValueError("Beta requires its own profile and disabled tracking")
    protocol = sources["protocol"]
    if protocol["predictors"] != PREDICTORS or protocol["climate_predictors"] != CLIMATE:
        raise ValueError("Beta predictor contract changed")
    table = sources["table"]
    # No 2025 target/state enters outcome construction or any fitted/evaluated role.
    table = table.loc[table.year_month.lt(protocol["reserved_target_start"])].copy()
    validate_keys(table)
    matrix = predictor_matrix(table, sources["columns"])
    states = table[KEYS].copy()
    states["excess"] = table.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[table.zona_canal_t.isna(), "excess"] = pd.NA
    cohorts = {}
    for horizon in protocol["horizons"]:
        outcomes = labels(states, horizon)
        common = outcomes.eligible_at_t & outcomes.onset_target.notna() & matrix.notna().all(axis=1)
        common &= outcomes.target_month.lt(protocol["reserved_target_start"])
        frame = table.loc[common, [*KEYS, "department_code", *PREDICTORS]].copy()
        for name in ("onset_target", "target_month", "earlier_onset_t1"):
            frame[name] = outcomes.loc[common, name]
        frame["target_year"] = frame.target_month.str[:4].astype(int)
        frame["zona_canal_t"] = frame.zona_canal_t.map(
            {"EXITO": 0, "SEGURIDAD": 1, "ALERTA": 2, "EXCESO": 3}
        )
        if frame[PREDICTORS].isna().any().any():
            raise ValueError("Unrecognized canonical zone")
        cohorts[horizon] = frame.sort_values(KEYS).reset_index(drop=True)
    return {
        **sources,
        "cohorts": cohorts,
        "provenance": {**sources.get("provenance", {}), "operational": parameters},
    }


def role_parts(frame: pd.DataFrame, year: int, protocol: dict[str, Any]) -> dict[str, Any]:
    """Every municipality shares target cutoffs and the same origin embargo."""
    if year not in protocol["evaluation_years"] or year >= 2025:
        raise ValueError("Unapproved evaluation year")
    periods = {
        "train": (protocol["training_start"], f"{year - 4}-12"),
        "calibration": (f"{year - 3}-01", f"{year - 3}-12"),
        "adaptation": (f"{year - 2}-01", f"{year - 2}-12"),
        "selection": (f"{year - 1}-01", f"{year - 1}-12"),
        "evaluation": (f"{year}-01", f"{year}-12"),
    }
    parts, audit = {}, {}
    previous = None
    for role, (start, end) in periods.items():
        if role != "evaluation" and end >= "2024-01":
            raise ValueError("Stress year cannot fit or select")
        mask = frame.target_month.between(start, end)
        before = int(mask.sum())
        if previous:
            mask &= frame.year_month.ge(previous)
        part = frame.loc[mask].copy()
        if part.empty or (role in {"train", "calibration"} and part.onset_target.nunique() != 2):
            raise ValueError(f"Insufficient Beta support: {role}/{year}")
        parts[role] = part
        audit[role] = {
            "target_start": start,
            "target_end": end,
            "rows": len(part),
            "embargo_excluded": before - len(part),
            "origin_start": str(part.year_month.min()),
            "origin_end": str(part.year_month.max()),
            "municipalities": int(part.municipality_code.nunique()),
        }
        previous = end
    return {"parts": parts, "audit": audit}


def shifted(scores: Any, offset: Any) -> np.ndarray:
    """Apply an intercept in log odds without invalid probabilities."""
    p = np.clip(np.asarray(scores, dtype=float), 1e-7, 1 - 1e-7)
    if not np.isfinite(p).all():
        raise ValueError("Nonfinite score")
    z = np.clip(np.log(p / (1 - p)) + offset, -40, 40)
    return 1 / (1 + np.exp(-z))


def fit_intercept(scores: Any, truth: Any, penalty: float) -> float:
    """One regularized scalar; a Newton update, not a parameter search."""
    y = np.asarray(truth, dtype=float)
    p = np.asarray(scores, dtype=float)
    if len(y) == 0 or len(y) != len(p) or not np.isin(y, [0, 1]).all() or penalty <= 0:
        raise ValueError("Invalid intercept inputs")
    offset = 0.0
    for _ in range(100):
        fitted = shifted(p, offset)
        gradient = float((fitted - y).sum()) + penalty * offset
        hessian = float((fitted * (1 - fitted)).sum()) + penalty
        step = gradient / hessian
        offset = float(np.clip(offset - step, -10, 10))
        if abs(step) < 1e-10:
            break
    return offset


def fit_adaptation(frame: pd.DataFrame, scores: Any, spec: dict[str, Any]) -> dict[str, Any]:
    """Estimate department residual intercepts with a zero-offset global fallback."""
    y = frame.onset_target.astype(int).to_numpy()
    scores = np.asarray(scores, dtype=float)
    result = {}
    for code in sorted(frame.department_code.unique()):
        mask = frame.department_code.eq(code).to_numpy(dtype=bool)
        positive = int(y[mask].sum())
        sufficient = (
            int(mask.sum()) >= spec["minimum_rows"]
            and min(positive, int(mask.sum()) - positive) >= spec["minimum_per_class"]
        )
        result[str(code)] = {
            "offset": fit_intercept(scores[mask], y[mask], spec["penalty"]) if sufficient else 0.0,
            "status": "adapted" if sufficient else "global_fallback",
            "rows": int(mask.sum()),
            "onsets": positive,
        }
    return result


def thresholds(truth: Any, scores: Any, exposure: float, budget: float) -> dict[str, Any]:
    """Maximize detections under the fixed budget, keeping probability ties whole."""
    y, s = np.asarray(truth, dtype=int), np.asarray(scores, dtype=float)
    if len(y) == 0 or len(y) != len(s) or not np.isin(y, [0, 1]).all() or exposure <= 0:
        raise ValueError("Invalid policy support")
    if not np.isfinite(s).all() or ((s < 0) | (s > 1)).any() or budget < 0:
        raise ValueError("Invalid probabilities/budget")
    limit = int(np.floor(exposure * budget))
    # Sorted cumulative whole-tie groups avoid quadratic threshold enumeration.
    order = np.argsort(-s, kind="stable")
    ordered = s[order]
    ends = np.r_[np.flatnonzero(ordered[:-1] != ordered[1:]), len(y) - 1]
    tp, fp = np.cumsum(y[order]), np.cumsum(1 - y[order])
    feasible: list[tuple[int, int, float, float | None]] = [(0, 0, float("inf"), None)]
    feasible += [
        (int(tp[i]), -int(fp[i]), float(ordered[i]), float(ordered[i]))
        for i in ends
        if fp[i] <= limit
    ]
    best = max(feasible, key=lambda v: v[:3])
    return {
        "threshold": best[3],
        "detected": best[0],
        "false_alerts": -best[1],
        "false_alert_limit": limit,
        "exposure": exposure,
    }


def metric_row(frame: pd.DataFrame, budget: float) -> dict[str, Any]:
    """Exposure is observed eligible target-months/12, not unique municipality count."""
    from sklearn.metrics import average_precision_score  # type: ignore[import-untyped]

    y, alert = frame.truth.astype(int), frame.alert.astype(bool)
    tp, fp = int((y.eq(1) & alert).sum()), int((y.eq(0) & alert).sum())
    positives, exposure = int(y.sum()), len(frame) / 12.0
    return {
        "rows": len(frame),
        "municipalities": int(frame.municipality_code.nunique()),
        "onsets": positives,
        "detected": tp,
        "false_alerts": fp,
        "exposure_municipality_years": exposure,
        "sensitivity": tp / positives if positives else None,
        "false_alerts_per_municipality_year": fp / exposure,
        "budget_met": fp / exposure <= budget,
        "precision": tp / int(alert.sum()) if alert.any() else None,
        "average_precision": float(average_precision_score(y, frame.score)) if positives else None,
        "brier": float(np.mean((frame.score - y) ** 2)),
    }
