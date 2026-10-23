"""Defer optional evaluation implementations until their selected node executes."""

from typing import Any

from sat_dengue.datasets.training import require_modeling


def resolve_replay_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import resolve_replay_configuration as calculate

    with no_adjustment():
        return calculate(inputs, parameters, sources)


def resolve_synthetic_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import resolve_synthetic_configuration as calculate

    with no_adjustment():
        return calculate(inputs, parameters)


def generate_synthetic_sources(resolved: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import generate_synthetic_sources as calculate

    with no_adjustment():
        return calculate(resolved)


def validate_sources(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import validate_sources as calculate

    with no_adjustment():
        return calculate(sources, resolved)


def construct_cohorts(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import construct_cohorts as calculate

    with no_adjustment():
        return calculate(sources, resolved)


def replay_raw_probabilities(
    sources: dict[str, Any], cohort_data: dict[str, Any], resolved: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import replay_raw_probabilities as calculate

    with no_adjustment():
        return calculate(sources, cohort_data, resolved)


def apply_calibration(raw: dict[str, Any], sources: dict[str, Any]) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import apply_calibration as calculate

    with no_adjustment():
        return calculate(raw, sources)


def emit_alerts(
    raw: dict[str, Any],
    calibrated: dict[str, Any],
    sources: dict[str, Any],
    cohort_data: dict[str, Any],
) -> dict[int, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import emit_alerts as calculate

    with no_adjustment():
        return calculate(raw, calibrated, sources, cohort_data)


def compute_final_metrics(
    predictions: dict[int, Any],
    cohort_data: dict[str, Any],
    sources: dict[str, Any],
    resolved: dict[str, Any],
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import compute_final_metrics as calculate

    with no_adjustment():
        return calculate(predictions, cohort_data, sources, resolved)


def compute_development_metrics(
    sources: dict[str, Any], resolved: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import compute_development_metrics as calculate

    with no_adjustment():
        return calculate(sources, resolved)


def apply_decision_policy(
    result: dict[str, Any], resolved: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation_legacy import no_adjustment
    from sat_dengue.final_evaluation.workflow import apply_decision_policy as calculate

    with no_adjustment():
        return calculate(result, resolved, sources)


def assemble_payloads(
    result: dict[str, Any],
    development: dict[str, Any],
    sources: dict[str, Any],
    resolved: dict[str, Any],
) -> dict[str, Any]:
    require_modeling()
    from sat_dengue.datasets.evaluation import assemble_payloads as calculate
    from sat_dengue.datasets.evaluation_legacy import no_adjustment

    with no_adjustment():
        return calculate(result, development, sources, resolved)
