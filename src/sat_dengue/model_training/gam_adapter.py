"""Bernoulli/logit additive cubic B-spline model with explicit ridge basis penalty."""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy.interpolate import BSpline  # type: ignore[import-untyped]
from scipy.special import expit  # type: ignore[import-untyped]
from sklearn.exceptions import ConvergenceWarning  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.preprocessing import SplineTransformer  # type: ignore[import-untyped]
from threadpoolctl import threadpool_limits  # type: ignore[import-untyped]

from sat_dengue.training_preparation.serialization import json_bytes

from .candidate_preparation import fit_representation, transform_representation, validate_training
from .contract import ModelTrainingError


def spline_matrix(X: pd.DataFrame, preparer: dict[str, Any]) -> np.ndarray:
    """Apply saved univariate bases, constant extrapolation and untouched linear terms.

    Args:
        X: Ordered raw predictors.
        preparer: Training-fitted knots, coefficients and category vocabulary.

    Returns:
        Additive design matrix in saved term order, with no interactions.
    """
    encoded = transform_representation(X, preparer)
    parts = []
    for term in preparer["gam"]["terms"]:
        values = encoded[term["column"]].to_numpy(dtype=float)
        if term["kind"] == "spline":
            t, k = np.asarray(term["knots"]), term["degree"]
            spline = BSpline(t, np.asarray(term["coefficients"]), k)
            parts.append(spline(np.clip(values, t[k], t[-k - 1]))[:, :-1])
        elif term["kind"] == "constant":
            parts.append(np.zeros((len(X), 1)))
        else:
            parts.append(values[:, None])
    return np.concatenate(parts, axis=1)


@dataclass
class FittedGAM:
    """Portable additive logistic coefficients and safe JSON basis state.

    Args:
        model: Coefficients/intercept and convergence metadata.
        preparer: Training-only spline and categorical representation.
    """

    model: dict[str, Any]
    preparer: dict[str, Any]

    def predict(self, X: pd.DataFrame) -> pd.Series:
        """Evaluate the saved additive predictor and inverse logit.

        Args:
            X: Ordered raw predictors.

        Returns:
            Finite aligned binary probabilities.
        """
        values = expit(
            spline_matrix(X, self.preparer) @ np.asarray(self.model["coefficients"])
            + self.model["intercept"]
        )
        if not np.isfinite(values).all():
            raise ModelTrainingError("Invalid GAM probabilities")
        return pd.Series(values, index=X.index)

    def model_bytes(self) -> bytes:
        """Return safe numeric JSON; no pickled estimator is required."""
        return json_bytes(self.model)


def restore_candidate(model_bytes: bytes, preparer: dict[str, Any]) -> FittedGAM:
    """Restore locally trusted hash-verified numeric model state.

    Args:
        model_bytes: JSON coefficient payload.
        preparer: Matching basis/category state.

    Returns:
        Inference object without refitting.
    """
    return FittedGAM(json.loads(model_bytes), preparer)


def fit_candidate(
    X: pd.DataFrame,
    y: pd.Series,
    parameters: dict[str, Any],
    *,
    seed: int,
    threads: int,
    excluded: list[str] | None = None,
) -> FittedGAM:
    """Fit a penalized additive Bernoulli model using training-only cubic splines.

    Args:
        X: Raw training predictors; existing mes_sin/mes_cos remain linear Fourier terms.
        y: Aligned binary labels.
        parameters: n_knots controls basis complexity; C is inverse ridge strength.
        seed: Reproducible solver seed.
        threads: CPU thread limit for linear algebra.

    Returns:
        Converged additive model; ridge penalizes coefficients, not spline curvature.
    """
    validate_training(X, y)
    preparer = fit_representation(X, excluded)
    encoded = transform_representation(X, preparer)
    terms = []
    names: list[str] = []
    for column in encoded:
        values = encoded[[column]].to_numpy(dtype=float)
        smooth = column in preparer["numeric_columns"] and column not in ("mes_sin", "mes_cos")
        if smooth and np.ptp(values) > 0:
            transformer = SplineTransformer(
                n_knots=parameters["n_knots"],
                degree=3,
                knots="uniform",
                extrapolation="constant",
                include_bias=False,
            ).fit(values)
            spline = transformer.bsplines_[0]
            terms.append(
                dict(
                    column=column,
                    kind="spline",
                    knots=spline.t.tolist(),
                    coefficients=spline.c.tolist(),
                    degree=spline.k,
                )
            )
            names.extend(f"{column}:basis_{i}" for i in range(transformer.n_features_out_))
        else:
            # Training-constant numeric terms have zero slope: freeze as zero at all origins.
            if smooth:
                terms.append(dict(column=column, kind="constant"))
            else:
                terms.append(dict(column=column, kind="linear"))
            names.append(column)
    preparer["gam"] = dict(
        terms=terms,
        output_columns=names,
        distribution="Bernoulli",
        link="logit",
        penalty="L2 basis coefficient shrinkage; not a curvature penalty",
        extrapolation="constant",
        interactions=0,
    )
    matrix = spline_matrix(X, preparer)
    with threadpool_limits(limits=threads), warnings.catch_warnings():
        warnings.simplefilter("error", ConvergenceWarning)
        estimator = LogisticRegression(
            C=parameters["C"], solver="lbfgs", max_iter=2000, tol=1e-7, random_state=seed
        ).fit(matrix, y.to_numpy(dtype=int))
    model = dict(
        schema="additive-logit-v1",
        coefficients=estimator.coef_[0].tolist(),
        intercept=float(estimator.intercept_[0]),
        iterations=int(estimator.n_iter_[0]),
    )
    fitted = FittedGAM(model, preparer)
    if not np.allclose(
        fitted.predict(X), estimator.predict_proba(matrix)[:, 1], rtol=0, atol=1e-12
    ):
        raise ModelTrainingError("GAM numeric export differs from fitted estimator")
    return fitted
