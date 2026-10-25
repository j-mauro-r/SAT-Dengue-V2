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
