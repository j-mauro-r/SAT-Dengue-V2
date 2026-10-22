# System Overview

## Implemented Local Scientific Pipeline

1. The Kedro `data` graph consumes verified epidemiological/climate sources and publishes new isolated individual/monthly outputs, current channel, future Y and readiness/provenance evidence. Pure rules live in `src/sat_dengue/data/`. [Notebook 03](../../notebooks/03_consolidated_dataset_pipeline.ipynb), its original outputs and import/CLI adapter remain preserved for historical and downstream consumers.
2. [Notebook 04](../../notebooks/04_training_preparation_pipeline.ipynb) orchestrates `scripts/training_preparation/`. It reads notebook 03 products without rerunning EDA, creates deterministic antecedents, selects temporal X/Y, fits preparers on training only and persists immutable bundles with reusable JSON state.
3. The [preparation workflow](../product/stage-3/README.md) owns interfaces and output roles. Stage 4 trained the candidate families and Stage 5 completed the frozen 2025 comparison. All six candidate/horizon procedures missed the approved false-alert constraint; Mauricio accepted G5 `NOT_APPROVED`, no champion is selected, and Stage 5 is closed. The [master plan](../roadmap/master-plan.md) owns the integration boundary.

Private source data, derived CSVs and runtime evidence stay outside Git under the [data policy](../data/data-policy.md). Tests use small synthetic fixtures; current contracts and code are versioned.

## Implemented Kedro Foundation

[ADR-0002](../decisions/adr-0002-kedro-orchestration-boundary.md) owns the package,
configuration and dependency decision. `src/sat_dengue/configuration.py` resolves
operational settings without framework imports; `config_loader.py` validates
merged YAML/runtime parameters; `pipeline_registry.py` registers the one-node
`foundation` graph and the 11-node Stage 2 `data` graph; `datasets/` reads the
approved scientific JSON documents and publishes verified execution snapshots and
isolated Stage 2 engineering bundles. Settings register the loader.

```text
conf/base + approved scientific JSON + execution provenance
    -> strict configuration resolution -> immutable per-run JSON snapshot
```

The implemented profiles are `foundation` and `data`, both with `tracking: disabled`. No scientific
values can be supplied through YAML. Catalog replacement, unknown settings and
changed authority identities fail closed. Existing physical data/artifact paths,
scientific bundles and original hashes remain authoritative. MLflow is an optional
pinned dependency; its adapter belongs to T-tracking. The data graph consumes resolved configuration after snapshot publication.
All future stage assembly must retain this boundary; domain calculations remain
independent of framework and persistence concerns.

The [migration record](../operations/kedro-migration.md) owns installation,
metadata lineage, the Stage 2 catalog and exact dispositions. Stage 2 parity
compares complete protected cohorts and preserves original bytes/identities.
Stage 3 and later implementations remain at their existing script/notebook
entrypoints until their separately authorized migration tasks.

## Planned Runtime Product

The approved first vertical slice is read-only:

```text
persisted, traceable result -> read-only API -> dashboard
```

The dashboard may filter and present API-supplied values but cannot write data, trigger inference, recompute scientific values, or present an evaluation procedure as operationally approved. A prototype precedes Stage 6 contract freeze. Model integration remains blocked while G5 has no approved champion.

A later write-enabled iteration may add explicit monthly input -> validation -> inference -> persistence and separate expert-feedback persistence. Feedback links to an immutable prediction identity and remains separate from the later observed epidemiological outcome. The [dashboard story](../product/stage-1/PROD-04-dashboard-master-user-story.md) owns behavior; final runtime schemas remain unfrozen. Do not introduce services, orchestration platforms, or deployment infrastructure solely to mirror the target architecture.
