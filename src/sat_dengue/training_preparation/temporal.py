"""Pure reference-aligned temporal partitions; no I/O or fitting."""

from dataclasses import dataclass
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .contract import PreparationError
from .eligibility import readiness
from .features import KEYS


@dataclass(frozen=True)
class WindowSelection:
    """Selected rows and auditable configured/effective time boundaries.

    Args:
        train: Training rows selected by existing target-aware selector.
        validation: Sequential validation-origin rows selected by the same reference.
        audit: Actual support, configured target interval and independent agreement.
    """

    train: pd.DataFrame
    validation: pd.DataFrame
    audit: dict[str, Any]


def select_window(
    frame: pd.DataFrame, policy: dict[str, Any], cutoff: str, horizon: int
) -> WindowSelection:
    """Reuse the existing selectors and enforce training/validation causal boundaries.

    Args:
        frame: Development keys and target controls, with no reserved reference rows.
        policy: Current notification-year-backed policy.
        cutoff: Fit cutoff, inclusive for observable training targets.
        horizon: One or two calendar months.

    Returns:
        Reference row selections and audit distinguishing configured/effective periods.

    Raises:
        PreparationError: If calendar, labels or independent key sets disagree.
    """
    if horizon not in (1, 2) or frame.duplicated(KEYS).any():
        raise PreparationError("Invalid horizon or duplicate temporal keys")
    bounds = policy["development_target_eligibility"]
    if (frame["year_month"] >= bounds["reserved_block_start"]).any():
        raise PreparationError("Reserved origins cannot enter temporal preparation")
    target_column, label_column = f"target_period_t{horizon}", f"y_t{horizon}"
    expected = pd.Series(
        (pd.PeriodIndex(frame["year_month"], freq="M") + horizon).astype(str), index=frame.index
    )
    if not frame[target_column].eq(expected).all():
        raise PreparationError("Target calendar contradicts prediction origin/horizon")
    configured_start = str(pd.Period(cutoff, freq="M") + 1)
    configured_end = str(pd.Period(cutoff, freq="M") + 6)
    target_end = min(
        configured_end,
        bounds["target_max"],
        str(pd.Period(bounds["reserved_block_start"], freq="M") - 1),
    )
    target_start = max(configured_start, bounds["target_min"])
    selections = []
    for split, kwargs in (
        (
            "train",
            dict(
                reference_max_period=cutoff,
                target_min_period=bounds["target_min"],
                target_max_period=min(cutoff, bounds["target_max"]),
            ),
        ),
        (
            "validation",
            dict(
                reference_min_period=cutoff,
                reference_max_period=configured_end,
                target_min_period=target_start,
                target_max_period=target_end,
            ),
        ),
    ):
        selected = readiness.independent_select_supervised_rows(frame, horizon, **kwargs)
        if (
            selected.empty
            or selected[label_column].isna().any()
            or not selected[label_column].isin([0, 1]).all()
        ):
            raise PreparationError(f"Empty or non-evaluable temporal selection: {split}")
        if (selected[target_column] >= bounds["reserved_block_start"]).any():
            raise PreparationError("Reserved target entered development")
        selections.append(selected)
    train, validation = selections
    if (
        (train[target_column] > cutoff).any()
        or (validation["year_month"] < cutoff).any()
        or not validation[target_column].between(target_start, target_end).all()
        or set(train.index) & set(validation.index)
    ):
        raise PreparationError("Temporal causal boundary or partition overlap violated")
    audit = {
        "cutoff": cutoff,
        "horizon": horizon,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "configured_target_start": configured_start,
        "configured_target_end": configured_end,
        "reference_selector_agrees": True,
        "validation_semantics": (
            "Sequential predictions at each origin using information at that origin; "
            "not a single forecast at fit cutoff."
        ),
    }
    for split, selected in (("train", train), ("validation", validation)):
        audit[split] = {
            "origin_start": str(selected["year_month"].min()),
            "origin_end": str(selected["year_month"].max()),
            "target_start": str(selected[target_column].min()),
            "target_end": str(selected[target_column].max()),
        }
    return WindowSelection(train, validation, audit)
