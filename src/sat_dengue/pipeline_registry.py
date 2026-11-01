"""Assemble the implemented foundation and Stage 2 data pipelines."""

from kedro.pipeline import Pipeline, node

from sat_dengue.configuration import resolve_configuration
from sat_dengue.experiments import exp03, exp03_preflight, exp03_runner
from sat_dengue.experiments.exp01 import synthetic_run
from sat_dengue.experiments.exp01_preflight import preflight
from sat_dengue.experiments.exp01_runner import execute_authorized, load_authorized_sources
from sat_dengue.experiments.exp03_1_preflight import preflight as exp03_1_preflight
from sat_dengue.experiments.exp03_1_runner import (
    execute_authorized as execute_exp03_1_authorized,
)
from sat_dengue.experiments.exp03_1_runner import (
    load_authorized_sources as load_exp03_1_authorized_sources,
)
from sat_dengue.pipelines.canonical.pipeline import create_pipeline as canonical_pipeline
from sat_dengue.pipelines.data.pipeline import create_pipeline
from sat_dengue.pipelines.evaluation.pipeline import create_replay_pipeline as evaluation_replay
from sat_dengue.pipelines.evaluation.pipeline import (
    create_synthetic_pipeline as evaluation_synthetic,
)
from sat_dengue.pipelines.exp02.pipeline import pipelines as exp02_pipelines
from sat_dengue.pipelines.exp04.pipeline import pipelines as exp04_pipelines
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
    exp01_preflight = Pipeline(
        [
            node(
                preflight,
                inputs=["parameters", "exp01_sources"],
                outputs="exp01_preflight_receipt",
                name="exp01_preflight",
            )
        ]
    )
    exp01 = exp01_preflight + Pipeline(
        [
            node(
                load_authorized_sources,
                inputs="exp01_preflight_receipt",
                outputs="exp01_authorized_sources",
                name="exp01_authorize_and_load",
            ),
            node(
                execute_authorized,
                inputs="exp01_authorized_sources",
                outputs="exp01_bundle",
                name="exp01_execute_paired",
            ),
        ]
    )
    exp03_check = Pipeline(
        [
            node(
                exp03_preflight.preflight,
                inputs=["parameters", "exp03_sources"],
                outputs="exp03_preflight_receipt",
                name="exp03_preflight",
            )
        ]
    )
    exp03_real = exp03_check + Pipeline(
        [
            node(
                exp03_runner.load_authorized_sources,
                inputs="exp03_preflight_receipt",
                outputs="exp03_authorized_sources",
                name="exp03_authorize_and_load",
            ),
            node(
                exp03_runner.execute_authorized,
                inputs="exp03_authorized_sources",
                outputs="exp03_bundle",
                name="exp03_execute_ablation",
            ),
        ]
    )
    exp03_1_check = Pipeline(
        [
            node(
                exp03_1_preflight,
                inputs=["parameters", "exp03_1_sources"],
                outputs="exp03_1_preflight_receipt",
                name="exp03_1_preflight",
            )
        ]
    )
    exp03_1_real = exp03_1_check + Pipeline(
        [
            node(
                load_exp03_1_authorized_sources,
                inputs=["exp03_1_preflight_receipt", "parameters"],
                outputs="exp03_1_authorized_sources",
                name="exp03_1_authorize_and_load",
            ),
            node(
                execute_exp03_1_authorized,
                inputs="exp03_1_authorized_sources",
                outputs="exp03_1_bundle",
                name="exp03_1_execute_frozen_matrix",
            ),
        ]
    )
    return {
        "canonical_model_table_v1": canonical_pipeline(),
        **exp04_pipelines(),
        "exp03_1": exp03_1_real,
        "exp03_1_preflight": exp03_1_check,
        "exp03": exp03_real,
        "exp03_preflight": exp03_check,
        "exp03_synthetic": Pipeline(
            [
                node(
                    exp03.synthetic_run,
                    inputs=None,
                    outputs="exp03_synthetic_receipt",
                    name="exp03_synthetic_probe",
                )
            ]
        ),
        "exp01": exp01,
        "exp01_preflight": exp01_preflight,
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
        **exp02_pipelines(),
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
