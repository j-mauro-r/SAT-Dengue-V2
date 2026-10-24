"""Execute the public replay CLI with a whole-process real-adjustment denial guard."""

from __future__ import annotations

import sys

from sat_dengue.datasets.evaluation_legacy import no_adjustment
from sat_dengue.final_evaluation import workflow as evaluation_workflow
from sat_dengue.pipeline_registry import register_pipelines

if __name__ == "__main__":
    from kedro.framework.cli import main

    register_pipelines()
    del evaluation_workflow
    sys.argv = ["kedro", "run", "--pipeline=replay"]
    with no_adjustment():
        main()
