# EXP01 runner infrastructure handoff

This corrective delivery registers the future real `exp01` graph and a separate
`exp01_preflight` graph on PR #27. EXP01 scientific execution and formal MLflow
registration remain pending. The frozen protocol, experiment registry status,
conclusions, EXP00, EXP02, G5 `NOT_APPROVED` and champion `not_selected` retain
their existing identities and decisions. The protocol's implementation-status
paragraph describes its original infrastructure delivery; this engineering record
owns the subsequent runner implementation without changing the protocol hash.

## Graph and datasets

| Node | Inputs | Output and responsibility |
| --- | --- | --- |
| `exp01_preflight` | `parameters`, `exp01_sources` | `exp01_preflight_receipt`: public authorities, exact dependency pins, installed/source correspondence, catalog/graph, source stat metadata and read-only SQLite destination checks |
| `exp01_authorize_and_load` | `exp01_preflight_receipt` | `exp01_authorized_sources`: verify separate approval before any private-content read, then reuse the existing manifest/schema/preparation reader with a pre-2025 boundary |
| `exp01_execute_paired` | `exp01_authorized_sources` | `exp01_bundle`: atomically reserve science identity, reuse paired scientific functions and native family/sigmoid adapters, verify inputs again, validate and atomically publish native results, then finish aggregate-only MLflow tracking |

`Exp01SourcesDataset` is a metadata-only descriptor for the existing pinned Stage 2
manifest, construction contract, consolidated monthly panel, notification source,
label/channel traceability and municipality catalog. Its `load()` never opens
private contents. The existing Stage 3 reader verifies the pinned manifest and
its payload fingerprints only after authorization. No EXP00 predictions are read.
`Exp01BundleDataset` publishes immutable `result.json`, `provenance.json` and a
content-addressed manifest under `tmp/kedro-migration/exp01-runs`.

Both horizons require observed Y(T)=0. T+2 Y(T+1) only constructs retrospective
outcomes; it never filters operational eligibility or enters X. Unknown outcomes
stay unavailable. The fitted excess and onset arms share the evaluable role
intersection, ordered predictors, missingness, train-only preparation, cutoffs,
fixed parameters, sigmoid calibration and the complete development false-alert
budget frontier. Per-role hashes record their correspondence. Each fitted arm
retains its own probability target. No evaluation/stress result selects a budget
or model. Consumed 2025 rows are removed before typed preparation and never enter
EXP01 features, labels, fitting, calibration, selection or evaluation.

EXP00's saved predictions are explicitly incompatible with this design. A future
approved run needs 36 new model/preparer fits and 36 sigmoid fits; this delivery
performs none. The existing Stage 4 deterministic persistence function runs on the
same evaluation rows. Under the non-excess-at-T risk set it emits no alerts.
Its Brier/calibration are not applicable, and zero-alert false-alarm ratio is
unavailable. Consequently the secondary five-point guardrail cannot be declared
satisfied. This reference does not add fitted models or MLflow children.

## No-fit preflight

Use the pinned Kedro environment documented by the migration owner. A drifted
`.venv` is rejected even when `pip check` alone finds no broken dependencies.
All required base/modeling/tracking direct pins and installed exported transitive
pins must match the frozen project/constraints. Preflight also verifies installed
package bytes against the checkout and records explicit code/runtime hashes.

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
python -m sat_dengue.experiments.exp01_preflight
```

The equivalent Kedro graph is:

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
kedro run --pipeline=exp01_preflight \
  --params="profile=exp01_preflight,tracking=enabled,experiment_id=EXP01"
```

A passing preflight reports `status=structural_pass`, zero fits and MLflow writes,
and `execution_ready=false`. It does not inspect private values, establish
class support/operational latency, or certify future scientific success. Missing
sources, modified protocol/authorities, version drift, wrong catalog, unsafe or
inconsistent storage fail closed. SQLite inspection uses an immutable read-only
connection; no experiment, parent, child, artifact or database is created.

## Future authorization and execution

Mauricio and an independent reviewer must separately authorize real EXP01 for the
clean reviewed commit, frozen protocol, pinned data manifest and preflight
configuration hash. The acknowledgement must include retrospective predictor
availability and the new paired excess comparator fits. An approval is an
auditable local human record, not cryptographic identity authentication. The
runner never creates an approval record. Do not infer approval from this handoff,
a successful test, a preflight receipt or the frozen protocol's original
`real_execution_authorized=false` delivery-state field.

After that human decision, place the reviewed JSON under ignored repository-local
`tmp/` and set `SAT_DENGUE_EXP01_APPROVAL` to its relative path. The closed schema
requires `schema=exp01-execution-approval-v1`, `experiment_id=EXP01`,
`protocol_sha256`, `git_revision`, `data_version`, `configuration_sha256`,
`authority=Mauricio`, a distinct nonempty `independent_reviewer` token, and Boolean
`real_execution_authorized`, `retrospective_availability_acknowledged` and
`comparator_refit_authorized` all explicitly true. Bind the four identities to a
fresh preflight receipt from the clean final commit. No approval file is supplied
with this delivery.

Only after that separate authorization, Mauricio's exact command is:

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
kedro run --pipeline=exp01 \
  --params="profile=exp01,tracking=enabled,experiment_id=EXP01"
```

This real command was not executed. It rejects absent/stale approval before
private reads, fits or MLflow writes. The permanent store remains unchanged by
this delivery. Scientific identity reservations exclude approval metadata, so a
new approval cannot silently repeat identical science. Reservations persist on
failure; recovery needs an explicit human decision after examining the failed
run. Automatic retry/refit is intentionally unavailable.

Tracking reuses container `sat-dengue-bounded-v1`, scientific tag `EXP01`, common
hypothesis/objective tags and existing local artifact transport. One parent and
36 objective/family/horizon/window children are expected. Parent identity/purpose
is logged before computation, so failed runs retain provenance. Failures do not
invent zero fit counts. Successful native results carry actual procedure counts and validated bundle
identity. The existing security policy permits only zero synthetic adjustment
counters in MLflow; real fit/preparer/calibrator counts remain native and are
omitted from MLflow rather than replaced with zeros. Full aggregate frontiers
remain native; MLflow receives
allowlisted lineage/aggregate probability metrics and no raw rows/private paths.

## Validation and limitations

[The testing guide](../TESTING_GUIDE.md#exp01-real-runner-corrective-infrastructure)
owns the executed gate selection. The local corrective record is
`.dwp/plans/PLAN_037_exp01_real_runner`; the prior PLAN_035 evidence is preserved.
The independent review uses the vendored AI Diff Reviewer methodology and the
full corrective diff, including new files. Gate logs, first failures, corrections,
store fingerprints, preflight receipts and reviewer findings are retained there.
No EXP01 scientific result, conclusion, champion or human gate approval follows.

The unbenchmarked planning estimate is 1–4 hours, one model thread, approximately
2–8 GB RAM and less than 1 GB additional native/MLflow output. The existing source
reader must hash the roughly 1.1 GB notification file in addition to the monthly
panel and traceability inputs. Full-frontier grouped metrics may dominate runtime.
Actual class support, wall time, peak memory and storage remain unverified until
a separately authorized real run; no private benchmark was performed for this
estimate. Each annual evaluation window lacks the two distinct years required by
the frozen block bootstrap, so its interval remains unavailable under the existing
protocol. Human scientific interpretation remains necessary.
