"""Assemble the implemented foundation and Stage 2 data pipelines."""

from kedro.pipeline import Pipeline, node

from sat_dengue.configuration import resolve_configuration
from sat_dengue.pipelines.data.pipeline import create_pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Expose foundation by default and explicit no-fit Stage 2 execution."""
    foundation = Pipeline(
        [
            node(
                resolve_configuration,
                inputs=["configuration_inputs", "parameters"],
                outputs="resolved_configuration",
                name="resolve_configuration",
            ),
        ]
    )
    return {"__default__": foundation, "foundation": foundation, "data": create_pipeline()}
