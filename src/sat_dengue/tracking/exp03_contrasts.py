"""Closed aggregate-only contrast projection, with canonical fitted-cell references."""

from __future__ import annotations

import math
from typing import Any

from sat_dengue.experiments.exp01 import digest

METRICS = {
    "real_onsets",
    "detected_onsets",
    "missed_episodes",
    "detected_episodes",
    "false_alerts",
    "emitted_alerts",
    "onset_sensitivity",
    "onset_precision",
    "false_alarm_ratio",
    "false_alerts_per_municipality_year",
    "evaluable_rows",
    "unavailable_outcomes",
    "missing_predictions",
    "useful_lead_months",
}
FIELDS = {
    "contrast_id",
    "left_variant",
    "right_variant",
    "family",
    "horizon",
    "window",
    "selection_false_alert_budget",
    "left_cells",
    "right_cells",
    "source_cuts",
    "left_metrics",
    "right_metrics",
    "paired_sensitivity_difference",
    "paired_interval",
    "semantic_roles",
}


def projection(rows: list[Any]) -> list[Any]:
    return [{k: r[k] for k in FIELDS} for r in rows]


def budgets(cells: list[Any], design: dict[str, Any]) -> dict[tuple[Any, ...], list[int]]:
    result = {}
    for family in design["families"]:
        for horizon in design["horizons"]:
            development = []
            for window in design["windows"]:
                group = [
                    c
                    for c in cells
                    if c["family"] == family
                    and c["horizon"] == horizon
                    and c["window"] == window["id"]
                ]
                support = [
                    [r["selection_false_alert_budget"] for r in c["frontier"]] for c in group
                ]
                if (
                    not group
                    or any(v != support[0] for v in support)
                    or support[0] != list(range(len(support[0])))
                ):
                    raise ValueError("Incomplete common cell budget frontier")
                result[family, horizon, window["id"]] = support[0]
                if window["evidence_type"] == "retrospective_development":
                    development.append(set(support[0]))
            result[family, horizon, "development_oof"] = sorted(set.intersection(*development))
    return result


def validate(rows: Any, design: dict[str, Any], expected_budgets: dict | None = None) -> None:
    if not isinstance(rows, list):
        raise ValueError("Invalid aggregate contrasts")
    contrasts = {c["id"]: c for c in design["contrasts"]}
    windows = {w["id"]: w for w in design["windows"]}
    seen = set()
    for r in rows:
        if not isinstance(r, dict) or set(r) != FIELDS or r["contrast_id"] not in contrasts:
            raise ValueError("Unapproved contrast fields")
        c = contrasts[r["contrast_id"]]
        if (
            r["family"] not in design["families"]
            or r["horizon"] not in design["horizons"]
            or any(r[side + "_variant"] != c[side] for side in ("left", "right"))
            or r["semantic_roles"] != c["semantic_roles"]
        ):
            raise ValueError("Unbound contrast identity")
        cuts = (
            [
                w["id"]
                for w in design["windows"]
                if w["evidence_type"] == "retrospective_development"
            ]
            if r["window"] == "development_oof"
            else [r["window"]]
        )
        if any(w not in windows for w in cuts) or r["source_cuts"] != cuts:
            raise ValueError("Unbound contrast cuts")
        for side in ("left", "right"):
            if r[side + "_cells"] != [
                digest([c[side], r["family"], r["horizon"], w]) for w in cuts
            ]:
                raise ValueError("Contrast must reference canonical existing cells")
            metrics = r[side + "_metrics"]
            if set(metrics) != METRICS or any(
                v is not None and (type(v) not in (float, int) or not math.isfinite(v) or v < 0)
                for v in metrics.values()
            ):
                raise ValueError("Unsafe aggregate metrics")
        budget = r["selection_false_alert_budget"]
        if type(budget) is not int or budget < 0:
            raise ValueError("Invalid contrast budget")
        key = (c["id"], r["family"], r["horizon"], r["window"], budget)
        if key in seen:
            raise ValueError("Duplicate aggregate contrast")
        seen.add(key)
        delta = r["paired_sensitivity_difference"]
        if delta is not None and (
            type(delta) not in (float, int) or not math.isfinite(delta) or not -1 <= delta <= 1
        ):
            raise ValueError("Invalid paired difference")
        ci = r["paired_interval"]
        if set(ci) != {"status", "interval", "valid_replicates"} or ci["status"] not in {
            "insufficient_cluster_support",
            "retrospective_paired",
            "no_onset_support",
        }:
            raise ValueError("Unsafe interval")
        if type(ci["valid_replicates"]) is not int or not 0 <= ci["valid_replicates"] <= 1000:
            raise ValueError("Invalid bootstrap replicate support")
        values = ci["interval"]
        if values is not None and (
            not isinstance(values, list)
            or len(values) != 2
            or any(
                type(v) not in (float, int) or not math.isfinite(v) or not -1 <= v <= 1
                for v in values
            )
            or values[0] > values[1]
        ):
            raise ValueError("Invalid confidence bounds")
        if r["window"] != "development_oof" and (
            values is not None or ci["status"] != "insufficient_cluster_support"
        ):
            raise ValueError("Single-year contrast cannot claim interval")
    if expected_budgets is not None:
        expected = {
            (c["id"], family, horizon, window, b)
            for c in design["contrasts"]
            for (family, horizon, window), support in expected_budgets.items()
            for b in support
        }
        if seen != expected:
            raise ValueError("Incomplete eleven-contrast grid or budget frontier")
