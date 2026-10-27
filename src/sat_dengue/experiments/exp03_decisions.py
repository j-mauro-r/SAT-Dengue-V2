"""Predeclared descriptive candidates; no model/budget selection or approval."""

from __future__ import annotations

from typing import Any

import numpy as np


def calibration_coefficients(truth: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    """Assessment-only logistic reliability slope/intercept; no predictive refit."""
    x = np.column_stack(
        [
            np.ones(len(scores)),
            np.log(np.clip(scores, 1e-8, 1 - 1e-8) / np.clip(1 - scores, 1e-8, 1)),
        ]
    )
    if np.linalg.matrix_rank(x) < 2 or len(np.unique(truth)) < 2:
        return {"status": "not_estimable", "slope": None, "intercept": None}
    beta = np.zeros(2)
    for _ in range(100):
        p = 1 / (1 + np.exp(-np.clip(x @ beta, -35, 35)))
        hessian = (x.T * (p * (1 - p))) @ x
        try:
            step = np.linalg.solve(hessian, x.T @ (truth - p))
        except np.linalg.LinAlgError:
            break
        beta += step
        if np.max(np.abs(beta)) > 100:
            break
        if np.max(np.abs(step)) < 1e-7:
            return {"status": "estimable", "intercept": float(beta[0]), "slope": float(beta[1])}
    return {"status": "not_estimable", "slope": None, "intercept": None}


def candidates(contrasts: list[dict[str, Any]], design: dict[str, Any]) -> list[dict[str, Any]]:
    development = {
        w["id"] for w in design["windows"] if w["evidence_type"] == "retrospective_development"
    }
    grouped: dict[tuple[Any, ...], list[Any]] = {}
    for row in contrasts:
        if row["window"] in development:
            key = (
                row["contrast_id"],
                row["family"],
                row["horizon"],
                row["selection_false_alert_budget"],
            )
            grouped.setdefault(key, []).append(row)
    output = []
    for (cid, family, horizon, budget), rows in grouped.items():
        if {r["window"] for r in rows} != development:
            continue
        if cid.startswith("added_"):
            value = all(
                r["paired_sensitivity_difference"] is not None
                and r["paired_sensitivity_difference"] >= 0
                for r in rows
            ) and any((r["paired_sensitivity_difference"] or 0) > 0 for r in rows)
            kind = "consistent_added_detection"
        else:
            value = all(
                r["left_metrics"]["real_onsets"] > 0
                and r["right_metrics"]["real_onsets"] > 0
                and r["right_metrics"]["detected_onsets"] >= r["left_metrics"]["detected_onsets"]
                and r["right_metrics"]["false_alerts"] <= r["left_metrics"]["false_alerts"]
                and r["right_brier"] <= r["left_brier"]
                and r["right_ece"] <= r["left_ece"]
                for r in rows
            )
            value = value and len(design["variants"][rows[0]["right_variant"]]) < len(
                design["variants"][rows[0]["left_variant"]]
            )
            kind = "candidate_removal_requires_prospective_confirmation"
        output.append(
            {
                "contrast_id": cid,
                "family": family,
                "horizon": horizon,
                "selection_false_alert_budget": budget,
                "rule": kind,
                "candidate": value,
                "automatic_selection": False,
            }
        )
    return output
