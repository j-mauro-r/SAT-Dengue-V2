"""Verified development-only predictions and shared retrospective metric evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.evaluation_metrics import evaluate_comparison_metrics
from scripts.model_evaluation.contract import ModelEvaluationConfig
from scripts.model_evaluation.pipeline import build_model_evaluation
from scripts.model_training.contract import ModelTrainingConfig
from scripts.model_training.events import load_event_context
from scripts.model_training.loading import load_temporal_source, load_window_dataset
from scripts.model_training.references import persistence_reference

from .input_validation import verify_equivalent_input
from .policy import require_development


def load_comparison(
    root: Path,
) -> tuple[Path, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Verify native inference and rebuild development metrics from identical keys.

    Args:
        root: Repository root containing local trusted input artifacts.

    Returns:
        Verified input, metrics, linked predictions and audited-equivalence receipt.

    Raises:
        ValueError: For substituted inputs, cohorts or disagreement with saved metrics.
    """
    result = build_model_evaluation(ModelEvaluationConfig(root), verify_only=True)
    bundle = result.bundle
    contract = json.loads(
        (root / "docs/product/stage-5/model_evaluation_contract_v1.json").read_text()
    )
    approved = root / "artifacts/model_evaluation" / contract["approved_input_bundle"]
    input_receipt = verify_equivalent_input(bundle, approved)
    frame = pd.read_csv(bundle / "posterior_predictions.csv", dtype={"municipality_code": "string"})
    require_development(frame.target_period)
    saved = pd.read_csv(bundle / "posterior_metrics.csv")
    config = ModelTrainingConfig(root)
    source = load_temporal_source(config)
    records, linked = [], []
    for window_id in sorted(frame.window_id.unique()):
        dataset = load_window_dataset(source, window_id)
        index = dataset.validation_index.reset_index(drop=True)
        context = load_event_context(config, source, index, target_column=dataset.target_column)
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
                input_bundle=str(bundle.relative_to(root)),
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
    for row in overall[overall.metric.ne("auroc")].itertuples():
        matches = saved[
            saved.candidate.eq(row.candidate)
            & saved.window_id.eq(row.window_id)
            & saved.metric.eq(row.metric)
        ]
        if matches.empty:
            raise ValueError("Saved metric missing")
        for field in ("value", "numerator", "denominator"):
            expected = matches[field].to_numpy(dtype=float)
            actual = float(getattr(row, field))
            if not np.allclose(expected, actual, rtol=0, atol=1e-12, equal_nan=True):
                raise ValueError(
                    f"Saved metric mismatch {row.candidate}/{row.window_id}/{row.metric}/{field}"
                )
    return (
        bundle,
        overall,
        metrics[~metrics.scope.eq("overall")].reset_index(drop=True),
        pd.concat(linked, ignore_index=True),
        input_receipt,
    )
