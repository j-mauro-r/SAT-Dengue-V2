"""Assemble only the implemented configuration-validation pipeline."""

from kedro.pipeline import Pipeline, node

from sat_dengue.configuration import resolve_configuration


def register_pipelines() -> dict[str, Pipeline]:
    """Expose a useful no-fit command; scientific pipelines follow in later tasks."""
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
    return {"__default__": foundation, "foundation": foundation}
