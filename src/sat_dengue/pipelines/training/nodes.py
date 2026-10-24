"""Load optional model implementations only when a training node executes."""

from typing import Any

from sat_dengue.datasets.training import require_modeling


def resolve_replay_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.model_training.workflow import resolve_replay_configuration as resolve

    return resolve(inputs, parameters, sources)


def resolve_synthetic_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.model_training.workflow import resolve_synthetic_configuration as resolve

    return resolve(inputs, parameters)


def synthetic_cases(resolved: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.model_training.workflow import synthetic_cases as generate

    return generate(resolved)


def fit_synthetic(cases: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.model_training.workflow import fit_synthetic as fit

    return fit(cases, resolved)


def replay(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.training_legacy import no_fitting
    from sat_dengue.model_training.workflow import replay_components

    with no_fitting():
        return replay_components(sources, resolved)


def assemble_training_payloads(result: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    from sat_dengue.datasets.training import assemble_training_payloads as assemble

    return assemble(result, resolved)
