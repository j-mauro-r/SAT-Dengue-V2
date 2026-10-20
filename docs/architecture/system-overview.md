# System Overview

## Implemented Local Scientific Pipeline

1. [Notebook 03](../../notebooks/03_consolidated_dataset_pipeline.ipynb) and `scripts/stage2_consolidated_dataset_pipeline.py` consume the epidemiological and climate sources. They publish the individual consolidated CSV, municipality-month panel, current endemic-channel state, future Y and construction/quality evidence.
2. [Notebook 04](../../notebooks/04_training_preparation_pipeline.ipynb) orchestrates `scripts/training_preparation/`. It reads notebook 03 products without rerunning EDA, creates deterministic antecedents, selects temporal X/Y, fits preparers on training only and persists immutable bundles with reusable JSON state.
3. The [preparation workflow](../product/stage-3/README.md) owns interfaces and output roles. The [master plan](../roadmap/master-plan.md) owns progress and outstanding gates. A future modeling task consumes these verified outputs; no predictor or champion exists yet.

Private source data, derived CSVs and runtime evidence stay outside Git under the [data policy](../data/data-policy.md). Tests use small synthetic fixtures; current contracts and code are versioned.

## Planned Runtime Product

Model inference -> result persistence -> API -> dashboard remains planned. A user will upload a new period, validate it and explicitly trigger inference; opening/refreshing the dashboard will read persisted results. The [product definition](../product/product-definition.md) owns that behavior.

Final runtime input/prediction/API schemas remain unfrozen until scientific/model evidence and product needs are aligned. Do not introduce services, orchestration platforms or deployment infrastructure solely to mirror this target diagram.
