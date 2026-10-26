# Scientific Experiment Registry

This directory is the authoritative index for planned, running and completed
scientific experiments in SAT-Dengue V2. It connects each experiment and
hypothesis to its frozen protocol, Kedro pipeline, MLflow lineage and written
conclusions.

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
7. Consumed 2025 evidence is replay-only and cannot be used for fitting,
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
