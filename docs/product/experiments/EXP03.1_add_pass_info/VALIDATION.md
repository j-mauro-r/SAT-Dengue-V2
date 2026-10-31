# EXP03.1 validation evidence

Current documentary status (2026-10-31): **`CLOSED_WITH_EXACT_OBSERVABLE_REPLAY`**.
The dated implementation evidence below is retained; the completed replay
validation is recorded in the final section. G5 remains `NOT_APPROVED` and
champion remains `not_selected`.

Status on 2026-10-27: **FOCUSED ACCEPTANCE PASS; ONE ENVIRONMENT-SPECIFIC FULL-SUITE FAILURE DOCUMENTED**. All executable examples are `synthetic_generated_data`; no real science was run or authorized.

Required final gates: focused contract/unit/integration tests; scoped Ruff check/format and mypy; JSON/YAML and canonical generator; validation-surface classification; Markdown links; `git diff --check`; diff-only secret/private-path scans; repo-only, scoped-plan, and separately reported all-plan conformance.

| Evidence | State | Result |
| --- | --- | --- |
| Focused contract/unit/integration suite | PASS | 26 passed (58 with registry contracts in the post-review run) |
| Scoped Ruff check and format | PASS | all selected files clean/formatted |
| Scoped mypy | PASS | 11 source files, no issues |
| Canonical generator and JSON/YAML parsing | PASS | protocol SHA-256 `46f287468ace7cee7c67220b871cf85a7a9c0670a131d80838d3baf147da0075`; 96 total cells, 24 terminal cells |
| Complete ignored synthetic example | PASS | `synthetic_generated_data`; bundle SHA-256 `8b64af888b31b2edf6dfe3f867371d8c28fb46a0de476ca1b66be240b80adb72`; zero real effects |
| Validation-surface classifier | PASS | conservative full gate selected for Kedro graph, tracking, scientific contract, docs and an unknown new path |
| Registry/disposition contracts excluding local protected inventory | PASS | 56 passed, 1 deliberately separated environment-specific case |
| Markdown links and `git diff --check` | PASS | no broken links or whitespace errors |
| Diff-only secret and private-path scans | PASS | no findings |
| Repository-only DWP conformance | PASS | 17 checks |
| `PLAN_050_exp03_1_trajectory` conformance before Final Review | PASS | 7 mandatory checks; expected active-plan advisories only |
| All-plan DWP conformance | FAIL (historical, unrelated) | existing unresolved PLAN_012 security-review finding and legacy mixed lifecycle in `PLAN_stage2_data_understanding_initial_recognition`; not waived |
| Full public unit/contract/integration suite | FAIL (local private-inventory harness only) | 1,088 passed, 12 deselected; only `test_protected_inventory_when_locally_supplied` failed because the locally supplied private baseline pins the prior bytes of the explicitly updated active decision register `traking-concluciones.md`. The data-free CI path skips that private preservation assertion. The protected baseline was not edited or bypassed. |

Independent diff/security review: **PASS AFTER FIXES** — five medium and one low finding resolved; no unresolved critical/high/medium finding. Remote CI remains **UNVERIFIED** until the PR runs complete.

## New operational-path evidence

The following checks cover only the new EXP03.1 operational boundary code and
use in-memory fixtures, fit/calibration doubles, and a temporary SQLite
tracking store under repository `tmp/`. They do not execute the experiment or
read scientific input files.

| Exact command | Result |
| --- | --- |
| `python -m py_compile src/sat_dengue/configuration.py src/sat_dengue/experiments/exp03_1_preflight.py src/sat_dengue/experiments/exp03_1_runner.py src/sat_dengue/experiments/exp03_1_reporting.py src/sat_dengue/experiments/exp03_1_evaluation.py src/sat_dengue/experiments/exp03_1_validate.py src/sat_dengue/tracking/exp03_1.py src/sat_dengue/datasets/exp03_1.py src/sat_dengue/pipeline_registry.py tests/integration/test_exp03_1_operational.py` | PASS |
| `pytest -q tests/integration/test_exp03_1_operational.py` | PASS — 16 passed; one Kedro advisory about dataset names containing dots. The focused run exercises authorization accept/deny, pre-authorization admission barrier, source-manifest hash tampering, official-coverage zero/unknown semantics, both registered profiles and unknown-ID rejection, tracking-root separation, 96-cell executor with test doubles, controlled M00 reuse/refit planning, complete/incomplete real-bundle checks, bundle-manifest tamper rejection, and temporary-store parent/child correspondence. |
| `git diff --check` | PASS |

No experiment preflight command, scientific-source loader, real or synthetic
experiment, fitted scientific estimator, calibration, permanent MLflow store,
global suite, Ruff, Mypy, CI, DWP, or G5 gate was run during this operational
implementation.


## Replay persistence repair (2026-10-30)

Status: `EXP031_REPLAY_PERSISTENCE_IMPLEMENTED_NOT_EXECUTED`.
The original scientific execution remains the current evidence. G5:
`NOT_APPROVED`; champion: `not_selected`. No EXP03.1 scientific execution,
Kedro execution, real replay, private-source read or permanent MLflow write
was performed. No dependencies, scientific protocol/matrix, EXP04 or scientific
conclusions were changed. DWP was not invoked and no new plan was created.

Validation is limited to five gate types, using generated data, native
round-trips and temporary repository-local tracking stores:

| Gate | Evidence |
| --- | --- |
| Focused EXP03.1 tests | PASS: 58 tests across `test_exp03_1_contract.py`, `test_exp03_1_integration.py`, `test_exp03_1_operational.py` and `test_exp03_1_replay.py`. After retaining source-month audits across the existing preparation merge, only the affected executor test and replay module were repeated: 7 passed. No full suite. |
| Ruff check | PASS: the four touched EXP03.1 modules and two touched test modules. |
| Ruff format check | PASS: the same six Python files. |
| Focused mypy | PASS: the same six Python files; the initial four annotation/suppression findings were corrected. |
| `git diff --check` | Recorded by the final pre-commit check below. |

The native round-trip tests fit only small generated fixtures for GAM,
LightGBM and XGBoost. Fit entry points are forbidden during reload. They cover
raw and calibrated scores, null/whole-tie thresholds, exact alerts, precision,
row order/dtypes, source and event-month provenance, tamper/overwrite/path
rejection, all four comparison outcomes, discrete/bin/tie mismatches, the
96-cell companion inventory, and historical v1 validation compatibility.
The existing executor double confirms 96 model fits, 96 calibrator fits,
96 threshold selections and exactly 288 predictor calls with capture enabled.
These are synthetic test counters, not a scientific execution.

The five reproducible validation commands are:

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest tests/contracts/test_exp03_1_contract.py tests/integration/test_exp03_1_integration.py tests/integration/test_exp03_1_operational.py tests/integration/test_exp03_1_replay.py -q
.venv/bin/python -m ruff check src/sat_dengue/experiments/exp03_1_{runner,reporting,validate,preflight}.py tests/integration/test_exp03_1_{operational,replay}.py
.venv/bin/python -m ruff format --check src/sat_dengue/experiments/exp03_1_{runner,reporting,validate,preflight}.py tests/integration/test_exp03_1_{operational,replay}.py
.venv/bin/python -m mypy src/sat_dengue/experiments/exp03_1_{runner,reporting,validate,preflight}.py tests/integration/test_exp03_1_{operational,replay}.py
git diff --check
```

The only targeted pytest retry after the temporal-audit instrumentation change
selected `test_executor_walks_96_cells_with_fit_and_calibration_doubles` and
`test_exp03_1_replay.py`. Ruff/format and mypy were checked on the final Python
content. The initial full focused run had two dependency advisories (Kedro dataset
names and SQLAlchemy's deprecated `noload` strategy), with no failures.
Independent scientific replay equivalence and original intermediate-state
identity remain unverified/not comparable. No new execution approval was created.
Future commands and the exact new approval fields are owned by [RUNBOOK](RUNBOOK.md).

## Validated observable replay and documentary closure (2026-10-31)

Status: **`CLOSED_WITH_EXACT_OBSERVABLE_REPLAY`**. The official read-only
validator returned `status: verified`. This result supersedes the earlier
unverified replay comparison, without changing the historical execution or
the scientific conclusions.

| Identity | Original execution | Preserved replay |
| --- | --- | --- |
| Bundle ID | `afcb8b4a6cb512c1247fc52c5d9786a3f0d245663981a29f8f23ac76873a3e04` | `732a9d7743b4c54d9252adf7095f2c4e2775cd4d6472446d2bd2e41a476927f4` |
| Bundle SHA-256 | `5b3f20a266c5e6aae7d2727a00a2213ea9cc3bc691bac5f02267a3e44edc5619` | `e6c6325dbc948fa0d0a654c3af13f2898f7697747ce19846766311392f76e155` |
| MLflow parent | `a37877c20dbd4b1382567e79e8d89e7b` | `2c932c4bcffa475280cec95f50e1533d` |

The replay records execution commit
`1c5dfd23cb8ebf807c66f68898b61279d65c1cc5` and scientific protocol SHA-256
`46f287468ace7cee7c67220b871cf85a7a9c0670a131d80838d3baf147da0075`.
Its manifest SHA-256 is
`99807fc011228954ffbbda16bb7e7680ea066d44db5dd9c63ca124fd53f321cf`;
the companion manifest SHA-256 is
`78f5764092fad8ec0825a3c35b72a4253c84c8982721a9f1ddf7ba517fdc9e41`.
The preserved paths and exact validation command are:

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -B -m sat_dengue.experiments.exp03_1_validate \
  --bundle tmp/kedro-migration/exp03-1-runs/4fd644502e8fb2bb18155060bba68aedd7fc295cf66e16401b91c44af72781de \
  --bundle-id 732a9d7743b4c54d9252adf7095f2c4e2775cd4d6472446d2bd2e41a476927f4 \
  --tracking-root tmp/kedro-migration/exp03-1-replay-mlflow \
  --original-bundle tmp/kedro-migration/exp03-1-runs/007f54d4ef171db3ba10f7ad5a04c00aa5ebf5ff886629a111285c5b1923e928
```

Result: **PASS — `EXACT_OBSERVABLE_REPLAY`**, 96 comparable cells,
60,207 comparable predictions, 96 linked child runs, and
`differences: []` (zero observable differences).
The validator reports
`comparison_correction: canonical_numeric_type_normalization_v1` and
`stored_comparison_status: REPLAY_MISMATCH`. The correction normalizes
equal-valued numeric types when comparing persisted observables; the stored
bundles, manifests, scores, thresholds and comparison receipt were not edited.

Absent original predictors, preparers, calibrators, raw/intermediate scores,
training/role membership, score temporal provenance, selection tie groups,
threshold-selection details and observed environment remain `NOT_COMPARABLE`.
The replay's saved objects and reload checks establish its own reproducibility;
they do not establish identity with original states that were never persisted.
The complete historical-state disposition is retained in the
[EXP04 baseline manifest](../EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/BASELINE_MANIFEST.json).

EXP03.1 needs no further execution for this documentary closure. Q1, Q2, Q3
and their predictive conclusions remain unchanged. EXP04's mature OOF history
is a separate requirement; observable replay does not resolve it or authorize
scientific execution. This closure ran no experiment, fit, calibration or
threshold selection, read no private scientific sources and made zero MLflow
writes. G5: `NOT_APPROVED`; champion: `not_selected`.
