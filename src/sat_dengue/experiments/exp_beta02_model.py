"""Parsimonious NB2 count regression; optional numerical imports stay lazy."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


def transformed(frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    """Fixed log-count transform; retain signed climate and explicit feature order."""
    values = frame[columns].to_numpy(dtype=float, copy=True)
    for index, name in enumerate(columns):
        if "notifications_count" in name or name.startswith(("p25_", "p50_", "p75_")):
            if (values[:, index] < 0).any():
                raise ValueError("Count/threshold predictors must be nonnegative")
            values[:, index] = np.log1p(values[:, index])
    if not np.isfinite(values).all():
        raise ValueError("Nonfinite count-model predictors")
    return values


def objective(theta: np.ndarray, x: np.ndarray, y: np.ndarray, penalty: float) -> Any:
    """Stable summed NB2 negative log likelihood and exact analytic gradient."""
    from scipy.special import digamma, gammaln  # type: ignore[import-untyped]

    beta, log_alpha = theta[:-1], theta[-1]
    eta, r = x @ beta, np.exp(-log_alpha)
    log_r = -log_alpha
    denominator = np.logaddexp(log_r, eta)
    ll = (
        gammaln(y + r)
        - gammaln(r)
        - gammaln(y + 1)
        + r * (log_r - denominator)
        + y * (eta - denominator)
    )
    gradient_beta = x.T @ ((r + y) * np.exp(eta - denominator) - y)
    gradient_beta[1:] += penalty * beta[1:]
    derivative_r = (
        digamma(y + r) - digamma(r) + log_r + 1 - denominator - (r + y) * np.exp(-denominator)
    )
    gradient = np.r_[gradient_beta, r * derivative_r.sum()]
    value = -ll.sum() + penalty * float(beta[1:] @ beta[1:]) / 2
    return float(value), gradient


def fit(frame: pd.DataFrame, columns: list[str], spec: dict[str, Any]) -> dict[str, Any]:
    """Fit transforms, mean coefficients and dispersion on training counts only."""
    from scipy.optimize import minimize  # type: ignore[import-untyped]
    from threadpoolctl import threadpool_limits  # type: ignore[import-untyped]

    y = frame.count_target.to_numpy(dtype=float)
    if (
        len(y) < spec["minimum_training_rows"]
        or not np.isfinite(y).all()
        or (y < 0).any()
        or (y % 1 != 0).any()
        or y.sum() <= 0
    ):
        raise ValueError("Insufficient or invalid training counts")
    values = transformed(frame, columns)
    center, scale = values.mean(axis=0), values.std(axis=0)
    scale[scale == 0] = 1.0
    x = np.column_stack([np.ones(len(y)), (values - center) / scale])
    low, high = spec["alpha_bounds"]
    alpha = np.clip((y.var() - y.mean()) / y.mean() ** 2, low, high)
    initial = np.r_[np.log(y.mean()), np.zeros(len(columns)), np.log(alpha)]
    with threadpool_limits(limits=spec["threads"]):
        result = minimize(
            objective,
            initial,
            args=(x, y, spec["ridge_penalty_sum_likelihood"]),
            method="L-BFGS-B",
            jac=True,
            bounds=[(None, None)] * x.shape[1] + [(np.log(low), np.log(high))],
            options={k: spec[k] for k in ("maxiter", "ftol", "gtol", "maxls")},
        )
    if not result.success or not np.isfinite(result.x).all() or not np.isfinite(result.fun):
        raise ValueError(f"NB2 did not converge: {result.message}")
    return {
        "schema": "exp-beta02-nb2-model-v1",
        "predictors": columns,
        "center": center.tolist(),
        "scale": scale.tolist(),
        "coefficients": result.x[:-1].tolist(),
        "alpha": float(np.exp(result.x[-1])),
        "training_rows": len(y),
        "iterations": int(result.nit),
        "penalized_negative_log_likelihood": float(result.fun),
        "converged": bool(result.success),
        "message": str(result.message),
        "dispersion_at_bound": bool(np.isclose(np.exp(result.x[-1]), [low, high]).any()),
    }


def forecast(frame: pd.DataFrame, model: dict[str, Any]) -> pd.DataFrame:
    """Return the full NB2 parameterization and conditional predictive interval."""
    from scipy.stats import nbinom  # type: ignore[import-untyped]

    values = transformed(frame, model["predictors"])
    x = np.column_stack([np.ones(len(frame)), (values - model["center"]) / model["scale"]])
    with np.errstate(over="raise", invalid="raise"):
        mean = np.exp(x @ np.asarray(model["coefficients"]))
    r = 1.0 / model["alpha"]
    p = r / (r + mean)
    result = pd.DataFrame(
        {
            "mean": mean,
            "alpha": model["alpha"],
            "nb_r": r,
            "nb_p": p,
            "q05": nbinom.ppf(0.05, r, p),
            "q95": nbinom.ppf(0.95, r, p),
        },
        index=frame.index,
    )
    if not np.isfinite(result.to_numpy()).all() or not ((p > 0) & (p <= 1)).all():
        raise ValueError("Invalid NB2 predictive distribution")
    return result


def risks(distribution: pd.DataFrame, p75: Any, horizon: int) -> pd.DataFrame:
    """Strict H5 exceedance is onset only for T+1 in this eligible cohort."""
    from scipy.stats import nbinom

    threshold = np.asarray(p75, dtype=float)
    if horizon not in (1, 2) or not np.isfinite(threshold).all() or (threshold < 0).any():
        raise ValueError("Invalid H5 risk target")
    result = distribution.copy()
    result["excess_score"] = nbinom.sf(np.floor(threshold), result.nb_r, result.nb_p)
    result["score"] = result.excess_score if horizon == 1 else np.nan
    result["onset_status"] = "EVALUABLE" if horizon == 1 else "NO_EVALUABLE"
    return result
