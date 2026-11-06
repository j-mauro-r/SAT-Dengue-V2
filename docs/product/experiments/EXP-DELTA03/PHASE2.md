# Phase 2 implementation and synthetic validation

## Authority and current boundary

The [training contract](training-contract.json) owns the approved model, calibration,
selection budget and uncertainty settings. Mauricio approved the full bundled
proposal under [Phase 2 authority](PHASE2-AUTHORIZATION.md):
`APPROVED_FOR_PHASE2_IMPLEMENTATION`. Execution remains separately gated. The original
[Phase 1 handoff](PHASE1.md), labels, roles and matrix bytes remain unchanged.
Execution remains `not_authorized`; Phase 3, real training, deployment and G5
approval remain outside this implementation.

The original bundle contains national training but Meta/Tolima calibration,
selection and evaluation. National evaluation is approved for separate additive
annex preparation only; executable national inputs remain explicitly pending. It must preserve exact original regional key/label/X
correspondence and have its own complete national cohort identity. It cannot
reclassify existing training roles or present regional metrics as national.
A distinct pinned H5 excess/comparator/exposure join is also required: onset
negatives do not establish absence of excess.

## Implemented consumers

`exp_delta03_preflight` verifies public contracts and immutable bundle hashes,
parses only JSON matrix metadata and derives counts. It never parses real table
rows, reserves a scientific execution or fits a model.

`exp_delta03_synthetic` adds a full generated-only execution to the preserved
Phase 1 zero-fit probe. It traverses contract loading, admission, plan building,
model fitting, calibration, selection, prediction/reload, evaluation, paired
comparison, protected publication and isolated tracking. Generated national
annexes and arbitrary generated frozen-comparator controls exercise these paths;
they are not scientific evidence or reproductions of private V2 scores.

`exp_delta03` has the same learning responsibilities and requires a separate
manual Phase 3 grant before private row loading. Contract freeze alone is
insufficient. The [Phase 3 handoff](PHASE3-HANDOFF.md) owns its operational gates.

All variants, roles, predictor order, supported cells, comparison links and run
counts derive from verified Phase 1 metadata. Four unsupported 2024 surface-water
cells remain explicit. Transfer excludes Meta/Tolima from every learned role;
main models retain their approved national training population. NDVI references
remain tied to the appropriate training population. No imputation or HPO is added.

## Native artifacts and tracking

The [artifact catalogue](artifact-schemas.json) provides lightweight required-field
and header validation, supplemented by semantic domain guards. It is consumed before native
publication and completed-bundle reuse. Models use UBJ plus metadata; calibrators,
policies, metrics, comparisons, columns, provenance and the execution plan use
JSON. Protected prediction and cohort tables use CSV. Byte hashes and the
execution identity bind every native member to protocol, matrix bundle, commit,
code/configuration, parameters, resource limits and runtime versions. Native
reload must reproduce raw/calibrated probabilities and alerts exactly.

Publication uses a locked execution reservation, immutable stage checkpoints,
explicit incomplete states and atomic visibility. An interrupted fit without a
verified checkpoint requires inspection; resume never silently repeats an
unknown adjustment. Completed publications cannot be replaced. Model/calibrator
attempt caps are derived from the admitted plan. The wall budget is checked at
node/loop boundaries and around fits, before publication and tracking; it is a
cooperative execution deadline, not a process-killing CPU quota.

MLflow receives one parent and dynamically derived children only after native
verification. Stored tags, parameters, aggregate metrics and lineage are checked
on reuse. Detailed identifiable rows and predictions stay in protected native
storage. Synthetic tracking always uses an isolated ignored namespace under
`tmp/exp-delta03-phase2/synthetic`, independent of the permanent-store environment.

## Interpretation

Onset, excess, row and episode outcomes remain distinct. Undefined metrics carry
explicit non-evaluable statuses. Monitored exposure comes from a separate unique
calendar, while eligible rows/12 define the experimental selection denominator.
CHANNEL and PERSISTENCE retain deterministic alerts and have no invented
probabilities. Frozen comparator tables must have exactly paired keys/outcomes;
no convenient population intersection is allowed. A frozen comparator's original
alert policy is not asserted to share a new experimental budget.

Paired contrasts report absolute/relative differences and gained/lost/shared
onsets. Development years and consumed 2024 stress are reported separately.
The approved uncertainty method shares municipality and connected calendar-year
block draws across arms and preserves episodes spanning years. Insufficient
independent blocks remain non-evaluable; no independent-row fallback is used.
Missing inherited transmission-profile mapping is explicitly non-evaluable and
never filters the primary cohort. Ablations support descriptive predictive
comparisons only, without causal, operational or champion claims.

## Validation status

The development Kedro CLI and observed PLAN_056 gate 32 complete all 12 generated
nodes, native publication and temporary MLflow. Three focused integration tests
pass, including exact reload/repeat with zero new adjustments and no duplicate
runs, full annex admission and unauthorized real-graph refusal. Refreshed contract,
evaluation and publication gates pass; changed-file Ruff/format/mypy pass. The
independent review resolved every critical/high/medium finding in its focused
passes. Final range review and remote final-head CI are recorded in PLAN_056 and
PR #78; consult their current evidence rather than treating this document as a
CI receipt. Final closure requires the bounded annex verification, clean independent review
and seven passing final-head checks; the DWP delivery gate owns that observation.

## Approved scientific freeze and preserved proposal

Mauricio approved the following complete proposal on 2026-11-06. Its prior
PROPOSED revision remains preserved at `3957bce`; the recorded approval changes
implementation maturity only. The approved decision is:

1. Preserve the complete Phase 1 core and authorize preparation of a **separate
   additive national evaluation/excess/comparator/monitored-calendar annex**.
   Do not change historical V2 labels or roles. Publish new annex identities
   separately, with exact regional correspondence, without any real fit.
2. Retain the DESIGN core: 80 trees, depth 2, learning rate 0.05, histogram
   trees, seed 1729, one CPU thread and native missing values. Freeze all other
   explicit settings in the [training contract](training-contract.json), including
   max-bin 128, minimum-child-weight 5, L1 0/L2 1, full row/column sampling,
   base-score 0.5 and no HPO.
3. Use V2's pooled regularized intercept, penalty 1, separately for each
   admitted cell/horizon. Minimum one observation per class is an admission
   guard, not a robustness claim. JSON-only Phase 1 metadata show the smallest
   calibration supports are 45 positives and 256 negatives; no evaluation
   scores were inspected to propose the method.
4. Freeze experimental budget **B=1 false onset alert per eligible
   municipality-year**, with eligible selection rows/12, floor rounding,
   whole-score ties and the explicit lexicographic policy in the contract.
   No-alert uses a null threshold; no selection positives is non-evaluable.
   This carries the V2 matched-cohort experimental convention into the new
   comparison, approved for implementation; it is not measured operational capacity.
   The academic five-percentage-point excess-FAR margin is a different rule.
5. Use paired municipality and episode-preserving connected calendar-year block
   resampling: 1,000 draws, 95% intervals, seed 1729, at least two municipalities
   and two connected temporal blocks, at least 80% valid draws. Keep 2024
   separate. Episode connections may collapse all development years to one
   block; then uncertainty is explicitly non-evaluable, with no IID fallback.
   Report descriptive estimates only; no formal superiority/materiality,
   champion or deployment conclusion is authorized.

This decision freezes design choices and permits bounded annex preparation only.
No Phase 3, real model/calibrator fit, scientific prediction, permanent tracking,
G5/champion decision or merge is authorized.

## Separate annex preparation

The [annex record](ANNEX.md) and [inspectable inventory](ANNEX-PREPARATION.json)
identify an immutable protected publication with national primary eligible keys,
frozen onset labels and an independently observed monitored calendar. All eight
horizon/year slices preserve exact Meta/Tolima evaluation key/label identities.
The annex copies existing eligibility/labels; no Phase 1 matrix or role changes.

There are 77,094 eligible cohort rows and 103,224 observed calendar rows across
the eight slices. These count slice membership, not distinct people or unique
municipality-months across horizons. Exposure is reported separately per slice.
Source manifests and payload bytes for excess/comparators are hash-verified;
score/prediction rows are never parsed. No national model-input matrices, new
predictions or comparator-policy adjustment are created by this preparation.
National per-cell X/coverage, complete excess/episode joins and exact frozen
comparator joins remain explicit pending inputs before any Phase 3 proposal.
This bounded preparation is verified; the executable annex is not ready.

Counts derive from the immutable matrix descriptor: 112 descriptors, 108
supported future model/calibrator cells, four unsupported water2024 descriptors,
78 paired contrasts and 109 future tracking runs (one parent plus 108 children).
No real model, calibrator or tracking run was created.
