"""Pure cohort construction, ordered schemas and actual temporal availability."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.model_evaluation.availability import availability_transition
from sat_dengue.model_training.events import build_event_context
from sat_dengue.training_preparation.features import derive_features


@dataclass
class Cohort:
    """Separate predictors, targets, keys and evaluation-only context for one horizon.

    Args:
        horizon: Forecast months.
        train_X: Raw train-only predictors.
        train_y: Complete training outcomes.
        train_index: Actual training keys including target dates.
        X: Full reserved predictor population, including explicit missing rows.
        y: Nullable reserved outcomes.
        index: Complete expected keys in stable order.
        context: Original S/S−1 scientific states, never predictors.
    """

    horizon: int
    train_X: pd.DataFrame
    train_y: pd.Series
    train_index: pd.DataFrame
    X: pd.DataFrame
    y: pd.Series
    index: pd.DataFrame
    context: pd.DataFrame


def expected_index(population: list[str], targets: list[str], horizon: int) -> pd.DataFrame:
    """Build the declared municipality/calendar product without reading outcomes.

    Args:
        population: Exact approved municipal codes.
        targets: Canonical target months.
        horizon: Forecast months.

    Returns:
        Ordered unique municipality/origin/target keys.
    """
    frame = (
        pd.MultiIndex.from_product(
            [population, targets], names=["municipality_code", "target_period"]
        )
        .to_frame(index=False)
        .astype("string")
    )
    frame["year_month"] = (pd.PeriodIndex(frame.target_period, freq="M") - horizon).astype(str)
    return frame[["municipality_code", "year_month", "target_period"]]


def build_cohorts(
    panel: pd.DataFrame, contract: dict[str, Any], proposal: dict[str, Any]
) -> dict[int, Cohort]:
    """Construct and preflight both horizons before any adapter is called.

    Args:
        panel: Authorized source history or explicitly synthetic fixture.
        contract: Unchanged preparation contract.
        proposal: Verified six-procedure scientific proposal.

    Returns:
        Complete cohorts with unknown evaluation evidence retained, never dropped.
    """
    population = proposal["common_population"]
    features = derive_features(panel.loc[panel.year_month <= "2025-12"], contract)
    keys = ["municipality_code", "year_month"]
    source = panel.set_index(keys)
    feature_source = features.set_index(keys)
    cohorts = {}
    for h in (1, 2):
        procedures = [p for p in proposal["procedures"] if p["horizon"] == h]
        procedure = procedures[0]
        columns = procedure["future_preparer"]["input_columns"]
        if any(p["future_preparer"]["input_columns"] != columns for p in procedures):
            raise ValueError("Frozen feature schemas differ across families")
        expected_columns = ["municipality_code", *features.columns.drop(keys)]
        if columns != expected_columns:
            raise ValueError(
                "Frozen predictor allowlist/order differs from deterministic preparation"
            )

        def select(
            index: pd.DataFrame, columns: list[str] = columns, h: int = h
        ) -> tuple[pd.DataFrame, pd.Series]:
            requested = pd.MultiIndex.from_frame(index[keys])
            X = feature_source.reindex(requested).reset_index()[columns]
            labels = source.reindex(requested)
            declared = labels[f"target_period_t{h}"].reset_index(drop=True).astype("string")
            if (declared.notna() & declared.ne(index.target_period)).any():
                raise ValueError("Target/origin calendar mismatch in scientific panel")
            y = labels[f"y_t{h}"].reset_index(drop=True).astype("Int64")
            evaluable = (
                labels[f"y_evaluable_t{h}"].reset_index(drop=True).fillna(False).astype(bool)
            )
            return X, y.where(evaluable)

        train_targets = (
            pd.period_range(
                procedure["training_target_start"], procedure["training_target_end"], freq="M"
            )
            .astype(str)
            .tolist()
        )
        train_index = expected_index(population, train_targets, h)
        index = expected_index(population, procedure["targets"], h)
        train_X, train_y = select(train_index)
        X, y = select(index)
        states = (
            panel[["municipality_code", "year_month", "zona_canal_t"]]
            .rename(columns={"year_month": "target_period"})
            .copy()
        )
        states["excess"] = (
            states.zona_canal_t.eq("EXCESO").where(states.zona_canal_t.notna()).astype("Int64")
        )
        context = build_event_context(
            index,
            states,
            target_column="target_period",
            target_start="2025-01",
            reserved_start="2026-01",
        )
        cohort = Cohort(h, train_X, train_y, train_index, X, y, index, context)
        validate_cohort(cohort, proposal)
        cohorts[h] = cohort
    return cohorts


def validate_cohort(cohort: Cohort, proposal: dict[str, Any]) -> dict[str, Any]:
    """Audit exact cohorts, support and actual label/component availability before fits.

    Args:
        cohort: Selected horizon data.
        proposal: Exact protocol and component specifications.

    Returns:
        Bounded preflight counts and actual availability evidence.
    """
    procedures = [p for p in proposal["procedures"] if p["horizon"] == cohort.horizon]
    p = procedures[0]
    expected = expected_index(proposal["common_population"], p["targets"], cohort.horizon)
    if not cohort.index.astype("string").equals(expected.astype("string")):
        raise ValueError("Incomplete or misaligned evaluation cohort")
    expected_train = expected_index(
        proposal["common_population"],
        pd.period_range(p["training_target_start"], p["training_target_end"], freq="M")
        .astype(str)
        .tolist(),
        cohort.horizon,
    )
    if not cohort.train_index.astype("string").equals(expected_train.astype("string")):
        raise ValueError("Training cohort/calendar mismatch")
    for X, y, index in [
        (cohort.X, cohort.y, cohort.index),
        (cohort.train_X, cohort.train_y, cohort.train_index),
    ]:
        if not X.index.equals(y.index) or not X.index.equals(index.index) or len(X) != len(index):
            raise ValueError("X/Y/key alignment mismatch")
        if list(X.columns) != p["future_preparer"]["input_columns"]:
            raise ValueError("Labels, controls or undeclared columns in X")
        if not X.municipality_code.astype("string").equals(
            index.municipality_code.astype("string")
        ):
            raise ValueError("Municipal alignment mismatch")
        if not y.dropna().isin([0, 1]).all():
            raise ValueError("Nonbinary labels")
        numeric = X.select_dtypes(include="number")
        if not np.isfinite(
            numeric.to_numpy(dtype=float, na_value=np.nan)[numeric.notna().to_numpy()]
        ).all():
            raise ValueError("Invalid infinite predictor")
    if (
        cohort.train_X.isna().any().any()
        or cohort.train_y.isna().any()
        or set(cohort.train_y.unique()) != {0, 1}
    ):
        raise ValueError(
            "Incomplete training evidence or class support; no imputation/drop allowed"
        )
    if not cohort.context.index.equals(cohort.y.index):
        raise ValueError("Context alignment mismatch")
    known = cohort.y.notna()
    if (
        not cohort.y[known]
        .astype("Int64")
        .equals(cohort.context.actual_excess[known].astype("Int64"))
    ):
        raise ValueError("Y differs from the existing scientific target state")
    checks = []
    for procedure in procedures:
        dependencies = {
            r["producer_role"]: r["effective_availability"]
            for r in procedure["retained_component_availability_checks"]
        }
        checks.append(
            availability_transition(
                cohort.train_index.target_period,
                cohort.index.year_month,
                dependencies=dependencies,
                producer="final_model_and_preparer",
                consumer="reserved_prediction",
            )
        )
    return dict(
        horizon=cohort.horizon,
        rows=len(cohort.index),
        municipalities=cohort.index.municipality_code.nunique(),
        train_rows=len(cohort.train_index),
        train_positives=int(cohort.train_y.eq(1).sum()),
        train_negatives=int(cohort.train_y.eq(0).sum()),
        evaluation_positives=int(cohort.y.eq(1).sum()),
        evaluation_negatives=int(cohort.y.eq(0).sum()),
        missing_labels=int(cohort.y.isna().sum()),
        missing_predictor_rows=int(cohort.X.isna().any(axis=1).sum()),
        unknown_event_rows=int((~cohort.context.onset_evaluable).sum()),
        availability=checks,
    )
