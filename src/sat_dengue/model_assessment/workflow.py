"""Complete development metric cohorts from supplied frames; no reading or selection."""

from __future__ import annotations

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.metrics import evaluate_comparison_metrics
from sat_dengue.model_training.loading import WindowDataset
from sat_dengue.model_training.references import persistence_reference

from .policy import require_development


def assess_development(
    windows: dict[str, WindowDataset],
    contexts: dict[str, pd.DataFrame],
    frame: pd.DataFrame,
    input_bundle: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Retain exact ordered cohorts, all subgroup denominators and equal window support."""
    require_development(frame.target_period)
    records, linked = [], []
    for window_id in sorted(frame.window_id.unique()):
        dataset = windows[window_id]
        index = dataset.validation_index.reset_index(drop=True)
        context = contexts[window_id]
        y = dataset.validation_y[dataset.y_column].reset_index(drop=True)
        candidates = frame[frame.window_id.eq(window_id)]
        expected_keys = index[["municipality_code", "year_month", dataset.target_column]].astype(
            "string"
        )
        expected_keys.columns = ["municipality_code", "origin_period", "target_period"]
        for candidate in ["gam", "lightgbm", "xgboost", "persistence"]:
            if candidate == "persistence":
                prediction = persistence_reference(
                    dataset.validation_X.reset_index(drop=True), horizon=dataset.horizon
                )
                rows = expected_keys.copy()
                rows["model_artifact"] = "deterministic_zona_canal_t"
                rows["preparer_artifact"] = "none"
                rows["calibration_choice"] = "none"
                rows["selected_threshold"] = pd.NA
            else:
                rows = candidates[candidates.candidate.eq(candidate)].reset_index(drop=True)
                if not rows[list(expected_keys)].astype("string").equals(expected_keys):
                    raise ValueError(f"Cohort/order mismatch: {candidate}/{window_id}")
                prediction = pd.DataFrame(
                    {
                        "prediction_kind": "probabilistic",
                        "prediction_score": rows.probability_selected,
                        "prediction_probability": rows.probability_selected,
                        "prediction_label": rows.prediction_label,
                    }
                )
            rows = rows.assign(
                candidate=candidate,
                window_id=window_id,
                horizon=dataset.horizon,
                y_true=y,
                prediction_score=prediction.prediction_score,
                prediction_probability=prediction.prediction_probability,
                prediction_label=prediction.prediction_label,
                input_bundle=input_bundle,
                calibrator_artifact="calibrators.json" if candidate != "persistence" else "none",
                threshold_artifact="threshold_selection.csv"
                if candidate != "persistence"
                else "none",
            )
            linked.append(rows)
            groups = [("overall", "all", index.index)]
            for scope, codes in (
                ("period", rows.target_period),
                ("department", rows.municipality_code.str[:2]),
                ("municipality", rows.municipality_code),
            ):
                groups.extend(
                    (scope, str(code), members.index) for code, members in codes.groupby(codes)
                )
            for scope, group_id, positions in groups:
                computed = evaluate_comparison_metrics(
                    candidate,
                    y.loc[positions],
                    prediction.loc[positions],
                    index.loc[positions],
                    target_column=dataset.target_column,
                    threshold_policy_declared=True,
                    event_context=context.loc[positions],
                )
                for record in computed:
                    record.update(
                        candidate=candidate,
                        horizon=dataset.horizon,
                        window_id=window_id,
                        scope=scope,
                        group_id=group_id,
                        rows=len(positions),
                        municipalities=index.loc[positions].municipality_code.nunique(),
                    )
                    records.append(record)
    metrics = pd.DataFrame(records)
    overall = metrics[metrics.scope.eq("overall")].reset_index(drop=True)
    return (
        overall,
        metrics[~metrics.scope.eq("overall")].reset_index(drop=True),
        pd.concat(linked, ignore_index=True),
    )
