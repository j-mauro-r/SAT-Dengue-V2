"""Shared generated-only setup, no private sources or permanent stores."""

from __future__ import annotations

from typing import Any


def generated_delivery() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """A small audit fixture, not a substitute for the full engine example."""
    design = {
        "variants": {"V00": ["lag1"], "V06": ["lag1", "current"]},
        "inventory": {
            "lag1": {"latest_event_month": "T-1"},
            "current": {"latest_event_month": "T"},
        },
        "B_primary": {
            "value": 0,
            "units": "false-onset-alerts/monitored-municipality-year",
            "rationale": "synthetic test",
        },
        "contrasts": [
            {"id": "P1", "left": "V06", "right": "V00"},
            {"id": "S1", "left": "V06", "right": "V00"},
        ],
    }
    contrasts = [
        {
            "contrast_id": "P1",
            "family": "generated",
            "horizon": 1,
            "window": "pooled_development",
            "paired_sensitivity_difference": -0.5,
            "paired_burden_difference": 0.1,
            "recommendation": "inconclusive",
            "evidence_type": "synthetic_generated_data",
            "guardrail": "unknown",
        },
        {
            "contrast_id": "S1",
            "family": "generated",
            "horizon": 2,
            "window": "stress_2024",
            "paired_sensitivity_difference": None,
            "paired_burden_difference": None,
            "status": "not_evaluable",
            "reason": "no_onsets",
            "recommendation": "inconclusive",
        },
    ]
    predictions = []
    for year in (2020, 2021, 2022):
        for variant, score in (("V00", 0.8), ("V06", 0.2)):
            predictions.append(
                {
                    "municipality_code": "synthetic_001",
                    "origin": f"{year - 1}-12",
                    "target_month": f"{year}-01",
                    "horizon": 1,
                    "window": f"development_{year}",
                    "objective": "onset",
                    "variant": variant,
                    "family": "generated",
                    "onset_target": 1,
                    "excess_target": 1,
                    "raw_score": score,
                    "score": score,
                    "threshold": 0.5,
                    "alert": score >= 0.5,
                    "profile": "history_insufficient",
                    "risk_eligible": True,
                }
            )
    selection = [{**r, "origin": "2019-10", "target_month": "2019-11"} for r in predictions[:2]]
    result = {
        "schema": "exp03-result-v2",
        "experiment_id": "EXP03",
        "synthetic": True,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "real_model_fits": 0,
        "children": [
            {
                "cell_id": "fixture",
                "variant": "V00",
                "family": "generated",
                "horizon": 1,
                "window": "development_2020",
                "objective": "onset",
                "status": "evaluable",
                "private_rows": predictions,
            }
        ],
        "contrasts": contrasts,
        "oof_predictions": predictions,
        "selection_predictions": selection,
        "primary_contrasts": contrasts[:1],
        "secondary_contrasts": contrasts[1:],
        "performance_by_group": [
            {
                "year": 2020,
                "department": "synthetic",
                "profile": "history_insufficient",
                "support": 1,
                "onset_sensitivity": None,
                "brier": 0.5,
                "guardrail": "unknown",
            }
        ],
        "coverage_and_exclusions": [
            {"source_rows": 20, "common_rows": 6, "abstentions": 14, "excluded_onsets": 1}
        ],
        "exposure_by_cluster": [
            {
                "municipality_code": "synthetic_001",
                "target_year": 2020,
                "monitored_exposure": 1,
                "eligible_exposure": 0.5,
                "common_exposure": 0.25,
            }
        ],
        "error_types_and_delay": [
            {
                "diagnostic": "strict_availability",
                "status": "not_evaluable",
                "reason": "Y(T)_unavailable",
                "abstentions": 6,
            }
        ],
        "transport_2024_2025": [
            {
                "target_year": 2025,
                "view": "annual",
                "evidence_type": "consumed_retrospective_benchmark",
                "status": "not_evaluable",
                "reason": "synthetic_missing_coverage",
                "model_fits": 0,
                "preparer_fits": 0,
                "calibrator_fits": 0,
                "searches": 0,
                "threshold_selections": 0,
            }
        ],
        "thresholds": [
            {
                "variant": "V00",
                "threshold": 0.5,
                "selection_false_alert_cap": 0,
                "tp": 1,
                "fp": 0,
                "ties": 1,
            }
        ],
        "model_artifacts": {
            "synthetic_fixture.json": b'{"synthetic":true,"kind":"unit-audit-fixture"}\n'
        },
    }
    from sat_dengue.experiments.exp03_evaluation import select_threshold

    result["thresholds"] = [
        {
            **{key: row[key] for key in ("variant", "family", "horizon", "window", "objective")},
            **select_threshold([row["onset_target"]], [row["score"]], 0, 1),
        }
        for row in selection
    ]
    provenance = {"protocol_sha256": "fixture", "git_revision": "fixture-not-a-scientific-run"}
    return result, provenance, design
