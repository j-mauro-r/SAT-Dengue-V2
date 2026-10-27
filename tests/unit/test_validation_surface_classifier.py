"""Regression tests for proportional local and CI validation routing."""

from __future__ import annotations

import pytest

from scripts.classify_validation_surface import ValidationPlan, classify_paths


@pytest.mark.parametrize(
    ("paths", "expected"),
    [
        (
            ["docs/operations/runbook.md"],
            {"surfaces": ("narrative_docs",), "run_docs": True, "pytest_scope": "none"},
        ),
        (
            ["docs/governance/dwp.md"],
            {"surfaces": ("dwp",), "run_dwp": True, "pytest_scope": "none"},
        ),
        (
            ["scripts/read_only_api/api.py"],
            {
                "surfaces": ("api", "integration"),
                "run_python_quality": True,
                "pytest_scope": "api",
                "run_base_package": True,
                "run_dashboard": True,
                "run_integration_smoke": True,
            },
        ),
        (
            ["apps/dashboard/src/components/municipal-map.tsx"],
            {"surfaces": ("dashboard",), "run_dashboard": True, "pytest_scope": "none"},
        ),
        (
            ["src/sat_dengue/pipelines/preparation/nodes.py"],
            {
                "surfaces": ("data_preparation",),
                "run_python_quality": True,
                "pytest_scope": "full",
                "full_gate": True,
            },
        ),
        (
            ["src/sat_dengue/tracking/local.py"],
            {
                "surfaces": ("model_tracking",),
                "run_python_quality": True,
                "pytest_scope": "full",
                "full_gate": True,
            },
        ),
        (
            ["docs/product/stage-4/model_engineering_contract_v1.json"],
            {
                "surfaces": ("model_tracking", "scientific_contract"),
                "run_python_quality": True,
                "pytest_scope": "full",
                "full_gate": True,
            },
        ),
        (
            ["docs/product/stage-1/PROD-07-draft-prediction-contract.md"],
            {
                "surfaces": ("scientific_contract",),
                "run_docs": True,
                "run_python_quality": True,
                "pytest_scope": "full",
                "full_gate": True,
            },
        ),
        (
            ["apps/dashboard/src/lib/dashboard-client.ts"],
            {
                "surfaces": ("dashboard", "integration"),
                "run_dashboard": True,
                "pytest_scope": "none",
                "run_integration_smoke": True,
            },
        ),
        (
            ["src/sat_dengue/pipeline_registry.py"],
            {
                "surfaces": ("kedro_graph",),
                "run_dashboard": True,
                "pytest_scope": "full",
                "run_integration_smoke": True,
                "full_gate": True,
            },
        ),
        (
            [
                "scripts/read_only_api/service.py",
                "apps/dashboard/src/routes/index.tsx",
            ],
            {
                "surfaces": ("api", "dashboard", "integration"),
                "run_dashboard": True,
                "pytest_scope": "api",
                "run_integration_smoke": True,
                "full_gate": False,
            },
        ),
        (
            ["unexpected/new-runtime.xyz"],
            {
                "surfaces": ("unknown",),
                "run_docs": True,
                "run_dwp": True,
                "run_dashboard": True,
                "run_python_quality": True,
                "pytest_scope": "full",
                "run_base_package": True,
                "run_integration_smoke": True,
                "full_gate": True,
            },
        ),
        (
            ["pyproject.toml"],
            {
                "surfaces": ("shared_ci",),
                "run_dashboard": True,
                "run_python_quality": True,
                "pytest_scope": "full",
                "run_integration_smoke": True,
                "full_gate": True,
            },
        ),
        (
            [".github/workflows/ci.yml", "scripts/classify_validation_surface.py"],
            {
                "surfaces": ("shared_ci",),
                "run_dashboard": True,
                "run_python_quality": True,
                "pytest_scope": "full",
                "run_integration_smoke": True,
                "full_gate": True,
            },
        ),
    ],
    ids=[
        "narrative-docs",
        "dwp",
        "api",
        "dashboard",
        "data-preparation",
        "model-tracking",
        "scientific-contract-not-narrative",
        "markdown-contract-not-narrative",
        "api-dashboard-integration",
        "kedro-graph",
        "mixed-api-dashboard",
        "unknown-fail-closed",
        "shared-dependency",
        "shared-ci-self-change",
    ],
)
def test_classifier_matrix(paths: list[str], expected: dict[str, object]) -> None:
    plan = classify_paths(paths)
    for field, value in expected.items():
        assert getattr(plan, field) == value


def test_protected_branch_push_forces_complete_plan() -> None:
    plan = classify_paths(["docs/README.md"], force_full=True)
    assert isinstance(plan, ValidationPlan)
    assert "protected_branch" in plan.surfaces
    assert plan.pytest_scope == "full"
    assert plan.run_dashboard
    assert plan.run_python_quality
    assert plan.run_base_package
    assert plan.run_integration_smoke
    assert plan.run_dwp


@pytest.mark.parametrize(
    "path",
    [
        "src/sat_dengue/experiments/exp03_admission.py",
        "src/sat_dengue/experiments/exp03_reporting.py",
        "src/sat_dengue/tracking/exp03.py",
        "docs/product/experiments/EXP03_feature_ablation/protocol.json",
        "src/sat_dengue/experiments/exp02_runner.py",
        "tests/integration/test_exp02_execution.py",
    ],
)
def test_experiment_changes_select_full_acceptance(path: str) -> None:
    assert classify_paths([path]).pytest_scope == "full"


def test_workflow_retains_critical_public_integrations() -> None:
    from pathlib import Path

    import yaml  # type: ignore[import-untyped]

    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text())
    step = next(
        s
        for s in workflow["jobs"]["unit-tests"]["steps"]
        if s.get("if", "").endswith("== 'full'") and "pytest " in s.get("run", "")
    )
    for name in (
        "exp02_catalog",
        "exp02_execution",
        "exp02_tracking",
        "exp03_input_integration",
        "exp03_admission",
        "exp03_revision_tracking",
        "exp03_tracking",
    ):
        assert Path(f"tests/integration/test_{name}.py").is_file()
        assert "tests/integration" in step["run"].split()
    assert "--require-migration-evidence" not in step["run"]
    assert step["run"] in Path("docs/TESTING_GUIDE.md").read_text()


@pytest.mark.parametrize("paths", [[], [""], ["../escape"], ["unknown/file.xyz"]])
def test_empty_unknown_and_malformed_paths_fail_closed(paths: list[str]) -> None:
    assert classify_paths(paths).full_gate


def test_git_errors_never_report_a_successful_narrow_gate(repo_tmp_path) -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "scripts/classify_validation_surface.py",
            "--base",
            "no-such-base",
            "--head",
            "HEAD",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert '"pytest_scope": "none"' not in result.stdout


def test_rename_and_delete_keep_both_risk_paths(repo_tmp_path) -> None:
    import subprocess

    from scripts.classify_validation_surface import _changed_paths

    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(repo_tmp_path), *args], text=True).strip()

    git("init")
    git("config", "user.email", "synthetic@example.invalid")
    git("config", "user.name", "Synthetic fixture")
    old = repo_tmp_path / "docs/old.md"
    old.parent.mkdir()
    old.write_text("unchanged material\n")
    deleted = repo_tmp_path / "unknown.xyz"
    deleted.write_text("removed\n")
    git("add", ".")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD")
    new = repo_tmp_path / "new.xyz"
    old.rename(new)
    deleted.unlink()
    git("add", "-A")
    git("commit", "-m", "rename/delete")
    # Exercise the real Git command from a separate generated repository.
    from unittest.mock import patch

    original_run = subprocess.run
    with patch(
        "scripts.classify_validation_surface.subprocess.run",
        side_effect=lambda args, **kw: original_run(args, cwd=repo_tmp_path, **kw),
    ):
        paths = _changed_paths(base, "HEAD")
    assert "new.xyz" in paths and "unknown.xyz" in paths
    assert classify_paths(paths).full_gate
