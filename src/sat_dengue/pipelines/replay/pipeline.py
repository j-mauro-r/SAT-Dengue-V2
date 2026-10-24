"""Expand existing nodes into namespaces; checkpoint shortcuts preserve real dependencies."""

from __future__ import annotations

from functools import partial
from typing import Any

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets.replay import assemble_replay
from sat_dengue.datasets.replay_identity import CACHED, open_execution
from sat_dengue.datasets.replay_sources import (
    data_inputs,
    evaluation_inputs,
    preparation_inputs,
    training_inputs,
)
from sat_dengue.pipelines.data.pipeline import create_pipeline as data_pipeline
from sat_dengue.pipelines.evaluation import nodes as evaluation_nodes
from sat_dengue.pipelines.evaluation.pipeline import common_nodes
from sat_dengue.pipelines.preparation.pipeline import create_pipeline as preparation_pipeline
from sat_dengue.pipelines.training.pipeline import (
    create_replay_pipeline as training_replay,
)
from sat_dengue.pipelines.training.pipeline import (
    create_synthetic_pipeline as training_synthetic,
)


def invoke(
    context: dict[str, Any],
    *args: Any,
    function: Any,
    stage: str,
    arity: int,
    publication: bool = False,
    fixture_inference: bool = False,
) -> Any:
    if stage in context["cache"]:
        if publication:
            return {"reuse": context["cache"][stage], "context": context}
        return tuple(CACHED for _ in range(arity)) if arity > 1 else CACHED
    from sat_dengue.datasets.evaluation_legacy import no_adjustment

    if fixture_inference:
        from sat_dengue.datasets.replay_synthetic import saved_fixture_inference

        with no_adjustment():
            return saved_fixture_inference(*args)
    if context["mode"] == "synthetic" and stage == "training":
        return function(*args)
    with no_adjustment():
        return function(*args)


def stage_graph(graph: Pipeline, stage: str, *, synthetic: bool) -> list[Any]:
    result = []
    for original in graph.nodes:
        outputs = [stage + "." + n for n in original.outputs]
        publication = original.outputs == [
            {
                "data": "stage2_bundle",
                "preparation": "preparation_bundle",
                "training": "training_bundle",
                "evaluation": "evaluation_bundle",
            }[stage]
        ]
        function: Any = partial(
            invoke,
            function=original.func,
            stage=stage,
            arity=len(outputs),
            publication=publication,
            fixture_inference=synthetic
            and stage == "evaluation"
            and original.name == "evaluation_saved_component_inference",
        )
        function.__name__ = original.name
        result.append(
            node(
                function,
                ["replay_context", *[stage + "." + n for n in original.inputs]],
                outputs if len(outputs) > 1 else outputs[0],
                name="replay_" + stage + "__" + original.name,
            )
        )
    return result


def create_pipeline(*, synthetic: bool = False) -> Pipeline:
    mode = "synthetic" if synthetic else "replay"
    evaluation = Pipeline(
        [
            node(
                evaluation_nodes.resolve_replay_configuration
                if not synthetic
                else evaluation_nodes.resolve_synthetic_configuration,
                ["configuration_inputs", "parameters", "evaluation_sources"]
                if not synthetic
                else ["configuration_inputs", "parameters"],
                "resolved_configuration",
                name="resolve_evaluation_configuration",
            ),
            *common_nodes("evaluation_sources"),
        ]
    )
    return Pipeline(
        [
            node(
                partial(open_execution, mode=mode),
                ["configuration_inputs", "parameters"],
                "replay_context",
                name="replay_resolve_verify_and_open_execution",
            ),
            node(
                data_inputs,
                "replay_context",
                [
                    "data.configuration_inputs",
                    "data.parameters",
                    "data.stage2_sources",
                    "data.stage2_epi_raw",
                    "data.stage2_climate_raw",
                ],
                name="replay_bind_data_inputs",
            ),
            *stage_graph(data_pipeline(), "data", synthetic=synthetic),
            node(
                preparation_inputs,
                ["replay_context", "data.stage2_bundle"],
                [
                    "preparation.configuration_inputs",
                    "preparation.parameters",
                    "preparation.preparation_sources",
                    "preparation.saved_preparers",
                ],
                name="replay_verify_data_and_bind_preparation",
            ),
            *stage_graph(preparation_pipeline(), "preparation", synthetic=synthetic),
            node(
                training_inputs,
                ["replay_context", "preparation.preparation_bundle"],
                ["training.configuration_inputs", "training.parameters"]
                + ([] if synthetic else ["training.training_sources"]),
                name="replay_verify_preparation_and_bind_training",
            ),
            *stage_graph(
                training_synthetic() if synthetic else training_replay(),
                "training",
                synthetic=synthetic,
            ),
            node(
                evaluation_inputs,
                ["replay_context", "training.training_bundle"],
                [
                    "evaluation.configuration_inputs",
                    "evaluation.parameters",
                    "evaluation.evaluation_sources",
                ],
                name="replay_verify_training_and_bind_evaluation",
            ),
            *stage_graph(evaluation, "evaluation", synthetic=synthetic),
            node(
                assemble_replay,
                [
                    "replay_context",
                    "data.stage2_bundle",
                    "preparation.preparation_bundle",
                    "training.training_bundle",
                    "evaluation.evaluation_bundle",
                ],
                "replay_bundle",
                name="replay_verify_full_lineage_and_commit",
            ),
        ]
    )
