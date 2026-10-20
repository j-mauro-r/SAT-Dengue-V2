# Milestone 1 validation — 2026-10-19

Scope: structure, contract and input validation only. Initial branch `main` was clean at `97f0aeedf045474a320fb26c1f31eea849edb97e`, including untracked status. Work branch: `Stage3/Data-Preparation`, created from that revision. No existing local changes required relocation or overwriting. No push, PR or merge was performed.

The explicit human request authorizes this bounded scaffold while G2 remains open. It does not approve training, change the canonical dictionary or freeze a scientific contract. The phase plan is local `.dwp/plans/PLAN_018_training_data_preparation/` (v7 contract `bc93a144797f…`); its immutable task acceptance, authorization note, baseline hashes, journal and runner gate logs remain there. The general phase and its Final Review remain incomplete.

| Check | Result | Evidence |
|---|---|---|
| Synthetic preparation tests | PASS — 34 tests | `tests/unit/test_training_preparation.py`; DWP `AC-structure` runner log |
| Full unit suite | PASS — 137 tests | `tmp/training_preparation_full_tests.log`; eight existing Stage 2 deprecation warnings |
| Ruff lint and formatting | PASS | `ruff check tests scripts/training_preparation`; `ruff format --check tests scripts/training_preparation` |
| Types | PASS | `mypy tests`; `mypy --explicit-package-bases scripts/training_preparation` |
| Policy/secret scans | PASS — no matches in changed files; full repository matches classified below | `tmp/training_preparation_policy_scan.log`; `tmp/training_preparation_secret_scan_paths.log` |
| Markdown links | PASS | `python scripts/check_markdown_links.py` |
| Notebook execution | PASS — all five code cells executed sequentially | `tmp/training_preparation_notebook_execution.log`; notebook contains no Markdown/raw cells |
| Existing product validation | PASS — 17,936 rows × 51 columns; 76 municipalities; 2006-06 through 2026-01 | DWP `AC-preservation` runner log and `tmp/training_preparation_audit.json` |
| Scientific preservation | PASS — 17 pre-task fingerprints unchanged | Plan `analysis_results/input_baseline.json`; raw files, source references, processed products, construction contract/manifest/traces and notebook 03 included |
| Scoped DWP conformance | PASS | `conformance.sh --plan .dwp/plans/PLAN_018_training_data_preparation` |
| Global DWP conformance | FAIL — two pre-existing historical issues | PLAN_012 completed-review critical-text detector; legacy initial-recognition mixed lifecycle. No historical plan modified. |

The existing panel retains 608 missing climate rows and 4,560 non-evaluable labels per horizon. These are reported, not filled, removed or redefined. Input dimensions and SHA-256/byte records are verified against the notebook 03 construction manifest. Aggregate coverage is not evidence of surveillance completeness or historical operational availability.

The combined invocation `mypy tests scripts/training_preparation` encountered namespace duplication because the existing `scripts/` directory is a namespace package. Required `mypy tests` passes; explicit package bases validate the new modules separately without changing repository packaging.

Skills disposition: none; these are product modules, not a reusable agent workflow. Documentation decision: add a preparation-specific contract/workflow and testing map, indexed from the documentation entry point. Security/data self-check: no private case rows are displayed or added, input paths cannot escape the repository, inputs are read-only and no dependencies or auth boundaries changed. This implementer check is not independent review; the phase Final Review remains pending.

Milestone 2 resumes only after explicit authorization. Implement the declared lag/change/retrospective-mean/previous-zone/calendar families with past-only municipality isolation and future-perturbation tests. Set the rolling window/minimum observations explicitly and preserve warm-up missingness. Milestone 3 must isolate horizon-aware training folds and the reserved block before any learned preprocessing; neither milestone has run.

The full secret-pattern scan used `rg --no-ignore --hidden --follow -l` with the repository-prescribed patterns and exclusions, replacing a slow recursive grep run. Filename-only output avoids logging potential secret values. Its two matches are a random AWS-ID-shaped substring inside Pillow’s embedded base64 font and a historical PLAN_004 scan log referencing that same Pillow line; AST inspection located the match inside `base64.b64decode`. No changed file matched. The policy exclusion scan found no matches. Neither dependency nor historical plan was modified.
