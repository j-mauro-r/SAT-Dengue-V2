"""Pure ten-arm onset ablation using frozen EXP01 science; no I/O during fitting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01
from sat_dengue.experiments.onset import KEYS, predictor_projection
from sat_dengue.experiments.onset_evaluation import (
    calibration_summary,
    episode_metrics,
    matched_thresholds,
    paired_block_interval,
    stratified_episode_metrics,
)

PROTOCOL = Path("docs/product/experiments/EXP03_feature_ablation/protocol.json")
VARIANTS = (
    "baseline_history_season",
    "baseline_plus_target_thresholds",
    "baseline_plus_recent_channel_state",
    "baseline_plus_sir",
    "baseline_plus_climate",
    "baseline_plus_complete_channel",
    "full",
    "full_without_target_thresholds",
    "full_without_recent_channel_state",
    "full_without_sir",
)


def load_protocol() -> dict[str, Any]:
    from sat_dengue.experiments.exp03_features import validate_design
    from sat_dengue.tracking.experiments import resolve_experiment

    p = json.loads(PROTOCOL.read_text())
    source = exp01.load_protocol()
    if exp01.digest(p) != resolve_experiment("EXP03")["protocol_sha256"]:
        raise ValueError("EXP03 protocol changed")
    if exp01.digest(source) != p["reproducibility"]["exp01_protocol_sha256"]:
        raise ValueError("EXP01 scientific interface changed")
    for key in (
        "families",
        "seed",
        "threads",
        "calibration",
        "predictor_availability_offset_months",
    ):
        if p["design"][key] != source["design"][key]:
            raise ValueError("EXP03 differs from EXP01: " + key)
    validate_design(p["design"])
    if set(p["design"]["variants"]) != set(VARIANTS):
        raise ValueError("Canonical variants changed")
    return p


def variant_names() -> tuple[str, ...]:
    return tuple(load_protocol()["design"]["variants"])


def native_fit(
    family: str, X: pd.DataFrame, y: pd.Series, parameters: dict[str, Any], seed: int
) -> exp01.Predictor:
    """Explicit Stage4 exclusions, never restore excluded observed values."""
    from sat_dengue.model_training.candidate_families import fit_model

    all_names = load_protocol()["design"]["predictors"]
    missing = [n for n in all_names if n not in X]

    def envelope(frame: pd.DataFrame) -> pd.DataFrame:
        # Schema slots only; existing projection removes these BEFORE preparation.
        return frame.reindex(columns=all_names).rename(
            columns={"municipality_code_feature": "municipality_code"}
        )

    excluded = ["municipality_code" if n == "municipality_code_feature" else n for n in missing]
    model = fit_model(family, envelope(X), y, parameters, seed=seed, threads=1, excluded=excluded)

    class Adapter:
        def predict(self, frame: pd.DataFrame) -> pd.Series:
            return model.predict(envelope(frame))

    return Adapter()


def execute(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    design: dict[str, Any],
    *,
    fit: exp01.Fit,
    calibrate: exp01.Calibrate,
    synthetic: bool = False,
) -> dict[str, Any]:
    """Exactly one fit per evaluable cell, common rows fixed BEFORE subsetting X."""
    from sat_dengue.experiments.exp03_contrasts import evaluate
    from sat_dengue.experiments.exp03_features import (
        cohorts,
        validate_design,
    )
    from sat_dengue.experiments.exp03_features import (
        coverage as operational_summary,
    )
    from sat_dengue.metrics import auroc_metric, average_precision_metric, brier_metric

    expected = validate_design(design)
    prepared = cohorts(panel, contract, design)
    cache = {}
    operational_coverage = []
    full = design["predictors"]
    variants = design["variants"]
    if variants["full"] != full:
        raise ValueError("Noncanonical variants")
    if synthetic and fit is not exp01.synthetic_fit:
        raise ValueError("Synthetic route cannot call production estimators")
    children: list[dict[str, Any]] = []
    fits = 0
    calibrations = 0
    for horizon in design["horizons"]:
        for window in design["windows"]:
            parts, selected = prepared[horizon, window["id"]]
            for name, cols in variants.items():
                operational_coverage.append(
                    {
                        "variant": name,
                        "horizon": horizon,
                        "window": window["id"],
                        "analysis": "secondary_coverage_not_paired_prediction",
                        **operational_summary(parts["evaluation"], cols, full),
                    }
                )
            hashes = {
                role: exp01.digest(
                    f[KEYS + ["target_month", "onset_target"]].to_json(orient="split")
                )
                for role, f in selected.items()
            }
            coverage = {
                role: {
                    **parts[role].attrs["coverage"],
                    "operational_rows": len(parts[role]),
                    "evaluable_rows": len(f),
                }
                for role, f in selected.items()
            }
            for family, parameters in design["families"].items():
                cells: dict[str, Any] = {}
                for variant in variants:
                    cols = variants[variant]
                    child = {
                        "variant": variant,
                        "cell_id": exp01.digest([variant, family, horizon, window["id"]]),
                        "objective": "onset",
                        "family": family,
                        "horizon": horizon,
                        "window": window["id"],
                        "seed": design["seed"],
                        "evidence_type": "synthetic_interface_probe"
                        if synthetic
                        else window["evidence_type"],
                        "cohort": "non_excess_at_t",
                        "cohort_sha256": hashes["evaluation"],
                        "role_sha256": hashes,
                        "predictors_sha256": exp01.digest(cols),
                        "number_of_variables": len(cols),
                        "coverage": coverage,
                        "frontier": [],
                        "status": "non_evaluable",
                        "reason": None,
                    }
                    if any(f.empty for f in selected.values()) or any(
                        selected[r].onset_target.nunique() != 2 for r in ("train", "calibration")
                    ):
                        child["reason"] = "insufficient_common_coverage_or_classes"
                        cells[variant] = {"child": child}
                        continue
                    matrices = {
                        role: predictor_projection(
                            f[cols],
                            cols,
                            dict.fromkeys(cols, design["predictor_availability_offset_months"]),
                        )
                        for role, f in selected.items()
                    }
                    model = fit(
                        family,
                        matrices["train"],
                        selected["train"].onset_target,
                        parameters,
                        design["seed"],
                    )
                    fits += 1
                    transform = calibrate(
                        model.predict(matrices["calibration"]),
                        selected["calibration"].onset_target,
                        design["seed"],
                    )
                    calibrations += 1
                    scores = {
                        r: transform(model.predict(matrices[r])).to_numpy(dtype=float)
                        for r in ("selection", "evaluation")
                    }
                    truth = selected["evaluation"].onset_target
                    prediction = pd.Series(scores["evaluation"], index=truth.index)
                    from sat_dengue.experiments.exp03_decisions import calibration_coefficients

                    child.update(
                        calibration_coefficients=calibration_coefficients(
                            truth.to_numpy(dtype=int), scores["evaluation"]
                        ),
                        status="evaluable",
                        average_precision=average_precision_metric(truth, prediction)["value"],
                        brier=brier_metric(truth, prediction)["value"],
                        auroc=auroc_metric(truth, prediction)["value"],
                        calibration=calibration_summary(
                            truth.to_numpy(dtype=int), scores["evaluation"]
                        ),
                    )
                    cells[variant] = {"child": child, "scores": scores}
                if cells["full"]["child"]["status"] == "evaluable":
                    truth = selected["selection"].onset_target.to_numpy(dtype=int)
                    evaluation = selected["evaluation"]
                    for budget in range(int((truth == 0).sum()) + 1):
                        for variant in variants:
                            cell = cells[variant]
                            if cell["child"]["status"] != "evaluable":
                                continue
                            thresholds = matched_thresholds(
                                truth,
                                cells["full"]["scores"]["selection"],
                                cell["scores"]["selection"],
                                budget,
                            )
                            alerts = {
                                k: np.zeros(len(evaluation), dtype=bool)
                                if t is None
                                else cells["full" if k == "excess" else variant]["scores"][
                                    "evaluation"
                                ]
                                >= t
                                for k, t in thresholds.items()
                            }
                            base = episode_metrics(evaluation, alerts["excess"])
                            metric = episode_metrics(evaluation, alerts["onset"])
                            profile_metrics = {}
                            for profile in evaluation.transmission_profile.dropna().unique():
                                mask = evaluation.transmission_profile.eq(profile).to_numpy()
                                profile_metrics[str(profile)] = episode_metrics(
                                    evaluation.loc[mask], alerts["onset"][mask]
                                )
                            emitted = alerts["onset"]
                            metric["excess_false_alarm_ratio"] = (
                                float(
                                    (
                                        emitted
                                        & evaluation.excess_target.eq(0).to_numpy(dtype=bool)
                                    ).sum()
                                    / emitted.sum()
                                )
                                if emitted.any()
                                else None
                            )
                            delta = (
                                None
                                if metric["onset_sensitivity"] is None
                                else metric["onset_sensitivity"] - base["onset_sensitivity"]
                            )
                            cell["child"]["frontier"].append(
                                {
                                    "selection_false_alert_budget": budget,
                                    "threshold": thresholds["onset"],
                                    "full_threshold": thresholds["excess"],
                                    "paired_onset_sensitivity_difference": delta,
                                    "full_realized_false_alerts": base["false_alerts"],
                                    "paired_interval": paired_block_interval(
                                        evaluation,
                                        alerts["excess"],
                                        alerts["onset"],
                                        seed=design["seed"],
                                    ),
                                    "by_group": stratified_episode_metrics(
                                        evaluation, alerts["onset"]
                                    )
                                    | {"transmission_profile": profile_metrics},
                                    **metric,
                                }
                            )
                cache[family, horizon, window["id"]] = (selected, cells)
                children.extend(cells[v]["child"] for v in variants)
    if len(children) != expected or fits != expected or calibrations != fits:
        raise ValueError("EXP03 count safety boundary")
    contrasts, audit = evaluate(cache, design)
    from sat_dengue.experiments.exp03_decisions import candidates

    decisions = candidates(contrasts, design)
    return {
        "decision_candidates": decisions,
        "contrasts": contrasts,
        "oof_audit": audit,
        "operational_coverage": operational_coverage,
        "schema": "exp03-result-v1",
        "experiment_id": "EXP03",
        "synthetic": synthetic,
        "real_model_fits": 0 if synthetic else fits,
        "real_preparer_refits": 0 if synthetic else fits,
        "calibrator_fits": 0 if synthetic else calibrations,
        "synthetic_interface_fits": fits if synthetic else 0,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "children": children,
    }


def synthetic_run() -> dict[str, Any]:
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(value, freq="M") + 180) for value in panel.year_month]
    design = load_protocol()["design"]
    return execute(
        panel,
        contract,
        design,
        fit=exp01.synthetic_fit,
        calibrate=lambda scores, truth, seed: lambda values: values,
        synthetic=True,
    )
