"""EXP04 policy phases over supplied frozen scores; no predictor operation or I/O."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp03_1_reporting import _frame_state, _restore_frame
from sat_dengue.experiments.exp04 import (
    apply_calibrator,
    calibration_window,
    evaluate_frozen,
    fit_calibrator,
    temporal_roles,
    threshold_policy,
)
from sat_dengue.experiments.exp04_baseline import paired_support
from sat_dengue.experiments.exp04_contract import digest
from sat_dengue.experiments.exp04_runner import compare_policies

DIMENSIONS = ("cut", "family", "horizon", "objective")


def group_id(group: dict[str, Any]) -> str:
    return digest({name: group[name] for name in DIMENSIONS})


def support(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": len(frame),
        "positives": int(frame.truth.sum()),
        "negatives": int(len(frame) - frame.truth.sum()),
        "municipalities": int(frame.municipality_code.nunique()),
        "months": int(frame.target_month.nunique()),
        "exposure": len(frame) / 12,
    }


def selection_blocks(frame: pd.DataFrame, horizon: int, p: dict[str, Any]) -> pd.DataFrame:
    """Assign the frozen ISSUE-month blocks, independently of labels and scores."""
    result = frame.copy()
    months = pd.to_datetime(result.forecast_issue_date).dt.month
    blocks = p["C2_issue_month_blocks"][str(horizon)]
    if not months.isin([month for block in blocks for month in block]).all():
        raise ValueError("Selection issue outside frozen C2 calendar")
    result["selection_block"] = np.where(months.isin(blocks[0]), "1", "2")
    return result


def summarize(
    rows: pd.DataFrame,
    threshold: float | None,
    objective: str,
    p: dict[str, Any],
    historical_exposure: float | None = None,
) -> dict[str, Any]:
    # Metrics consume the already stored probabilities and alerts, without refitting.
    supplied = rows.copy()
    supplied["raw_score"] = supplied.score
    checked, metric = evaluate_frozen(
        supplied,
        {"method": "identity"},
        threshold,
        bins=p["ECE_bins"],
        objective=objective,
        historical_exposure=historical_exposure,
    )
    if not np.array_equal(checked.alert.to_numpy(), rows.alert.to_numpy()):
        raise ValueError("Saved alerts differ from frozen threshold")
    metric["TN"] = int((rows.truth.eq(0) & ~rows.alert).sum())
    metric["support"]["months"] = int(rows.target_month.nunique())
    metric["support"]["negatives"] = int(rows.truth.eq(0).sum())
    return metric


def measured(
    rows: pd.DataFrame,
    state: dict[str, Any],
    decision: dict[str, Any],
    inputs: dict[str, Any],
    p: dict[str, Any],
) -> dict[str, Any]:
    group = inputs["group"]
    metric = summarize(
        rows, decision["threshold"], group["objective"], p, inputs["historical_exposure"]
    )
    selection = _restore_frame(inputs["selection"])
    selected_score = (
        selection.score
        if decision["policy"] == "historical_frozen"
        else apply_calibrator(selection, state)
    )
    alert = False if decision["threshold"] is None else selected_score.ge(decision["threshold"])
    rate = float((selection.truth.eq(0) & alert).sum()) / (len(selection) / 12)
    metric["selection_common_FA_rate"] = rate
    metric["selection_evaluation_drift"] = metric["common_FA_rate"] - rate
    strata = {}
    for code, name in p["territories"].items():
        part = rows.loc[rows.municipality_code.str.startswith(code)]
        strata[name] = (
            summarize(part, decision["threshold"], group["objective"], p)
            if not part.empty
            else {"status": "NOT_EVALUABLE", "reason": "territory_support"}
        )
    if not rows.municipality_code.str[:2].isin(p["territories"]).all():
        raise ValueError("Unknown EXP04 territory")
    return {"metrics": metric, "strata": strata, "predictions": _frame_state(rows)}


def unavailable(group: dict[str, Any], arm: str, reason: str) -> dict[str, Any]:
    return {
        **{k: group[k] for k in DIMENSIONS},
        "arm": arm,
        "group_id": group_id(group),
        "status": "NOT_EVALUABLE",
        "reason": reason,
    }


def reference(inputs: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    group = inputs["group"]
    rows = _restore_frame(inputs["evaluation"])
    # A0 uses saved probabilities/alerts, not another application of its calibrator.
    if not {"score", "alert"} <= set(rows):
        raise ValueError("A0 requires original saved probabilities and alerts")
    decision = {"threshold": inputs["reference_threshold"], "policy": "historical_frozen"}
    return {
        **unavailable(group, "A0", ""),
        "status": "evaluable",
        "reason": None,
        "months": "original",
        "method": "original",
        "selector": "historical_frozen",
        "calibrator": inputs["reference_calibrator"],
        "threshold": decision,
        "support": {"evaluation": support(rows)},
        "historical_roles": inputs["historical_roles"],
        **measured(rows, inputs["reference_calibrator"], decision, inputs, p),
    }


def policy_cell(
    inputs: dict[str, Any],
    arm: str,
    months: int,
    method: str,
    selector: str,
    p: dict[str, Any],
    counters: dict[str, int],
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    group = inputs["group"]
    if group["objective"] != "onset":
        raise ValueError("Excess control never enters onset policy selection")
    cal, info = calibration_window(
        _restore_frame(inputs["history"]),
        months=months,
        last_mature_month=group["roles"]["calibration"][1],
        cutoff=group["calibration_cutoff"],
    )
    selection = selection_blocks(_restore_frame(inputs["selection"]), group["horizon"], p)
    evaluation = _restore_frame(inputs["evaluation"])
    base = {
        **unavailable(group, arm, ""),
        "months": months,
        "method": method,
        "calibrator_fit_performed": False,
        "threshold_selection_performed": False,
        "selector": selector,
        "support": {
            "calibration": info,
            "selection": support(selection),
            "selection_blocks": {
                str(b): support(part) for b, part in selection.groupby("selection_block")
            },
            "evaluation": support(evaluation),
        },
    }
    if info["status"] != "evaluable":
        return {**base, "reason": info["reason"]}
    temporal_roles(
        cal,
        selection,
        evaluation,
        horizon=group["horizon"],
        calibration_cutoff=group["calibration_cutoff"],
        decision_date=group["decision_date"],
    )
    if state is None:
        state = fit_calibrator(
            cal,
            method="sigmoid" if method == "original" else method,
            seed=p["calibration"]["sigmoid"]["seed"],
            minimum_class_support=p["calibration"]["isotonic"]["minimum_positives"],
        )
        if state.get("status") == "NOT_EVALUABLE":
            return {**base, "reason": state["reason"]}
        counters["calibrator_fits"] += 1
        base["calibrator_fit_performed"] = True
    selection["score"] = apply_calibrator(selection, state)
    decision = threshold_policy(selection, policy=selector)
    if decision.get("status") == "NOT_EVALUABLE":
        return {**base, "reason": decision["reason"], "calibrator": state}
    counters["threshold_selections"] += 1
    base["threshold_selection_performed"] = True
    rows, _ = evaluate_frozen(
        evaluation, state, decision["threshold"], bins=p["ECE_bins"], objective="onset"
    )
    return {
        **base,
        "status": "evaluable",
        "reason": None,
        "calibrator": state,
        "threshold": decision,
        "calibration_cutoff": group["calibration_cutoff"],
        "decision_date": group["decision_date"],
        **measured(rows, state, decision, inputs, p),
    }


def alias(cell: dict[str, Any], arm: str) -> dict[str, Any]:
    return {
        **deepcopy(cell),
        "arm": arm,
        "reused_policy_arm": cell["arm"],
        "calibrator_fit_performed": False,
        "threshold_selection_performed": False,
    }


def choose(cells: list[dict[str, Any]], phase: str, p: dict[str, Any]) -> dict[str, Any]:
    """Pure deterministic selection. Stress and territories cannot enter its inputs."""
    arms = {"A": ["A1", "A2", "A3"], "B": ["B0", "B1", "B2"], "C": ["C0", "C1", "C2"]}[phase]
    control = {"A": "A0", "B": "B0", "C": "C0"}[phase]
    dev = {
        (cell["arm"], int(cell["cut"][-4:])): cell
        for cell in cells
        if cell["objective"] == "onset" and int(cell["cut"][-4:]) in p["selection"]["years"]
    }
    decisions = []
    for rank, arm in enumerate(arms):
        years = [
            year
            for year in p["selection"]["years"]
            if dev.get((arm, year), {}).get("status") == "evaluable"
            and dev.get((control, year), {}).get("status") == "evaluable"
        ]
        candidate = [dev[arm, year]["metrics"] for year in years]
        controls = [dev[control, year]["metrics"] for year in years]
        positives = sum(m["positives"] for m in candidate)
        control_positives = sum(m["positives"] for m in controls)
        sensitivity = sum(m["detected"] for m in candidate) / positives if positives else None
        baseline = (
            sum(m["detected"] for m in controls) / control_positives if control_positives else None
        )
        paired = all(
            paired_support(
                _restore_frame(dev[control, year]["predictions"]),
                _restore_frame(dev[arm, year]["predictions"]),
            )["status"]
            == "evaluable"
            for year in years
        )
        eligible = (
            bool(years and positives and control_positives and paired)
            and all(m["common_FA_rate"] <= p["B_primary"] for m in candidate)
            and sensitivity is not None
            and baseline is not None
            and (sensitivity - baseline >= p["sensitivity_noninferiority_margin"])
        )
        rows = sum(m["rows"] for m in candidate)
        decisions.append(
            {
                "arm": arm,
                "eligible": eligible,
                "development_years": years,
                "excluded_years": [y for y in p["selection"]["years"] if y not in years],
                "maximum_annual_budget_excess": max(
                    (m["budget_excess"] for m in candidate), default=None
                ),
                "pooled_sensitivity": sensitivity,
                "control_pooled_sensitivity": baseline,
                "pooled_Brier": sum(m["brier"] * m["rows"] for m in candidate) / rows
                if rows
                else None,
                "annual_FA_rate": {str(y): dev[arm, y]["metrics"]["common_FA_rate"] for y in years},
                "conservative_rank": rank,
            }
        )
    eligible_options = [item for item in decisions if item["eligible"]]

    def key(item: dict[str, Any]) -> tuple[Any, ...]:
        common = (item["maximum_annual_budget_excess"], -item["pooled_sensitivity"])
        return (
            *common,
            *([item["pooled_Brier"]] if phase == "B" else []),
            item["conservative_rank"],
        )

    selected = min(eligible_options, key=key)["arm"] if eligible_options else None
    return {
        "phase": phase,
        "status": "evaluable" if selected else "NOT_EVALUABLE",
        "selected": selected,
        "candidates": decisions,
        "selection_years": p["selection"]["years"],
    }


def phases(
    inputs: dict[str, Any],
    phase: str,
    decisions: dict[str, Any],
    existing: list[dict[str, Any]],
    p: dict[str, Any],
    counters: dict[str, int],
) -> list[dict[str, Any]]:
    group = inputs["group"]
    if phase == "A":
        return [
            reference(inputs, p),
            *[
                policy_cell(inputs, f"A{i}", months, "original", "C0", p, counters)
                for i, months in enumerate((12, 24, 36), 1)
            ],
            unavailable(group, "A4", "expanding_origin_undefined"),
        ]
    window = decisions["A"]["selected"]
    arms = ("B0", "B1", "B2") if phase == "B" else ("C0", "C1", "C2")
    if window is None or (phase == "C" and decisions["B"]["selected"] is None):
        return [unavailable(group, arm, "no_eligible_development_policy") for arm in arms]
    months = {"A1": 12, "A2": 24, "A3": 36}[window]
    by_arm = {c["arm"]: c for c in existing}
    if phase == "B":
        return [
            alias(by_arm[window], "B0"),
            policy_cell(inputs, "B1", months, "sigmoid", "C0", p, counters),
            policy_cell(inputs, "B2", months, "isotonic", "C0", p, counters),
        ]
    selected = by_arm[decisions["B"]["selected"]]
    if selected["status"] != "evaluable":
        return [unavailable(group, arm, "selected_calibrator_has_no_cell_support") for arm in arms]
    return [
        alias(selected, "C0"),
        *[
            policy_cell(
                inputs,
                arm,
                months,
                selected["method"],
                arm,
                p,
                counters,
                state=selected["calibrator"],
            )
            for arm in ("C1", "C2")
        ],
    ]


def describe(cells: list[dict[str, Any]], p: dict[str, Any]) -> dict[str, Any]:
    """Paired effects, interannual load and territorial limits; no inference."""
    indexed = {(c["group_id"], c["arm"]): c for c in cells}
    contrasts = []
    for question, pairs in p["contrasts"].items():
        for candidate, control in pairs:
            for cell in cells:
                if cell["arm"] != candidate or cell["objective"] != "onset":
                    continue
                ref = indexed.get((cell["group_id"], control))
                record = {k: cell[k] for k in DIMENSIONS}
                record.update(
                    question=question,
                    candidate=candidate,
                    reference=control,
                    classification="DESCRIPTIVE_ONLY",
                    uncertainty="UNAVAILABLE",
                )
                if cell["status"] != "evaluable" or ref is None or ref["status"] != "evaluable":
                    contrasts.append({**record, "status": "NOT_EVALUABLE", "reason": "arm_support"})
                    continue
                left, right = (_restore_frame(c["predictions"]) for c in (ref, cell))
                effect = compare_policies(left, right, ref["metrics"], cell["metrics"])
                effect["classification"] = "DESCRIPTIVE_ONLY"
                territorial: dict[str, Any] = {}
                deteriorated = False
                for name in p["territories"].values():
                    a, b = ref["strata"][name], cell["strata"][name]
                    if a["status"] != "evaluable" or b["status"] != "evaluable":
                        territorial[name] = {"status": "NOT_EVALUABLE"}
                        continue
                    ds = (
                        None
                        if a["sensitivity"] is None or b["sensitivity"] is None
                        else b["sensitivity"] - a["sensitivity"]
                    )
                    df = b["common_FA_rate"] - a["common_FA_rate"]
                    bad = (ds is not None and ds < 0) or df > 0
                    deteriorated |= bad
                    territorial[name] = {
                        "sensitivity_delta": ds,
                        "FA_rate_delta": df,
                        "deterioration": bad,
                    }
                contrasts.append(
                    {
                        **record,
                        **effect,
                        "territories": territorial,
                        "interpretation": "PARCIAL / SIN APROBACIÓN"
                        if deteriorated
                        else "DESCRIPTIVE_ONLY / SIN APROBACIÓN",
                    }
                )
    trajectories = []
    for family in p["families"]:
        for horizon in (1, 2):
            for arm in p["arms"]:
                subset = [
                    c
                    for c in cells
                    if c["family"] == family
                    and c["horizon"] == horizon
                    and c["objective"] == "onset"
                    and c["arm"] == arm
                    and c["status"] == "evaluable"
                ]
                rates = {c["cut"]: c["metrics"]["common_FA_rate"] for c in subset}
                trajectories.append(
                    {
                        "family": family,
                        "horizon": horizon,
                        "arm": arm,
                        "annual_FA_rate": rates,
                        "range": max(rates.values()) - min(rates.values()) if rates else None,
                    }
                )
    return {
        "contrasts": contrasts,
        "transport": trajectories,
        "hypotheses": {
            h: {
                "classification": "DESCRIPTIVE_ONLY",
                "uncertainty": "UNAVAILABLE",
                "contrasts": sum(c["question"] == h for c in contrasts),
            }
            for h in ("H1", "H1a", "H1b", "H1c")
        },
    }


def run_phases(inputs: dict[str, Any], p: dict[str, Any]) -> dict[str, Any]:
    """Freeze all six onset trajectories before touching any stress evaluation."""
    counters = {
        "predictor_fits": 0,
        "calibrator_fits": 0,
        "threshold_selections": 0,
        "mlflow_writes": 0,
    }
    cells: list[dict[str, Any]] = []
    frozen = {}
    for family in p["families"]:
        for horizon in (1, 2):
            development = [
                v
                for v in inputs.values()
                if v["group"]["family"] == family
                and v["group"]["horizon"] == horizon
                and v["group"]["objective"] == "onset"
                and int(v["group"]["cut"][-4:]) in p["selection"]["years"]
            ]
            decisions: dict[str, Any] = {}
            current: list[dict[str, Any]] = []
            for phase in ("A", "B", "C"):
                for source in development:
                    existing = [c for c in current if c["group_id"] == group_id(source["group"])]
                    current.extend(phases(source, phase, decisions, existing, p, counters))
                decisions[phase] = choose(current, phase, p)
            cells.extend(current)
            frozen[f"{family}/T+{horizon}"] = decisions
    freeze_id = digest(frozen)
    for source in inputs.values():
        group = source["group"]
        if group["objective"] == "excess_control":
            control = reference(source, p)
            control["control_report"] = "separate_frozen_excess_no_onset_budget_or_selection"
            cells.append(control)
        elif int(group["cut"][-4:]) == 2024:
            decisions = frozen[f"{group['family']}/T+{group['horizon']}"]
            current = []
            for phase in ("A", "B", "C"):
                current.extend(phases(source, phase, decisions, current, p, counters))
            selected = next((c for c in current if c["arm"] == decisions["C"]["selected"]), None)
            composed = (
                alias(selected, "D")
                if selected is not None
                else unavailable(group, "D", "no_eligible_development_composition")
            )
            composed.update(evidence="DESCRIPTIVE_STRESS_ONLY", freeze_id=freeze_id)
            current.append(composed)
            cells.extend(current)
    identities = []
    for cell in cells:
        cell["cell_id"] = digest({k: cell[k] for k in (*DIMENSIONS, "arm")})
        identities.append(cell["cell_id"])
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate scientific cell")
    equality = []
    for source in inputs.values():
        pair = {
            c["arm"]: c
            for c in cells
            if c["group_id"] == group_id(source["group"]) and c["arm"] in ("B0", "B1")
        }
        if len(pair) == 2 and all(c["status"] == "evaluable" for c in pair.values()):
            equality.append(
                {
                    "group_id": group_id(source["group"]),
                    "B0_B1_identical": all(
                        pair["B0"][k] == pair["B1"][k]
                        for k in ("calibrator", "threshold", "predictions", "metrics")
                    ),
                }
            )
    return {
        "cells": cells,
        "frozen": frozen,
        "freeze_id": freeze_id,
        "B0_B1_identity": equality,
        "execution_counters": counters,
        **describe(cells, p),
    }


def validate_science(result: dict[str, Any], p: dict[str, Any]) -> None:
    """Recompute from saved probabilities, never fitting a calibrator or predictor."""
    cells, inputs = result["cells"], result["inputs"]
    if (
        result.get("G5") != "NOT_APPROVED"
        or result.get("champion") != "not_selected"
        or result.get("uncertainty") != "UNAVAILABLE"
        or result.get("evidence") != "DESCRIPTIVE_ONLY"
        or result.get("year_2025") != "NOT_EVALUABLE"
    ):
        raise ValueError("Scientific approval, uncertainty or evidence boundary differs")
    expected_inventory = set()
    for identity, source in inputs.items():
        group = source["group"]
        if identity != group_id(group) or int(group["cut"][-4:]) not in (2020, 2021, 2022, 2024):
            raise ValueError("Scientific input group or 2025 boundary differs")
        arms = ["A0"] if group["objective"] == "excess_control" else list(p["arms"])
        for arm in arms:
            if arm != "D" or int(group["cut"][-4:]) == 2024:
                expected_inventory.add((identity, arm))
    indexed = {(cell["group_id"], cell["arm"]): cell for cell in cells}
    if len(indexed) != len(cells) or set(indexed) != expected_inventory:
        raise ValueError("Scientific arm/cell inventory differs")
    frozen = {}
    for family in p["families"]:
        for horizon in (1, 2):
            trajectory = [
                c
                for c in cells
                if c["family"] == family and c["horizon"] == horizon and c["objective"] == "onset"
            ]
            frozen[f"{family}/T+{horizon}"] = {
                phase: choose(trajectory, phase, p) for phase in ("A", "B", "C")
            }
    if frozen != result["frozen"] or digest(frozen) != result["freeze_id"]:
        raise ValueError("Deterministic development selection or freeze differs")
    for cell in cells:
        source = inputs[cell["group_id"]]
        group, arm = source["group"], cell["arm"]
        if any(cell[k] != group[k] for k in DIMENSIONS) or cell["cell_id"] != digest(
            {k: cell[k] for k in (*DIMENSIONS, "arm")}
        ):
            raise ValueError("Scientific cell provenance differs")
        by_arm = {a: indexed[cell["group_id"], a] for g, a in indexed if g == cell["group_id"]}
        if arm == "A0":
            expected = reference(source, p)
            for name in (
                "predictions",
                "metrics",
                "strata",
                "calibrator",
                "threshold",
                "support",
                "historical_roles",
            ):
                if cell.get(name) != expected.get(name):
                    raise ValueError("Frozen A0 or excess control changed")
            continue
        if arm == "A4":
            if cell["status"] != "NOT_EVALUABLE" or cell["reason"] != "expanding_origin_undefined":
                raise ValueError("A4 must remain NOT_EVALUABLE")
            continue
        decisions = frozen[f"{group['family']}/T+{group['horizon']}"]
        if arm == "D":
            selected = decisions["C"]["selected"]
            if (
                cell["freeze_id"] != result["freeze_id"]
                or cell["evidence"] != "DESCRIPTIVE_STRESS_ONLY"
            ):
                raise ValueError("D is descriptive stress after freeze only")
            if selected is None:
                if cell["status"] != "NOT_EVALUABLE":
                    raise ValueError("D cannot invent a fallback")
            else:
                for name in (
                    "status",
                    "predictions",
                    "metrics",
                    "strata",
                    "calibrator",
                    "threshold",
                ):
                    if cell.get(name) != by_arm[selected].get(name):
                        raise ValueError("D differs from frozen development composition")
            continue
        fit_expected = arm in ("A1", "A2", "A3", "B1", "B2") and cell["status"] == "evaluable"
        threshold_expected = (
            arm in ("A1", "A2", "A3", "B1", "B2", "C1", "C2") and cell["status"] == "evaluable"
        )
        if (
            cell.get("calibrator_fit_performed", False) != fit_expected
            or cell.get("threshold_selection_performed", False) != threshold_expected
        ):
            raise ValueError("Scientific fit/selection operation provenance differs")
        selected_window = decisions["A"]["selected"]
        selected_calibrator = decisions["B"]["selected"]
        if arm.startswith(("B", "C")) and (
            selected_window is None or (arm.startswith("C") and selected_calibrator is None)
        ):
            if (
                cell["status"] != "NOT_EVALUABLE"
                or cell["reason"] != "no_eligible_development_policy"
            ):
                raise ValueError("Dependent arm cannot invent a fallback")
            continue
        months = {"A1": 12, "A2": 24, "A3": 36}[arm if arm.startswith("A") else selected_window]
        method = (
            "original"
            if arm.startswith("A") or arm == "B0"
            else "sigmoid"
            if arm == "B1"
            else "isotonic"
            if arm == "B2"
            else by_arm[selected_calibrator].get("method")
        )
        if arm.startswith("C") and by_arm[selected_calibrator]["status"] != "evaluable":
            if cell["status"] != "NOT_EVALUABLE":
                raise ValueError("Selected calibrator without support cannot evaluate")
            continue
        cal, info = calibration_window(
            _restore_frame(source["history"]),
            months=months,
            last_mature_month=group["roles"]["calibration"][1],
            cutoff=group["calibration_cutoff"],
        )
        selection = selection_blocks(_restore_frame(source["selection"]), group["horizon"], p)
        evaluation = _restore_frame(source["evaluation"])
        reason = info.get("reason") if info["status"] != "evaluable" else None
        if method == "isotonic" and min(int(cal.truth.eq(i).sum()) for i in (0, 1)) < 20:
            reason = "isotonic_class_support"
        if arm == "C2" and any(
            set(b.truth) != {0, 1} for _, b in selection.groupby("selection_block")
        ):
            reason = "C2_block_class_support"
        if reason:
            if cell["status"] != "NOT_EVALUABLE" or cell["reason"] != reason:
                raise ValueError("B2/C2 or calibration support rule differs")
            continue
        if cell["status"] != "evaluable" or cell["months"] != months or cell["method"] != method:
            raise ValueError("Scientific evaluability or selected method/window differs")
        if any(cell.get(name) != group[name] for name in ("calibration_cutoff", "decision_date")):
            raise ValueError("Scientific frozen role dates differ")
        temporal_roles(
            cal,
            selection,
            evaluation,
            horizon=group["horizon"],
            calibration_cutoff=group["calibration_cutoff"],
            decision_date=group["decision_date"],
        )
        state = cell["calibrator"]
        if state["method"] != ("sigmoid" if method == "original" else method):
            raise ValueError("Scientific calibrator method differs")
        if arm.startswith("C") and state != by_arm[selected_calibrator]["calibrator"]:
            raise ValueError("C arms cannot refit or change the selected calibrator")
        if arm == "B0" and state != by_arm[selected_window]["calibrator"]:
            raise ValueError("B0 must retain the selected A calibrator")
        selection["score"] = apply_calibrator(selection, state)
        decision = threshold_policy(selection, policy=arm if arm.startswith("C") else "C0")
        if cell["threshold"] != decision:
            raise ValueError("Deterministic threshold or C2 blocks differ")
        rows, _ = evaluate_frozen(
            evaluation, state, decision["threshold"], bins=p["ECE_bins"], objective="onset"
        )
        expected_measured = measured(rows, state, decision, source, p)
        if any(cell[k] != value for k, value in expected_measured.items()):
            raise ValueError("Scientific predictions, metrics or strata differ")
        if cell["support"] != {
            "calibration": info,
            "selection": support(selection),
            "selection_blocks": {
                str(b): support(part) for b, part in selection.groupby("selection_block")
            },
            "evaluation": support(evaluation),
        }:
            raise ValueError("Scientific cell support differs")
    expected_counters = {
        "predictor_fits": 0,
        "mlflow_writes": 0,
        "calibrator_fits": sum(c.get("calibrator_fit_performed", False) for c in cells),
        "threshold_selections": sum(c.get("threshold_selection_performed", False) for c in cells),
    }
    if result["execution_counters"] != expected_counters:
        raise ValueError("Scientific execution counters or predictor-fit prohibition differs")
    expected_description = describe(cells, p)
    if any(result[k] != value for k, value in expected_description.items()):
        raise ValueError("Scientific contrasts, territory limits or descriptive hypotheses differ")
    expected_identity_groups = {
        identity
        for identity in inputs
        if all(
            indexed.get((identity, arm), {}).get("status") == "evaluable" for arm in ("B0", "B1")
        )
    }
    if (
        len(result["B0_B1_identity"]) != len(expected_identity_groups)
        or {item["group_id"] for item in result["B0_B1_identity"]} != expected_identity_groups
    ):
        raise ValueError("B0/B1 identity inventory differs")
    for item in result["B0_B1_identity"]:
        a, b = indexed[item["group_id"], "B0"], indexed[item["group_id"], "B1"]
        if item["B0_B1_identical"] != all(
            a[k] == b[k] for k in ("calibrator", "threshold", "predictions", "metrics")
        ):
            raise ValueError("B0/B1 mathematical identity declaration differs")
