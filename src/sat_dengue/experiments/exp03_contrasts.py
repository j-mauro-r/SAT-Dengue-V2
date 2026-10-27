"""Paired contrasts from already fitted cells; OOF development only for inference."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.onset_evaluation import (
    episode_metrics,
    matched_thresholds,
    stratified_episode_metrics,
)


def interval(frame: pd.DataFrame, left: np.ndarray, right: np.ndarray, seed: int) -> dict[str, Any]:
    """Two-way municipality/year cluster weights, paired draws and no IID fallback."""
    municipalities = sorted(frame.municipality_code.unique())
    years = sorted(frame.target_month.str[:4].unique())
    if len(municipalities) < 2 or len(years) < 3:
        return {"status": "insufficient_cluster_support", "interval": None, "valid_replicates": 0}
    positive = frame.onset_target.to_numpy(dtype=int) == 1
    counts = np.zeros((3, len(municipalities), len(years)))
    for m, municipality in enumerate(municipalities):
        for y, year in enumerate(years):
            mask = (
                frame.municipality_code.eq(municipality).to_numpy()
                & frame.target_month.str.startswith(year).to_numpy()
                & positive
            )
            counts[:, m, y] = [mask.sum(), (mask & left).sum(), (mask & right).sum()]
    rng = np.random.default_rng(seed)
    wm = rng.multinomial(
        len(municipalities), np.full(len(municipalities), 1 / len(municipalities)), size=1000
    )
    wy = rng.multinomial(len(years), np.full(len(years), 1 / len(years)), size=1000)
    totals = np.einsum("rm,rn,kmn->kr", wm, wy, counts)
    valid = totals[0] > 0
    differences = (totals[1, valid] - totals[2, valid]) / totals[0, valid]
    return {
        "valid_replicates": int(valid.sum()),
        "status": "retrospective_paired" if len(differences) else "no_onset_support",
        "interval": np.quantile(differences, [0.025, 0.975]).tolist() if len(differences) else None,
    }


def evaluate(
    cache: dict[tuple[str, int, str], Any], design: dict[str, Any]
) -> tuple[list[Any], list[Any]]:
    results, audit = [], []
    for family in design["families"]:
        for horizon in design["horizons"]:
            pooled: dict[tuple[str, int], list[Any]] = {}
            for window in design["windows"]:
                parts, cells = cache[family, horizon, window["id"]]
                selection, evaluation = parts["selection"], parts["evaluation"]
                truth = selection.onset_target.to_numpy(dtype=int)
                cap = int((truth == 0).sum())
                for c in design["contrasts"]:
                    a, b = cells[c["left"]], cells[c["right"]]
                    for budget in range(cap + 1):
                        thresholds = matched_thresholds(
                            truth, a["scores"]["selection"], b["scores"]["selection"], budget
                        )
                        alerts = [
                            np.zeros(len(evaluation), dtype=bool)
                            if thresholds[k] is None
                            else scores >= thresholds[k]
                            for k, scores in (
                                ("excess", a["scores"]["evaluation"]),
                                ("onset", b["scores"]["evaluation"]),
                            )
                        ]
                        row = contrast(
                            c,
                            family,
                            horizon,
                            window["id"],
                            budget,
                            evaluation,
                            alerts,
                            design["seed"],
                        )
                        row["left_cells"] = [a["child"]["cell_id"]]
                        row["right_cells"] = [b["child"]["cell_id"]]
                        row["source_cuts"] = [window["id"]]
                        row["left_brier"] = a["child"]["brier"]
                        row["right_brier"] = b["child"]["brier"]
                        row["left_ece"] = a["child"]["calibration"]["expected_calibration_error"]
                        row["right_ece"] = b["child"]["calibration"]["expected_calibration_error"]
                        results.append(row)
                        if window["evidence_type"] == "retrospective_development":
                            pooled.setdefault((c["id"], budget), []).append(
                                (evaluation, alerts, window["id"])
                            )
                # Native audit only; artifact projection never includes individual predictions.
                for name, cell in cells.items():
                    for pos, record in enumerate(
                        evaluation[["municipality_code", "year_month", "target_month"]].to_dict(
                            "records"
                        )
                    ):
                        audit.append(
                            {
                                **record,
                                "family": family,
                                "horizon": horizon,
                                "variant": name,
                                "source_cut": window["id"],
                                "score": float(cell["scores"]["evaluation"][pos]),
                                "development_oof": window["evidence_type"]
                                == "retrospective_development",
                            }
                        )
            ndev = sum(w["evidence_type"] == "retrospective_development" for w in design["windows"])
            for (cid, budget), blocks in pooled.items():
                if len(blocks) != ndev:
                    continue  # Common integer budget support across all development cuts.
                frame = pd.concat([b[0] for b in blocks], ignore_index=True)
                if frame.duplicated(["municipality_code", "target_month"]).any():
                    raise ValueError("Duplicate pooled OOF prediction")
                alerts = [np.concatenate([b[1][side] for b in blocks]) for side in (0, 1)]
                c = next(c for c in design["contrasts"] if c["id"] == cid)
                row = contrast(
                    c, family, horizon, "development_oof", budget, frame, alerts, design["seed"]
                )
                row["source_cuts"] = [b[2] for b in blocks]
                for side in ("left", "right"):
                    row[side + "_cells"] = [
                        digest([c[side], family, horizon, b[2]]) for b in blocks
                    ]
                row["evaluation_years"] = sorted(frame.target_month.str[:4].unique())
                results.append(row)
    return results, audit


def contrast(
    c: dict[str, Any],
    family: str,
    horizon: int,
    window: str,
    budget: int,
    frame: pd.DataFrame,
    alerts: list[np.ndarray],
    seed: int,
) -> dict[str, Any]:
    left, right = [episode_metrics(frame, a) for a in alerts]
    delta = (
        None
        if left["onset_sensitivity"] is None
        else left["onset_sensitivity"] - right["onset_sensitivity"]
    )
    return {
        "contrast_id": c["id"],
        "semantic_roles": c["semantic_roles"],
        "left_variant": c["left"],
        "right_variant": c["right"],
        "family": family,
        "horizon": horizon,
        "window": window,
        "selection_false_alert_budget": budget,
        "cohort_sha256": digest(
            frame[["municipality_code", "year_month", "target_month", "onset_target"]].to_json(
                orient="split"
            )
        ),
        "left_metrics": left,
        "right_metrics": right,
        "paired_sensitivity_difference": delta,
        "paired_interval": interval(frame, alerts[0], alerts[1], seed),
        "by_group": {
            side: stratified_episode_metrics(frame, a)
            | {
                "transmission_profile": {
                    str(profile): episode_metrics(
                        frame.loc[frame.transmission_profile.eq(profile)],
                        a[frame.transmission_profile.eq(profile).to_numpy()],
                    )
                    for profile in frame.transmission_profile.dropna().unique()
                }
            }
            for side, a in zip(("left", "right"), alerts, strict=True)
        },
        "evidence": "retrospective_candidate_only_requires_prospective_confirmation",
    }
