"""Explicit no-fit national V4 graph."""

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets.national_v4 import assemble_v4


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                assemble_v4,
                ["national_v4_sources", "parameters"],
                "canonical_model_table_national_v4",
                name="build_canonical_national_v4",
            )
        ]
    )
