"""Nested temporal selection using existing selectors and the approved Stage 4 policy."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.metrics import average_precision_metric, brier_metric
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes, serialize_table
from sat_dengue.training_preparation.temporal import WindowSelection, select_window

from .candidate_families import FittedModel, fit_model, simplicity, validate_grid
from .contract import ModelTrainingError


@dataclass
class SelectionResult:
    """Training-only result of bounded internal selection and outer refitting.

    Args:
        fitted: Model/preparer fitted on complete permitted outer training.
        selected: Selected predeclared configuration.
        evidence: Split, fit, timing, score and tie evidence.
        oof: Keyed internal out-of-sample probabilities for all configurations.
    """

    fitted: FittedModel
    selected: dict[str, Any]
    evidence: dict[str, Any]
    oof: pd.DataFrame


def internal_folds(
    index: pd.DataFrame, y: pd.Series, *, cutoff: str, horizon: int
) -> list[WindowSelection]:
    """Select two six-month folds entirely inside the permitted outer training.

    Args:
        index: Outer training linkage keys only, in X order.
        y: Evaluable outer training labels.
        cutoff: External fit cutoff, inclusive for observable labels.
        horizon: One or two months.

    Returns:
        Existing Stage 3 selections at cutoff minus12 and minus6 months.
    """
    target = f"target_period_t{horizon}"
    if (
        not index.index.equals(y.index)
        or y.isna().any()
        or not y.isin([0, 1]).all()
        or (index[target] > cutoff).any()
        or (index[target] >= "2025-01").any()
    ):
        raise ModelTrainingError("Invalid outer training boundary/alignment")
    frame = index.copy()
    frame[f"y_t{horizon}"] = y
    frame[f"y_evaluable_t{horizon}"] = True
    policy = {
        "development_target_eligibility": {
            "target_min": "2012-01",
            "target_max": cutoff,
            "reserved_block_start": "2025-01",
        }
    }
    return [
        select_window(frame, policy, str(pd.Period(cutoff, freq="M") - offset), horizon)
        for offset in (12, 6)
    ]


def tied_configurations(scores: list[dict[str, Any]], policy: dict[str, Any]) -> list[str]:
    """Apply approved AP/Brier/family-simplicity order with fixed absolute tolerance.

    Args:
        scores: Complete two-fold means and explicit complexity tuples.
        policy: Existing approved selection_policy, not a new selection rule.

    Returns:
        Canonical IDs still tied after the approved complexity rule.
    """
    if not scores or any(not np.isfinite([r["ap"], r["brier"]]).all() for r in scores):
        raise ModelTrainingError("Every candidate needs evaluable internal AP and Brier")
    tolerance = policy["numeric_ties"]["absolute_tolerance"]
    best = max(r["ap"] for r in scores)
    tied = [r for r in scores if best - r["ap"] <= tolerance]
    best_brier = min(r["brier"] for r in tied)
    tied = [r for r in tied if r["brier"] - best_brier <= tolerance]
    complexity = min(r["simplicity"] for r in tied)
    return sorted(str(r["id"]) for r in tied if r["simplicity"] == complexity)


def choose_configuration(scores: list[dict[str, Any]], policy: dict[str, Any]) -> str:
    """Return the canonical representative, preserving residual scientific ties elsewhere.

    Args:
        scores: Two-fold internal candidate scores and complexity tuples.
        policy: Existing approved policy.

    Returns:
        Deterministic ID for fitting; no claim of superiority among residual ties.
    """
    return tied_configurations(scores, policy)[0]


def select_and_fit(
    X: pd.DataFrame,
    y: pd.Series,
    index: pd.DataFrame,
    *,
    cutoff: str,
    horizon: int,
    settings: dict[str, Any],
    policy: dict[str, Any],
    family: str = "xgboost",
) -> SelectionResult:
    """Select then refit using only outer-training inputs; external data are not accepted.

    Args:
        X: Raw outer training predictors.
        y: Existing binary labels.
        index: Separate outer training linkage keys.
        cutoff: Inclusive observable-target cutoff.
        horizon: Forecast horizon.
        settings: Frozen grid, seed and resource limits.
        policy: Existing approved Stage 4 selection policy.
        family: One of the three declared adapters.

    Returns:
        Selected fitted model, reproducible search evidence and internal predictions.
    """
    if not X.index.equals(y.index) or not X.index.equals(index.index):
        raise ModelTrainingError("Training linkage indices differ")
    grid = settings["configurations"]
    if not 1 <= len(grid) <= 6 or settings["inner_folds"] != 2:
        raise ModelTrainingError("Search exceeds six configurations/two internal folds")
    validate_grid(family, grid)
    folds = internal_folds(index, y, cutoff=cutoff, horizon=horizon)
    records: list[dict[str, Any]] = []
    oof: list[pd.DataFrame] = []
    summaries = []
    for number, params in enumerate(grid):
        cid = f"{family}_{number:02d}"
        local = []
        for fold_number, fold in enumerate(folds):
            tr, va = fold.train.index, fold.validation.index
            started = perf_counter()
            fitted = fit_model(
                family,
                X.loc[tr],
                y.loc[tr],
                params,
                seed=settings["seed"],
                threads=settings["threads"],
            )
            probability = fitted.predict(X.loc[va])
            ap = average_precision_metric(y.loc[va], probability)
            brier = brier_metric(y.loc[va], probability)
            if ap["value"] is None or brier["value"] is None:
                raise ModelTrainingError("Internal fold not evaluable; never omit a fold")
            record = dict(
                configuration_id=cid,
                fold=fold_number,
                parameters=params,
                ap=ap["value"],
                brier=brier["value"],
                elapsed_seconds=perf_counter() - started,
                boundaries=fold.audit,
                preparer=fitted.preparer,
                train_keys=bytes_record(serialize_table(index.loc[tr])),
                validation_keys=bytes_record(serialize_table(index.loc[va])),
            )
            records.append(record)
            local.append(record)
            oof.append(
                index.loc[va].assign(
                    configuration_id=cid, fold=fold_number, prediction_probability=probability
                )
            )
        summaries.append(
            dict(
                id=cid,
                parameters=params,
                ap=float(np.mean([r["ap"] for r in local])),
                brier=float(np.mean([r["brier"] for r in local])),
                simplicity=simplicity(family, X.shape[1], params, fitted.preparer),
            )
        )
    selected_id = choose_configuration(summaries, policy)
    selected = next(r["parameters"] for r in summaries if r["id"] == selected_id)
    started = perf_counter()
    final = fit_model(family, X, y, selected, seed=settings["seed"], threads=settings["threads"])
    evidence = dict(
        selected_id=selected_id,
        residual_tied_ids=tied_configurations(summaries, policy),
        selected=selected,
        folds=records,
        candidates=summaries,
        outer_fit_seconds=perf_counter() - started,
        training_fingerprint=bytes_record(serialize_table(X)),
        training_y_fingerprint=bytes_record(serialize_table(y.to_frame())),
        policy_fingerprint=bytes_record(json_bytes(policy)),
        fit_count=len(records) + 1,
        residual_tie_rule="Canonical ID is display stability, not scientific superiority",
    )
    return SelectionResult(final, selected, evidence, pd.concat(oof, ignore_index=True))
