"""Beta's bounded native estimator execution; optional imports stay at fit boundaries."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, PREDICTORS
from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp_beta01 import (
    KEYS,
    fit_adaptation,
    fit_intercept,
    metric_row,
    role_parts,
    shifted,
    thresholds,
)
from sat_dengue.training_preparation.serialization import bytes_record, serialize_table


def train(prepared: dict[str, Any]) -> dict[str, Any]:
    """One pooled predictor per horizon/year/climate setting; no municipality fits."""
    from xgboost import XGBClassifier

    protocol = prepared["protocol"]
    cells = []
    for horizon, frame in prepared["cohorts"].items():
        for year in protocol["evaluation_years"]:
            partition = role_parts(frame, year, protocol)
            parts = partition["parts"]
            for climate in ("OFF", "ON"):
                columns = [n for n in PREDICTORS if climate == "ON" or n not in CLIMATE]
                model = XGBClassifier(
                    **{k: v for k, v in protocol["model"].items() if k != "family"}
                )
                model.fit(
                    parts["train"][columns].astype(float), parts["train"].onset_target.astype(int)
                )
                scores = {
                    role: model.predict_proba(part[columns].astype(float))[:, 1].astype(float)
                    for role, part in parts.items()
                    if role != "train"
                }
                # OOF roles are pooled across all territories with a common chronology.
                offset = fit_intercept(
                    scores["calibration"],
                    parts["calibration"].onset_target.astype(int),
                    protocol["calibration"]["penalty"],
                )
                cells.append(
                    {
                        "horizon": horizon,
                        "year": year,
                        "climate": climate,
                        "predictors": columns,
                        "parts": parts,
                        "role_audit": partition["audit"],
                        "raw_scores": scores,
                        "global_offset": offset,
                        "model_bytes": bytes(model.get_booster().save_raw(raw_format="ubj")),
                    }
                )
    return {**prepared, "cells": cells}


def adapt(trained: dict[str, Any]) -> dict[str, Any]:
    """L1 adapts the sole available global source, G0, separately for ON and OFF."""
    for cell in trained["cells"]:
        frame = cell["parts"]["adaptation"]
        scores = shifted(cell["raw_scores"]["adaptation"], cell["global_offset"])
        cell["department_offsets"] = fit_adaptation(
            frame, scores, trained["protocol"]["adaptation"]
        )
    return trained


def predict(adapted: dict[str, Any]) -> dict[str, Any]:
    """Select policies on past selection rows, then predict paired evaluation rows."""
    predictions, policies = [], []
    budget = adapted["protocol"]["policy"]["budget_false_alerts_per_municipality_year"]
    for cell in adapted["cells"]:
        select, evaluate = cell["parts"]["selection"], cell["parts"]["evaluation"]
        for arm in ("G0", "L1"):
            scores = {}
            for role in ("selection", "evaluation"):
                frame = cell["parts"][role]
                offset = np.zeros(len(frame)) + cell["global_offset"]
                if arm == "L1":
                    offset += np.array(
                        [
                            cell["department_offsets"].get(str(code), {"offset": 0.0})["offset"]
                            for code in frame.department_code
                        ]
                    )
                scores[role] = shifted(cell["raw_scores"][role], offset)
            policy = thresholds(
                select.onset_target, scores["selection"], len(select) / 12.0, budget
            )
            identity = {n: cell[n] for n in ("horizon", "year", "climate")}
            policies.append({**identity, "arm": arm, **policy})
            output = evaluate[[*KEYS, "department_code", "target_month", "target_year"]].copy()
            output["truth"] = evaluate.onset_target.astype(int)
            output["score"] = scores["evaluation"]
            output["alert"] = (
                False if policy["threshold"] is None else output.score.ge(policy["threshold"])
            )
            for key, value in {**identity, "arm": arm}.items():
                output[key] = value
            predictions.append(output)
    return {
        **adapted,
        "predictions": pd.concat(predictions, ignore_index=True),
        "policies": policies,
    }


def paired_reference(
    predictions: pd.DataFrame, reference: Any
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Use R0 only when its full evaluation keys/truth agree with the Beta cohort."""
    outcomes, audit = [], []
    for (horizon, year), base in predictions.loc[
        predictions.arm.eq("G0") & predictions.climate.eq("ON")
    ].groupby(["horizon", "year"], sort=True):
        spec = {"horizon": int(horizon), "year": int(year)}
        if reference is None:
            audit.append(
                {**spec, "status": "NO_EVALUABLE", "reason": "identified frozen R0 unavailable"}
            )
            continue
        old = reference.loc[
            reference.horizon.eq(horizon) & reference.target_month.str[:4].eq(str(year))
        ].copy()
        old = old.rename(columns={"origin_month": "year_month"})
        ordered = old.sort_values(KEYS).reset_index(drop=True)
        current = base.sort_values(KEYS).reset_index(drop=True)
        if (
            ordered.duplicated(KEYS).any()
            or len(ordered) != len(current)
            or ordered[KEYS].to_records(index=False).tolist()
            != current[KEYS].to_records(index=False).tolist()
            or ordered.truth.astype(int).tolist() != current.truth.astype(int).tolist()
        ):
            audit.append(
                {
                    **spec,
                    "status": "NO_EVALUABLE",
                    "reason": "cohort/target mismatch; no intersection substituted",
                    "beta_rows": len(current),
                    "reference_rows": len(ordered),
                }
            )
            continue
        for name in ("score", "alert"):
            current[name] = ordered[name].to_numpy()
        current["arm"], current["climate"] = "R0", "historical"
        if not np.isfinite(current.score).all() or not current.score.between(0, 1).all():
            raise ValueError("Invalid frozen reference scores")
        outcomes.append(current)
        audit.append({**spec, "status": "PAIRED", "rows": len(current)})
    return (
        pd.concat(outcomes, ignore_index=True) if outcomes else predictions.iloc[:0].copy()
    ), audit


def evaluate(predicted: dict[str, Any]) -> dict[str, Any]:
    """Persist native predictions, role/cell states, metrics and explicit limitations."""
    protocol, predictions = predicted["protocol"], predicted["predictions"]
    reference, reference_audit = paired_reference(predictions, predicted["reference"])
    predictions = pd.concat([predictions, reference], ignore_index=True)
    budget = protocol["policy"]["budget_false_alerts_per_municipality_year"]
    margin = protocol["policy"]["noninferiority_margin"]
    rows = []
    for keys, frame in predictions.groupby(["arm", "climate", "horizon", "year"], sort=True):
        for department in ("all", "50", "73"):
            group = (
                frame if department == "all" else frame.loc[frame.department_code.eq(department)]
            )
            if group.empty:
                continue
            rows.append(
                {
                    **dict(zip(("arm", "climate", "horizon", "year"), keys, strict=True)),
                    "department": department,
                    **metric_row(group, budget),
                }
            )
    metrics = pd.DataFrame(rows)
    # Formal margin is against R0; this describes observed compliance, never proves NI.
    comparisons = []
    index = {(r["horizon"], r["year"], r["department"]): r for r in rows if r["arm"] == "R0"}
    for row in rows:
        if row["arm"] == "R0":
            continue
        old = index.get((row["horizon"], row["year"], row["department"]))
        delta = (
            None
            if old is None or old["sensitivity"] is None or row["sensitivity"] is None
            else row["sensitivity"] - old["sensitivity"]
        )
        comparisons.append(
            {
                **{k: row[k] for k in ("arm", "climate", "horizon", "year", "department")},
                "reference": "R0",
                "sensitivity_difference": delta,
                "descriptive_joint_compliance": None
                if delta is None
                else bool(row["budget_met"] and delta >= -margin),
                "statistical_noninferiority": "UNAVAILABLE",
                "superiority": "NOT_ESTABLISHED",
            }
        )
    by_key = {(r["arm"], r["climate"], r["horizon"], r["year"], r["department"]): r for r in rows}
    contrasts = []
    for row in rows:
        if row["arm"] == "R0":
            continue
        matches = []
        if row["arm"] == "L1":
            matches.append(("adaptation", ("G0", row["climate"])))
        if row["climate"] == "ON":
            matches.append(("climate", (row["arm"], "OFF")))
        for contrast, (arm, climate) in matches:
            other = by_key[(arm, climate, row["horizon"], row["year"], row["department"])]
            assert row["rows"] == other["rows"] and row["onsets"] == other["onsets"]
            delta = (
                None
                if row["sensitivity"] is None or other["sensitivity"] is None
                else row["sensitivity"] - other["sensitivity"]
            )
            contrasts.append(
                {
                    **{k: row[k] for k in ("arm", "climate", "horizon", "year", "department")},
                    "contrast": contrast,
                    "sensitivity_difference": delta,
                    "detected_difference": row["detected"] - other["detected"],
                    "false_alert_difference": row["false_alerts"] - other["false_alerts"],
                    "brier_difference": row["brier"] - other["brier"],
                    "candidate_budget_met": row["budget_met"],
                }
            )
    # DEC-137 fixes R0 as the NI reference. G0/L1 remains an incremental contrast.
    failures = [
        r for r in comparisons if r["arm"] == "L1" and r["descriptive_joint_compliance"] is False
    ]
    conclusions = {
        "learning_global": {"status": "NO_EVALUABLE", "reason": protocol["global_hypothesis"]},
        "local_adaptation": {
            "status": "NO_RESPALDADA" if failures else "NO_EVALUABLE",
            "reason": "descriptive year/department sensitivity-load guardrails against R0 fail"
            if failures
            else "descriptive compliance cannot establish inferential benefit",
            "failing_strata": len(failures),
        },
        "G1": protocol["G1"],
        "R0": reference_audit,
        "profiles": protocol["profile_strata"],
        "confirmation": protocol["confirmation"],
        "uncertainty": protocol["uncertainty"],
        "champion": "not_selected",
        "G5": "NOT_APPROVED",
        "statistical_noninferiority": "UNAVAILABLE",
        "superiority": "NOT_ESTABLISHED",
    }
    payloads = {
        "predictions.csv": serialize_table(
            predictions.sort_values(["arm", "climate", "horizon", "year", *KEYS])
        ),
        "metrics.csv": serialize_table(metrics),
        "contrasts.csv": serialize_table(pd.DataFrame(contrasts)),
        "comparisons_r0.json": canonical_bytes({"comparisons": comparisons}),
        "conclusions.json": canonical_bytes(conclusions),
        "protocol.json": canonical_bytes(protocol),
        "provenance.json": canonical_bytes(predicted["provenance"]),
        "policies.json": canonical_bytes({"policies": predicted["policies"]}),
    }
    ledger = []
    for cell in predicted["cells"]:
        name = f"model-h{cell['horizon']}-{cell['year']}-climate-{cell['climate']}.ubj"
        payloads[name] = cell["model_bytes"]
        ledger.append(
            {
                **{
                    k: cell[k]
                    for k in (
                        "horizon",
                        "year",
                        "climate",
                        "predictors",
                        "role_audit",
                        "global_offset",
                        "department_offsets",
                    )
                },
                "model_file": name,
                "evaluation_keys_sha256": bytes_record(
                    serialize_table(cell["parts"]["evaluation"][KEYS])
                )["sha256"],
            }
        )
    payloads["cells.json"] = canonical_bytes({"cells": ledger})
    body = {
        "schema": "exp-beta01-publication-v1",
        "experiment_id": "EXP-BETA01",
        "evidence_type": predicted["evidence_type"],
        "canonical_bundle_id": protocol["canonical_bundle_id"],
        "files": {name: bytes_record(value) for name, value in payloads.items()},
        "real_model_fits": len(ledger)
        if predicted["evidence_type"] == "authorized_retrospective"
        else 0,
        "generated_model_fits": len(ledger)
        if predicted["evidence_type"] == "synthetic_generated_data"
        else 0,
        "global_calibrations": len(ledger),
        "territorial_intercepts": sum(len(c["department_offsets"]) for c in predicted["cells"]),
        "sources": predicted["provenance"]["sources"],
    }
    manifest = {**body, "bundle_id": hashlib.sha256(canonical_bytes(body)).hexdigest()}
    payloads["manifest.json"] = canonical_bytes(manifest)
    return {"payloads": payloads, "provenance": predicted["provenance"]}
