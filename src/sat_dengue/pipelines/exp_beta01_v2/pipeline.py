"""Five explicit G1 stages; no historical fitting or territorial adaptation."""

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets.exp_beta01_v2 import evaluate
from sat_dengue.experiments.exp_beta01_v2 import calibrate, predict, prepare, train


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                prepare,
                ["exp_beta01_v2_sources", "parameters"],
                "beta_v2_prepared",
                name="beta_v2_prepare",
            ),
            node(train, "beta_v2_prepared", "beta_v2_trained", name="beta_v2_train"),
            node(calibrate, "beta_v2_trained", "beta_v2_calibrated", name="beta_v2_calibrate"),
            node(predict, "beta_v2_calibrated", "beta_v2_predictions", name="beta_v2_predict"),
            node(evaluate, "beta_v2_predictions", "exp_beta01_v2_bundle", name="beta_v2_evaluate"),
        ]
    )
