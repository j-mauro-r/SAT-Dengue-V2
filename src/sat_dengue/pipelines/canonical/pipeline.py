"""An additional data source; independent of replay and model tracking."""

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets.canonical import assemble_canonical


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                assemble_canonical,
                inputs=["canonical_stage2_sources", "parameters"],
                outputs="canonical_model_table_v1",
                name="build_canonical_model_table_v1",
            ),
        ]
    )
