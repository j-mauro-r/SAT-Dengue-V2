# Stage 4 delivery 1 — shared model-training pipeline and simple references

This first bounded Stage 4 delivery implements a shared execution pipeline on top of current Stage 3 temporal artifacts. It runs two references only:

- Persistence: deterministic binary alert derived from current endemic-zone state.
- Train prevalence: constant probability estimated from `Y_train` per window/horizon.

This delivery does **not** train XGBoost, LightGBM or GAM. It does not close G4, and it does not retroactively close G2/G3.

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
