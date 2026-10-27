"""Generated three-phase EXP03 admission: no real approval, fits or MLflow writes."""

from __future__ import annotations

import builtins
import copy
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from test_exp03_input_integration import ROOT, bind_generated_sources, generated_sources

from sat_dengue.experiments import exp01_inputs
from sat_dengue.experiments import exp03_admission as admission
from sat_dengue.experiments import exp03_preflight as pf
from sat_dengue.experiments import exp03_runner as runner
from sat_dengue.experiments.exp01 import digest


@pytest.fixture
def admitted_context(repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    config = generated_sources(repo_tmp_path / "sources")
    bind_generated_sources(config, monkeypatch)
    monkeypatch.setattr(pf, "runtime_versions", lambda: {"fixture": "generated"})
    monkeypatch.setattr(
        pf,
        "execution_metadata",
        lambda: {
            "code_sha256": "a" * 64,
            "environment_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(pf, "git_identity", lambda: {"git_revision": "c" * 40, "git_dirty": False})
    monkeypatch.setenv(
        "SAT_DENGUE_TRACKING_ROOT", str((repo_tmp_path / "tracking").relative_to(ROOT))
    )
    receipt = pf.preflight(
        {"profile": "exp03", "tracking": "enabled", "experiment_id": "EXP03"}, pf.descriptor()
    )
    approval = {
        "schema": "exp03-execution-approval-v2",
        "experiment_id": "EXP03",
        "authority": "Mauricio",
        "independent_reviewer": "GeneratedFixture",
        "structural_receipt_sha256": digest(receipt),
        **{
            key: receipt[key]
            for key in ("protocol_sha256", "git_revision", "data_version", "configuration_sha256")
        },
        "real_execution_authorized": True,
        "comparator_refit_authorized": True,
        "variant_refits_authorized": True,
        "retrospective_availability_acknowledged": True,
    }
    approval_path = repo_tmp_path / "in-memory-only.json"
    original = Path.read_text
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda path, *a, **kw: (
            json.dumps(approval) if path == approval_path else original(path, *a, **kw)
        ),
    )
    monkeypatch.setenv("SAT_DENGUE_EXP03_APPROVAL", str(approval_path))
    effects = {key: 0 for key in admission.ZERO_EFFECTS}

    def forbidden(name: str) -> Any:
        def call(*args: Any, **kwargs: Any) -> Any:
            effects[name] += 1
            raise AssertionError("Unexpected scientific side effect: " + name)

        return call

    monkeypatch.setattr(runner, "reserve_execution", forbidden("reservations"))
    monkeypatch.setattr(runner, "native_fit", forbidden("real_model_fits"))
    monkeypatch.setattr(runner, "fit_calibration", forbidden("calibrator_fits"))
    monkeypatch.setattr("sat_dengue.tracking.exp03.Exp03Tracking", forbidden("mlflow_writes"))
    return dict(
        config=config, receipt=receipt, approval=approval, effects=effects, root=repo_tmp_path
    )


def test_structural_receipt_never_opens_sources(
    admitted_context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = admitted_context
    source_root = context["config"].root / "data"
    original, path_original = builtins.open, Path.open

    def check(path: Any) -> None:
        if isinstance(path, (str, Path)):
            absolute = Path(path).absolute()
            assert not absolute.is_relative_to(source_root)
            assert not absolute.is_relative_to(ROOT / "data")

    def guarded(file: Any, *a: Any, **kw: Any) -> Any:
        check(file)
        return original(file, *a, **kw)

    def guarded_path(path: Path, *a: Any, **kw: Any) -> Any:
        check(path)
        return path_original(path, *a, **kw)

    monkeypatch.setattr(builtins, "open", guarded)
    monkeypatch.setattr(Path, "open", guarded_path)
    r = pf.preflight(
        {"profile": "exp03_preflight", "tracking": "enabled", "experiment_id": "EXP03"},
        pf.descriptor(),
    )
    assert r["status"] == "structural_pass" and r["execution_ready"] is False
    assert r["source_identity_status"] == "pending_authorized_verification"
    assert r["expected_source_sha256"] == r["sources"]["expected_source_sha256"]
    assert "not observed" in r["expected_identity_origin"]
    assert "observed_source_sha256" not in r
    assert (r["expected_children"], r["expected_terminal_cells"], r["expected_runs"]) == (
        408,
        102,
        409,
    )
    assert r["protocol_version"] == "2.0.1" and r["B_primary"] == 1.0
    assert all(
        r[key] == 0
        for key in (
            "private_reads",
            "real_model_fits",
            "calibrator_fits",
            "reservations",
            "mlflow_writes",
        )
    )
    assert pf.authorize(r) == context["approval"]


@pytest.mark.parametrize(
    "field",
    [
        "structural_receipt_sha256",
        "runtime",
        "tracking",
        "output_root",
        "expected_source_sha256",
        "sources",
    ],
)
def test_approval_binds_entire_structural_receipt(
    admitted_context: dict[str, Any],
    field: str,
) -> None:
    r = copy.deepcopy(admitted_context["receipt"])
    if field == "structural_receipt_sha256":
        admitted_context["approval"].pop(field)
    else:
        r[field] = "tampered"
    with pytest.raises(PermissionError, match="authorization"):
        pf.authorize(r)
    assert not any(admitted_context["effects"].values())


def test_no_authorization_no_admission(
    admitted_context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SAT_DENGUE_EXP03_APPROVAL")
    monkeypatch.setattr(
        runner, "admit_sources", lambda *a: pytest.fail("admission before authorization")
    )
    with pytest.raises(PermissionError, match="APPROVAL"):
        runner.load_authorized_sources(admitted_context["receipt"])
    assert not any(admitted_context["effects"].values())


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "hash",
        "manifest",
        "symlink",
        "external",
        "traversal",
        "catalog",
        "schema",
        "after_hash",
        "during_preparation",
    ],
)
def test_invalid_admission_has_zero_scientific_effects(
    admitted_context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
) -> None:
    context = admitted_context
    config = context["config"]
    path = config.resolve("data/processed/panel_mensual_dengue_clima.csv")
    if fault == "missing":
        path.unlink()
    elif fault == "hash":
        path.write_bytes(path.read_bytes() + b"\n")
    elif fault == "manifest":
        config.resolve(config.manifest_path).write_text("{}")
    elif fault == "symlink":
        target = path.with_name("replacement.csv")
        path.rename(target)
        path.symlink_to(target)
    elif fault in {"external", "traversal"}:
        r = context["receipt"]
        r["sources"]["declared_paths"][0] = (
            "/outside/private.csv" if fault == "external" else "tmp/../private.csv"
        )
        context["approval"]["structural_receipt_sha256"] = digest(r)
        # Fresh preflight still sees the canonical descriptor and must reject.
    elif fault == "catalog":
        config.resolve("data/sources/Divipola-municipios.md").write_text("{}")
    elif fault in {"after_hash", "during_preparation"}:
        original = exp01_inputs.prepare_exp01_inputs

        def changed(c: Any) -> Any:
            if fault == "after_hash":
                path.write_bytes(path.read_bytes() + b"\n")
                return original(c)
            value = original(c)
            path.write_bytes(path.read_bytes() + b"\n")
            return value

        monkeypatch.setattr(exp01_inputs, "prepare_exp01_inputs", changed)
    else:
        # Valid newly authorized bytes, invalid consumed schema: no estimator call.
        content = path.read_text().replace("rain_mm_month_sum", "invalid_column", 1)
        path.write_text(content)
        manifest_path = config.resolve(config.manifest_path)
        manifest = json.loads(manifest_path.read_text())
        from sat_dengue.datasets.legacy_preparation.pipeline import fingerprint

        manifest["outputs"]["panel_mensual_dengue_clima"].update(fingerprint(path))
        manifest_path.write_text(json.dumps(manifest))
        record = fingerprint(manifest_path)
        pf.NATIVE_IDENTITIES[pf.NATIVE_MANIFEST] = record
        r = pf.preflight(
            {"profile": "exp03", "tracking": "enabled", "experiment_id": "EXP03"}, pf.descriptor()
        )
        context["receipt"] = r
        context["approval"].update(
            data_version=r["data_version"], structural_receipt_sha256=digest(r)
        )
    with pytest.raises((admission.AdmissionError, PermissionError, ValueError)) as error:
        runner.load_authorized_sources(context["receipt"])
    if isinstance(error.value, admission.AdmissionError):
        assert all(error.value.receipt[key] == 0 for key in admission.ZERO_EFFECTS)
    assert not any(context["effects"].values())
    assert not list(context["root"].rglob("*.reservation"))
    assert not (context["root"] / "tracking").exists()


@pytest.mark.parametrize("mutate", [False, True])
def test_valid_admission_reaches_prefit_boundary_and_rechecks_sources(
    admitted_context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    mutate: bool,
) -> None:
    context = admitted_context
    sources = runner.load_authorized_sources(context["receipt"])
    a = sources["admission"]
    assert a["status"] == a["source_identity_status"] == "verified"
    assert (
        a["expected_source_sha256"]
        == a["observed_source_sha256"]
        == context["receipt"]["expected_source_sha256"]
    )
    assert a["structural_receipt_sha256"] == digest(context["receipt"])

    class BoundaryReached(Exception):
        pass

    def cohorts(*args: Any) -> None:
        if mutate:
            path = context["config"].resolve("data/processed/panel_mensual_dengue_clima.csv")
            path.write_bytes(path.read_bytes() + b"\n")

    def reserve(provenance: dict[str, Any]) -> str:
        admission.validate_admission(provenance)
        assert provenance["source_admission"] == a
        raise BoundaryReached

    monkeypatch.setattr("sat_dengue.experiments.exp03_features.cohorts", cohorts)
    monkeypatch.setattr(runner, "reserve_execution", reserve)
    with pytest.raises(admission.AdmissionError if mutate else BoundaryReached) as caught:
        runner.execute_authorized(sources)
    if mutate:
        assert isinstance(caught.value, admission.AdmissionError)
        assert all(caught.value.receipt[key] == 0 for key in admission.ZERO_EFFECTS)
    assert not any(context["effects"].values())


def test_real_publication_requires_observed_lineage(admitted_context: dict[str, Any]) -> None:
    sources = runner.load_authorized_sources(admitted_context["receipt"])
    a = sources["admission"]
    p = dict(
        source_admission=a,
        admission_sha256=digest(a),
        data_version=a["expected_source_sha256"],
        data_sha256=digest(a["files"]),
    )
    admission.validate_admission(p)
    for field in ("observed_source_sha256", "expected_source_sha256", "status", "files"):
        bad = copy.deepcopy(p)
        bad["source_admission"].pop(field)
        with pytest.raises(ValueError, match="admission lineage"):
            admission.validate_admission(bad)


def test_other_experiment_contracts_and_scientific_protocol_unchanged() -> None:
    base = "ba2870bafd6888bb0c2628a06461d6cb52c36cd0"
    paths = [p for p in Path("docs/product/experiments").glob("EXP0[012]*/*") if p.is_file()]
    paths += list(Path("docs/product/experiments/EXP03_feature_ablation").glob("*.json"))
    paths += [Path("docs/product/experiments/EXP03_feature_ablation/ablation-matrix.frozen.yml")]
    for p in paths:
        assert p.read_bytes() == subprocess.check_output(["git", "show", f"{base}:{p}"])


def test_replace_and_restore_source_cannot_change_parser_bytes(
    admitted_context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import pandas as pd  # type: ignore[import-untyped]

    context = admitted_context
    path = context["config"].resolve("data/processed/panel_mensual_dengue_clima.csv")
    original_bytes = path.read_bytes()
    original_read = pd.read_csv
    expected = original_read(path, dtype="string", keep_default_na=False)
    altered = expected.copy()
    altered.loc[0, "rain_mm_month_sum"] = "999999"
    snapshots: list[Path] = []

    def racing_read(file: Any, *args: Any, **kwargs: Any) -> Any:
        # Replace AND restore between identity checks, while the parser is reading.
        altered.to_csv(path, index=False)
        try:
            snapshots.append(Path(file))
            return original_read(file, *args, **kwargs)
        finally:
            path.write_bytes(original_bytes)

    monkeypatch.setattr(pd, "read_csv", racing_read)
    sources = runner.load_authorized_sources(context["receipt"])
    assert float(sources["panel"].iloc[0]["rain_mm_month_sum"]) == float(
        expected.iloc[0]["rain_mm_month_sum"]
    )
    assert snapshots and all(not p.exists() and p != path for p in snapshots)
    assert not any(context["effects"].values())


def test_benchmark_rechecks_manifest_before_readiness(
    admitted_context: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources = runner.load_authorized_sources(admitted_context["receipt"])
    config = admitted_context["config"]
    manifest_path = config.resolve(config.manifest_path)
    manifest_path.write_text("{}")
    monkeypatch.setattr(
        "sat_dengue.experiments.exp03_persistence._load_terminal", lambda *a: (None, None, "frozen")
    )
    monkeypatch.setattr(
        "sat_dengue.experiments.exp03_inputs.prepare_benchmark_inputs",
        lambda *a: pytest.fail("unverified benchmark read"),
    )
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        runner.evaluate_authorized_benchmark(
            sources, {"terminal_manifest": {"manifest_sha256": "frozen"}}, admitted_context["root"]
        )
    assert not any(admitted_context["effects"].values())


def test_real_result_validator_rejects_missing_admission() -> None:
    from sat_dengue.experiments.exp03 import load_protocol
    from sat_dengue.tracking.exp03 import validate_result

    result = dict(
        schema="exp03-result-v2",
        experiment_id="EXP03",
        synthetic=False,
        G5="NOT_APPROVED",
        champion="not_selected",
    )
    with pytest.raises(ValueError, match="admission lineage"):
        validate_result(result, {"protocol_sha256": digest(load_protocol())})
