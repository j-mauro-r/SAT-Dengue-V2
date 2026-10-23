"""Explicit disjoint data dependencies prevent real fitting from replay/default routes."""

from kedro.pipeline import Pipeline, node

from . import nodes


def create_replay_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                nodes.resolve_replay_configuration,
                ["configuration_inputs", "parameters", "training_sources"],
                "resolved_configuration",
                name="resolve_training_replay_configuration",
            ),
            node(
                nodes.replay,
                ["training_sources", "resolved_configuration"],
                "training_replayed",
                name="training_saved_component_replay",
            ),
            node(
                nodes.assemble_training_payloads,
                ["training_replayed", "resolved_configuration"],
                "training_bundle",
                name="training_replay_publish",
            ),
        ]
    )


def create_synthetic_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                nodes.resolve_synthetic_configuration,
                ["configuration_inputs", "parameters"],
                "resolved_configuration",
                name="resolve_training_synthetic_configuration",
            ),
            node(
                nodes.synthetic_cases,
                "resolved_configuration",
                "training_synthetic_cases",
                name="training_generate_synthetic_cases",
            ),
            node(
                nodes.fit_synthetic,
                ["training_synthetic_cases", "resolved_configuration"],
                "training_synthetic_result",
                name="training_fit_synthetic_only",
            ),
            node(
                nodes.assemble_training_payloads,
                ["training_synthetic_result", "resolved_configuration"],
                "training_bundle",
                name="training_synthetic_publish",
            ),
        ]
    )
