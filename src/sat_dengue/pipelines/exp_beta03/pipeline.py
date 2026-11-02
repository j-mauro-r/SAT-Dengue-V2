"""Keep development policy selection separate from application and reporting."""

from kedro.pipeline import Pipeline, node

from sat_dengue.experiments.exp_beta03 import apply, evaluate, prepare, select


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                prepare,
                ["exp_beta03_sources", "parameters"],
                "beta03_prepared",
                name="beta03_prepare",
            ),
            node(select, "beta03_prepared", "beta03_selected", name="beta03_select"),
            node(apply, "beta03_selected", "beta03_alerts", name="beta03_apply"),
            node(evaluate, "beta03_alerts", "exp_beta03_bundle", name="beta03_evaluate"),
        ]
    )
