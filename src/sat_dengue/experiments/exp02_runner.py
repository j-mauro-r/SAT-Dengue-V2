"""Protected EXP02 orchestration; scientific functions remain independent of I/O."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import AUTHORITIES, validate_parameters
from sat_dengue.datasets.legacy_preparation.contract import PreparationConfig
from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint
from sat_dengue.datasets.stage2 import NATIVE_IDENTITIES, NATIVE_MANIFEST
from sat_dengue.experiments.exp01 import digest, native_calibration, native_fit, synthetic_fit
from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs
from sat_dengue.experiments.exp01_runner import reserve_execution
from sat_dengue.experiments.exp02_labels import compare_stability, construct_variants, records
from sat_dengue.experiments.exp02_prediction import evaluate_predictive
from sat_dengue.experiments.exp02_preflight import (
    BINDINGS,
    authorize,
    load_protocol,
    safe_path,
    storage_preflight,
)


def guard(context: dict[str, Any], *, contents: bool = False) -> None:
    approval = authorize(context["preflight"])
    if digest(approval) != context["approval_sha256"]:
        raise PermissionError("EXP02 approval changed after admission")
    if contents:
        for relative, expected in context["input_fingerprints"].items():
            if fingerprint(safe_path(relative)) != expected:
                raise ValueError("EXP02 input contents changed")
    storage_preflight(context["preflight"]["tracking_root"])


def load_authorized_sources(receipt: dict[str, Any]) -> dict[str, Any]:
    approval = authorize(receipt)
    if fingerprint(safe_path(NATIVE_MANIFEST)) != NATIVE_IDENTITIES[NATIVE_MANIFEST]:
        raise ValueError("EXP02 approved data version changed")
    prepared = prepare_exp01_inputs(PreparationConfig(Path.cwd()))
    protocol = load_protocol()
    if (
        prepared.panel.year_month.ge("2025-01").any()
        or prepared.panel.municipality_code.nunique() != protocol["population"]["municipalities"]
    ):
        raise ValueError("EXP02 admitted population differs")
    contract = json.loads(
        safe_path(AUTHORITIES["training_preparation_contract_v1"]["path"]).read_text()
    )
    if prepared.contract != contract:
        raise ValueError("EXP02 preparation contract changed")
    provenance = {key: receipt[key] for key in (*BINDINGS, "code", "runtime", "versions")}
    provenance.update(
        {
            "data_sha256": digest(prepared.report["input_fingerprints"]),
            "approval_sha256": digest(approval),
            "evidence_type": "authorized_retrospective",
        }
    )
    context = {
        "panel": prepared.panel,
        "contract": contract,
        "preflight": receipt,
        "input_fingerprints": prepared.report["input_fingerprints"],
        "approval_sha256": digest(approval),
        "provenance": provenance,
    }
    guard(context, contents=True)
    context["execution_id"] = reserve_execution(provenance, receipt["output_root"])
    return context


def construct_authorized(context: dict[str, Any]) -> dict[str, Any]:
    guard(context)
    return {**context, "variants": construct_variants(context["panel"])}


def compare_authorized(context: dict[str, Any]) -> dict[str, Any]:
    guard(context)
    return {
        **context,
        "stability": compare_stability(context["variants"], load_protocol()["design"]),
    }


def predictive_authorized(context: dict[str, Any]) -> dict[str, Any]:
    guard(context, contents=True)
    counts = {"fit": 0, "calibration": 0}

    def fit(*args: Any) -> Any:
        guard(context)
        counts["fit"] += 1
        if counts["fit"] > 54:
            raise ValueError("EXP02 fit budget exceeded")
        return native_fit(*args)

    def calibrate(*args: Any) -> Any:
        guard(context)
        counts["calibration"] += 1
        if counts["calibration"] > 54:
            raise ValueError("EXP02 calibration budget exceeded")
        return native_calibration(*args)

    predictive = evaluate_predictive(
        context["panel"],
        context["contract"],
        context["variants"],
        load_protocol()["design"],
        fit=fit,
        calibrate=calibrate,
    )
    guard(context, contents=True)
    return {**context, "predictive": predictive}


def result_from_context(context: dict[str, Any], *, synthetic: bool) -> dict[str, Any]:
    return {
        "schema": "exp02-result-v1",
        "experiment_id": "EXP02",
        "evidence_type": "synthetic_interface_probe" if synthetic else "authorized_retrospective",
        "G5": "NOT_APPROVED",
        "champion": "not_selected",
        "stability": context["stability"],
        "predictive": context["predictive"],
        "labels": {str(h): records(v["states"]) for h, v in context["variants"].items()},
        "episodes": {str(h): v["episodes"] for h, v in context["variants"].items()},
    }


def publication_authorized(context: dict[str, Any]) -> dict[str, Any]:
    guard(context, contents=True)
    return {
        "result": result_from_context(context, synthetic=False),
        "context": context,
        "provenance": context["provenance"],
    }


def synthetic_inputs() -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    """Generated counts and climate only; no source descriptor or private loader."""
    contract = json.loads(
        safe_path(AUTHORITIES["training_preparation_contract_v1"]["path"]).read_text()
    )
    design = copy.deepcopy(load_protocol()["design"])
    rng = np.random.default_rng(design["seed"])
    rows = []
    for municipality in ["50001", "50002", "50003", "73001", "73002", "73003"]:
        for month in pd.period_range("2000-01", "2024-12", freq="M"):
            row = {"municipality_code": municipality, "year_month": str(month)}
            row.update(
                {
                    c: float(rng.integers(0, 30))
                    for c in contract["roles"]["predictors"]
                    if c != "zona_canal_t"
                }
            )
            rows.append(row)
    return pd.DataFrame(rows), contract, design


def synthetic_run(parameters: dict[str, Any]) -> dict[str, Any]:
    if validate_parameters(parameters) != {
        "profile": "exp02_synthetic",
        "tracking": "disabled",
        "experiment_id": "EXP02",
    }:
        raise ValueError("EXP02 synthetic pipeline requires disabled tracking")
    panel, contract, design = synthetic_inputs()
    variants = construct_variants(panel)
    context = {
        "variants": variants,
        "stability": compare_stability(variants, design),
        "predictive": evaluate_predictive(
            panel,
            contract,
            variants,
            design,
            fit=synthetic_fit,
            calibrate=lambda scores, truth, seed: lambda values: values,
            synthetic=True,
        ),
    }
    return result_from_context(context, synthetic=True)
