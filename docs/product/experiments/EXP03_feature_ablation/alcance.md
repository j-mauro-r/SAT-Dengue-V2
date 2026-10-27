# EXP03 scope revision — scientific specification and implementation handoff

Status: **scope implemented; primary budget fixed; real execution not authorized**.
Review date: 2026-10-27 UTC. Reviewed implementation: PR #34, commit
`52e13a4af73add8acd1c87b42d413e0e967235d3`.

Mauricio requested a methodical scope expansion and this documentation update.
That request authorizes the scope work, not scientific execution, a champion,
G5 approval or merging. This document owns the revised EXP03 requirements.
[DESIGN.md](DESIGN.md) is its entry point; [CONCLUSIONS.md](CONCLUSIONS.md) owns
evidence status and the eventual scientific interpretation.

The existing [protocol](protocol.json) and [matrix](ablation-matrix.frozen.yml)
still describe the superseded ten-set implementation. Their bytes and hash are
preserved in this documentation delivery. They are **not an executable encoding
of this scope**. Do not run the old protocol as if it satisfied this document.
The implementation task must reconcile code, registry, matrix, protocol, tests
and scientific decision register together, then generate a new canonical hash.
Old approvals, reservations and execution identities cannot authorize the revision.

## 1. Decision to support and evidence behind the change

Question: **which information adds exact-onset predictive value, beyond lagged
history and current epidemiological state, at a fixed alert-burden policy, and
how stable is that contribution across horizons, years and territories?**

The thesis contribution is a controlled analysis of information, error types and
transportability. A null or heterogeneous result is informative. A guaranteed
accuracy gain, operational deployment or biological causality is not promised.

Controlling evidence reviewed:

- [EXP00 consolidated conclusions at main f48f3d4](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/f48f3d4b5a3aa9f67cc4d31dc02424d327f610fb/docs/product/experiments/EXP00_historical_baseline/CONCLUSIONS.md).
- [EXP01 consolidated conclusions at main f48f3d4](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/f48f3d4b5a3aa9f67cc4d31dc02424d327f610fb/docs/product/experiments/EXP01_direct_onset/CONCLUSIONS.md).
- [Six-experiment plan at main f48f3d4](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/f48f3d4b5a3aa9f67cc4d31dc02424d327f610fb/docs/product/experiments/experimentos.md).
- Reviewed preparation, partitions and decisions: [EXP01 preparation](../../../../src/sat_dengue/experiments/exp01.py), [onset semantics](../../../../src/sat_dengue/experiments/onset.py), [EXP03 features](../../../../src/sat_dengue/experiments/exp03_features.py), [EXP03 decisions](../../../../src/sat_dengue/experiments/exp03_decisions.py).
- [Scientific standards](../../../standards/ml-scientific-standards.md) and
  [active scientific decision register](../../traking-concluciones.md).

The linked consolidated conclusions postdate the source branch's inherited
conclusion files. Reconcile with current main before implementation; do not
overwrite consolidated EXP00/EXP01 evidence with the older pending text.
This review uses documented results and public code, not a rerun or a new audit
of private inputs or MLflow. Earlier conversational recommendations are assessed
below, rather than treated as demonstrated findings.

| Evidence / limitation | Implication for EXP03 | Bounded response |
| --- | --- | --- |
| EXP00's greater detection comes with false-alert burden and development-to-2025 deterioration | Discrimination alone cannot select information | Joint detection/burden/calibration reporting |
| EXP01 has identical T+1 labels within Y(T)=0 | Two T+1 objectives duplicate the same task | One onset arm at T+1 |
| EXP01 T+2 benefit changes with family, year and budget; favorable 2020 trade-offs do not recur in 2022 | Direct onset is the main task, not a proven universally superior objective | Two bounded excess controls at T+2 |
| EXP01's single-year intervals are unavailable | Need multi-year out-of-sample evidence | Development cuts 2020, 2021, 2022 and paired clustered uncertainty |
| Equal selection caps do not imply equal realized false alerts; aggregate gains redistribute burden between Meta and Tolima | Examine both capacity and territorial effects | Fixed normalized policy, realized burden and subgroup guardrails |
| Current counts and their transformations are inside the old history base | Removing channel variables does not remove current epidemiological information | Explicit lagged and current blocks, with addition and removal contrasts |
| Historical publication dates are unproven | An event-time lag is not proof of availability | Conditional retrospective inference plus bounded availability diagnostics |
| EXP01 lacks individual prediction artifacts for independent metric reconstruction | Aggregate results alone limit auditability | Protected native row predictions, thresholds and audit tables |

### Corrections to earlier interpretations

1. Rolling cuts are **not independent replications**: training sets overlap,
   municipalities recur, and outcomes have temporal dependence. Each prediction
   must be out of sample for its own fit; pooling does not make years independent.
2. With the same nonnegative five historical counts and P75 definition, expected
   count zero implies P75 zero. A positive current count then implies Y(T)=1,
   already excluded by the current Y(T)=0 risk set. The old positive/zero ratio
   does not demonstrate *additional* primary-cohort loss in that situation.
   Missing history, lagged ratios and any later risk-set change still need audit.
3. Removing T predictors while retaining eligibility Y(T)=0 still uses knowledge
   of T. Such a model is a lagged-feature comparison **conditional on that gate**,
   not a demonstrated system issuable before T or with T entirely unavailable.
4. T-only predictors can validly predict future onset if available at issuance.
   Failure to improve T+2, or loss under a delay scenario, is not by itself proof
   of persistence, leakage or lack of biological relevance.
5. Three observed development years improve support but do not create prospective
   confirmation. Neither 2024 nor the consumed 2025 becomes a blind test set.

## 2. Scope boundary and scientific questions

| Tier | Required question | Decision/output |
| --- | --- | --- |
| A: primary ablation | Does current epidemiological information add value beyond lagged information? Do lagged climate and target-month thresholds add value? | Retain, remove for further study, conditional contribution, or inconclusive, per horizon/family |
| B: required diagnostics | Does the effect survive years, territories and historical profiles? Is it associated with onset versus continuation? How sensitive is it to a specified one-month information delay? | Explain failure modes and limitations; do not tune on these evaluation slices |
| C: consumed benchmark | Do already frozen models and alert policies transport from 2024 to 2025? | Separate descriptive transport report; no selection or refitting |

EXP02 owns sensitivity of labels/episodes to 5/7/9 years and epidemic-year handling.
EXP03 keeps the five-year reference for its primary paired contrasts. If EXP02
changes the adopted label definition, open a versioned replication of a bounded
set of contrasts; never silently relabel this run or compare different Y as the
same prediction task. These label diagnostics need no predictive training by
default; the rolling predictive scheme is not imposed on every EXP02 analysis.

Continuous recalibration, feedback learning from each false alert, hyperparameter
search, models per territory/profile, new population data, a full missingness or
nowcasting study, and prospective deployment are outside this revision. They belong
to later experiments. Predeclared historical refits per evaluation cut remain
necessary for evaluation; they are not adaptive production learning.

## 3. Population, targets and time contract

- Unit: municipality, origin month T, exact target S=T+h, h in {1,2}.
- Population: the governed 76 municipalities in Meta and Tolima; no outcome-driven
  municipality selection. Report actual coverage rather than assuming 76 complete years.
- Y(s)=1 iff general-dengue count at s is strictly greater than type-7 P75 of the
  previous five observations of the same calendar month; retain epidemic years.
  Covered zero counts are valid; missing history or outcomes remain unknown.
- Primary eligibility: known Y(T)=0 for every variant/objective in a paired cell.
  Never use Y(T+1) to admit a T+2 forecast.
- Onset O_h(T)=1 iff Y(S-1)=0 and Y(S)=1. T+1 onset and excess are identical in
  this risk set. T+2 excess E_2(T)=Y(T+2) is a secondary control only.
- Missing labels do not become negatives. Unknown predictors/labels, embargo,
  ineligibility and unavailable predictions have separate exclusion counters.
- Learned encodings, scaling, imputation and models use training data only;
  calibration uses its own earlier role; thresholds use selection only.
- Every predictor records source event month, transformation, latest source month,
  assumed publication availability and as-of policy. Recompute target thresholds
  from historical observations, never from supplied future labels or zones.

Within T+2 evaluation, classify outcomes as onset (0,1), continuation (1,1), or
no excess (*,0), using (Y(T+1),Y(T+2)). Preserve an earlier-T+1-onset marker in the
audit. At T+1 continuation has no support under Y(T)=0: report N/A, not zero evidence
for or against persistence. These are evaluation strata, never X or selection filters.
An alert for a continuation is false for the exact-onset task but can be correct
for excess. Do not mix those two false-alarm definitions.

## 4. Feature blocks and finite variant matrix

Use the existing sources, with explicit new recipes rather than ambiguous aliases.
No feature group may leak through an excluded equivalent encoding. Statistical
correlation between retained groups is expected; ablation measures conditional
predictive contribution and does not identify a unique biological cause.

| Symbol | Block and exact content | Latest event month |
| --- | --- | --- |
| B | Base: dengue lags 1/2/3, severe-dengue lags 1/2; dengue mean of T-1,T-2,T-3; dengue difference T-1 minus T-2; existing month sine/cosine; categorical municipality | T-1 for observations; calendar known at T |
| U | Current raw state: dengue and severe-dengue counts at T; dengue difference T minus T-1; dengue mean of T,T-1,T-2 | T |
| L | Reconstructed zone and excess indicator at T-1 | T-1 |
| Z | Reconstructed zone and excess indicator at T | T |
| R- | Notification observed/expected representation at T-1, specified below | T-1 |
| R0 | Same representation at T | T |
| F | Historical type-7 P25/P75 for target calendar month S from the previous five years | At most T-1 for h=1/2; assert from actual source dates |
| C- | Each of the existing 15 climate recipes shifted back exactly one month: current aggregates become lag1; original lag1 becomes lag2; original lag2 becomes lag3 | T-1 or earlier |
| Cm | Existing 15 mixed current/lag climate recipes, retained as a retrospective availability comparison | T |

Define A=U+Z+R0 (all current epidemiological encodings) and K=F+L+R-
(historical channel context). C- and Cm are alternatives, never combined in one
variant. Reuse identical climate source/transform/offset columns across the two
alternatives where appropriate; do not duplicate columns or fit identical sets.
Z's current excess flag is constant zero within eligibility; report that fact,
do not claim it has learned value. Keep its group semantics auditable.

### Notification ratio, zero references and missingness

Use the term **notification observed/expected**, not standardized incidence or
population relative risk. For s=T or T-1, let E_s be the mean of the five prior
same-calendar-month counts. Define two columns:

- `log1p(count_s / E_s)` if E_s>0, otherwise the sentinel 0 when E_s=0;
- `expected_zero_s = 1[E_s=0]`.

If count or any required history is missing, both are unavailable. A zero sentinel
is only a numerical representation with an accompanying flag, never an assertion
that positive/zero has ratio zero. The matching raw count is retained (in B at
T-1, in U when A is present); report affected rows/events explicitly. R0-only
diagnostics inside Y(T)=0 have no positive/zero examples under the same reference.
No pseudocount, undocumented clipping or automatic transfer of Umaña's 0.001.
This representation is a methodological proposal to encode in the new protocol,
not an empirically validated improvement. Missing history remains distinct from zero.

### Canonical sets (16), with immutable IDs in the revised protocol

| ID | Name | Composition |
| --- | --- | --- |
| V00 | base_lagged | B |
| V01 | base_plus_target_thresholds | B+F |
| V02 | base_plus_recent_channel_state | B+L+Z |
| V03 | base_plus_current_notification_ratio | B+R0 |
| V04 | base_plus_lagged_climate | B+C- |
| V05 | base_plus_historical_channel | B+K |
| V06 | base_plus_current_state | B+A |
| V07 | full_without_current_state | B+K+C- |
| V08 | full_without_climate | B+K+A |
| V09 | full | B+K+A+C- |
| V10 | full_without_target_thresholds | V09 minus F |
| V11 | full_without_recent_channel_state | V09 minus L and Z |
| V12 | full_without_notification_ratios | V09 minus R- and R0 |
| V13 | full_mixed_climate | B+K+A+Cm |
| V14 | base_plus_complete_channel | B+F+L+Z+R-+R0 |
| V15 | full_without_complete_channel | B+U+C- |

V14 and V08 are now distinct: V08 includes U; V14 does not. The previous ten-set
alias is historical and must not be reused mechanically. Expand groups, deduplicate
identical feature recipes, validate uniqueness, then derive fit counts. Do not
pretend the revised `full` is the same predictor set as legacy `full`.

Four primary contrasts, left minus right, at the one prespecified budget:

| ID | Contrast | Attribution |
| --- | --- | --- |
| P1 | V06 - V00 | Add all current epidemiological state to lagged history |
| P2 | V09 - V07 | Add current state in the presence of historical channel and lagged climate |
| P3 | V04 - V00 | Add lagged climate to the base |
| P4 | V01 - V00 | Add historical target-month thresholds to the base |

Secondary contrasts preserve the original questions and bound the expansion:
V02-V00 (recent channel), V03-V00 (current ratio), V05-V00 (historical channel),
V14-V00 (complete channel), V09-V00 (full versus base), V09-V10 (remove thresholds),
V09-V11 (remove recent channel), V09-V12 (remove ratios), V09-V08 (remove climate),
V09-V15 (remove complete channel), V07-V00 (lagged combined information),
V13-V09 (mixed versus lagged climate). These are 12 secondary contrasts, 16 total;
report whether an effect is incremental or a block-removal loss. No unlisted
factorial combinations or post-hoc winning-budget search.

All 16 variants use onset, all three existing fixed families, both horizons and
four temporal cuts: **384 model/preparer/calibrator cells**. Add excess controls
only for V00 and V09, T+2, all three families and four cuts: **24 cells**.
Total planned maximum: **408 fits**, compared with legacy 240. The two objective
contrasts use identical X/cohort/roles and the same onset-based alert policy.
The remaining excess objectives are explicitly outside scope. At T+1 never
duplicate an excess arm. Threshold budgets, contrast calculations, delay diagnostics
and benchmark inference add zero model/preparer/calibrator fits.

## 5. Temporal protocol and fixed alert policy

| Cut | Train targets | Calibration targets | Selection targets | Evaluation targets |
| --- | --- | --- | --- | --- |
| development_2020 | 2012-01..2018-12 | 2019-01..2019-06 | 2019-07..2019-12 | 2020-01..2020-12 |
| development_2021 | 2012-01..2019-12 | 2020-01..2020-06 | 2020-07..2020-12 | 2021-01..2021-12 |
| development_2022 | 2012-01..2020-12 | 2021-01..2021-06 | 2021-07..2021-12 | 2022-01..2022-12 |
| stress_2024 | 2012-01..2022-12 | 2023-01..2023-06 | 2023-07..2023-12 | 2024-01..2024-12 |

Preserve the horizon embargo requiring origin >= previous role's last target.
Report actual months (including T+2 January exclusions), never label nominal years
as complete coverage. Fit one model/preparer and sigmoid calibrator per cell using
the existing fixed family settings. No hyperparameter or calibration-method search.
2020-2022 provide development OOF predictions only for their source fit. Later
fits can use earlier development years as specified. Clustered uncertainty is
conditional on these historical fits; it is not uncertainty over future retraining.

Freeze the variant matrix, target, families, decision rule and selection policy
before development execution. Freeze any development-based shortlist and all
terminal artifacts **before opening either 2024 or 2025 outputs**. Prefer reporting
the full prespecified matrix; a shortlist is not required. The terminal 2024/2025
artifact uses training through 2022 and the two 2023 roles above, never 2020-2022
OOF predictions themselves as a replacement fitted model. No post-calibration refit.

### One budget, explicit exposure

`B_primary = 1.0` is the human-approved experimental comparison budget: one
false onset alert per monitored municipality-year. It was fixed before executing
EXP03 to provide a common, interpretable and reproducible comparison across variants.
The value is conservative; it is not validated operational capacity, clinical
equivalence, a deployment threshold or production authorization. It cannot be
optimized retrospectively on 2020–2022, 2024 or 2025. No model or champion is
selected or approved automatically.

For a paired comparison and role, define monitored exposure D as distinct
municipality-target months with governed source/outcome coverage and known current
state, after the role embargo, **before the Y(T)=0 eligibility filter**, divided by
12. Use the same D for all arms. The risk-set subset determines fit/evaluation rows;
ineligible covered months generate no onset alert. Also report eligible exposure
and common complete-feature exposure separately. Never silently change the
denominator to improve a burden rate or compare it to EXP01's eligible-exposure rate.

For 76 municipalities observed over six months, D = 76 × 6 / 12 = 38
municipality-years; floor(1.0 × 38) = 38 false onset alerts. This example assumes
all those months meet the frozen monitored-exposure conditions above.

Set selection cap to floor(B_primary * D_selection). Within each arm select the
threshold maximizing selection onset detections within that cap, keeping whole
score ties; then fewer false alerts, fewer total alerts, higher threshold. Include
the explicit no-alert policy. Preserve achieved selection counts and underspend.
Carry thresholds unchanged into evaluation. Equal caps do not ensure equal realized
burden; report realized differences, violations and uncertainty. No evaluation
retuning to force equality. The full legacy frontier may remain a labelled secondary
diagnostic; its points are correlated and cannot supply independent significance votes.

Continuous or outcome-triggered recalibration is outside EXP03. Selecting one
threshold per historical cut with earlier data is the evaluation procedure, not
learning automatically from later false alerts.

## 6. Pairing, coverage, profiles and bounded delay diagnostics

Primary contrasts share rows, labels, family, target, role dates and policy. Define
one common cohort per horizon/cut before feature projection, using the union of
required recipes for the 16 variants, and keep the excess control on that same
cohort. Report the selection induced by complete-case inclusion; it can favor
well-covered places even when all arms are paired. No variant may silently change
the primary cohort. Keep a full eligible-event denominator outside that intersection:
report onsets excluded from primary prediction, abstentions and coverage-adjusted
sensitivity (available detected onsets / all known eligible onsets). This diagnostic
does not turn an unknown outcome into a miss or a negative.

Secondary variant-specific coverage reports additional potentially scoreable
rows, municipalities and onsets. Without predictions there, call this potential
coverage, not achieved predictive benefit; no extra refits are added here.

Historical municipality profiles are fixed **per cut** from pre-evaluation history,
using the 60 calendar months ending at that cut's training-target end. Use only
covered observations, never convert missing to zero. The specification to encode is:

- history_insufficient: fewer than 48 covered months out of 60;
- intermittent: otherwise zero-month fraction >= 0.50;
- remaining municipalities: low/medium/high notification-volume tertiles, with
  boundaries computed from those municipalities' historical means only, equal
  municipality weight and type-7 quantiles; ties use <= for the lower category;
- if tertiles collapse or support is absent, emit an explicit collapsed/insufficient
  stratum; do not force equal group sizes or use evaluation outcomes to repair it.

These numerical cutoffs are transparent **design conventions**, not validated
epidemiological classifications. Freeze the rule before execution and retain the
computed boundaries and membership per cut. Report zero fraction, mean count,
coverage and historical onset count continuously alongside the categories. Profiles
are notification patterns, not population incidence. The old three-month stratum
may be retained as `recent_burden_stratum`, never as a historical profile. The
2024 profile assignment is also frozen for the 2025 transport benchmark.

For department/profile diagnostics, always show onsets, municipalities and years.
Use a prespecified interpretability floor of 10 onsets, 3 municipalities and 2
development years with onsets for a pooled group guardrail; this is a reporting
floor, not a power calculation. Insufficient support yields unknown, not pass.
Individual municipality sensitivities with zero onsets are N/A. Macro sensitivity
averages equally across municipalities with positive known support and explicitly
reports exclusions; macro burden/calibration use their own stated denominators.

### Delay diagnostic without new fitting

Predeclare one-month stale-input stress for V09 and V13, both horizons/families/cuts,
using their fitted models, calibrators and thresholds unchanged. Recompute current
raw counts, current zone, R0, current differences/means and current climate from
the latest complete month T-1; already-valid lagged sources stay at their original
dates. Target S and its historical thresholds remain tied to S. Do not simply
rename every lag or shift the outcome. Record effective source months for every
changed recipe and score on the identical evaluable intersection.

Report two interpretations explicitly:

1. Conditional feature stress: Y(T) is assumed independently known for the eligibility
   gate; this isolates stale predictor dependence. It is not evidence of real availability.
2. Strict availability audit: if current epidemiology is unavailable, Y(T) cannot be
   established under the primary rule. Report inability to issue/abstention and
   resulting coverage; do not secretly replace the gate with Y(T-1)=0.

Replacing current zone with the previous month's zone can introduce EXCESO or an
excess flag of 1 into a feature that was constant zero during training. Report
unseen categories, out-of-training ranges and unsupported rows, using the frozen
preparer's documented handling. Such a result measures input-distribution stress;
it cannot by itself attribute degradation to publication latency or persistence.

Changing the gate would change the population and estimand and belongs to a later
availability experiment. C- is only an event-time-lagged proxy until publication
dates are demonstrated. An observed-data vintage reconstruction is not required
in this bounded EXP03, and no claim of real-time effectiveness follows from it.

## 7. Metrics, uncertainty and decision language

Primary estimand for each contrast/horizon/family: paired difference in exact-onset
sensitivity at the prespecified selection-budget policy, **jointly with realized
false-alert burden**. Report counts, denominators and percentage points; no claim
of gain at equal realized burden when the burden actually increased.

Required metrics: eligible and covered onsets, detected/missed onsets, emitted and
false onset alerts, sensitivity, precision, FAR=FP/(TP+FP), FPR=FP/(FP+TN) if shown,
false alerts per monitored and per eligible municipality-year, and alert-month
fraction. At one horizon an alert is one municipality-target action; count unique
events. Do not sum T+1 and T+2 detections or burden as independent episodes. Report
nominal lead h separately from actual issuance-to-event time; actual lead remains
unavailable without publication/issuance evidence.

For same-target probabilities report AP (the existing grouped-tie convention),
prevalence, Brier, ECE/reliability bins and calibration slope/intercept when estimable;
AUROC is secondary. Report raw and calibrated diagnostics where retained, without
choosing a new calibration method. T+2 onset and excess AP/Brier use different
outcomes and cannot establish superiority by direct subtraction. Compare those
arms on common onset alert utility, while labelling probability metrics by target.

Use 2020-2022 pooled OOF predictions, unique source-cut keys and paired two-way
municipality/year cluster resampling, preserving full year blocks and identical
weights between arms. Provide 95% intervals for sensitivity difference and realized
false-alert-rate difference, valid-replicate counts and seed. At least three OOF
years with onset support are needed for the primary interval. Retain the existing
1000 draws as the baseline method; report sparse support and failed resamples.
No IID fallback, single-year confirmatory interval, or inclusion of stress/benchmark
years in development intervals. Three year clusters limit interval reliability;
the intervals are conditional retrospective descriptions, not calibrated guarantees
for future epidemic seasons or simultaneous confidence across all contrasts.

Retain monitored and eligible exposure by municipality/year/source cut, including
covered ineligible months with no prediction row. Apply the same cluster weights
to event counts, false-alert counts and these exposure denominators. Resampling
only complete-case prediction rows would estimate a different burden rate; holding
the exposure denominator fixed across draws is also incorrect. Report valid draws
per metric because a zero-onset draw can still have valid burden exposure.

Report each development year, pooled counts and an equal-year sensitivity summary,
alongside micro and equal-municipality summaries. A large year must not silently
become the sole basis for a stable-effect claim. Family/horizon/contrast multiplicity
is explicit: P1-P4 are primary, others exploratory, all pointwise intervals; no
global p-value, cherry-picked significant contrast or confirmatory superiority claim.

Decision record per contrast includes separate pass/fail/unknown assessments:

- aggregate benefit: effect size and interval, with per-year direction;
- operational burden: realized rate, delta, cap violation and its interval;
- department guardrail and historical-profile guardrail with support counts;
- probability calibration, coverage and delay limitations;
- evidence level: retrospective development, stress, or consumed benchmark.

Use zero deterioration as the default descriptive reference for subgroup
sensitivity/burden and same-target Brier; zero is not a proven clinical margin.
Positive aggregate point estimates do not override a harmful or unknown subgroup.
An unadjusted interval above zero can support a *candidate for further validation*,
not automatic selection. For removal, point equality or a non-significant difference
does not establish equivalence; any formal noninferiority claim requires separately
justified margins and power. Practical-importance margins and measured capacity
remain pending; do not invent them or recycle EXP00's different FAR guardrail.

Allowed conclusions: consistent retrospective contribution, horizon/profile-specific
contribution, additional detection at additional burden, current-state dependence,
candidate simplification requiring confirmation, or inconclusive. Do not classify
everything failing a significance threshold as useless. A continuation-heavy
pattern is evidence compatible with persistence, not its causal proof.

## 8. 2024 stress and consumed 2025 benchmark

Implement `consumed_2025_benchmark` as a separate inference/evaluation path, not a
fifth fitting window. Preserve EXP01's historical 2025 rejection and immutable
artifacts; introduce explicit EXP03 boundaries rather than disabling shared guards.

Before opening 2024 outputs, save the terminal fitted model, train-only preparer,
calibrator, threshold, selected B, feature schema, profile mapping, code/environment
and data identities for every prespecified terminal cell. Benchmark **all 102
terminal cells** (16*3*2 onset plus 2*3 T+2 excess) to avoid an informal shortlist;
this is inference, not 102 new fits. All 408 development/stress fits remain the
maximum. If an artifact cannot be serialized/reloaded reproducibly, fix persistence
before the authorized real run; never substitute a fresh fit during benchmarking.

Reuse exactly those terminal artifacts for 2024 and 2025. Expected counts for the
2025 path are zero model/preparer/calibrator fits, searches and threshold selections.
Verify artifact hashes before and after; never feed 2025 outcomes into adaptation,
selection or candidate flags. 2025 can enter rolling predictors or historical
references only when its event month is <= the individual forecast origin; future
months supply labels only. Frozen transformations are not frozen numerical input
values. Reading legitimate past observations is not re-estimating model parameters.

Known 2025 outcomes have already informed this project; freezing now cannot undo
that knowledge. Name every result `consumed_retrospective_benchmark`. It may expose
failure, but may not select another family, feature set, target, budget or calibrator.
Any subsequent redesign needs a new experiment/version and unobserved confirmation.

Before scoring, verify governed coverage/maturity from data provenance. Full-year
targets require origins 2024-12..2025-11 at T+1 and 2024-11..2025-10 at T+2, plus
labels and historical references. Calendar dates alone do not prove consolidation.
Audit role boundary embargo against the last 2023 selection target: do not reset
the embargo at January 2025. Report actual target months. If 2024 T+2 omits January
but 2025 includes it, show the annual coverage and a common-month sensitivity view;
do not silently compare different exposure as complete equal years.

Deliver annual/territorial/profile results first. A 2024-2025 count-pooled summary
is secondary descriptive context, recomputed from counts/exposure rather than an
unweighted average of percentages. Do not pool it with development uncertainty or
call two consumed years independent validation. V1/EXP00 numbers are contextual
unless population, target, horizons, rows and false-alert definitions align.
Reserve a future genuinely unexamined period separately; do not assume 2026 qualifies.

## 9. Result delivery contract — required for decision value

Create the following native artifacts in the protected experiment bundle. They
are required outputs of the future implementation, not files produced by this
documentation task. Extend the verified bundle manifest/schema consistently.
Keep row predictions and municipal identifiers local under the data policy;
MLflow receives only approved aggregate projections and accurate execution counters.

| Deliverable | Required content / decision served |
| --- | --- |
| scope_execution_receipt.json | Revised scope/protocol/matrix/commit/data/runtime hashes, B, freeze timestamp, counts by phase, evidence class, exclusions and deviations |
| variant_inventory.json | Canonical predictor recipes, latest source/availability dates, group unions, unique-set hashes, aliases, fitted and reused cell identities |
| oof_predictions.parquet (or equivalent native tabular artifact) | Municipality, origin/target, horizon, cut, objective, variant/family, true labels, risk eligibility, raw/calibrated score, threshold and alert, profile, coverage/exclusion reasons; unique keys and native provenance |
| selection_predictions.parquet | Protected selection-role rows, raw/calibrated scores, onset/excess labels, keys and role identity, allowing independent reconstruction of threshold optimality, whole ties and achieved cap |
| threshold_selection.json | Fixed policy, D and B, numeric threshold/no-alert state, achieved TP/FP/alerts, ties and selection-role identity for each cell |
| primary_contrasts.csv | P1-P4: paired detection and burden deltas/intervals, counts, per-year direction, all guardrails, and evidence class |
| secondary_contrasts.csv | All 12 secondary contrasts and two T+2 objective comparisons; no omitted adverse or null results |
| performance_by_group.csv | Department, municipality, historical profile, year; both arms, support, rates, uncertainty availability, micro/macro summaries |
| coverage_and_exclusions.csv | Source coverage -> embargo -> gate -> label availability -> common/variant predictors -> scoring; excluded onsets and abstentions by group |
| exposure_by_cluster.csv | Monitored/eligible/common exposure by municipality, year and cut, including covered ineligible months; identical paired cluster weights for burden uncertainty |
| error_types_and_delay.csv | Onset/continuation/no-excess alert decomposition; fixed-threshold stale-input stress and separate eligibility availability limitation |
| transport_2024_2025.csv | Frozen artifact IDs, annual results then contextual aggregate; zero-fit/zero-selection counters and benchmark label |
| model_artifacts/ | Reloadable terminal models/preparers/calibrators, feature schemas and checksums; protected native storage only |

The human-readable report and updated CONCLUSIONS.md must lead with answers to:
what helped, by how much and at what burden; for whom/which horizon; whether the
effect repeated; what disappeared under delay; and what decision is supported.
Every numeric finding links to a contrast/cell/artifact locator. Include:

1. A one-page decision table: group, paired comparison, detection/burden effect,
   interval/support, years/territories affected, recommendation and evidence level.
2. Primary paired-effect plot with uncertainty and burden alongside it.
3. Year-by-department/profile effect matrix with support counts.
4. Reliability and coverage/abstention views; 2024/2025 transport shown separately.
5. Explicit confirmed findings, interpretations, limitations, and next hypotheses.

No chart alone substitutes for the source table. No fabricated run IDs, probabilities,
models, operating-capacity values or prospective claims. Completion can conclude
INCONCLUSIVE and still be scientifically useful. G5 stays NOT_APPROVED and champion
not_selected until their separate decision process.

## 10. Implementation sequence and acceptance checks

This delivery changes narrative scope only. The next coding task should implement
one bounded sequence, preserving EXP00/EXP01 and unrelated EXP02 work:

1. Reconcile current main and the consolidated conclusions; capture legacy EXP03
   identity. Add an explicit revision/status check so an older approval cannot run
   the expanded scope. Update registry and scientific decision register by reference.
2. Implement feature provenance, B/A/K/C recipes, finite ratio handling, profiles,
   16 unique variants and the contrast map; generate the matrix from one source.
3. Implement fixed normalized budget, exposures, three OOF cuts, paired controls,
   metrics/uncertainty and guarded descriptive decisions.
4. Persist reloadable terminal artifacts, native predictions/selection evidence,
   bounded delay diagnostics and report tables.
5. Implement isolated 2025 inference admission and annual transport reporting.
6. Validate with generated data, independently review the method and code, encode
   the new protocol and hash consistently, then request the existing execution
   authorization against the clean reviewed identity. Do not execute real science
   or write permanent MLflow as part of this scope update.

Required generated-data acceptance checks:

- For each source cut and forecast origin, future-value perturbations cannot change
  that origin's predictors/eligibility or its already-fitted model/threshold. Profile
  membership ignores observations after its historical cutoff. An earlier evaluation
  year may legitimately affect a later cut's training; do not prohibit that declared
  rolling design. Changing stored evaluation-label fields with source observations
  fixed changes metrics only. Changing raw case counts can legitimately change
  predictors for subsequent origins; test as-of boundaries rather than freezing
  all observations throughout an evaluation year.
- B, K and C- source recipes never consume T observations. A removal removes all
  declared T epidemiological encodings; eligibility's T dependency remains explicit.
- Exact calendar lags do not bridge gaps. Missing/zero history and positive/zero
  examples retain distinct reasons; prove the positive/zero Y(T)=1 exclusion above.
- Canonical expanded sets are unique; each fits once; aliases/contrasts reuse cells.
  Expected maximum 408 fits and 102 terminal cells, with zero T+1 excess duplicates.
- Cohort hashes agree within primary comparisons and with the two excess controls.
  Denominator/coverage counts reconcile before/after gate and complete-case filters.
- Whole-score ties, no-alert policy, achieved selection burden and realized
  evaluation burden have boundary tests; budget metadata is mandatory.
- One-year/zero-onset/zero-alert/sparse-profile cases yield explicit N/A or unknown,
  not fabricated perfect metrics or a passed guardrail. Micro/macro denominators reconcile.
- Bootstrap pairs source rows and clusters; 2024/2025 never enter development
  intervals/flags. All listed contrasts, including adverse cases, are emitted.
- Delayed transforms update all dependent recipes; they cannot claim Y(T) is known
  when current sources are absent. Frozen model states/thresholds remain unchanged.
- Serialized/reloaded terminal predictions agree within a predeclared numeric
  tolerance; 2025 cannot reach any fit/calibration/threshold-selection interface.
  Perturbing 2025 labels cannot change 2024 predictions, configuration or shortlist.
- Native rows reconstruct reported metrics, thresholds, exposures and contrasts;
  selection rows reconstruct threshold search/ties/cap, and paired exposure draws
  reproduce the monitored-population burden estimand rather than a complete-case rate;
  MLflow aggregate projection excludes private row/municipality content and records
  zero versus absent execution counters honestly.

Run focused checks per [testing guide](../../../TESTING_GUIDE.md), then remote CI.
Synthetic PASS establishes implementation behavior, not a scientific finding.
The expanded experiment is complete only when all required tiers and output
contracts are implemented; missing actual 2025 data may make its execution explicitly
not_evaluable, but cannot justify silently dropping the benchmark implementation.

### Open decisions before real execution

| Item | Current status | Rule |
| --- | --- | --- |
| Numeric B_primary and its research/operational interpretation | Human-approved 1.0 in protocol 2.0.1 | Experimental comparison only; fixed before execution, never outcome-selected |
| Practical effect / noninferiority margins and actual capacity | Not established | Report effects and uncertainty; make no formal clinical-usefulness/equivalence claim |
| 2025 coverage, consolidation and historical publication availability | Unverified | Validate under authorized access; missing evidence stays a limitation |
| Executable revised protocol, counts and identity | Implemented; 408/102 retained | See versioned validation/review; older evidence does not authorize execution |
| Labels after EXP02 | Five-year reference retained provisionally | Changes require versioned replication, never silent relabeling |

