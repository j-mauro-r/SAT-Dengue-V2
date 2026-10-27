# Testing and Validation Guide

## Validation Policy

Validation is mapped by touched surface and reported using explicit evidence states. The
goal is the smallest safe gate, not the fewest checks. Unknown paths, changes to the CI
workflow or classifier, protected-branch pushes, and mixed changes whose ownership is
ambiguous fail closed to the conservative gate.

Evidence states:

- PASS
- FAIL
- BLOCKED
- UNVERIFIED

## Proportional Gate Set

### CI classifier

Inspect CI selection with the existing deterministic classifier (this does not require running its full selection locally):

```bash
.venv/bin/python scripts/classify_validation_surface.py <changed-path> [<changed-path> ...]
.venv/bin/python scripts/classify_validation_surface.py --base <base-revision> --head HEAD
```

The JSON result identifies the surfaces, selected pytest scope, and each CI job gate.
Classification is by repository-relative path and is intentionally conservative for empty,
malformed and unknown inputs.

### CI validation matrix

| Changed surface | Required gates |
|---|---|
| Narrative documentation | Markdown links, repository structure and security scans; no Python dependency install and no pytest |
| DWP or agent governance | Narrative-documentation gates plus repository/scoped-plan conformance as applicable |
| Stage 7 API, service or contractual fixtures | Scoped Ruff/format/mypy, the three Stage 7 API test modules and base-wheel validation; API-dashboard smoke is manual-only |
| Dashboard only | Manual-only: `bun install --frozen-lockfile`, lint, test and build |
| Dashboard client, adapter, proxy/config or shared API contract | Applicable Python/API jobs; Dashboard and API-dashboard smoke are manual-only |
| Stage 2/3 data preparation | Full Python quality and the public CI pytest suite |
| Models, metrics or calibration | Full Python quality and the public CI pytest suite |
| Tracking or MLflow | Full Python quality and the public CI pytest suite |
| Kedro configuration or shared graph | Conservative gate because producer/consumer reach is cross-surface |
| Scientific contracts | Owning data/model gates; Stage 6 API-dashboard smoke is manual-only |
| Packaging or shared dependencies | Full Python quality, public CI pytest suite and base wheel; Dashboard/smoke manual-only |
| CI workflow, classifier, protected `main` push, unclassified configuration, unknown or ambiguous path | Conservative gate: all four automatic base jobs execute their full steps; Dashboard remains manual-only |

Mixed known surfaces use the union of their gates. A mixed API plus dashboard change, for
example, runs scoped API checks and base-wheel validation; Dashboard/smoke stay manual; it
does not escalate to the complete public suite merely because two known surfaces changed.

The automatic base job names remain `Repository Quality`, `Python Quality`,
`Unit Tests`, and `Base wheel without optional dependencies`. Existing surface selection
still applies to these jobs. CodeQL Python remains a separately managed security check.
Dashboard and its API smoke are available only through the `Manual Dashboard` workflow
(`workflow_dispatch`); no automatic Dashboard check is emitted. Classifier Dashboard/smoke
flags remain advisory for manual use and do not reactivate automatic execution.

### When to run each gate

1. **Before push:** run only existing focused tests for changed files/behavior, plus quick
   syntax/configuration validation of affected workflows. Run Markdown links when linked
   documentation changes and scan only changed files/the diff for secrets.
2. **PR CI:** GitHub runs the complete validation required by the selected surfaces, using
   the four automatic base jobs and separately managed CodeQL Python. Do not repeat that
   full selection locally as a prerequisite to pushing.
3. **Full local suites:** retain all commands below for manual use. Repeat a full suite
   locally only when CI cannot execute it, while diagnosing a remote failure, or when a
   change affects the repository across surfaces. This exception does not authorize a
   scientific experiment or private-data access.
4. **Dashboard:** Mauricio may run `Manual Dashboard` from Actions → Run workflow, selecting
   a reviewed branch after this workflow exists on the default branch. It runs existing
   install/lint/tests/build and API smoke. Reactivation of automatic execution requires a
   separate explicit request.

### GitHub security and required-check handoff

The only versioned automatic workflow before this change was `ci.yml`, with Repository
Quality, Dashboard, Python Quality, Unit Tests and Base wheel without optional dependencies.
No CodeQL workflow is defined in this repository. Default setup, check runs, branch
protection and ruleset API queries returned HTTP 403 during the audit; their configuration
and required-check status are **UNVERIFIED**, not assumed disabled or safe to remove.

Before merging, Mauricio must inspect Settings → Rules → Rulesets and Settings → Branches
→ the rule for `main` → required status checks. Remove an automatic `Dashboard` requirement
if present, and remove JavaScript/TypeScript or unconditional Actions CodeQL requirements
that would otherwise wait forever. Preserve the four base job requirements and CodeQL
Python. Also inspect any required Code Scanning tools; do not leave an obsolete language
analysis mandatory. This PR remains draft/not ready until that review is complete.

In Settings → Code security (or Code security and analysis) → Code scanning → CodeQL:

- If **Default setup** owns the scans, edit its language selection to retain **Python only**;
  deselect JavaScript/TypeScript and Actions. Python must remain enabled. Default setup
  cannot express an Actions-only workflow-path condition; do not add a duplicate repository
  CodeQL workflow to try to override it.
- To retain Actions analysis with the approved scope, Mauricio must deliberately configure
  **Advanced setup**, preserving the existing Python analysis, and review its generated
  workflow before enabling it. The separate Actions-only workflow must use language
  `actions`, PR/push path filters `.github/workflows/**`, base branch `main`, and no schedule
  or unfiltered automatic trigger. Keep Python in its own automatic analysis so path filters
  cannot suppress Python. Do not leave JavaScript/TypeScript in the matrix. If Advanced
  setup already owns scans elsewhere, make those same changes in that owner rather than
  enabling a second setup.
- Verify a workflow-changing PR produces Actions analysis, while a subsequent ordinary
  scientific/docs PR does not. Confirm CodeQL Python still reports successfully.

These are manual configuration instructions, not changes performed by this branch.
Remote CodeQL language removal, path scoping and required-check reconciliation remain
pending until observed in GitHub. The dashboard directory still contains TypeScript;
its automatic checks are suspended by explicit human scope decision, not because those
files are absent.

The scientific public suite retains temporal-leakage, reserved-block, artifact-integrity,
G5/Champion, read-only API and no-fallback controls. The matrix changes frequency and scope;
it does not delete or relax those assertions.

### Full public Python gate

In CI, or under the explicit full-local-suite exceptions above, when the matrix selects
`pytest_scope=full`, use the installed complete synthetic environment
(`.[dev,modeling,tracking]`) and run:

```bash
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest \
  tests/unit tests/contracts tests/integration/test_migration_parity.py \
  tests/integration/test_mlflow_tracking.py tests/integration/test_kedro_e2e.py -v
```

This public suite deselects private migration evidence unless the human explicitly requests
`--require-migration-evidence`. It never authorizes a real replay, model adjustment, notebook
execution or scientific regeneration.

### Security and policy scans

CI treats every match as a failure. Local inspection may use the Quick Commands in
`AGENTS.md`, but a report must not call the scan PASS merely because `|| true` masked a match.
The effective shell shape is fail-closed:

```bash
if grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp \
  --exclude-dir=.github --include='*.py' --include='*.json' \
  --include='*.toml' --include='*.sh'; then exit 1; fi
if grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' \
  . --exclude-dir=.git --exclude=skills-lock.json; then exit 1; fi
```

### Documentation consistency checks (required)

- `python3 scripts/check_markdown_links.py`

## Escalation Rule

If path ownership or a mixed surface is ambiguous, CI uses the classifier's conservative gate.
Local pre-push validation follows the focused-check rule above.
Do not weaken a gate ad hoc in the workflow.

## No-repeat rule for DWP execution

Order cheap scoped gates before broader gates. Once a broader passing gate demonstrably
subsumes a narrower command at the same commit and environment, reuse that evidence rather
than rerunning the subset. Rerun only when the relevant code/configuration/environment changed,
the prior run failed or was interrupted, or the narrower command validates a distinct runtime
boundary such as the API-dashboard smoke. Record the reason for any rerun in the active plan.

## Stage 7 executable read-only API contract

Map `scripts/read_only_api/**` (including its demonstrative fixtures) and
`tests/unit/test_read_only_api_contract.py` to the focused executable-contract gate:

```bash
.venv/bin/python -m pytest tests/unit/test_read_only_api_contract.py -q
.venv/bin/ruff check scripts/read_only_api tests/unit/test_read_only_api_contract.py
.venv/bin/ruff format --check scripts/read_only_api tests/unit/test_read_only_api_contract.py
.venv/bin/mypy --explicit-package-bases scripts/read_only_api tests/unit/test_read_only_api_contract.py
```

These tests validate the separate runtime-owned Tolima and Meta demonstrative fixtures,
explicit department resolution, exact enums, territorial membership and uniqueness,
reference-to-target month coherence including year rollover, UUID/nullability rules,
availability/alert coherence, G5 governance, result identity uniqueness, and T1/T2
completeness. They do not start a server, access Kedro, train a model, execute inference,
or select a Champion. Apply the matrix above; API changes select the scoped API gate, base
wheel and smoke without automatically selecting model/tracking tests.

Product Contract v1.1 additionally requires exact DANE/DIVIPOLA inventories of
47 Tolima and 29 Meta municipalities, the closed `INELIGIBLE` unavailable shape,
and API-supplied `endemic_channel_series`. Focused tests reject duplicate or
unordered series periods, observed cases after T, unordered percentiles,
reference-point disagreement, and empty series paired with available observed
context. They also prove that every municipality has exactly one T1 and one T2.

## Stage 7 read-only repository, service, and HTTP endpoint

Map `scripts/read_only_api/repository.py`, `service.py`, `errors.py`, and `api.py`
plus their focused tests to these gates:

```bash
.venv/bin/python -m pytest tests/unit/test_dashboard_query_service.py tests/unit/test_read_only_api_http.py tests/unit/test_read_only_api_contract.py -q
.venv/bin/ruff check scripts/read_only_api tests/unit/test_dashboard_query_service.py tests/unit/test_read_only_api_http.py tests/unit/test_read_only_api_contract.py
.venv/bin/ruff format --check scripts/read_only_api tests/unit/test_dashboard_query_service.py tests/unit/test_read_only_api_http.py tests/unit/test_read_only_api_contract.py
.venv/bin/mypy --explicit-package-bases scripts/read_only_api tests/unit/test_dashboard_query_service.py tests/unit/test_read_only_api_http.py tests/unit/test_read_only_api_contract.py
```

The tests protect exact department-period retrieval, no fallback to another persisted
period, substitute repositories, read-only repeatability, both successful department
responses, contracted 400/404/500 bodies, safe internal-error filtering, and OpenAPI
without an uncontracted 422 response. They start no server and execute no Kedro,
training, inference, model selection, or write flow. Apply the matrix above.

## Stage 7 installable distribution and local startup

Install the API and the optional local server from a checkout with:

```bash
python -m pip install ".[server]"
```

Start the ASGI application through its factory; importing the package does not
start a server:

```bash
uvicorn --factory scripts.read_only_api.api:create_app
```

With the default Uvicorn address, the two persisted demonstrative results are:

- Tolima: <http://127.0.0.1:8000/api/dashboard?department_code=73&period=2026-09>
- Meta: <http://127.0.0.1:8000/api/dashboard?department_code=50&period=2026-12>

An exact key that is not persisted, such as
<http://127.0.0.1:8000/api/dashboard?department_code=73&period=2026-12>, returns
`404 DASHBOARD_DATA_NOT_FOUND`. These are demonstrative persisted results: G5 is
`NOT_APPROVED`, Champion is `NOT_SELECTED`, and every associated model role is
`PROVISIONAL_CANDIDATE`. Starting or querying the API performs no training,
inference, Kedro execution, or result write.

Packaging validation stays outside the normal unit suite because it builds and
installs a wheel in a temporary virtual environment. Run it from the repository
environment as follows:

```bash
rm -rf tmp/stage7-dist
.venv/bin/python -m build --wheel --outdir tmp/stage7-dist .
.venv/bin/python scripts/validate_read_only_api_wheel.py tmp/stage7-dist/*.whl
```

The validator inspects the archive, rejects unrelated repository Python
packages, installs the wheel in a fresh virtual environment, changes to a
directory outside the checkout, launches the application in-process through
ASGI, checks the two `200` responses plus contracted `404` and `400` responses,
and compares fixture hashes and modification times before and after all queries.

## Scoped Commands, Mapping, Fallback (Documentation Standard 3.4)

Scoped commands:

- `git status --short --branch`
- `find docs -type f -name '*.md' | sort`
- `test -f docs/governance/ai-developer-first.md && echo OK || echo MISSING`

Mapping rule:

- Use scoped commands for fast local inspection.
- Use the classifier and matrix above for CI selection; local pre-push checks remain focused.

Fallback rule:

- When command mapping is uncertain, let CI use the conservative gate; widen local checks
  only under the explicit exceptions above.

## Stage 8 standalone dashboard subtree

`apps/dashboard/**`, `scripts/dashboard_subtree_sync.sh`, and the canonical
[subtree synchronization guide](operations/dashboard-subtree-sync.md) map to the
dashboard's Bun lockfile and existing package scripts:

```bash
cd apps/dashboard
bun install --frozen-lockfile
bun run lint
bun run test
bun run build
bun audit --audit-level=high
```

The Stage 8 integration tests read the canonical Stage 7 fixtures directly from
`scripts/read_only_api/fixtures`; they validate both departments, all 76
municipalities, all five availability states, URL/error handling, response
validation, direct alert/channel/result traceability, coherent navigation, and
manual retry without maintaining a second fixture copy. Run the real local
two-service smoke with one command:

```bash
.venv/bin/python scripts/dashboard_e2e_smoke.py
```

It starts the ASGI factory and dashboard on free loopback ports, waits for both,
and queries Tolima `73/2026-09`, Meta `50/2026-12`, and a contracted 404 through
the dashboard origin and configurable proxy. It terminates both process groups
on success or failure. Verify generated dependency/build paths remain ignored.
The smoke runs in CI only when the classifier selects the integration surface or for a
protected `main` push. Pure visual dashboard changes retain lint/test/build without starting
the Python service.

## Stage 2 data integrity and retired experimental EDA

The [experimental EDA](archive/experimental-eda/README.md) was retired on 2026-10-19. Its notebooks, reports and pending rerun instructions are historical. Do not run the old panel/analysis/rules phases as the default Stage 2 workflow. New analysis requires a new bounded task and current acceptance criteria; retirement does not approve scientific outputs or close G2.

Keep all existing tests enabled. Synthetic regressions (`.venv/bin/python -m pytest tests/unit/test_stage2_panel_review.py -q`) run without private snapshots and preserve independent-join, missingness, geography, non-swap and calendar-adjacent safeguards. The three tests against ignored historical monthly-association outputs remain artifact-consistency checks; their passing status does not make those results current analytical evidence. The historical analytical scripts stay at their import paths with deprecation docstrings and unchanged logic because tests and local historical validators depend on them.

Active data-integrity safeguards: `.venv/bin/python -m pytest tests/unit/test_january_2020_climate_incorporation.py tests/unit/test_stage2_manifest_traceability.py -q`. These verify incorporation/traceability behavior on test fixtures; they do not download or reintegrate source data. Run the full unit suite, Ruff checks, `mypy src tests` and `scripts/check_markdown_links.py` under the foundation gate policy above. Also lint/format any touched Python script.

For this archival migration, local PLAN_012 validates the path/hash manifest, byte-identical notebooks, restricted report transformations, unchanged script logic, original data/evidence hashes and preserved historical plan records. It is a one-time migration check, not a new recurring scientific gate. New DWP work must pass scoped conformance; report pre-existing legacy-plan global failures separately without rewriting their records or weakening validation.

## Clean-checkout CI installation

The project installs the used `sat_dengue` package from `src/` only. The wheel
excludes data, notebooks and external configuration. Install with `.[dev,modeling,tracking]`
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

## Historical Stage 4–5 delivery validation

Original notebook execution/training commands and recorded fit budgets belong to
their dated delivery evidence. Recover the original guide at pre-cleanup Git
revision `861b36966cec26d1d2b36edee4d6ada6d5bc0930`; do not execute those commands
against consumed real evidence. Current contracts retain the same scientific roles,
metrics, thresholds, cutoffs and decisions. The existing model-training, candidate,
metric, assessment and final-evaluation unit suites stay enabled, now importing
their single package owners. Current guarded replay and private parity are below.

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
that denies all seven optional modeling/tracking imports. All registered pipeline names must still
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

## Composed replay E2E (Session 7)

`pipelines/replay`, `datasets/replay{,_identity,_sources,_parity,_synthetic}.py`,
registry/catalog/configuration, tracking hooks/identity projection and base graph
registration map to `tests/integration/test_kedro_e2e.py`, existing bootstrap/config
unit tests and `test_mlflow_tracking.py`. The E2E test runs two isolated source-free
synthetic graphs, compares every stage CSV, observes tracking on/off, injects failure
after computation/before final publication, denies all subsequent fixture refits on
restart, verifies single publication/success and rejects tampering, missing ancestry,
stale context and changed contract/configuration identities. Changed code/environment
creates a new context without reuse. The code identity includes every retained
Python script adapter; injected adapter identity changes cannot reuse old stages.
CI explicitly selects this synthetic seam.

Run the exact contractual gate through the official sequential DWP gate runner:

```bash
bash -lc "python -m pytest tests/integration/test_kedro_e2e.py tests/integration/test_migration_parity.py --require-migration-evidence -q && python -m ruff check src tests && python -m ruff format --check src tests && python -m mypy src tests"
```

The private E2E test invokes the public replay CLI under a whole-process real
adjustment denial guard. Full construction/preparation/training/evaluation comparisons
use the unchanged baseline tolerances and complete cohorts. It independently checks
protected evidence before/after. Existing private comparisons remain selected.
Missing evidence is a failure, not a skip or synthetic replacement. The
[migration owner](operations/kedro-migration.md#composed-replay-and-restart--session-7--t-e2e)
owns CLI configuration, identity storage and failure boundaries.

Also run the public `kedro run --pipeline=replay`, exact tracking regression,
complete CI selection and full private suite:

```bash
python -m pytest tests/unit tests/contracts tests/integration/test_migration_parity.py tests/integration/test_mlflow_tracking.py tests/integration/test_kedro_e2e.py -q
python -m pytest tests/integration -m migration_evidence --require-migration-evidence -q
```

Build the actual wheel and exercise a base-only installation with modeling/tracking
imports absent, plus a wheel installation with the approved modeling/tracking extras;
verify packaged source bytes and run `pip check` in each. Run Markdown links,
`git diff --check`, privacy/secret/dependency scans and independent preservation of
all 2,553 original identities/45 native bundles. Report repo-only, scoped PLAN_030 and
all-plan conformance separately; inherited historical plan incidents are not current
source failures. Run every validation and DWP writer sequentially. Record commands,
wall times, zero real-adjustment counters, hashes and limitations under PLAN_030
`analysis_results/session7/e2e/`. T-cleanup reconciles these consumers; T-final-review remains a separate pending task.


## Repository cleanup and disposition (Session 8)

The official E2E command is `kedro run --pipeline=replay`. The exact AC-cleanup
command remains unchanged in PLAN_030. `tests/contracts/test_repository_disposition.py`
verifies the resolved executable registry, retired-path absence/import boundaries,
required owners/entrypoints, retained adapter ownership, scaffold rejection,
historical notebook role, exact67-path ceiling and separate preservation mapping.
`tests/integration/cleanup_support.py` verifies both original and pre-cleanup Git
blobs and final physical presence/absence. Existing preservation checks still
verify every earlier closed mapping, all2553 original identities and exact45 native
bundle memberships/payloads. Private data missing locally fails required acceptance.

```bash
python -m pytest tests/unit tests/contracts tests/integration/test_migration_parity.py tests/integration/test_mlflow_tracking.py tests/integration/test_kedro_e2e.py -q
python -m pytest tests/integration -m migration_evidence --require-migration-evidence -q
```

Run all seven affected owning-stage contractual regressions (foundation through
E2E) unchanged through the official sequential DWP runner, plus AC-cleanup. Run
pip checks, base-only and modeling/tracking wheel installs, Markdown links, diff,
secret/privacy/dependency controls and before/after protected preservation. Report
repo-only, PLAN_030 and global conformance separately. Existing historical global
failures are never silently waived or repaired. No real fit/search/selection or
notebook execution is authorized by cleanup. Preserve original failure logs.

Maintained script quality covers the Markdown checker, constraints exporter, two
thin Stage2 source-identity facades, the visual/calendar compatibility helper and
traceability validator. Historical EDA/reconciliation/January acquisition sources
remain immutable regression/provenance evidence, not current execution commands.
Their whole-directory lint/type diagnostics remain explicit debt; do not introduce
broad ignores or edit protected paths outside the approved ceiling. CI checks the
enumerated maintained scripts alongside src/tests. Module-root options for mypy
must identify src, test helpers and script namespaces consistently; do not suppress
missing annotations or install undeclared stub packages to conceal failures.

+
+Validation receipts allocate a unique directory per check, never a fixed earlier
+session destination. By default they go under ignored
+`tmp/kedro-migration/validation-evidence`. A session may set
+`SAT_DENGUE_VALIDATION_EVIDENCE_ROOT` to its repository-local PLAN_030 analysis
+directory; every test still creates a new UUID child. Inputs keep their pinned
+paths. Earlier session logs/receipts and prior runtime observations are not
+overwritten by a fresh regression. Unsafe/external output roots fail closed.
+

## Registered scientific experiment tracking

`tracking/experiments.py`, experiment registry/protocols, configuration, hooks and
replay parameter propagation map to the following permitted validation:

```bash
python -m pytest tests/unit tests/contracts tests/integration/test_mlflow_tracking.py -q
python -m pytest tests/integration/test_kedro_e2e.py -k 'not test_one_command_full_guarded_replay_and_complete_preservation' -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src tests
python scripts/check_markdown_links.py
git diff --check
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
bash .agents/skills/deepworkplan/verify/conformance.sh --plan PLAN_031_exp00_baseline_tracking
```

The tracking suite uses registered synthetic fixtures, including source-free
composition, protocol immutability, privacy and duplicate registration checks.
For PLAN_031 the user explicitly prohibited real replay, including
`test_one_command_full_guarded_replay_and_complete_preservation` and private parity
commands that invoke it. Do not use `--require-migration-evidence` for this work.
The formal EXP00 replay is a pending manual final check, not a claimed pass.
Report global historical DWP failures separately. Runtime setup remains owned by
[the migration guide](operations/kedro-migration.md); experiment registration and
the later manual command are owned by [the registry guide](product/experiments/README.md).

### EXP01 direct-onset infrastructure

EXP01's scientific functions, frozen protocol resolver, synthetic Kedro graph,
configuration profile and isolated MLflow path map to these tests:

```bash
.venv/bin/python -m pytest tests/unit/test_exp01_onset.py tests/contracts/test_kedro_configuration.py tests/unit/test_repository_bootstrap.py -q
.venv/bin/python -m pytest tests/integration/test_exp01_tracking.py -q
.venv/bin/python -m ruff check src/sat_dengue/experiments src/sat_dengue/tracking tests/unit/test_exp01_onset.py tests/integration/test_exp01_tracking.py
.venv/bin/python -m ruff format --check src tests
MYPYPATH=src:tests:tests/integration:tests/unit:tests/contracts .venv/bin/python -m mypy --explicit-package-bases --exclude '(^|/)conftest\.py$' src tests
.venv/bin/python scripts/check_markdown_links.py
```

These tests use generated rows and a dedicated ignored temporary MLflow store.
The EXP01 integration check asserts the exact parent/36-child structure, protocol
and data identities, no logged synthetic metrics, zero real-fit counters, and
duplicate protection. It does not run a real scientific pipeline,
load private panel data, or evaluate 2024/2025.

The explicit mypy invocation avoids the repository's duplicate top-level
conftest module names while checking all other source and test files.


## EXP00 tracking audit corrections

The protocol MLflow object must contain exactly `experiment_name` and
`required_conceptual_tags`. The registry resolver and local tracker share the fixed
container constant; mutable registration status and implementation notes are
rejected. `test_experiment_registry.py` covers correct/missing/different names,
extra fields, unchanged conceptual tags and the direct PyYAML base pin.
`test_mlflow_tracking.py` checks that the actual MLflow container uses the constant.

For PLAN_032, run the focused registry/tracking suites, then the complete
unit/contracts/tracking selection and standard Python/documentation gates above.
Use the official constraints exporter after a clean full-extras install. Build a
wheel with `python -m pip wheel --no-deps .`, then install that wheel with its base
dependencies in a fresh repository-local virtual environment using the generated
constraints. Run `pip check` and, outside source import paths (`python -I`), verify
`import sat_dengue.tracking.experiments`, its installed module location, PyYAML's
pinned version and its direct `Requires-Dist` metadata. Confirm optional MLflow and
modeling packages remain absent. Run only `foundation` for a Kedro startup smoke.
Do not execute real replay, its excluded E2E test or replay-dependent private suites.


### EXP01 raw-input admission correction (R1)

`experiments/exp01_inputs.py`, its authorized runner binding and the shared source-identity/
field-typing helpers map to `tests/unit/test_exp01_inputs.py` and
`tests/integration/test_exp01_input_integration.py`, using
`tests/integration/exp01_inputs_fixture.py`. Each changed synthetic CSV receives a freshly fingerprinted
manifest; the byte-tamper case intentionally keeps its old fingerprint and must fail.
The integration test uses a real catalog, generated inputs, controlled fit/calibration
interfaces, an in-memory fixture authorization boundary and isolated synthetic publication/
tracking. It never invokes the real EXP01 pipeline or writes its permanent store.

For this bounded correction, run those modules plus the existing EXP01 path/authorization
checks and affected historical preparation-reader regressions. Run Ruff/format/mypy only
on changed Python files and links only for changed documentation. A single temporary
wheel/import correspondence check covers the new installed module; do not reinstall the
operational runtime. GitHub owns full Python/contract/E2E validation.

### EXP01 real runner corrective infrastructure

The registered real graph, metadata descriptor, explicit approval/reservation,
paired engine and result tracking map to `test_exp01_runner.py`,
`test_exp01_runner_tracking.py`, the existing EXP01 onset/tracking tests,
configuration contracts and base bootstrap. Use the pinned foundation environment:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
python -m pytest tests/unit/test_exp01_runner.py tests/unit/test_exp01_onset.py tests/contracts/test_kedro_configuration.py tests/unit/test_repository_bootstrap.py tests/integration/test_exp01_runner_tracking.py tests/integration/test_exp01_tracking.py -q
```

Run the full unit/contracts plus MLflow/EXP01 and permitted synthetic E2E selection
in a fresh source checkout without private `data/` or persistent `tmp/`. Preserve
its existing three absent historical-EDA skips and default private-test
deselections as separate limitations. Do not invoke real replay, private parity,
real EXP01 or `--require-migration-evidence`. Every tracking test owns a fresh
`repo_tmp_path` store. Confirm the permanent replay-MLflow file hashes before and
after validation. Synthetic probe parents/children remain explicitly synthetic.

Also run Ruff lint/format, the explicit mypy command above, maintained-script
quality, Markdown links, `pip check`, secret/runtime scans, diff checks,
repo-only/scoped-plan/all-plan DWP checks, an isolated base wheel installation
and an isolated modeling/tracking wheel installation with frozen constraints.
Build/register the actual installed graph outside source import paths. Run only
foundation startup for the base wheel and generated synthetic probes for optional
extras. Exercise metadata-only preflight on the local declared source paths and
read-only permanent tracking destination; no private-content read is allowed.
The handoff owns the [future command and approval boundary](operations/exp01-runner-handoff.md).

### EXP02: estabilidad de etiquetas y episodios

El alcance nuevo se mapea a `tests/contracts/test_exp02_protocol.py`,
`tests/unit/test_exp02_labels.py`, `tests/unit/test_exp02_prediction.py` y
`tests/integration/test_exp02_{execution,catalog,tracking}.py`. Las regresiones
compartidas pertinentes son rutas/catálogo de EXP01, registro de experimentos,
configuración y bootstrap. Ejecutar únicamente esa selección durante el desarrollo;
las suites completas siguen siendo responsabilidad de GitHub.

Las pruebas de EXP02 usan fuentes generadas, adaptadores fijos y tiendas temporales
propias. El recorrido real se ejercita con admisión y ajustes sustituidos por fixtures:
ninguna llamada de interfaz es un fit de estimador o calibrador. El guard de pruebas
rechaza acceso al almacenamiento permanente. Las reservas y aprobaciones de prueba
son ficticias y se eliminan con su directorio aislado.

El preflight operativo, la admisión privada, la preparación del runtime y la ejecución
científica no son gates de esta implementación. El [diseño de EXP02](product/experiments/EXP02_label_stability/DESIGN.md)
conserva el comando futuro y los gates de Mauricio y del revisor independiente.

## EXP03 guarded selective feature ablation

[EXP03 design](product/experiments/EXP03_feature_ablation/DESIGN.md) owns the
scientific definitions; the revised protocol/matrix derive sixteen unique sets,
four primary/twelve secondary ablations, two bounded T+2 controls, 408 fits and
102 terminal cells. [Implementation traceability](product/experiments/EXP03_feature_ablation/IMPLEMENTATION.md)
maps the complete generated-only acceptance surface. EXP01 is prioritized experiment 1;
EXP02 implements label sensitivity 5/7/9; EXP03 implements prioritized experiment 3.

Changed EXP03 preparation/contrasts/decisions/tracking map to `tests/unit/test_exp03.py`,
`tests/integration/test_exp03_tracking.py` and `tests/integration/test_exp03_input_integration.py`.
The revised feature/evaluation/persistence/benchmark/reporting suites are all
selected by `tests/unit/test_exp03*.py`, with objective-aware tracking validation in
`tests/integration/test_exp03_revision_tracking.py`.
Use modified-file Ruff/format/mypy, relevant contracts, Markdown links and diff
privacy checks. The full CI selection includes the new integration module.

Source-free structural preflight (does not authorize real execution):

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow KEDRO_DISABLE_TELEMETRY=yes kedro run --pipelines=exp03_preflight --params=profile=exp03_preflight,tracking=enabled,experiment_id=EXP03
```

It always returns `execution_ready=false`. It validates declared three-year OOF
support; actual common-cohort support is checked only after human authorization,
before reservation/fits/tracking. A shared-store preflight is an operational task
for a later authorized session; tests select isolated temporary stores.

Generated-only probe, zero real fits/calibrations/reservations:

```bash
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipelines=exp03_synthetic --params=profile=exp03_synthetic,tracking=disabled,experiment_id=EXP03
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest tests/unit/test_exp03.py tests/integration/test_exp03_tracking.py tests/integration/test_exp03_input_integration.py -q
```

Future real execution remains **NOT AUTHORIZED**. Mauricio must separately provide
`SAT_DENGUE_EXP03_APPROVAL`, a repository-tmp JSON record with exact schema
`exp03-execution-approval-v2`, EXP03 identity, authority Mauricio, independent
reviewer, protocol/Git/data/configuration hashes and the four explicit execution,
comparator-refit, variant-refit and retrospective-availability flags. It must bind
a new clean reviewed commit/environment. Never reuse historical records or pins.

Only after separate authorization, the future command is:

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow SAT_DENGUE_EXP03_APPROVAL=tmp/reviewed-exp03-approval.json KEDRO_DISABLE_TELEMETRY=yes kedro run --pipelines=exp03 --params=profile=exp03,tracking=enabled,experiment_id=EXP03
```

Results stay under `tmp/kedro-migration/exp03-runs`, disjoint from tracking. The
single parent `exp03-frontier-mlflow-v1` artifact contains closed aggregate cells
and contrasts, protocol/bundle/hash binding and canonical cell references. Native
OOF audit rows/municipality strata never enter MLflow. G5/champion remain unchanged.


Revised EXP03 focused acceptance (generated sources only):

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest tests/unit/test_exp03*.py tests/integration/test_exp03*.py -q
.venv/bin/python -m sat_dengue.experiments.exp03_contract --check
```

`exp03_generated_result` is a session-owned generated native-estimator fixture.
Its non-executable JSON/base64 cache is keyed by scientific source bytes under
ignored `tmp/exp03-generated-fixtures`; no private-source or tracking cache is
read. Bundle semantic reconstruction, privacy and tamper tests still execute.
A missing `B_primary` blocks before scientific source reads, reservations or fits.
Protocol 2.0.1 fixes that number at 1.0; obtaining real-run authorization remains a future task.
For the budget-only correction, use `tests/contracts/test_exp03_budget.py`, the
non-fit budget/admission/preflight cases in `tests/unit/test_exp03.py`, and the
pending-budget regression in `test_exp03_input_integration.py`. Do not invoke the
generated native-estimator fixture, scientific runtime or operational preflight.

## Test-suite value reduction acceptance

The full CI command is the single command in `.github/workflows/ci.yml` under
`Run units, contracts including test_repository_disposition.py, and synthetic E2E`.
It includes EXP02 catalog/execution/tracking and EXP03 input/tracking/revision
acceptance. `test_exp03_admission.py` is absent on the main baseline; its unmerged
production implementation is not imported as part of test cleanup. Private
`migration_evidence` remains deselected by default and is not public CI evidence.

