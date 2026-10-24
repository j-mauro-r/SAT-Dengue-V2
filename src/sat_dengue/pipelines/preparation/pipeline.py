"""Explicit scientific inputs, cutoff boundaries and immutable preparation outputs."""

from kedro.pipeline import Pipeline, node

from . import nodes


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                nodes.resolve_preparation_configuration,
                ["configuration_inputs", "parameters", "preparation_sources", "saved_preparers"],
                "resolved_configuration",
                name="resolve_preparation_configuration",
            ),
            node(
                nodes.boundaries,
                "resolved_configuration",
                ["producer_cutoffs", "consumer_cutoffs"],
                name="preparation_cutoffs",
            ),
            node(
                nodes.features,
                ["preparation_sources", "resolved_configuration"],
                ["preparation_keys", "preparation_features"],
                name="preparation_features",
            ),
            node(
                nodes.eligibility,
                ["preparation_sources", "resolved_configuration"],
                ["preparation_controls", "preparation_eligibility"],
                name="preparation_eligibility",
            ),
            node(
                nodes.partitions,
                [
                    "preparation_keys",
                    "preparation_features",
                    "preparation_controls",
                    "preparation_sources",
                    "resolved_configuration",
                    "producer_cutoffs",
                    "consumer_cutoffs",
                ],
                "preparation_windows",
                name="preparation_partitions",
            ),
            node(
                nodes.replay,
                [
                    "preparation_windows",
                    "saved_preparers",
                    "resolved_configuration",
                    "producer_cutoffs",
                    "consumer_cutoffs",
                ],
                "preparation_transformed",
                name="preparation_replay",
            ),
            node(
                nodes.bundle_payloads,
                [
                    "preparation_keys",
                    "preparation_features",
                    "preparation_controls",
                    "preparation_eligibility",
                    "preparation_transformed",
                    "resolved_configuration",
                    "producer_cutoffs",
                    "consumer_cutoffs",
                ],
                "preparation_bundle",
                name="preparation_publish",
            ),
        ]
    )
