# Testing and Validation Guide

## Validation Policy

Validation is mapped by touched surface and reported using explicit evidence states.

Evidence states:

- PASS
- FAIL
- BLOCKED
- UNVERIFIED

## Foundation Gate Set

### Prerequisite

- `python -m pip install --upgrade pip && pip install -e ".[dev]"`

### Full gate (required before merge)

- `bash .agents/skills/deepworkplan/verify/conformance.sh`
- `ruff check src tests`
- `ruff format --check src tests`
- `mypy src tests`
- `pytest tests/unit -v`

### Security and policy scans (required)

- PITAGORAS exclusion scan:
  - `grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp --exclude-dir=.github --include='*.py' --include='*.json' --include='*.toml' --include='*.sh' || true`
- Secret pattern scan:
  - `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true`

### Documentation consistency checks (required)

- `python3 scripts/check_markdown_links.py`

## Surface-to-Gate Mapping

- `docs/**`, `AGENTS.md`, `.github/**` changes:
  - run full gate set above.
- `.agents/**` and DWP governance changes:
  - full gate set + DWP conformance is mandatory.
- Maintained Python source/tests changes:
  - full gate set plus scope-specific tests as required.

## Escalation Rule

If test mapping is ambiguous, run the full gate set.

## Scoped Commands, Mapping, Fallback (Documentation Standard 3.4)

Scoped commands:

- `git status --short --branch`
- `find docs -type f -name '*.md' | sort`
- `test -f docs/governance/ai-developer-first.md && echo OK || echo MISSING`

Mapping rule:

- Use scoped commands for fast local inspection.
- Use the full gate set for merge readiness and any material change.

Fallback rule:

- When command mapping is uncertain, default to the full gate set.

## Stage 2 data integrity and retired experimental EDA

The [experimental EDA](archive/experimental-eda/README.md) was retired on 2026-10-19. Its notebooks, reports and pending rerun instructions are historical. Do not run the old panel/analysis/rules phases as the default Stage 2 workflow. New analysis requires a new bounded task and current acceptance criteria; retirement does not approve scientific outputs or close G2.

Keep all existing tests enabled. Synthetic regressions (`.venv/bin/python -m pytest tests/unit/test_stage2_panel_review.py -q`) run without private snapshots and preserve independent-join, missingness, geography, non-swap and calendar-adjacent safeguards. The three tests against ignored historical monthly-association outputs remain artifact-consistency checks; their passing status does not make those results current analytical evidence. The historical analytical scripts stay at their import paths with deprecation docstrings and unchanged logic because tests and local historical validators depend on them.

Active data-integrity safeguards: `.venv/bin/python -m pytest tests/unit/test_january_2020_climate_incorporation.py tests/unit/test_stage2_manifest_traceability.py -q`. These verify incorporation/traceability behavior on test fixtures; they do not download or reintegrate source data. Run the full unit suite, Ruff checks, `mypy src tests` and `scripts/check_markdown_links.py` under the foundation gate policy above. Also lint/format any touched Python script.

For this archival migration, local PLAN_012 validates the path/hash manifest, byte-identical notebooks, restricted report transformations, unchanged script logic, original data/evidence hashes and preserved historical plan records. It is a one-time migration check, not a new recurring scientific gate. New DWP work must pass scoped conformance; report pre-existing legacy-plan global failures separately without rewriting their records or weakening validation.

## Clean-checkout CI installation

The project installs the used `sat_dengue` package from `src/` only. The wheel
excludes data, notebooks and external configuration. Install with `.[dev,modeling]`
for synthetic CI; the complete reproducible local environment uses
`python -m pip install -r requirements-dev.txt`. The generated constraints derive
from `pyproject.toml`; see the migration record for their regeneration recipe.

Validate packaging in a repository-local isolated environment: install the package,
run the full unit suite plus configuration contracts, build a wheel with
`pip wheel --no-deps .` into ignored scratch, inspect its members, install that
wheel into another clean environment, run `pip check` and invoke
`KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=foundation` from the repository
root. Verify a new content-hashed read-only snapshot and no data writes. Keep
private data outside CI. An installed wheel still uses the repository's external
configuration and approved JSON authorities.

## Historical preparation milestones

Milestones 1–3 and notebook 04 remain preserved dated evidence. Their original
commands and receipts describe historical execution. Current preparation commands,
source-to-test mapping and mandatory real parity are owned by
[Kedro Stage 3 migration](#kedro-stage-3-preparation-migration-session-4).
Existing feature, temporal, native-category and atomic-publication regression tests
remain enabled. Do not execute notebooks or refit real preparers to refresh old
identities. The original baseline and all native scientific bundles remain immutable.

## Stage 4 shared references (delivery 1)

Stage 4 delivery 1 maps `scripts/model_training/**`, notebook 05 and
`docs/product/stage-4/model_engineering_contract_v1.json` to bounded reference
execution only. This surface runs persistence and train-prevalence references
over verified Stage 3 artifacts; it does not train XGBoost, LightGBM or GAM.

Use at least the following checks:

```bash
.venv/bin/python -m pytest tests/unit/test_model_training.py -q
.venv/bin/python -m ruff check scripts/model_training tests/unit/test_model_training.py
.venv/bin/python -m mypy --explicit-package-bases scripts/model_training tests/unit/test_model_training.py
.venv/bin/python -m scripts.model_training.execution --execute
.venv/bin/python -m scripts.model_training.execution --verify
.venv/bin/python -m scripts.model_training.notebook_execution --execute
.venv/bin/python -m scripts.model_training.notebook_execution --verify
.venv/bin/python scripts/check_markdown_links.py
```

Reference metrics must keep non-evaluable states explicit when denominators or
class support are missing. Probabilistic references must not emit event alert
metrics unless a threshold policy is declared by contract. Artifacts are local
only under `artifacts/model_training/` and must use immutable identity reuse.


### Stage 4 metric correction

`tests/unit/test_model_metrics.py` supplies independent expected AP fractions for
constant/partial/binary ties and permutations, perfect ranking, unavailable/invalid
inputs, exact calendar predecessor lookup (including the first validation month),
municipality isolation and T+1/T+2 differences. Its integration fixture verifies
source hashes, keyed context, independent dictionary/calendar event counts and
prediction invariance under changed retrospective evaluation context.

Run it with `test_model_training.py`, the full foundation suite and Ruff/mypy on
`scripts/model_training`. Execute notebook 05 in a fresh kernel and verify its
receipt using the separate `--execute` and `--verify` commands above. Correction
evidence must compare old/new metrics while preserving old artifacts, prediction
bytes, Stage 3 cohort/manifests and original scientific source hashes. No numeric
historical diagnostic may be imposed on the regenerated outputs. Evaluate
context in `evaluation_context.csv` only; never feed it into X or fit/selection.

PLAN_021 is a corrective audit of previously accredited PLAN_020 results; the
latter's contract, journals and approval remain untouched historical evidence.


## Stage 4 XGBoost candidate (delivery 2)

`test_xgboost_candidate.py` maps adapter, nested selection, candidate persistence
and notebook06 orchestration to synthetic temporal-key expectations, fresh
inner-only vocabulary, forbidden target/event controls, explicit missing history,
approved tie rules, bounded search, native inference roundtrip and a real
orchestration perturbation test: changing external labels/features/categories
cannot change the fitted model, preparation or selected configuration. Input,
configuration and code changes invalidate reuse; payload corruption fails closed.

Install `requirements-modeling.txt` alongside `.[dev]` in local/CI environments.
The separate pinned file avoids invalidating Stage3's fingerprinted pyproject.
Run all unit tests, Ruff/format on tests and model_training, mypy on tests and
explicit-package-bases model_training, Markdown links and scoped DWP conformance.
Run notebook06 with `python -m scripts.model_training.candidate_notebook --execute`
from the repository environment, followed separately by `--verify`. The latter
checks current identity and native inference without refitting. Refresh and
verify notebook05 when shared code/config fingerprints change. All cells of
both notebooks must be code. Preserve prior immutable artifacts and03/04 bytes.

Real-data evidence checks all eight cohorts, declared inner cutoffs/observable
labels,104fit budget, complete AP/Brier support, pending threshold metrics,
preparation/model roundtrips and equal-weight horizon comparisons. Bounded
runtime and resubstitution/calibration/territorial diagnostics do not approve a
scientific gate or authorize external-validation tuning.


## Stage4 families and ablations (delivery3)

`test_candidate_families.py` covers LightGBM/GAM safe roundtrips, explicit
missing/unknown categories, forbidden controls, internal-only vocabulary and
GAM knots, binary non-evaluability, independent library spline agreement and
removal invariance of all ablated values/encodings. The existing orchestration
perturbation/reuse/corruption test now runs for all three families. Run both
family and XGBoost tests plus the full foundation gates and lint/type checks
for model_training. Fresh-kernel notebooks05 and06 must verify their current
receipts. PLAN023 audits all40 fitted outer models, shared cohorts, inner
boundaries,264-fit budget, unchanged scientific sources/prior artifacts,
fixed-parameter ablations and all four metric records including territorial
non-evaluability. Scientific acceptance, calibration and thresholds remain open.


## Stage 5 calibration and temporal thresholds (delivery 1)

Stage 5 delivery 1 maps `scripts/model_evaluation/**`, notebook 07,
`tests/unit/test_model_evaluation.py`, and
`docs/product/stage-5/probability_calibration_thresholds_contract_v1.json` to
bounded calibration/threshold development over verified Stage 4 artifacts.

Run at least:

```bash
.venv/bin/python -m pytest tests/unit/test_model_evaluation.py -q
.venv/bin/python -m ruff check scripts/model_evaluation tests/unit/test_model_evaluation.py
.venv/bin/python -m ruff format --check scripts/model_evaluation tests/unit/test_model_evaluation.py
.venv/bin/python -m mypy --explicit-package-bases scripts/model_evaluation tests/unit/test_model_evaluation.py
.venv/bin/python -m scripts.model_evaluation.execution --execute
.venv/bin/python -m scripts.model_evaluation.execution --verify
.venv/bin/python -m scripts.model_evaluation.notebook_execution --execute
.venv/bin/python -m scripts.model_evaluation.notebook_execution --verify
```

Required checks for this surface:

- Enforce per-window role chronology from `window_role_calendar`:
  `hyperparameter_selection -> calibration_fit -> calibration_selection -> threshold_selection -> external evaluation`.
- Reject selection leakage: calibration/threshold rows must come from folds disjoint
  from the fold used for hyperparameter selection.
- Reject late component availability: `component_available_by_origin` must be <=
  external origin start for each window/horizon.
- Do not use Stage 4 external `evaluation_context.csv` to fit calibrators or
  select thresholds.
- Keep all adjustment targets before the reserved block (`2025-01`).
- Keep denominator-unavailable cases explicit; do not coerce them to zero.
- Require `temporal_audit.csv` and `independent_checks.csv` with all checks passing.
- Distinct Stage 5 knob values must produce distinct immutable identities under
  `artifacts/model_evaluation/` without overwriting previous bundles.

Critical regression tests are encoded in `tests/unit/test_model_evaluation.py`:

- reject calibrator/threshold availability after external origin;
- reject reuse of labels for configuration selection and later adjustment roles.


## Stage5 closure delivery1: six procedures and AUROC

Map `scripts/evaluation_metrics.py`, `scripts/model_assessment/**`, notebook08
and the owning model_evaluation contract to `tests/unit/test_model_assessment.py`.
Preserve all prior equivalence/temporal tests. Add only critical AUROC pairwise
reference (including ties), single-class/missing/alignment, equal-window aggregation
and six-procedure early-T+2 calendar regressions.

```bash
.venv/bin/python -m pytest tests/unit -q
.venv/bin/ruff check tests scripts/model_assessment scripts/evaluation_metrics.py
.venv/bin/ruff format --check tests scripts/model_assessment scripts/evaluation_metrics.py
.venv/bin/mypy tests
.venv/bin/mypy --explicit-package-bases scripts/model_assessment scripts/evaluation_metrics.py
.venv/bin/python scripts/check_markdown_links.py
.venv/bin/python -m scripts.model_assessment.execution --execute
.venv/bin/python -m scripts.model_assessment.execution --verify
```

Execute notebook08 from a fresh kernel and verify its saved receipt. Independently
check AUROC, unchanged original metric records and all six exact retained component
lineages. Guard real verify/reuse against fitting and silent repair; compare all
historical artifact hashes. Keep live input verification plus exact scientific
equivalence, not a single-current-ID restriction or a relaxed science check. Do not
execute earlier training pipelines: their code/contracts and fitted outputs are
inputs to this delivery. No2025 label/result/statistic access or new training.
DWP acceptance is bounded to the revised development delivery; G4/G5 and future
reserved execution remain separately authorized.

## Stage5 closure delivery2: gated final evaluation

Map `scripts/final_evaluation/**`, migrated notebook08 and its owning Stage5README
to `tests/unit/test_final_evaluation.py`. Preserve frozen assessment/metric code,
contract and every historical bundle. The preceding assessment CLI applies to its
historical notebook revision; current notebook08 uses the final-route CLI.

```bash
.venv/bin/python -m pytest tests/unit -q
.venv/bin/ruff check tests scripts/final_evaluation
.venv/bin/ruff format --check tests scripts/final_evaluation
.venv/bin/mypy tests
.venv/bin/mypy --explicit-package-bases scripts/final_evaluation
.venv/bin/python scripts/check_markdown_links.py
.venv/bin/python -m scripts.final_evaluation.execution --execute
.venv/bin/python -m scripts.final_evaluation.execution --verify
```

The default notebook mode checks development-only readiness. Add `--scientific`
only after explicit human authorization; its presence never supplies authorization.
Critical synthetic regressions exercise T2 November→January availability, both
complete cohorts before any fit, predictor controls/future invariance, original
S/S−1 monthly-block accounting, unavailable acceptance and native six-adapter
round-trip/reuse with fitting blocked. Verify current development dependencies
through their existing native verify-only path with fit/selection entrypoints
blocked; do not retrain or inspect2025 to prepare approval. Check all historical
hashes and separate the new notebook migration identity from the fixed proposal.
Independent review must examine actual source and execution evidence. Actual final
coverage/results require separate scientific authorization. After Mauricio's exact
authorization, the observed gate is:

```bash
bash .dwp/plans/PLAN_028_stage5_comparison_reserved_evaluation/reserved_checks.sh
```

It verifies the current immutable final bundle, six saved inference round trips,
complete 2025 cohorts, fit accounting, metric denominators, common temporal-block
draws, protected inputs, full unit suite and scoped DWP conformance. It performs
zero new model or preparer fits. G5 remains outside this gate.

## Stage5 final scientific review and technical closure

The final review reuses the immutable scientific bundle and runs verification only.
It checks the final interpretation, decision boundary, documentation, security and
review evidence, then repeats the repository controls for the touched surfaces.

```bash
bash .dwp/plans/PLAN_028_stage5_comparison_reserved_evaluation/final_checks.sh
```

The command must not call fit, search, calibration or threshold-selection entry
points. It does not approve G5 or select a champion. Global DWP incidents in older
plans remain visible separately; PLAN_028 acceptance uses scoped conformance.


## Kedro migration baseline (Session 1)

Owner: [migration baseline, evidence and recovery](operations/kedro-migration.md).
`tests/conftest.py` registers `--require-migration-evidence`; ordinary CI deselects
private migration tests and runs the synthetic comparators. The existing CI test
job selects `tests/unit tests/integration/test_migration_parity.py`; it never passes
the private-evidence option. The explicit flag
requires selected evidence tests and fails on absent inputs, runtime, source
reconstruction, bundles or eligible comparisons. It never turns missing private
evidence into a successful skip. No model fitting or notebook execution is needed.

- `tests/integration/migration_support.py`: hash/path validation and strict ordered
  frame comparisons; synthetic corruption, missingness and decision drift tests.
- `tests/integration/migration_replay.py`: separate historical runtime process,
  original native component loading and no-fit replay, with write/fit guards.
- `tests/integration/test_migration_parity.py`: protected source/contract/input and
  native-bundle identity, complete active-chain source recovery, the closed 13
  historical exceptions and 4.6/4.7 compatibility. Its 4.7 test independently
  rehashes all 2,553 protected files and checks exact bundle membership/identity
  after replay, including failed replay attempts.
- `docs/operations/kedro-baseline-scope.json`: pinned revision-2 approved scope
  and KEEP / UNVERIFIED dispositions for the 17 affected historical bundles.
  Synthetic mutations exercise active missing sources, extra historical missing
  sources, exception path/hash drift, forbidden dispositions/equivalence claims,
  full-history claims and scientific authorization boundaries.

Run from the repository root with the existing `.venv` (no installation into it):

```bash
export PATH="$PWD/.venv/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
python -m pytest tests/unit -q
python -m pytest tests/integration/test_migration_parity.py -q
python -m pytest tests/integration/test_migration_parity.py --require-migration-evidence -q
python -m ruff check tests
python -m ruff format --check tests
python -m mypy tests
```

The private command requires the original local baseline inventory and artifacts,
recovered source snapshots and two separately configured runtimes. A fresh clone
without them must fail that gate. Stable selectors for later migration tasks are
`baseline`, `compatibility`, `preparation`, `training` and `evaluation`; future
selectors require actual stage tests before use. The current harness does not
claim parity for Kedro code that has not been implemented.

## Kedro foundation (Session 2)

`src/sat_dengue/**`, `conf/base/**`, packaging/dependency changes and
[ADR-0002](decisions/adr-0002-kedro-orchestration-boundary.md) map to:

```bash
python -m pytest tests/unit/test_repository_bootstrap.py tests/contracts/test_kedro_configuration.py -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src tests
```

Use the isolated foundation environment. The snapshot contract test owns and cleans a unique
temporary directory under ignored `tmp/`; its storage boundary remains repository-local.
The contractual commands and CI selection require no `PYTEST_DEBUG_TEMPROOT`,
`PYTEST_ADDOPTS`, `--basetemp` or global `TMPDIR` changes. A separate negative test
verifies that external snapshot storage remains rejected.
Bootstrap tests verify installed metadata, the actual nonempty graph and framework
independence of existing domain modules. Configuration tests exercise merged YAML
and CLI runtime overrides, unknown profiles, invalid/changed scientific JSON,
catalog replacement, immutable atomic snapshots, unique execution identities,
single-source dependency pins and the exact two-file metadata amendment.

Run the full preexisting unit suite and synthetic migration suite after dependency
changes. Run the protected migration suite with `--require-migration-evidence` to
verify all original evidence, the unchanged 13 exceptions / 17 historical bundle
dispositions and preserved 4.6/4.7 saved-component replay. The explicit approved
metadata mapping verifies original `pyproject.toml` and `requirements-modeling.txt`
Git blobs against baseline.json and current versions against
`operations/kedro-foundation-metadata.json`; it does not relax native scientific
hash verification or overwrite baseline.json. Mutated origins, current hashes,
revision, additional exceptions and unrelated protected-file drift must fail.

Run Markdown links, repository-only and scoped PLAN_030 conformance; report
all-plan historical failures separately. CI now checks `src tests` for lint,
format and typing and collects configuration contracts alongside existing synthetic
tests. No model fitting with real data, notebook execution or scientific pipeline
migration is authorized by these foundation gates.

## Kedro Stage 2 data migration (Session 3)

Use `tmp/kedro-migration/foundation`; commands require no `PYTEST_DEBUG_TEMPROOT`,
`PYTEST_ADDOPTS`, `--basetemp` or changes to `TMPDIR`.

| Maintained surface | Safeguards |
| --- | --- |
| `src/sat_dengue/data/consolidation.py` | Existing `test_consolidated_dataset_pipeline.py`: normalization, dates, aggregation, zeros/missingness, Y/P75 and channel boundaries |
| `src/sat_dengue/data/readiness.py` | Existing `test_stage2_training_readiness.py`: independent channel, eligibility, temporal selectors and provenance |
| `data/validation.py`, `data/workflow.py`, `pipelines/data/`, `datasets/stage2.py` | `test_kedro_data.py`: actual synthetic graph, explicit snapshot dependencies, wrong schema/keys/month coverage/source manifest, contradictory science, no overwrite and corrupted membership |
| `datasets/legacy_*`, old script adapters | Original Stage 2 unit guards; Stage 3 unit consumers stay intact |
| Catalog/registry/configuration | `test_repository_bootstrap.py`, `tests/contracts/test_kedro_configuration.py`, `test_kedro_data.py` |
| Protected real Stage 2 inputs/outputs | `test_data_kedro_complete_stage2_parity` in `test_migration_parity.py`: actual CLI, complete cohorts, ordered frames/dtypes/schema/masks, byte-exact individual CSV, full targets/channel/readiness/provenance and before/after preservation |

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
python -m pytest tests/unit tests/contracts tests/integration/test_migration_parity.py -q
python -m pytest tests/integration/test_migration_parity.py --require-migration-evidence -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src tests
python -m pip check
python scripts/check_markdown_links.py
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
bash .agents/skills/deepworkplan/verify/conformance.sh --plan PLAN_030_kedro_architecture_migration
git diff --check
```

Also run the exact AC-data compound command declared by PLAN_030 through the
local official DWP gate runner. Its historical selector excludes filenames
containing `training`, so the separate full affected unit/CI selection is required
for all readiness guards. Default CI uses only synthetic tests; private evidence
is mandatory locally and cannot pass through a missing-data skip.

The two-script original/current mapping in `operations/kedro-data-identities.json`
is verified separately from the unchanged foundation metadata mapping. The private
suite preserves all 2,553 original identities, every native bundle, and the exact
13 historical exceptions / 17 KEEP / UNVERIFIED dispositions. No historical
notebook, model fitting, Stage 3 construction or tracking is required by this gate.

## Kedro Stage 3 preparation migration (Session 4)

Use the isolated `tmp/kedro-migration/foundation` environment. No
`PYTEST_DEBUG_TEMPROOT`, `PYTEST_ADDOPTS`, `--basetemp` or global `TMPDIR` change
is required. The catalog explicitly selects the protected Stage 2 manifest and
native development/temporal identities; a missing source fails private acceptance.

| Maintained surface | Owning checks |
| --- | --- |
| `training_preparation/features.py`, `validation.py`, `eligibility.py`, `contract.py` | `test_training_preparation.py`: all original scientific regressions, role/schema validation, full synthetic graph and X/Y/keys/control alignment |
| `training_preparation/temporal.py`, `preprocessing.py`, `workflow.py` | `test_training_temporal.py`, `test_training_preparation.py`: eight windows, producer/consumer cutoff negatives, 2025/non-train fit refusal, saved schema/category/order/state, synthetic train-only fit and validation perturbation |
| `datasets/preparation.py`, `datasets/legacy_preparation/`, `serialization.py` | Preparation unit suites: atomic no-overwrite publication, corrupt payload/manifest/membership, legacy import behavior; original atomic failure cleanup tests remain enabled |
| `pipelines/preparation/`, catalog, registry and configuration | Actual synthetic Kedro graph, explicit cutoffs/saved states, `test_repository_bootstrap.py` and configuration contracts |
| Protected real preparation | `test_preparation_kedro_complete_cohorts_and_saved_replay`: actual CLI with call-level fit denial, all 99 original payload bytes, full 16,948-row development cohort, eight temporal cohorts, native categories/dtypes, 29/114-column transforms and saved parameters |
| Closed original/current mapping | `migration_support.py`: exact twelve-path Session 4 ledger, original Git blobs and current sizes/hashes, plus independent 2,553-file/45-bundle preservation |

Run the exact contractual preparation gate through the official local DWP runner:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
python -m pytest tests/unit/test_training_preparation.py tests/unit/test_training_temporal.py \
  tests/integration/test_migration_parity.py -k "preparation or temporal or baseline" \
  --require-migration-evidence -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src tests
```

Also run the complete CI synthetic selection and full private suite:

```bash
python -m pytest tests/unit tests/contracts tests/integration/test_migration_parity.py -v
python -m pytest tests/integration/test_migration_parity.py --require-migration-evidence -q
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=preparation --params=profile=preparation
python -m pip check
python scripts/check_markdown_links.py
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
bash .agents/skills/deepworkplan/verify/conformance.sh --plan PLAN_030_kedro_architecture_migration
git diff --check
```

Lint/format the touched legacy adapters too. Private CLI acceptance installs a fit
call guard and verifies the protected inventory before and after; all new fits in
unit tests use deterministic synthetic data. Saved preparers are loaded/replayed,
never refitted. No model training or Stage 4 migration is part of this gate. Report
all-plan conformance separately: the two recorded historical plan incidents do not
become current code failures. The closed preparation mapping preserves the active
README's original historical bytes while its current owner follows DEC-135.

## Kedro Stage 4 model migration (Session 5)

Use the isolated foundation environment and unset special pytest variables as in
Session 4. No basetemp or global TMPDIR override is required. Private acceptance
requires the original baseline, all active native components and the two existing
4.6/4.7 runtime environments; a missing input fails rather than becoming a skip.

| Maintained surface | Owning checks |
| --- | --- |
| `model_training/` families, preparation, selection and references | `test_candidate_families.py`, `test_xgboost_candidate.py`, `test_model_training.py`: native roundtrips, approved grids/budgets, synthetic fits for all three families, ablation projection, train-only temporal selection and leakage negatives |
| `metrics.py` | `test_model_metrics.py`, `test_model_training.py`: grouped ties/permutations, class/zero support, Brier, onset S/S−1 context, missing predictions, no-alert non-evaluability, FAR denominators and equal window weights |
| `pipelines/training/`, catalog and configuration | Actual synthetic Kedro graph, separate real-source-free input set, unknown profile/config/family rejection, bootstrap and configuration contract suites |
| `datasets/training.py`, `training_legacy.py`, retained adapters | Fit/search alias denial, explicit pinned inputs, atomic no-overwrite publication, corrupt manifest/payload/membership/missing artifact refusal; existing atomic failure cleanup and legacy consumer tests stay enabled |
| Complete real replay | `test_training_kedro_all_saved_components_and_metrics`: whole-process guarded Kedro CLI, 40 development and six frozen models, 16,720/6,688 development/reference predictions, 160/64 metric rows, 56 horizon means, 5,472 frozen raw probabilities and 1,824 persistence rows; full cohorts and masks, no sampling |
| Native compatibility and preservation | The same private test runs current adapters under both LightGBM 4.6 and 4.7 with zero-tolerance predictions/model roundtrips. Existing historical full final-output replay stays separate. `migration_support.py` verifies the closed 21-path original/current mapping and all 2,553 original identities / 45 bundles. |

Run the exact AC-training compound gate through the official local DWP runner:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
bash -lc "python -m pytest tests/unit/test_model_training.py tests/unit/test_candidate_families.py tests/unit/test_model_metrics.py tests/unit/test_xgboost_candidate.py tests/integration/test_migration_parity.py -k 'training or candidate or metric or baseline' --require-migration-evidence -q && python -m ruff check src tests && python -m ruff format --check src tests && python -m mypy src tests"
```

Additional required checks:

```bash
python -m pytest tests/unit tests/contracts tests/integration/test_migration_parity.py -v
python -m pytest tests/integration/test_migration_parity.py --require-migration-evidence -q
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=training_synthetic --params=profile=training_synthetic
python -m pip check
python scripts/check_markdown_links.py
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
bash .agents/skills/deepworkplan/verify/conformance.sh --plan PLAN_030_kedro_architecture_migration
git diff --check
```

Lint/format the retained training adapters separately too. Record exact floats for
native prediction/model roundtrips, exact keys/order/schema/missingness and the
pre-existing comparator tolerances for declared metric numeric columns. Do not
relax tolerances or substitute sampled comparisons. Inspect secret and prohibited
runtime patterns on the changed surface, then independently verify preservation
after replay and after the commit. Report all-plan conformance separately from
the repository and PLAN_030; the two inherited historical incidents remain.

## Base installation and checkout-independent test storage

`tests/conftest.py::repo_tmp_path` owns repository-local temporary test storage.
It creates the ignored parent when absent, yields a unique workspace per test,
and cleans only its own files. Tests must request this fixture instead of creating
`TemporaryDirectory(dir=ROOT / "tmp")` directly. No precreated directory, global
temporary-environment override or execution-order dependency is permitted.
Validate the synthetic selection in a `git archive HEAD` checkout with no `tmp/`.

`test_base_bootstrap_and_training_dependency_boundary` runs a fresh subprocess
that denies all six optional modeling imports. All six pipeline names must still
register, default must remain foundation, and foundation must execute successfully.
Training nodes and native source loading must fail with an explicit instruction
to install `sat-dengue-v2[modeling]`. The private replay and synthetic training
checks above validate the same deferred boundaries with modeling installed.
Validate an actual base-only wheel installation and `pip check` too; never move
modeling libraries into base dependencies to satisfy bootstrap.


## Kedro Stage 5 frozen assessment (Session 6)

The existing `test_model_evaluation.py`, `test_model_assessment.py` and
`test_final_evaluation.py` own pure calendar/availability, calibration, threshold,
utility, cohort and event/uncertainty rules. Their original regressions stay enabled.
New final-evaluation tests exercise the actual source-free synthetic graph,
deterministic publication, runtime scientific override rejection, call/alias fit
and selection denial, consumed real-route rejection, and atomic failure/no-overwrite.
They use the shared repository-local temporary-workspace fixture.

`test_evaluation_kedro_all_frozen_decisions_probabilities_and_metrics` owns the
complete real guarded CLI, saved development/final probability replay, full cohorts,
metrics and decisions, closed source/component/proposal negatives and independent
before/after preservation. Missing private evidence fails; it is never a skip.
`migration_support.py` verifies the new closed 23-path evaluation correspondence
alongside all prior mappings and the original 2,553-file/45-bundle inventory.

Run the exact contractual gate through the official local DWP runner:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
bash -lc "python -m pytest tests/unit/test_model_evaluation.py tests/unit/test_model_assessment.py tests/unit/test_final_evaluation.py tests/integration/test_migration_parity.py -k 'evaluation or assessment or baseline' --require-migration-evidence -q && python -m ruff check src tests && python -m ruff format --check src tests && python -m mypy src tests"
```

Also run the complete synthetic CI and private suite, prior exact AC-training and
AC-foundation gates, both new evaluation CLIs (real replay under the call guard),
all retained-adapter lint/format, pip check, Markdown links, diff and boundary scans:

```bash
KEDRO_DISABLE_TELEMETRY=yes python -m pytest tests/unit tests/contracts tests/integration/test_migration_parity.py -q
python -m pytest tests/integration/test_migration_parity.py --require-migration-evidence -q
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=evaluation_synthetic --params=profile=evaluation_synthetic
PYTHONPATH=.:src KEDRO_DISABLE_TELEMETRY=yes python tests/integration/evaluation_cli.py
python -m pip check
python scripts/check_markdown_links.py
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
bash .agents/skills/deepworkplan/verify/conformance.sh --plan PLAN_030_kedro_architecture_migration
git diff --check
```

The direct guarded probe needs repository root and src on PYTHONPATH, as supplied
by its private test. Validate a fresh git archive with no manually created tmp and
an actual new base-only wheel: all eight graphs register and foundation executes
without modeling. Preserve the three existing absent historical-report skips in
an archive as a separate limitation; no corrected test is skipped. No special
pytest environment override or basetemp is permitted. Report global conformance
separately from current repo/scoped-plan conformance, retaining inherited incidents.
All real fits/refits/calibration/selection/search counts must be zero. Synthetic
fixtures never replace real parity; no 2025 selection or scientific approval follows.

## Bounded MLflow tracking (Session 7)

`tracking/{local,lineage,artifacts}.py`, `hooks.py`, settings and operational tracking
switches map to `tests/integration/test_mlflow_tracking.py`: actual SQLite-backed
MLflow, complete synthetic Kedro publications, standard/diagnostic profile comparison,
identical science with tracking disabled, parent/child relationships, full publication
verification, compute/publication failures, aborts, duplicate-success prevention,
allowlist rejection, missing extra and invalid storage. Database dumps, run metadata
and approved artifacts must exclude private absolute paths and raw records.

Run the exact AC-tracking command through the official local DWP runner:

```bash
bash -lc "python -m pytest tests/integration/test_mlflow_tracking.py -q && python -m ruff check src tests && python -m ruff format --check src tests && python -m mypy src tests"
```

Also run the complete CI selection including the new tracking test, exact foundation
and evaluation regressions, base-only wheel/bootstrap without MLflow or modeling,
`pip check`, Markdown links, diff and bounded secret/privacy/dependency scans,
repo-only and PLAN_030 conformance, and independent protected inventory verification.
The existing CI extra remains optional for base installation. Missing private evidence
fails local parity; the synthetic tracking comparison cannot substitute for it.
Inspect ignored SQLite/artifact locations with `git check-ignore` one path at a time.
Report inherited global plan incidents separately. Failure/development logs remain
under PLAN_030 `analysis_results/session7/tracking/`. No notebook or real fit is needed.
