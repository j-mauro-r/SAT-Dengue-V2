# System Overview

## Implemented Local Scientific Pipeline

1. [Notebook 03](../../notebooks/03_consolidated_dataset_pipeline.ipynb) and `scripts/stage2_consolidated_dataset_pipeline.py` consume the epidemiological and climate sources. They publish the individual consolidated CSV, municipality-month panel, current endemic-channel state, future Y and construction/quality evidence.
2. [Notebook 04](../../notebooks/04_training_preparation_pipeline.ipynb) orchestrates `scripts/training_preparation/`. It reads notebook 03 products without rerunning EDA, creates deterministic antecedents, selects temporal X/Y, fits preparers on training only and persists immutable bundles with reusable JSON state.
3. The [preparation workflow](../product/stage-3/README.md) owns interfaces and output roles. Stage 4 trained the candidate families and Stage 5 completed the frozen 2025 comparison. All six candidate/horizon procedures missed the approved false-alert constraint; Mauricio accepted G5 `NOT_APPROVED`, no champion is selected, and Stage 5 is closed. The [master plan](../roadmap/master-plan.md) owns the integration boundary.

Private source data, derived CSVs and runtime evidence stay outside Git under the [data policy](../data/data-policy.md). Tests use small synthetic fixtures; current contracts and code are versioned.

## Planned Runtime Product

The approved first vertical slice is read-only:

```text
persisted, traceable result -> read-only API -> dashboard
```

The dashboard may filter and present API-supplied values but cannot write data, trigger inference, recompute scientific values, or present an evaluation procedure as operationally approved. A prototype precedes Stage 6 contract freeze. Model integration remains blocked while G5 has no approved champion.

A later write-enabled iteration may add explicit monthly input -> validation -> inference -> persistence and separate expert-feedback persistence. Feedback links to an immutable prediction identity and remains separate from the later observed epidemiological outcome. The [dashboard story](../product/stage-1/PROD-04-dashboard-master-user-story.md) owns behavior; final runtime schemas remain unfrozen. Do not introduce services, orchestration platforms, or deployment infrastructure solely to mirror the target architecture.
