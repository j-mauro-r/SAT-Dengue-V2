# EXP01 runner infrastructure handoff

This corrective delivery registers the future real `exp01` graph and a separate
`exp01_preflight` graph on PR #27. EXP01 scientific execution and formal MLflow
registration remain pending. The frozen protocol, experiment registry status,
conclusions, EXP00, EXP03, G5 `NOT_APPROVED` and champion `not_selected` retain
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
private contents. The EXP01-specific reader verifies the pinned manifest and complete payload fingerprints
only after authorization. It checks the full header/dimensions, then projects keys, raw
predictors and the controls needed for population, count and climate-coverage validation.
It removes origins after December 2024 before typing predictor values. Supplied labels,
future target metadata and channel values are not interpreted or validated; EXP01
rebuilds its own channel and targets. Whole-file hashing establishes source identity
and does not imply semantic use of discarded columns. November/December 2024 remain
available as history; target roles still end before 2025. Only keys/raw predictors and
verified provenance reach scientific preparation. No EXP00 predictions are read.
`Exp01BundleDataset` publishes immutable `result.json`, `provenance.json` and a
content-addressed manifest under `tmp/kedro-migration/exp01-runs`.
Kedro resolves catalog dataset paths to absolute paths before materialization.
The dataset accepts the exact configured relative path and its canonical absolute
equivalent under the real project root, preserving the global path restrictions.
Preflight now materializes this dataset through a real Kedro session/context,
without loading private contents or creating its output directory. After merging
this correction, generate a fresh preflight and a new human/reviewer authorization
for the resulting clean commit. The older approval is obsolete and must remain
unused until Mauricio decides its disposition.

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

Use the current-wheel runtime prepared at `tmp/exp01-runtime` with frozen
constraints. The older foundation installation retains 0.1.0 distribution metadata
and remains available for existing quality tools; its metadata must not stand in
for a properly installed 0.2.0 EXP01 runtime. A drifted `.venv` is also rejected
even when `pip check` alone finds no broken dependencies.
All required base/modeling/tracking direct pins and installed exported transitive
pins must match the frozen project/constraints. Preflight also verifies installed
package bytes against the checkout and records explicit code/runtime hashes.

```bash
export PATH="$PWD/tmp/exp01-runtime/bin:$PATH"
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
python -m sat_dengue.experiments.exp01_preflight
```

The equivalent Kedro graph is:

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
KEDRO_DISABLE_TELEMETRY=yes \
kedro run --pipelines=exp01_preflight \
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
kedro run --pipelines=exp01 \
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
2–8 GB RAM and 0.1–2 GB additional native/MLflow output. The existing source
reader must hash the roughly 1.1 GB notification file in addition to the monthly
panel and traceability inputs. Full-frontier grouped metrics may dominate runtime.
Actual class support, wall time, peak memory and storage remain unverified until
a separately authorized real run; no private benchmark was performed for this
estimate. Each annual evaluation window lacks the two distinct years required by
the frozen block bootstrap, so its interval remains unavailable under the existing
protocol. Human scientific interpretation remains necessary.


## Corrective file inventory

Created (7): `docs/operations/exp01-runner-handoff.md`;
`src/sat_dengue/datasets/exp01.py`;
`src/sat_dengue/experiments/exp01_preflight.py`;
`src/sat_dengue/experiments/exp01_runner.py`;
`src/sat_dengue/tracking/exp01.py`;
`tests/unit/test_exp01_runner.py`;
`tests/integration/test_exp01_runner_tracking.py`.

Modified (14): `conf/base/catalog.yml`; `docs/README.md`;
`docs/TESTING_GUIDE.md`; `docs/product/experiments/README.md`;
`docs/roadmap/master-plan.md`; `src/sat_dengue/config_loader.py`;
`src/sat_dengue/configuration.py`; `src/sat_dengue/experiments/exp01.py`;
`src/sat_dengue/experiments/onset.py`; `src/sat_dengue/hooks.py`;
`src/sat_dengue/pipeline_registry.py`; `src/sat_dengue/tracking/artifacts.py`;
`tests/integration/base_bootstrap.py`; `tests/unit/test_repository_bootstrap.py`.
No files were deleted. This inventory is relative to corrective baseline
`f6ee425f9ac00b1c0aeb99aced5186bdd9df3a52` and preserves earlier PR #27 work.

## Corrective validation evidence

| Gate | Result |
| --- | --- |
| Focused EXP01/configuration/bootstrap/tracking | PASS: 85 generated/public tests, DWP gate seq 14 |
| Complete public unit/contracts/tracking/permitted E2E | PASS: 705; 3 existing absent historical-output skips; 12 private tests deselected by repository policy |
| Ruff lint and format, including maintained scripts | PASS |
| Explicit mypy and maintained scripts | PASS |
| Markdown links and diff check | PASS; documentation handoff changes receive an additional owning check |
| Fresh base and modeling/tracking wheel installs | PASS: source bytes verified, all graphs registered; base foundation startup and generated extras parent/36-child probe |
| Source/base/extras/dedicated-runtime dependencies | PASS: pip checks; exact frozen dependency checks |
| Dedicated-runtime standalone/Kedro preflight | PASS: structural only, zero fits/writes; execution authorization remains pending |
| Secrets and prohibited runtime-pattern scan | PASS on 285 tracked project text files; pinned tools/UI/private data/historical notebooks excluded |
| EXP00/permanent-store preservation | PASS: four permanent-store files byte-identical; protected protocol/conclusion/data/notebook paths absent from diff |
| Independent review | R1–R7 resolved; no outstanding high or medium findings; infrastructure approval only |
| Repository/scoped corrective DWP conformance | PASS; final closure is recorded in the local journal/receipt |
| All local-plan conformance | FAIL: the two inherited PLAN_012 and legacy initial-recognition incidents remain; no historical evidence rewritten |

The individual public-suite/wheel checks completed successfully; the parent
wrapper exceeded its 600-second deadline and remains a failed attempt.
Continuation reuses those completed checks only after exact tested-tree/wheel
correspondence and frozen-runtime verification, then executes remaining gates.
Earlier metadata/backend/helper failures and their corrections remain in the local
corrective evidence. These are not scientific EXP01 runs. Remote CI observation
belongs to the current PR head rather than a claim based on earlier green runs.

## R1 raw-input admission correction

The former generic reader validated legacy target/channel columns attached to retained
late-2024 origins, allowing unused January/February 2025 target values to reject admission.
`experiments/exp01_inputs.py` now applies the existing protocol through an explicit raw
projection and compatible schema, key, calendar, population, category, missingness and
coverage validators. Full input identities are checked before and after loading. No target
columns are fabricated and no global validation is disabled. Historical `prepare_inputs`
consumers retain their default full-schema and target/channel validation.

The separate EXP03 runner also reused `prepare_inputs`. Its admission path therefore
requires its own assessment/adoption on that branch. This PR does not change that branch
or claim EXP03 is corrected. The frozen EXP01 protocol and hash, design, budgets, G5 and
champion remain unchanged. The minor standalone logging-prefix observation is out of scope.

A generated-manifest connection test materializes the real Kedro catalog (including
canonical absolute publication-path resolution), exercises authorization denial before
content reads, then uses an explicitly in-memory fixture boundary for source loading.
It calls the paired engine with controlled estimator/calibrator substitutes and publishes
an explicitly synthetic result through the real bundle dataset and isolated tracking: one
parent and 36 children. It does not invoke the real EXP01 graph, create a real approval or
reservation, access private sources, or write the permanent store. This proves connection
compatibility, not successful private scientific execution.

After merge, resume PLAN_039 without treating this correction as operational completion:
update only the installed project package from the new clean main commit using `--no-deps`,
verify unchanged dependencies and installed/source correspondence, and generate a new
no-fit preflight. Review the independent disposition and the human authorization bound to
that new commit, protocol, data and configuration. The existing runtime/receipt/approval
identities do not automatically transfer to the merged code. Mauricio runs
`kedro run --pipelines=exp01` only after the separate authorization process.
