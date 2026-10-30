# EXP03.1 validation evidence

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
