"""Execute the real inference-only Kedro CLI with whole-process fit/search denial."""

from __future__ import annotations

import sys

from sat_dengue.datasets.training_legacy import no_fitting
from sat_dengue.pipeline_registry import register_pipelines

if __name__ == "__main__":
    from kedro.framework.cli import main

    # Import-time sklearn decorator construction is not a fit; guard all CLI execution.
    register_pipelines()
    sys.argv = ["kedro", "run", "--pipeline=training_replay", "--params=profile=training_replay"]
    with no_fitting():
        main()
