"""Evaluación pura de objetivos variables sobre X, cohortes y referencia constantes."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp01 import Calibrate, Fit, digest, prepare
from sat_dengue.experiments.exp02_labels import HISTORY_YEARS, records
from sat_dengue.experiments.onset import KEYS, labels, partitions, predictor_projection
from sat_dengue.experiments.onset_evaluation import (
    calibration_summary,
    episode_metrics,
    matched_thresholds,
    paired_block_interval,
    stratified_episode_metrics,
)
from sat_dengue.metrics import average_precision_metric, brier_metric


def common_partitions(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    variants: dict[int, dict[str, Any]],
    design: dict[str, Any],
    horizon: int,
    window: dict[str, Any],
) -> tuple[dict[str, pd.DataFrame], dict[str, Any]]:
    """Fija elegibilidad y X de cinco años; intersecta disponibilidad, nunca valores Y."""
    cohort = prepare(panel, contract, horizon)
    targets = []
    for history in HISTORY_YEARS:
        target = f"onset_{history}"
        targets.append(target)
        outcome = labels(variants[history]["states"], horizon)[KEYS + ["onset_target"]]
        cohort = cohort.merge(
            outcome.rename(columns={"onset_target": target}), on=KEYS, validate="one_to_one"
        )
    parts = partitions(cohort, window)
    selected, coverage = {}, {}
    for role, frame in parts.items():
        available = frame[targets + design["predictors"]].notna().all(axis=1)
        selected[role] = frame.loc[available].copy()
        coverage[role] = {
            **frame.attrs.get("coverage", {}),
            "operational_rows": len(frame),
            "common_rows": int(available.sum()),
            "unavailable_rows": int((~available).sum()),
        }
    return selected, coverage


def probability_summary(frame: pd.DataFrame, scores: np.ndarray, history: int) -> dict[str, Any]:
    truth = frame[f"onset_{history}"].astype(int)
    prediction = pd.Series(scores, index=frame.index)
    return {
        "average_precision": average_precision_metric(truth, prediction)["value"],
        "brier": brier_metric(truth, prediction)["value"],
        "calibration": calibration_summary(truth.to_numpy(), scores),
    }


def evaluate_predictive(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    variants: dict[int, dict[str, Any]],
    design: dict[str, Any],
    *,
    fit: Fit,
    calibrate: Calibrate,
    synthetic: bool = False,
) -> dict[str, Any]:
    """Ajustes independientes; conserva probabilidades para exportación sin reentrenar."""
    children: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    fit_count = 0
    columns = design["predictors"]
    availability = dict.fromkeys(columns, design["predictor_availability_offset_months"])
    for horizon in design["horizons"]:
        for window in design["windows"]:
            parts, coverage = common_partitions(panel, contract, variants, design, horizon, window)
            reason = None
            if any(frame.empty for frame in parts.values()):
                reason = "empty_common_role"
            elif any(
                parts[role][f"onset_{h}"].nunique() != 2
                for role in ("train", "calibration")
                for h in HISTORY_YEARS
            ):
                reason = "single_class_training_or_calibration"
            role_hashes = {
                role: digest(frame[KEYS + ["target_month"] + columns].to_json(orient="split"))
                for role, frame in parts.items()
            }
            key_hash = digest(records(parts["evaluation"][KEYS + ["target_month"]]))
            for family, parameters in design["families"].items():
                dimensions = {
                    "layer": "predictive",
                    "family": family,
                    "horizon": horizon,
                    "window": window["id"],
                    "evidence_type": window["evidence_type"],
                    "coverage": coverage,
                    "cohort_sha256": key_hash,
                    "role_sha256": role_hashes,
                }
                if reason:
                    for history in HISTORY_YEARS:
                        children.append(
                            {
                                **dimensions,
                                "history_years": history,
                                "status": "not_evaluable",
                                "reason": reason,
                                "own_definition": None,
                                "fixed_anchor": None,
                                "frontier": [],
                            }
                        )
                    continue
                scores: dict[int, dict[str, np.ndarray]] = {}
                for history in HISTORY_YEARS:
                    matrices = {
                        role: predictor_projection(frame[columns], columns, availability)
                        for role, frame in parts.items()
                    }
                    model = fit(
                        family,
                        matrices["train"],
                        parts["train"][f"onset_{history}"].copy(),
                        dict(parameters),
                        design["seed"],
                    )
                    transformation = calibrate(
                        model.predict(matrices["calibration"]),
                        parts["calibration"][f"onset_{history}"].copy(),
                        design["seed"],
                    )
                    fit_count += 1
                    scores[history] = {
                        role: transformation(model.predict(matrices[role])).to_numpy(dtype=float)
                        for role in ("selection", "evaluation")
                    }
                    for role in ("selection", "evaluation"):
                        values = scores[history][role]
                        if (
                            len(values) != len(parts[role])
                            or not np.isfinite(values).all()
                            or ((values < 0) | (values > 1)).any()
                        ):
                            raise ValueError(
                                "Probabilidades incompletas o inválidas; no cambiar denominadores"
                            )
                        exported = (
                            parts[role][KEYS + ["target_month", "onset_5", f"onset_{history}"]]
                            .loc[:, lambda f: ~f.columns.duplicated()]
                            .copy()
                        )
                        exported["probability"] = values
                        predictions.extend(
                            {
                                **r,
                                "history_years": history,
                                "family": family,
                                "horizon": horizon,
                                "window": window["id"],
                                "role": role,
                            }
                            for r in records(exported)
                        )
                anchor = parts["evaluation"].copy()
                anchor["onset_target"] = anchor.onset_5
                selection_truth = parts["selection"].onset_5.to_numpy(dtype=int)
                frontiers: dict[int, list[dict[str, Any]]] = {h: [] for h in HISTORY_YEARS}
                for budget in range(int((selection_truth == 0).sum()) + 1):
                    thresholds = {
                        h: matched_thresholds(
                            selection_truth, scores[5]["selection"], scores[h]["selection"], budget
                        )["onset"]
                        for h in HISTORY_YEARS
                    }
                    alerts = {
                        h: np.zeros(len(anchor), dtype=bool)
                        if thresholds[h] is None
                        else scores[h]["evaluation"] >= thresholds[h]
                        for h in HISTORY_YEARS
                    }
                    for history in HISTORY_YEARS:
                        own = anchor.copy()
                        own["onset_target"] = own[f"onset_{history}"]
                        fixed_metrics = episode_metrics(anchor, alerts[history])
                        base_metrics = episode_metrics(anchor, alerts[5])
                        gain = (
                            None
                            if fixed_metrics["onset_sensitivity"] is None
                            else fixed_metrics["onset_sensitivity"]
                            - base_metrics["onset_sensitivity"]
                        )
                        frontiers[history].append(
                            {
                                "selection_false_alert_budget": budget,
                                "threshold": thresholds[history],
                                "own_definition": episode_metrics(own, alerts[history]),
                                "fixed_anchor": fixed_metrics,
                                "paired_anchor_sensitivity_difference": gain,
                                "paired_interval": paired_block_interval(
                                    anchor,
                                    alerts[5],
                                    alerts[history],
                                    seed=design["seed"],
                                    repeats=1000,
                                ),
                                "by_group": stratified_episode_metrics(anchor, alerts[history]),
                            }
                        )
                for history in HISTORY_YEARS:
                    children.append(
                        {
                            **dimensions,
                            "history_years": history,
                            "status": "evaluable",
                            "reason": None,
                            "own_definition": probability_summary(
                                anchor, scores[history]["evaluation"], history
                            ),
                            "fixed_anchor": probability_summary(
                                anchor, scores[history]["evaluation"], 5
                            ),
                            "frontier": frontiers[history],
                        }
                    )
    return {
        "children": children,
        "predictions": predictions,
        "real_model_fits": 0 if synthetic else fit_count,
        "real_preparer_refits": 0 if synthetic else fit_count,
        "calibrator_fits": 0 if synthetic else fit_count,
        "synthetic_interface_fits": fit_count if synthetic else 0,
        "interpretation": "changed_y_is_not_predictive_improvement",
    }
