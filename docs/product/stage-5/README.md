# Stage 5 — calibration, development assessment and final protocol

Delivery 1 implements bounded Stage 5 development work over verified Stage 4 artifacts.
It does not reopen EDA, change labels/features/population, select a champion, or use
reserved targets from 2025-01 onward.

## Scope

- Reuse Stage 4 candidate families and metrics (`xgboost`, `lightgbm`, `gam`).
- Select one configuration per candidate/window/horizon from hyperparameter-selection
  role months only.
- Compare original probabilities versus sigmoid calibration per candidate/window/horizon
  using calibration-selection role months only.
- Select one initial municipality-shared threshold per candidate/window/horizon from
  threshold-selection role months only.
- Refit one outer model per candidate/window/horizon before external evaluation.
- Persist immutable artifacts with reproducible identities and independent formula checks.

## Contract and notebook

- Contract/config: [probability_calibration_thresholds_contract_v1.json](probability_calibration_thresholds_contract_v1.json)
- Notebook orchestrator (code-only): [07_probability_calibration_thresholds.ipynb](../../../notebooks/07_probability_calibration_thresholds.ipynb)
- Reusable modules: [scripts/model_evaluation](../../../scripts/model_evaluation)

## Utility knobs (percentage points)

- `max_false_alarm_increase_pp = 5.0`
- `min_onset_sensitivity_gain_pp = 10.0`
- `seed = 42`

Threshold feasibility rules use the exact contract formulas:

- `false_alarm_ratio_candidate <= false_alarm_ratio_persistence + max_false_alarm_increase_pp / 100`
- `onset_sensitivity_candidate >= onset_sensitivity_persistence + min_onset_sensitivity_gain_pp / 100`

Unavailable denominators remain unavailable and are never converted to zero.

## Temporal role protocol

Temporal roles are explicit per external window/horizon in
`window_role_calendar` (contract v1.2.0):

- `hyperparameter_selection_targets`
- `calibration_fit_targets`
- `calibration_selection_targets`
- `threshold_selection_targets`
- `external_evaluation_origin_range` and `external_evaluation_target_range`

Required chronology per window/horizon:

`max(producer labeled targets, actual fitted dependencies) <= min(consumer origins)`

Equality uses retrospective month-close availability, not a demonstrated operational publication schedule.

Stage 4 external context remains posterior-only and is never used for
configuration selection, calibration fitting, calibration selection or threshold
selection.

### Label-availability correction (PLAN_027)

PLAN_026's origin-to-origin acceptance and its old bundles remain historical and
are superseded. Issuing a prediction does not make its future label available.
The late Stage4 T+2 fold cannot contain the existing minimum role supports plus
the necessary label-availability gaps. No external rows or support requirements
were removed. Earlier training-only evidence uses the unchanged family grids.

For cutoff C, HP selection targets C−17..C−12 (six months), calibration fit
C−10..C−9, calibration choice C−7..C−6, threshold selection C−4..C−3
(two months each). For C=2018-12 and T+2:

| Component | Labeled targets | Prediction origins | Model training end |
|---|---|---|---|
| HP selection | 2017-07..2017-12 | 2017-05..2017-10 | 2017-05 |
| Calibration fit | 2018-02..2018-03 | 2017-12..2018-01 | 2017-12 |
| Calibration choice | 2018-05..2018-06 | 2018-03..2018-04 | 2017-12 |
| Threshold selection | 2018-08..2018-09 | 2018-06..2018-07 | 2017-12 |
| External evaluation | 2019-02..2019-06 | 2018-12..2019-04 | 2018-12 |

All eight calendars, monthly population, class support and model availability
are checked before any fit. The declared maximum is 112 HP models, 24 selected
internal models, 24 outer models, and 24 sigmoid calibrators: 184 fits total.
The selected internal model is frozen throughout the three downstream roles.
The outer model/preparer refit through C retains the earlier calibrator and
threshold. Transfer to that refitted model is a calibration limitation; no
external recalibration or threshold correction is performed.

### Current correction evidence

- `calendar_preflight.json`: actual support and training-label cutoffs before fits.
- `availability_transitions.csv`: 96 actual target/origin/dependency comparisons.
- Per-family/window internal predictions, model files, preparers and provenance:
  reproduce all HP configurations and selected development predictions.
- Outer training provenance and fitted components reproduce external predictions.
- PLAN_027 audit independently recalculates dates and guards real verify/reuse
  paths against model fitting, calibration fitting and threshold selection.


- `temporal_audit.csv`: chronology, fold disjointness, component-availability and
  reserved-block checks per candidate/window/horizon.
- `independent_checks.csv`: independent oracle checks for threshold/event counts and
  structural leak guards.
- `hyperparameter_selection.csv`: explicit evidence that configuration selection uses
  only hyperparameter-selection role rows.

## Commands

```bash
.venv/bin/python -m scripts.model_evaluation.execution --execute
.venv/bin/python -m scripts.model_evaluation.execution --verify
.venv/bin/python -m scripts.model_evaluation.notebook_execution --execute
.venv/bin/python -m scripts.model_evaluation.notebook_execution --verify
```

Artifacts are written under `artifacts/model_evaluation/` with immutable identities.
Distinct configurations must create distinct bundle IDs and never overwrite prior runs.

## Delivery boundaries

- No final-block (>= 2025-01) adjustment or evaluation.
- No champion selection.
- No G4/G5 approval claim.
- No merge authorization.

## Delivery 2 — development assessment and pending final protocol

The separate [assessment contract](model_evaluation_contract_v1.json) and
[notebook08](../../../notebooks/08_model_evaluation.ipynb) consume the corrected
PLAN_027 input without changing its code identity or refitting components.
Implementation lives in [model_assessment](../../../scripts/model_assessment).
AP ranking, DEC-125 point utility and uncertainty remain separate. All four
windows have equal weight within each horizon. Missing metrics invalidate their
aggregate; persistence has no probabilistic Brier score. Period, department and
municipality tables retain counts and non-evaluable groups without local tuning.

The development sensitivity analysis enumerates all 256 ordered whole-window
bootstrap draws. It preserves the full municipal panel in each window. Four
clusters cannot establish a calibrated confidence interval or remove dependence
across seasons; its percentile ranges are descriptive.

The final protocol is a **proposal requiring explicit human acceptance**:
choose the highest-AP candidate meeting point utility per horizon, retain its
verified 2024-06 internal configuration/calibration/threshold decisions, and refit
only the outer model/preparer through December2024 for T+1 or November2024 for
T+2. This preserves November2024 → January2025 rather than using later labels.
Retained calibration transfer remains a limitation. There are no reserved-label
updates. The proposed final cohort is all 76 municipalities for targets
January–December2025, with missing evidence explicit. The contract specifies
paired temporal-block uncertainty and a conservative three-way research
conclusion; these scientific choices are not yet accepted.

Before acceptance, the executable stops at a complete development comparison
and immutable `freeze_proposal.json`. It has no reserved-execution switch and
produces no final results or fitted final components. G4 remains open; G5 is not
approved. A subsequent authorized task must implement and audit the accepted
final procedure, including actual row-derived availability, before claiming final
completion. Proposed dates are not evidence that final models have been fitted.

Run from the repository root:

```bash
.venv/bin/python -m scripts.model_assessment.execution --execute
.venv/bin/python -m scripts.model_assessment.execution --verify
```

Execution uses a fresh kernel, then verifies saved outputs against recomputed
artifacts. Verification uses native input inference, never fallback training.
Identical valid artifacts are reused; absent/corrupt artifacts fail verification.
New source, input, contract or notebook code creates a distinct immutable identity.
Local artifacts remain under `artifacts/model_assessment/` and execution receipts
under `artifacts/model_assessment_notebook_executions/`; they are not Git deliverables.

Validation for this surface (in addition to the repository foundation checks):

```bash
.venv/bin/python -m pytest tests/unit/test_model_assessment.py -q
.venv/bin/ruff check scripts/model_assessment tests/unit/test_model_assessment.py
.venv/bin/ruff format --check scripts/model_assessment tests/unit/test_model_assessment.py
.venv/bin/mypy --explicit-package-bases scripts/model_assessment tests/unit/test_model_assessment.py
```

The critical regressions cover early T+2 availability, reserved-target rejection
and the approved onset/false-alert denominators and utility knobs. PLAN_028 owns
execution evidence and independent review. Historical DWP conformance incidents
remain separately recorded; they are not repaired by rewriting previous plans.

### Corrected development comparison

These are equal-weight means of all four windows, separately by horizon; they
are not pooled ratios. Candidate coverage is 1,824 T+1 and 1,520 T+2 examples,
with 76 municipalities at each cutoff. Source: corrected Stage5 bundle
`7a4f36dc93ed1aba69ac00c6f086bf822f46bb2bfb640cd91dfde0ea4eebb257`.

| Horizon | Procedure | AP | Brier | Onset sensitivity | False/emitted alerts | DEC-125 point utility |
|---|---|---:|---:|---:|---:|---|
| T+1 | XGBoost | 0.7281 | 0.1500 | 17.08% | 36.43% | Meets |
| T+1 | LightGBM | 0.7244 | 0.1491 | 29.19% | 39.46% | Does not meet FAR constraint |
| T+1 | GAM | 0.7144 | 0.1579 | 17.47% | 37.06% | Meets |
| T+1 | Persistence | 0.5813 | N/A | 0.00% | 32.45% | Reference |
| T+2 | LightGBM | 0.6642 | 0.1927 | 40.64% | 41.05% | Meets |
| T+2 | XGBoost | 0.6578 | 0.1935 | 35.12% | 40.26% | Meets |
| T+2 | GAM | 0.6570 | 0.2013 | 43.17% | 40.33% | Meets |
| T+2 | Persistence | 0.5463 | N/A | 20.52% | 36.36% | Reference |

All six candidate point decisions have complete global window metrics. Territorial
and period metrics can be non-evaluable; their individual support is retained.
`window_metrics.csv` records every numerator/denominator, and `comparison.csv`
keeps count totals distinct from mean rates. For example, the proposed XGBoost
T+1 has 44 detected / 219 known onsets and 231 false / 820 emitted alerts across
all windows; LightGBM T+2 has 87 / 179 and 253 / 782 respectively. Those pooled
counts must not be substituted for the approved equal-window rates above.

The descriptive interval for XGBoost T+1 onset gain spans roughly 2.11–32.05pp,
and FAR increase −0.66–6.91pp. For LightGBM T+2 the corresponding ranges are
5.00–35.25pp and 2.14–6.83pp. Both cross required utility boundaries. Point utility
and descriptive AP therefore support a proposal to evaluate, not established
scientific acceptance. Final research conclusions remain unavailable until the
separately authorized frozen evaluation is executed.
