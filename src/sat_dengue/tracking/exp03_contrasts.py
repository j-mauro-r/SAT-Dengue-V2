"""Objective-aware, closed aggregate contrast evidence for revised EXP03."""

from __future__ import annotations

import math
from typing import Any

from sat_dengue.experiments.exp01 import digest

FIELDS = {
    "contrast_id",
    "left_variant",
    "right_variant",
    "left_objective",
    "right_objective",
    "family",
    "horizon",
    "window",
    "source_cuts",
    "left_cells",
    "right_cells",
    "tier",
    "paired_sensitivity_difference",
    "paired_burden_difference",
    "paired_interval",
    "decision",
    "left_metrics",
    "right_metrics",
}
INTERVAL_FIELDS = {"estimate", "lower", "upper", "valid_draws", "status"}
DECISION_FIELDS = {
    "calibration_limitation",
    "sensitivity_direction",
    "evaluation_cap",
    "formal_equivalence",
    "clinical_margin_established",
    "automatic_selection",
    "aggregate_benefit",
    "operational_burden",
    "department_guardrail",
    "profile_guardrail",
    "calibration",
    "coverage",
    "delay",
    "support",
    "evidence_level",
    "recommendation",
}
DECISION_VALUES = {
    "different_probability_targets_not_comparable",
    "pass",
    "fail",
    "unknown",
    "retrospective_development",
    "retrospective_stress",
    "consumed_retrospective_benchmark",
    "candidate_for_further_validation",
    "inconclusive",
    "additional_detection_at_additional_burden",
    "not_evaluated",
    "descriptive_only",
}


def projection(rows: list[Any]) -> list[Any]:
    """Drop private dimensions and raw audit payloads through a finite allowlist."""
    from sat_dengue.tracking.exp03 import metric_projection

    result = []
    for row in rows:
        projected = {k: row[k] for k in FIELDS if k in row}
        for name in ("paired_sensitivity_difference", "paired_burden_difference"):
            projected.setdefault(name, None)
        interval = row.get("paired_interval", {})
        projected["paired_interval"] = {
            k: (
                {name: item for name, item in v.items() if name in INTERVAL_FIELDS}
                if k in {"sensitivity_difference", "false_alert_rate_difference"}
                and isinstance(v, dict)
                else v
            )
            for k, v in interval.items()
            if k
            in {
                "sensitivity_difference",
                "false_alert_rate_difference",
                "seed",
                "draws",
                "method",
                "status",
            }
        }
        for side in ("left", "right"):
            projected[side + "_metrics"] = metric_projection(row.get(side + "_metrics", {}))
        result.append(projected)
    return result


def _finite(value: Any) -> bool:
    return value is None or (type(value) in (int, float) and math.isfinite(value))


def _interval(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("Invalid interval")
    allowed = {
        "sensitivity_difference",
        "false_alert_rate_difference",
        "seed",
        "draws",
        "method",
        "status",
    }
    if not set(value) <= allowed:
        raise ValueError("Unapproved interval fields")
    for key in ("sensitivity_difference", "false_alert_rate_difference"):
        if key not in value:
            continue
        record = value[key]
        if not isinstance(record, dict) or set(record) != INTERVAL_FIELDS:
            raise ValueError("Unapproved interval metric")
        if any(not _finite(record[k]) for k in ("estimate", "lower", "upper")):
            raise ValueError("Invalid interval metric")
        if type(record["valid_draws"]) is not int or not 0 <= record["valid_draws"] <= 1000:
            raise ValueError("Invalid bootstrap support")
        if record["status"] not in {
            "not_applicable_stress",
            "available",
            "retrospective_paired",
            "insufficient_cluster_support",
            "insufficient_onset_years",
            "no_onset_support",
            "no_valid_resamples",
            "unavailable",
            "unknown",
            "ok",
            "not_evaluable",
            "insufficient_support",
        }:
            raise ValueError("Invalid interval status")
        if (
            record["lower"] is not None
            and record["upper"] is not None
            and record["lower"] > record["upper"]
        ):
            raise ValueError("Invalid interval bounds")
    if "seed" in value and type(value["seed"]) is not int:
        raise ValueError("Invalid interval seed")
    if "draws" in value and (type(value["draws"]) is not int or not 0 <= value["draws"] <= 1000):
        raise ValueError("Invalid interval draws")
    if (
        "method" in value
        and value["method"] != "paired_two_way_municipality_year_cluster_percentile"
    ):
        raise ValueError("Invalid interval method")
    if "status" in value and value["status"] not in {
        "retrospective_stress_no_development_interval",
        "insufficient_cluster_support",
        "retrospective_paired",
        "not_evaluable",
        "ok",
        "unknown",
    }:
        raise ValueError("Invalid interval status")


def validate(rows: Any, design: dict[str, Any], expected_budgets: dict | None = None) -> None:
    """Validate both declared ablations and the two bounded objective controls."""
    from sat_dengue.tracking.exp03 import METRIC_FIELDS

    if not isinstance(rows, list):
        raise ValueError("Invalid aggregate contrasts")
    contrasts = {c["id"]: c for c in design["contrasts"]}
    for index, variant in enumerate(("V00", "V09"), 1):
        contrasts["O" + str(index)] = {"left": variant, "right": variant}
    windows = {w["id"]: w for w in design["windows"]}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != FIELDS or row["contrast_id"] not in contrasts:
            raise ValueError("Unapproved contrast fields or identity")
        c = contrasts[row["contrast_id"]]
        control = row["contrast_id"] in {"O1", "O2"}
        if (
            row["family"] not in design["families"]
            or row["horizon"] not in design["horizons"]
            or any(row[side + "_variant"] != c[side] for side in ("left", "right"))
            or row["left_objective"] not in {"onset", "excess"}
            or row["right_objective"] not in {"onset", "excess"}
            or (
                control
                and (
                    row["horizon"] != 2
                    or {row["left_objective"], row["right_objective"]} != {"onset", "excess"}
                )
            )
            or (
                not control
                and (row["left_objective"] != "onset" or row["right_objective"] != "onset")
            )
        ):
            raise ValueError("Unbound contrast identity")
        cuts = (
            [
                w["id"]
                for w in design["windows"]
                if w["evidence_type"] == "retrospective_development"
            ]
            if row["window"] in {"pooled_development", "development_oof"}
            else [row["window"]]
        )
        if any(w not in windows for w in cuts) or row["source_cuts"] != cuts:
            raise ValueError("Unbound contrast cuts")
        for side in ("left", "right"):
            expected = [
                digest(
                    {
                        "variant": c[side],
                        "objective": row[side + "_objective"],
                        "family": row["family"],
                        "horizon": row["horizon"],
                        "window": w,
                    }
                )
                for w in cuts
            ]
            if row[side + "_cells"] != expected:
                raise ValueError("Contrast must reuse canonical fitted cells")
            metrics = row[side + "_metrics"]
            if (
                not isinstance(metrics, dict)
                or not set(metrics) <= METRIC_FIELDS
                or any(not _finite(v) for v in metrics.values())
            ):
                raise ValueError("Unapproved aggregate metrics")
        key = (row["contrast_id"], row["family"], row["horizon"], row["window"])
        if key in seen:
            raise ValueError("Duplicate aggregate contrast")
        seen.add(key)
        for metric_key in ("paired_sensitivity_difference", "paired_burden_difference"):
            if not _finite(row[metric_key]):
                raise ValueError("Invalid paired difference")
        if row["tier"] not in {"primary", "secondary", "objective_control", "control"}:
            raise ValueError("Invalid contrast tier")
        _interval(row["paired_interval"])
        if row["window"] == "stress_2024" and any(
            value.get("lower") is not None or value.get("upper") is not None
            for key, value in row["paired_interval"].items()
            if key in {"sensitivity_difference", "false_alert_rate_difference"}
        ):
            raise ValueError("Stress cannot carry a development interval")
        decision = row["decision"]
        if (
            not isinstance(decision, dict)
            or not set(decision) <= DECISION_FIELDS
            or any(
                (
                    v is not False
                    if k
                    in {"formal_equivalence", "clinical_margin_established", "automatic_selection"}
                    else v not in DECISION_VALUES
                )
                for k, v in decision.items()
            )
        ):
            raise ValueError("Unapproved decision record")

    if rows:
        expected_keys = {
            (cid, family, horizon, window)
            for cid in contrasts
            for family in design["families"]
            for horizon in design["horizons"]
            for window in ("pooled_development", "stress_2024")
            if cid not in {"O1", "O2"} or horizon == 2
        }
        if seen != expected_keys:
            raise ValueError("Incomplete revised contrast grid")
