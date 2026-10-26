"""Pure six-arm onset ablation using frozen EXP01 science; no I/O during fitting."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments import exp01
from sat_dengue.experiments.onset import KEYS, partitions, predictor_projection
from sat_dengue.experiments.onset_evaluation import (
    calibration_summary,
    episode_metrics,
    matched_thresholds,
    paired_block_interval,
    stratified_episode_metrics,
)

PROTOCOL = Path("docs/product/experiments/EXP02_feature_ablation/protocol.json")
VARIANTS = (
    "full",
    "without_current_zone",
    "without_channel",
    "history",
    "history_season",
    "history_climate",
)


def load_protocol() -> dict[str, Any]:
    from sat_dengue.tracking.experiments import resolve_experiment

    p = json.loads(PROTOCOL.read_text())
    source = exp01.load_protocol()
    if exp01.digest(p) != resolve_experiment("EXP02")["protocol_sha256"]:
        raise ValueError("EXP02 protocol changed")
    if exp01.digest(source) != p["reproducibility"]["exp01_protocol_sha256"]:
        raise ValueError("EXP01 scientific interface changed")
    for key in (
        "predictors",
        "families",
        "windows",
        "seed",
        "threads",
        "calibration",
        "predictor_availability_offset_months",
    ):
        if p["design"][key] != source["design"][key]:
            raise ValueError("EXP02 differs from EXP01: " + key)
    groups = p["design"]["groups"]
    expected = source["design"]["predictors"]
    if len(sum(groups.values(), [])) != len(expected) or set(sum(groups.values(), [])) != set(
        expected
    ):
        raise ValueError("Feature group mismatch")
    memberships = {
        "full": list(groups),
        "without_current_zone": [g for g in groups if g != "canal_actual"],
        "without_channel": [g for g in groups if not g.startswith("canal")],
        "history": ["historia"],
        "history_season": ["historia", "estacionalidad"],
        "history_climate": ["historia", "clima"],
    }
    if set(p["design"]["variants"]) != set(VARIANTS):
        raise ValueError("EXP02 requires six variants")
    for name, included in memberships.items():
        if p["design"]["variants"][name] != [
            c for c in expected if c in sum((groups[g] for g in included), [])
        ]:
            raise ValueError("Variant composition changed")
    if any(
        p["design"][k] != 108
        for k in ("expected_children", "expected_model_fits", "expected_calibrator_fits")
    ):
        raise ValueError("Fit budget changed")
    return p


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
    from sat_dengue.metrics import auroc_metric, average_precision_metric, brier_metric

    full = design["predictors"]
    variants = design["variants"]
    if set(variants) != set(VARIANTS) or variants["full"] != full:
        raise ValueError("Noncanonical variants")
    if synthetic and fit is not exp01.synthetic_fit:
        raise ValueError("Synthetic route cannot call production estimators")
    children: list[dict[str, Any]] = []
    fits = 0
    calibrations = 0
    for horizon in (1, 2):
        cohort = exp01.prepare(panel, contract, horizon)
        for window in design["windows"]:
            parts = partitions(cohort, window)
            selected = {
                role: f.loc[
                    f.onset_target.notna() & f.excess_target.notna() & f[full].notna().all(axis=1)
                ].copy()
                for role, f in parts.items()
            }
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
                for variant in VARIANTS:
                    cols = variants[variant]
                    child = {
                        "variant": variant,
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
                    child.update(
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
                        for variant in VARIANTS:
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
                                    ),
                                    **metric,
                                }
                            )
                children.extend(cells[v]["child"] for v in VARIANTS)
    if len(children) != 108 or fits > 108 or calibrations != fits:
        raise ValueError("EXP02 count safety boundary")
    return {
        "schema": "exp02-result-v1",
        "experiment_id": "EXP02",
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
    panel, contract, generated = exp01.synthetic_inputs()
    frozen = load_protocol()["design"]
    for window, original in zip(generated["windows"], frozen["windows"], strict=True):
        window["id"] = original["id"]
    design = {**frozen, "windows": generated["windows"]}
    return execute(
        panel,
        contract,
        design,
        fit=exp01.synthetic_fit,
        calibrate=lambda scores, truth, seed: lambda x: x,
        synthetic=True,
    )
