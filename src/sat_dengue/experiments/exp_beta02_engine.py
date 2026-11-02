"""Six-stage count experiment; scientific outputs never replace prior artifacts."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, PREDICTORS
from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments import exp_beta02_model as nb
from sat_dengue.experiments.exp_beta01 import metric_row, thresholds
from sat_dengue.experiments.exp_beta02 import paired, role_parts
from sat_dengue.experiments.onset import KEYS
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table


def train(prepared: dict[str, Any]) -> dict[str, Any]:
    """One fixed NB2 per horizon/year/climate; no validation-selected alternatives."""
    cells = []
    for horizon, frame in prepared["cohorts"].items():
        for year in prepared["protocol"]["evaluation_years"]:
            roles = role_parts(frame, year, prepared["protocol"])
            for climate in ("OFF", "ON"):
                columns = [n for n in PREDICTORS if climate == "ON" or n not in CLIMATE]
                model = nb.fit(roles["parts"]["train"], columns, prepared["protocol"]["model"])
                cells.append(
                    {
                        "horizon": horizon,
                        "year": year,
                        "climate": climate,
                        "parts": roles["parts"],
                        "role_audit": roles["audit"],
                        "model": model,
                    }
                )
    return {**prepared, "cells": cells}


def forecast(trained: dict[str, Any]) -> dict[str, Any]:
    """Persistable direct count marginals; no labels enter prediction."""
    for cell in trained["cells"]:
        cell["distributions"] = {
            role: nb.forecast(cell["parts"][role], cell["model"])
            for role in ("selection", "evaluation")
        }
    return trained


def risk(forecasted: dict[str, Any]) -> dict[str, Any]:
    """H5 conversion never substitutes the observed future transition."""
    for cell in forecasted["cells"]:
        h = cell["horizon"]
        cell["risks"] = {
            role: nb.risks(distribution, cell["parts"][role][f"p75_h5_t{h}"], h)
            for role, distribution in cell["distributions"].items()
        }
    return forecasted


def policy(predicted: dict[str, Any]) -> dict[str, Any]:
    """Select on the previous year only; T2 onset alerts remain unavailable."""
    outputs, policies = [], []
    budget = predicted["protocol"]["policy"]["budget_false_alerts_per_municipality_year"]
    for cell in predicted["cells"]:
        ident = {k: cell[k] for k in ("horizon", "year", "climate")}
        evaluate = cell["parts"]["evaluation"]
        output = evaluate[
            [*KEYS, "department_code", "target_month", "count_target", "onset_target"]
        ].copy()
        for name, value in ident.items():
            output[name] = value
        for name in cell["risks"]["evaluation"]:
            output[name] = cell["risks"]["evaluation"][name]
        output["arm"] = "NB"
        if cell["horizon"] == 1:
            select = cell["parts"]["selection"]
            selected = thresholds(
                select.onset_target, cell["risks"]["selection"].score, len(select) / 12, budget
            )
            output["alert"] = (
                False if selected["threshold"] is None else output.score.ge(selected["threshold"])
            )
            policies.append({**ident, **selected, "status": "EVALUABLE"})
        else:
            output["alert"] = pd.NA
            policies.append(
                {
                    **ident,
                    "threshold": None,
                    "status": "NO_EVALUABLE",
                    "reason": "marginal distributions do not identify joint onset",
                }
            )
        outputs.append(output.reset_index(drop=True))
    return {**predicted, "forecasts": pd.concat(outputs, ignore_index=True), "policies": policies}


def count_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    """Count accuracy/distribution coverage is separate from alert utility."""
    from scipy.stats import nbinom  # type: ignore[import-untyped]

    error = frame["mean"] - frame.count_target
    nll = -nbinom.logpmf(frame.count_target, frame.nb_r, frame.nb_p)
    if not np.isfinite(nll).all():
        raise ValueError("Nonfinite count log score")
    return {
        "rows": len(frame),
        "mae": float(error.abs().mean()),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "mean_negative_log_likelihood": float(np.mean(nll)),
        "predictive_90_coverage": float(frame.count_target.between(frame.q05, frame.q95).mean()),
        "predictive_90_mean_width": float((frame.q95 - frame.q05).mean()),
    }


def evaluate(selected: dict[str, Any]) -> dict[str, Any]:
    """Strict pairing, per-year/territory metrics and immutable native publication."""
    protocol, forecasts = selected["protocol"], selected["forecasts"]
    events = [forecasts.loc[forecasts.horizon.eq(1)].rename(columns={"onset_target": "truth"})]
    reference_audit = []
    for cell in selected["cells"]:
        if cell["climate"] != "ON":
            continue
        h, year, base = cell["horizon"], cell["year"], cell["parts"]["evaluation"]
        old = paired(base, selected["reference"], h, year)
        reference_audit.append(
            {
                "reference": "R0",
                "horizon": h,
                "year": year,
                "status": "PAIRED" if old is not None else "NO_EVALUABLE",
                "rows": len(base),
            }
        )
        if h != 1:
            continue
        if old is not None:
            ref = (
                base[[*KEYS, "department_code", "target_month"]]
                .sort_values(KEYS)
                .reset_index(drop=True)
            )
            for name in ("truth", "score", "alert"):
                ref[name] = old[name].to_numpy()
            ref["arm"], ref["climate"], ref["horizon"], ref["year"] = "R0", "historical", h, year
            events.append(ref)
        secondary = selected.get("secondary")
        if secondary is not None:
            for (arm, climate), group in secondary.loc[secondary.arm.isin(["G0", "L1"])].groupby(
                ["arm", "climate"]
            ):
                matched = paired(base, group, h, year)
                reference_audit.append(
                    {
                        "reference": f"BETA01_{arm}_{climate}",
                        "horizon": h,
                        "year": year,
                        "status": "PAIRED" if matched is not None else "NO_EVALUABLE",
                    }
                )
                if matched is not None:
                    ref = (
                        base[[*KEYS, "department_code", "target_month"]]
                        .sort_values(KEYS)
                        .reset_index(drop=True)
                    )
                    for name in ("truth", "score", "alert"):
                        ref[name] = matched[name].to_numpy()
                    ref["arm"], ref["climate"] = f"BETA01_{arm}", climate
                    ref["horizon"], ref["year"] = h, year
                    events.append(ref)
    detection = pd.concat(events, ignore_index=True)
    count_rows, onset_rows = [], []
    budget, margin = (
        protocol["policy"][k]
        for k in ("budget_false_alerts_per_municipality_year", "noninferiority_margin")
    )
    for keys, group in forecasts.groupby(["climate", "horizon", "year"], sort=True):
        for department in ("all", "50", "73"):
            frame = (
                group if department == "all" else group.loc[group.department_code.eq(department)]
            )
            if not frame.empty:
                count_rows.append(
                    {
                        **dict(zip(("climate", "horizon", "year"), keys, strict=True)),
                        "department": department,
                        **count_metrics(frame),
                    }
                )
    for keys, group in detection.groupby(["arm", "climate", "horizon", "year"], sort=True):
        for department in ("all", "50", "73"):
            frame = (
                group if department == "all" else group.loc[group.department_code.eq(department)]
            )
            if not frame.empty:
                onset_rows.append(
                    {
                        **dict(zip(("arm", "climate", "horizon", "year"), keys, strict=True)),
                        "department": department,
                        **metric_row(frame, budget),
                    }
                )
    reference = {(r["year"], r["department"]): r for r in onset_rows if r["arm"] == "R0"}
    comparisons = []
    for row in onset_rows:
        if row["arm"] != "NB":
            continue
        old = reference.get((row["year"], row["department"]))
        delta = (
            None
            if old is None or row["sensitivity"] is None or old["sensitivity"] is None
            else row["sensitivity"] - old["sensitivity"]
        )
        comparisons.append(
            {
                **{k: row[k] for k in ("climate", "horizon", "year", "department")},
                "reference": "R0",
                "sensitivity_difference": delta,
                "descriptive_joint_compliance": None
                if delta is None
                else bool(row["budget_met"] and delta >= -margin),
                "statistical_noninferiority": "UNAVAILABLE",
                "superiority": "NOT_ESTABLISHED",
            }
        )
    failures = sum(r["descriptive_joint_compliance"] is False for r in comparisons)
    conclusions = {
        "hypothesis": "NO_RESPALDADA" if failures else "NO_EVALUABLE",
        "failing_T1_strata": failures,
        "T2_onset": protocol["distribution"]["onset_t2"],
        "neural_candidate": protocol["neural_candidate"],
        "profiles": protocol["profiles"],
        "confirmation": protocol["confirmation"],
        "statistical_noninferiority": "UNAVAILABLE",
        "superiority": "NOT_ESTABLISHED",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
    }
    payloads = {
        "forecasts.csv": serialize_table(
            forecasts.sort_values(["horizon", "year", "climate", *KEYS])
        ),
        "onset_predictions.csv": serialize_table(
            detection.sort_values(["arm", "climate", "year", *KEYS])
        ),
        "count_metrics.csv": serialize_table(pd.DataFrame(count_rows)),
        "onset_metrics.csv": serialize_table(pd.DataFrame(onset_rows)),
        "comparisons_r0.json": canonical_bytes({"comparisons": comparisons}),
        "reference_audit.json": canonical_bytes({"comparisons": reference_audit}),
        "conclusions.json": canonical_bytes(conclusions),
        "protocol.json": canonical_bytes(protocol),
        "provenance.json": canonical_bytes(selected["provenance"]),
        "policies.json": canonical_bytes({"policies": selected["policies"]}),
    }
    ledger = []
    for cell in selected["cells"]:
        name = f"nb2-h{cell['horizon']}-{cell['year']}-{cell['climate']}.json"
        payloads[name] = canonical_bytes(cell["model"])
        ledger.append(
            {
                **{k: cell[k] for k in ("horizon", "year", "climate", "role_audit")},
                "model_file": name,
                "training_keys_sha256": bytes_record(serialize_table(cell["parts"]["train"][KEYS]))[
                    "sha256"
                ],
                "evaluation_keys_sha256": bytes_record(
                    serialize_table(cell["parts"]["evaluation"][KEYS])
                )["sha256"],
            }
        )
    payloads["cells.json"] = canonical_bytes({"cells": ledger})
    real = selected["evidence_type"] == "authorized_retrospective"
    body = {
        "schema": "exp-beta02-publication-v1",
        "experiment_id": "EXP-BETA02",
        "evidence_type": selected["evidence_type"],
        "canonical_bundle_id": protocol["canonical_bundle_id"],
        "files": {n: bytes_record(b) for n, b in payloads.items()},
        "real_model_fits": len(ledger) if real else 0,
        "generated_model_fits": 0 if real else len(ledger),
        "sources": selected["provenance"]["sources"],
    }
    payloads["manifest.json"] = canonical_bytes(
        {**body, "bundle_id": hashlib.sha256(canonical_bytes(body)).hexdigest()}
    )
    return {"payloads": payloads, "provenance": selected["provenance"]}
