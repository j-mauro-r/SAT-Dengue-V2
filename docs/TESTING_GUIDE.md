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
- `ruff check tests`
- `ruff format --check tests`
- `mypy tests`
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

Active data-integrity safeguards: `.venv/bin/python -m pytest tests/unit/test_january_2020_climate_incorporation.py tests/unit/test_stage2_manifest_traceability.py -q`. These verify incorporation/traceability behavior on test fixtures; they do not download or reintegrate source data. Run the full unit suite, Ruff checks, `mypy tests` and `scripts/check_markdown_links.py` under the foundation gate policy above. Also lint/format any touched Python script.

For this archival migration, local PLAN_012 validates the path/hash manifest, byte-identical notebooks, restricted report transformations, unchanged script logic, original data/evidence hashes and preserved historical plan records. It is a one-time migration check, not a new recurring scientific gate. New DWP work must pass scoped conformance; report pre-existing legacy-plan global failures separately without rewriting their records or weakening validation.

## Clean-checkout CI installation

The Stage 2 project distribution is metadata-only: setuptools has an explicit empty package list, so `data/` and `notebooks/` are never auto-discovered as installable packages. The `dev` extra declares NumPy and pandas because the synthetic panel tests import them. This changes neither data publication policy nor analysis-population rules.

Validate packaging changes from a fresh Git archive/checkout in a separate temporary environment: install `.[dev]`, run `pytest tests/unit -q`, `ruff check tests`, `ruff format --check tests` and `mypy tests`; build a wheel with `pip wheel --no-deps .` and inspect that it contains no source datasets/notebooks. The three tests backed by ignored private analytical outputs are expected to skip in a public checkout; synthetic regressions still run. Keep a separate local full-suite check when those outputs are available. Never copy private datasets into CI to make these checks pass.

## Training preparation inputs (milestone 1)

The [preparation contract and workflow](product/stage-3/README.md) map
`scripts/training_preparation/**`, notebook 04 and its preparation contract to
`.venv/bin/python -m pytest tests/unit/test_training_preparation.py -q`.
Synthetic tests reject schema/type/nullability errors, duplicate keys, missing
months/municipalities, invalid categories/coverage, forbidden predictors and
fingerprint tampering. No private input is needed for those tests.

Run `.venv/bin/python -m scripts.training_preparation.audit` for read-only local
validation of existing notebook 03 products, including manifest SHA-256 checks.
This requires the private local products and never regenerates them. For a
preservation audit, provide `--baseline <path>` with a pre-task fingerprint map.
Execute notebook 04 cells sequentially with the repository environment; only
aggregate evidence and contract roles are displayed. Run the full foundation
gates, lint/format the new modules and check Markdown links for this surface.
Use `--basetemp=tmp/pytest-training-preparation` when test artifacts must remain
inside the repository. Report historical global DWP failures separately from
`conformance.sh --plan .dwp/plans/PLAN_018_training_data_preparation`.

## Deterministic development features (milestone 2)

The same `tests/unit/test_training_preparation.py` also covers two-municipality
isolation, row-order invariance, December/January boundaries, exact missing-month
lookups, first observations, valid negative changes, complete T/T−1/T−2 means,
January-phased cycles, future perturbation, reserved outcome masking, preservation
of current climate signs, immutable atomic publication, corruption rejection and
invalidation after data/config/code changes. Use repository-local `--basetemp`.

Run the following to publish an immutable development bundle and then recompute
all bytes, audit real horizon eligibility against the existing policy, and verify
original scientific hashes:

```bash
.venv/bin/python -m scripts.training_preparation.development
.venv/bin/python -m scripts.training_preparation.development --verify \
  --baseline .dwp/plans/PLAN_018_training_data_preparation/analysis_results/input_baseline.json
```

No reserved reference features or model training is generated. Full foundation
gates remain required. Check new modules with
`.venv/bin/mypy --explicit-package-bases scripts/training_preparation`, plus
required `mypy tests`, Ruff lint/format and Markdown links. Notebook 04 must remain
code-only and execute sequentially; its summaries are development aggregates only.

## Temporal partitions, inference preparers and executed notebook (milestone 3)

`tests/unit/test_training_temporal.py` maps the temporal/preprocessing/execution
modules to eight synthetic window/horizon comparisons against the existing
reference, causal target/origin boundaries, training-only parameters under
validation perturbation, explicit missing/unknown categories, JSON/CSV inference
roundtrips, rejected Y/controls and stable notebook code/output identities.
Run alongside all earlier preparation regressions and the full foundation gate:

```bash
.venv/bin/python -m pytest tests/unit/test_training_preparation.py tests/unit/test_training_temporal.py -q
.venv/bin/python -m scripts.training_preparation.temporal
.venv/bin/python -m scripts.training_preparation.temporal --verify \
  --baseline .dwp/plans/PLAN_018_training_data_preparation/analysis_results/input_baseline.json
.venv/bin/python -m scripts.training_preparation.notebook_execution --execute
.venv/bin/python -m scripts.training_preparation.notebook_execution --verify
```

The baseline flag uses local plan evidence and may be omitted on another checkout;
manifest/hash verification still applies. Notebook commands require the optional
`notebook` extra declared in pyproject; synthetic tests do not require private data
or notebook runtime packages. Use repository-local `--basetemp` for pytest. Run
Ruff and explicit-package-bases mypy for all preparation modules, required
`mypy tests`, Markdown links, policy scans and scoped DWP conformance. Saved
notebook outputs must match the current artifacts and an actual new-kernel receipt.

No final-block objective may enter adjustment or comparisons. All eight real
partitions must agree with reference key sets; 456 T+1 and 380 T+2 validation
examples per cutoff are expected for the current data, not forced sample limits.
Configured six-month target intervals and actual horizon-specific origin/target
support are reported separately. No predictor training is part of these checks.

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
  native-bundle identity, historical source recovery and 4.6/4.7 compatibility.

Run from the repository root with the existing `.venv` (no installation into it):

```bash
export PATH="$PWD/.venv/bin:$PATH"
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_DEBUG_TEMPROOT="$PWD/tmp/kedro-migration"
python -m pytest tests/unit -q
python -m pytest tests/integration/test_migration_parity.py -q
python -m pytest tests/integration/test_migration_parity.py -k "baseline or compatibility" --require-migration-evidence -q
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
