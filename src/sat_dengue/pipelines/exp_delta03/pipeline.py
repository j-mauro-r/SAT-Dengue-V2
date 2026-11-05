"""Thin graph bindings; scientific transformations remain pure domain functions."""

from kedro.pipeline import Pipeline, node

from sat_dengue.datasets.exp_delta03 import analyze, assemble, preflight, synthetic


def pipelines() -> dict[str, Pipeline]:
    return {
        "exp_delta03_preflight": Pipeline(
            [
                node(
                    preflight,
                    ["exp_delta03_sources", "parameters"],
                    "exp_delta03_admission",
                    name="exp_delta03_verify_source",
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
