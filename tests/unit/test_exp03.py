"""Revised EXP03 generated acceptance and fail-closed execution admission."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from sat_dengue.experiments import exp01, exp03
from sat_dengue.experiments import exp03_preflight as pf
from sat_dengue.experiments.exp03_engine import require_budget
from sat_dengue.experiments.exp03_revision import cell_counts, validate_design


def test_exact_variants_and_fixed_identity() -> None:
    design = exp03.load_protocol()["design"]
    assert validate_design(design) == 408
    assert cell_counts(design) == dict(onset=384, excess=24, total=408, terminal=102)
    assert design["B_primary"] == 1.0
    assert len({frozenset(v) for v in design["variants"].values()}) == 16
    assert set(design["inventory"]) == set(design["predictors"])
    bad = copy.deepcopy(design)
    bad["variants"]["V03"] = bad["variants"]["V00"]
    with pytest.raises(ValueError):
        validate_design(bad)


def test_probe_counts_pairing_freeze_and_controls(exp03_generated_result: dict) -> None:
    r = exp03_generated_result
    assert len(r["children"]) == r["synthetic_interface_fits"] == 408
    assert all(r[k] == 0 for k in ("real_model_fits", "real_preparer_refits", "calibrator_fits"))
    assert len({c["cell_id"] for c in r["children"]}) == 408
    assert r["terminal_manifest"]["terminal_cell_count"] == 102
    assert r["terminal_manifest"]["evaluation_outputs_opened"] is False
    assert len(r["terminal_manifest"]["reload_verification"]) == 102
    assert len(r["contrasts"]) == 204
    phases = r["execution_counters"]
    assert phases["development_oof"]["model_fits"] == 306
    assert phases["terminal_stress_2024"]["model_fits"] == 102
    assert phases["consumed_2025_benchmark"]["model_fits"] == 0
    assert all(v["searches"] == 0 for v in phases.values())
    assert not any(c["objective"] == "excess" and c["horizon"] == 1 for c in r["children"])
    for family in exp03.load_protocol()["design"]["families"]:
        for h in (1, 2):
            for window in exp03.load_protocol()["design"]["windows"]:
                cells = [
                    c
                    for c in r["children"]
                    if c["family"] == family and c["horizon"] == h and c["window"] == window["id"]
                ]
                assert len({c["cohort_sha256"] for c in cells}) == 1
                assert len({exp01.digest(c["role_sha256"]) for c in cells}) == 1
    for row in r["contrasts"]:
        assert row["decision"]["automatic_selection"] is False
        if row["tier"] == "objective_control":
            assert row["decision"]["calibration"] == "unknown"
        if row["window"] == "pooled_development":
            assert row["source_cuts"] == [
                "development_2020",
                "development_2021",
                "development_2022",
            ]


def test_budget_blocks_before_any_sources_or_fits(monkeypatch: pytest.MonkeyPatch) -> None:
    import sat_dengue.experiments.exp03_runner as runner
    from sat_dengue.experiments.exp01_inputs import prepare_exp01_inputs

    def forbidden(*a: Any, **kw: Any) -> Any:
        raise AssertionError("private reader reached")

    protocol = exp03.load_protocol()
    protocol["design"]["B_primary"] = None
    monkeypatch.setattr(runner, "load_protocol", lambda: protocol)
    monkeypatch.setattr("sat_dengue.experiments.exp01_inputs.prepare_exp01_inputs", forbidden)
    with pytest.raises(PermissionError, match="B_primary"):
        runner.load_authorized_sources({})
    assert callable(prepare_exp01_inputs)
    for value in (None,):
        d = copy.deepcopy(exp03.load_protocol()["design"])
        d["B_primary"] = value
        with pytest.raises(PermissionError):
            require_budget(d)
    d.update(B_primary=1.0, budget_rationale="generated fixture", synthetic_budget_fixture=True)
    with pytest.raises(PermissionError, match="Synthetic budget"):
        require_budget(d)
    assert require_budget(d, synthetic=True)["value"] == 1.0


def test_foreign_generated_flag_does_not_bypass_budget() -> None:
    p, c, _ = exp01.synthetic_inputs()
    design = exp03.load_protocol()["design"]
    design["B_primary"] = None
    with pytest.raises(PermissionError, match="B_primary"):
        exp03.execute(
            p,
            c,
            design,
            fit=exp01.synthetic_fit,
            calibrate=lambda s, y, seed: lambda x: x,
            synthetic=True,
        )


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
    from sat_dengue.experiments import exp03_runner
    from sat_dengue.experiments.exp03_runner import load_authorized_sources
    from sat_dengue.tracking.local import LocalTracking

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Missing authorization reached scientific side effect")

    monkeypatch.setattr(exp03_runner, "native_fit", forbidden)
    monkeypatch.setattr(exp03_runner, "fit_calibration", forbidden)
    monkeypatch.setattr(exp03_runner, "reserve_execution", forbidden)
    monkeypatch.setattr("sat_dengue.experiments.exp01_inputs.prepare_exp01_inputs", forbidden)
    monkeypatch.setattr(LocalTracking, "__init__", forbidden)
    monkeypatch.delenv("SAT_DENGUE_EXP03_APPROVAL", raising=False)
    with pytest.raises(PermissionError):
        load_authorized_sources({})


def test_preflight_no_private_reads_or_writes(
    monkeypatch: pytest.MonkeyPatch, repo_tmp_path: Path
) -> None:
    import builtins

    from kedro.io import DataCatalog

    from sat_dengue.config_loader import ValidatedConfigLoader
    from sat_dengue.experiments import exp03_runner
    from sat_dengue.pipeline_registry import register_pipelines
    from sat_dengue.tracking.local import LocalTracking

    root_path = Path.cwd().resolve()
    original_open, original_path_open = builtins.open, Path.open

    def guard(path: Any, mode: Any) -> None:
        if isinstance(path, (str, Path)):
            assert not Path(path).resolve().is_relative_to(root_path / "data"), (
                "Private content read"
            )
        assert not any(ch in str(mode) for ch in "wax+"), "Preflight write"

    def guarded_open(file: Any, *a: Any, **kw: Any) -> Any:
        guard(file, a[0] if a else kw.get("mode", "r"))
        return original_open(file, *a, **kw)

    def guarded_path_open(path: Path, *a: Any, **kw: Any) -> Any:
        guard(path, a[0] if a else kw.get("mode", "r"))
        return original_path_open(path, *a, **kw)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Preflight reached scientific side effect")

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(Path, "open", guarded_path_open)
    for name in ("native_fit", "fit_calibration", "reserve_execution"):
        monkeypatch.setattr(exp03_runner, name, forbidden)
    monkeypatch.setattr("sat_dengue.experiments.exp01_inputs.prepare_exp01_inputs", forbidden)
    monkeypatch.setattr(LocalTracking, "__init__", forbidden)
    for private in (Path("data/never-read.csv"), root_path / "data/never-read.csv"):
        for opening in (lambda p=private: p.open(), lambda p=private: builtins.open(p)):
            with pytest.raises(AssertionError, match="Private content read"):
                opening()
    for writing in (
        lambda: Path("tmp/never-written").open("w"),
        lambda: builtins.open("tmp/never-written", "w"),
    ):
        with pytest.raises(AssertionError, match="Preflight write"):
            writing()
    actual_load = DataCatalog.load

    def guarded_catalog_load(self: Any, name: str, *args: Any, **kwargs: Any) -> Any:
        assert name == "exp03_sources", "Private catalog load"
        return actual_load(self, name, *args, **kwargs)

    monkeypatch.setattr(DataCatalog, "load", guarded_catalog_load)
    # Guards precede the real absolute Kedro source-descriptor load.
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


def test_invalid_approval(monkeypatch: pytest.MonkeyPatch) -> None:
    protocol = exp03.load_protocol()
    monkeypatch.setattr(pf, "load_protocol", lambda: protocol)
    monkeypatch.setenv("SAT_DENGUE_EXP03_APPROVAL", "tmp/invalid-exp03-record.json")
    monkeypatch.setattr(Path, "read_text", lambda *a, **kw: "{}")
    with pytest.raises(PermissionError, match="Invalid EXP03 authorization"):
        pf.authorize({"protocol_sha256": exp01.digest(protocol)})


def test_reservation_survives_retry(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from sat_dengue.experiments.exp03_runner import reserve_execution

    monkeypatch.chdir(repo_tmp_path)
    provenance = {"configuration_sha256": "a" * 64}
    first = reserve_execution(provenance)
    assert len(first) == 64
    with pytest.raises(FileExistsError):
        reserve_execution(provenance)
    assert len(list((repo_tmp_path / pf.OUTPUT_ROOT).iterdir())) == 1


@pytest.mark.parametrize(
    "root", [pf.OUTPUT_ROOT, pf.OUTPUT_ROOT + "/nested", "tmp/kedro-migration"]
)
def test_tracking_root_rejects_result_overlap(root: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAT_DENGUE_TRACKING_ROOT", root)
    with pytest.raises(ValueError, match="separate"):
        pf.tracking_root()
