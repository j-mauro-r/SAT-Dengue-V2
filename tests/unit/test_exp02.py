"""EXP02 frozen compatibility, generated probes and fail-closed infrastructure."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.experiments import exp01, exp02
from sat_dengue.experiments import exp02_preflight as pf
from sat_dengue.experiments.onset import partitions
from sat_dengue.model_training.candidate_preparation import (
    fit_representation,
    transform_representation,
)


def generated() -> tuple[Any, Any, Any]:
    panel, contract, design = exp01.synthetic_inputs()
    frozen = exp02.load_protocol()["design"]
    for w, p in zip(design["windows"], frozen["windows"], strict=True):
        w["id"] = p["id"]
    return panel, contract, {**frozen, "windows": design["windows"]}


@pytest.fixture(scope="module")
def result() -> dict[str, Any]:
    panel, contract, design = generated()
    return exp02.execute(
        panel,
        contract,
        design,
        fit=exp01.synthetic_fit,
        calibrate=lambda s, y, seed: lambda x: x,
        synthetic=True,
    )


def test_exact_variants() -> None:
    p = exp02.load_protocol()["design"]
    full = p["predictors"]
    v = p["variants"]
    assert full == exp01.load_protocol()["design"]["predictors"]
    assert set(full) - set(v["without_current_zone"]) == {"zona_canal_t"}
    assert set(full) - set(v["without_channel"]) == {"zona_canal_t", "zona_canal_lag_1"}
    assert v["history"] == [n for n in full if n in p["groups"]["historia"]]
    assert (
        len(v["history"]) == 9
        and len(v["history_season"]) == 11
        and len(v["history_climate"]) == 24
    )
    assert "municipality_code_feature" not in v["history"]
    assert set(v) == set(exp02.VARIANTS)


def test_probe_counts_and_pairing(result: dict[str, Any]) -> None:
    assert len(result["children"]) == 108
    assert result["synthetic_interface_fits"] == 108
    assert all(
        result[k] == 0 for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits")
    )
    for i in range(0, 108, 6):
        cells = result["children"][i : i + 6]
        assert all(c["role_sha256"] == cells[0]["role_sha256"] for c in cells)
        assert all(c["coverage"] == cells[0]["coverage"] for c in cells)
        assert all(c["status"] == "evaluable" for c in cells)
        for c in cells:
            assert [x["selection_false_alert_budget"] for x in c["frontier"]] == list(
                range(len(c["frontier"]))
            )
            assert all(
                x["paired_interval"]["status"] == "insufficient_cluster_support"
                for x in c["frontier"]
            )


def test_determinism(result: dict[str, Any]) -> None:
    p, c, d = generated()
    assert (
        exp02.execute(
            p,
            c,
            d,
            fit=exp01.synthetic_fit,
            calibrate=lambda s, y, seed: lambda x: x,
            synthetic=True,
        )
        == result
    )


def test_production_fitter_not_synthetic() -> None:
    p, c, d = generated()
    with pytest.raises(ValueError, match="Synthetic route"):
        exp02.execute(
            p, c, d, fit=exp02.native_fit, calibrate=exp01.native_calibration, synthetic=True
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


@pytest.mark.parametrize("variant", exp02.VARIANTS)
def test_exclusions_remove_all_encodings(variant: str) -> None:
    p, c, d = generated()
    cohort = exp01.prepare(p, c, 1)
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
        "tmp/kedro-migration/exp02-runs-neighbor",
        "tmp/../outside",
        "https://host/x",
        "/outside/exp02-runs",
    ],
)
def test_paths_rejected(bad: str) -> None:
    from sat_dengue.datasets.exp02 import Exp02BundleDataset

    with pytest.raises(ValueError):
        Exp02BundleDataset(bad)


def test_kedro_absolute_and_symlink(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.datasets.exp02 import Exp02BundleDataset

    monkeypatch.chdir(repo_tmp_path)
    a = Exp02BundleDataset(pf.OUTPUT_ROOT)
    b = Exp02BundleDataset(str(repo_tmp_path / pf.OUTPUT_ROOT))
    assert a._describe() == b._describe()
    (repo_tmp_path / "tmp").mkdir()
    target = repo_tmp_path / "real"
    target.mkdir()
    (repo_tmp_path / "tmp/kedro-migration").symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink"):
        Exp02BundleDataset(pf.OUTPUT_ROOT)


def test_missing_approval_before_load(monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.experiments.exp02_runner import load_authorized_sources

    monkeypatch.delenv("SAT_DENGUE_EXP02_APPROVAL", raising=False)
    with pytest.raises(PermissionError):
        load_authorized_sources({})


def test_preflight_no_private_reads_or_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    from kedro.io import DataCatalog

    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.pipeline_registry import register_pipelines

    # Real catalog is resolved absolutely by Kedro; descriptor cannot read data.
    cat = DataCatalog.from_config(
        ValidatedConfigLoader("conf", base_env="base", default_run_env="base")["catalog"]
    )
    assert cat.load("exp02_sources") == pf.descriptor()
    assert register_pipelines()["exp02"].outputs() == {"exp02_bundle"}
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
    original = Path.open

    def guarded(path: Path, *a: Any, **kw: Any) -> Any:
        mode = a[0] if a else kw.get("mode", "r")
        assert not str(path).startswith("data/")
        assert not any(ch in str(mode) for ch in ("w", "a", "x", "+"))
        return original(path, *a, **kw)

    monkeypatch.setattr(Path, "open", guarded)
    r = pf.preflight(
        {"profile": "exp02_preflight", "tracking": "enabled", "experiment_id": "EXP02"},
        pf.descriptor(),
    )
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
    monkeypatch.setenv("SAT_DENGUE_EXP02_APPROVAL", str(file))
    with pytest.raises(PermissionError, match="Invalid"):
        pf.authorize({})


def test_non_evaluable_variants_retained() -> None:
    p, c, d = generated()
    p["rain_mm_month_sum"] = pd.NA
    r = exp02.execute(
        p, c, d, fit=exp01.synthetic_fit, calibrate=lambda s, y, seed: lambda x: x, synthetic=True
    )
    assert len(r["children"]) == 108 and r["synthetic_interface_fits"] == 0
    assert all(x["status"] == "non_evaluable" for x in r["children"])


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
        "schema": "exp02-execution-approval-v1",
        "experiment_id": "EXP02",
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
    monkeypatch.setenv("SAT_DENGUE_EXP02_APPROVAL", str(file))
    fresh = copy.deepcopy(receipt)
    fresh["tracking"]["state"] = "existing_read_only_verified"
    monkeypatch.setattr(pf, "preflight", lambda parameters, sources: fresh)
    monkeypatch.setattr(pf, "git_identity", lambda: {"git_dirty": False})
    assert pf.authorize(receipt) == approval
    reverse = copy.deepcopy(fresh)
    fresh["tracking"]["state"] = "not_initialized"
    with pytest.raises(PermissionError, match="disappeared"):
        pf.authorize(reverse)
    fresh["tracking"]["state"] = "existing_read_only_verified"
    fresh["configuration_sha256"] = "e" * 64
    with pytest.raises(PermissionError, match="Stale"):
        pf.authorize(receipt)


def test_reservation_survives_retry(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.experiments.exp02_runner import reserve_execution

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

    design = exp02.load_protocol()["design"]
    cols = design["variants"]["history"]
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
        assert set(excluded) == set(frame) - set(cols)

        class Model:
            def predict(self, frame: Any) -> pd.Series:
                return pd.Series([0.0, 1.0], index=frame.index)

        return Model()

    monkeypatch.setattr(candidate_families.ADAPTERS[family], "fit_candidate", stub)
    model = exp02.native_fit(family, X, y, design["families"][family], 42)
    assert list(model.predict(X)) == [0.0, 1.0]
