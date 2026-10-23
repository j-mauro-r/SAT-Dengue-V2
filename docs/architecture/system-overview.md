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
three-node `training_replay` graph, four-node `training_synthetic` graph, ten-node
`evaluation_replay` and eleven-node `evaluation_synthetic` graphs; `datasets/` reads the
approved scientific JSON documents and publishes verified execution snapshots and
isolated Stage 2 engineering bundles. Settings register the loader.

```text
conf/base + approved scientific JSON + execution provenance
    -> strict configuration resolution -> immutable per-run JSON snapshot
```

The implemented profiles are `foundation`, `data`, `preparation`, `training_replay`,
`training_synthetic`, `evaluation_replay` and `evaluation_synthetic`, with explicit `tracking: disabled` by default. No scientific
values can be supplied through YAML. Catalog replacement, unknown settings and
changed authority identities fail closed. Existing physical data/artifact paths,
scientific bundles and original hashes remain authoritative. MLflow is an optional
pinned dependency; its local adapter is registered through lifecycle hooks. The data graph consumes resolved configuration after snapshot publication.
All future stage assembly must retain this boundary; domain calculations remain
independent of framework and persistence concerns.

The [migration record](../operations/kedro-migration.md) owns installation,
metadata lineage, the Stage 2 catalog and exact dispositions. Stage 2 parity
compares complete protected cohorts and preserves original bytes/identities.
Stage 3 consumes explicit producer/consumer cutoffs and saved-state identities at node
boundaries. Its real run performs zero model fits and zero preparer refits. Stage 4
replay preserves that boundary, verifies complete saved outputs and native roundtrips
under both LightGBM 4.6 and 4.7, and rejects unknown families/configurations. The
synthetic graphs have no real-source input. The evaluation graph verifies the fixed
proposal and source/component provenance, validates cohorts/availability, applies saved
calibration and thresholds, recomputes full development/final metrics and preserves
the six frozen decisions. Its pure domain functions are independent of persistence;
its datasets lazily load modeling dependencies and atomically publish isolated
engineering evidence. Retained script entrypoints are thin adapters; tracking remains explicitly disabled by default. The default
remains foundation. Explicit `replay` composes verified construction/preparation,
saved-component training and frozen assessment with zero real adjustments.

## Planned Runtime Product

The approved first vertical slice is read-only:

```text
persisted, traceable result -> read-only API -> dashboard
```

The dashboard may filter and present API-supplied values but cannot write data, trigger inference, recompute scientific values, or present an evaluation procedure as operationally approved. A prototype precedes Stage 6 contract freeze. Model integration remains blocked while G5 has no approved champion.

A later write-enabled iteration may add explicit monthly input -> validation -> inference -> persistence and separate expert-feedback persistence. Feedback links to an immutable prediction identity and remains separate from the later observed epidemiological outcome. The [dashboard story](../product/stage-1/PROD-04-dashboard-master-user-story.md) owns behavior; final runtime schemas remain unfrozen. Do not introduce services, orchestration platforms, or deployment infrastructure solely to mirror the target architecture.

## Optional tracking boundary

Kedro lifecycle hooks invoke a lazily imported local MLflow client only when
`tracking: enabled` is requested. Current training/evaluation native publications
are independently verified before a parent and candidate/horizon children can finish.
The adapter stores only approved aggregate metrics, zero real-adjustment counters,
version/identity metadata and safe relative pointers. SQLite and schema-validated
lineage receipts stay in ignored local storage; logical `satlocal:` artifact URIs
avoid private absolute checkout paths. No autologging, remote service, registry,
model duplication or domain dependency on tracking is introduced. The
[security owner](../SECURITY.md#bounded-local-mlflow-tracking) defines exclusions;
the [migration owner](../operations/kedro-migration.md#optional-local-tracking--session-7--t-tracking)
owns the exact local recipe and sequential recovery limitations.


The composed replay has four namespaced stage graphs and explicit producer/consumer
bridges. Complete native parity precedes reuse; checkpoints bind source, contract,
code, environment, configuration and ancestor identities. The final atomic immutable
receipt contains audit/configuration/lineage only. Optional tracking can finish only
after that receipt and all stage payloads are verified. A separate source-free
synthetic graph connects bounded fixture training components to assessment. The
[migration owner](../operations/kedro-migration.md#composed-replay-and-restart--session-7--t-e2e)
owns sequential restart behavior and its failure boundaries; existing scientific
status and historical reproducibility limitations remain unchanged.
