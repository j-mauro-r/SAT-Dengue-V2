# Stage 4 — shared references and XGBoost candidate

The first bounded delivery implements a shared pipeline over verified Stage 3 temporal artifacts and these two references. Delivery 2 adds the XGBoost candidate described below:

- Persistence: deterministic binary alert derived from current endemic-zone state.
- Train prevalence: constant probability estimated from `Y_train` per window/horizon.

The reference-only delivery does **not** train XGBoost, LightGBM or GAM; the delivery2 section below adds the first XGBoost candidate. It does not close G4, and it does not retroactively close G2/G3.

## Scope and inputs

- Stage 3 source contract: [training_preparation_contract_v1.json](../stage-3/training_preparation_contract_v1.json)
- Stage 4 contract: [model_engineering_contract_v1.json](model_engineering_contract_v1.json)
- Notebook orchestrator: [05_baseline_models.ipynb](../../../notebooks/05_baseline_models.ipynb)
- Pipeline modules: [scripts/model_training](../../../scripts/model_training)

The pipeline verifies Stage 3 temporal artifacts from manifests and hash checks before loading any window. It never selects folders by alphabetical order or "latest" naming.

## Reference behavior

1. Persistence
- Formula: `predict_excess_t_plus_h = 1 if zona_canal_t == EXCESO else 0`.
- Unknown/missing state rows are marked non-evaluable.
- Outputs are deterministic alerts, not calibrated probabilities.

2. Train prevalence
- Formula: `mean(Y_train)` for each cutoff-horizon window.
- Probability is constant on the corresponding validation rows.
- Event metrics for this reference remain non-evaluable unless a threshold policy is declared in a future delivery.

Planned future reference not in this delivery: Poisson baseline.

## Metrics in this delivery (corrected evaluation)

Primary metrics:
- `average_precision`
- `onset_sensitivity` (detected/total)
- `false_alarm_ratio` (incorrect alerts / emitted alerts)
- `brier` (probabilistic outputs only)

Event definitions are explicit in the contract:
- onset definition
- anticipation semantics
- evaluable population
- unknown-period treatment

Average Precision is non-interpolated: each distinct descending score threshold contributes its recall increment times its precision. All tied observations enter together. A constant score with both classes has AP equal to the evaluated positive fraction, regardless of row order. Empty/single-class populations remain non-evaluable. Invalid/nonfinite values raise; missing required predictions make the whole selected-population AP unavailable, with counts, rather than silently scoring a reduced sample.

Onsets are constructed independently from predictions using approved observed excess at the target month S and exactly S−1, from the hash-verified Stage 3 development bundle. The preceding month may lie outside validation. For T+2, S−1 is T+1, not the origin. Missing months are not replaced by the prior available record. Unknown scientific states are explicitly counted/excluded. True onsets, available predictions and detections remain separate: missing predictions never shrink the true-onset denominator. With unavailable alerts, point sensitivity is non-evaluable and detected/all-real-onsets is reported only as a named lower bound. Without an alert threshold, probabilistic event metrics and that lower bound remain unavailable, although actual onsets are counted.

Retrospective context is saved separately in `evaluation_context.csv`; it never enters X, reference fitting, inner searches or threshold selection. Only selected development targets and their required preceding months are consulted. No source Y, channel, percentile or Stage 3 artifact is rewritten. Persistence Brier is non-applicable because its alerts are not calibrated probabilities.

## Commands

```bash
.venv/bin/python -m scripts.model_training.execution --execute
.venv/bin/python -m scripts.model_training.execution --verify
.venv/bin/python -m scripts.model_training.notebook_execution --execute
.venv/bin/python -m scripts.model_training.notebook_execution --verify
```

Artifacts are written under `artifacts/model_training/` (gitignored), with immutable identity directories and byte-verified reuse.

## Approved selection policy

Mauricio approved this policy in the corrective request recorded as DEC-123. The executable declaration is `selection_policy` in the existing Stage 4 contract; no candidate adapter, search or ranking is implemented here.

1. Reject technically ineligible runs first: leakage, invalid/unavailable required predictions, misalignment or unverifiable artifacts.
2. Choose hyperparameters by highest mean AP over temporal inner-training splits. Break numerical ties by lower mean Brier on the same splits, then simpler within-family configuration.
3. Use fixed absolute tolerance **1e-12**, relative tolerance **0**, against the best AP and then the best Brier. This is a computational tie rule, not statistical equivalence.
4. Declare simplicity before searching: XGBoost compares `(input features, max depth, estimators, max bins)`; LightGBM `(input features, leaves, max depth, estimators, max bins)`; GAM `(interaction terms, total basis functions, smooth terms, negative comparable common scalar regularization)`. Compare lexicographically, smaller first; unlimited depth is infinity. Specify basis/grid parameters before use. Noncomparable families/regularization remain tied on complexity; canonical IDs only stabilize display.
5. Compare fixed candidates externally by mean AP across **all four windows with equal window weight**, separately for T+1 and T+2. Report Brier where probabilistic, per-window stability and territorial results/support alongside it. Do not discard invalid or inconvenient windows to improve rankings.
6. Event sensitivity and false alarms need a declared threshold policy; no arbitrary combined score. Do not repeatedly tune candidates to external validation or consult the reserved final block. Stage 4 ranking is not Stage 5 champion approval.

These reference outputs remain diagnostic. We do not rank deterministic persistence and probabilistic train-prevalence together as if all their metrics were comparable.

## Corrective provenance

PLAN_021 corrects AP tie handling and incomplete onset-calendar context previously accredited in PLAN_020. The old immutable artifacts and historical contract/journal remain preserved; their metrics are superseded for current evaluation, not silently rewritten. Current correction evidence, before/after comparisons and preserved prediction/cohort fingerprints are recorded in the corrective validation section below and PR #15. A successful reference rerun does not approve G2/G3/G4 or predictive utility.

## Corrective validation — 2026-10-20

Fresh-kernel notebook 05 execution completed all five code cells. An independent threshold-count oracle using rational arithmetic and an exact previous-calendar-month dictionary oracle checked all eight windows and 16 reference evaluations. Results below are recomputed from the current cohorts, not acceptance constants. AP columns show old → corrected; onset/detection columns refer to persistence.

| Window | Persistence AP | Train-prevalence AP | Real onsets | Detected onsets | Onset sensitivity |
|---|---:|---:|---:|---:|---:|
| 2018-12_t1 | 0.847487 → 0.755651 | 0.707484 → 0.570175 | 60 → 71 | 0 → 0 | 0.000000 → 0.000000 |
| 2018-12_t2 | 0.851917 → 0.762740 | 0.746580 → 0.615789 | 48 → 60 | 9 → 12 | 0.187500 → 0.200000 |
| 2020-12_t1 | 0.193077 → 0.189474 | 0.056427 → 0.065789 | 14 → 18 | 0 → 0 | 0.000000 → 0.000000 |
| 2020-12_t2 | 0.127419 → 0.125768 | 0.056155 → 0.065789 | 13 → 14 | 0 → 0 | 0.000000 → 0.000000 |
| 2022-12_t1 | 0.799589 → 0.736829 | 0.646797 → 0.578947 | 57 → 74 | 0 → 0 | 0.000000 → 0.000000 |
| 2022-12_t2 | 0.784160 → 0.729737 | 0.674841 → 0.607895 | 41 → 57 | 11 → 14 | 0.268293 → 0.245614 |
| 2024-06_t1 | 0.679558 → 0.643099 | 0.478388 → 0.471491 | 48 → 56 | 0 → 0 | 0.000000 → 0.000000 |
| 2024-06_t2 | 0.617658 → 0.566789 | 0.500982 → 0.463158 | 37 → 48 | 16 → 18 | 0.432432 → 0.375000 |

False-alarm ratios and applicable Brier scores are unchanged in every window. Train-prevalence now records the same true-event counts, but event sensitivity remains unavailable without a threshold; its old zero event denominators represented uncomputed context, not evidence of zero events. Persistence T+1 cannot detect a transition from non-excess at the origin to excess next month under its unchanged rule, explaining its zero onset sensitivity. This is diagnostic behavior, not a new performance claim.

Preservation audit: all **150 protected files** are byte-identical, including original scientific inputs, Stage 3 cohorts/manifests, the old Stage 4 delivery and historical PLAN_020 evidence. New and old `predictions.csv` files are byte-identical (6,688 rows). No candidate was trained and no reserved-block outcomes were analyzed. The corrected bundle adds evaluation-only context without changing predictors or reference fitting.

Local immutable bundle identities:

- Historical: `artifacts/model_training/a3f9f8b26dc72a458279220f0b45c811ce853e93f691a422720de7c4a622c479`.
- Corrected: `artifacts/model_training/21c39298880121e268cb25d9870a3e28319aeb68429ab36b1c027df5ec45acad`.

Local DWP evidence: `.dwp/plans/PLAN_021_stage4_metric_correction/analysis_results/CORRECTION_AUDIT.json`, `metric_comparison.csv` (all 16 reference/window comparisons including false alarms and Brier), preservation snapshot and observed gate logs. Artifacts and detailed local evidence stay gitignored; the public summary contains no individual records.

Validation: 30 focused metric/reference tests and 214 full unit tests; Ruff, formatting, mypy and Markdown link checks pass. Independent native-agent source and artifact review is required before corrective closure. Global DWP historical conformance issues remain separate; this correction does not rewrite historical approvals or approve scientific gates.

## XGBoost candidate — delivery 2

Notebook [06_candidate_models.ipynb](../../../notebooks/06_candidate_models.ipynb)
orchestrates the same verified raw loading, temporal selector, corrected metrics
and immutable persistence used by the references. `candidate_selection.py`
accepts training inputs only; `xgboost_adapter.py` fits native binary CPU histogram
boosters. `candidates.py` adds evaluation and bounded diagnostics after selection.
No source feature, label, cohort or Stage 3 preparer implementation changes.

The existing preparer is fitted afresh with **one-hot categories, no scaling,
no imputation and explicit unknown municipality handling**. Numeric missingness
is rejected; complete eligible inputs do not need imputation. The matrix is
converted to float32 in saved output-column order. Four known zones, missing
and unknown category behavior remain defined by Stage 3. Each inner fold learns
its vocabulary only from its training rows; final fitting learns it from the
permitted outer training. No full-outer preparer is reused inside inner folds.

Install the pinned modeling dependencies with:

```bash
.venv/bin/python -m pip install -r requirements-modeling.txt
.venv/bin/python -m scripts.model_training.notebook_execution --execute
.venv/bin/python -m scripts.model_training.candidate_notebook --execute
.venv/bin/python -m scripts.model_training.candidate_notebook --verify
```

The native API avoids a new scikit-learn dependency. XGBoost 3.0.5 and SciPy
1.18.1 are pinned separately so the fingerprinted Stage 3 project metadata and
its already verified products remain intact. The adapter uses native JSON model
IO as documented in the [XGBoost API](https://xgboost.readthedocs.io/en/release_3.0.0/python/python_api.html)
and [model persistence guide](https://xgboost.readthedocs.io/en/release_3.0.0/tutorials/saving_model.html).
Runtime versions, model configuration, ordered columns and preparation state are
bound to each artifact identity. Never load untrusted native model files.

### Frozen search and evaluation protocol

The contract's `xgboost_candidate` section declares the search before external
results are inspected. Six configurations vary trees (80/160), depth (2/4),
learning rate (0.05/0.1) and L1/L2 regularization (0/1 or 0.1/5). It is a small
predeclared set, not their Cartesian product. Max bins 128 and child weight 5
are fixed. Seed 42, one CPU thread, full row/column sampling, no early stopping,
no class weighting and no external eval-set are used.

Each outer window/horizon has two six-month inner validations, fitted at its
cutoff minus 12 and minus 6 months. The existing temporal selector requires
training targets observable through each fit cutoff, validation origins at or
after it and targets within the declared interval. This gives six effective
validation target months for T+1 and five for T+2; predictions are issued
successively at their individual origins. Internal selection follows the
**unchanged approved selection_policy**. Residual ties retain all tied IDs;
a canonical representative does not establish scientific superiority. Chosen
parameters are refitted using only the corresponding outer training window.
The full delivery budget is **96 internal fits plus eight outer fits**.

External targets/cohorts remain the eight existing partitions (456 T+1 and
380 T+2 examples per cutoff for current inputs); final-block targets from
2025-01 never enter selection or evaluation. External data cannot influence
hyperparameters, iteration count, preparation, weighting or alert thresholds.
There is no approved operational alert threshold: XGBoost event sensitivity and
false-alarm ratio are explicitly unavailable, with scientific onset counts
retained by the shared evaluator. No event context enters model fitting.

### Saved evidence and inference

Each immutable candidate bundle under `artifacts/model_training/xgboost/`
contains eight native JSON models and train-only preparers, chosen parameters,
all internal fold scores/boundaries/key fingerprints/preparation states and
keyed internal predictions, external keyed probabilities, the four shared
metric records, reference comparisons and separate evaluation context.
Source datasets are referenced through their existing manifests, not copied.

Health outputs include invalid/constant predictions, resubstitution train versus
external AP/Brier, per-window variation, per-territory scores and class support,
fixed-bin reliability summaries and elapsed search/fitting time. Small or
single-class territorial groups may have no AP; they are retained with support.
Training scores are optimistic diagnostics, not selection evidence. Reliability
bins are descriptive and no calibrator is fitted. Retrospective data still do
not establish historical operational availability.

Reuse requires matching inputs, contract/configuration, code, dependencies and
runtime identities, verified payload hashes and exact native-model/preparer
prediction reproduction. Verification never fits. Measured execution time is
stored with the initial run and is not expected to be byte-identical across
independent retraining. Old reference and candidate identities remain intact.
The common code changes require refreshing notebook05's identity; this does not
change the corrected definitions or reopen PLAN_021.

Technical execution and scientific improvement are reported separately. No
champion is selected and G4/G5 remain open. Prompt3 must add its separately
scoped candidate using this protocol, without tuning to these external results.

### Executed candidate results — 2026-10-20

The frozen six-configuration search consumed exactly 96 internal and 8 outer fits.
The recorded search/fit/evaluation portion took 45.14 seconds on the local host;
this excludes source verification and fresh-kernel startup. All eight saved
native models reproduce external probabilities exactly with their corresponding
preparers. There are 29 raw predictors (28 existing features plus municipality),
encoded into 114 numeric columns for the current complete municipality vocabulary.
No new scientific feature was introduced.

| Horizon | XGBoost mean AP | Persistence mean AP | Prevalence mean AP | XGBoost mean Brier | Prevalence mean Brier |
|---|---:|---:|---:|---:|---:|
| T+1 | 0.728860 | 0.581263 | 0.421601 | 0.150014 | 0.257645 |
| T+2 | 0.654211 | 0.546259 | 0.438158 | 0.182128 | 0.263932 |

Means give each of the four external windows equal weight. Persistence Brier is
not applicable to its deterministic alerts. The candidate improves these observed
AP/Brier comparisons; this is descriptive evidence, not statistical superiority,
calibration approval, an operational threshold or a champion decision. The
candidate/representation/search configuration was frozen before these outputs.

| Window | Training rows | Validation rows | XGBoost AP | XGBoost Brier |
|---|---:|---:|---:|---:|
| 2018-12_t1 | 6384 | 456 | 0.905040 | 0.170881 |
| 2018-12_t2 | 6384 | 380 | 0.884264 | 0.218751 |
| 2020-12_t1 | 8208 | 456 | 0.407156 | 0.061001 |
| 2020-12_t2 | 8208 | 380 | 0.277973 | 0.072476 |
| 2022-12_t1 | 10032 | 456 | 0.875400 | 0.181969 |
| 2022-12_t2 | 10032 | 380 | 0.841038 | 0.216370 |
| 2024-06_t1 | 11400 | 456 | 0.727843 | 0.186206 |
| 2024-06_t2 | 11400 | 380 | 0.613568 | 0.220914 |

Coverage is 76 municipalities per window, 3,344 external predictions overall. The
2018/2020/2022 December cuts validate January–June T+1 and February–June T+2;
the June 2024 cut validates July–December T+1 and August–December T+2. Each
prediction has its own origin; these are not whole-semester forecasts issued
at the initial cutoff. No 2025+ target enters this delivery.

No invalid or constant external probability vectors were found. AP varies from
0.277973 to 0.905040 across windows; the 2020 T+2 training AP 0.680702 versus external
AP 0.277973 illustrates temporal performance variation that the mean alone hides.
All 608 territorial groups remain in diagnostics with support 5 or 6; 275 single-class
groups have unavailable AP rather than fabricated scores. Fixed reliability-bin
counts cover every external prediction; no production calibrator was fitted.
Event alert metrics remain pending an approved threshold criterion.

Local candidate bundle:
`artifacts/model_training/xgboost/3d8350b5c41c82124f4412bb75d25bbd57d1e7de8a50b5346d9fd17d7c10479c`.
Current reference bundle:
`artifacts/model_training/957a1fc145dab07a6cf0cb71c58a9d52c2d5a107d23f0e95d1c0d6b0fe43534b`.
Detailed model/data evidence remains gitignored. PLAN_022 records the independent
review, preservation audit, notebook receipts and mapped controls. Historical
PLAN_020/021 and their artifact identities remain preserved.
