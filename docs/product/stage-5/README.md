# Stage 5 — probability calibration and temporal thresholds (delivery 1)

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
