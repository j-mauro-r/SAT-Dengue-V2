# Stage 5 — frozen Kedro assessment and preserved scientific evidence

## Current execution and governance

Use `kedro run --pipeline=replay` for construction through frozen assessment,
or `kedro run --pipeline=evaluation_replay --params=profile=evaluation_replay`
for the explicit verified assessment boundary. `evaluation_synthetic` is disjoint
and consumes no private source. Tracking is optional and disabled by default.
G5 is `NOT_APPROVED`, champion `not_selected`; all six real decisions are
`does_not_meet`. Consumed 2025 cannot train, adjust, calibrate, search or select.
The migrated workflow applies saved components and thresholds, with zero real fits.

The [migration owner](../../operations/kedro-migration.md#current-cleanup-and-execution--session-8)
owns installation/restart/tracking/recovery and the [testing guide](../../TESTING_GUIDE.md)
owns required synthetic/private controls. Replaced Stage 4/5 script facades have
direct package consumers; the [cleanup correspondence](../../operations/kedro-cleanup-identities.json)
checks originals, prior engineering bytes and final absence without changing older
mappings. Notebooks 07/08 remain frozen source identity evidence, never production
entrypoints. No new reporting notebooks or native scientific bundles are created.
All prior scientific limitations and decision IDs remain. This is not complete
historical reproducibility or operational model approval.

## Historical scientific delivery records

The following delivery protocols, recorded commands/results and earlier migration
checkpoints are historical evidence. Their fitting/notebook commands apply only
to their original recoverable Git tree, never to current production execution.


Current execution is the guarded Kedro migration described in
[Maintained frozen assessment](#maintained-frozen-assessment--kedro-session-6).
Earlier delivery sections below preserve scientific decisions and dated evidence;
their fitting/notebook commands are historical, not authorization to execute them.

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
- Reusable modules: [scripts/model_evaluation](../../../src/sat_dengue/datasets/legacy_evaluation/model_evaluation/__init__.py)

## Utility knobs (percentage points)

The active values live only in
[`champion_decision_policy_v1.json`](champion_decision_policy_v1.json), under
`utility`. This README explains their meaning without maintaining a second copy.

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

The owning [assessment contract](model_evaluation_contract_v1.json) and
[notebook08](../../../notebooks/08_model_evaluation.ipynb) consume the corrected
PLAN_027 input without changing its code identity or refitting components.
Implementation lives in [model_assessment](../../../src/sat_dengue/datasets/legacy_evaluation/model_assessment/__init__.py).
AP ranking, DEC-125 point utility and uncertainty remain separate. AUROC is
complementary and never changes ranking, utility, thresholds or training. All four
windows have equal weight within each horizon. Missing metrics invalidate their
aggregate; persistence has no probabilistic Brier score. Period, department and
municipality tables retain counts and non-evaluable groups without local tuning.

The development sensitivity analysis enumerates all 256 ordered whole-window
bootstrap draws. It preserves the full municipal panel in each window. Four
clusters cannot establish a calibrated confidence interval or remove dependence
across seasons; its percentile ranges are descriptive.

The current final protocol is a **six-procedure proposal requiring explicit human
acceptance before reserved access**. Include XGBoost, LightGBM and GAM at both
horizons, regardless of development utility qualification. Retain each verified
2024-06 internal configuration/calibration/threshold decision and refit only its
outer model/preparer through December2024 for T+1 or November2024 for T+2. This preserves November2024 → January2025 rather than using later labels.
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
.venv/bin/python -m scripts.final_evaluation.execution --execute
.venv/bin/python -m scripts.final_evaluation.execution --verify
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
with 76 municipalities at each cutoff. Source: current development assessment bundle
`0f26a4eb97ad37075f3fba2d8da0afd55cf3450db945e8f9cb86d7dccac2f257`,
using the live scientifically equivalent Stage5 input. The original audited anchor
remains part of provenance; it is not the only permitted current input identity.

| Horizon | Procedure | AP | AUROC | Brier | Onset sensitivity | False/emitted alerts | DEC-125 point utility |
|---|---|---:|---:|---:|---:|---:|---|
| T+1 | XGBoost | 0.7281 | 0.7941 | 0.1500 | 17.08% | 36.43% | Meets |
| T+1 | LightGBM | 0.7244 | 0.7966 | 0.1491 | 29.19% | 39.46% | Does not meet FAR constraint |
| T+1 | GAM | 0.7144 | 0.7903 | 0.1579 | 17.47% | 37.06% | Meets |
| T+1 | Persistence | 0.5813 | 0.7259 | N/A | 0.00% | 32.45% | Reference |
| T+2 | LightGBM | 0.6642 | 0.7518 | 0.1927 | 40.64% | 41.05% | Meets |
| T+2 | XGBoost | 0.6578 | 0.7447 | 0.1935 | 35.12% | 40.26% | Meets |
| T+2 | GAM | 0.6570 | 0.7529 | 0.2013 | 43.17% | 40.33% | Meets |
| T+2 | Persistence | 0.5463 | 0.6727 | N/A | 20.52% | 36.36% | Reference |

All six candidate point decisions have complete global window metrics. Territorial
and period metrics can be non-evaluable; their individual support is retained.
`window_metrics.csv` records every numerator/denominator, and `comparison.csv`
keeps count totals distinct from mean rates. For example, XGBoost
T+1 has 44 detected / 219 known onsets and 231 false / 820 emitted alerts across
all windows; LightGBM T+2 has 87 / 179 and 253 / 782 respectively. Those pooled
counts must not be substituted for the approved equal-window rates above.

The descriptive interval for XGBoost T+1 onset gain spans roughly 2.11–32.05pp,
and FAR increase −0.66–6.91pp. For LightGBM T+2 the corresponding ranges are
5.00–35.25pp and 2.14–6.83pp. Both cross required utility boundaries. Point utility
and descriptive AP do not establish scientific acceptance; the current proposal
includes all six combinations rather than filtering to these two. Final research conclusions remain unavailable until the
separately authorized frozen evaluation is executed.

### Reexecuting notebooks 03–08

Notebook08 retains the audited Stage5 input as an anchor rather than requiring
every upstream reexecution to retain the same bundle directory. The current
input must first pass live Stage5 verification. Its scientific payloads, code,
configuration, runtime and rules must then match the retained audited anchor
exactly. Only upstream manifest references and matching summary paths may
differ. `input_verification.json` records the actual input and anchor; a new
assessment and proposal identity preserve this lineage. Missing anchors,
changed scientific results and corruption stop execution without fitting.
Historical bundles and proposals remain untouched; G4/G5 and reserved access
remain pending and do not transfer through this compatibility check.


## Stage5 closure delivery1 — six procedures and complementary AUROC

The explicit October21 revision supersedes the former XGBoost T+1/LightGBM T+2
proposal, not its historical evidence. All six procedures retain their own June2024
internal decisions. The proposed future budget is six outer model fits and six
train-only preparers, zero hyperparameter searches, zero calibrator fits and zero
threshold selections. This delivery performs none of those fits or any reserved
evaluation. Both G4 and final-protocol acceptance remain separate human decisions.

The shared supplementary evaluator is
[scripts/evaluation_metrics.py](../../../src/sat_dengue/metrics.py). It calls
the existing four-metric implementation unchanged and adds sklearn binary AUROC
on the same continuous model scores and aligned population. Persistence uses its
documented deterministic score, not a calibrated probability; Brier remains N/A.
Single-class, empty or missing populations are explicitly non-evaluable; invalid
or misaligned inputs reject. AUROC positive/total support counts are not a formula
for the area. No F1 is introduced.

Development AUROC is the equal-weight mean of the four window AUROCs, never the
area after pooling predictions. An unavailable window invalidates that mean. The
new evaluator is included in assessment code identity; the immutable input-era
four-metric contract and fitted-code identity remain intact. Live input verification
plus exact audited scientific equivalence remain mandatory, including all405
scientific payloads. This is not permission to accept an arbitrary new bundle.

Before opening2025, the owning contract specifies a **proposed** recommendation
rule per horizon: require complete common cohorts, valid availability/inference
and the existing utility/uncertainty acceptance; compare annual reserved-cohort
AP among qualified candidates. Do not average monthly AP or combine horizons.
Exact AP ties remain unresolved for human choice; AUROC is not a tie-breaker.
If none qualifies, do not force a recommendation: distinguish complete point
failures from insufficient evidence. Numerical AP differences alone do not prove
scientific superiority. Acceptance of this rule remains pending.

The existing3-month whole-panel temporal-block uncertainty method is retained,
with the same paired draws across all families/reference within a horizon.
Intervals are candidate-wise and marginal: no simultaneous-family or post-selection
coverage is asserted, and no new multiplicity correction is introduced. Comparing
and recommending among candidates using2025 consumes that block for the decision;
it cannot subsequently be described as an additional independent test of the
selected procedure. Rules must be fixed before consulting outcomes.

The proposal enumerates all76 municipality codes, twelve target months, exact
component/preparer provenance and first consuming origins. Actual final components
are explicitly not fitted. November2024 → January2025 T+2 is retained. Missing
rows stay explicit and cannot be silently removed to obtain acceptance.

Required gates and the shared-evaluator test mapping are recorded in the
[testing guide](../../TESTING_GUIDE.md#stage5-closure-delivery1-six-procedures-and-auroc).

## Closure delivery 2 — gated final route

Implementation: [final_evaluation](../../../src/sat_dengue/datasets/legacy_evaluation/final_evaluation/__init__.py). The exact
six-procedure proposal remains `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`
in assessment bundle `0f26a4eb97ad37075f3fba2d8da0afd55cf3450db945e8f9cb86d7dccac2f257`.
The scientific contract and original assessment modules remain byte-identical to
that proposal. No replacement proposal is silently generated.

Notebook08 has an explicit orchestration migration. Its original code is retained
under `artifacts/model_final_protocol/<proposal_sha>/development_notebook_code.json`,
checked against the original proposal code fingerprint. Every other frozen source
and contract fingerprint is verified against live files. New notebook/final-route
code fingerprints are recorded separately in readiness receipts and final identities.
The migrated notebook displays the immutable development comparison and, only when
requested and authorized, executes the final route. Historical assessment CLI
receipts belong to the previous notebook orchestration; use the current commands below.

Default execution performs readiness checks only, with zero reserved access or
scientific fitting:

```bash
.venv/bin/python -m scripts.final_evaluation.execution --execute
.venv/bin/python -m scripts.final_evaluation.execution --verify
```

After final evaluation, later repository refactors may intentionally change live
development contracts or assessment modules. Readiness still verifies the immutable
proposal bundle and reports `live_frozen_dependencies=changed_after_freeze` plus the
first mismatch; it does not silently declare the new code equivalent. In that state
`scientific_execution_allowed=false`, and `run_final` remains fail-closed. Historical
results must be read from the verified final bundle rather than regenerated with the
new dependency identity.

After actual human acceptance of G4, this exact proposal/protocol, and final
execution is recorded, the scientific command is:

```bash
.venv/bin/python -m scripts.final_evaluation.execution --execute --scientific
.venv/bin/python -m scripts.final_evaluation.execution --verify --scientific
```

`--scientific` does not approve anything. The route requires a local
`artifacts/model_final_protocol/<proposal_sha>/human_authorization.json` containing
`authority: "Mauricio"`, the exact `proposal_sha256`, explicit true values for
`accept_G4`, `accept_exact_protocol`, `authorize_final_execution`, and a
`decision_source` with the repository-relative path and `{sha256, bytes}` fingerprint
of the actual human decision text. The agent may record a decision only after the
human actually supplies it, including the corresponding DWP authority signoff; the
software does not manufacture approval or claim cryptographic proof of authorship.
No such acceptance is supplied by a request to implement this route.

Before the first final fit, both complete horizon cohorts and all six frozen
configurations, preparation specifications, thresholds and calibration objects are
checked. Training labels start January2012 and end December2024/T1 or November2024/T2.
The unchanged deterministic preparation builds full prior history before selecting
origins. Forecast rows remain the complete common76×12 calendar; unknown evaluation
inputs/labels/context stay explicit and prevent acceptance. Incomplete training
inputs or class support stop before fitting rather than imputing or dropping rows.
S/S−1 stays in evaluation context, outside all predictor matrices.

Final outputs use `artifacts/model_final_evaluation/<identity>/`: six native/numeric
JSON models, six JSON preparers, retained-decision references, training provenance,
full keyed predictions, annual comparison, period/department/municipality metrics,
actual cohort preflight, original event contexts, common month-resampling indices,
marginal utility intervals, fit accounting and a hashed manifest. Annual metrics
use the full annual cohort, separately from development means. Uncertainty sums
shared monthly event counts at sampled original months, preserving original onsets;
any unavailable resample leaves bounds unavailable instead of dropping that draw.
No champion or G5 acceptance is produced.

Every saved model is restored and its probabilities reproduced before publication.
Verification/reuse replays inference and recomputes metrics without fitting or repair.
Missing/corrupt artifacts fail. A proposal-wide exclusive fit-attempt record prevents
concurrent or silently repeated fitting after interruption or identity change;
partial attempts require explicit investigation and human-authorized recovery.
Successful current-run counters are separate from the six historical model/preparer
fits recorded in the immutable result. Synthetic regression fits are test fixtures,
never scientific evidence or final model packages.

Mauricio accepted G4 and the exact proposal/protocol on October 21, 2026. The
authorization is bound to the proposal hash above. The single scientific execution
completed the declared six model fits and six train-only preparer fits, with zero
searches, calibrator fits or threshold selections. The immutable owning contract
remains the pre-authorization protocol snapshot; DEC-132 and the final execution
receipt record the later human gate and observed outcome without rewriting it.

The final bundle is
`artifacts/model_final_evaluation/768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35`.
Both horizons contain all 76 municipalities and all 12 targets in 2025: 912 rows,
237 positive labels, 675 negative labels, no missing labels, no incomplete predictor
rows and no unknown onset context per horizon. T+1 uses 11,856 training rows through
December 2024; T+2 uses 11,780 through November 2024 and preserves the November 2024
origin for January 2025.

| Horizon | Procedure | AP | AUROC | Brier | Detected/real onsets | False/emitted alerts | Result |
|---|---|---:|---:|---:|---:|---:|---|
| T+1 | Persistence | 0.4746 | 0.7430 | N/A | 0/86 | 102/253 | Reference |
| T+1 | XGBoost | 0.6757 | 0.8189 | 0.1433 | 22/86 | 177/350 | Does not meet |
| T+1 | LightGBM | 0.6689 | 0.8192 | 0.1431 | 34/86 | 218/403 | Does not meet |
| T+1 | GAM | 0.6448 | 0.8093 | 0.1477 | 20/86 | 151/321 | Does not meet |
| T+2 | Persistence | 0.4299 | 0.7166 | N/A | 30/86 | 132/281 | Reference |
| T+2 | XGBoost | 0.5611 | 0.7638 | 0.1672 | 48/86 | 289/469 | Does not meet |
| T+2 | LightGBM | 0.5469 | 0.7585 | 0.1689 | 55/86 | 336/530 | Does not meet |
| T+2 | GAM | 0.5210 | 0.7465 | 0.1767 | 62/86 | 406/611 | Does not meet |

Every candidate increases onset sensitivity, but every candidate also exceeds the
predeclared maximum five-point increase in false-alert ratio. The frozen research
classification is therefore `does_not_meet` for all six procedures. This consumes
the 2025 block for comparison; it is not an independent post-selection test.
Verification restored all six packages and reproduced their probabilities with zero
new fits. G5 remains unapproved and `champion` remains `not_selected`. The third
delivery owns final interpretation, recommendation and the human Stage 6 handoff.

## Final scientific review and Stage 6 handoff

PLAN_028 is technically reproducible and scientifically unsuccessful under its
frozen utility rule. The exact proposal, notebook receipt and 37-payload bundle
manifest agree. Verification reloads all six saved models and preparers and
reproduces predictions, metrics and identities without fitting, repair or artifact
regeneration. This technical success does not establish operational usefulness.

The candidates rank municipality-months better than persistence: every AP and AUROC
is higher, and every candidate detects more of the 86 observed onsets. Their frozen
alert thresholds also emit too many incorrect alerts. The required false-alert-ratio
increase was at most five percentage points relative to the horizon-specific
persistence reference. All six point estimates exceed that limit, so higher AP,
AUROC, lower Brier or higher sensitivity cannot qualify any procedure by itself.

| Horizon | Procedure | Onset gain vs persistence | Marginal interval | False-alert-ratio increase | Marginal interval | Frozen result |
|---|---|---:|---:|---:|---:|---|
| T+1 | XGBoost | +25.58 pp | [18.91, 32.04] pp | +10.26 pp | [6.80, 12.60] pp | Does not meet |
| T+1 | LightGBM | +39.53 pp | [28.95, 48.96] pp | +13.78 pp | [10.14, 15.95] pp | Does not meet |
| T+1 | GAM | +23.26 pp | [15.07, 29.76] pp | +6.72 pp | [2.15, 9.30] pp | Does not meet |
| T+2 | XGBoost | +20.93 pp | [15.66, 25.93] pp | +14.65 pp | [12.85, 16.57] pp | Does not meet |
| T+2 | LightGBM | +29.07 pp | [22.22, 35.44] pp | +16.42 pp | [13.91, 18.78] pp | Does not meet |
| T+2 | GAM | +37.21 pp | [29.67, 45.45] pp | +19.47 pp | [16.50, 22.12] pp | Does not meet |

These are candidate-wise marginal intervals from the frozen common 2,000-draw
three-month temporal-block procedure. They describe uncertainty under that method;
they are not simultaneous family-selection intervals or a new independent test.
For five procedures, even the lower false-alert-ratio bound exceeds five points.
T+1 GAM has a lower bound below five points, but its observed increase is 6.72
points and the frozen rule is applied to the point estimate; uncertainty was never
authorized to rescue a failing point result.

Failure concentration is descriptive. June 2025 is a maximum false-alert month
for every candidate/horizon; LightGBM T+2 ties June with July at 34. October 2025
is a maximum missed-onset month for every candidate/horizon; XGBoost T+1 ties it
with February at 7, GAM T+2 ties it with February at 4, and LightGBM T+2 ties it
with February and June at 4. Tolima
(department 73) contributes the largest false-alert count in each candidate result,
with different emitted-alert denominators: XGBoost 101/161, LightGBM 125/192 and
GAM 82/142 at T+1; XGBoost 169/237, LightGBM 204/278 and GAM 259/341 at T+2.
Meta contributes 76/189, 93/211 and 69/179 at T+1, and 120/232, 132/252 and
147/270 at T+2. The largest single-municipality counts vary by procedure. These
counts do not establish a territorial or seasonal cause; support and denominators
differ.

| Horizon | Procedure | June false/emitted | October missed/real onsets | Municipality with most false/emitted | Municipality with most missed/real onsets |
|---|---|---:|---:|---:|---:|
| T+1 | XGBoost | 24/37 | 7/10 | 73168: 7/9 | 50350: 3/3 |
| T+1 | LightGBM | 30/43 | 7/10 | 50318: 7/10 | 73043: 3/3 |
| T+1 | GAM | 23/36 | 9/10 | 73671: 6/8 | 50318: 3/4 |
| T+2 | XGBoost | 34/46 | 6/10 | 73168: 10/12 | 73043: 2/3 |
| T+2 | LightGBM | 34/47 | 4/10 | 73168: 10/12 | 73043: 2/3 |
| T+2 | GAM | 41/55 | 4/10 | 73483: 11/11 | 73043: 2/3 |

Municipality codes are shown because the final artifact uses those stable keys.
“Missed/real” is the complement of detected/real onset sensitivity for the named
group; it is not a new metric or denominator.

The evidence uses retrospectively consolidated data, and historical as-of
availability has not been demonstrated. The June 2024 calibration and threshold
decisions may not transfer to later operating conditions. The 2025 block has now
been consumed for this comparison and cannot be tuned on and then described as a
new independent test.

Mauricio accepted the scientific disposition **G5 NOT_APPROVED** on 2026-10-21.
`champion` remains `not_selected`; no XGBoost, LightGBM or GAM package is approved
for product integration. Stage 5 is closed with an unsatisfactory scientific
result. The read-only MVP may present persisted historical/evaluation results with
their visible `NOT_APPROVED` status, but it must not connect a champion to an API
or dashboard or present those results as operational forecasts.

The single editable policy for utility tolerances, ranking, retained alert-threshold
authority and the human disposition is
[`champion_decision_policy_v1.json`](champion_decision_policy_v1.json). Stage 5
contracts reference that file rather than duplicate its values. Editing its utility
tolerances can recompute an evaluation classification; editing a retained alert
threshold changes which probabilities emit alerts. Neither action retrains a model,
rewrites the consumed 2025 evidence or creates scientific approval. A future
scientific iteration requires a new protocol and independent evaluation evidence.

The one recommended next experiment changes only the alert-threshold decision
family. Keep all three fitted model families, features, configurations and saved
calibration choices as historical evidence. Within a new protocol, select a more
conservative shared threshold per candidate/horizon using nested rolling temporal
development only: require the false-alert-ratio increase to remain within five
points in each inner evaluation period, then maximize onset sensitivity among
feasible thresholds. Do not use 2025 for fitting or selection. Evaluate the locked
policy in a genuinely later independent period, or use a predeclared nested temporal
outer assessment when later data are unavailable. This experiment requires a new
plan and protocol; PLAN_028 does not implement it.

## PR #16 dependency reconciliation — 2026-10-22

Mauricio explicitly chose to retain main's LightGBM 4.7.0 update from PR #19
when resolving PR #16. The frozen Stage 5 evaluation used LightGBM 4.6.0.
The recorded results, notebook outputs and scientific disposition remain
historical evidence from that environment; they have not been regenerated.

Compatibility and saved-artifact reproducibility under LightGBM 4.7.0 remain
UNVERIFIED. Passing repository checks or synthetic tests does not establish
equivalence of the frozen scientific results. The modeling requirements file
participates in candidate identity fingerprints, so existing bundles must not
be silently relabeled, repaired or overwritten to bypass a mismatch. Validate
saved components and their predictions in a separate bounded follow-up before
claiming reproduction with the new dependency. This conflict resolution does
not authorize retraining, retuning, renewed use of 2025 for selection, a champion
or a change to G5 NOT_APPROVED.


## Maintained frozen assessment — Kedro Session 6

Use the existing isolated foundation environment, with modeling installed:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=evaluation_replay --params=profile=evaluation_replay
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=evaluation_synthetic --params=profile=evaluation_synthetic
```

`evaluation_replay` has ten nodes and uses only the fixed saved development,
proposal and final bundles. It resolves the approved contracts, verifies the
exact proposal and source/component identities, constructs complete cohorts and
validates availability, replays saved raw probabilities, applies retained
calibration, emits alerts from retained thresholds, computes final metrics and
paired uncertainty, independently rebuilds development assessment, applies the
existing decision policy and assembles verified atomic publication. There is no
fit, calibration-fit, hyperparameter, calibrator-choice or threshold-search node.
The already consumed 2025 block cannot become a new selection or training route.

`evaluation_synthetic` has eleven nodes. Its extra node creates its entire toy
fixture internally in memory; it has no frozen-source dataset input. Toy scores
exercise the same calibration, alert, cohort, metric, policy and publication
interfaces with zero fits. Synthetic results are interface tests, not evidence
of equivalence with real results. Existing deterministic native-model synthetic
roundtrip tests remain enabled separately.

Pure scientific owners are `src/sat_dengue/model_evaluation/`,
`model_assessment/` and `final_evaluation/`; metrics remain shared in `metrics.py`.
`datasets/evaluation_legacy.py` owns narrow native input reading and call guards;
`datasets/evaluation.py` owns lazy loading and atomic immutable output. Optional
modeling imports occur only when an evaluation node/dataset executes. Registration
and foundation remain usable with the base package alone. YAML selects only the
operational profile and disabled tracking; scientific overrides are rejected.

Each run publishes a distinct engineering bundle below ignored
`tmp/kedro-migration/evaluation-runs/`. Payloads retain full final predictions,
comparison, metrics, uncertainty, cohort keys/context and common draw indices;
complete development replay/assessment tables; and aggregate audit/provenance.
Every payload has a size/SHA-256 record. Publication rejects partial payload sets,
corruption, missing input identities and overwrites. Scientific native bundles,
proposal, policy, notebooks and historical hashes are never repaired or replaced.

The replay checks all 160 saved development models and six final models. It
reproduces all 72,048 internal/outer development inference rows, the 21,888 selected
development and 10,032 posterior rows, and the complete assessment outputs. Final
comparison uses 7,296 prediction rows (5,472 candidates and 1,824 persistence),
3,640 metric rows, eight comparison rows, sixteen uncertainty rows, two complete
912-row cohorts and two shared 2,000-by-12 resampling matrices. Original probability
roundtrips remain exact; development sigmoid replay retains its existing 1e-12
absolute bound. Other metric comparisons retain the migration's predeclared
1e-8 relative / 1e-10 absolute tolerances. No new tolerance is introduced.

All six research decisions remain `does_not_meet`. G5 remains `NOT_APPROVED` and
champion remains `not_selected`, read from the single decision policy. The
outer-refit/calibrator transfer and retrospective as-of-availability limitations
remain. 2025 cannot fit, refit, calibrate, tune, select alternatives or select a
champion. The 13 historical source exceptions and 17 KEEP / UNVERIFIED bundles
remain excluded from equivalence; full historical reproducibility is not claimed.

Twenty-two old modules stay as thin import/CLI adapters because notebooks,
protocol/cohort helpers and regression tests still consume them. Their CLI routes
now invoke guarded Kedro replay; `--scientific` rejects renewed execution.
Synthetic library regressions retain their isolated fake-repository engine.
No script or notebook is retired; retirement belongs to T-cleanup. Exact original
and current engineering identities and destinations are recorded in the
[migration identity mapping](../../operations/kedro-evaluation-identities.json).
Observed validation and consumer details live in local PLAN_030
`analysis_results/session6/HANDOFF.md`; the [testing guide](../../TESTING_GUIDE.md)
owns recurring commands. Tracking, E2E composition and later tasks remain separate.
