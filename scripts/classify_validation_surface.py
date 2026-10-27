"""Classify changed paths into the smallest safe validation plan.

The classifier is intentionally conservative: an empty, malformed, unknown, or
shared-CI path escalates instead of silently skipping a required check.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class ValidationPlan:
    """Machine-readable CI decisions derived only from changed paths."""

    surfaces: tuple[str, ...]
    run_docs: bool
    run_dwp: bool
    run_dashboard: bool
    run_python_quality: bool
    pytest_scope: str
    run_base_package: bool
    run_integration_smoke: bool
    full_gate: bool
    reason: str


NARRATIVE_ROOT_FILES = {
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
}
DWP_PATHS = {
    "AGENTS.md",
    "CLAUDE.md",
    ".dwp/config.json",
    "docs/governance/dwp.md",
}
SHARED_PATHS = {
    "pyproject.toml",
    "requirements-dev.txt",
    "requirements-modeling.txt",
    "scripts/classify_validation_surface.py",
    "tests/unit/test_validation_surface_classifier.py",
}
KEDRO_PATHS = {
    "src/sat_dengue/config_loader.py",
    "src/sat_dengue/pipeline_registry.py",
}
API_TESTS = {
    "tests/unit/test_dashboard_query_service.py",
    "tests/unit/test_read_only_api_http.py",
    "tests/unit/test_read_only_api_contract.py",
}
DASHBOARD_INTEGRATION_PATHS = {
    "apps/dashboard/package.json",
    "apps/dashboard/bun.lock",
    "apps/dashboard/src/lib/dashboard-client.ts",
    "apps/dashboard/src/lib/dashboard-config.ts",
    "apps/dashboard/src/lib/dashboard-contract.ts",
    "apps/dashboard/src/lib/use-dashboard.ts",
    "apps/dashboard/src/server.ts",
    "apps/dashboard/vite.config.ts",
    "scripts/dashboard_e2e_smoke.py",
}


def _normalise(raw_path: str) -> str | None:
    path = raw_path.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    parsed = PurePosixPath(path)
    if not path or parsed.is_absolute() or ".." in parsed.parts:
        return None
    return parsed.as_posix()


def _surfaces_for_path(path: str) -> set[str]:
    if path in DWP_PATHS or path.startswith((".agents/", ".claude/", ".cursor/")):
        return {"dwp"}
    if (
        path.startswith(".github/workflows/")
        or path in SHARED_PATHS
        or path.startswith(("requirements/", ".review/"))
    ):
        return {"shared_ci"}
    if path.startswith("scripts/read_only_api/") or path in API_TESTS:
        return {"api", "integration"}
    if path.startswith("apps/dashboard/"):
        surfaces = {"dashboard"}
        if path in DASHBOARD_INTEGRATION_PATHS or path.startswith(
            "apps/dashboard/src/test/dashboard-integration"
        ):
            surfaces.add("integration")
        return surfaces
    if path == "scripts/dashboard_e2e_smoke.py":
        return {"api", "integration"}
    if path.startswith("docs/product/stage-6/"):
        return {"scientific_contract", "integration"}
    if path.startswith(("docs/product/stage-2/", "docs/product/stage-3/")):
        return {"scientific_contract", "data_preparation"}
    if path.startswith(
        ("docs/product/stage-4/", "docs/product/stage-5/", "docs/product/experiments/")
    ):
        return {"scientific_contract", "model_tracking"}
    if path.startswith("docs/product/") and any(
        marker in PurePosixPath(path).name.lower()
        for marker in ("contract", "policy", "conclu", "protocol")
    ):
        return {"scientific_contract"}
    if path.startswith(
        (
            "src/sat_dengue/datasets/",
            "src/sat_dengue/pipelines/data/",
            "src/sat_dengue/pipelines/preparation/",
            "src/sat_dengue/training_preparation/",
            "scripts/stage2_",
            "scripts/january_2020_",
            "scripts/validate_stage2_",
            "tests/unit/test_stage2_",
            "tests/unit/test_training_preparation",
            "tests/unit/test_consolidated_dataset",
        )
    ):
        return {"data_preparation"}
    if (
        path.startswith(
            (
                "src/sat_dengue/model_",
                "src/sat_dengue/tracking/",
                "src/sat_dengue/pipelines/evaluation/",
                "src/sat_dengue/pipelines/training/",
                "scripts/model_",
                "tests/integration/test_mlflow_tracking.py",
                "tests/integration/test_kedro_e2e.py",
            )
        )
        or path == "src/sat_dengue/hooks.py"
    ):
        return {"model_tracking"}
    if path in KEDRO_PATHS or path.startswith(
        ("conf/", "src/sat_dengue/pipelines/", "tests/contracts/")
    ):
        return {"kedro_graph"}
    if path.startswith("docs/") or path in NARRATIVE_ROOT_FILES:
        return {"narrative_docs"}
    return {"unknown"}


def classify_paths(paths: Iterable[str], *, force_full: bool = False) -> ValidationPlan:
    """Return deterministic job decisions for *paths*.

    ``force_full`` is used for protected-branch pushes. It never reduces checks.
    """

    surfaces: set[str] = set()
    for raw_path in paths:
        normalised = _normalise(raw_path)
        surfaces.update({"unknown"} if normalised is None else _surfaces_for_path(normalised))
    if not surfaces:
        surfaces.add("unknown")
    if force_full:
        surfaces.add("protected_branch")

    escalated = bool(surfaces & {"unknown", "shared_ci", "kedro_graph", "protected_branch"})
    full_python = escalated or bool(
        surfaces & {"data_preparation", "model_tracking", "scientific_contract"}
    )
    integration = escalated or "integration" in surfaces
    dashboard = escalated or bool(surfaces & {"dashboard", "integration"})
    python_quality = escalated or bool(
        surfaces & {"api", "data_preparation", "model_tracking", "scientific_contract"}
    )
    pytest_scope = "full" if full_python else "api" if "api" in surfaces else "none"
    run_docs = escalated or bool(surfaces & {"narrative_docs", "dwp", "scientific_contract"})
    run_dwp = escalated or "dwp" in surfaces
    run_base_package = escalated or "api" in surfaces

    ordered_surfaces = tuple(sorted(surfaces))
    reason = f"surfaces={','.join(ordered_surfaces)}; pytest={pytest_scope}"
    return ValidationPlan(
        surfaces=ordered_surfaces,
        run_docs=run_docs,
        run_dwp=run_dwp,
        run_dashboard=dashboard,
        run_python_quality=python_quality,
        pytest_scope=pytest_scope,
        run_base_package=run_base_package,
        run_integration_smoke=integration,
        full_gate=full_python,
        reason=reason,
    )


def _changed_paths(base: str, head: str) -> list[str]:
    result = subprocess.run(
        [
            "git",
            "diff",
            "--name-only",
            "--no-renames",
            "--diff-filter=ACDMRTUXB",
            "-z",
            f"{base}...{head}",
        ],
        check=True,
        capture_output=True,
    )
    return [path.decode() for path in result.stdout.split(b"\0") if path]


def _write_github_output(plan: ValidationPlan, destination: Path) -> None:
    values = asdict(plan)
    values["surfaces"] = ",".join(plan.surfaces)
    with destination.open("a", encoding="utf-8") as output:
        for key, value in values.items():
            rendered = str(value).lower() if isinstance(value, bool) else str(value)
            output.write(f"{key}={rendered}\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Changed repository-relative paths")
    parser.add_argument("--base", help="Git base revision; requires --head")
    parser.add_argument("--head", help="Git head revision; requires --base")
    parser.add_argument("--force-full", action="store_true", help="Escalate protected pushes")
    parser.add_argument("--github-output", type=Path, help="Append GitHub Actions outputs")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if bool(args.base) != bool(args.head):
        raise SystemExit("--base and --head must be provided together")
    paths = list(args.paths)
    if args.base:
        if paths:
            raise SystemExit("provide paths or --base/--head, not both")
        paths = _changed_paths(args.base, args.head)
    plan = classify_paths(paths, force_full=args.force_full)
    if args.github_output:
        _write_github_output(plan, args.github_output)
    print(json.dumps(asdict(plan), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
