"""Generated operational seams: dedicated roots, immutable reuse and episode dates."""

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.datasets.exp_delta03 import publish
from sat_dengue.datasets.exp_delta03_execution import (
    ExecutionStore,
    publication_prefix,
    verify_publication,
)
from sat_dengue.experiments.exp_delta03_contract import canonical
from sat_dengue.experiments.exp_delta03_inputs import validate_bound_outcomes


def test_dedicated_real_tmp_root_keeps_real_mode_on_completed_reuse(tmp_path):
    relative = "tmp/kedro-migration/exp-delta03-runs"
    execution = {"generated_fixture": True, "roots": {"publication": relative}}
    permission = {"identity": execution, "allow_resume": True}
    payloads = {"result.json": canonical({"generated_fixture": True})}
    with ExecutionStore(
        tmp_path, relative, execution, synthetic=False, permission=permission
    ) as store:
        receipt = store.publish(payloads)
    with ExecutionStore(
        tmp_path, relative, execution, synthetic=False, permission=permission
    ) as store:
        assert store.publish(payloads) == receipt
    assert verify_publication(tmp_path, receipt, synthetic=False) == payloads
    with pytest.raises(ValueError):
        verify_publication(tmp_path, receipt, synthetic=True)


@pytest.mark.parametrize(
    "path",
    ["tmp/other", "tmp/kedro-migration/exp-delta03-runs-extra", "data/processed/exp_delta03-other"],
)
def test_execution_roots_reject_lookalikes(path):
    with pytest.raises(ValueError):
        publication_prefix(path, synthetic=False)


def test_existing_preparation_publisher_accepts_only_pinned_annex_root(tmp_path):
    receipt = publish(tmp_path, "data/processed/exp_delta03-inputs", {"generated.json": b"{}"})
    assert (
        publish(tmp_path, "data/processed/exp_delta03-inputs", {"generated.json": b"{}"}) == receipt
    )
    with pytest.raises(ValueError):
        publish(tmp_path, "data/processed/unrelated", {"generated.json": b"{}"})


def test_episode_start_validates_actual_excess_onset_and_consistency():
    rows = pd.DataFrame(
        {
            "divipola_municipio": ["50001", "50001"],
            "periodo_mes": ["2020-01", "2020-02"],
            "horizon": [1, 1],
            "target_month": ["2020-02", "2020-03"],
            "truth": [1, 0],
            "onset_truth": [1, 0],
            "target_excess": [1, 1],
            "origin_excess": [0, 1],
            "origin_count": [0, 2],
            "target_p75": [1, 1],
            "episode_id": ["frozen_episode", "frozen_episode"],
            "episode_start": ["2020-02", "2020-02"],
        }
    )
    validate_bound_outcomes(rows)
    for changed in [None, "2020-04", "2020-01"]:
        bad = rows.copy()
        bad.loc[0, "episode_start"] = changed
        with pytest.raises(ValueError):
            validate_bound_outcomes(bad)
    bad = rows.copy()
    bad.loc[1, "episode_start"] = "2020-03"
    with pytest.raises(ValueError, match="Inconsistent episode"):
        validate_bound_outcomes(bad)


def test_structural_annex_requires_exact_inventory_and_hashes_without_csv_parsing(
    tmp_path, monkeypatch
):
    from sat_dengue.datasets.exp_delta03 import identity
    from sat_dengue.datasets.exp_delta03_training import verify_executable_annex

    def forbidden(*args, **kwargs):
        raise AssertionError("Preflight cannot parse table rows")

    monkeypatch.setattr(pd, "read_csv", forbidden)
    path = tmp_path / "data/processed/exp_delta03-inputs/generated.csv"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"generated,not-parsed\n")
    descriptor = {"path": str(path.relative_to(tmp_path)), **identity(path)}
    annex = {
        "schema": "exp-delta03-evaluation-annex-v1",
        "outcomes": descriptor,
        "calendar": descriptor,
        "exposure": descriptor,
        "national_cells": {
            "generated": {"rows": descriptor, "X": descriptor, "cohort": {"rows": 1}}
        },
        "comparators": {"generated": {n: descriptor for n in ["R0", "G0_OFF", "G0_ON", "G1"]}},
    }
    plan = {"cells": [{"id": "generated", "reference": "primary"}]}
    assert verify_executable_annex(tmp_path, annex, plan)["rows_parsed"] == 0
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="payload changed"):
        verify_executable_annex(tmp_path, annex, plan)


def test_manual_admission_rejects_changed_installed_bytes(tmp_path):
    from sat_dengue.datasets.exp_delta03 import identity
    from sat_dengue.datasets.exp_delta03_execution import verify_installed_runtime
    from sat_dengue.experiments.exp_delta03_contract import digest

    folder = tmp_path / "tmp/exp-delta03-runtime"
    package = folder / "site-packages/sat_dengue/generated.py"
    package.parent.mkdir(parents=True)
    package.write_bytes(b"generated code")
    wheel = folder / "generated.whl"
    wheel.write_bytes(b"generated wheel")
    lock = folder / "dependencies.lock"
    lock.write_bytes(b"generated==1")
    files = {str(package.relative_to(tmp_path)): identity(package)}
    receipt = {
        "wheel": {"path": str(wheel.relative_to(tmp_path)), **identity(wheel)},
        "dependencies": {"path": str(lock.relative_to(tmp_path)), **identity(lock)},
        "installed_files": files,
        "installed_files_sha256": digest(files),
    }
    verify_installed_runtime(tmp_path, receipt, full=True)
    package.write_bytes(b"altered code!!")
    with pytest.raises(ValueError, match="runtime file changed"):
        verify_installed_runtime(tmp_path, receipt, full=False)


def test_public_contract_load_does_not_require_private_annex_before_admission(
    tmp_path, monkeypatch
):
    import json

    from sat_dengue.datasets import exp_delta03_training as engine

    owner = tmp_path / "docs/product/experiments/EXP-DELTA03"
    owner.mkdir(parents=True)
    contract = {
        "evaluation_annex": {
            "path": "data/processed/exp_delta03-inputs/missing.json",
            "sha256": "a" * 64,
            "bytes": 1,
        }
    }
    (owner / "training-contract.json").write_text(json.dumps(contract))
    monkeypatch.setattr(engine, "ROOT", tmp_path)
    loaded, _ = engine._public_contract()
    assert loaded == contract
    with pytest.raises(FileNotFoundError):
        engine.resolve_evaluation_annex(tmp_path, loaded)


def test_official_authorizer_enforces_manual_only_scope(tmp_path):
    from test_exp_delta03_execution import authorization_fixture

    from sat_dengue.datasets.exp_delta03_execution import authorize

    context, current, grant, now, relative = authorization_fixture(tmp_path)
    context["contract"]["phase3_preparation"] = {"generated_fixture": True}
    grant.update(
        execution_mode="manual_only", executor="Mauricio", agent_execution_authorized=False
    )
    path = tmp_path / relative
    path.write_bytes(canonical(grant))
    authorize(tmp_path, context, current, authorization_relative=relative, now=now)
    for key, value in [
        ("execution_mode", "automatic"),
        ("executor", "agent"),
        ("agent_execution_authorized", True),
    ]:
        changed = {**grant, key: value}
        path.write_bytes(canonical(changed))
        with pytest.raises(PermissionError, match="only Mauricio manual"):
            authorize(tmp_path, context, current, authorization_relative=relative, now=now)
    assert not (tmp_path / "data").exists()
