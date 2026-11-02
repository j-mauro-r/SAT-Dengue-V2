"""Controlled national G1 extension; frozen regional comparators are never fitted."""

from __future__ import annotations

import io
import json
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.national import predictor_matrix
from sat_dengue.canonical.table import CLIMATE, PREDICTORS
from sat_dengue.configuration import canonical_bytes, validate_parameters
from sat_dengue.experiments.exp_beta01 import (
    fit_intercept,
    metric_row,
    role_parts,
    shifted,
    thresholds,
)
from sat_dengue.experiments.exp_beta01 import (
    prepare as regional_prepare,
)
from sat_dengue.experiments.onset import KEYS, labels
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table

FEATURES = [n for n in PREDICTORS if n not in CLIMATE]


def require_pair(left: pd.DataFrame, right: pd.DataFrame, columns: list[str]) -> None:
    """Reject cohort intersections, changed targets and different regional X."""
    a, b = (f.sort_values(KEYS).reset_index(drop=True) for f in (left, right))
    if len(a) != len(b) or a.duplicated(KEYS).any() or b.duplicated(KEYS).any():
        raise ValueError("V2 paired cohort key mismatch")
    for name in columns:
        equal = a[name].eq(b[name]) | (a[name].isna() & b[name].isna())
        if not equal.fillna(False).all():
            raise ValueError(f"V2 paired cohort value mismatch: {name}")


def prepare(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Verify regional support exactly; add national data to the train role only."""
    if validate_parameters(parameters) != {"profile": "exp_beta01_v2", "tracking": "disabled"}:
        raise ValueError("V2 requires its separate disabled-tracking profile")
    protocol = sources["protocol"]
    if protocol["model"] != sources["regional"]["protocol"]["model"]:
        raise ValueError("V2 model changed from frozen G0")
    regional = regional_prepare(
        sources["regional"], {"profile": "exp_beta01", "tracking": "disabled"}
    )["cohorts"]
    table = sources["table"].copy().reset_index(drop=True)
    if table.year_month.ge(protocol["reserved_target_start"]).any():
        raise ValueError("Reserved origin in V2 national table")
    matrix = predictor_matrix(table, sources["national_contract"], False)
    states = table[KEYS].copy()
    states["excess"] = table.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[table.zona_canal_t.isna(), "excess"] = pd.NA
    frozen = sources["frozen_predictions"]
    cells, support = [], []
    for h in protocol["horizons"]:
        outcomes = labels(states, h)
        mask = outcomes.eligible_at_t & outcomes.onset_target.notna() & matrix.notna().all(axis=1)
        mask &= outcomes.target_month.lt(protocol["reserved_target_start"])
        mask &= ~table.requires_record_review
        if not mask.eq(table[f"g1_no_climate_t{h}"]).all():
            raise ValueError("National eligibility mask or H5 outcome changed")
        truth = (
            table[f"onset_T{h}"].eq(outcomes.onset_target)
            | (table[f"onset_T{h}"].isna() & outcomes.onset_target.isna())
        ).fillna(False)
        if not truth.all():
            raise ValueError("National direct-onset label mismatch")
        frame = table.loc[mask, [*KEYS, "department_code", *FEATURES]].copy()
        frame["onset_target"] = outcomes.loc[mask, "onset_target"]
        frame["target_month"] = outcomes.loc[mask, "target_month"]
        frame["target_year"] = frame.target_month.str[:4].astype(int)
        frame["zona_canal_t"] = frame.zona_canal_t.map(
            {"EXITO": 0, "SEGURIDAD": 1, "ALERTA": 2, "EXCESO": 3}
        )
        for year in protocol["evaluation_years"]:
            old_roles = role_parts(regional[h], year, protocol)
            national_roles = role_parts(frame, year, protocol)
            regional_parts = old_roles["parts"]
            for role, old in regional_parts.items():
                new = national_roles["parts"][role]
                new = new.loc[new.department_code.isin(["50", "73"])]
                require_pair(old, new, [*KEYS, "onset_target", "target_month", *FEATURES])
            evaluate = regional_parts["evaluation"]
            references = []
            for arm, climate in (("G0", "OFF"), ("R0", "historical")):
                old = frozen.loc[
                    frozen.arm.eq(arm)
                    & frozen.climate.eq(climate)
                    & frozen.horizon.eq(h)
                    & frozen.year.eq(year)
                ].copy()
                expected = evaluate[
                    [*KEYS, "target_month", "department_code", "onset_target"]
                ].rename(columns={"onset_target": "truth"})
                require_pair(expected, old, [*KEYS, "target_month", "department_code", "truth"])
                native = sources["regional"].get("reference")
                if arm == "R0" and native is not None:
                    native = native.loc[
                        native.horizon.eq(h) & native.target_month.str[:4].eq(str(year))
                    ].rename(columns={"origin_month": "year_month"})
                    require_pair(old, native, [*KEYS, "truth", "score", "alert"])
                references.append(old)
            train = national_roles["parts"]["train"].sort_values(KEYS).reset_index(drop=True)
            extra = train.loc[~train.department_code.isin(["50", "73"])]
            ready = bool(
                len(extra)
                and train.onset_target.nunique() == 2
                and regional_parts["calibration"].onset_target.nunique() == 2
            )
            ident = {"horizon": h, "year": year, "status": "EVALUABLE" if ready else "NO_EVALUABLE"}
            audit = {
                **ident,
                "train_rows": len(train),
                "train_municipalities": int(train.municipality_code.nunique()),
                "additional_rows": len(extra),
                "additional_municipalities": int(extra.municipality_code.nunique()),
                "additional_onsets": int(extra.onset_target.sum()),
                "additional_first_origin": str(extra.year_month.min()) if len(extra) else None,
                "additional_last_origin": str(extra.year_month.max()) if len(extra) else None,
                "additional_origin_months": int(extra.year_month.nunique()),
                "regional_train_rows": len(regional_parts["train"]),
                "regional_support_parity": "EXACT_ALL_FIVE_ROLES",
                "G0_MATCHED": "NOT_REQUIRED_EXACT_REGIONAL_SUPPORT",
                "train_keys_sha256": bytes_record(serialize_table(train[KEYS]))["sha256"],
                "regional_role_audit": old_roles["audit"],
            }
            support.append(audit)
            if ready:
                cells.append(
                    {
                        **ident,
                        "train": train,
                        "parts": regional_parts,
                        "references": pd.concat(references),
                        "audit": audit,
                    }
                )
    return {**sources, "cells": cells, "preflight": support}


def train(prepared: dict[str, Any]) -> dict[str, Any]:
    """Fit exactly one G1 XGBoost per supported year/horizon; no control fits."""
    from xgboost import XGBClassifier

    for cell in prepared["cells"]:
        model = XGBClassifier(
            **{k: v for k, v in prepared["protocol"]["model"].items() if k != "family"}
        )
        model.fit(cell["train"][FEATURES].astype(float), cell["train"].onset_target.astype(int))
        cell["model_bytes"] = bytes(model.get_booster().save_raw(raw_format="ubj"))
        cell["raw_scores"] = {
            role: model.predict_proba(cell["parts"][role][FEATURES].astype(float))[:, 1].astype(
                float
            )
            for role in ("calibration", "selection", "evaluation")
        }
    return prepared


def calibrate(trained: dict[str, Any]) -> dict[str, Any]:
    """Use the original regional calibration and selection populations only."""
    for cell in trained["cells"]:
        cell["offset"] = fit_intercept(
            cell["raw_scores"]["calibration"],
            cell["parts"]["calibration"].onset_target.astype(int),
            trained["protocol"]["calibration"]["penalty"],
        )
        scores = shifted(cell["raw_scores"]["selection"], cell["offset"])
        cell["policy"] = thresholds(
            cell["parts"]["selection"].onset_target,
            scores,
            len(scores) / 12,
            trained["protocol"]["policy"]["budget_false_alerts_per_municipality_year"],
        )
    return trained


def predict(calibrated: dict[str, Any]) -> dict[str, Any]:
    """Persist G1 predictions alongside unchanged frozen G0 and R0 rows."""
    predictions = []
    for cell in calibrated["cells"]:
        frame = cell["parts"]["evaluation"]
        output = frame[[*KEYS, "department_code", "target_month", "target_year"]].copy()
        output["truth"] = frame.onset_target.astype(int)
        output["score"] = shifted(cell["raw_scores"]["evaluation"], cell["offset"])
        threshold = cell["policy"]["threshold"]
        output["alert"] = False if threshold is None else output.score.ge(threshold)
        for name, value in {
            "arm": "G1",
            "climate": "OFF",
            "horizon": cell["horizon"],
            "year": cell["year"],
        }.items():
            output[name] = value
        predictions.extend([output, cell["references"]])
    calibrated["predictions"] = (
        pd.concat(predictions, ignore_index=True)
        if predictions
        else calibrated["frozen_predictions"].iloc[:0].copy()
    )
    return calibrated


def summarize(
    predictions: pd.DataFrame, protocol: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Report paired strata and the frozen descriptive hypothesis decision."""
    rows = []
    budget = protocol["policy"]["budget_false_alerts_per_municipality_year"]
    for (arm, h), frame in predictions.groupby(["arm", "horizon"], sort=True):
        for year in ["all", *protocol["evaluation_years"]]:
            period = frame if year == "all" else frame.loc[frame.year.eq(year)]
            for dept in ("all", "50", "73"):
                group = period if dept == "all" else period.loc[period.department_code.eq(dept)]
                if len(group):
                    rows.append(
                        {
                            "arm": arm,
                            "horizon": int(h),
                            "year": str(year),
                            "department": dept,
                            **metric_row(group, budget),
                        }
                    )
    metrics = pd.DataFrame(rows)
    lookup = {(r["arm"], r["horizon"], r["year"], r["department"]): r for r in rows}
    contrasts = []
    for row in rows:
        if row["arm"] != "G1":
            continue
        for arm in ("G0", "R0"):
            other = lookup[(arm, row["horizon"], row["year"], row["department"])]
            if row["rows"] != other["rows"] or row["onsets"] != other["onsets"]:
                raise ValueError("Paired exposure/onset denominator changed")
            delta = (
                None
                if row["sensitivity"] is None or other["sensitivity"] is None
                else row["sensitivity"] - other["sensitivity"]
            )
            contrasts.append(
                {
                    **{n: row[n] for n in ("horizon", "year", "department")},
                    "reference": arm,
                    "sensitivity_difference": delta,
                    "detected_difference": row["detected"] - other["detected"],
                    "false_alert_difference": row["false_alerts"] - other["false_alerts"],
                    "load_difference": row["false_alerts_per_municipality_year"]
                    - other["false_alerts_per_municipality_year"],
                    "brier_difference": row["brier"] - other["brier"],
                    "ap_difference": None
                    if row["average_precision"] is None or other["average_precision"] is None
                    else row["average_precision"] - other["average_precision"],
                    "joint_compliance": None
                    if delta is None
                    else bool(
                        row["budget_met"] and delta >= -protocol["policy"]["noninferiority_margin"]
                    ),
                }
            )
    comparison = pd.DataFrame(contrasts)
    pooled = [
        r
        for r in contrasts
        if r["reference"] == "G0" and r["year"] == "all" and r["department"] == "all"
    ]
    favorable = [
        r
        for r in pooled
        if r["sensitivity_difference"] is not None
        and r["sensitivity_difference"] > 0
        and r["load_difference"] <= 0
    ]
    guardrails = [r for r in contrasts if r["reference"] == "R0"]
    stable = all(
        r["sensitivity_difference"] is not None and r["sensitivity_difference"] >= 0
        for r in contrasts
        if r["reference"] == "G0"
    )
    supported = (
        len(favorable) == 2 and all(r["joint_compliance"] is True for r in guardrails) and stable
    )
    status = (
        "NO_EVALUABLE"
        if not pooled
        else "RESPALDADA"
        if supported
        else "PARCIALMENTE_RESPALDADA"
        if favorable
        else "NO_RESPALDADA"
    )
    return (
        metrics,
        comparison,
        {
            "national_expansion": status,
            "G5": "NOT_APPROVED",
            "champion": "not_selected",
            "statistical_noninferiority": "UNAVAILABLE",
            "superiority": "NOT_ESTABLISHED",
            "automatic_follow_up": False,
        },
    )


def reproduce(prepared: dict[str, Any], payloads: dict[str, bytes]) -> dict[str, Any]:
    """Replay identified native models, calibration and policies with zero fits."""
    from xgboost import XGBClassifier

    ledger = json.loads(payloads["cells.json"])["cells"]
    cells = {(c["horizon"], c["year"]): c for c in prepared["cells"]}
    replayed = []
    for record in ledger:
        cell = cells[(record["horizon"], record["year"])].copy()
        if record["predictors"] != FEATURES:
            raise ValueError("Replay predictor list changed")
        model = XGBClassifier(n_jobs=1)
        model.load_model(bytearray(payloads[record["model_file"]]))
        scores = {}
        for role, filename in record["scores"].items():
            frame = cell["parts"][role]
            expected = pd.read_csv(
                io.BytesIO(payloads[filename]),
                dtype={"municipality_code": str},
                float_precision="round_trip",
            )
            require_pair(frame, expected, [*KEYS, "onset_target"])
            values = model.predict_proba(frame[FEATURES].astype(float))[:, 1].astype(float)
            if not np.array_equal(values, expected.raw_score.to_numpy()):
                raise ValueError("Native model raw scores changed on replay")
            scores[role] = values
        policy = thresholds(
            cell["parts"]["selection"].onset_target,
            shifted(scores["selection"], record["offset"]),
            len(scores["selection"]) / 12,
            prepared["protocol"]["policy"]["budget_false_alerts_per_municipality_year"],
        )
        if policy != record["policy"]:
            raise ValueError("Replayed selection policy changed")
        replayed.append(
            {**cell, "raw_scores": scores, "offset": record["offset"], "policy": policy}
        )
    predictions = predict({**prepared, "cells": replayed})["predictions"]
    ordered = predictions.sort_values(["arm", "horizon", "year", "municipality_code", "year_month"])
    metrics, contrasts, conclusions = summarize(predictions, prepared["protocol"])
    for name, actual in {
        "predictions.csv": serialize_table(ordered),
        "metrics.csv": serialize_table(metrics),
        "comparisons.csv": serialize_table(contrasts),
        "conclusions.json": canonical_bytes(conclusions),
    }.items():
        if actual != payloads[name]:
            raise ValueError(f"V2 replay payload mismatch: {name}")
    return {
        "reloaded_models": len(ledger),
        "new_model_fits": 0,
        "raw_scores": "PASS",
        "policies": "PASS",
        "predictions_and_metrics_bytes": "PASS",
    }
