"""Verify the installed package, used Kedro graph and framework boundaries."""

import ast
import importlib.metadata
from pathlib import Path

from kedro.framework.project import pipelines
from kedro.framework.startup import bootstrap_project

import sat_dengue

ROOT = Path(__file__).resolve().parents[2]


def test_repository_bootstrap() -> None:
    metadata = bootstrap_project(ROOT)
    assert metadata.package_name == "sat_dengue"
    assert importlib.metadata.version("sat-dengue-v2") == sat_dengue.__version__
    assert set(pipelines) == {
        "__default__",
        "foundation",
        "data",
        "preparation",
        "training_replay",
        "training_synthetic",
        "evaluation_replay",
        "evaluation_synthetic",
        "replay",
        "replay_synthetic",
        "exp01_synthetic",
        "exp01",
        "exp01_preflight",
        "exp02",
        "exp02_preflight",
        "exp02_synthetic",
        "exp03",
        "exp03_preflight",
        "exp03_synthetic",
    }
    assert {node.name for node in pipelines["foundation"].nodes} == {"resolve_configuration"}
    assert pipelines["foundation"].inputs() == {"configuration_inputs", "parameters"}
    assert pipelines["foundation"].outputs() == {"resolved_configuration"}


def test_domain_functions_have_no_orchestration_or_tracking_imports() -> None:
    paths = [
        *ROOT.joinpath("scripts").rglob("*.py"),
        ROOT / "src/sat_dengue/configuration.py",
        *ROOT.joinpath("src/sat_dengue/data").glob("*.py"),
    ]
    for path in paths:
        tree = ast.parse(path.read_text())
        for statement in ast.walk(tree):
            modules = []
            if isinstance(statement, ast.Import):
                modules = [alias.name for alias in statement.names]
            elif isinstance(statement, ast.ImportFrom) and statement.module:
                modules = [statement.module]
            assert not {name.split(".")[0] for name in modules} & {"kedro", "mlflow"}, path


def test_base_bootstrap_and_training_dependency_boundary() -> None:
    import os
    import subprocess
    import sys

    env = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join([str(ROOT), str(ROOT / "src")]),
        PYTHONDONTWRITEBYTECODE="1",
        KEDRO_DISABLE_TELEMETRY="yes",
    )
    result = subprocess.run(
        [sys.executable, "tests/integration/base_bootstrap.py"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"optional_modules_imported": []' in result.stdout
