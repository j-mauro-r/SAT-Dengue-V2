"""Distinct onset/excess/episode metrics and paired structured retrospective uncertainty."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.metrics import average_precision_score, roc_auc_score  # type: ignore[import-untyped]

from sat_dengue.experiments.exp_delta03_learning import probabilities

KEYS = ["divipola_municipio", "periodo_mes", "horizon", "target_month"]


def metrics(
    frame: pd.DataFrame,
    *,
    monitored_exposure: float | None = None,
    expected_rows: int | None = None,
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    if frame.duplicated(KEYS).any():
        raise ValueError("Duplicate prediction key")
    if frame.empty:
        return {
            "status": "NO_EVALUABLE_EMPTY",
            "rows": 0,
            "sensitivity": None,
            "precision": None,
            "academic_excess_FAR": None,
            "brier": None,
            "average_precision": None,
            "auroc_secondary": None,
        }
    if frame.horizon.nunique() != 1:
        raise ValueError("Report horizons separately")
    p = probabilities(frame.score, frame.truth)
    if not frame.alert.isin([0, 1]).all():
        raise ValueError("Nonbinary alert")
    y, a = frame.truth.to_numpy(dtype=int), frame.alert.to_numpy(dtype=bool)
    w = np.ones(len(frame), dtype=float) if weights is None else np.asarray(weights, dtype=float)
    if w.shape != p.shape or not np.isfinite(w).all() or (w < 0).any() or not w.sum():
        raise ValueError("Invalid sampling weights")
    live = w > 0
    positive, negative = float(w @ y), float(w @ (1 - y))
    tp, fp, alerts = float(w @ (a & (y == 1))), float(w @ (a & (y == 0))), float(w @ a)
    n, exposure = float(w.sum()), float(w.sum() / 12)
    if monitored_exposure is not None:
        if not np.isfinite(monitored_exposure) or monitored_exposure + 1e-10 < exposure:
            raise ValueError("Monitored exposure cannot be smaller than eligible exposure")
    excess_available = "target_excess" in frame and frame.target_excess.notna().all()
    false_excess = None
    if excess_available:
        excess = frame.target_excess.to_numpy()
        if not np.isin(excess, [0, 1]).all() or ((y == 1) & (excess != 1)).any():
            raise ValueError("Invalid excess/onset outcome correspondence")
        false_excess = float(w @ (a & (excess == 0)))
    reliability = []
    bins = np.minimum((p * 10).astype(int), 9)
    for group in range(10):
        mask = (bins == group) & live
        if mask.any():
            mass = float(w[mask].sum())
            reliability.append(
                {
                    "bin": group,
                    "rows": mass,
                    "mean_probability": float(np.average(p[mask], weights=w[mask])),
                    "observed_fraction": float(np.average(y[mask], weights=w[mask])),
                }
            )
    episode: dict[str, Any] = {
        "status": "UNAVAILABLE_EPISODE_IDENTITIES",
        "observed": None,
        "detected": None,
        "missed": None,
        "sensitivity": None,
    }
    if "episode_id" in frame and frame.loc[frame.truth.eq(1), "episode_id"].notna().all():
        rows = frame.loc[live & (y == 1), ["divipola_municipio", "episode_id", "alert"]].copy()
        rows["weight"] = w[live & (y == 1)]
        grouped = rows.groupby(["divipola_municipio", "episode_id"], dropna=False)
        counts = grouped.weight.max()
        detected = grouped.alert.max().astype(float)
        observed, got = float(counts.sum()), float((counts * detected).sum())
        episode = {
            "status": "EVALUABLE" if observed else "NO_EVALUABLE_NO_EPISODES",
            "observed": observed,
            "detected": got,
            "missed": observed - got,
            "sensitivity": got / observed if observed else None,
        }
    lead = (
        pd.PeriodIndex(frame.target_month, freq="M").asi8
        - pd.PeriodIndex(frame.periodo_mes, freq="M").asi8
    )
    if not np.array_equal(lead, frame.horizon.to_numpy()) or (lead < 1).any():
        raise ValueError("Invalid prediction anticipation")
    result = {
        "status": "EVALUABLE",
        "rows": n,
        "positive_support": positive,
        "negative_support": negative,
        "onsets_observed": positive,
        "onsets_detected": tp,
        "onsets_missed": positive - tp,
        "alerts_emitted": alerts,
        "false_onset_alerts": fp,
        "false_excess_alerts": false_excess,
        "sensitivity": tp / positive if positive else None,
        "precision": tp / alerts if alerts else None,
        "academic_excess_FAR": false_excess / alerts
        if false_excess is not None and alerts
        else None,
        "excess_status": "EVALUABLE" if excess_available else "UNAVAILABLE_TARGET_EXCESS",
        "eligible_exposure_municipality_years": exposure,
        "monitored_exposure_municipality_years": monitored_exposure,
        "false_onset_alerts_per_eligible_municipality_year": fp / exposure,
        "false_onset_alerts_per_monitored_municipality_year": (
            fp / monitored_exposure if monitored_exposure else None
        ),
        "average_precision": float(average_precision_score(y[live], p[live], sample_weight=w[live]))
        if positive and negative
        else None,
        "auroc_secondary": float(roc_auc_score(y[live], p[live], sample_weight=w[live]))
        if positive and negative
        else None,
        "brier": float(np.average((p - y) ** 2, weights=w)),
        "calibration": {
            "reliability": reliability,
            "expected_calibration_error": sum(
                r["rows"] * abs(r["mean_probability"] - r["observed_fraction"]) for r in reliability
            )
            / n,
            "mean_probability_minus_observed": float(np.average(p - y, weights=w)),
        },
        "coverage": n / expected_rows if expected_rows else None,
        "municipalities": int(frame.loc[live, "divipola_municipio"].nunique()),
        "target_months": int(frame.loc[live, "target_month"].nunique()),
        "episodes": episode,
        "anticipation_months_detected": float(
            np.average(lead[a & (y == 1)], weights=w[a & (y == 1)])
        )
        if tp
        else None,
    }
    return result


def paired(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    a, b = (f.sort_values(KEYS).reset_index(drop=True) for f in (left, right))
    if a.duplicated(KEYS).any() or b.duplicated(KEYS).any() or len(a) != len(b):
        raise ValueError("Paired prediction key mismatch")
    columns = KEYS + ["truth"]
    for optional in ["target_excess", "episode_id"]:
        if (optional in a) != (optional in b):
            raise ValueError("Paired outcome schema differs")
        if optional in a:
            columns.append(optional)
    if not a[columns].equals(b[columns]):
        raise ValueError("Paired keys/outcomes differ; no convenient intersection")
    return a, b


def difference(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "sensitivity",
        "precision",
        "academic_excess_FAR",
        "false_onset_alerts",
        "false_onset_alerts_per_eligible_municipality_year",
        "average_precision",
        "brier",
    ]
    return {
        key: {
            "absolute": None if left[key] is None or right[key] is None else left[key] - right[key],
            "relative": None
            if left[key] is None or right[key] in (None, 0)
            else (left[key] - right[key]) / right[key],
        }
        for key in fields
    }


def uncertainty(
    left: pd.DataFrame,
    right: pd.DataFrame,
    exposures: pd.DataFrame,
    specification: dict[str, Any],
) -> dict[str, Any]:
    """Paired municipality × connected-year blocks, with episode boundaries preserved."""
    a, b = paired(left, right)
    if a.empty:
        return {"status": "NO_EVALUABLE_EMPTY"}
    years = sorted(pd.PeriodIndex(a.target_month, freq="M").year.unique().tolist())
    if 2024 in years and len(years) > 1:
        raise ValueError("Stress2024 cannot enter development uncertainty")
    if any(year >= 2025 for year in years):
        raise ValueError("Excluded2025 in uncertainty")
    e = exposures.copy()
    if e.duplicated(["divipola_municipio", "year"]).any():
        raise ValueError("Duplicate monitored exposure")
    if (
        not e.year.isin(years).all()
        or (e.monitored_exposure < 0).any()
        or not np.isfinite(e.monitored_exposure).all()
    ):
        raise ValueError("Invalid exposure coverage")
    needed = set(
        zip(a.divipola_municipio, pd.PeriodIndex(a.target_month, freq="M").year, strict=True)
    )
    if not needed <= set(e[["divipola_municipio", "year"]].itertuples(index=False, name=None)):
        raise ValueError("Missing municipality/year exposure")
    municipalities = sorted(e.divipola_municipio.unique())
    if not set(a.divipola_municipio) <= set(municipalities):
        raise ValueError("Missing exposure municipality")
    parent = {year: year for year in years}

    def find(year):
        while parent[year] != year:
            year = parent[year]
        return year

    if "episode_id" not in a:
        return {"status": "NO_EVALUABLE_EPISODE_IDENTITIES"}
    episode_rows = a.loc[
        a.episode_id.notna(), ["divipola_municipio", "episode_id", "target_month"]
    ].copy()
    episode_rows["year"] = pd.PeriodIndex(episode_rows.target_month, freq="M").year
    for _, group in episode_rows.groupby(["divipola_municipio", "episode_id"]):
        connected = group.year.unique()
        for year in connected[1:]:
            parent[find(int(year))] = find(int(connected[0]))
    blocks = sorted({find(year) for year in years})
    base = {
        "method": specification["method"],
        "seed": specification["seed"],
        "draws_requested": specification["draws"],
        "confidence": specification["confidence"],
        "municipalities": len(municipalities),
        "temporal_blocks": len(blocks),
        "episode_year_connections": {str(y): find(y) for y in years},
        "interpretation": "retrospective paired descriptive uncertainty; no formal superiority",
    }
    if (
        len(municipalities) < specification["minimum_municipalities"]
        or len(blocks) < specification["minimum_temporal_blocks"]
    ):
        return {**base, "status": "NO_EVALUABLE_INSUFFICIENT_CLUSTER_SUPPORT", "intervals": None}
    rng = np.random.default_rng(specification["seed"])
    muni_idx = {v: i for i, v in enumerate(municipalities)}
    block_idx = {v: i for i, v in enumerate(blocks)}
    row_muni = np.array([muni_idx[v] for v in a.divipola_municipio])
    row_blocks = np.array(
        [block_idx[find(int(y))] for y in pd.PeriodIndex(a.target_month, freq="M").year]
    )
    exposure_muni = np.array([muni_idx[v] for v in e.divipola_municipio])
    exposure_blocks = np.array([block_idx[find(int(y))] for y in e.year])
    samples: dict[str, list[float]] = {}
    for _ in range(specification["draws"]):
        mw = np.bincount(
            rng.integers(0, len(municipalities), len(municipalities)), minlength=len(municipalities)
        )
        tw = np.bincount(rng.integers(0, len(blocks), len(blocks)), minlength=len(blocks))
        w = mw[row_muni] * tw[row_blocks]
        monitored = float(
            np.sum(mw[exposure_muni] * tw[exposure_blocks] * e.monitored_exposure.to_numpy())
        )
        if not w.sum():
            continue
        delta = difference(
            metrics(a, monitored_exposure=monitored, weights=w),
            metrics(b, monitored_exposure=monitored, weights=w),
        )
        for name, value in delta.items():
            if value["absolute"] is not None:
                samples.setdefault(name, []).append(value["absolute"])
    alpha = (1 - specification["confidence"]) / 2
    minimum = max(2, int(np.ceil(specification["draws"] * specification["minimum_valid_fraction"])))
    intervals = {}
    for key, values in samples.items():
        sufficient = len(values) >= minimum
        intervals[key] = {
            "low": float(np.quantile(values, alpha)) if sufficient else None,
            "high": float(np.quantile(values, 1 - alpha)) if sufficient else None,
            "valid_draws": len(values),
            "status": "EVALUABLE" if sufficient else "NO_EVALUABLE_TOO_FEW_DRAWS",
        }
    return {
        **base,
        "status": "EVALUABLE"
        if any(v["status"] == "EVALUABLE" for v in intervals.values())
        else "NO_EVALUABLE_UNDEFINED_METRICS",
        "intervals": intervals,
    }
