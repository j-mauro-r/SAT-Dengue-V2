"""EXP03 frozen compatibility, generated probes and fail-closed infrastructure."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments import exp01, exp03
from sat_dengue.experiments import exp03_preflight as pf
from sat_dengue.experiments.onset import partitions
from sat_dengue.model_training.candidate_preparation import (
    fit_representation,
    transform_representation,
)


def generated() -> tuple[Any, Any, Any]:
    panel, contract, _ = exp01.synthetic_inputs()
    panel["year_month"] = [str(pd.Period(v, freq="M") + 180) for v in panel.year_month]
    return panel, contract, exp03.load_protocol()["design"]


@pytest.fixture(scope="module")
def result() -> dict[str, Any]:
    return exp03.synthetic_run()


def test_exact_variants() -> None:
    from sat_dengue.experiments.exp03_features import validate_design

    design = exp03.load_protocol()["design"]
    assert validate_design(design) == 240
    assert len(design["variants"]) == len({frozenset(v) for v in design["variants"].values()}) == 10
    assert all("municipality_code_feature" in v for v in design["variants"].values())
    assert set(design["inventory"]) == set(design["predictors"])
    altered = copy.deepcopy(design)
    altered["variants"]["baseline_plus_sir"] = altered["variants"]["baseline_history_season"]
    with pytest.raises(ValueError, match="duplicate"):
        validate_design(altered)
    altered = copy.deepcopy(design)
    altered["windows"] = [w for w in altered["windows"] if w["id"] != "development_2021"]
    with pytest.raises(ValueError, match="temporal support"):
        validate_design(altered)


def test_probe_counts_pairing_and_canonical_reuse(result: dict[str, Any]) -> None:
    assert len(result["children"]) == result["synthetic_interface_fits"] == 240
    assert all(
        result[k] == 0 for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits")
    )
    cells = {c["cell_id"]: c for c in result["children"]}
    assert len(cells) == 240
    assert not any(c["variant"] == "full_without_climate" for c in cells.values())
    rows = result["contrasts"]
    assert {r["contrast_id"] for r in rows} == {
        c["id"] for c in exp03.load_protocol()["design"]["contrasts"]
    }
    for row in rows:
        for side in ("left", "right"):
            assert all(cells[c]["variant"] == row[side + "_variant"] for c in row[side + "_cells"])
        if row["contrast_id"] == "full_without_climate":
            assert row["right_variant"] == "baseline_plus_complete_channel"
            assert row["semantic_roles"] == {"right": "full_without_climate"}
        if row["window"] == "development_oof":
            assert row["evaluation_years"] == ["2020", "2021", "2022"]
            assert row["paired_interval"]["status"] == "retrospective_paired"
            assert "stress_2024" not in row["source_cuts"]
    for family in exp03.load_protocol()["design"]["families"]:
        for h in (1, 2):
            for window in exp03.load_protocol()["design"]["windows"]:
                group = [
                    c
                    for c in cells.values()
                    if c["family"] == family and c["horizon"] == h and c["window"] == window["id"]
                ]
                assert len({c["cohort_sha256"] for c in group}) == 1
                assert len({exp01.digest(c["role_sha256"]) for c in group}) == 1
    assert all(r["automatic_selection"] is False for r in result["decision_candidates"])
    assert all(
        r["analysis"] == "secondary_coverage_not_paired_prediction"
        for r in result["operational_coverage"]
    )


def test_production_fitter_not_synthetic() -> None:
    p, c, d = generated()
    with pytest.raises(ValueError, match="Synthetic route"):
        exp03.execute(
            p, c, d, fit=exp03.native_fit, calibrate=exp01.native_calibration, synthetic=True
        )


def test_consumed_year_and_stress() -> None:
    p, c, d = generated()
    p.loc[0, "year_month"] = "2025-01"
    with pytest.raises(ValueError, match="2025"):
        exp01.prepare(p, c, 2)
    p, c, d = generated()
    cohort = exp01.prepare(p, c, 2)
    w = copy.deepcopy(d["windows"][0])
    w["selection"] = ["2024-01", "2024-06"]
    with pytest.raises(ValueError):
        partitions(cohort, w)


@pytest.mark.parametrize("variant", exp03.VARIANTS)
def test_exclusions_remove_all_encodings(variant: str) -> None:
    p, c, d = generated()
    from sat_dengue.experiments.exp03_features import prepare

    cohort = prepare(p, c, 1)
    full = d["predictors"]
    f = (
        cohort[full]
        .dropna()
        .iloc[:30]
        .rename(columns={"municipality_code_feature": "municipality_code"})
    )
    removed = [
        ("municipality_code" if n == "municipality_code_feature" else n)
        for n in full
        if n not in d["variants"][variant]
    ]
    state = fit_representation(f, removed)
    matrix = transform_representation(f, state)
    assert not any(n.split("=", 1)[0] in removed for n in matrix)
    assert set(n.split("=", 1)[0] for n in matrix) == set(f) - set(removed)


@pytest.mark.parametrize(
    "bad",
    [
        "tmp/kedro-migration/exp03-runs-neighbor",
        "tmp/../outside",
        "https://host/x",
        "/outside/exp03-runs",
    ],
)
def test_paths_rejected(bad: str) -> None:
    from sat_dengue.datasets.exp03 import Exp03BundleDataset

    with pytest.raises(ValueError):
        Exp03BundleDataset(bad)


def test_kedro_absolute_and_symlink(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.datasets.exp03 import Exp03BundleDataset

    monkeypatch.chdir(repo_tmp_path)
    a = Exp03BundleDataset(pf.OUTPUT_ROOT)
    b = Exp03BundleDataset(str(repo_tmp_path / pf.OUTPUT_ROOT))
    assert a._describe() == b._describe()
    (repo_tmp_path / "tmp").mkdir()
    target = repo_tmp_path / "real"
    target.mkdir()
    (repo_tmp_path / "tmp/kedro-migration").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        Exp03BundleDataset(pf.OUTPUT_ROOT)


def test_missing_approval_before_load(monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.experiments.exp03_runner import load_authorized_sources

    monkeypatch.delenv("SAT_DENGUE_EXP03_APPROVAL", raising=False)
    with pytest.raises(PermissionError):
        load_authorized_sources({})


def test_preflight_no_private_reads_or_writes(
    monkeypatch: pytest.MonkeyPatch, repo_tmp_path: Path
) -> None:
    from kedro.io import DataCatalog

    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipeline_registry import register_pipelines

    # Real catalog is resolved absolutely by Kedro; descriptor cannot read data.
    cat = DataCatalog.from_config(
        ValidatedConfigLoader("conf", base_env="base", default_run_env="base")["catalog"]
    )
    assert cat.load("exp03_sources") == pf.descriptor()
    assert register_pipelines()["exp03"].outputs() == {"exp03_bundle"}
    monkeypatch.setattr(pf, "runtime_versions", lambda: {"probe": "generated"})
    monkeypatch.setattr(
        pf,
        "execution_metadata",
        lambda: {
            "code": {},
            "runtime": {},
            "code_sha256": exp01.digest({}),
            "environment_sha256": exp01.digest({}),
        },
    )
    root = str(repo_tmp_path.relative_to(Path.cwd()) / "store-a")
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", root)
    original = Path.open

    def guarded(path: Path, *a: Any, **kw: Any) -> Any:
        mode = a[0] if a else kw.get("mode", "r")
        assert not str(path).startswith("data/")
        assert not any(ch in str(mode) for ch in ("w", "a", "x", "+"))
        return original(path, *a, **kw)

    monkeypatch.setattr(Path, "open", guarded)
    r = pf.preflight(
        {"profile": "exp03_preflight", "tracking": "enabled", "experiment_id": "EXP03"},
        pf.descriptor(),
    )
    assert r["tracking"]["root"] == root
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", root + "-other")
    other = pf.preflight(
        {"profile": "exp03_preflight", "tracking": "enabled", "experiment_id": "EXP03"},
        pf.descriptor(),
    )
    assert r["configuration_sha256"] != other["configuration_sha256"]
    assert r["execution_ready"] is False
    assert all(
        r[k] == 0
        for k in (
            "real_model_fits",
            "calibrator_fits",
            "private_reads",
            "reservations",
            "mlflow_writes",
            "writes",
        )
    )


def test_invalid_approval(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(repo_tmp_path)
    (repo_tmp_path / "tmp").mkdir()
    file = repo_tmp_path / "tmp/approval.json"
    file.write_text("{}")
    monkeypatch.setenv("SAT_DENGUE_EXP03_APPROVAL", str(file))
    with pytest.raises(PermissionError, match="Invalid"):
        pf.authorize({})


def test_non_evaluable_variants_retained() -> None:
    p, c, d = generated()
    p["rain_mm_month_sum"] = pd.NA
    with pytest.raises(ValueError, match="Insufficient common"):
        exp03.execute(
            p,
            c,
            d,
            fit=exp01.synthetic_fit,
            calibrate=lambda s, y, seed: lambda x: x,
            synthetic=True,
        )


def test_approval_tracks_initialization_but_rejects_mutation(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(repo_tmp_path)
    (repo_tmp_path / "tmp").mkdir()
    receipt: dict[str, Any] = {
        "protocol_sha256": "a" * 64,
        "git_revision": "b" * 40,
        "data_version": "c" * 64,
        "configuration_sha256": "d" * 64,
        "git_dirty": False,
        "tracking": {"root": pf.TRACKING_ROOT, "state": "not_initialized", "writes": 0},
    }
    approval = {
        "schema": "exp03-execution-approval-v1",
        "experiment_id": "EXP03",
        "authority": "Mauricio",
        "independent_reviewer": "GeneratedReviewer",
        "real_execution_authorized": True,
        "comparator_refit_authorized": True,
        "variant_refits_authorized": True,
        "retrospective_availability_acknowledged": True,
        **{
            k: receipt[k]
            for k in ("protocol_sha256", "git_revision", "data_version", "configuration_sha256")
        },
    }
    file = repo_tmp_path / "tmp/generated-approval.json"
    file.write_text(json.dumps(approval))
    monkeypatch.setenv("SAT_DENGUE_EXP03_APPROVAL", str(file))
    fresh = copy.deepcopy(receipt)
    fresh["tracking"]["state"] = "existing_read_only_verified"
    monkeypatch.setattr(pf, "preflight", lambda parameters, sources: fresh)
    monkeypatch.setattr(pf, "git_identity", lambda: {"git_dirty": False})
    assert pf.authorize(receipt) == approval
    prior_root = fresh["tracking"]["root"]
    fresh["tracking"]["root"] = prior_root + "-different"
    with pytest.raises(PermissionError, match="Stale"):
        pf.authorize(receipt)
    fresh["tracking"]["root"] = prior_root

    reverse = copy.deepcopy(fresh)
    fresh["tracking"]["state"] = "not_initialized"
    with pytest.raises(PermissionError, match="disappeared"):
        pf.authorize(reverse)
    fresh["tracking"]["state"] = "existing_read_only_verified"
    fresh["configuration_sha256"] = "e" * 64
    with pytest.raises(PermissionError, match="Stale"):
        pf.authorize(receipt)


def test_reservation_survives_retry(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.experiments.exp03_runner import reserve_execution

    monkeypatch.chdir(repo_tmp_path)
    provenance = {"configuration_sha256": "a" * 64}
    first = reserve_execution(provenance)
    assert len(first) == 64
    with pytest.raises(FileExistsError):
        reserve_execution(provenance)
    assert len(list((repo_tmp_path / pf.OUTPUT_ROOT).iterdir())) == 1


@pytest.mark.parametrize("family", ["gam", "lightgbm", "xgboost"])
def test_adapter_keeps_only_projected_columns(family: str, monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.model_training import candidate_families

    design = exp03.load_protocol()["design"]
    cols = design["variants"]["baseline_history_season"]
    X = pd.DataFrame({n: [1.0, 2.0] for n in cols})
    y = pd.Series([0, 1])

    def stub(
        frame: Any, truth: Any, parameters: Any, *, seed: Any, threads: Any, excluded: Any
    ) -> Any:
        assert set(frame) == {
            n.replace("municipality_code_feature", "municipality_code")
            for n in design["predictors"]
        }
        assert all(frame[n].isna().all() for n in excluded)
        assert set(excluded) == set(frame) - {
            n.replace("municipality_code_feature", "municipality_code") for n in cols
        }

        class Model:
            def predict(self, frame: Any) -> pd.Series:
                return pd.Series([0.0, 1.0], index=frame.index)

        return Model()

    monkeypatch.setattr(candidate_families.ADAPTERS[family], "fit_candidate", stub)
    model = exp03.native_fit(family, X, y, design["families"][family], 42)
    assert list(model.predict(X)) == [0.0, 1.0]


@pytest.mark.parametrize(
    "root", [pf.OUTPUT_ROOT, pf.OUTPUT_ROOT + "/nested", "tmp/kedro-migration"]
)
def test_tracking_root_rejects_result_overlap(root: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", root)
    with pytest.raises(ValueError, match="separate"):
        pf.tracking_root()
