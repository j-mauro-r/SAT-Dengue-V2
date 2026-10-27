"""Explicit preflight → authorization → labels → comparison → prediction → publication."""

from kedro.pipeline import Pipeline, node

from sat_dengue.experiments.exp02_preflight import preflight
from sat_dengue.experiments.exp02_runner import (
    compare_authorized,
    construct_authorized,
    load_authorized_sources,
    predictive_authorized,
    publication_authorized,
    synthetic_run,
)


def pipelines() -> dict[str, Pipeline]:
    check = node(
        preflight,
        ["parameters", "exp02_sources"],
        "exp02_preflight_receipt",
        name="exp02_preflight",
    )
    return {
        "exp02_preflight": Pipeline([check]),
        "exp02_synthetic": Pipeline(
            [node(synthetic_run, "parameters", "exp02_synthetic_receipt", name="exp02_synthetic")]
        ),
        "exp02": Pipeline(
            [
                check,
                node(
                    load_authorized_sources,
                    "exp02_preflight_receipt",
                    "exp02_authorized",
                    name="exp02_authorize_and_load",
                ),
                node(
                    construct_authorized,
                    "exp02_authorized",
                    "exp02_variants",
                    name="exp02_construct_labels",
                ),
                node(
                    compare_authorized,
                    "exp02_variants",
                    "exp02_compared",
                    name="exp02_compare_stability",
                ),
                node(
                    predictive_authorized,
                    "exp02_compared",
                    "exp02_predicted",
                    name="exp02_predictive_comparison",
                ),
                node(
                    publication_authorized, "exp02_predicted", "exp02_bundle", name="exp02_publish"
                ),
            ]
        ),
    }
