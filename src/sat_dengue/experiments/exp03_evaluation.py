"""EXP03 fixed-budget utility and paired, exposure-aware retrospective summaries.

This module performs no scientific input reads, fitting, persistence or tracking.
All uncertainty is conditional on supplied out-of-sample predictions.
"""

from __future__ import annotations

from hashlib import sha256
from math import floor
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03_decisions import calibration_coefficients
from sat_dengue.experiments.onset_evaluation import calibration_summary

BUDGET_UNITS = "false_onset_alerts_per_monitored_municipality_year"


def _binary(values: Any, name: str) -> np.ndarray:
    result = np.asarray(values)
    if not np.isin(result, [0, 1]).all():
        raise ValueError(f"{name} must contain known binary values")
    return result.astype(int)


def _probability(values: Any) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if not np.isfinite(result).all() or ((result < 0) | (result > 1)).any():
        raise ValueError("Scores must be finite probabilities")
    return result


def _exposure(value: float, name: str) -> float:
    result = float(value)
    if not np.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def select_threshold(
    truth: Any, scores: Any, budget: float | dict[str, Any] | None, exposure: float
) -> dict[str, Any]:
    """Optimize onset detections subject to floor(B*D), without splitting ties.

    Numeric budgets are useful for generated fixtures. Production admission must
    additionally establish the budget's authority and rationale before reading data.
    """
    if budget is None:
        raise PermissionError("B_primary is pending; threshold selection is blocked")
    metadata = budget if isinstance(budget, dict) else {"value": budget}
    if metadata.get("units", BUDGET_UNITS) != BUDGET_UNITS:
        raise ValueError("B_primary units differ from monitored municipality-years")
    rate = _exposure(metadata["value"], "B_primary")
    denominator = _exposure(exposure, "selection exposure")
    y, p = _binary(truth, "Selection onset truth"), _probability(scores)
    if len(y) != len(p):
        raise ValueError("Selection truth and scores differ in length")
    if denominator == 0 and len(y):
        raise ValueError("Selection rows cannot have zero monitored exposure")
    cap = floor(rate * denominator)
    choices: list[tuple[int, int, int, float | None]] = [(0, 0, 0, None)]
    for threshold in np.unique(p):
        alerts = p >= threshold
        fp = int((alerts & (y == 0)).sum())
        tp = int((alerts & (y == 1)).sum())
        if fp <= cap:
            choices.append((tp, -fp, -int(alerts.sum()), float(threshold)))
    tp, negative_fp, negative_alerts, threshold = max(
        choices, key=lambda v: (v[0], v[1], v[2], 2.0 if v[3] is None else v[3])
    )
    fp, emitted = -negative_fp, -negative_alerts
    return {
        "threshold": threshold,
        "no_alert": threshold is None,
        "B_primary": rate,
        "units": BUDGET_UNITS,
        "budget_rationale": metadata.get("rationale"),
        "monitored_exposure": denominator,
        "selection_false_alert_cap": cap,
        "detected_onsets": tp,
        "false_alerts": fp,
        "emitted_alerts": emitted,
        "underspend": cap - fp,
        "achieved_false_alert_rate": fp / denominator if denominator else None,
        "whole_score_ties": True,
        "threshold_tie_size": int((p == threshold).sum()) if threshold is not None else 0,
        "distinct_scores": int(len(np.unique(p))),
        "selection_rows": len(y),
        "policy": "maximize_tp_then_minimize_fp_then_alerts_then_maximize_threshold",
    }


def _keys(frame: pd.DataFrame) -> list[str]:
    columns = ["municipality_code", "target_month"]
    for name in ("source_cut", "window"):
        if name in frame:
            columns.append(name)
    if frame.duplicated(columns).any():
        raise ValueError("Duplicate municipality/target/source-cut prediction keys")
    return columns


def metrics(
    frame: pd.DataFrame,
    alerts: Any,
    monitored_exposure: float,
    eligible_exposure: float | None = None,
    score: Any = None,
    objective: str = "onset",
) -> dict[str, Any]:
    """Count common-onset alert utility; probability metrics retain their target.

    Unknown outcomes are excluded explicitly. Missing predictions retain known
    onsets as missed and are counted as abstentions. Supplied exposure comes from
    the pre-gate ledger, never from complete-case prediction rows.
    """
    _keys(frame)
    if objective not in {"onset", "excess"}:
        raise ValueError("Probability objective must be onset or excess")
    denominator = _exposure(monitored_exposure, "monitored exposure")
    eligible = (
        _exposure(eligible_exposure, "eligible exposure") if eligible_exposure is not None else None
    )
    a = pd.Series(alerts).reset_index(drop=True)
    if len(a) != len(frame) or not a.dropna().isin([0, 1, False, True]).all():
        raise ValueError("Alerts must be aligned binary values or explicit abstentions")
    y = frame.onset_target.reset_index(drop=True)
    if not y.dropna().isin([0, 1]).all():
        raise ValueError("Onset targets must be binary or unknown")
    known = y.notna().to_numpy()
    emitted = a.fillna(False).to_numpy(dtype=bool)
    positive = y.eq(1).fillna(False).to_numpy(dtype=bool)
    negative = y.eq(0).fillna(False).to_numpy(dtype=bool)
    tp, fp = int((emitted & positive).sum()), int((emitted & negative).sum())
    onsets, total_alerts = int(positive.sum()), int(emitted.sum())
    tn = int((~emitted & negative).sum())
    evaluable_alerts = tp + fp
    covered_onsets = int(frame.attrs.get("covered_onsets", onsets))
    eligible_onsets = int(frame.attrs.get("eligible_onsets", onsets))
    if min(covered_onsets, eligible_onsets) < onsets:
        raise ValueError("Known eligible onset denominator cannot be smaller than common onsets")
    if (
        "covered_onsets" in frame.attrs
        and "eligible_onsets" in frame.attrs
        and covered_onsets < eligible_onsets
    ):
        raise ValueError("Known covered onset denominator cannot be smaller than eligible onsets")
    result: dict[str, Any] = {
        "rows": len(frame),
        "known_outcomes": int(known.sum()),
        "unknown_outcomes": int((~known).sum()),
        "covered_onsets": covered_onsets,
        "covered_onsets_source": "explicit_known_covered_onsets"
        if "covered_onsets" in frame.attrs
        else "supplied_frame_known_onsets_only",
        "eligible_onsets": eligible_onsets,
        "real_onsets": onsets,
        "common_onsets": onsets,
        "eligible_onsets_excluded_from_common": eligible_onsets - onsets,
        "coverage_denominator_source": frame.attrs.get(
            "coverage_denominator_source",
            "explicit_known_eligible_onsets"
            if "eligible_onsets" in frame.attrs
            else "supplied_frame_known_onsets_only",
        ),
        "detected_onsets": tp,
        "missed_onsets": onsets - tp,
        "emitted_alerts": total_alerts,
        "false_alerts": fp,
        "true_negatives": tn,
        "alerts_with_unknown_outcomes": int((emitted & ~known).sum()),
        "abstentions": int(a.isna().sum()),
        "onset_sensitivity": tp / onsets if onsets else None,
        "coverage_adjusted_sensitivity": tp / eligible_onsets if eligible_onsets else None,
        "onset_precision": tp / evaluable_alerts if evaluable_alerts else None,
        "false_alarm_ratio": fp / evaluable_alerts if evaluable_alerts else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
        "false_alerts_per_monitored_municipality_year": fp / denominator if denominator else None,
        "false_alerts_per_eligible_municipality_year": fp / eligible if eligible else None,
        "monitored_exposure": denominator,
        "eligible_exposure": eligible,
        "alert_month_fraction": total_alerts / (12 * denominator) if denominator else None,
        "nominal_lead_months": (
            int(frame.horizon.iloc[0]) if "horizon" in frame and not frame.empty else None
        ),
        "actual_lead_months": None,
        "probability_objective": objective,
        "average_precision": None,
        "brier": None,
        "auroc": None,
        "prevalence": None,
        "calibration": None,
        "calibration_coefficients": {"status": "not_estimable", "slope": None, "intercept": None},
    }
    if score is not None:
        from sat_dengue.metrics import auroc_metric, average_precision_metric, brier_metric

        values = pd.Series(score).reset_index(drop=True)
        target = frame[f"{objective}_target"].reset_index(drop=True)
        if len(values) != len(frame):
            raise ValueError("Probability scores differ in length")
        if not values.dropna().between(0, 1).all():
            raise ValueError("Probability scores outside [0,1]")
        result["probability_unavailable_rows"] = int((values.isna() | target.isna()).sum())
        result["average_precision"] = average_precision_metric(target, values)["value"]
        result["brier"] = brier_metric(target, values)["value"]
        result["auroc"] = auroc_metric(target, values)["value"]
        if len(frame) and not result["probability_unavailable_rows"]:
            truth, probabilities = target.to_numpy(dtype=int), values.to_numpy(dtype=float)
            result["prevalence"] = float(truth.mean())
            result["calibration"] = calibration_summary(truth, probabilities)
            result["calibration_coefficients"] = calibration_coefficients(truth, probabilities)
    return result


def _paired_frames(left: pd.DataFrame, right: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    keys = _keys(left)
    if keys != _keys(right):
        raise ValueError("Paired source-cut key columns differ")
    a, b = (f.sort_values(keys).reset_index(drop=True).copy() for f in (left, right))
    if not a[keys].equals(b[keys]) or not a.onset_target.equals(b.onset_target):
        raise ValueError("Paired prediction keys or onset labels differ")
    if a.onset_target.isna().any():
        raise ValueError("Paired uncertainty requires known common-cohort labels")
    _binary(a.onset_target, "Paired onset truth")
    for f in (a, b):
        _binary(f.alert, "Paired alerts")
        f["target_year"] = f.target_month.astype(str).str[:4].astype(int)
        if not f.target_year.isin([2020, 2021, 2022]).all():
            raise ValueError("Only 2020-2022 development enters paired uncertainty")
    return a, b


def paired_interval(
    left: pd.DataFrame,
    right: pd.DataFrame,
    exposures: pd.DataFrame,
    *,
    seed: int = 42,
    draws: int = 1000,
) -> dict[str, Any]:
    """Two-way municipality/year paired bootstrap of counts AND exposure.

    Municipalities with covered ineligible months but no predictions remain in
    the sampling universe. Full year blocks receive the same multiplicity in
    both arms and in all numerator and denominator tensors.
    """
    if not isinstance(draws, int) or draws < 1:
        raise ValueError("A positive number of bootstrap draws is required")
    a, b = _paired_frames(left, right)
    e = exposures.copy()
    if "target_year" not in e:
        raise ValueError("Exposure ledger requires target_year")
    e["target_year"] = e.target_year.astype(int)
    if not e.target_year.isin([2020, 2021, 2022]).all():
        raise ValueError("Stress/benchmark exposures cannot enter development uncertainty")
    exposure_columns = ["monitored_exposure", "eligible_exposure", "common_exposure"]
    for column in exposure_columns:
        if column not in e or not np.isfinite(e[column].to_numpy(dtype=float)).all():
            raise ValueError(f"Missing/nonfinite exposure ledger column: {column}")
        if e[column].lt(0).any():
            raise ValueError("Negative exposure")
    if (e.eligible_exposure > e.monitored_exposure + 1e-12).any() or (
        e.common_exposure > e.eligible_exposure + 1e-12
    ).any():
        raise ValueError("Exposure stages do not reconcile")
    exposure_keys = ["municipality_code", "target_year"]
    for name in ("source_cut", "window"):
        if name in e:
            exposure_keys.append(name)
    if e.duplicated(exposure_keys).any():
        raise ValueError("Duplicate exposure/source-cut keys")
    if any(name not in e for name in exposure_keys if name in {"window", "source_cut"}):
        raise ValueError("Exposure/source-cut identity missing")
    for name in ("source_cut", "window"):
        if name in a and name not in e:
            raise ValueError("Exposure/source-cut identity missing")
    common_keys = [k for k in exposure_keys if k in a]
    if not set(map(tuple, a[common_keys].itertuples(index=False, name=None))) <= set(
        map(tuple, e[common_keys].itertuples(index=False, name=None))
    ):
        raise ValueError("Prediction source-cut lacks exposure")
    prediction_clusters = set(zip(a.municipality_code, a.target_year, strict=True))
    exposure_clusters = set(zip(e.municipality_code, e.target_year, strict=True))
    if not prediction_clusters <= exposure_clusters:
        raise ValueError("Prediction cluster lacks monitored exposure")
    # Every common prediction represents one common municipality-target month.
    counts = a.groupby(["municipality_code", "target_year"]).size()
    by_cluster = e.groupby(["municipality_code", "target_year"])[exposure_columns].sum()
    for key, n in counts.items():
        if float(by_cluster.loc[key, "common_exposure"]) + 1e-12 < n / 12:
            raise ValueError("Common exposure cannot be less than prediction exposure")
    municipalities = sorted(e.municipality_code.astype(str).unique())
    years = sorted(e.target_year.unique())
    m_index, y_index = ({v: i for i, v in enumerate(values)} for values in (municipalities, years))
    tensor = np.zeros((len(municipalities), len(years), 8), dtype=float)
    for f, offset in ((a, 1), (b, 2)):
        for row in f.itertuples(index=False):
            m, y = m_index[str(row.municipality_code)], y_index[row.target_year]
            positive, alert = int(row.onset_target), int(row.alert)
            if offset == 1:
                tensor[m, y, 0] += positive
            tensor[m, y, offset] += positive * alert
            tensor[m, y, offset + 2] += (1 - positive) * alert
    for row in e.itertuples(index=False):
        for offset, column in enumerate(exposure_columns, 5):
            tensor[m_index[str(row.municipality_code)], y_index[row.target_year], offset] += float(
                getattr(row, column)
            )
    totals = tensor.sum(axis=(0, 1))
    onset_years = int((tensor[:, :, 0].sum(axis=0) > 0).sum())
    onset_municipalities = int((tensor[:, :, 0].sum(axis=1) > 0).sum())
    support = onset_years >= 3 and onset_municipalities >= 2
    rng = np.random.default_rng(seed)
    sensitivity, burden, denominators = [], [], []
    joint_exposure_draws: list[list[float]] = []
    for _ in range(draws):
        mw = (
            np.bincount(
                rng.integers(0, len(municipalities), len(municipalities)),
                minlength=len(municipalities),
            )
            if municipalities
            else np.array([])
        )
        yw = (
            np.bincount(rng.integers(0, len(years), len(years)), minlength=len(years))
            if years
            else np.array([])
        )
        sampled = (tensor * (mw[:, None] * yw[None, :])[:, :, None]).sum(axis=(0, 1))
        # The three denominators travel through the same tensor and weights as
        # both arms' onset/false-alert counts, including exposure-only clusters.
        joint_exposure_draws.append(sampled[5:8].tolist())
        if sampled[0] > 0 and support:
            sensitivity.append(float((sampled[1] - sampled[2]) / sampled[0]))
        if sampled[5] > 0:
            burden.append(float((sampled[3] - sampled[4]) / sampled[5]))
            denominators.append(float(sampled[5]))

    def record(values: list[float], estimate: float | None, reason: str) -> dict[str, Any]:
        low, high = np.quantile(values, [0.025, 0.975]) if values else (None, None)
        return {
            "estimate": estimate,
            "lower": float(low) if low is not None else None,
            "upper": float(high) if high is not None else None,
            "valid_draws": len(values),
            "failed_draws": draws - len(values),
            "status": "available" if values else "unavailable",
            "reason": None if values else reason,
        }

    def exposure_audit(offset: int) -> dict[str, Any]:
        values = [row[offset] for row in joint_exposure_draws]
        valid = [v for v in values if v > 0]
        return {
            "minimum": min(valid) if valid else None,
            "maximum": max(valid) if valid else None,
            "valid_draws": len(valid),
            "zero_draws": draws - len(valid),
            "sum": float(sum(values)),
            "resampled": True,
        }

    return {
        "method": "paired_two_way_municipality_year_cluster_percentile",
        "seed": seed,
        "draws": draws,
        "confidence": 0.95,
        "conditional_on_historical_fits": True,
        "onset_years": onset_years,
        "onset_municipalities": onset_municipalities,
        "municipalities": len(municipalities),
        "years": [int(year) for year in years],
        "sensitivity_difference": record(
            sensitivity,
            float((totals[1] - totals[2]) / totals[0]) if totals[0] else None,
            "requires_three_development_years_and_two_municipalities_with_onsets",
        ),
        "false_alert_rate_difference": record(
            burden,
            float((totals[3] - totals[4]) / totals[5]) if totals[5] else None,
            "no_positive_monitored_exposure_resamples",
        ),
        "exposure_draws": {
            "minimum": min(denominators) if denominators else None,
            "maximum": max(denominators) if denominators else None,
            "resampled": True,
            "monitored": exposure_audit(0),
            "eligible": exposure_audit(1),
            "common": exposure_audit(2),
            "paired_cluster_weights_shared": True,
            "joint_draw_sha256": sha256(
                np.asarray(joint_exposure_draws, dtype="<f8").tobytes()
            ).hexdigest(),
            "joint_draw_column_order": ["monitored", "eligible", "common"],
        },
        "limitations": (
            "Three dependent year clusters; pointwise retrospective intervals, "
            "no prospective guarantee."
        ),
    }


def _safe_mean(values: list[float | None]) -> float | None:
    present = [v for v in values if v is not None]
    return float(np.mean(present)) if present else None


def group_summary(
    frame: pd.DataFrame,
    alerts: Any,
    exposures: pd.DataFrame,
    *,
    score: Any = None,
    objective: str = "onset",
) -> dict[str, Any]:
    """Native group metrics and micro/equal-municipality/equal-year summaries."""
    f = frame.copy()
    f.attrs = {}
    f["_alert"] = list(alerts)
    if score is not None:
        f["_score"] = list(score)
    f["target_year"] = f.target_month.astype(str).str[:4].astype(int)
    f["department"] = f.municipality_code.astype(str).str.zfill(5).str[:2]
    e = exposures.copy()
    e["target_year"] = e.target_year.astype(int)
    e["department"] = e.municipality_code.astype(str).str.zfill(5).str[:2]
    profile = "historical_profile" if "historical_profile" in f else "transmission_profile"
    if profile in f:
        f[profile] = f[profile].fillna("profile_unavailable")
    if profile in e:
        e[profile] = e[profile].fillna("profile_unavailable")
    if profile in f and profile not in e:
        # Recover only declared assignments visible on the same municipality/cut.
        # Exposure-only clusters with no assignment remain explicitly unavailable.
        profile_keys = ["municipality_code", "target_year"] + [
            k for k in ("window", "source_cut") if k in f and k in e
        ]
        mapping = f[profile_keys + [profile]].drop_duplicates()
        if mapping.duplicated(profile_keys).any():
            raise ValueError("Ambiguous historical profile membership for exposure cluster")
        e = e.merge(mapping, on=profile_keys, how="left", validate="many_to_one")
        e[profile] = e[profile].fillna("profile_unavailable")

    def known_denominators(subset: pd.DataFrame, ledger: pd.DataFrame) -> None:
        for attr, column in (
            ("eligible_onsets", "known_eligible_onsets"),
            ("covered_onsets", "known_covered_onsets"),
        ):
            if column not in ledger:
                continue
            known = ledger[column]
            if (
                known.isna().any()
                or not np.isfinite(known.to_numpy(dtype=float)).all()
                or known.lt(0).any()
                or not known.eq(np.floor(known)).all()
            ):
                raise ValueError("Known onset ledger must contain nonnegative counts")
            subset.attrs[attr] = int(known.sum())
        if "known_eligible_onsets" in ledger:
            subset.attrs["coverage_denominator_source"] = "pre_gate_ledger_known_eligible_onsets"
        if {"known_eligible_onsets", "known_covered_onsets"} <= set(ledger):
            if (ledger.known_eligible_onsets > ledger.known_covered_onsets).any():
                raise ValueError(
                    "Known covered onset ledger cannot be smaller than eligible onsets"
                )

    known_denominators(f, e)
    dimensions = ["department", "municipality_code", "target_year"]
    if profile in f:
        dimensions.append(profile)
    groups: list[dict[str, Any]] = []
    for dimension in dimensions:
        for value in sorted(
            set(f[dimension].dropna()) | (set(e[dimension].dropna()) if dimension in e else set())
        ):
            subset = f.loc[f[dimension].eq(value)].copy()
            subset.attrs = {}
            if dimension in e:
                ledger = e.loc[e[dimension].eq(value)]
            else:
                ledger = e.loc[e.municipality_code.isin(subset.municipality_code)]
            known_denominators(subset, ledger)
            metric = metrics(
                subset,
                subset._alert,
                float(ledger.monitored_exposure.sum()),
                float(ledger.eligible_exposure.sum()),
                subset._score if score is not None else None,
                objective,
            )
            positive = subset.loc[subset.onset_target.eq(1)]
            groups.append(
                {
                    "dimension": dimension,
                    "group": str(value),
                    "municipalities": int(
                        ledger.loc[ledger.monitored_exposure.gt(0), "municipality_code"].nunique()
                    ),
                    "municipalities_with_common_onsets": int(positive.municipality_code.nunique()),
                    "years_with_onsets": int(positive.target_year.nunique()),
                    "support": "sufficient"
                    if metric["real_onsets"] >= 10
                    and ledger.loc[ledger.monitored_exposure.gt(0), "municipality_code"].nunique()
                    >= 3
                    and positive.target_year.nunique() >= 2
                    else "insufficient",
                    **metric,
                }
            )
    municipal = [r for r in groups if r["dimension"] == "municipality_code"]
    annual = [r for r in groups if r["dimension"] == "target_year"]
    return {
        "groups": groups,
        "micro": metrics(
            f,
            f._alert,
            float(e.monitored_exposure.sum()),
            float(e.eligible_exposure.sum()),
            f._score if score is not None else None,
            objective,
        ),
        "macro": {
            "sensitivity": _safe_mean([r["onset_sensitivity"] for r in municipal]),
            "sensitivity_included_municipalities": sum(r["real_onsets"] > 0 for r in municipal),
            "sensitivity_excluded_municipalities": sum(r["real_onsets"] == 0 for r in municipal),
            "burden": _safe_mean(
                [r["false_alerts_per_monitored_municipality_year"] for r in municipal]
            ),
            "burden_denominator": "equal_municipality_weight_with_positive_monitored_exposure",
            "burden_included_municipalities": sum(
                r["false_alerts_per_monitored_municipality_year"] is not None for r in municipal
            ),
            "burden_excluded_municipalities": sum(
                r["false_alerts_per_monitored_municipality_year"] is None for r in municipal
            ),
            "brier": _safe_mean([r["brier"] for r in municipal]),
            "brier_denominator": "equal_municipality_weight_with_complete_probability_rows",
            "brier_included_municipalities": sum(r["brier"] is not None for r in municipal),
            "brier_excluded_municipalities": sum(r["brier"] is None for r in municipal),
        },
        "equal_year_sensitivity": _safe_mean([r["onset_sensitivity"] for r in annual]),
        "equal_year_sensitivity_included_years": sum(r["real_onsets"] > 0 for r in annual),
        "equal_year_sensitivity_excluded_years": sum(r["real_onsets"] == 0 for r in annual),
    }


def guardrails(
    left: dict[str, Any],
    right: dict[str, Any],
    interval: dict[str, Any] | None = None,
    *,
    budget: float | None = None,
    support: bool = True,
) -> dict[str, Any]:
    """Separate pass/fail/unknown descriptive checks; never approve a champion."""

    def direction(a: Any, b: Any, *, increasing: bool) -> str:
        if not support or a is None or b is None:
            return "unknown"
        good = a >= b if increasing else a <= b
        return "pass" if good else "fail"

    benefit = "unknown"
    if support and interval is not None:
        bound = interval["sensitivity_difference"]
        if bound["lower"] is not None:
            benefit = "pass" if bound["lower"] > 0 else "fail" if bound["upper"] < 0 else "unknown"
    burden = direction(
        left.get("false_alerts_per_monitored_municipality_year"),
        right.get("false_alerts_per_monitored_municipality_year"),
        increasing=False,
    )
    rate = left.get("false_alerts_per_monitored_municipality_year")
    cap = "unknown" if budget is None or rate is None else "fail" if rate > budget else "pass"
    return {
        "aggregate_benefit": benefit,
        "sensitivity_direction": direction(
            left.get("onset_sensitivity"), right.get("onset_sensitivity"), increasing=True
        ),
        "operational_burden": burden,
        "evaluation_cap": cap,
        "calibration": direction(left.get("brier"), right.get("brier"), increasing=False),
        "support": "pass" if support else "unknown",
        "evidence_level": "retrospective_development",
        "formal_equivalence": False,
        "clinical_margin_established": False,
        "automatic_selection": False,
        "recommendation": "candidate_for_further_validation"
        if benefit == "pass" and burden == "pass" and support
        else "inconclusive",
    }
