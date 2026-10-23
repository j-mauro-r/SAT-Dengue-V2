"""Verified development-only predictions and shared retrospective metric evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.legacy_evaluation.model_evaluation.contract import ModelEvaluationConfig
from sat_dengue.datasets.legacy_evaluation.model_evaluation.pipeline import build_model_evaluation
from scripts.model_training.contract import ModelTrainingConfig
from scripts.model_training.events import load_event_context
from scripts.model_training.loading import load_temporal_source, load_window_dataset

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
    from sat_dengue.model_assessment.workflow import assess_development

    windows = {w: load_window_dataset(source, w) for w in sorted(frame.window_id.unique())}
    contexts = {
        w: load_event_context(
            config, source, d.validation_index.reset_index(drop=True), target_column=d.target_column
        )
        for w, d in windows.items()
    }
    overall, breakdown, linked = assess_development(
        windows, contexts, frame, str(bundle.relative_to(root))
    )
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
        breakdown,
        linked,
        input_receipt,
    )
