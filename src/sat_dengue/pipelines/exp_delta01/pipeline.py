"""Minimal verify/select/apply/evaluate responsibilities."""

from kedro.pipeline import Pipeline, node

from sat_dengue.experiments.exp_delta01 import apply, evaluate, prepare, select


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                prepare,
                ["exp_delta01_sources", "parameters"],
                "delta_prepared",
                name="delta_prepare",
            ),
            node(select, "delta_prepared", "delta_selected", name="delta_select"),
            node(apply, "delta_selected", "delta_applied", name="delta_apply"),
            node(evaluate, "delta_applied", "exp_delta01_bundle", name="delta_evaluate"),
        ]
    )
