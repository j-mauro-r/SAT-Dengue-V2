"""Two-phase EXP03 execution: fit/select/freeze, then evaluate; no source I/O."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03_evaluation import (
    BUDGET_UNITS,
    group_summary,
    guardrails,
    metrics,
    paired_interval,
    select_threshold,
)
from sat_dengue.experiments.exp03_features import (
    cohorts,
    coverage,
    coverage_groups,
    exposure_table,
    prepare,
)
from sat_dengue.experiments.exp03_persistence import FrozenCell, freeze_terminal
from sat_dengue.experiments.exp03_revision import cell_grid, validate_design


def require_budget(design: dict[str, Any], *, synthetic: bool = False) -> dict[str, Any]:
    """Fail before private readers/reservations/fits when the research choice is absent."""
    value = design.get("B_primary")
    if value is None:
        raise PermissionError(
            "B_primary is pending; private reads, reservation and scientific fits blocked"
        )
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not np.isfinite(value)
        or value <= 0
    ):
        raise ValueError("B_primary must be a finite positive rate")
    rationale = design.get("budget_rationale")
    if (
        design.get("budget_units") != BUDGET_UNITS
        or not isinstance(rationale, str)
        or not rationale.strip()
    ):
        raise PermissionError("B_primary requires units and an explicit rationale")
    if not synthetic and design.get("synthetic_budget_fixture"):
        raise PermissionError("Synthetic budget fixture cannot authorize scientific execution")
    return {"value": float(value), "units": BUDGET_UNITS, "rationale": design["budget_rationale"]}


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return frame.astype(object).where(pd.notna(frame), None).to_dict(orient="records")


def _ledger(
    prepared: dict, h: int, window: str, role: str, ledgers: dict | None = None
) -> pd.DataFrame:
    table = ledgers[h, window] if ledgers is not None else exposure_table(prepared[h, window][0])
    return table.query("role == @role").copy()


def _sum(ledger: pd.DataFrame, name: str) -> float:
    return float(ledger[name].sum())


def _rows(
    frame: pd.DataFrame, cell: dict, raw: Any, scores: Any, threshold: float | None
) -> pd.DataFrame:
    controls = [
        "municipality_code",
        "year_month",
        "target_month",
        "onset_target",
        "excess_target",
        "eligible_at_t",
        "earlier_onset_t1",
        "transmission_profile",
        "target_year",
        "profile_covered_months",
        "profile_coverage",
        "profile_zero_fraction",
        "profile_mean_count",
        "profile_historical_onsets",
        "profile_onset_evaluable_months",
        "profile_onset_unknown_months",
        "profile_history_start",
        "profile_history_end",
    ]
    f = frame[[c for c in controls if c in frame]].copy()
    f.attrs = {}
    for key in ("cell_id", "variant", "objective", "family", "horizon", "window"):
        f[key] = cell[key]
    f["raw_score"] = np.asarray(raw, dtype=float)
    f["score"] = np.asarray(scores, dtype=float)
    f["threshold"] = threshold
    f["alert"] = False if threshold is None else f.score.ge(threshold)
    f["coverage_status"] = "common_complete_case"
    f["exclusion_reason"] = None
    f["source_cut"] = cell["window"]
    return f


def execute(
    panel: pd.DataFrame,
    contract: dict,
    design: dict,
    *,
    fit: Any,
    calibrate: Any,
    synthetic: bool = False,
    terminal_root: Path | None = None,
    provenance: dict | None = None,
    draws: int = 1000,
) -> dict[str, Any]:
    """All fits are cached once; contrasts, delay and benchmark never refit.

    Native terminal persistence is mandatory. Synthetic marks caller-provided
    generated inputs and counters; it does not turn any real input into a fixture.
    """
    expected = validate_design(design)
    budget = require_budget(design, synthetic=synthetic)
    if synthetic and panel.attrs.get("synthetic_generated") is not True:
        raise PermissionError("Synthetic route requires explicitly generated input fixture")
    if terminal_root is None:
        raise ValueError("A protected terminal_root is required before fitting")
    provenance = dict(provenance or {})
    provenance.update(
        evidence_class="synthetic_generated_data" if synthetic else "authorized_retrospective",
        matrix_sha256=digest(design),
        B_primary=budget,
    )
    prepared = cohorts(panel, contract, design)
    for _, common in prepared.values():
        for frame in common.values():
            frame.attrs = {"profiles": frame.attrs.get("profiles", {})}
    ledgers = {key: exposure_table(parts) for key, (parts, _) in prepared.items()}
    grid = cell_grid(design)
    cache: dict[str, dict] = {}
    children, thresholds, selection_rows, terminals, exposures, coverage_rows = (
        [],
        [],
        [],
        [],
        [],
        [],
    )
    # Phase 1: no evaluation scores/outcomes inspected for model/threshold choice.
    for spec in grid:
        cell = dict(spec, cell_id=digest(spec))
        parts, common = prepared[spec["horizon"], spec["window"]]
        columns = design["variants"][spec["variant"]]
        hashes = {
            r: digest(
                records(f[["municipality_code", "year_month", "onset_target", "excess_target"]])
            )
            for r, f in common.items()
        }
        child = dict(
            cell,
            seed=design["seed"],
            status="non_evaluable",
            reason=None,
            model_fitted=False,
            evidence_type="synthetic_generated_data"
            if synthetic
            else next(w["evidence_type"] for w in design["windows"] if w["id"] == spec["window"]),
            number_of_variables=len(columns),
            predictors_sha256=digest(columns),
            role_sha256=hashes,
            cohort_sha256=hashes["evaluation"],
            coverage={r: len(f) for r, f in common.items()},
            metrics={},
        )
        train, calibration, selection = [common[r] for r in ("train", "calibration", "selection")]
        target = spec["objective"] + "_target"
        if any(f.empty for f in (train, calibration, selection)) or any(
            f[target].nunique() != 2 for f in (train, calibration)
        ):
            child["reason"] = "insufficient_common_role_support_or_classes"
            children.append(child)
            cache[cell["cell_id"]] = {"child": child}
            continue
        model = fit(
            spec["family"],
            train[columns],
            train[target].astype(int),
            design["families"][spec["family"]],
            design["seed"],
        )
        transform = calibrate(
            model.predict(calibration[columns]), calibration[target].astype(int), design["seed"]
        )
        raw = model.predict(selection[columns])
        scores = transform(raw)
        ledger = _ledger(prepared, spec["horizon"], spec["window"], "selection", ledgers)
        policy = select_threshold(
            selection.onset_target, scores, budget, _sum(ledger, "monitored_exposure")
        )
        policy.update(cell)
        thresholds.append(policy)
        selected = _rows(selection, cell, raw, scores, policy["threshold"])
        selected["role"] = "selection"
        selection_rows.extend(records(selected))
        child.update(
            status="evaluable", model_fitted=True, threshold=policy["threshold"], selection=policy
        )
        cache[cell["cell_id"]] = {
            "child": child,
            "model": model,
            "calibrator": transform,
            "columns": columns,
        }
        children.append(child)
        if spec["window"] == "stress_2024":
            profiles = common["train"].attrs.get("profiles", {})
            membership = parts["train"][
                ["municipality_code", "transmission_profile"]
            ].drop_duplicates()
            profiles = {**profiles, "membership": records(membership)}
            terminals.append(
                FrozenCell(
                    cell["cell_id"],
                    cell,
                    model,
                    transform,
                    policy["threshold"],
                    budget["value"],
                    profiles,
                    provenance,
                )
            )
    terminal_ids = [digest(s) for s in grid if s["window"] == "stress_2024"]
    if len(terminals) != len(terminal_ids):
        raise ValueError(
            "Cannot evaluate stress/benchmark without every prespecified terminal cell"
        )
    freeze = freeze_terminal(
        terminals,
        Path(terminal_root),
        terminal_ids,
        provenance,
        validation_frames={
            c.cell_id: prepared[c.metadata["horizon"], c.metadata["window"]][1]["selection"][
                c.predictor.columns
            ]
            for c in terminals
        },
    )
    # Only after the full terminal freeze do any evaluation predictions exist.
    oof, groups, diagnostics = [], [], []
    stale_cache = {h: prepare(panel, contract, h, delay=True) for h in design["horizons"]}
    for child in children:
        if child["status"] != "evaluable":
            continue
        item = cache[child["cell_id"]]
        parts, common = prepared[child["horizon"], child["window"]]
        evaluation = common["evaluation"]
        model, transform, cols = item["model"], item["calibrator"], item["columns"]
        if evaluation.empty:
            child.update(status="non_evaluable", reason="no_common_evaluation_support")
            raw = pd.Series([], index=evaluation.index, dtype=float)
            scores = raw.copy()
        else:
            raw = model.predict(evaluation[cols])
            scores = transform(raw)
        native = _rows(evaluation, child, raw, scores, child["threshold"])
        native["role"] = "evaluation"
        item["predictions"] = native
        ledger = _ledger(prepared, child["horizon"], child["window"], "evaluation", ledgers)
        native.attrs["eligible_onsets"] = int(ledger.known_eligible_onsets.sum())
        native.attrs["covered_onsets"] = int(
            ledger.get("known_covered_onsets", ledger.known_eligible_onsets).sum()
        )
        metric = metrics(
            native,
            native.alert,
            _sum(ledger, "monitored_exposure"),
            _sum(ledger, "eligible_exposure"),
            scores,
            child["objective"],
        )
        metric["raw_probability"] = metrics(
            native,
            native.alert,
            _sum(ledger, "monitored_exposure"),
            _sum(ledger, "eligible_exposure"),
            raw,
            child["objective"],
        )
        child["metrics"] = metric
        child.update(
            average_precision=metric["average_precision"],
            brier=metric["brier"],
            auroc=metric["auroc"],
        )
        summary = group_summary(
            native, native.alert, ledger, score=scores, objective=child["objective"]
        )
        child["summaries"] = {k: v for k, v in summary.items() if k != "groups"}
        for row in summary["groups"]:
            groups.append(
                {
                    **{
                        k: child[k]
                        for k in ("cell_id", "variant", "objective", "family", "horizon", "window")
                    },
                    **row,
                }
            )
        oof.extend(records(native))
        for category in ("onset", "continuation", "no_excess"):
            if category == "onset":
                mask = native.onset_target.eq(1)
            elif category == "continuation":
                mask = native.excess_target.eq(1) & native.onset_target.eq(0)
            else:
                mask = native.excess_target.eq(0)
            diagnostics.append(
                {
                    **{
                        k: child[k]
                        for k in ("cell_id", "variant", "objective", "family", "horizon", "window")
                    },
                    "diagnostic": "error_type",
                    "category": category,
                    "rows": int(mask.sum()),
                    "alerts": int(native.loc[mask, "alert"].sum()),
                    "status": "not_applicable"
                    if category == "continuation" and child["horizon"] == 1
                    else "descriptive",
                }
            )
        if child["variant"] in design["delay_variants"] and child["objective"] == "onset":
            stale = stale_cache[child["horizon"]].copy()
            stale.attrs = {}
            stale = stale.set_index(["municipality_code", "year_month"]).reindex(
                pd.MultiIndex.from_frame(evaluation[["municipality_code", "year_month"]])
            )
            stale.index = evaluation.index
            valid = stale[cols].notna().all(axis=1)
            delayed_scores = (
                transform(model.predict(stale.loc[valid, cols]))
                if valid.any()
                else pd.Series([], dtype=float)
            )
            delayed_alerts = (
                False if child["threshold"] is None else delayed_scores.ge(child["threshold"])
            )
            support = (
                model.audit_support(stale.loc[valid, cols])
                if valid.any()
                else pd.DataFrame({"unsupported": []})
            )
            same = native.loc[valid].copy()
            same.attrs = {}
            delayed_metric = metrics(
                same,
                np.repeat(False, len(same)) if child["threshold"] is None else delayed_alerts,
                _sum(ledger, "monitored_exposure"),
                _sum(ledger, "eligible_exposure"),
                delayed_scores,
                child["objective"],
            )
            baseline_metric = metrics(
                same,
                same.alert,
                _sum(ledger, "monitored_exposure"),
                _sum(ledger, "eligible_exposure"),
                same.score,
                child["objective"],
            )
            diagnostics.append(
                {
                    **{
                        k: child[k]
                        for k in ("cell_id", "variant", "objective", "family", "horizon", "window")
                    },
                    "diagnostic": "conditional_stale_feature_stress",
                    "rows": int(valid.sum()),
                    "abstentions": int((~valid).sum()),
                    "unsupported_rows": int(support.unsupported.sum()),
                    "baseline": baseline_metric,
                    "delayed": delayed_metric,
                    "eligibility_assumption": "Y(T) independently known; availability unverified",
                    "effective_source_months": records(
                        stale_cache[child["horizon"]]
                        .attrs["source_months"]
                        .loc[evaluation.index, cols]
                    ),
                }
            )
            diagnostics.append(
                {
                    "cell_id": child["cell_id"],
                    "diagnostic": "strict_current_unavailable",
                    "status": "unable_to_issue",
                    "abstentions": len(native),
                    "coverage": 0,
                    "reason": "Y(T) unavailable; gate cannot be replaced by Y(T-1)",
                }
            )
    feature_provenance = []
    for (h, w), (parts, _) in prepared.items():
        for role, part in parts.items():
            latest = part.attrs["source_months"]
            events = part.attrs["source_event_months"]
            for idx in part.index:
                feature_provenance.append(
                    {
                        "municipality_code": part.at[idx, "municipality_code"],
                        "year_month": part.at[idx, "year_month"],
                        "target_month": part.at[idx, "target_month"],
                        "horizon": h,
                        "window": w,
                        "role": role,
                        "source_months": latest.loc[idx].to_dict(),
                        "source_event_months": events.loc[idx].to_dict(),
                        "publication_availability": "unverified retrospective event-month proxy",
                    }
                )
        ledger = exposure_table(parts)
        ledger["horizon"] = h
        exposures.extend(records(ledger))
        for variant, cols in design["variants"].items():
            for role, part in parts.items():
                coverage_rows.append(
                    {
                        "variant": variant,
                        "horizon": h,
                        "window": w,
                        "role": role,
                        "dimension": "all",
                        "group": "all",
                        **part.attrs.get("coverage", {}),
                        **coverage(part, cols, design["predictors"]),
                    }
                )
                coverage_rows.extend(
                    {"variant": variant, "horizon": h, "window": w, "role": role, **audit}
                    for audit in coverage_groups(part, cols, design["predictors"])
                )
    contrasts = _contrasts(cache, prepared, design, budget["value"], draws, ledgers)
    native_files = {
        str(p.relative_to(terminal_root)): p.read_bytes()
        for p in Path(terminal_root).rglob("*")
        if p.is_file()
    }
    count = sum(c["model_fitted"] for c in children)
    if len(children) != expected:
        raise ValueError("Expanded grid incomplete")
    phase_counts = {}
    for phase, windows in (
        (
            "development_oof",
            {
                w["id"]
                for w in design["windows"]
                if w["evidence_type"] == "retrospective_development"
            },
        ),
        ("terminal_stress_2024", {"stress_2024"}),
    ):
        executed = sum(c["model_fitted"] for c in children if c["window"] in windows)
        phase_counts[phase] = {
            "model_fits": executed,
            "preparer_fits": executed,
            "calibrator_fits": executed,
            "searches": 0,
            "threshold_selections": sum(t["window"] in windows for t in thresholds),
            "kind": "synthetic_generated_data" if synthetic else "authorized_retrospective",
        }
    phase_counts["consumed_2025_benchmark"] = {
        "model_fits": 0,
        "preparer_fits": 0,
        "calibrator_fits": 0,
        "searches": 0,
        "threshold_selections": 0,
        "kind": "inference_only",
    }
    return {
        "schema": "exp03-result-v2",
        "experiment_id": "EXP03",
        "synthetic": synthetic,
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "B_primary": budget,
        "real_model_fits": 0 if synthetic else count,
        "real_preparer_refits": 0 if synthetic else count,
        "calibrator_fits": 0 if synthetic else count,
        "synthetic_interface_fits": count if synthetic else 0,
        "synthetic_calibrator_fits": count if synthetic else 0,
        "synthetic_preparer_refits": count if synthetic else 0,
        "execution_counters": phase_counts,
        "searches": 0,
        "threshold_selections": len(thresholds),
        "children": children,
        "contrasts": contrasts,
        "primary_contrasts": [r for r in contrasts if r["tier"] == "primary"],
        "secondary_contrasts": [r for r in contrasts if r["tier"] != "primary"],
        "oof_predictions": oof,
        "selection_predictions": selection_rows,
        "thresholds": thresholds,
        "performance_by_group": groups,
        "coverage_and_exclusions": coverage_rows,
        "exposure_by_cluster": exposures,
        "feature_provenance": feature_provenance,
        "error_types_and_delay": diagnostics,
        "transport_2024_2025": [
            {
                "year": 2025,
                "status": "not_evaluable",
                "reason": "benchmark coverage/maturity admission not yet supplied",
                "evidence_type": "consumed_retrospective_benchmark",
                "model_fits": 0,
                "preparer_fits": 0,
                "calibrator_fits": 0,
                "threshold_selections": 0,
                "searches": 0,
            }
        ],
        "terminal_manifest": freeze,
        "model_artifacts": native_files,
        "decision_candidates": [r["decision"] for r in contrasts],
    }


def _contrasts(
    cache: dict,
    prepared: dict,
    design: dict,
    budget: float,
    draws: int,
    ledgers: dict | None = None,
) -> list[dict]:
    output = []
    comparisons = [
        dict(c, left_objective="onset", right_objective="onset") for c in design["contrasts"]
    ]
    comparisons.extend(
        {
            "id": "O" + str(i),
            "left": v,
            "right": v,
            "tier": "objective_control",
            "left_objective": "onset",
            "right_objective": "excess",
        }
        for i, v in enumerate(design["excess_controls"], 1)
    )
    for comparison in comparisons:
        for family in design["families"]:
            for horizon in design["horizons"]:
                if comparison["tier"] == "objective_control" and horizon != 2:
                    continue
                for window, cuts in [
                    (
                        "pooled_development",
                        [
                            w["id"]
                            for w in design["windows"]
                            if w["evidence_type"] == "retrospective_development"
                        ],
                    ),
                    ("stress_2024", ["stress_2024"]),
                ]:
                    sides = []
                    ids = []
                    for side in ("left", "right"):
                        selected = [
                            item
                            for item in cache.values()
                            if item["child"]["family"] == family
                            and item["child"]["horizon"] == horizon
                            and item["child"]["window"] in cuts
                            and item["child"]["variant"] == comparison[side]
                            and item["child"]["objective"] == comparison[side + "_objective"]
                        ]
                        ids.append([item["child"]["cell_id"] for item in selected])
                        frames = []
                        for item in selected:
                            if "predictions" in item:
                                frame = item["predictions"].copy()
                                frame.attrs = {}
                                frames.append(frame)
                        sides.append(
                            pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
                        )
                    identity = {
                        "contrast_id": comparison["id"],
                        "left_variant": comparison["left"],
                        "right_variant": comparison["right"],
                        "left_objective": comparison["left_objective"],
                        "right_objective": comparison["right_objective"],
                        "family": family,
                        "horizon": horizon,
                        "window": window,
                        "source_cuts": cuts,
                        "left_cells": ids[0],
                        "right_cells": ids[1],
                        "tier": comparison["tier"],
                    }
                    if any(f.empty for f in sides):
                        output.append(
                            {
                                **identity,
                                "status": "non_evaluable",
                                "reason": "missing_cell_predictions",
                                "decision": {
                                    "recommendation": "inconclusive",
                                    "automatic_selection": False,
                                },
                            }
                        )
                        continue
                    ledger = pd.concat(
                        [_ledger(prepared, horizon, w, "evaluation", ledgers) for w in cuts],
                        ignore_index=True,
                    )
                    summary = [
                        group_summary(
                            f,
                            f.alert,
                            ledger,
                            score=f.score,
                            objective=comparison[side + "_objective"],
                        )
                        for f, side in zip(sides, ("left", "right"), strict=True)
                    ]
                    m = [s["micro"] for s in summary]
                    interval = (
                        paired_interval(
                            sides[0], sides[1], ledger, seed=design["seed"], draws=draws
                        )
                        if window == "pooled_development"
                        else {
                            "status": "retrospective_stress_no_development_interval",
                            **{
                                key: {
                                    "estimate": None,
                                    "lower": None,
                                    "upper": None,
                                    "valid_draws": 0,
                                    "failed_draws": 0,
                                    "status": "not_applicable_stress",
                                }
                                for key in ("sensitivity_difference", "false_alert_rate_difference")
                            },
                        }
                    )
                    decision = guardrails(m[0], m[1], interval, budget=budget)
                    if comparison["left_objective"] != comparison["right_objective"]:
                        decision["calibration"] = "unknown"
                        decision["calibration_limitation"] = (
                            "different_probability_targets_not_comparable"
                        )
                    if window == "stress_2024":
                        decision.update(
                            aggregate_benefit="unknown",
                            evidence_level="retrospective_stress",
                            recommendation="inconclusive",
                        )
                    subgroup = []
                    for a, b in zip(summary[0]["groups"], summary[1]["groups"], strict=True):
                        if a["dimension"] in ("department", "transmission_profile"):
                            subgroup.append(
                                {
                                    "dimension": a["dimension"],
                                    "group": a["group"],
                                    **guardrails(
                                        a,
                                        b,
                                        budget=budget,
                                        support=a["support"] == b["support"] == "sufficient",
                                    ),
                                }
                            )
                    if comparison["left_objective"] != comparison["right_objective"]:
                        for row in subgroup:
                            row["calibration"] = "unknown"
                            row["calibration_limitation"] = (
                                "different_probability_targets_not_comparable"
                            )
                    for dim, key in [
                        ("department", "department_guardrail"),
                        ("transmission_profile", "profile_guardrail"),
                    ]:
                        checks = [r for r in subgroup if r["dimension"] == dim]
                        decision[key] = (
                            "fail"
                            if any(
                                r["sensitivity_direction"] == "fail"
                                or r["operational_burden"] == "fail"
                                for r in checks
                            )
                            else "unknown"
                            if not checks or any(r["support"] == "unknown" for r in checks)
                            else "pass"
                        )
                    if any(
                        decision[k] != "pass" for k in ("department_guardrail", "profile_guardrail")
                    ):
                        decision["recommendation"] = "inconclusive"
                    delta = {
                        key: None if any(v[key] is None for v in m) else m[0][key] - m[1][key]
                        for key in (
                            "onset_sensitivity",
                            "false_alerts_per_monitored_municipality_year",
                        )
                    }
                    output.append(
                        {
                            **identity,
                            "status": "evaluable",
                            "left_metrics": m[0],
                            "right_metrics": m[1],
                            "paired_sensitivity_difference": delta["onset_sensitivity"],
                            "paired_burden_difference": delta[
                                "false_alerts_per_monitored_municipality_year"
                            ],
                            "paired_interval": interval,
                            "decision": decision,
                            "guardrails": subgroup,
                            "per_year": [
                                {"year": a["group"], "left": a, "right": b}
                                for a, b in zip(
                                    summary[0]["groups"], summary[1]["groups"], strict=True
                                )
                                if a["dimension"] == "target_year"
                            ],
                        }
                    )
    return output
