"""One independent, explicitly selected national data publication."""

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets.national import assemble_national


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                assemble_national,
                inputs=["national_canonical_sources", "parameters"],
                outputs="canonical_model_table_national_v1",
                name="build_canonical_model_table_national_v1",
            )
        ]
    )
