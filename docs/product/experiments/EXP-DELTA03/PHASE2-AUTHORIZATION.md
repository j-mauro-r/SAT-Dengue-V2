# Phase 2 scientific implementation approval

Mauricio explicitly approved the complete bundled proposal on 2026-11-06.
The original request is preserved in PLAN_056, with SHA256
`2b517c65c579836da1bd68d3dea05fb56899b29745094c4e5e3cae26acd90579`.
DWP revision 2 records the bounded approval under `T-final-review`; revision 1,
its approval and all prior evidence remain preserved. The prior proposed
contract is retained in git at `3957bce`.

Status: **APPROVED_FOR_PHASE2_IMPLEMENTATION**. This freezes all explicit model,
calibration, policy and uncertainty values in the [training contract](training-contract.json).

- XGBoost, 80 trees, depth 2, learning rate 0.05, histogram trees, seed 1729,
  one CPU thread; the remaining explicit defaults are approved unchanged.
  No hyperparameter search.
- Regularized intercept calibration, penalty 1, calibration role only;
  evaluation is independent of all learned choices.
- B=1 false onset alert per eligible municipality-year; eligible selection
  rows/12, floor cap, complete deterministic score ties and the stated
  lexicographic objective. Report monitored exposure separately. No evaluation
  budget adjustment.
- Paired municipality and episode-connected annual blocks; 1,000 replicates,
  95% intervals, seed 1729, at least two municipalities and two blocks,
  at least 80% valid replicates. No IID row fallback. Estimates are descriptive;
  no formal superiority or materiality conclusion is approved.
- 2024 remains separate consumed retrospective stress. 2025 remains excluded
  from learned roles, selection and evaluation.
- Prepare a separate national evaluation/excess/comparator/exposure annex.
  Preserve every Phase 1 core matrix, label and cohort. Declare available and
  pending inputs explicitly; preparation does not imply execution readiness.

`execution=not_authorized`, `training_authorized=false`,
`phase3_authorized=false`, `operational_PIT=false`,
`preparation_regime=RETROSPECTIVE_CONSOLIDATED`, G5 `NOT_APPROVED` and champion
`not_selected` remain in force. No real fit, calibration, scientific prediction,
permanent MLflow write, Phase 3, deployment, merge or champion selection is
authorized. Operational PIT and causal claims remain prohibited.
