"""Existing calibration, temporal and threshold calculations; no storage or framework."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]

from sat_dengue.metrics import average_precision_metric, brier_metric, evaluate_metrics
from sat_dengue.model_training.loading import WindowDataset
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

from .availability import transition_records
from .contract import ModelEvaluationError, Stage5Contract


def _window_index_with_labels(dataset: WindowDataset, horizon: int) -> pd.DataFrame:
    """Build train index rows with labels and zone state for one window.

    Args:
        dataset: Temporal train/validation rows for one window.
        horizon: Forecast horizon.

    Returns:
        Train key rows augmented with label and zone context.
    """
    target_column = f"target_period_t{horizon}"
    y_column = f"y_t{horizon}"
    frame = dataset.train_index[
        ["municipality_code", "year_month", target_column, "feature_row"]
    ].copy()
    frame[y_column] = dataset.train_y[y_column].astype("Int64").reset_index(drop=True)
    frame["zona_canal_t"] = dataset.train_X["zona_canal_t"].astype("string").reset_index(drop=True)
    return frame


def _read_window_calendar(contract: Stage5Contract, window: str) -> dict[str, Any]:
    """Return one explicit role calendar from Stage 5 contract."""
    calendar = contract.raw["window_role_calendar"].get(window)
    if not isinstance(calendar, dict):
        raise ModelEvaluationError(f"Missing role calendar for window: {window}")
    return calendar


def _validate_role_calendar_against_dataset(
    window: str,
    dataset: WindowDataset,
    horizon: int,
    calendar: dict[str, Any],
    *,
    reserved_start: str,
) -> None:
    """Validate role-calendar targets/origins against actual temporal supports."""
    target_column = f"target_period_t{horizon}"
    validation = dataset.validation_index
    eval_origin = calendar["external_evaluation_origin_range"]
    eval_target = calendar["external_evaluation_target_range"]

    observed_origin_start = str(validation["year_month"].min())
    observed_origin_end = str(validation["year_month"].max())
    observed_target_start = str(validation[target_column].min())
    observed_target_end = str(validation[target_column].max())

    if (
        eval_origin["start"] != observed_origin_start
        or eval_origin["end"] != observed_origin_end
        or eval_target["start"] != observed_target_start
        or eval_target["end"] != observed_target_end
    ):
        raise ModelEvaluationError(f"External evaluation range mismatch for {window}")

    role_names = (
        "hyperparameter_selection_targets",
        "calibration_fit_targets",
        "calibration_selection_targets",
        "threshold_selection_targets",
    )
    months = [month for role_name in role_names for month in calendar[role_name]]
    if any(month >= reserved_start for month in months):
        raise ModelEvaluationError(f"Reserved target month entered role calendar for {window}")


def _merge_internal_with_truth(
    inner: pd.DataFrame,
    dataset: WindowDataset,
    horizon: int,
    *,
    reserved_start: str,
    window: str,
) -> pd.DataFrame:
    """Join internal predictions with train labels and enforce integrity checks."""
    target_column = f"target_period_t{horizon}"
    y_column = f"y_t{horizon}"
    truth = _window_index_with_labels(dataset, horizon)
    merged = inner.merge(
        truth,
        on=["municipality_code", "year_month", target_column, "feature_row"],
        how="left",
        validate="many_to_one",
    )
    if merged[y_column].isna().any():
        raise ModelEvaluationError(f"Internal predictions missing labels for {window}")
    if not merged[y_column].isin([0, 1]).all():
        raise ModelEvaluationError(f"Internal predictions contain non-binary labels for {window}")
    if (merged[target_column] >= reserved_start).any():
        raise ModelEvaluationError(f"Internal predictions leak reserved targets for {window}")
    return merged


def _assign_internal_role(
    frame: pd.DataFrame,
    target_column: str,
    calendar: dict[str, Any],
) -> pd.Series:
    """Assign temporal role names from explicit target-month calendars."""
    role_by_month: dict[str, str] = {}
    for role_name, output in ROLE_CALENDAR_TO_SPLIT:
        for month in calendar[role_name]:
            role_by_month[month] = output
    return frame[target_column].map(role_by_month).fillna("unused").astype("string")


def _month_ordinal(month: str) -> int:
    """Return the monthly ordinal for deterministic chronology comparisons."""
    return int(pd.Period(month, freq="M").ordinal)


def _month_gap(start: str, end: str) -> int:
    """Return end-start month distance in integer months."""
    return _month_ordinal(end) - _month_ordinal(start)


def _month_lag_series(frame: pd.DataFrame, target_column: str) -> pd.Series:
    """Return target-origin lag in months per row."""
    target_ordinals = pd.PeriodIndex(
        frame[target_column].astype("string"),
        freq="M",
    ).astype("int64")
    origin_ordinals = pd.PeriodIndex(
        frame["year_month"].astype("string"),
        freq="M",
    ).astype("int64")
    return pd.Series(target_ordinals - origin_ordinals, dtype="Int64")


def _role_boundaries(
    *,
    candidate: str,
    window: str,
    frame: pd.DataFrame,
    target_column: str,
    calendar: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Collect observed target/origin ranges for each internal role with strict month coverage."""
    boundaries: dict[str, dict[str, Any]] = {}
    for calendar_key, split_role in ROLE_CALENDAR_TO_SPLIT:
        role_frame = frame[frame["split_role"] == split_role]
        if role_frame.empty:
            raise ModelEvaluationError(
                f"Internal role has no rows for {candidate} {window}: {split_role}"
            )
        observed = set(role_frame[target_column].astype("string"))
        expected = set(calendar[calendar_key])
        if observed != expected:
            missing = sorted(expected - observed)
            unexpected = sorted(observed - expected)
            raise ModelEvaluationError(
                f"{candidate} {window} {split_role} target coverage mismatch: "
                f"missing={missing} unexpected={unexpected}"
            )
        boundaries[split_role] = {
            "target_start": str(role_frame[target_column].min()),
            "target_end": str(role_frame[target_column].max()),
            "origin_start": str(role_frame["year_month"].min()),
            "origin_end": str(role_frame["year_month"].max()),
            "rows": int(role_frame.shape[0]),
        }
    return boundaries


def _build_temporal_audit_row(
    *,
    candidate: str,
    window: str,
    horizon: int,
    cutoff: str,
    selected_configuration_id: str,
    selected_internal: pd.DataFrame,
    target_column: str,
    calendar: dict[str, Any],
    reserved_start: str,
    external_origin_start: str,
    hp_folds: set[int],
    development_folds: set[int],
    components: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one row-level temporal audit record using observed labeled-target availability."""
    boundaries = _role_boundaries(
        candidate=candidate,
        window=window,
        frame=selected_internal,
        target_column=target_column,
        calendar=calendar,
    )

    if components is None:
        # Synthetic callers can exercise row-derived transitions without a fitted model.
        components = dict(
            hp_model_target_end=boundaries["hyperparameter_selection"]["origin_start"],
            internal_model_target_end=boundaries["hyperparameter_selection"]["target_end"],
            configuration_target_end=boundaries["hyperparameter_selection"]["target_end"],
            calibrator_target_end=boundaries["calibration_fit"]["target_end"],
            outer_model_target_end=cutoff,
        )
    observed_transitions = transition_records(
        selected_internal,
        target_column,
        pd.Series([external_origin_start, calendar["external_evaluation_origin_range"]["end"]]),
        components,
    )
    transition_lookup = {r["producer_role"]: r for r in observed_transitions}

    lag_series = _month_lag_series(selected_internal, target_column)
    lag_values = sorted({int(value) for value in lag_series.dropna().tolist()})
    lag_matches_horizon = lag_values == [horizon]

    chronology_by_target_pass = True
    chronology_by_origin_pass = True
    transition_passes: dict[str, bool] = {}
    transition_component_available: dict[str, str] = {}
    transition_consumer_origin_start: dict[str, str] = {}
    transition_origin_gap: dict[str, int] = {}

    for producer, consumer in zip(ROLE_SEQUENCE, ROLE_SEQUENCE[1:], strict=False):
        producer_end_target = boundaries[producer]["target_end"]
        consumer_start_target = boundaries[consumer]["target_start"]
        target_pass = producer_end_target < consumer_start_target
        chronology_by_target_pass = chronology_by_target_pass and target_pass

        producer_available_origin = transition_lookup[producer]["effective_availability"]
        consumer_origin_start = boundaries[consumer]["origin_start"]
        origin_pass = producer_available_origin <= consumer_origin_start
        chronology_by_origin_pass = chronology_by_origin_pass and origin_pass

        transition_name = f"{producer}_to_{consumer}"
        transition_passes[transition_name] = origin_pass
        transition_component_available[transition_name] = producer_available_origin
        transition_consumer_origin_start[transition_name] = consumer_origin_start
        transition_origin_gap[transition_name] = _month_gap(
            producer_available_origin,
            consumer_origin_start,
        )

    threshold_available_origin = transition_lookup["threshold_selection"]["effective_availability"]
    threshold_to_external_pass = threshold_available_origin <= external_origin_start
    component_available = threshold_available_origin
    component_available_pass = component_available <= external_origin_start
    no_reserved_pass = bool(
        selected_internal[target_column].astype("string").max() < reserved_start
    )

    return {
        "candidate": candidate,
        "window_id": window,
        "horizon": horizon,
        "cutoff": cutoff,
        "selected_configuration_id": selected_configuration_id,
        "hyperparameter_selection_target_start": boundaries["hyperparameter_selection"][
            "target_start"
        ],
        "hyperparameter_selection_target_end": boundaries["hyperparameter_selection"]["target_end"],
        "hyperparameter_selection_origin_start": boundaries["hyperparameter_selection"][
            "origin_start"
        ],
        "hyperparameter_selection_origin_end": boundaries["hyperparameter_selection"]["origin_end"],
        "calibration_fit_target_start": boundaries["calibration_fit"]["target_start"],
        "calibration_fit_target_end": boundaries["calibration_fit"]["target_end"],
        "calibration_fit_origin_start": boundaries["calibration_fit"]["origin_start"],
        "calibration_fit_origin_end": boundaries["calibration_fit"]["origin_end"],
        "calibration_selection_target_start": boundaries["calibration_selection"]["target_start"],
        "calibration_selection_target_end": boundaries["calibration_selection"]["target_end"],
        "calibration_selection_origin_start": boundaries["calibration_selection"]["origin_start"],
        "calibration_selection_origin_end": boundaries["calibration_selection"]["origin_end"],
        "threshold_selection_target_start": boundaries["threshold_selection"]["target_start"],
        "threshold_selection_target_end": boundaries["threshold_selection"]["target_end"],
        "threshold_selection_origin_start": boundaries["threshold_selection"]["origin_start"],
        "threshold_selection_origin_end": boundaries["threshold_selection"]["origin_end"],
        "observed_target_origin_lag_months": ",".join(str(value) for value in lag_values),
        "expected_target_origin_lag_months": horizon,
        "target_origin_lag_pass": lag_matches_horizon,
        "chronology_by_target_pass": chronology_by_target_pass,
        "chronology_by_origin_pass": chronology_by_origin_pass,
        "hyperparameter_to_calibration_fit_component_available_by_origin": (
            transition_component_available["hyperparameter_selection_to_calibration_fit"]
        ),
        "hyperparameter_to_calibration_fit_consumer_origin_start": (
            transition_consumer_origin_start["hyperparameter_selection_to_calibration_fit"]
        ),
        "hyperparameter_to_calibration_fit_origin_gap_months": transition_origin_gap[
            "hyperparameter_selection_to_calibration_fit"
        ],
        "hyperparameter_to_calibration_fit_pass": transition_passes[
            "hyperparameter_selection_to_calibration_fit"
        ],
        "calibration_fit_to_calibration_selection_component_available_by_origin": (
            transition_component_available["calibration_fit_to_calibration_selection"]
        ),
        "calibration_fit_to_calibration_selection_consumer_origin_start": (
            transition_consumer_origin_start["calibration_fit_to_calibration_selection"]
        ),
        "calibration_fit_to_calibration_selection_origin_gap_months": transition_origin_gap[
            "calibration_fit_to_calibration_selection"
        ],
        "calibration_fit_to_calibration_selection_pass": transition_passes[
            "calibration_fit_to_calibration_selection"
        ],
        "calibration_selection_to_threshold_component_available_by_origin": (
            transition_component_available["calibration_selection_to_threshold_selection"]
        ),
        "calibration_selection_to_threshold_consumer_origin_start": (
            transition_consumer_origin_start["calibration_selection_to_threshold_selection"]
        ),
        "calibration_selection_to_threshold_origin_gap_months": transition_origin_gap[
            "calibration_selection_to_threshold_selection"
        ],
        "calibration_selection_to_threshold_pass": transition_passes[
            "calibration_selection_to_threshold_selection"
        ],
        "threshold_component_available_by_origin": threshold_available_origin,
        "external_origin_start": calendar["external_evaluation_origin_range"]["start"],
        "external_origin_end": calendar["external_evaluation_origin_range"]["end"],
        "external_target_start": calendar["external_evaluation_target_range"]["start"],
        "external_target_end": calendar["external_evaluation_target_range"]["end"],
        "threshold_to_external_origin_pass": threshold_to_external_pass,
        "component_available_by_origin": component_available,
        "component_available_pass": component_available_pass,
        "hyperparameter_selection_fold_ids": ",".join(map(str, sorted(hp_folds))),
        "development_fold_ids": ",".join(map(str, sorted(development_folds))),
        "independence_pass": True,
        "no_reserved_pass": no_reserved_pass,
        "chronology_pass": (
            lag_matches_horizon
            and chronology_by_target_pass
            and chronology_by_origin_pass
            and all(transition_passes.values())
            and threshold_to_external_pass
        ),
    }


def _assert_verify_allowed(*, verify_only: bool, operation: str) -> None:
    """Fail fast if a fitting/selection operation is attempted while verifying."""
    if verify_only:
        raise ModelEvaluationError(f"verify_only forbids operation: {operation}")


def _calibrator_provenance(frame: pd.DataFrame, horizon: int) -> dict[str, Any]:
    """Fingerprint actual labeled calibration inputs for inference-only verification."""
    target, label = f"target_period_t{horizon}", f"y_t{horizon}"
    fit = frame[frame.split_role.eq("calibration_fit")].reset_index(drop=True)
    return dict(
        target_max=str(fit[target].max()),
        rows=len(fit),
        keys=bytes_record(
            serialize_table(fit[["municipality_code", "year_month", target, "feature_row"]])
        ),
        probabilities=bytes_record(serialize_table(fit[["probability_raw"]])),
        labels=bytes_record(serialize_table(fit[[label]])),
    )


def _apply_saved_calibrator(
    probability: pd.Series,
    calibrator_record: dict[str, Any],
) -> pd.Series:
    """Apply persisted calibrator parameters without fitting."""
    if not bool(calibrator_record.get("available")):
        return probability.astype("Float64")
    coefficient = float(calibrator_record["coefficient"])
    intercept = float(calibrator_record["intercept"])
    transformed = 1.0 / (
        1.0 + np.exp(-(coefficient * probability.to_numpy(dtype=float) + intercept))
    )
    return pd.Series(transformed, index=probability.index, dtype="Float64")


def _extract_fold_months(search: dict[str, Any]) -> dict[int, set[str]]:
    """Extract unique validation target months per internal fold."""
    fold_months: dict[int, set[str]] = {}
    for record in search["folds"]:
        fold = int(record["fold"])
        start = record["boundaries"]["validation"]["target_start"]
        end = record["boundaries"]["validation"]["target_end"]
        months = pd.period_range(start=start, end=end, freq="M")
        fold_months.setdefault(fold, set()).update(str(month) for month in months)
    return fold_months


def _assert_selection_independence(selected_internal: pd.DataFrame) -> tuple[set[int], set[int]]:
    """Reject fold leakage between hyperparameter selection and later roles.

    Args:
        selected_internal: Selected-configuration internal predictions with split_role and fold.

    Returns:
        Two disjoint fold-id sets: hyperparameter-selection folds and development folds.

    Raises:
        ModelEvaluationError: If any calibration/threshold prediction comes from the same fold
            used to select the configuration.
    """
    hp_folds = set(
        selected_internal.loc[
            selected_internal["split_role"].eq("hyperparameter_selection"), "fold"
        ].astype(int)
    )
    development_folds = set(
        selected_internal.loc[
            selected_internal["split_role"].isin(
                ["calibration_fit", "calibration_selection", "threshold_selection"]
            ),
            "fold",
        ].astype(int)
    )
    if not hp_folds or not development_folds or not hp_folds.isdisjoint(development_folds):
        raise ModelEvaluationError(
            "Selection independence violated: calibration/threshold rows share fold with "
            "hyperparameter-selection rows"
        )
    return hp_folds, development_folds


def _fit_sigmoid(
    probability: pd.Series,
    y_true: pd.Series,
    seed: int,
    *,
    allow_fit: bool = True,
) -> LogisticRegression | None:
    """Fit a sigmoid calibrator when both classes are present."""
    if not allow_fit:
        raise ModelEvaluationError("verify_only forbids operation: calibrator_fit")
    labels = y_true.astype("Int64")
    if labels.nunique(dropna=True) < 2:
        return None
    calibrator = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=seed)
    calibrator.fit(probability.to_numpy(dtype=float).reshape(-1, 1), labels.to_numpy(dtype=int))
    return calibrator


def _apply_sigmoid(probability: pd.Series, calibrator: LogisticRegression | None) -> pd.Series:
    """Apply sigmoid transform or preserve original probabilities."""
    if calibrator is None:
        return probability.astype("Float64")
    transformed = calibrator.predict_proba(probability.to_numpy(dtype=float).reshape(-1, 1))[:, 1]
    return pd.Series(transformed, index=probability.index, dtype="Float64")


def _calibration_curve_table(
    probability: pd.Series,
    y_true: pd.Series,
    *,
    bins: int,
    min_bin_support: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build calibration bins with support and weighted-gap summaries."""
    if bins < 2:
        raise ModelEvaluationError("calibration bins must be >=2")
    frame = pd.DataFrame(
        {
            "probability": probability.astype("Float64"),
            "y": y_true.astype("Int64"),
        }
    )
    if frame["probability"].isna().any() or frame["y"].isna().any():
        raise ModelEvaluationError("Calibration split contains unavailable labels or probabilities")
    if not frame["probability"].between(0, 1).all():
        raise ModelEvaluationError("Calibration probabilities must be within [0, 1]")

    edges = np.linspace(0.0, 1.0, bins + 1)
    frame["bin_id"] = pd.cut(
        frame["probability"],
        bins=edges,
        include_lowest=True,
        right=True,
        labels=False,
    )
    grouped = (
        frame.groupby("bin_id", dropna=False)
        .agg(
            rows=("y", "size"),
            positives=("y", "sum"),
            mean_probability=("probability", "mean"),
            observed_fraction=("y", "mean"),
        )
        .reset_index()
    )
    grouped["bin_id"] = grouped["bin_id"].astype(int)
    grouped["bin_lower"] = grouped["bin_id"].map(lambda idx: float(edges[idx]))
    grouped["bin_upper"] = grouped["bin_id"].map(lambda idx: float(edges[idx + 1]))
    grouped["absolute_gap"] = (grouped["observed_fraction"] - grouped["mean_probability"]).abs()
    grouped["supported"] = grouped["rows"] >= min_bin_support

    supported = grouped[grouped["supported"]]
    weighted_gap = None
    if not supported.empty and int(supported["rows"].sum()) > 0:
        weighted_gap = float(
            (supported["absolute_gap"] * supported["rows"]).sum() / supported["rows"].sum()
        )

    summary = {
        "rows": int(grouped["rows"].sum()),
        "positives": int(grouped["positives"].sum()),
        "supported_bins": int(supported.shape[0]),
        "supported_rows": int(supported["rows"].sum()) if not supported.empty else 0,
        "weighted_absolute_gap": weighted_gap,
    }
    return grouped, summary


def _choose_calibration(
    raw_brier: float,
    sigmoid_brier: float | None,
    raw_curve: dict[str, Any],
    sigmoid_curve: dict[str, Any] | None,
    policy: dict[str, Any],
) -> dict[str, Any]:
    """Apply predeclared acceptance and tie rules for calibration choice."""
    if sigmoid_brier is None or sigmoid_curve is None:
        return {
            "selected": "original",
            "reason": "sigmoid_unavailable",
            "raw_brier": raw_brier,
            "sigmoid_brier": None,
            "raw_weighted_gap": raw_curve["weighted_absolute_gap"],
            "sigmoid_weighted_gap": None,
        }

    brier_tolerance = float(policy["brier_tolerance"])
    gap_tolerance = float(policy["calibration_gap_tolerance"])
    min_supported_bins = int(policy["min_supported_bins"])

    if (
        sigmoid_brier + brier_tolerance < raw_brier
        and sigmoid_curve["supported_bins"] >= min_supported_bins
    ):
        return {
            "selected": "sigmoid",
            "reason": "brier_improved",
            "raw_brier": raw_brier,
            "sigmoid_brier": sigmoid_brier,
            "raw_weighted_gap": raw_curve["weighted_absolute_gap"],
            "sigmoid_weighted_gap": sigmoid_curve["weighted_absolute_gap"],
        }

    if abs(sigmoid_brier - raw_brier) <= brier_tolerance:
        raw_gap = raw_curve["weighted_absolute_gap"]
        sigmoid_gap = sigmoid_curve["weighted_absolute_gap"]
        if (
            raw_gap is not None
            and sigmoid_gap is not None
            and sigmoid_curve["supported_bins"] >= min_supported_bins
            and sigmoid_gap + gap_tolerance < raw_gap
        ):
            return {
                "selected": "sigmoid",
                "reason": "tied_brier_better_calibration_gap",
                "raw_brier": raw_brier,
                "sigmoid_brier": sigmoid_brier,
                "raw_weighted_gap": raw_gap,
                "sigmoid_weighted_gap": sigmoid_gap,
            }
        return {
            "selected": "original",
            "reason": "tied_brier_no_calibration_gain",
            "raw_brier": raw_brier,
            "sigmoid_brier": sigmoid_brier,
            "raw_weighted_gap": raw_gap,
            "sigmoid_weighted_gap": sigmoid_gap,
        }

    return {
        "selected": "original",
        "reason": "brier_not_improved",
        "raw_brier": raw_brier,
        "sigmoid_brier": sigmoid_brier,
        "raw_weighted_gap": raw_curve["weighted_absolute_gap"],
        "sigmoid_weighted_gap": sigmoid_curve["weighted_absolute_gap"],
    }


def _threshold_limits(
    persistence_onset: float | None,
    persistence_false_alarm: float | None,
    contract: Stage5Contract,
) -> tuple[float | None, float | None]:
    """Compute utility limits in proportion units."""
    if persistence_onset is None or persistence_false_alarm is None:
        return None, None
    return (
        persistence_onset + contract.knobs.min_onset_sensitivity_gain,
        persistence_false_alarm + contract.knobs.max_false_alarm_increase,
    )


def _build_threshold_grid(
    *,
    candidate: str,
    horizon: int,
    probability: pd.Series,
    y_true: pd.Series,
    index: pd.DataFrame,
    event_context: pd.DataFrame,
    precision: int,
) -> pd.DataFrame:
    """Evaluate threshold candidates with Stage 4 metric definitions."""
    values = sorted({0.0, 1.0, *probability.round(precision).to_list()})
    rows: list[dict[str, Any]] = []
    for threshold in values:
        prediction_label = probability.ge(threshold).astype("Int64")
        frame = pd.DataFrame(
            {
                "prediction_kind": "probabilistic",
                "prediction_score": probability,
                "prediction_probability": probability,
                "prediction_label": prediction_label,
            }
        )
        metrics = {
            record["metric"]: record
            for record in evaluate_metrics(
                candidate,
                y_true,
                frame,
                index,
                target_column=f"target_period_t{horizon}",
                threshold_policy_declared=True,
                event_context=event_context,
            )
        }
        onset = metrics["onset_sensitivity"]
        false_alarm = metrics["false_alarm_ratio"]
        rows.append(
            {
                "threshold": float(threshold),
                "onset_sensitivity": onset["value"],
                "onset_sensitivity_evaluable": bool(onset["evaluable"]),
                "detected_onsets": int(onset["numerator"]),
                "real_onsets": int(onset["denominator"]),
                "false_alarm_ratio": false_alarm["value"],
                "false_alarm_ratio_evaluable": bool(false_alarm["evaluable"]),
                "false_alerts": int(false_alarm["numerator"]),
                "emitted_alerts": int(false_alarm["denominator"]),
                "alerts_unavailable_rows": int(false_alarm.get("unavailable_rows", 0)),
            }
        )
    return pd.DataFrame(rows).sort_values("threshold").reset_index(drop=True)


def _select_threshold_from_grid(
    threshold_grid: pd.DataFrame,
    *,
    min_required_onset: float | None,
    max_allowed_false_alarm: float | None,
    allow_selection: bool = True,
) -> dict[str, Any]:
    """Select threshold maximizing onset sensitivity under false-alert constraint."""
    if not allow_selection:
        raise ModelEvaluationError("verify_only forbids operation: threshold_selection")
    if min_required_onset is None or max_allowed_false_alarm is None:
        return {
            "status": "baseline_unavailable",
            "selected_threshold": None,
            "meets_min_onset_gain": None,
            "selected_onset_sensitivity": None,
            "selected_false_alarm_ratio": None,
            "selected_false_alerts": None,
            "selected_emitted_alerts": None,
            "feasible_threshold_count": 0,
        }

    feasible = threshold_grid[
        threshold_grid["onset_sensitivity_evaluable"]
        & threshold_grid["false_alarm_ratio_evaluable"]
        & (threshold_grid["false_alarm_ratio"] <= max_allowed_false_alarm)
    ].copy()
    if feasible.empty:
        return {
            "status": "no_feasible_threshold",
            "selected_threshold": None,
            "meets_min_onset_gain": False,
            "selected_onset_sensitivity": None,
            "selected_false_alarm_ratio": None,
            "selected_false_alerts": None,
            "selected_emitted_alerts": None,
            "feasible_threshold_count": 0,
        }

    feasible = feasible.sort_values(
        by=["onset_sensitivity", "false_alerts", "false_alarm_ratio", "threshold"],
        ascending=[False, True, True, False],
    )
    chosen = feasible.iloc[0]
    onset = float(chosen["onset_sensitivity"])
    return {
        "status": "selected",
        "selected_threshold": float(chosen["threshold"]),
        "meets_min_onset_gain": bool(onset >= min_required_onset),
        "selected_onset_sensitivity": onset,
        "selected_false_alarm_ratio": float(chosen["false_alarm_ratio"]),
        "selected_false_alerts": int(chosen["false_alerts"]),
        "selected_emitted_alerts": int(chosen["emitted_alerts"]),
        "feasible_threshold_count": int(feasible.shape[0]),
    }


def _oracle_event_counts(
    y_true: pd.Series,
    prediction_label: pd.Series,
    event_context: pd.DataFrame,
) -> dict[str, Any]:
    """Independent event-count oracle for denominator and rule checks."""
    y = y_true.astype("Int64")
    labels = prediction_label.astype("Int64")
    onset = event_context["actual_onset"].fillna(False).astype(bool)

    alerts = labels.eq(1)
    false_alerts = int((alerts & y.eq(0)).sum())
    emitted = int(alerts.sum())
    false_alarm_ratio = float(false_alerts / emitted) if emitted else None

    real_onsets = int(onset.sum())
    detected = int((alerts & onset).sum())
    onset_sensitivity = float(detected / real_onsets) if real_onsets else None

    return {
        "false_alerts": false_alerts,
        "emitted_alerts": emitted,
        "false_alarm_ratio": false_alarm_ratio,
        "detected_onsets": detected,
        "real_onsets": real_onsets,
        "onset_sensitivity": onset_sensitivity,
    }


def _select_configuration_from_hyperparameter_role(
    *,
    candidate: str,
    search: dict[str, Any],
    hp_rows: pd.DataFrame,
    y_column: str,
    target_column: str,
    stage4_policy: dict[str, Any],
    train_feature_count: int,
) -> tuple[str, dict[str, Any], pd.DataFrame]:
    """Select one configuration from hyperparameter-selection role rows only."""
    candidate_meta = {row["id"]: row for row in search["candidates"]}
    score_rows: list[dict[str, Any]] = []
    for configuration_id, frame in hp_rows.groupby("configuration_id", dropna=False):
        ap = average_precision_metric(frame[y_column], frame["prediction_probability"])["value"]
        brier = brier_metric(frame[y_column], frame["prediction_probability"])["value"]
        if ap is None or brier is None:
            raise ModelEvaluationError(
                f"Hyperparameter-selection AP/Brier unavailable for {candidate} {configuration_id}"
            )
        meta = candidate_meta.get(str(configuration_id))
        if not isinstance(meta, dict):
            raise ModelEvaluationError(
                f"Missing configuration metadata in search: {configuration_id}"
            )
        simplicity_tuple = meta.get("simplicity")
        if not isinstance(simplicity_tuple, list):
            raise ModelEvaluationError("Missing simplicity tuple in Stage4 search evidence")
        score_rows.append(
            {
                "configuration_id": str(configuration_id),
                "ap": float(ap),
                "brier": float(brier),
                "simplicity": simplicity_tuple,
                "rows": int(frame.shape[0]),
                "months": int(frame[target_column].nunique()),
            }
        )

    if not score_rows:
        raise ModelEvaluationError("No hyperparameter-selection rows were available")

    tolerance = float(stage4_policy["numeric_ties"]["absolute_tolerance"])
    table = pd.DataFrame(score_rows)
    best_ap = float(table["ap"].max())
    ap_tied = table[table["ap"] >= best_ap - tolerance].copy()
    best_brier = float(ap_tied["brier"].min())
    brier_tied = ap_tied[ap_tied["brier"] <= best_brier + tolerance].copy()

    if brier_tied.empty:
        raise ModelEvaluationError("No configuration survived AP/Brier tie filtering")

    simplicity_keys = [tuple(value) for value in brier_tied["simplicity"]]
    best_simplicity = min(simplicity_keys)
    final_tied = brier_tied[
        brier_tied["simplicity"].map(lambda value: tuple(value) == best_simplicity)
    ].copy()
    selected_id = sorted(final_tied["configuration_id"].astype(str).to_list())[0]
    selected_parameters = candidate_meta[selected_id]["parameters"]

    selected_trace = table.copy()
    selected_trace["selected"] = selected_trace["configuration_id"].eq(selected_id)
    selected_trace["selection_policy"] = (
        "AP(desc), Brier(asc), simplicity(within-family), canonical id for residual ties"
    )
    selected_trace["train_feature_count"] = train_feature_count
    selected_trace["candidate"] = candidate
    return selected_id, selected_parameters, selected_trace


def _to_bool(value: Any) -> bool:
    """Normalize booleans loaded from CSV payloads."""
    if isinstance(value, bool):
        return value
    if value is None or pd.isna(value):
        return False
    return str(value).strip().lower() == "true"


ROLE_CALENDAR_TO_SPLIT: tuple[tuple[str, str], ...] = (
    ("hyperparameter_selection_targets", "hyperparameter_selection"),
    ("calibration_fit_targets", "calibration_fit"),
    ("calibration_selection_targets", "calibration_selection"),
    ("threshold_selection_targets", "threshold_selection"),
)

ROLE_SEQUENCE: tuple[str, ...] = tuple(split for _, split in ROLE_CALENDAR_TO_SPLIT)
