# System Overview

## Implemented Local Scientific Pipeline

1. The Kedro `data` graph consumes verified epidemiological/climate sources and publishes new isolated individual/monthly outputs, current channel, future Y and readiness/provenance evidence. Pure rules live in `src/sat_dengue/data/`. [Notebook 03](../../notebooks/03_consolidated_dataset_pipeline.ipynb), its original outputs and import/CLI adapter remain preserved for historical and downstream consumers.
2. The Kedro `preparation` graph reads explicitly verified Stage 2 products, creates deterministic antecedents, selects eight temporal X/Y cohorts and replays existing saved preparers without refitting. Pure rules live in `src/sat_dengue/training_preparation/`; dataset adapters persist separate X/Y/keys/controls/schema/state/provenance in new isolated immutable engineering bundles. [Notebook 04](../../notebooks/04_training_preparation_pipeline.ipynb), original bundles and legacy import paths remain preserved.
3. Kedro `training_synthetic` runs bounded fitting on an internally generated deterministic fixture; `training_replay` loads and predicts with 40 development models and six frozen components under fit/search denial. Pure model rules live in `src/sat_dengue/model_training/`, shared metrics in `src/sat_dengue/metrics.py`; datasets verify native identities and atomically publish separate engineering bundles. The [Stage 4 workflow](../product/stage-4/README.md) owns these disjoint routes. Historical notebooks, native components and thin import adapters remain preserved.
4. The [preparation workflow](../product/stage-3/README.md) owns interfaces and output roles. Stage 4 trained the candidate families and Stage 5 completed the frozen 2025 comparison. All six candidate/horizon procedures missed the approved false-alert constraint; Mauricio accepted G5 `NOT_APPROVED`, no champion is selected, and Stage 5 is closed. The [master plan](../roadmap/master-plan.md) owns the integration boundary.

Private source data, derived CSVs and runtime evidence stay outside Git under the [data policy](../data/data-policy.md). Tests use small synthetic fixtures; current contracts and code are versioned.

## Implemented Kedro Foundation

[ADR-0002](../decisions/adr-0002-kedro-orchestration-boundary.md) owns the package,
configuration and dependency decision. `src/sat_dengue/configuration.py` resolves
operational settings without framework imports; `config_loader.py` validates
merged YAML/runtime parameters; `pipeline_registry.py` registers the one-node
`foundation` graph, the 11-node Stage 2 `data` graph, seven-node Stage 3 `preparation` graph,
three-node `training_replay` graph and four-node `training_synthetic` graph; `datasets/` reads the
approved scientific JSON documents and publishes verified execution snapshots and
isolated Stage 2 engineering bundles. Settings register the loader.

```text
conf/base + approved scientific JSON + execution provenance
    -> strict configuration resolution -> immutable per-run JSON snapshot
```

The implemented profiles are `foundation`, `data`, `preparation`, `training_replay`
and `training_synthetic`, all with `tracking: disabled`. No scientific
values can be supplied through YAML. Catalog replacement, unknown settings and
changed authority identities fail closed. Existing physical data/artifact paths,
scientific bundles and original hashes remain authoritative. MLflow is an optional
pinned dependency; its adapter belongs to T-tracking. The data graph consumes resolved configuration after snapshot publication.
All future stage assembly must retain this boundary; domain calculations remain
independent of framework and persistence concerns.

The [migration record](../operations/kedro-migration.md) owns installation,
metadata lineage, the Stage 2 catalog and exact dispositions. Stage 2 parity
compares complete protected cohorts and preserves original bytes/identities.
Stage 3 consumes explicit producer/consumer cutoffs and saved-state identities at node
boundaries. Its real run performs zero model fits and zero preparer refits. Stage 4
replay preserves that boundary, verifies complete saved outputs and native roundtrips
under both LightGBM 4.6 and 4.7, and rejects unknown families/configurations. The
synthetic graph has no real-source input. Calibration, thresholds and final assessment
retain existing entrypoints until T-evaluation; tracking remains disabled. The default
remains foundation, and future default E2E must compose inference-only replay.

## Planned Runtime Product

The approved first vertical slice is read-only:

```text
persisted, traceable result -> read-only API -> dashboard
```

The dashboard may filter and present API-supplied values but cannot write data, trigger inference, recompute scientific values, or present an evaluation procedure as operationally approved. A prototype precedes Stage 6 contract freeze. Model integration remains blocked while G5 has no approved champion.

A later write-enabled iteration may add explicit monthly input -> validation -> inference -> persistence and separate expert-feedback persistence. Feedback links to an immutable prediction identity and remains separate from the later observed epidemiological outcome. The [dashboard story](../product/stage-1/PROD-04-dashboard-master-user-story.md) owns behavior; final runtime schemas remain unfrozen. Do not introduce services, orchestration platforms, or deployment infrastructure solely to mirror the target architecture.
