"""Generated cohort tests and metadata/hash-only verification of prepared annex."""

import copy
import hashlib
import json

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data.exp_delta03_retrospective import row_hash
from sat_dengue.datasets.exp_delta03_training import ROOT, verify_annex_preparation
from sat_dengue.experiments.exp_delta03_annex import prepare_cohorts
from sat_dengue.experiments.exp_delta03_contract import validate_freeze


def fixture():
    national = pd.DataFrame(
        {
            "divipola_municipio": ["05001", "50001", "50001", "50001"],
            "divipola_departamento": ["05", "50", "50", "50"],
            "periodo_mes": ["2019-12", "2019-12", "2020-01", "2024-12"],
            "onset_T1": [1, 0, 1, 1],
            "g1_no_climate_t1": [True, True, False, True],
            "y_evaluable_t1": [True, True, True, True],
        }
    )
    original = national.iloc[[1]].rename(columns={"onset_T1": "truth"}).copy()
    original["horizon"], original["year"], original["role"], original["primary"] = (
        1,
        2020,
        "evaluation",
        True,
    )
    plan = {
        "cells": [
            {
                "variant": "FULL_COMMON",
                "horizon": 1,
                "year": 2020,
                "roles": {
                    "evaluation": {
                        "key_label_sha256": row_hash(
                            original, ["divipola_municipio", "periodo_mes", "truth"]
                        )
                    }
                },
            }
        ]
    }
    return national, original, plan


def test_annex_preserves_regions_and_independent_monitored_exposure():
    national, original, plan = fixture()
    cohorts, calendar, summaries = prepare_cohorts(national, original, plan)
    assert len(cohorts) == 2 and len(calendar) == 3
    assert summaries[0]["eligible_municipality_years"] == 2 / 12
    assert summaries[0]["monitored_municipality_years"] == 3 / 12
    assert summaries[0]["regional_correspondence"] == "EXACT"
    assert not cohorts.target_month.str.startswith("2025").any()


@pytest.mark.parametrize("mutation", ["duplicate", "label", "calendar", "geography", "unknown"])
def test_annex_rejects_source_drift(mutation):
    national, original, plan = fixture()
    if mutation == "duplicate":
        national = pd.concat([national, national.iloc[:1]], ignore_index=True)
    if mutation == "label":
        national.loc[1, "onset_T1"] = 1
    if mutation == "calendar":
        national.loc[0, "y_evaluable_t1"] = False
    if mutation == "geography":
        national.loc[0, "divipola_departamento"] = "50"
    if mutation == "unknown":
        national["g1_no_climate_t1"] = national.g1_no_climate_t1.astype(object)
        national.loc[0, "g1_no_climate_t1"] = None
    with pytest.raises(ValueError):
        prepare_cohorts(national, original, plan)


def test_approved_public_freeze_still_has_no_execution_grant():
    owner = ROOT / "docs/product/experiments/EXP-DELTA03"
    contract = json.loads((owner / "training-contract.json").read_bytes())
    validate_freeze(contract, synthetic=False)
    assert contract["decision_status"] == "APPROVED_FOR_PHASE2_IMPLEMENTATION"
    assert contract["model"]["n_estimators"] == 80
    assert contract["model"]["max_depth"] == 2
    assert contract["model"]["learning_rate"] == 0.05
    assert contract["model_search"] == "none"
    assert contract["calibration"]["penalty"] == 1
    assert contract["calibration"]["fit_role"] == "calibration_only"
    assert contract["policy"]["B"] == 1 and contract["policy"]["rounding"] == "floor"
    assert contract["policy"]["selection_role"] == "selection_only"
    assert contract["policy"]["ties"] == "whole score ties"
    assert contract["uncertainty"]["draws"] == 1000
    assert contract["uncertainty"]["confidence"] == 0.95
    assert contract["uncertainty"]["minimum_valid_fraction"] == 0.8
    assert contract["uncertainty"]["minimum_municipalities"] == 2
    assert contract["uncertainty"]["minimum_temporal_blocks"] == 2
    assert contract["uncertainty"]["iid_row_fallback"] is False
    assert contract["G5"] == "NOT_APPROVED" and contract["champion"] == "not_selected"
    for value in [contract, json.loads((owner / "protocol.draft.json").read_bytes())]:
        assert value["execution"] == "not_authorized"
        assert value["phase3_authorized"] is value["training_authorized"] is False
        assert value["operational_PIT"] is False
        assert value["preparation_regime"] == "RETROSPECTIVE_CONSOLIDATED"
    approval = contract["approval"]
    assert approval["task"] == "T-final-review"
    assert (
        hashlib.sha256((ROOT / approval["document"]).read_bytes()).hexdigest()
        == approval["document_sha256"]
    )
    invalid = copy.deepcopy(contract)
    invalid["decision_status"] = "APPROVED"
    with pytest.raises(ValueError, match="human freeze"):
        validate_freeze(invalid, synthetic=False)


def test_annex_verification_reads_no_private_table_rows(tmp_path, monkeypatch):
    from sat_dengue.datasets.exp_delta03 import canonical

    def forbidden(*args, **kwargs):
        raise AssertionError("Private row parsing is forbidden")

    monkeypatch.setattr(pd, "read_csv", forbidden)
    report = {
        "schema": "exp-delta03-annex-preparation-v1",
        "status": "PREPARED_WITH_EXPLICIT_PENDING_INPUTS",
        "execution_ready": False,
        "pending_inputs": ["generated missing X"],
        "phase1_manifest_sha256": "a" * 64,
        "activity_counters": {
            k: 0
            for k in [
                "real_model_fits",
                "real_calibrations",
                "real_predictions",
                "permanent_mlflow_writes",
            ]
        },
    }
    payloads = {
        "preparation.json": canonical(report),
        "national-primary-cohorts.csv": b"generated,cohort\n",
        "national-primary-monitored-calendar.csv": b"generated,calendar\n",
    }
    records = {
        n: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
        for n, b in sorted(payloads.items())
    }
    bundle = hashlib.sha256(canonical(records)).hexdigest()
    folder = tmp_path / "data/processed/exp_delta03-inputs" / bundle
    folder.mkdir(parents=True)
    for n, b in payloads.items():
        (folder / n).write_bytes(b)
    manifest = canonical({"bundle_id": bundle, "files": records})
    (folder / "manifest.json").write_bytes(manifest)
    report.update(
        files=records,
        protected_preparation={
            "path": str(folder.relative_to(tmp_path)),
            "bundle_id": bundle,
            "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        },
    )
    public = tmp_path / "docs/product/experiments/EXP-DELTA03/ANNEX-PREPARATION.json"
    public.parent.mkdir(parents=True)
    public.write_text(json.dumps(report))
    contract = {
        "annex_preparation": {
            "path": str(public.relative_to(tmp_path)),
            "sha256": hashlib.sha256(public.read_bytes()).hexdigest(),
        },
        "matrix_bundle": {"manifest_sha256": "a" * 64},
    }
    assert verify_annex_preparation(tmp_path, contract)["execution_ready"] is False
    altered = copy.deepcopy(contract)
    altered["annex_preparation"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="inventory changed"):
        verify_annex_preparation(tmp_path, altered)
    (folder / "national-primary-cohorts.csv").write_bytes(b"changed")
    with pytest.raises(ValueError, match="member changed"):
        verify_annex_preparation(tmp_path, contract)
