"""Explicit contract, provenance, cohort, inference, calibration, alert and policy dependencies."""

from kedro.pipeline import Node, Pipeline, node

from . import nodes


def common_nodes(source_name: str) -> list[Node]:
    return [
        node(
            nodes.validate_sources,
            [source_name, "resolved_configuration"],
            "evaluation_verified",
            name="evaluation_validate_frozen_proposal_and_sources",
        ),
        node(
            nodes.construct_cohorts,
            ["evaluation_verified", "resolved_configuration"],
            "evaluation_cohorts",
            name="evaluation_build_cohorts_and_validate_availability",
        ),
        node(
            nodes.replay_raw_probabilities,
            ["evaluation_verified", "evaluation_cohorts", "resolved_configuration"],
            "evaluation_raw_probabilities",
            name="evaluation_saved_component_inference",
        ),
        node(
            nodes.apply_calibration,
            ["evaluation_raw_probabilities", "evaluation_verified"],
            "evaluation_calibrated_probabilities",
            name="evaluation_apply_frozen_calibration",
        ),
        node(
            nodes.emit_alerts,
            [
                "evaluation_raw_probabilities",
                "evaluation_calibrated_probabilities",
                "evaluation_verified",
                "evaluation_cohorts",
            ],
            "evaluation_alerts",
            name="evaluation_emit_retained_threshold_alerts",
        ),
        node(
            nodes.compute_final_metrics,
            [
                "evaluation_alerts",
                "evaluation_cohorts",
                "evaluation_verified",
                "resolved_configuration",
            ],
            "evaluation_metrics",
            name="evaluation_compute_frozen_metrics_and_uncertainty",
        ),
        node(
            nodes.compute_development_metrics,
            ["evaluation_verified", "resolved_configuration"],
            "evaluation_development",
            name="evaluation_replay_development_assessment",
        ),
        node(
            nodes.apply_decision_policy,
            ["evaluation_metrics", "resolved_configuration", "evaluation_verified"],
            "evaluation_decisions",
            name="evaluation_apply_frozen_decision_policy",
        ),
        node(
            nodes.assemble_payloads,
            [
                "evaluation_decisions",
                "evaluation_development",
                "evaluation_verified",
                "resolved_configuration",
            ],
            "evaluation_bundle",
            name="evaluation_verify_parity_and_assemble_publication",
        ),
    ]


def create_replay_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                nodes.resolve_replay_configuration,
                ["configuration_inputs", "parameters", "evaluation_sources"],
                "resolved_configuration",
                name="resolve_evaluation_replay_configuration",
            ),
            *common_nodes("evaluation_sources"),
        ]
    )


def create_synthetic_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                nodes.resolve_synthetic_configuration,
                ["configuration_inputs", "parameters"],
                "resolved_configuration",
                name="resolve_evaluation_synthetic_configuration",
            ),
            node(
                nodes.generate_synthetic_sources,
                "resolved_configuration",
                "evaluation_synthetic_sources",
                name="evaluation_generate_internal_synthetic_fixture",
            ),
            *common_nodes("evaluation_synthetic_sources"),
        ]
    )
