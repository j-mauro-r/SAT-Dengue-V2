# Scientific Experiment Registry

[EXP-DELTA03 — Phase 3 manual operational preparation](EXP-DELTA03/PHASE3.md)
starts from merged PR78/e266b9c under PLAN_057. Existing Phase 1/2 architecture and
scientific settings are preserved; PLAN056 remains recorded7/8 without invented
CI evidence. Complete executable input connections, an isolated installed wheel
and independent no-fit admission prepare Mauricio's manual command. The agent
does not run the experiment. No real results, G5/champion or deployment follow.

[EXP-DELTA03 — approved retrospective Phase 1 preparation](EXP-DELTA03/PHASE1.md)
records source reconciliation, exact historical V2 H5/cohort preservation and
reproducible no-fit Kedro matrices. [Proposal A approval](EXP-DELTA03/PHASE1-AUTHORIZATION.md)
permits consolidated retrospective snapshots and four separate MODIS fractions;
it does not prove operational PIT availability or deployment. The design/protocol
and modeling matrix are approved for Phase 2 implementation only; predictive
execution is not_authorized.
Water uses genuine observations through2021 only;2024 stress stays separate and
2025 excluded. Zero training/calibration/permanent MLflow; G5 NOT_APPROVED,
champion not_selected. [Phase 2 implementation](EXP-DELTA03/PHASE2.md) is now
explicitly authorized for generated-only validation under PLAN_056. Mauricio approved the full [scientific freeze](EXP-DELTA03/PHASE2-AUTHORIZATION.md)
and separate [annex preparation](EXP-DELTA03/ANNEX.md); pending executable inputs
remain explicit. Real
execution, Phase 3, permanent MLflow and merge remain unauthorized.

[EXP-DELTA02-R1 — fixed-MGN spatial candidate `NOT_SUPPORTED`](EXP-DELTA02-R1/README.md)
is the independently authorized revision that treats DANE MGN 2018 as one
fixed retrospective approximation. The sole G0_OFF-plus-neighbor feature gains
one onset and seven false excess alerts on the frozen T+1 cohort; pooled A/B
pass but C fails. The byte-identical private publication and aggregate reports
preserve honest 81.9% feature missingness. This result does not rewrite the
original EXP-DELTA02 closure, promote a candidate, change G5/champion, or
authorize another experiment.

[EXP-DELTA02 — spatial feasibility `NOT_EVALUABLE`](EXP-DELTA02/README.md) closes
the explicitly authorized T+1 neighbor-signal hypothesis at its geography gate.
Three retrieved official DANE municipal archives expose nine unresolved changes
in positive-boundary membership affecting six target municipalities. Counts and
target codes are covered, but historical spatial correspondence is not admitted.
Execution is `COMPLETED_WITH_LIMITATIONS`; no feature, candidate or model fit was
produced. The frozen protocol, source identities and reproducible stop evidence
are separate from previous experiments. No technical model/pipeline registration,
new experiment family, G5 approval or champion selection follows.

[EDA-EXP01 — `COMPLETED_WITH_LIMITATIONS`](EDA-EXP01/README.md) is scientifically
closed as a read-only, seven-chapter analysis of identified results. Its climate
chapter concludes `INSUFFICIENT_EVIDENCE`. The
[closure](EDA-EXP01/CONCLUSIONS.md#scientific-closure--eda-exp01) preserves eight
original and five climate findings, lessons and open hypotheses without authorizing
a successor experiment, adopting a policy/model or changing scientific gates.
PR #74 integration remains separate from scientific closure. No other experiment
state or closed registry schema is changed by this entry.

The separate [EXP-BETA01 V2 national-transfer experiment](EXP-BETA01-V2/README.md)
is explicitly authorized for G1 without climate. Its frozen protocol preserves
V1's regional evaluation cohorts, model configuration and chronological roles;
national observations enter training only. V1 results and later BETA experiments
remain unchanged.

EXP01 is prioritized experiment 1. Prioritized experiment 2 (label sensitivity
5/7/9) remains pending and is outside EXP03. EXP03 is prioritized experiment 3:
[selective history/channel/climate ablation](EXP03_feature_ablation/DESIGN.md),
with sixteen canonical predictor sets, four primary and twelve secondary ablations,
two bounded T+2 objective controls, 408 fit cells and 102 terminal cells. Its real execution and
scientific conclusions remain pending independent authorization.

EXP03.1 is the registered follow-up [recent endemic-channel trajectory experiment](EXP03.1_add_pass_info/DESIGN.md). Its technical registry identifier is `EXP031` because the closed registry requires `EXP` followed by digits; `EXP03.1` remains the visible scientific identifier and `exp03_1` the Python/pipeline identifier. Its infrastructure compares M00/M01/M02 under the inherited EXP03 budget and temporal design. Scientific execution remains unauthorized.

This directory is the authoritative index for planned, running and completed
scientific experiments in SAT-Dengue V2. It connects each experiment and
hypothesis to its frozen protocol, Kedro pipeline, MLflow lineage and written
conclusions.

EXP04's [independent technical implementation](EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/IMPLEMENTATION.md)
provides read-only readiness and generated functional execution for temporal
calibration/threshold transport. Its mandatory EXP03.1 M00 baseline remains
`BLOCKED_BASELINE`; no EXP04 scientific evaluation or MLflow registration has
occurred. The technical protocol does not constitute a scientific protocol freeze.

## Rules

1. Register the experiment before its first scientific execution.
2. Freeze `protocol.json` before the first formal execution. It is immutable
   afterward. Later changes require a new registered experiment/protocol version
   and an explicit reason; never rewrite a protocol that produced a formal run.
3. Use the same `experiment_id`, `experiment_slug` and `hypothesis_id` in the
   registry, protocol, Kedro configuration, MLflow and conclusions.
4. Store only aggregate, allowlisted metadata in MLflow. Native scientific
   artifacts remain authoritative.
5. Write `CONCLUSIONS.md` after execution, including negative or inconclusive
   outcomes and material limitations.
6. Historical baselines retain their original decisions. Retrospective MLflow
   registration does not turn replay into a new experiment or approve a model.
7. Consumed 2025 is replay-only for EXP00 and inference-only through EXP03’s
   separately authorized frozen-artifact benchmark. It cannot be used for fitting,
   calibration, tuning, threshold selection or model selection.

## Registered experiments

The machine-readable registry is [`experiment-registry.yml`](experiment-registry.yml).
The first entry, `EXP00`, represents the last scientific result produced before
the Kedro migration and is the comparison baseline for future experiments.

## Register and freeze a protocol

Add a unique `EXP` identifier (2–6 digits) to `experiment-registry.yml` and a
`protocol.json` below this directory. Registry entries use the closed v1 schema;
unknown keys, duplicate identifiers/document keys, shared protocol paths, absolute
paths, parent traversal and symlinks are rejected. Register the matching pipeline,
experiment slug, hypothesis and experiment type. Add each new directory to the live
`directories` list in `docs/operations/repository-disposition.json`, preserving all
historical file mappings and identities. Protocol identity fields and
`mlflow.required_conceptual_tags` must agree with the registry. The `mlflow`
object has exactly two fields: `experiment_name` and `required_conceptual_tags`.
The name must equal the shared technical constant `MLFLOW_EXPERIMENT_NAME`
(`sat-dengue-bounded-v1`) used by the resolver and tracker; CLI cannot override it.
Unknown fields, missing fields and other container names are rejected.

Mutable registration state belongs only in `experiment-registry.yml` under
`mlflow_registration`. The actual run ID, registration date, evidence and conclusion
belong in `CONCLUSIONS.md`. Never modify the protocol to mark execution complete;
registration status and implementation notes are not protocol fields.

Before EXP00's first formal execution, the user authorized removal of its mutable
registration status and obsolete implementation note in PLAN_032. The expected
hash was recalculated with `sat_dengue.configuration.canonical_bytes`; scientific
content and all conceptual tags are unchanged. Formal registration remains pending.

Compute `protocol_sha256` from UTF-8 JSON with sorted keys, compact separators,
Unicode preserved, finite numbers only and one trailing newline. Store that SHA-256
in the registry before running. Whitespace changes do not change the canonical
identity; any content change does. Keep protocols that produced results immutable:
create a new experiment ID and protocol directory, explain its relationship and
reason in conclusions, and retain the old entry. Never update an old expected hash
to bypass verification. Git review protects history across tracking stores.

`experiment_id` is optional with tracking disabled and for isolated synthetic
fixtures; it is required for real scientific tracking. Supplied IDs are validated
even with tracking disabled. Configuration accepts only `profile`, `tracking` and
`experiment_id`. EXP00's registration remains `pending`; implementation does not
change its historical conclusions or authorize scientific adjustments.

## MLflow representation and retries

Every registered parent and candidate/horizon child receives this exact conceptual
allowlist: `experiment_id`, `experiment_slug`, `hypothesis_id`, `objective_slug`,
`experiment_type`, `target_definition`, `protocol_sha256`. Values come from the
verified protocol, never from arbitrary runtime tags. IDs, lowercase slugs and
SHA-256 values have bounded formats; credential-shaped strings, free text and
private paths are rejected. Narrative objectives and hypotheses are not uploaded.
Existing technical lineage remains available: pipeline, Git, bundle/manifest,
code/data/configuration/environment identities, cohort/window, family/horizon,
scientific decision, G5 and champion.

Parent names use `<experiment_id>:<experiment_slug>:<execution_hash_prefix>`;
children use `<experiment_id>:<family>:t<horizon>:<window>`. MLflow run UUIDs remain
the unique identities, even when display names coincide. The existing technical
MLflow experiment container remains `sat-dengue-bounded-v1`; the scientific
`experiment_id` is a tag and is distinct from MLflow's numeric container ID.

Within each persistent local store, the first registration pins the protocol hash.
A later edit to both protocol and registry cannot silently reuse that experiment
ID. Use the same persistent store for formal registration; a new store cannot
independently know another store's history. Git review and retained protocol
entries protect cross-store provenance. Synthetic fixtures may omit an ID and do
not count as formal registration.

Retries match scientific ID, protocol hash, bundle ID and pipeline. Lookup and
success publication are serialized by a local advisory file lock. A verified
existing success is returned; the new attempt becomes `KILLED` with
`status=duplicate_verified` and `duplicate_of=<existing UUID>`. Failed/aborted
attempts do not count as successful registration. Local tracking assumes trusted
repository/store ownership; it is not a remote multi-user tracking service.

### EXP01 paired-target lineage

EXP01's registered scientific pipeline identity is exp01; its only executable
pipeline in the infrastructure PR is exp01_synthetic. That source-free probe
uses generated rows, verifies the frozen 36-child shape (objective × family ×
horizon × three synthetic windows), and records no synthetic metric values. Its
parent records protocol, commit, data, configuration, code and typed-receipt
hashes, a generated-only cohort, evidence type and zero real-fit counters. Each
child records only objective, family, horizon, window, seed, cohort and synthetic
evidence type. No predictions, raw inputs, paths or scientific artifacts are
logged.

Retries are keyed by the immutable parent projection and all 36 child identities.
A verified repeat returns the original parent and records the attempt as
duplicate_verified. The official local store remains
tmp/kedro-migration/replay-mlflow; tests use a separate UUID temporary store.
The future real exp01 invocation requires a separately reviewed runner and
authorization bound to the frozen protocol, commit and data identities. Enabling
the synthetic profile never authorizes that run.

## Formal EXP00 registration — pending

The implementation is authorized. Formal execution remains pending by the user's
explicit decision. The following command is for Mauricio to run later from the
repository root in the documented Kedro environment; it was **not executed** as
part of this implementation:

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
kedro run --pipeline=replay \
  --params="tracking=enabled,experiment_id=EXP00"
```

After a successful verified registration, update `CONCLUSIONS.md` with the actual
returned parent run UUID, protocol hash, bundle ID, Git commit, registration date,
validation evidence, negative results and limitations. Update the registry's
registration status only then. Do not invent a run ID or change scientific results.
For EXP00, G5 remains `NOT_APPROVED`, champion `not_selected`, all six candidate
procedures `does_not_meet`, and 2025 remains consumed and replay-only.


## EXP01 corrective runner infrastructure

[Runner handoff](../../operations/exp01-runner-handoff.md) owns the later `exp01`
and `exp01_preflight` implementation, approval schema and exact future command.
The frozen protocol and its canonical hash remain unchanged. Its original
implementation-status notes are historical delivery metadata; they do not grant
real execution. Scientific execution/registration and conclusions stay pending.

EXP03 protocol 2.0.1 fixes the primary experimental comparison budget at 1.0 false
onset alert per monitored municipality-year before execution. See the
[decision and historical identity](EXP03_feature_ablation/DESIGN.md#primary-budget-decision--2026-10-27).
Execution still requires separate operational preparation and authorization.

## EXP-BETA01

The [Phase 2 implementation and local entry acceptance](EXP-BETA/PHASE2_IMPLEMENTATION.md)
and [retrospective results](EXP-BETA/RESULTS.md) supersede the local missing-input
blocker while retaining the [original Cloud entry-gate record](EXP-BETA/PHASE2.md).
Code and aggregate reports are versioned; private inputs and native publications
remain local. Updating the branch does not provision data in Cloud.

## EXP-BETA02

The independent [count-forecasting implementation](EXP-BETA02/README.md) and
[frozen protocol](EXP-BETA02/protocol.json) own Phase 3. Direct marginal T+2
forecasts do not supply a joint onset probability. This entry does not authorize
Phase 4 or declare any scientific model superior.
The [retrospective results](EXP-BETA02/RESULTS.md) reject the fixed marginal NB2
approach under joint sensitivity/load controls; R0 remains the primary reference.

## EXP-BETA03 and integral closure

The separately authorized [frozen-score policy implementation](EXP-BETA03/README.md)
and [real results](EXP-BETA03/RESULTS.md) complete the bounded fourth phase without
new estimator fits. The [consolidated conclusions and compliance matrix](EXP-BETA/CONCLUSIONS.md)
close the program as COMPLETED_WITH_LIMITATIONS. Neither global nor supported
department thresholds satisfy the joint controls consistently. G5 remains
NOT_APPROVED and champion not_selected; PR #67 still requires Mauricio's review.
