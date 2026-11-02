"""Separate supervised preparation, native fitting, adaptation, prediction and evaluation."""

from kedro.pipeline import Pipeline, node

from sat_dengue.experiments.exp_beta01 import prepare
from sat_dengue.experiments.exp_beta01_engine import adapt, evaluate, predict, train


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                prepare, ["exp_beta01_sources", "parameters"], "beta_prepared", name="beta_prepare"
            ),
            node(train, "beta_prepared", "beta_trained", name="beta_train"),
            node(adapt, "beta_trained", "beta_adapted", name="beta_adapt"),
            node(predict, "beta_adapted", "beta_predictions", name="beta_predict"),
            node(evaluate, "beta_predictions", "exp_beta01_bundle", name="beta_evaluate"),
        ]
    )
