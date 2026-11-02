"""Keep count fitting, probability conversion, policy and evaluation separate."""

from kedro.pipeline import Pipeline, node

from sat_dengue.experiments.exp_beta02 import prepare
from sat_dengue.experiments.exp_beta02_engine import evaluate, forecast, policy, risk, train


def create_pipeline() -> Pipeline:
    return Pipeline(
        [
            node(
                prepare,
                ["exp_beta02_sources", "parameters"],
                "beta02_prepared",
                name="beta02_prepare",
            ),
            node(train, "beta02_prepared", "beta02_trained", name="beta02_train"),
            node(forecast, "beta02_trained", "beta02_forecasts", name="beta02_forecast"),
            node(risk, "beta02_forecasts", "beta02_risks", name="beta02_risk"),
            node(policy, "beta02_risks", "beta02_alerts", name="beta02_policy"),
            node(evaluate, "beta02_alerts", "exp_beta02_bundle", name="beta02_evaluate"),
        ]
    )
