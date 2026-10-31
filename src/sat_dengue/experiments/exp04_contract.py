"""EXP04's independent technical contract; scientific readiness is separate."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from sat_dengue.configuration import canonical_bytes

ROOT = Path(
    "docs/product/experiments/EXP04_transporte_temporal_ de_calibracion_y_umbrales_de:decision"
)
BASELINE = Path(
    "tmp/kedro-migration/exp03-1-runs/"
    "007f54d4ef171db3ba10f7ad5a04c00aa5ebf5ff886629a111285c5b1923e928"
)
BASELINE_SHA256 = "5b3f20a266c5e6aae7d2727a00a2213ea9cc3bc691bac5f02267a3e44edc5619"
BASELINE_MANIFEST_SHA256 = "3315c0ab1349a404aca1e824d7d7527dfeaf22c9772fce2691700efcb3bbdd38"


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def protocol() -> dict[str, Any]:
    """Freeze implemented rules without accepting unspecified scientific choices."""
    return {
        "schema": "exp04-technical-protocol-v1",
        "version": "1.0.0",
        "experiment_id": "EXP04",
        "design_sha256": "70df561506873161b76860b21c2932131fa207be7dd885cad716ef1886c1f792",
        "status": "INDEPENDENT_COMPONENTS_ONLY",
        "baseline": {
            "source_experiment": "EXP03.1",
            "source_variant": "M00",
            "predictor_reference": "EXP03 V09 complete",
            "bundle_sha256": BASELINE_SHA256,
            "manifest_sha256": BASELINE_MANIFEST_SHA256,
            "source_git_revision": "001911f1e45874f36b74922094be4eb32ae7256e",
            "allow_substitution": False,
            "allow_refit": False,
            "allow_probability_inversion": False,
            "reconstruction": "require_verified_equivalence_or_BLOCKED_BASELINE",
        },
        "families": ["gam", "lightgbm", "xgboost"],
        "objectives": {"onset": [1, 2], "excess_control": [2]},
        "cuts": {
            "development": [2020, 2021, 2022],
            "retrospective_stress": [2024],
            "not_evaluable": [2025],
        },
        "target": "unchanged_H5_and_M00_paired_eligibility",
        "forbidden_features": ["EXP031_recent", "EXP031_change"],
        "exposure": {
            "historical": "original_M00_monitored_months_divided_by_12",
            "common": "same_eligible_observable_municipality_month_keys_divided_by_12",
            "primary": "common",
            "comparison": "identical_common_denominator_and_truth_in_every_paired_arm",
            "historical_rate_is_not_primary": True,
            "incomparable": "NOT_EVALUABLE",
        },
        "budget": {"B_primary": 1.0, "objective": "onset", "selection_only": True},
        "arms": {
            "A0": {"window": "original", "method": "original", "selector": "C0"},
            "A1": {"window_months": 12, "method": "original", "selector": "C0"},
            "A2": {"window_months": 24, "method": "original", "selector": "C0"},
            "A3": {"window_months": 36, "method": "original", "selector": "C0"},
            "A4": {"window": "expanding", "method": "original", "selector": "C0"},
            "B0": {"window": "development_selected", "method": "original", "selector": "C0"},
            "B1": {"window": "development_selected", "method": "sigmoid", "selector": "C0"},
            "B2": {"window": "development_selected", "method": "isotonic", "selector": "C0"},
            "C0": {"selector": "original", "calibration": "development_selected_frozen"},
            "C1": {"selector": "max_sensitivity_under_budget", "calibration": "same_as_C0"},
            "C2": {"selector": "worst_block_budget", "calibration": "same_as_C0"},
            "D": {
                "composition": "one_nested_development_choice",
                "without_support": "NOT_EVALUABLE",
            },
        },
        "contrasts": {
            "H1a": [["A1", "A0"], ["A2", "A0"], ["A3", "A0"], ["A4", "A0"]],
            "H1b": [["B1", "B0"], ["B2", "B0"]],
            "H1c": [["C1", "C0"], ["C2", "C0"]],
            "H1": [["D", "A0"]],
        },
        "threshold": {
            "comparison": ">=",
            "candidates": "distinct_selection_scores_and_no_alert_extreme",
            "ties": "max_TP_then_min_FP_then_min_alerts_then_highest_threshold",
            "C2_minimum_blocks": 2,
            "no_support": "NOT_EVALUABLE",
        },
        "calibration": {
            "sigmoid": "reuse_original_LogisticRegression_lbfgs_max_iter_1000",
            "isotonic": "monotone_increasing_no_fallback",
            "identity": "diagnostic_only_for_probability_scores",
        },
        "metrics": [
            "support",
            "TP",
            "FN",
            "FP",
            "TN",
            "sensitivity",
            "municipal_macro_sensitivity",
            "precision",
            "alerts",
            "common_FA_rate",
            "historical_FA_rate",
            "FAR",
            "FPR",
            "budget_excess",
            "selection_evaluation_drift",
            "brier",
            "ece",
            "reliability",
            "average_precision",
            "score_distribution",
            "prevalence",
            "coverage",
            "abstentions",
            "paired_differences",
            "year_department_strata",
            "false_alerts_by_error_class",
        ],
        "unresolved_scientific_inputs": [
            "verified_M00_raw_scores_calibrator_and_role_provenance",
            "mature_OOF_history_and_nested_role_schedule",
            "accepted_territorial_margin_and_material_FA_increase_rule",
            "isotonic_minimum_support",
            "uncertainty_block_unit_replicates_seed_or_explicit_UNAVAILABLE",
        ],
        "confirmatory_success": "DISABLED_UNTIL_SCIENTIFIC_PROTOCOL_FREEZE",
        "scientific_execution_authorized": False,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
