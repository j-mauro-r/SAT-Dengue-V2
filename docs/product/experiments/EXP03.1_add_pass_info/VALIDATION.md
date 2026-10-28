# EXP03.1 validation evidence

Status on 2026-10-27: **FOCUSED ACCEPTANCE PASS; ONE ENVIRONMENT-SPECIFIC FULL-SUITE FAILURE DOCUMENTED**. All executable examples are `synthetic_generated_data`; no real science was run or authorized.

Required final gates: focused contract/unit/integration tests; scoped Ruff check/format and mypy; JSON/YAML and canonical generator; validation-surface classification; Markdown links; `git diff --check`; diff-only secret/private-path scans; repo-only, scoped-plan, and separately reported all-plan conformance.

| Evidence | State | Result |
| --- | --- | --- |
| Focused contract/unit/integration suite | PASS | 25 passed |
| Scoped Ruff check and format | PASS | all selected files clean/formatted |
| Scoped mypy | PASS | 11 source files, no issues |
| Canonical generator and JSON/YAML parsing | PASS | protocol SHA-256 `ecc9299d56169e7a95df29d02f189a607544f6385f8473c9536f342eb4e8e531`; 96 total cells, 24 terminal cells |
| Complete ignored synthetic example | PASS | `synthetic_generated_data`; bundle SHA-256 `90724eab2a5157384bd37902b7b3578a85b1c160a50a8c5b569b9d12e1a72ac2`; zero real effects |
| Validation-surface classifier | PASS | conservative full gate selected for Kedro graph, tracking, scientific contract, docs and an unknown new path |
| Registry/disposition contracts excluding local protected inventory | PASS | 56 passed, 1 deliberately separated environment-specific case |
| Markdown links and `git diff --check` | PASS | no broken links or whitespace errors |
| Diff-only secret and private-path scans | PASS | no findings |
| Repository-only DWP conformance | PASS | 17 checks |
| `PLAN_050_exp03_1_trajectory` conformance before Final Review | PASS | 7 mandatory checks; expected active-plan advisories only |
| All-plan DWP conformance | FAIL (historical, unrelated) | existing unresolved PLAN_012 security-review finding and legacy mixed lifecycle in `PLAN_stage2_data_understanding_initial_recognition`; not waived |
| Full public unit/contract/integration suite | FAIL (local private-inventory harness only) | 1,088 passed, 12 deselected; only `test_protected_inventory_when_locally_supplied` failed because the locally supplied private baseline pins the prior bytes of the explicitly updated active decision register `traking-concluciones.md`. The data-free CI path skips that private preservation assertion. The protected baseline was not edited or bypassed. |

Independent diff/security review and remote CI remain **UNVERIFIED** until the Final Review and PR tasks complete.

