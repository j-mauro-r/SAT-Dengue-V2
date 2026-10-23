# Stage 4 — synthetic development and frozen-component replay

G2/G3 remain approved with documented limits under DEC-135. G4 retains the exact
protocol accepted under DEC-132. G5 remains `NOT_APPROVED`, champion
`not_selected` (DEC-134). The consumed 2025 block cannot train, fit preparers,
search, tune or select. Migration supplies engineering equivalence, not improved
accuracy, prospective validity or new scientific approval.

## Current execution

The unchanged [model contract](model_engineering_contract_v1.json) owns families,
parameters, budgets, seed, selection rules and metric definitions. Domain functions
live in [`model_training`](../../../src/sat_dengue/model_training/__init__.py);
[`sat_dengue.metrics`](../../../src/sat_dengue/metrics.py) is the single metric owner.
Kedro owns dependencies; dataset adapters own verified I/O and immutable publication.

From the repository root, use the isolated migration runtime:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=training_replay --params=profile=training_replay
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=training_synthetic --params=profile=training_synthetic
```

The routes are disjoint. `training_replay` loads explicitly identified native
components and predicts without fitting or searching. Its loader and computation
execute under a guard rejecting `fit`, `_fit`, native `train` and search calls.
It never falls back to fitting when an artifact is missing, stale or corrupt.
The default remains foundation; `kedro run --pipeline=replay` is the explicit composed E2E.

`training_synthetic` accepts only configuration inputs. It generates the entire
small deterministic fixture internally and rejects changed/foreign fixture data.
It exercises the approved family grids and existing two-inner-fold selection on
synthetic data, followed by outer fitting, prediction and native roundtrip. All
parameters, tie rules, seed 42 and one-thread limits come from the existing
contract. It cannot accept private source paths or real training frames.

Registered families are XGBoost, LightGBM and Bernoulli/logit GAM. Native formats
remain XGBoost JSON, LightGBM text and numeric GAM coefficient/BSpline JSON; no
pickle or global module-name alias is introduced. Unsupported families, parameters,
profiles and selected experiments fail closed. Original controlled XGBoost
without-climate/without-zone components are replayed; no new real ablation runs.

Catalog entries `configuration_inputs`, `parameters`, `training_sources`,
`resolved_configuration` and `training_bundle` have explicit roles. Both routes
publish/reload the resolved snapshot before computation. Engineering outputs use
new identities under `tmp/kedro-migration/training-runs/<bundle-id>/`, with separate
predictions, metrics, serialized synthetic components, audit and provenance.
Publication is atomic, immutable and refuses replacement; no implicit `latest`.
Original manifests and model/preparer bytes are never repaired or overwritten.

## Preserved scientific behavior

Persistence projects current `zona_canal_t == EXCESO`; unknown/missing zones remain
non-evaluable. Train prevalence uses only Y_train for the same horizon/window.
Persistence is a deterministic score, not a calibrated probability; its Brier is
non-applicable. Event metrics for probabilistic outputs remain unavailable without
a declared threshold policy.

AP is non-interpolated with tied scores entering together. Empty/single-class or
missing-prediction populations remain non-evaluable; no complete-case subset may
improve ranking. Brier, fixed 1e-12 absolute / zero relative selection tie tolerance,
within-family lexicographic simplicity and equal weight across all four windows per
horizon are unchanged. Missing eligible windows are explicitly non-evaluable.

Onset means excess at target S with no excess at exactly S−1. Retrospective context
stays outside X, fitting and selection. Missing predictions cannot shrink the true
onset denominator. FAR is false alerts / emitted alerts; zero denominators remain
unavailable, and emitting no alerts cannot qualify a policy. No scientific channel,
label, feature, cohort, cutoff, rule, seed, policy or tolerance changes.

The eight Stage 3 windows and ordered saved-preparer schemas are preserved. The
active development chain contains 40 saved components across three families and two
controlled ablations. Component replay also checks six saved frozen procedures over
5,472 historical raw candidate predictions and 1,824 persistence rows. Consumed 2025
is consulted only for frozen inference equivalence, never adjustment. This task does
not migrate or rerun calibration, threshold selection or final decision evaluation.
The pre-existing historical replay gate separately verifies retained final outputs.

Frozen LightGBM 4.6 evidence remains separate from the accepted current 4.7 runtime.
Both runtimes require saved-component compatibility evidence. Cross-version equality
is never inferred from a successful library import. The 13 historical source
exceptions and 17 KEEP / UNVERIFIED bundles remain closed and excluded from
engineering equivalence; full historical reproducibility is not established.

## Historical evidence, compatibility and validation

Notebooks [05](../../../notebooks/05_baseline_models.ipynb) and
[06](../../../notebooks/06_candidate_models.ipynb), original bundles and dated
scientific records remain untouched. The original version of this active README,
including its 2026-10-20 corrective tables, is recoverable from Git revision
`4e9c47025c73297ca066a8f2874bb94046fc7e4b` through the closed preservation mapping.
Those earlier statements do not override later DEC-132/134/135 decisions.

The replaced model-training and metric script facades have direct package consumers.
Their final absence and exact Git recovery identities are verified by the
[cleanup correspondence](../../operations/kedro-cleanup-identities.json).
Notebooks 05/06 remain frozen historical identity evidence, never production entrypoints. Real legacy bundle APIs
load pinned saved artifacts without rebuilding or fitting; synthetic fixture
orchestration remains for existing tests. The single native loader documents format
compatibility and verifies identities without modifying global module bindings.

The [migration owner](../../operations/kedro-migration.md#stage-4-execution--session-5)
records original/current identities and dispositions. The
[testing guide](../../TESTING_GUIDE.md#kedro-stage-4-model-migration-session-5)
owns commands, source-to-test mapping and mandatory full private parity. Session 5 remains historical evidence. Current execution uses Kedro; no notebook
execution, new real fits, scientific selection or publication is authorized.
