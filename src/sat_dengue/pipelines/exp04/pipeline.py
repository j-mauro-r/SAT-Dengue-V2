"""Minimal lazy bindings to the existing Kedro execution mechanism."""

from __future__ import annotations

from typing import Any

from kedro.pipeline import Pipeline, node


def run(parameters: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.configuration import validate_parameters
    from sat_dengue.experiments.exp04_runner import functional_run, preflight

    checked = validate_parameters(parameters)
    if checked["profile"] == "exp04_preflight":
        return preflight()
    if checked["profile"] == "exp04_functional":
        return functional_run()
    raise ValueError("EXP04 requires its explicit preflight or functional profile")


def pipelines() -> dict[str, Pipeline]:
    return {
        name: Pipeline([node(run, "parameters", name + "_result", name=name)])
        for name in ("exp04_preflight", "exp04_functional")
    }
