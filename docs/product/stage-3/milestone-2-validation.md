# Milestone 2 validation — 2026-10-20

Scope: deterministic candidate feature construction only. The existing branch `Stage3/Data-Preparation` was clean at milestone-2 starting revision `66b9116b95ab08707a4e471ec0f5652443b502e6`. No competing branch, plan or notebook was created. PLAN_018 revision 2 (`30b87813f2d7…`) records the explicit user authorization, exact formulas, new persistence surface and observed artifact gate. Milestone 1 evidence remains accepted; no unmet milestone-1 requirement was found. Its reader gained a development boundary for this task, without changing default input-audit behavior.

The same local plan is `.dwp/plans/PLAN_018_training_data_preparation/`. Its authorization is in `AUTHORIZATION_M2.md`; original and revised contracts, journal and gate evidence are preserved. Milestone 3 and phase Final Review remain unexecuted. G2 remains open; no training, push, PR or merge was performed.

| Check | State and evidence |
|---|---|
| Preparation synthetic tests | PASS — 48 tests; 14 added since milestone 1; DWP AC-derived gate runs the same test file |
| Full unit suite | PASS — 151 tests, eight existing Stage 2 warnings; `tmp/m2_full_unit_tests.log` |
| Ruff lint / format | PASS — tests and all preparation modules |
| Types | PASS — `mypy tests`; `mypy --explicit-package-bases scripts/training_preparation` |
| Markdown links / diff whitespace | PASS — documented checker and `git diff --check` |
| Notebook 04 | PASS — all five code cells executed sequentially; code-only; `tmp/m2_notebook_execution.log` |
| Real artifacts / byte determinism | PASS — regenerated payloads match all three tables and manifest exactly; AC-derived-artifacts uses `development --verify` |
| Scientific preservation | PASS — all 17 original baseline SHA-256/byte records unchanged before and after verification; no input, Y, current zone or percentile rewrite |
| Plan-specific DWP | PASS — same v7 plan and preserved criterion evidence; guarded closure covers only T-derived |
| Global DWP | FAIL — same two historical issues: PLAN_012 critical-text detector and legacy initial-recognition mixed lifecycle; no older plan edited |
| Policy / secret scans | PASS for changed files; whole-tree policy scan empty. Two unchanged secret-pattern matches are Pillow embedded font bytes and the historical PLAN_004 scan log referencing the same match, as classified in milestone 1. Filename-only scans avoid logging candidate secret values. |

Tests cover two municipalities and shuffled rows, December/January transitions, missing calendar months, first observations, valid negative changes, exactly T/T−1/T−2 with all values required, future perturbation, positive past lags only, current climate signs, reserved reference filtering and target masking, input nonmutation, deterministic serialization, atomic publication failure, immutable corruption/error handling and distinct identities after data/config/code changes. A synthetic test also confirms changing masked reserved target values cannot change persisted controls or eligibility counts. Required checks remain enabled; existing standalone readiness functions are reused through a typed runtime adapter.

## Development support and missingness

The feature table has **16,948 rows**, **76 municipalities**, **28 candidate columns** (12 retained plus 16 derived), from **2006-06 through 2024-12**. All 223 reference months per municipality are retained, including history preceding supervised eligibility. There is no feature construction or outcome summary for reserved reference months.

| Derived columns | Missing rows per column | Explanation |
|---|---|---|
| dengue_lag_1; grave_lag_1; dengue_cambio_1m | 76 | First observation lacks T−1 |
| dengue_lag_2; grave_lag_2; dengue_media_3m | 152 | First two observations lack complete support |
| dengue_lag_3 | 228 | First three observations lack T−3 |
| zona_canal_lag_1 | 4,636 | Existing zone warm-up plus one-month lag |
| lluvia_lag_1; temperatura_lag_1; rocio_lag_1; escorrentia_lag_1 | 608 | Climate coverage begins 2007-01 plus one-month lag |
| lluvia_lag_2; temperatura_lag_2 | 684 | Climate coverage begins 2007-01 plus two-month lag |
| mes_sin; mes_cos | 0 | Defined from reference calendar month |

Each retained current climate column has 532 missing development rows; the existing current zone has 4,560. Current counts have no missing values. These absences are preserved, never filled or removed. `dengue_media_3m` includes T and requires T−1/T−2; January calendar phase is zero. Negative changes and climate signs remain valid. No demographics, clipping, learned transforms or variable selection were added. Candidate variables are not demonstrated predictive utility.

## Existing policy and real eligible examples

Source ANO metadata yields notification-year backing 2007-01 through 2025-12. The existing conservative five-year-history policy therefore allows **target months 2012-01 through 2024-12**. These bounds are derived by the existing helper, not selected to match desired counts. Eligibility is audited after all development antecedents are built and never used to drop their earlier history.

| Horizon | Eligible examples | Reference months | Target months | Eligible rows with any missing candidate |
|---|---|---|---|---|
| T+1 | 11,856 | 2011-12 through 2024-11 | 2012-01 through 2024-12 | 0 |
| T+2 | 11,856 | 2011-11 through 2024-10 | 2012-01 through 2024-12 | 0 |

Both key sets agree exactly with the existing independent supervised selector. Reserved targets used: **zero**. Y, evaluability and target traces remain controls, never X. Outcome/percentile/history/evaluability controls whose target enters 2025 are masked in the development view; known target dates and exclusion flags remain. Original input values are unchanged. No final-block label rates, distributions, metrics or associations were inspected. These counts do not demonstrate operational historical availability, reporting completeness or predictive usefulness.

## Persisted artifacts

Current code/config/data identity: `fb0e7e2463e8463535585791333306138f0e9c09ba18667d37f3b9e80c5c4623`.

Directory: `data/processed/training_preparation/development/fb0e7e2463e8463535585791333306138f0e9c09ba18667d37f3b9e80c5c4623/` (ignored local data).

- `features.csv`: 28 candidate columns only; SHA-256 `7464360f83e419aa573b1d1e9bc9717a2c58b1150a3ff32c3a98b59450abfc00`.
- `keys.csv`: municipality/month keys in shared sorted row order; SHA-256 `8c5da8ca8c055e84478e95c9a5c96759efcac55f2708db96b1cf6fa540874a25`.
- `controls.csv`: keyed non-predictor metadata, development Y and horizon flags; SHA-256 `dbf436da551a59f5a076927609b0b964b32f7d97c9245d9d7853f21473af36e9`.
- `manifest.json`: exact input/config/code/runtime identity, roles, support, missingness, eligibility and table hashes.

The source/config/code/runtime identity is content-addressed. Default `reuse_identical` recomputes all bytes before reuse; policy `error` rejects existing output. No existing identity is replaced or repaired silently. Staging/file fsync plus atomic directory publication prevents partial bundles from becoming visible. Prior identities are retained as provenance and cannot be reused under the current identity. No personal absolute path is required by code or manifest.

Skills disposition: none — this is a product feature pipeline, not an agent workflow. Documentation decision: update the preparation contract/workflow, testing map and this evidence. Security/data self-check: no new dependencies, private case-row publication, credentials or authorization boundary changes. Independent phase review remains pending, not claimed by implementer checks.

Milestone 3 handoff: consume the verified current bundle, retain its key/control separation and apply horizon-aware temporal folds before any learned transforms. Reconcile target boundaries per horizon, keep 2025 onward reserved, never select predictors from final-block results, and do not treat retrospective consolidated data as proven as-of operational availability. Resume only on explicit human authorization.
