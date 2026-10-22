"""Wire the implemented Stage 2 calculations to explicit catalog dependencies."""

from kedro.pipeline import Pipeline, node

from sat_dengue.pipelines.data import nodes


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                nodes.resolve_data_configuration,
                ["configuration_inputs", "parameters", "stage2_sources"],
                "resolved_configuration",
                name="resolve_data_configuration",
            ),
            node(
                nodes.scope_catalog, "resolved_configuration", "stage2_catalog", name="stage2_scope"
            ),
            node(
                nodes.normalize_climate,
                ["stage2_climate_raw", "stage2_catalog", "resolved_configuration"],
                ["stage2_daily", "stage2_climate_summary"],
                name="stage2_normalize_climate",
            ),
            node(
                nodes.consolidate,
                ["stage2_epi_raw", "stage2_daily", "stage2_catalog", "resolved_configuration"],
                "stage2_consolidated",
                name="stage2_consolidate",
            ),
            node(
                nodes.aggregate_notifications,
                ["stage2_consolidated", "resolved_configuration"],
                "stage2_epi_summary",
                name="stage2_notification_counts",
            ),
            node(
                nodes.aggregate_climate,
                ["stage2_daily", "resolved_configuration"],
                "stage2_monthly_climate",
                name="stage2_monthly_climate",
            ),
            node(
                nodes.build_panel,
                [
                    "stage2_epi_summary",
                    "stage2_monthly_climate",
                    "stage2_catalog",
                    "resolved_configuration",
                ],
                "stage2_unlabeled_panel",
                name="stage2_panel",
            ),
            node(
                nodes.label_targets,
                ["stage2_unlabeled_panel", "resolved_configuration"],
                ["stage2_labeled_panel", "stage2_y_trace"],
                name="stage2_targets",
            ),
            node(
                nodes.current_channel,
                ["stage2_labeled_panel", "resolved_configuration"],
                ["stage2_panel", "stage2_channel_trace", "stage2_channel_summary"],
                name="stage2_current_channel",
            ),
            node(
                nodes.audit_readiness,
                ["stage2_panel", "stage2_epi_summary", "resolved_configuration"],
                ["stage2_readiness", "stage2_eligibility"],
                name="stage2_readiness",
            ),
            node(
                nodes.assemble_bundle,
                [
                    "stage2_panel",
                    "stage2_y_trace",
                    "stage2_channel_trace",
                    "stage2_channel_summary",
                    "stage2_epi_summary",
                    "stage2_climate_summary",
                    "stage2_readiness",
                    "stage2_eligibility",
                    "resolved_configuration",
                ],
                "stage2_bundle",
                name="stage2_provenance_bundle",
            ),
        ]
    )
