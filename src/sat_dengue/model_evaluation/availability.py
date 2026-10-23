"""Label-derived monthly availability, shared by execution and persisted replay."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from .contract import ModelEvaluationError

ROLES = (
    "hyperparameter_selection",
    "calibration_fit",
    "calibration_selection",
    "threshold_selection",
)


def availability_transition(
    producer_targets: pd.Series,
    consumer_origins: pd.Series,
    *,
    dependencies: dict[str, str],
    producer: str,
    consumer: str,
) -> dict[str, Any]:
    """Require all labeled producer outcomes and fitted dependencies before consumption.

    Args:
        producer_targets: Actual labeled target months used by the producer.
        consumer_origins: Actual origins of predictions consuming the decision.
        dependencies: Verified component availability months, including training label ends.
        producer: Producer role name.
        consumer: Consumer role name.

    Returns:
        Row-derived audit record. Equality is allowed at retrospective monthly closure.

    Raises:
        ModelEvaluationError: If any required outcome/component is available too late.
    """
    if (
        producer_targets.empty
        or consumer_origins.empty
        or producer_targets.isna().any()
        or consumer_origins.isna().any()
    ):
        raise ModelEvaluationError("Availability requires complete producer/consumer rows")
    targets = producer_targets.astype(str)
    origins = consumer_origins.astype(str)
    effective = (
        max(str(targets.max()), *dependencies.values()) if dependencies else str(targets.max())
    )
    valid = effective <= str(origins.min())
    record = dict(
        producer_role=producer,
        consumer_role=consumer,
        producer_target_min=str(targets.min()),
        producer_target_max=str(targets.max()),
        consumer_origin_min=str(origins.min()),
        consumer_origin_max=str(origins.max()),
        effective_availability=effective,
        dependencies=json.dumps(dependencies, sort_keys=True),
        availability_pass=valid,
    )
    if not valid:
        raise ModelEvaluationError(
            f"Label availability violation {producer} -> {consumer}: {effective} > {origins.min()}"
        )
    return record


def transition_records(
    frame: pd.DataFrame,
    target: str,
    external_origins: pd.Series,
    components: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compute all four transitions from observed role rows and verified component states.

    Args:
        frame: Keyed internal rows with roles and labeled targets.
        target: Horizon-specific target column.
        external_origins: Actual external origins, without external outcomes.
        components: Training/selection availability recorded and verified from training keys.

    Returns:
        Four accepted transition records; invalid transitions raise.
    """
    records = []
    previous = components["hp_model_target_end"]
    for position, producer in enumerate(ROLES):
        consumer = ROLES[position + 1] if position < 3 else "posterior_evaluation"
        produced = frame[frame.split_role.eq(producer)][target]
        origins = (
            frame[frame.split_role.eq(consumer)].year_month if position < 3 else external_origins
        )
        dependencies = {"upstream_decision": previous}
        if position < 3:
            dependencies["model_and_preparer_training_labels"] = components[
                "internal_model_target_end"
            ]
        else:
            dependencies.update(
                model_training_labels=components["outer_model_target_end"],
                preparer_training_labels=components["outer_model_target_end"],
                configuration_labels=components["configuration_target_end"],
                calibrator_labels=components["calibrator_target_end"],
            )
        row = availability_transition(
            produced, origins, dependencies=dependencies, producer=producer, consumer=consumer
        )
        previous = row["effective_availability"]
        records.append(row)
    return records


def preflight_window(
    dataset: Any, calendar: dict[str, Any], support: dict[str, int]
) -> dict[str, Any]:
    """Validate one frozen calendar on actual training rows before any model fitting.

    Args:
        dataset: Verified external window with separate train X/Y and keys.
        calendar: Declared role months and fit cutoffs.
        support: Unchanged minimum role month counts.

    Returns:
        Actual support and row-derived component availability.
    """
    target = dataset.target_column
    frame = dataset.train_index.copy()
    frame["label"] = dataset.train_y[dataset.y_column]
    chunks = []
    supports = {}
    municipalities = set(frame.municipality_code)
    for role in ROLES:
        months = calendar[f"{role}_targets"]
        rows = frame[frame[target].isin(months)].copy()
        if len(set(months)) < support[f"min_{role}_months"] or set(rows[target]) != set(months):
            raise ModelEvaluationError(f"Insufficient {role} month support")
        if rows.duplicated(["municipality_code", target]).any() or any(
            set(g.municipality_code) != municipalities for _, g in rows.groupby(target)
        ):
            raise ModelEvaluationError(f"Incomplete population for {role}")
        if rows.label.isna().any() or (rows[target] >= "2025-01").any():
            raise ModelEvaluationError("Unavailable/reserved internal labels")
        supports[role] = dict(
            rows=len(rows),
            months=len(months),
            positives=int(rows.label.sum()),
            negatives=int(rows.label.eq(0).sum()),
        )
        if role in ("hyperparameter_selection", "calibration_fit") and rows.label.nunique() != 2:
            raise ModelEvaluationError(f"Both classes required before fitting: {role}")
        rows["split_role"] = role
        chunks.append(rows)
    roles = pd.concat(chunks)
    hp_cut = calendar["hyperparameter_model_fit_cutoff"]
    internal_cut = calendar["internal_model_fit_cutoff"]
    components = {}
    for key, cutoff in (
        ("hp_model_target_end", hp_cut),
        ("internal_model_target_end", internal_cut),
        ("outer_model_target_end", dataset.cutoff),
    ):
        training = frame[frame[target] <= cutoff]
        if training.empty or training.label.nunique() != 2:
            raise ModelEvaluationError("Insufficient model training support")
        components[key] = str(training[target].max())
    components["configuration_target_end"] = str(chunks[0][target].max())
    components["calibrator_target_end"] = str(chunks[1][target].max())
    if components["hp_model_target_end"] > str(chunks[0].year_month.min()):
        raise ModelEvaluationError("Hyperparameter model uses future labels")
    records = transition_records(roles, target, dataset.validation_index.year_month, components)
    return dict(support=supports, components=components, transitions=records)
