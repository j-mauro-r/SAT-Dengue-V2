"""Executable repository retirement, ownership and protected-lineage boundaries."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from cleanup_support import CEILING_SHA256, MAPPING, load_cleanup, verify_cleanup
from migration_support import (
    BASELINE_SHA256,
    fingerprint,
    new_evidence_directory,
    verify_protected_inventory,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/operations/repository-disposition.json"


def registry() -> dict:
    return json.loads(REGISTRY.read_text())


def test_complete_disposition_and_required_owners() -> None:
    value = registry()
    assert value["schema"] == "sat-dengue-repository-disposition-v1"
    assert len(value["candidates"]) == 75
    assert set(value["baseline_paths"]) <= set(value["paths"])
    assert all(row["disposition"] in {"KEEP", "ADAPT", "RETIRE"} for row in value["paths"].values())
    for name in value["required_owners"]:
        assert (ROOT / name).is_file(), name
    for name, row in value["paths"].items():
        assert row["owner"] and row["reason"], name
        if row["disposition"] == "RETIRE":
            assert not (ROOT / name).exists(), name
            assert row["recovery"] and row["replacement"] and row["consumer_evidence"]
        else:
            assert (ROOT / name).exists(), name


def test_no_active_imports_to_retired_script_modules() -> None:
    retired = {
        name.removesuffix(".py").replace("/", ".").removesuffix(".__init__")
        for name, row in registry()["paths"].items()
        if name.startswith("scripts/") and name.endswith(".py") and row["disposition"] == "RETIRE"
    }
    for directory in ("src", "scripts", "tests"):
        for path in (ROOT / directory).rglob("*.py"):
            if path == ROOT / "tests/integration/migration_replay.py":
                # This isolated process verifies every imported module against the
                # reconstructed historical snapshot; it cannot import live facades.
                text = path.read_text()
                assert '"Imported live rather than historical source"' in text
                assert '"Imported source has no historical hash: {relative}"' in text
                continue
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module, *[node.module + "." + a.name for a in node.names]]
                elif isinstance(node, ast.Call) and node.args:
                    first = node.args[0]
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        names = [first.value]
                assert not any(
                    name == old or name.startswith(old + ".") for name in names for old in retired
                ), path


def test_retained_adapters_have_observed_ownership_and_retirement_conditions() -> None:
    for name, row in registry()["adapters"].items():
        assert (ROOT / name).is_file()
        assert row["owner"] and row["reason"] and row["retirement_condition"]
        assert row["consumers"] and all((ROOT / c).is_file() for c in row["consumers"])


def test_only_registered_project_directories_and_no_empty_scaffold() -> None:
    value = registry()
    for directory in ("src", "conf", "tests", "scripts", "notebooks", "docs"):
        for path in (ROOT / directory).rglob("*"):
            if not path.is_dir() or "__pycache__" in path.parts:
                continue
            assert str(path.relative_to(ROOT)) in value["directories"], path
            assert any(path.iterdir()), path
    for name in ("docs/contracts", "docs/methodology", "tests/fixtures"):
        assert not (ROOT / name).exists(), name


def test_active_commands_ci_and_historical_notebook_boundary() -> None:
    value = registry()
    assert value["production_entrypoint"] == "kedro run --pipeline=replay"
    for name in ("README.md", "AGENTS.md", "docs/TESTING_GUIDE.md"):
        assert value["production_entrypoint"] in (ROOT / name).read_text()
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert ".[dev,modeling,tracking]" in ci
    assert "test_kedro_e2e.py" in ci and "test_repository_disposition.py" in ci
    assert "--require-migration-evidence" not in ci
    assert "nbconvert" not in ci and "nbclient" not in ci
    assert all(row["production_entrypoint"] is False for row in value["notebooks"].values())
    for name, row in value["notebooks"].items():
        assert row["role"] == "historical identity evidence"
        assert row["recovery"] and row["readers"]
        assert name.endswith(".ipynb")


def test_all_original_and_pre_cleanup_identities_and_final_dispositions() -> None:
    value = load_cleanup(ROOT)
    assert value is not None and len(value["files"]) == 67
    assert registry()["ceiling_sha256"] == CEILING_SHA256
    verify_cleanup(ROOT)


def test_protected_inventory_when_locally_supplied(pytestconfig: pytest.Config) -> None:
    """Local cleanup checks native bytes too; data-free CI retains its public boundary."""
    baseline = ROOT / "tmp/kedro-migration/baseline.json"
    if not baseline.is_file():
        assert not pytestconfig.getoption("--require-migration-evidence"), (
            "Required private preservation inventory is absent"
        )
        return
    assert fingerprint(baseline)["sha256"] == BASELINE_SHA256
    report = verify_protected_inventory(ROOT, json.loads(baseline.read_text()))
    assert report["protected_files"] == 2553 and report["bundles"] == 45


def test_validation_receipts_are_fresh_and_cannot_overwrite_prior_runs(
    repo_tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAT_DENGUE_VALIDATION_EVIDENCE_ROOT", str(repo_tmp_path.relative_to(ROOT)))
    first = new_evidence_directory("regression")
    receipt = first / "receipt.json"
    receipt.write_text("preserved first result")
    second = new_evidence_directory("regression")
    assert first != second and list(second.iterdir()) == []
    assert receipt.read_text() == "preserved first result"
    monkeypatch.setenv("SAT_DENGUE_VALIDATION_EVIDENCE_ROOT", "docs")
    with pytest.raises(AssertionError):
        new_evidence_directory("regression")


@pytest.mark.parametrize("change", ["expand", "remove", "original", "pre_cleanup"])
def test_cleanup_mapping_rejects_unapproved_changes(repo_tmp_path: Path, change: str) -> None:
    value = json.loads((ROOT / MAPPING).read_text())
    name = next(iter(value["files"]))
    if change == "expand":
        value["files"]["outside.py"] = value["files"][name]
    elif change == "remove":
        value["files"].pop(name)
    elif change == "original":
        value["files"][name]["original"]["sha256"] = "0" * 64
    else:
        value["files"][name]["pre_cleanup_git"]["sha256"] = "0" * 64
    path = repo_tmp_path / MAPPING
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value))
    with pytest.raises(AssertionError):
        load_cleanup(repo_tmp_path)
