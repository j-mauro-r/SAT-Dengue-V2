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
    assert set(pipelines) == {"__default__", "foundation", "data"}
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
