"""Assemble the implemented foundation and Stage 2 data pipelines."""

from kedro.pipeline import Pipeline, node

from sat_dengue.configuration import resolve_configuration
from sat_dengue.experiments.exp01 import synthetic_run
from sat_dengue.pipelines.data.pipeline import create_pipeline
from sat_dengue.pipelines.evaluation.pipeline import create_replay_pipeline as evaluation_replay
from sat_dengue.pipelines.evaluation.pipeline import (
    create_synthetic_pipeline as evaluation_synthetic,
)
from sat_dengue.pipelines.preparation.pipeline import create_pipeline as preparation_pipeline
from sat_dengue.pipelines.replay.pipeline import create_pipeline as replay_pipeline
from sat_dengue.pipelines.training.pipeline import create_replay_pipeline, create_synthetic_pipeline


def register_pipelines() -> dict[str, Pipeline]:
    """Expose foundation, implemented stages and the source-free EXP01 probe."""
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
    return {
        "__default__": foundation,
        "replay": replay_pipeline(),
        "replay_synthetic": replay_pipeline(synthetic=True),
        "evaluation_replay": evaluation_replay(),
        "evaluation_synthetic": evaluation_synthetic(),
        "foundation": foundation,
        "data": create_pipeline(),
        "preparation": preparation_pipeline(),
        "training_replay": create_replay_pipeline(),
        "training_synthetic": create_synthetic_pipeline(),
        "exp01_synthetic": Pipeline(
            [
                node(
                    synthetic_run,
                    inputs=None,
                    outputs="exp01_synthetic_receipt",
                    name="exp01_synthetic_preflight",
                )
            ]
        ),
    }
