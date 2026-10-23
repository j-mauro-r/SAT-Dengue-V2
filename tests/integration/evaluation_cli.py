"""Run the frozen evaluation CLI under whole-process fitting and selection denial."""

from __future__ import annotations

import sys

from sat_dengue.datasets.evaluation_legacy import no_adjustment
from sat_dengue.pipeline_registry import register_pipelines

if __name__ == "__main__":
    from kedro.framework.cli import main

    register_pipelines()
    sys.argv = [
        "kedro",
        "run",
        "--pipeline=evaluation_replay",
        "--params=profile=evaluation_replay",
    ]
    with no_adjustment():
        main()
