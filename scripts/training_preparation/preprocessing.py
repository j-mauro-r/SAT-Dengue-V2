"""Training-only configurable category representation and numeric scaling; no Y input."""

from __future__ import annotations

import platform
from dataclasses import asdict, dataclass
from typing import Any, Literal

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationError
from .development import serialize_table
from .persistence import bytes_record

ZONES = ("EXITO", "SEGURIDAD", "ALERTA", "EXCESO")
MISSING = "__MISSING__"
UNKNOWN = "__UNKNOWN__"
CATEGORICAL = ("municipality_code", "zona_canal_t", "zona_canal_lag_1")


@dataclass(frozen=True)
class PreparerSpec:
    """Choose representation for a future estimator, independent of target labels.

    Args:
        encoding: Native pandas categories, explicit one-hot columns, or fixed ordinal codes.
        numeric_scaling: None or training mean/population-standard-deviation scaling.
        numeric_missing: Reject missing numeric values or explicitly preserve them.
        unknown_municipality: Map unseen municipality to a fixed token or reject it.
    """

    encoding: Literal["native", "onehot", "ordinal"] = "native"
    numeric_scaling: Literal["none", "standard"] = "none"
    numeric_missing: Literal["error", "preserve"] = "error"
    unknown_municipality: Literal["explicit", "error"] = "explicit"

    def validate(self) -> None:
        """Reject unsupported configurations before fitting or transforming."""
        if (
            self.encoding not in ("native", "onehot", "ordinal")
            or self.numeric_scaling not in ("none", "standard")
            or self.numeric_missing not in ("error", "preserve")
            or self.unknown_municipality not in ("explicit", "error")
        ):
            raise PreparationError("Unsupported preparer configuration")


def runtime_versions() -> dict[str, str]:
    """Return versions required to reproduce the preparer in inference.

    Returns:
        Python, pandas and NumPy version identifiers.
    """
    return {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}


def _check_numeric(frame: pd.DataFrame, numeric: list[str], spec: PreparerSpec) -> pd.DataFrame:
    """Validate numeric input without imputation.

    Args:
        frame: Predictor-only data.
        numeric: Ordered numeric names.
        spec: Explicit missing-value policy.

    Returns:
        Numeric values with missingness unchanged.

    Raises:
        PreparationError: If non-numeric, infinite or forbidden missing values appear.
    """
    try:
        values = frame[numeric].astype("Float64")
    except (ValueError, TypeError) as exc:
        raise PreparationError("Non-numeric predictor value") from exc
    if np.isinf(values.to_numpy(dtype=float, na_value=np.nan)).any() or (
        spec.numeric_missing == "error" and values.isna().any().any()
    ):
        raise PreparationError("Numeric missingness or infinity violates explicit policy")
    return values


def _category_values(
    frame: pd.DataFrame, name: str, categories: list[str], spec: PreparerSpec
) -> pd.Series:
    """Apply saved categories while keeping missing and unknown distinct from SEGURIDAD.

    Args:
        frame: Predictor-only data.
        name: Categorical column.
        categories: Saved vocabulary in explicit order.
        spec: Representation and unknown policy.

    Returns:
        Tokenized values; no parameters are learned here.

    Raises:
        PreparationError: If a zone or forbidden unknown municipality is encountered.
    """
    values = frame[name].astype("string").fillna(MISSING)
    unknown = ~values.isin(categories)
    if unknown.any():
        if name != "municipality_code" or spec.unknown_municipality == "error":
            raise PreparationError(f"Unknown categorical value: {name}")
        values = values.mask(unknown, UNKNOWN)
    return values


def fit_preparer(X_train: pd.DataFrame, spec: PreparerSpec) -> dict[str, Any]:
    """Fit only training predictors and return safe JSON inference state.

    Args:
        X_train: Ordered raw candidate predictors, including municipality representation.
        spec: Future-estimator representation, scaling and missingness policy.

    Returns:
        Parameters, vocabularies, names/order, versions and exact training-X fingerprint.

    Raises:
        PreparationError: If controls, labels, empty data or invalid categories appear.
    """
    spec.validate()
    names = list(X_train.columns)
    if (
        X_train.empty
        or X_train.columns.duplicated().any()
        or not set(CATEGORICAL).issubset(names)
        or any(
            n.startswith(
                (
                    "y_",
                    "target_",
                    "history_",
                    "p25_",
                    "p50_",
                    "p75_",
                    "eligible_",
                    "reserved_",
                    "future_",
                )
            )
            or n
            in (
                "year_month",
                "department_code",
                "municipality_name",
                "total_notifications_count",
                "in_epi_coverage",
                "epi_count_status",
                "climate_days_observed",
                "expected_days_in_month",
                "feature_row",
            )
            or n.endswith("_valid_days")
            for n in names
        )
    ):
        raise PreparationError("Preparer requires nonempty predictor-only X in declared order")
    categories = {
        "municipality_code": sorted(X_train["municipality_code"].dropna().astype(str).unique())
        + [MISSING, UNKNOWN],
        "zona_canal_t": [*ZONES, MISSING],
        "zona_canal_lag_1": [*ZONES, MISSING],
    }
    if any(len(v) != len(set(v)) for v in categories.values()):
        raise PreparationError("Reserved category token present as source municipality")
    numeric = [n for n in names if n not in CATEGORICAL]
    values = _check_numeric(X_train, numeric, spec)
    statistics: dict[str, Any] = {}
    if spec.numeric_scaling == "standard":
        for n in numeric:
            valid = values[n].dropna()
            if valid.empty:
                raise PreparationError(f"Insufficient training history for scaling: {n}")
            scale = float(valid.std(ddof=0))
            statistics[n] = {"mean": float(valid.mean()), "scale": scale if scale > 0 else 1.0}
    outputs = (
        numeric + [f"{n}={v}" for n in CATEGORICAL for v in categories[n]]
        if spec.encoding == "onehot"
        else names
    )
    state = {
        "schema": "training-preparer-v1",
        "spec": asdict(spec),
        "input_columns": names,
        "output_columns": outputs,
        "numeric_columns": numeric,
        "categories": categories,
        "statistics": statistics,
        "versions": runtime_versions(),
        "fit_rows": len(X_train),
        "fit_X_fingerprint": bytes_record(serialize_table(X_train)),
    }
    # Verify native/encoded representation on training without ever consulting Y.
    transform_predictors(X_train, state)
    return state


def transform_predictors(X: pd.DataFrame, state: dict[str, Any]) -> pd.DataFrame:
    """Apply a saved preparer to validation or inference without refitting.

    Args:
        X: Raw predictor columns in the fitted order.
        state: JSON state returned by fit_preparer, with matching runtime versions.

    Returns:
        Matrix with stable column order and native category dtypes when requested.

    Raises:
        PreparationError: If schema, runtime or explicit data policies differ.
    """
    if (
        state.get("schema") != "training-preparer-v1"
        or list(X.columns) != state["input_columns"]
        or state["versions"] != runtime_versions()
    ):
        raise PreparationError("Inference schema/order or runtime version mismatch")
    spec = PreparerSpec(**state["spec"])
    spec.validate()
    numeric = state["numeric_columns"]
    values = _check_numeric(X, numeric, spec)
    for n, params in state["statistics"].items():
        values[n] = (values[n] - params["mean"]) / params["scale"]
    columns = {name: values[name] for name in numeric}
    for name in CATEGORICAL:
        categories = state["categories"][name]
        tokens = _category_values(X, name, categories, spec)
        if spec.encoding == "onehot":
            for category in categories:
                columns[f"{name}={category}"] = tokens.eq(category).astype("Float64")
        elif spec.encoding == "native":
            columns[name] = pd.Categorical(tokens, categories=categories, ordered=False)
        else:
            columns[name] = tokens.map({v: i for i, v in enumerate(categories)}).astype("Int64")
    return pd.DataFrame(columns, index=X.index)[state["output_columns"]]
