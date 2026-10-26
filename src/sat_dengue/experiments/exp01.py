"""EXP01 paired scientific functions and generated-data interface probes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes
from sat_dengue.data.consolidation import compute_current_endemic_channel
from sat_dengue.training_preparation.features import derive_features

from .onset import KEYS, labels, partitions, predictor_projection, validate_keys
from .onset_evaluation import (
    calibration_summary,
    episode_metrics,
    matched_thresholds,
    paired_block_interval,
    stratified_episode_metrics,
)

PROTOCOL = Path("docs/product/experiments/EXP01_direct_onset/protocol.json")
SYNTHETIC_EVIDENCE = "synthetic_interface_probe_not_scientific_evidence"


class Predictor(Protocol):
    def predict(self, X: pd.DataFrame) -> pd.Series: ...


Fit = Callable[[str, pd.DataFrame, pd.Series, dict[str, Any], int], Predictor]
Calibrate = Callable[[pd.Series, pd.Series, int], Callable[[pd.Series], pd.Series]]


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_protocol() -> dict[str, Any]:
    from sat_dengue.tracking.experiments import resolve_experiment

    tags = resolve_experiment("EXP01")
    protocol = json.loads(PROTOCOL.read_text())
    if digest(protocol) != tags["protocol_sha256"]:
        raise ValueError("EXP01 protocol changed")
    return protocol


def prepare(panel: pd.DataFrame, contract: dict[str, Any], horizon: int) -> pd.DataFrame:
    """Rebuild channel/features before the T-only eligibility mask.

    Provided future-label and percentile columns are never consumed. The native
    channel uses only five prior same-month observations; no fold sees a learned
    transform before the training adapter is called on its own training rows.
    """
    validate_keys(panel)
    if panel.year_month.ge("2025-01").any():
        raise ValueError("Consumed 2025 is excluded from EXP01 input")
    raw = [c for c in contract["roles"]["predictors"] if c != "zona_canal_t"]
    source = panel[KEYS + raw].sort_values(KEYS).reset_index(drop=True)
    channel, _, _ = compute_current_endemic_channel(source)
    states = channel[KEYS].copy()
    states["excess"] = channel.zona_canal_t.map(
        {"EXITO": 0, "SEGURIDAD": 0, "ALERTA": 0, "EXCESO": 1}
    ).astype("Int64")
    outcomes = labels(states, horizon)
    features = derive_features(channel, contract)
    features["municipality_code_feature"] = features.municipality_code
    return outcomes.merge(features, on=KEYS, validate="one_to_one")


def native_fit(
    family: str, X: pd.DataFrame, y: pd.Series, parameters: dict[str, Any], seed: int
) -> Predictor:
    """Future authorized fits reuse the existing three model/preparer adapters."""
    from sat_dengue.model_training.candidate_families import fit_model

    X = X.rename(columns={"municipality_code_feature": "municipality_code"})
    model = fit_model(family, X, y, parameters, seed=seed, threads=1)

    class Adapter:
        def predict(self, X: pd.DataFrame) -> pd.Series:
            return model.predict(
                X.rename(columns={"municipality_code_feature": "municipality_code"})
            )

    return Adapter()


def native_calibration(
    scores: pd.Series, truth: pd.Series, seed: int
) -> Callable[[pd.Series], pd.Series]:
    from sat_dengue.model_evaluation.calibration import _apply_sigmoid, _fit_sigmoid

    if truth.nunique() != 2:
        raise ValueError("Sigmoid calibration requires both classes; no fallback")
    fitted = _fit_sigmoid(scores, truth, seed)
    return lambda values: _apply_sigmoid(values, fitted)


def execute_paired(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    design: dict[str, Any],
    *,
    fit: Fit,
    calibrate: Calibrate,
    synthetic: bool = False,
) -> dict[str, Any]:
    """Evaluate frozen paired objectives through injected adapters; no I/O.

    Both arms receive independently copied matrices from one common role/cohort.
    Orchestration owns real execution authorization and persistence.
    """
    from sat_dengue.metrics import auroc_metric, average_precision_metric, brier_metric
    from sat_dengue.model_training.references import persistence_reference

    columns = design["predictors"]
    seed = design["seed"]
    offset = design["predictor_availability_offset_months"]
    if offset != 0:
        raise ValueError("Frozen EXP01 predictors must be available by close of origin T")
    availability = dict.fromkeys(columns, offset)
    children = []
    for horizon in (1, 2):
        cohort = prepare(panel, contract, horizon)
        for window in design["windows"]:
            parts = partitions(cohort, window)
            for family, parameters in design["families"].items():
                scores: dict[str, dict[str, np.ndarray]] = {}
                for objective in ("excess", "onset"):
                    target = objective + "_target"
                    # Both arms use the SAME retrospective evaluability intersection.
                    selected = {
                        role: frame.loc[
                            frame.onset_target.notna() & frame.excess_target.notna()
                        ].copy()
                        for role, frame in parts.items()
                    }
                    if any(frame.empty for frame in selected.values()):
                        raise ValueError("Empty temporal role; experiment is not evaluable")
                    matrices = {
                        role: predictor_projection(frame[columns], columns, availability)
                        for role, frame in selected.items()
                    }
                    model = fit(
                        family, matrices["train"], selected["train"][target], parameters, seed
                    )
                    transform = calibrate(
                        model.predict(matrices["calibration"]),
                        selected["calibration"][target],
                        seed,
                    )
                    scores[objective] = {
                        role: transform(model.predict(matrices[role])).to_numpy(dtype=float)
                        for role in ("selection", "evaluation")
                    }
                reference = persistence_reference(selected["evaluation"], horizon=horizon)
                if not reference.state_evaluable.all():
                    raise ValueError("Persistence reference cannot drop paired evaluation rows")
                reference_alerts = reference.prediction_label.to_numpy(dtype=bool)
                persistence = {
                    "reference": "persistence",
                    "prediction_kind": "deterministic",
                    "formula": reference.reference_formula.iloc[0],
                    "calibration": "not_applicable_deterministic_reference",
                    "brier": None,
                    **episode_metrics(selected["evaluation"], reference_alerts),
                    "by_group": stratified_episode_metrics(
                        selected["evaluation"], reference_alerts
                    ),
                    "secondary_guardrail": "unavailable_when_reference_has_no_alerts",
                }
                paired_frontier: list[dict[str, Any]] = []
                selection_truth = selected["selection"].onset_target.to_numpy(dtype=int)
                for budget in range(int((selection_truth == 0).sum()) + 1):
                    thresholds = matched_thresholds(
                        selection_truth,
                        scores["excess"]["selection"],
                        scores["onset"]["selection"],
                        budget,
                    )
                    policies = {}
                    for objective in ("excess", "onset"):
                        threshold = thresholds[objective]
                        probabilities = scores[objective]["evaluation"]
                        policies[objective] = (
                            np.zeros(len(probabilities), dtype=bool)
                            if threshold is None
                            else probabilities >= threshold
                        )
                    excess_arm = episode_metrics(selected["evaluation"], policies["excess"])
                    onset_arm = episode_metrics(selected["evaluation"], policies["onset"])
                    difference = None
                    if (
                        excess_arm["onset_sensitivity"] is not None
                        and onset_arm["onset_sensitivity"] is not None
                    ):
                        difference = float(
                            onset_arm["onset_sensitivity"] - excess_arm["onset_sensitivity"]
                        )
                    paired_frontier.append(
                        {
                            "selection_false_alert_budget": budget,
                            "thresholds": thresholds,
                            "paired_onset_sensitivity_difference": difference,
                            "paired_interval": paired_block_interval(
                                selected["evaluation"],
                                policies["excess"],
                                policies["onset"],
                                seed=seed,
                                repeats=1000,
                            ),
                        }
                    )
                for objective in ("excess", "onset"):
                    evaluation = selected["evaluation"]
                    prediction = pd.Series(scores[objective]["evaluation"], index=evaluation.index)
                    outcomes = evaluation[objective + "_target"]
                    frontier = []
                    for paired in paired_frontier:
                        budget = paired["selection_false_alert_budget"]
                        threshold = paired["thresholds"][objective]
                        alerts = (
                            np.zeros(len(prediction), dtype=bool)
                            if threshold is None
                            else prediction.to_numpy() >= threshold
                        )
                        metric = episode_metrics(evaluation, alerts)
                        excess_y = evaluation.excess_target.to_numpy(dtype=int)
                        metric["excess_false_alarm_ratio"] = (
                            float((alerts & (excess_y == 0)).sum() / alerts.sum())
                            if alerts.any()
                            else None
                        )
                        metric["by_group"] = stratified_episode_metrics(evaluation, alerts)
                        frontier.append(
                            {
                                "selection_false_alert_budget": budget,
                                "threshold": threshold,
                                "paired_onset_sensitivity_difference": paired[
                                    "paired_onset_sensitivity_difference"
                                ],
                                "paired_interval": paired["paired_interval"],
                                **metric,
                            }
                        )
                    children.append(
                        {
                            "objective": objective,
                            "family": family,
                            "horizon": horizon,
                            "window": window["id"],
                            "cohort": "non_excess_at_t",
                            "seed": seed,
                            "evidence_type": (
                                "synthetic_interface_probe"
                                if synthetic
                                else window["evidence_type"]
                            ),
                            "average_precision": average_precision_metric(outcomes, prediction)[
                                "value"
                            ],
                            "auroc": auroc_metric(outcomes, prediction)["value"],
                            "brier": brier_metric(outcomes, prediction)["value"],
                            "calibration": calibration_summary(
                                outcomes.fillna(0).to_numpy(dtype=int),
                                prediction.to_numpy(dtype=float),
                            ),
                            "frontier": frontier,
                            "cohort_sha256": digest(
                                evaluation[KEYS + ["target_month"]].to_dict("records")
                            ),
                            "predictors_sha256": digest(columns),
                            "role_sha256": {
                                role: digest(
                                    frame[KEYS + ["target_month"] + columns].to_json(
                                        orient="split", date_format="iso"
                                    )
                                )
                                for role, frame in selected.items()
                            },
                            "operational_reference": persistence,
                            "coverage": {
                                role: {
                                    **parts[role].attrs["coverage"],
                                    "operational_rows": len(parts[role]),
                                    "evaluable_rows": len(frame),
                                }
                                for role, frame in selected.items()
                            },
                        }
                    )
    count = len(children)
    return {
        "schema": "exp01-paired-result-v1",
        "experiment_id": "EXP01",
        "synthetic": synthetic,
        "real_model_fits": 0 if synthetic else count,
        "real_preparer_refits": 0 if synthetic else count,
        "calibrator_fits": 0 if synthetic else count,
        "synthetic_interface_fits": count if synthetic else 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "children": children,
    }


def _execute_synthetic(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    design: dict[str, Any],
    *,
    fit: Fit,
    calibrate: Calibrate,
) -> dict[str, Any]:
    """Keep native fitters unreachable from the public synthetic route."""
    if fit is not synthetic_fit:
        raise ValueError("Synthetic execution accepts only the fixed synthetic fitter")
    return execute_paired(panel, contract, design, fit=fit, calibrate=calibrate, synthetic=True)


class SyntheticPredictor:
    """Seeded deterministic interface probe; never represents a scientific model."""

    def __init__(self, X: pd.DataFrame, y: pd.Series, seed: int) -> None:
        self.offset = float(y.mean())
        self.weight = float(np.random.default_rng(seed).uniform(0.001, 0.002))

    def predict(self, X: pd.DataFrame) -> pd.Series:
        return (self.offset + X.dengue_notifications_count.astype(float) * self.weight).clip(0, 1)


def synthetic_fit(
    family: str, X: pd.DataFrame, y: pd.Series, parameters: dict[str, Any], seed: int
) -> Predictor:
    """A fixed generated-data adapter; production estimators are unreachable here."""
    return SyntheticPredictor(X, y, seed)


def synthetic_inputs() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    """Generate the source-free interface fixture, never reading private data."""
    protocol = load_protocol()
    contract = json.loads(
        Path("docs/product/stage-3/training_preparation_contract_v1.json").read_text()
    )
    design = dict(protocol["design"])
    design["windows"] = [
        {
            "id": "synthetic_window_1",
            "train": ["1996-01", "2002-12"],
            "calibration": ["2003-01", "2003-12"],
            "selection": ["2004-01", "2004-12"],
            "evaluation": ["2005-01", "2005-12"],
            "evidence_type": "synthetic",
        },
        {
            "id": "synthetic_window_2",
            "train": ["1996-01", "2004-12"],
            "calibration": ["2005-01", "2005-12"],
            "selection": ["2006-01", "2006-12"],
            "evaluation": ["2007-01", "2007-12"],
            "evidence_type": "synthetic",
        },
        {
            "id": "synthetic_window_3",
            "train": ["1996-01", "2006-12"],
            "calibration": ["2007-01", "2007-12"],
            "selection": ["2008-01", "2008-12"],
            "evaluation": ["2009-01", "2009-12"],
            "evidence_type": "synthetic",
        },
    ]
    rng = np.random.default_rng(design["seed"])
    rows = []
    for municipality in ("50001", "73001"):
        for month in pd.period_range("1990-01", "2009-12", freq="M"):
            row: dict[str, Any] = {"municipality_code": municipality, "year_month": str(month)}
            for column in contract["roles"]["predictors"]:
                if column != "zona_canal_t":
                    row[column] = float(rng.integers(0, 100))
            rows.append(row)
    return pd.DataFrame(rows), contract, design


def synthetic_run() -> dict[str, Any]:
    protocol = load_protocol()
    panel, contract, design = synthetic_inputs()
    receipt = _execute_synthetic(
        panel,
        contract,
        design,
        fit=synthetic_fit,
        calibrate=lambda scores, truth, seed: lambda values: values,
    )
    children = [
        {
            key: child[key]
            for key in (
                "objective",
                "family",
                "horizon",
                "window",
                "cohort",
                "seed",
                "evidence_type",
            )
        }
        for child in receipt["children"]
    ]
    return {
        "schema": "exp01-synthetic-probe-v1",
        "experiment_id": "EXP01",
        "experiment_slug": "direct_episode_onset",
        "hypothesis_id": "EXP01-H1",
        "protocol_version": protocol["version"],
        "protocol_sha256": digest(protocol),
        "data_sha256": digest(panel.to_dict("records")),
        "configuration_sha256": digest(design),
        "kind": SYNTHETIC_EVIDENCE,
        "evidence_type": "synthetic_interface_probe",
        "pipeline": "exp01_synthetic",
        "profile": "exp01_synthetic",
        "cohort": "generated_fixture_only",
        "seed": design["seed"],
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "calibrator_fits": 0,
        "hyperparameter_search": 0,
        "threshold_selection": 0,
        "synthetic_interface_fits": receipt["synthetic_interface_fits"],
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "children": children,
    }
