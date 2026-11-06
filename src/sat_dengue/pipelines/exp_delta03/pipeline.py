"""Thin graph bindings; scientific transformations remain pure domain functions."""

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets import exp_delta03_training as training
from sat_dengue.datasets.exp_delta03 import analyze, assemble, synthetic


def pipelines() -> dict[str, Pipeline]:
    graphs = {
        "exp_delta03_preflight": Pipeline(
            [
                node(
                    training.phase2_preflight,
                    "parameters",
                    "exp_delta03_admission",
                    name="exp_delta03_verify_training_metadata",
                )
            ]
        ),
        "exp_delta03_preparation": Pipeline(
            [
                node(
                    analyze,
                    ["exp_delta03_sources", "parameters"],
                    ["exp_delta03_context", "exp_delta03_quality"],
                    name="exp_delta03_profile_source",
                ),
                node(
                    assemble,
                    ["exp_delta03_context", "exp_delta03_quality"],
                    "exp_delta03_prepared",
                    name="exp_delta03_prepare_and_gate_matrices",
                ),
            ]
        ),
        "exp_delta03_synthetic": Pipeline(
            [
                node(
                    synthetic,
                    "parameters",
                    "exp_delta03_synthetic_receipt",
                    name="exp_delta03_generated_probe",
                )
            ]
        ),
    }

    phases = [
        (training.training_source, "parameters", "sources", "load_training_contract"),
        (training.authorize_and_load, "sources", "admitted", "authorize_and_load"),
        (training.build_training_plan, "admitted", "planned", "build_training_plan"),
        (training.train_models, "planned", "trained", "train_models"),
        (training.fit_calibrators, "trained", "calibrated", "fit_calibrators"),
        (training.select_thresholds, "calibrated", "selected", "select_thresholds"),
        (training.generate_predictions, "selected", "predicted", "generate_predictions"),
        (training.evaluate, "predicted", "evaluated", "evaluate"),
        (training.compare_ablations, "evaluated", "compared", "compare_ablations"),
        (training.publish_bundle, "compared", "published", "publish_bundle"),
        (training.track_results, "published", "receipt", "track_results"),
    ]
    for profile in ("exp_delta03", "exp_delta03_synthetic"):
        namespace = "exp_delta03_training" if profile == "exp_delta03" else profile
        graph = Pipeline(
            [
                node(
                    function,
                    source if source == "parameters" else namespace + "_" + source,
                    (
                        profile + "_training_receipt"
                        if profile == "exp_delta03_synthetic" and destination == "receipt"
                        else "exp_delta03_receipt"
                        if profile == "exp_delta03" and destination == "receipt"
                        else namespace + "_" + destination
                    ),
                    name=profile + "_" + name,
                )
                for function, source, destination, name in phases
            ]
        )
        graphs[profile] = graphs[profile] + graph if profile in graphs else graph
    return graphs
