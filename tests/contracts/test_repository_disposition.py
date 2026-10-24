"""Executable repository retirement, ownership and protected-lineage boundaries."""

from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
from pathlib import Path
from typing import NamedTuple

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
PRE_CORRECTION = "3deafa32c070d4c085e4197ec88489bc98aa57fb"
DOCUMENT_OWNERS = (
    "README.md",
    "AGENTS.md",
    "docs/TESTING_GUIDE.md",
    "docs/architecture/system-overview.md",
    "docs/operations/kedro-migration.md",
    "docs/product/stage-3/README.md",
    "docs/product/stage-4/README.md",
    "docs/product/stage-5/README.md",
    "docs/standards/ml-scientific-standards.md",
)
RETIRED_COMMAND_TARGETS = (
    "scripts.model_evaluation",
    "scripts/model_evaluation",
    "scripts.final_evaluation",
    "scripts/final_evaluation",
    "scripts/model_assessment",
    "scripts.model_assessment",
    "scripts/training_preparation",
    "scripts.training_preparation",
    "scripts/model_training",
    "scripts.model_training",
)


class CommandBlock(NamedTuple):
    line: int
    body: str
    historical: bool


def document_command_blocks(text: str) -> list[CommandBlock]:
    """Read fences and explicit history regions; a distant heading is not an exemption."""
    blocks = []
    historical_region = False
    historical_collection = False
    historical_heading: int | None = None
    fence: str | None = None
    language = ""
    body: list[str] = []
    start = 0
    for number, line in enumerate(text.splitlines(), 1):
        if fence is not None:
            if re.fullmatch(r"\s*" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*", line):
                if language in {"", "bash", "sh", "shell", "console", "text"}:
                    blocks.append(
                        CommandBlock(
                            start,
                            "\n".join(body),
                            historical_region
                            or historical_collection
                            or historical_heading is not None,
                        )
                    )
                fence = None
            else:
                body.append(line)
            continue
        if line == "<!-- command-context: historical begin -->":
            assert not historical_region, "Nested historical command region"
            preceding = "\n".join(text.splitlines()[max(0, number - 12) : number - 1]).lower()
            assert "historical" in preceding and "git" in preceding, (
                "History needs visible recovery context"
            )
            historical_region = True
            continue
        if line == "<!-- command-context: historical end -->":
            assert historical_region, "Unmatched historical command region"
            historical_region = False
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading:
            level, title = len(heading[1]), heading[2].lower()
            if historical_heading is not None and level <= historical_heading:
                historical_heading = None
            if "historical" in title:
                historical_heading = level
            if title == "historical migration records":
                # This collection explicitly labels all subsequent session records.
                following = "\n".join(text.splitlines()[number : number + 6]).lower()
                assert "old notebook/cli commands are historical" in following
                assert "registry above owns current" in following
                historical_collection = True
            elif title.startswith(("current execution", "maintained ")):
                historical_collection = False
        opening = re.match(r"^ {0,3}(`{3,}|~{3,})\s*([\w-]*)[^\n]*$", line)
        if opening:
            fence, language, start, body = opening[1], opening[2], number, []
    assert fence is None, "Unclosed command fence"
    assert not historical_region, "Unclosed historical command region"
    return blocks


def validate_document_commands(text: str, pipelines: set[str]) -> list[str]:
    documented = []
    for block in document_command_blocks(text):
        if block.historical:
            continue
        assert not any(name in block.body for name in RETIRED_COMMAND_TARGETS), block
        for line in block.body.replace("\\\n", " ").splitlines():
            if not re.search(r"\bkedro\b.*\brun\b|--scientific", line):
                continue
            tokens = shlex.split(line.lstrip("$ "), comments=True)
            assert "--scientific" not in tokens, block
            for index, token in enumerate(tokens[:-1]):
                if Path(token).name != "kedro" or tokens[index + 1] != "run":
                    continue
                tail = tokens[index + 2 :]
                for offset, option in enumerate(tail):
                    if option in {"&&", "||", ";", "|"}:
                        break
                    if option == "--pipeline":
                        assert offset + 1 < len(tail), block
                        name = tail[offset + 1]
                    elif option.startswith("--pipeline="):
                        name = option.split("=", 1)[1]
                    else:
                        continue
                    assert name in pipelines, (block, name)
                    documented.append(name)
    return documented


def test_documented_active_commands_use_registered_kedro_and_package_owners() -> None:
    from sat_dengue.pipeline_registry import register_pipelines

    pipelines = set(register_pipelines())
    documented = []
    for name in DOCUMENT_OWNERS:
        try:
            documented.extend(validate_document_commands((ROOT / name).read_text(), pipelines))
        except AssertionError as error:
            raise AssertionError(f"Invalid active command in {name}: {error}") from error
    assert {"replay", "evaluation_replay", "evaluation_synthetic"} <= set(documented)
    stage5 = (ROOT / "docs/product/stage-5/README.md").read_text()
    assert "KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=replay" in stage5
    assert {"replay", "evaluation_replay", "evaluation_synthetic"} <= set(
        validate_document_commands(stage5, pipelines)
    )
    standard = (ROOT / "docs/standards/ml-scientific-standards.md").read_text()
    assert "src/sat_dengue" in standard and "Kedro is the active orchestrator" in standard
    for text in (stage5, standard):
        assert "frozen historical identity evidence" in text
        assert re.search(r"(?:not|never) production entrypoints", text)


@pytest.mark.parametrize(
    "command",
    [
        "python -m scripts.model_evaluation.execution --verify",
        "python -m scripts.final_evaluation.execution --execute --scientific",
        "python scripts/model_evaluation/execution.py --verify",
        "python -m scripts.model_assessment.execution --verify",
        "ruff check scripts/model_assessment tests",
        "mypy scripts/training_preparation tests",
        "ruff format --check scripts/model_training",
        "kedro run --pipeline=unregistered_route",
        "kedro run --pipeline replay --scientific",
    ],
)
def test_document_command_guard_rejects_retired_unknown_and_scientific_routes(command: str) -> None:
    with pytest.raises(AssertionError):
        validate_document_commands(
            "## Current execution\n```bash\n" + command + "\n```\n", {"replay"}
        )


def test_historical_command_context_is_explicit_and_does_not_hide_later_active_blocks() -> None:
    historical = (
        "## Historical procedure\nRecover the original commands from Git; do not run them.\n"
        "<!-- command-context: historical begin -->\n"
        "```text\npython -m scripts.final_evaluation.execution --scientific\n```\n"
        "<!-- command-context: historical end -->\n"
        "## Current execution\n```sh\nkedro run \\\n--pipeline=replay\n```\n"
    )
    assert validate_document_commands(historical, {"replay"}) == ["replay"]
    assert [block.historical for block in document_command_blocks(historical)] == [True, False]
    with pytest.raises(AssertionError):
        validate_document_commands(
            historical + "```bash\nkedro run --pipeline=stale\n```", {"replay"}
        )
    with pytest.raises(AssertionError):
        document_command_blocks("<!-- command-context: historical begin -->\n```sh\ntrue\n```\n")


def test_previous_stage5_document_fails_the_command_guard() -> None:
    before = subprocess.check_output(
        ["git", "show", f"{PRE_CORRECTION}:docs/product/stage-5/README.md"], cwd=ROOT, text=True
    )
    with pytest.raises(AssertionError):
        validate_document_commands(before, {"replay", "evaluation_replay", "evaluation_synthetic"})


def git_identity(revision: str, name: str) -> dict:
    assert revision in {PRE_CORRECTION, "89d538c93ff20824c96c7fe0929baaa9d900e999"}
    raw = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
    blob = subprocess.check_output(
        ["git", "rev-parse", f"{revision}:{name}"], cwd=ROOT, text=True
    ).strip()
    import hashlib

    return {
        "revision": revision,
        "path": name,
        "blob": blob,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def test_document_correction_retains_closed_history_and_supplemental_policy_identity() -> None:
    value = json.loads((ROOT / MAPPING).read_text())
    before = json.loads(
        subprocess.check_output(["git", "show", f"{PRE_CORRECTION}:{MAPPING}"], cwd=ROOT)
    )
    assert value["ceiling"] == before["ceiling"] and set(value["files"]) == set(before["files"])
    stage5 = "docs/product/stage-5/README.md"
    for name, row in before["files"].items():
        if name == stage5:
            updated = value["files"][name]
            assert updated["engineering_history"] == [
                {"contract_revision": 16, "commit": PRE_CORRECTION, "final": row["final"]}
            ]
            assert {
                k: v for k, v in updated.items() if k not in {"final", "engineering_history"}
            } == {k: v for k, v in row.items() if k != "final"}
        else:
            assert value["files"][name] == row
    correction = value["documentation_corrections"][0]
    assert len(value["documentation_corrections"]) == 1
    assert correction["contract_revision"] == 17 and correction["authority"] == "Mauricio"
    assert correction["pre_correction_revision"] == PRE_CORRECTION
    assert set(correction["files"]) == {stage5, "docs/standards/ml-scientific-standards.md"}
    for name, row in correction["files"].items():
        original = git_identity("89d538c93ff20824c96c7fe0929baaa9d900e999", name)
        assert row["original_git"] == original
        assert row["original"] == {k: original[k] for k in ("bytes", "sha256")}
        assert row["pre_correction_git"] == git_identity(PRE_CORRECTION, name)
        assert row["final"] == {"present": True, **fingerprint(ROOT / name)}
        assert row["owner"] and row["reason"] and row["disposition"] == "ADAPT"
        assert row["scientific_semantics"] == "unchanged"
    verify_cleanup(ROOT)


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
