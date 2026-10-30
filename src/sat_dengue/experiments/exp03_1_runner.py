"""Authorized EXP03.1 source loading and frozen 96-cell execution."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.experiments.exp01 import digest
from sat_dengue.experiments.exp03 import load_protocol as load_exp03_protocol
from sat_dengue.experiments.exp03_1_contract import cells, counts, matrix, protocol
from sat_dengue.experiments.exp03_1_engine import (
    execution_plan,
    reuse_decision,
    variant_predictors,
)
from sat_dengue.experiments.exp03_1_evaluation import metrics, paired_effect, select_threshold
from sat_dengue.experiments.exp03_1_features import (
    KEYS,
    paired_cohort,
    trajectory_features,
)
from sat_dengue.experiments.exp03_1_preflight import OUTPUT_ROOT, authorize
from sat_dengue.experiments.exp03_preflight import safe_path


def _read_coverage(snapshot: Any, contract: dict[str, Any]) -> pd.DataFrame:
    from sat_dengue.datasets.legacy_preparation.pipeline import parse_fields
    from sat_dengue.experiments.exp01_inputs import REFERENCE_END

    field = "in_epi_coverage"
    schema = [row for row in contract["schema"] if row["name"] == field]
    if len(schema) != 1 or schema[0]["dtype"].lower() != "bool":
        raise ValueError("EXP03.1 requires the governed boolean in_epi_coverage field")
    panel_path = snapshot.resolve(contract["panel_path"])
    coverage = pd.read_csv(
        panel_path,
        usecols=[*KEYS, field],
        dtype="string",
        keep_default_na=False,
    )
    coverage = coverage.loc[coverage.year_month.le(REFERENCE_END)].copy()
    coverage = parse_fields(coverage, {"schema": schema})
    if coverage.duplicated(KEYS).any():
        raise ValueError("EXP03.1 coverage keys must be unique")
    coverage = coverage.rename(columns={field: "covered"})
    # Unknown coverage remains outside the known/covered set; it is never inferred
    # from notification counts.
    coverage["covered"] = coverage.covered.eq(True).fillna(False).astype(bool)
    return coverage


def _apply_coverage(panel: pd.DataFrame, coverage: pd.DataFrame) -> pd.DataFrame:
    if panel.duplicated(KEYS).any() or coverage.duplicated(KEYS).any():
        raise ValueError("EXP03.1 source panel and coverage keys must be unique")
    combined = panel.merge(
        coverage,
        on=KEYS,
        how="outer",
        validate="one_to_one",
    )
    combined["covered"] = combined.covered.fillna(False).astype(bool)
    covered = combined.covered
    for column in ("dengue_notifications_count", "dengue_grave_notifications_count"):
        if column not in combined:
            raise ValueError("EXP03.1 source is missing notification count " + column)
        combined.loc[covered & combined[column].isna(), column] = 0.0
        combined.loc[~covered, column] = pd.NA
    return combined


def load_authorized_sources(receipt: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Authorize first, then admit and parse verified sources from isolated copies."""
    approval = authorize(receipt, parameters)
    from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
    from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs
    from sat_dengue.experiments.exp03_admission import admit_sources, reverify, verified_snapshot

    config = PreparationConfig(Path.cwd())
    admission = admit_sources(receipt, config)
    reverify(admission)
    try:
        with verified_snapshot(config, admission) as snapshot:
            inputs = prepare_exp01_inputs(snapshot)
            coverage = _read_coverage(snapshot, inputs.contract)
        panel = _apply_coverage(inputs.panel, coverage)
        if panel.year_month.ge("2025-01").any():
            raise ValueError("EXP03.1 rejects source observations after 2024")
        reverify(admission)
    except (OSError, KeyError, TypeError, ValueError):
        raise
    admission["status"] = "verified"
    return {
        "panel": panel,
        "contract": inputs.contract,
        "fingerprints": inputs.report["input_fingerprints"],
        "admission": admission,
        "preflight": receipt,
        "approval_sha256": digest(approval),
        "parameters": parameters,
    }


def _window_by_cut() -> dict[str, dict[str, Any]]:
    source = load_exp03_protocol()["design"]["windows"]
    result = {row["id"]: row for row in source}
    expected = set(protocol()["cuts"])
    if set(result) != expected:
        raise ValueError("EXP03 temporal cut identities differ from the frozen EXP03.1 cuts")
    return result


def _prepare(panel: pd.DataFrame, contract: dict[str, Any], horizon: int) -> pd.DataFrame:
    from sat_dengue.experiments.exp03_features import prepare

    frame = prepare(panel, contract, horizon)
    features = trajectory_features(panel, frame[KEYS])
    return frame.merge(features, on=KEYS, how="left", validate="one_to_one")


def execute_matrix(
    panel: pd.DataFrame,
    contract: dict[str, Any],
    *,
    fit: Callable[..., Any] | None = None,
    calibrate: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Fit every frozen cell with one paired, twelve-state cohort per cut/objective."""
    from sat_dengue.experiments.exp03_features import exposure_table, role_parts
    from sat_dengue.experiments.exp03_persistence import fit_calibration, fit_native

    fit = fit or fit_native
    calibrate = calibrate or fit_calibration
    p = protocol()
    parent_design = load_exp03_protocol()["design"]
    v09 = parent_design["variants"]["V09"]
    grid = cells()
    if len(grid) != counts()["maximum_refit_cells"] or len(grid) != 96:
        raise ValueError("EXP03.1 frozen cell grid is not exactly 96 cells")
    windows = _window_by_cut()
    prepared = {horizon: _prepare(panel, contract, horizon) for horizon in p["horizons"]}
    results: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    thresholds: list[dict[str, Any]] = []
    for spec in grid:
        horizon = spec["horizon"]
        target = "onset_target" if spec["objective"] == "onset" else "excess_target"
        labels = (
            ["onset_target"] if spec["objective"] == "onset" else ["onset_target", "excess_target"]
        )
        common, _ledger = paired_cohort(
            prepared[horizon],
            base_predictors=v09,
            labels=labels,
        )
        parts = role_parts(common, windows[spec["cut"]])
        selected_parts: dict[str, pd.DataFrame] = {}
        for role, part in parts.items():
            eligible = part["eligible_at_t"].fillna(False).astype(bool)
            selected_parts[role] = part.loc[eligible].copy()
        train, calibration, selection, evaluation = (
            selected_parts[role] for role in ("train", "calibration", "selection", "evaluation")
        )
        columns = variant_predictors(v09, spec["variant"])
        if any(frame.empty for frame in (train, calibration, selection, evaluation)):
            raise ValueError("Incomplete EXP03.1 cohort support; no partial run is publishable")
        if any(frame[target].nunique() != 2 for frame in (train, calibration)):
            raise ValueError("EXP03.1 fit/calibration roles require both target classes")
        model = fit(
            spec["family"],
            train[columns],
            train[target].astype(int),
            parent_design["families"][spec["family"]],
            parent_design["seed"],
        )
        calibrator = calibrate(
            model.predict(calibration[columns]),
            calibration[target].astype(int),
            parent_design["seed"],
        )
        selection_scores = calibrator(model.predict(selection[columns]))
        exposure = float(
            exposure_table(parts).query("role == 'selection'").monitored_exposure.sum()
        )
        threshold = select_threshold(
            selection.onset_target.astype(int),
            selection_scores,
            exposure=exposure,
            budget=p["budget"]["B_primary"],
        )
        scores = calibrator(model.predict(evaluation[columns]))
        alerts = (
            pd.Series(False, index=evaluation.index)
            if threshold["threshold"] is None
            else scores.ge(threshold["threshold"])
        )
        metric_frame = pd.DataFrame(
            {
                "truth": evaluation[target].astype(int),
                "score": scores.astype(float),
                "alert": alerts.astype(bool),
                "municipality_code": evaluation.municipality_code.astype(str),
                "target_year": evaluation.target_year.astype(int),
                "error_class": evaluation.error_type.astype("string"),
            }
        )
        evaluation_exposure = float(
            exposure_table(parts).query("role == 'evaluation'").monitored_exposure.sum()
        )
        exposure_rows = exposure_table(parts).query("role == 'evaluation'")
        exposure_by_municipality_year = {
            (str(row.municipality_code), int(row.target_year)): float(row.monitored_exposure)
            for row in exposure_rows.itertuples(index=False)
        }
        summary = metrics(metric_frame, exposure=evaluation_exposure)
        cell_id = digest(spec)
        result = {
            **spec,
            "cell_id": cell_id,
            "status": "evaluable",
            "rows": summary["rows"],
            "average_precision": summary["average_precision"],
            "brier": summary["brier"],
            "sensitivity": summary["sensitivity"],
            "false_alerts": summary["false_alerts"],
            "alerts_emitted": summary["alerts_emitted"],
            "threshold": threshold["threshold"],
            "budget": p["budget"]["B_primary"],
            "false_alert_limit": threshold["false_alert_limit"],
            "metrics": summary,
            "predictors": columns,
            "cohort_sha256": hashlib.sha256(
                common[KEYS].to_json(orient="records").encode()
            ).hexdigest(),
            "predictors_sha256": digest({"predictors": columns}),
        }
        results.append(result)
        thresholds.append(
            {
                "cell_id": cell_id,
                "threshold": threshold["threshold"],
                "budget": p["budget"]["B_primary"],
                "selection_exposure": exposure,
                "false_alert_limit": threshold["false_alert_limit"],
            }
        )
        for row_index, row in evaluation.iterrows():
            predictions.append(
                {
                    "cell_id": cell_id,
                    "municipality_code": str(row.municipality_code),
                    "origin_month": str(row.year_month),
                    "target_month": str(row.target_month),
                    "score": float(scores.loc[row_index]),
                    "alert": bool(alerts.loc[row_index]),
                    "truth": int(row[target]),
                    "error_class": str(row.error_type),
                    "objective": spec["objective"],
                    "variant": spec["variant"],
                    "family": spec["family"],
                    "horizon": horizon,
                    "cut": spec["cut"],
                    "exposure": exposure_by_municipality_year.get(
                        (str(row.municipality_code), int(row.target_year)), 0.0
                    ),
                }
            )
    if len(results) != 96:
        raise ValueError("EXP03.1 did not produce all 96 frozen cell results")
    contrast_definitions = {
        "Q1": ["M01", "M00"],
        "Q2": ["M02", "M01"],
        "Q3": ["M02", "M00"],
    }
    prediction_frame = pd.DataFrame(predictions)
    paired_effects: list[dict[str, Any]] = []
    for contrast_name, (left_variant, right_variant) in contrast_definitions.items():
        left_cells = {
            (row["objective"], row["family"], row["horizon"], row["cut"])
            for row in results
            if row["variant"] == left_variant
        }
        right_cells = {
            (row["objective"], row["family"], row["horizon"], row["cut"])
            for row in results
            if row["variant"] == right_variant
        }
        for objective, family, horizon, cut in sorted(left_cells & right_cells):
            left = prediction_frame.loc[
                (prediction_frame.variant == left_variant)
                & (prediction_frame.objective == objective)
                & (prediction_frame.family == family)
                & (prediction_frame.horizon == horizon)
                & (prediction_frame.cut == cut)
            ].copy()
            right = prediction_frame.loc[
                (prediction_frame.variant == right_variant)
                & (prediction_frame.objective == objective)
                & (prediction_frame.family == family)
                & (prediction_frame.horizon == horizon)
                & (prediction_frame.cut == cut)
            ].copy()
            delta = paired_effect(left, right, ["municipality_code", "target_month"])
            paired_effects.extend(
                {
                    "contrast": contrast_name,
                    "left_variant": left_variant,
                    "right_variant": right_variant,
                    "objective": objective,
                    "family": family,
                    "horizon": horizon,
                    "cut": cut,
                    **row,
                }
                for row in delta.to_dict(orient="records")
            )
    reuse = reuse_decision({}, {})
    plan = execution_plan(reuse)
    if plan["counts"] != {"total": 96, "reused": 0, "new_fits": 96}:
        raise ValueError("EXP03.1 M00 identity did not fail closed to the refit path")
    return {
        "protocol_sha256": digest(p),
        "matrix_sha256": digest(matrix(p)),
        "cells": results,
        "predictions": predictions,
        "thresholds": thresholds,
        "contrasts": {
            "definitions": contrast_definitions,
            "paired_effects": paired_effects,
        },
        "execution_plan": plan,
        "reuse_decision": reuse,
        "execution_counters": {
            "real_private_reads": 0,
            "real_reservations": 0,
            "real_model_fits": 0,
            "real_calibrator_fits": 0,
            "real_threshold_selections": 0,
            "permanent_mlflow_writes": 0,
        },
    }


def _reserve(provenance: dict[str, Any]) -> Path:
    root = safe_path(OUTPUT_ROOT, OUTPUT_ROOT)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    execution_id = digest(provenance)
    reservation = safe_path(str(root / (execution_id + ".reservation")))
    with reservation.open("x", encoding="utf-8") as stream:
        stream.write(execution_id + "\n")
    return reservation


def execute_authorized(sources: dict[str, Any]) -> dict[str, Any]:
    """Revalidate approval and admission before opening tracking or fitting."""
    from sat_dengue.experiments.exp03_1_contract import digest as protocol_digest
    from sat_dengue.experiments.exp03_admission import reverify
    from sat_dengue.tracking.exp03_1 import Exp03_1Tracking

    receipt = sources["preflight"]
    parameters = sources["parameters"]
    approval = authorize(receipt, parameters)
    if digest(approval) != sources["approval_sha256"]:
        raise PermissionError("EXP03.1 authorization changed after source admission")
    reverify(sources["admission"])
    provenance = {
        "experiment_id": "EXP031",
        "protocol_sha256": protocol_digest(protocol()),
        "matrix_sha256": receipt["matrix_sha256"],
        "source_admission": sources["admission"],
        "data_sha256": digest(sources["admission"]["files"]),
        "data_version": sources["admission"]["expected_source_sha256"],
        "admission_sha256": digest(sources["admission"]),
        "authorization_receipt_sha256": digest(receipt),
        "approval_sha256": digest(approval),
        "approval_record": approval,
        "configuration_sha256": receipt["configuration_sha256"],
        "tracking_root": receipt["tracking_root"],
        "source_descriptor_sha256": receipt["source_descriptor_sha256"],
        "git_revision": receipt["git_revision"],
        "code_sha256": receipt["code_sha256"],
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "real_private_reads": 1,
        "real_model_fits": 0,
        "real_calibrator_fits": 0,
        "mlflow_writes": 0,
    }
    reservation = _reserve(provenance)
    tracker = Exp03_1Tracking(digest(provenance), receipt["tracking_root"], protocol(), provenance)
    try:
        result = execute_matrix(sources["panel"], sources["contract"])
        reverify(sources["admission"])
        provenance.update(
            real_model_fits=result["execution_plan"]["counts"]["new_fits"],
            real_calibrator_fits=result["execution_plan"]["counts"]["new_fits"],
            mlflow_writes=0,
        )
        result["execution_counters"]["real_private_reads"] = len(sources["admission"]["files"])
        result["execution_counters"]["real_reservations"] = 1
        result["execution_counters"]["real_model_fits"] = result["execution_plan"]["counts"][
            "new_fits"
        ]
        result["execution_counters"]["real_calibrator_fits"] = result["execution_plan"]["counts"][
            "new_fits"
        ]
        result["execution_counters"]["real_threshold_selections"] = 96
        return {
            "result": result,
            "provenance": provenance,
            "tracker": tracker,
            "reservation": str(reservation),
        }
    except BaseException:
        tracker.fail()
        raise
