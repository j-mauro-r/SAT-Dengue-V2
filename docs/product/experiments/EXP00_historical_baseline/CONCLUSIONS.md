# EXP00 — Historical baseline conclusions before Kedro

## Status and decision

**Historical baseline registered; reproducibility verified; scientific outcome negative.**
EXP00 is `retrospective_baseline_registration`: a protected replay of saved components
and accepted pre-Kedro results. It is neither a new training experiment nor a test of a
new predictive hypothesis. All six candidate/horizon procedures remain
`does_not_meet`; **G5 is `NOT_APPROVED` and champion is `not_selected`**.

Its reproducibility question is: does the guarded Kedro replay preserve the accepted
historical results without model/preparer fits, recalibration, hyperparameter search,
threshold selection or model selection? The stored evidence answers **yes**. The
scientific question for later work is different: can a procedure improve onset detection
while satisfying the frozen false-alert constraint? EXP00 supplies a reproducible
**negative baseline**, not an operationally approved model.

**Confirmed:** all six models detect more onsets than same-horizon persistence, but
all exceed its monthly-excess false-alarm ratio by more than the permitted 5 percentage
points (pp). The principal failure is the detection/burden trade-off at the retained
thresholds. Predicting monthly excess was insufficient for acceptable onset warning
in these procedures and this consumed block. This is a descriptive finding, not proof
that the excess target, climate, endemic channel or algorithm family caused the failure.

## Evidence identity, integrity and replay

The [EXP00 protocol](protocol.json) owns intent and limits. Manifests, provenance,
audit and receipt own identity; the historical bundle owns the original scientific
result; the replay checks parity; SQLite verifies formal registration.

| Identity | Verified value |
| --- | --- |
| Hypothesis label | `EXP00-H0` — reproducibility, no new predictive hypothesis |
| Replay commit, clean at registration | `bebed44f79c10ef584b748dc33fcdc0933c0391b` |
| Canonical protocol SHA256 | `4f8e32d8c70ba1661b84efca3cb1cc25288335bbceb2508cec970231756b920b` |
| Original historical bundle | `768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35` |
| Historical manifest SHA256 | `5a526fa996112c86b014c533260f234b94c7c31bbcf47fa465fd61480c9b768f` |
| Replayed evaluation bundle | `f01fae3594249ab51fe3e5a19d3f8b88a0c9d2d59af648bddfcf4f01a63e8a10` |
| Pipeline identity | `d68ad5b031432f9480fd31a646198e3a5a9d3d7237f7eb6aa2599af08335291f` |
| Resolved configuration SHA256 | `9b13cc79cca3c5bd0ba9892ddee8c78f48632780b9baf98d357e470e61a14a4f` |
| MLflow experiment / scientific tag | `sat-dengue-bounded-v1` / `experiment_id=EXP00` |
| Parent run | `4a93225adb404e20a191a55b92f69457` |
| Parent start–end (UTC) | `2026-10-25T22:30:27.974Z`–`2026-10-25T22:36:12.362Z` |
| Seed / evaluated targets | `42` / `2025-01..2025-12` |

| Procedure | Child run verified in SQLite |
| --- | --- |
| XGBoost T+1 | `943290e169484064a7849adad653bdf5` |
| LightGBM T+1 | `5a46d1fca0cf4352a6748bca7b016c74` |
| GAM T+1 | `424e90ea317f4ad6b08c87ce0077f730` |
| XGBoost T+2 | `c5108cc27baa4af38e449454cfbc776f` |
| LightGBM T+2 | `46b32f3f7f094e5abfb342eefb5f7702` |
| GAM T+2 | `835bf433951e4a44b609fd3314d3a366` |

All seven runs are active and `FINISHED`, with verified EXP00/protocol tags; exactly
these six children link to the parent. Their family, horizon, decision, timestamps,
artifact URIs and ten logged metrics per child agree with native evidence. The
parent's receipt and uploaded JSON artifact are byte-identical. Its provenance
links the pipeline, environment, inputs and metric-definition hashes; all 156
recorded code/configuration files match the recorded Git commit. The five embedded
authority documents and their hashes match the current referenced contracts.

Integrity checks verified exact manifest membership, lengths and SHA256 for all
37 historical payloads and 20 replay payloads. The ten common scientific files are
**byte-identical**, stronger than migration's numeric tolerances: `metrics.csv`,
`comparison.csv`, `uncertainty.csv`, `predictions.csv`, and both horizons' evaluation
indices, event contexts and saved resampling indices. No scientific discrepancy was
found between the original result, replay and formal tracking.

The replay audit and parent MLflow metrics explicitly record **zero** model fits,
preparer refits, calibrator fits, searches and threshold selections. These are
present zeros, not missing counters. The historical `fit_accounting.json` records
six completed model fits and six preparer fits from the original final execution;
its calibration/search/threshold counters are zero. These describe different
operations and do not conflict. Saved components, nonempty predictions, matching
metrics and guards explain why zero replay fits mean valid execution rather than
an accidentally empty run. The replay audit also records 160 development models
replayed; replaying them is not training them. Some retained decision JSON still
contains pre-final `actual_final_components=not_fitted_pending_authorization`
planning metadata. Completed fit accounting and training provenance establish the
actual historical execution; that frozen planning field is not current run status.

## Historical design and population

Three frozen excess-classification families (XGBoost, LightGBM and GAM) were evaluated
separately at each horizon against persistence. Configurations, original-probability
choices and thresholds were retained from development before the final historical
fits. Historical final training targets run from January 2012 through December 2024
for T+1 and November 2024 for T+2, with 11,856 and 11,780 training rows respectively.
Replay reuses the saved final models and preparers.

**Cohort C25**, used by every row in the reference table below, is the same complete
912 municipality–target-month keys: 76 municipalities × 12 months, January–December
2025. Both horizons have identical target event contexts: 237 monthly excess
positives, 675 negatives and 86 onsets. All labels/predictions and previous-month
contexts are available; no unknown-event rows were silently dropped. The cohort
contains 29 Meta municipalities (348 rows, 40 onsets) and 47 Tolima municipalities
(564 rows, 46 onsets).

T+1 origins span December 2024–November 2025; T+2 origins span November 2024–October
2025. A prediction at origin T targets **exactly S=T+h**, not any event within the
next h months. Both probabilities describe excess at S. An onset at S requires
excess at S and no excess at exactly S−1. S−1 is event-evaluation context; it is not
a future input supplied to a T+2 forecast. The saved training/cohort availability
checks pass, but retrospectively consolidated data do not establish real-time
publication availability. Nominal T+2 lead time is therefore not demonstrated
operational warning lead time.

2025 is **consumed**, exclusively available for replay and retrospective comparison.
It is not a blind confirmation set or prospective validation, cannot be reused for
fitting, calibration, threshold/model selection or hypothesis selection, and cannot
change the frozen disposition. Later experiments may have been designed with
knowledge of these outcomes.

## Units and comparator semantics

An emitted alert is one positive decision for a municipality and exact target month
at one horizon. Consecutive alerts remain separate rows; they are not collapsed
into warning episodes. Each row maps to one target, not multiple future events.
Detected onsets count unique evaluable municipality–target onset events flagged by
that horizon's alert. Repeated excess months can produce many true-excess alerts
without detecting additional onsets.

- `onset_sensitivity = detected_onsets / real_onsets`; missed onsets = real − detected.
- `false_alerts` counts emitted alerts where **monthly excess Y(S)=0**.
- `false_alarm_ratio = false_alerts / emitted_alerts`, not FP/all negative rows and
  not the fraction of alerts that fail to identify an onset.
- `emitted_alerts − false_alerts` counts true-excess alert rows, not detected onset
  events. XGBoost T+1 illustrates the difference: 350 − 177 = 173 true-excess alerts,
  but only 22 detected onsets. The remaining 151 concern continuing excess.

Persistence predicts excess at S whenever the current origin's endemic-channel
state is `EXCESO`. It is the frozen **primary operational comparator for both
horizons**. There is no separately evaluated endemic-channel forecasting arm in
these authorized final artifacts; do not invent one or double-count persistence
as independent channel evidence. Channel-derived state also defines the outcome.
At T+1, persistence cannot flag an onset because Y(S−1)=0 at an onset, while its
alert requires Y(T)=1 and T=S−1. At T+2 it can flag re-entry after an intervening
non-excess month; its 30 detections do not establish a better onset mechanism.

## Reference table for subsequent experiments

All rows use **C25: identical 912 rows, 76 municipalities and 86 real onsets**.
The interval column is the marginal 95% interval for **sensitivity difference
versus same-horizon persistence**, in pp; it is not an absolute sensitivity interval.
“Reference” is not approval. These results are comparable only under the event,
cohort, alert-unit and horizon conditions above.

| Procedure | Detected / real | Missed | Sensitivity % | Alerts | False alerts | FAR % | Δ sensitivity interval (pp) | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Persistence T+1 | 0 / 86 | 86 | 0.00 | 253 | 102 | 40.32 | Self-difference | reference |
| XGBoost T+1 | 22 / 86 | 64 | 25.58 | 350 | 177 | 50.57 | [18.91, 32.04] | `does_not_meet` |
| LightGBM T+1 | 34 / 86 | 52 | 39.53 | 403 | 218 | 54.09 | [28.95, 48.96] | `does_not_meet` |
| GAM T+1 | 20 / 86 | 66 | 23.26 | 321 | 151 | 47.04 | [15.07, 29.76] | `does_not_meet` |
| Persistence T+2 | 30 / 86 | 56 | 34.88 | 281 | 132 | 46.98 | Self-difference | reference |
| XGBoost T+2 | 48 / 86 | 38 | 55.81 | 469 | 289 | 61.62 | [15.66, 25.93] | `does_not_meet` |
| LightGBM T+2 | 55 / 86 | 31 | 63.95 | 530 | 336 | 63.40 | [22.22, 35.44] | `does_not_meet` |
| GAM T+2 | 62 / 86 | 24 | 72.09 | 611 | 406 | 66.45 | [29.67, 45.45] | `does_not_meet` |


No frozen candidate is an acceptable operational benchmark on its own. For T+1,
**LightGBM is the sensitivity reference** (34 detections), with the highest AUROC
and lowest Brier; XGBoost is the AP reference and GAM the lowest-burden candidate.
For T+2, **XGBoost is the lower-burden/probabilistic reference** among candidates;
GAM supplies the sensitivity ceiling (62 detections), and LightGBM lies between
these operating points. These are descriptive roles, not a new selection. Under
the actual policy, AP can rank only eligible candidates; none is eligible.

At the observed frozen thresholds, persistence and all three candidates belong to
the sensitivity/false-alert trade-off frontier within each horizon: moving to a
higher-detection point also increases false-alert counts and FAR. This is a frontier
of four retained operating points, not a newly searched threshold curve. No family
dominates all relevant metrics and burden simultaneously.

## Frozen policy, uncertainty and failure margin

The [champion policy](../../stage-5/champion_decision_policy_v1.json) requires at least
**+10 pp onset sensitivity** versus persistence and at most **+5 pp FAR increase**.
Research acceptance additionally requires the lower onset-gain bound to meet +10 pp
and the upper FAR-increase bound to stay at or below +5 pp. AP ranking is separate
by horizon, restricted to eligible candidates. G5/champion approval remains human.

The annual FAR caps implied by the same-horizon reference are **45.3162% for T+1**
and **51.9751% for T+2**. These differ from the retained development-selection caps
of 32.5862% and 35.8642%; the rule is the same, but the reference population changes.
Neither cap is an absolute number of false alerts. Thresholds remain frozen.

| Procedure | Δ sensitivity pp | Δ FAR pp | 95% Δ FAR interval pp | FAR above annual cap pp |
| --- | --- | --- | --- | --- |
| XGBoost T+1 | 25.58 | 10.26 | [6.80, 12.60] | 5.26 |
| LightGBM T+1 | 39.53 | 13.78 | [10.14, 15.95] | 8.78 |
| GAM T+1 | 23.26 | 6.72 | [2.15, 9.30] | 1.72 |
| XGBoost T+2 | 20.93 | 14.65 | [12.85, 16.57] | 9.65 |
| LightGBM T+2 | 29.07 | 16.42 | [13.91, 18.78] | 11.42 |
| GAM T+2 | 37.21 | 19.47 | [16.50, 22.12] | 14.47 |


All onset-gain intervals exclude zero and their lower bounds exceed +10 pp. All
FAR-increase intervals exclude zero, every point exceeds +5 pp, and every upper
bound exceeds +5 pp. GAM T+1's FAR-increase interval crosses the +5 pp boundary;
its failing point estimate still fixes `does_not_meet`. None can be promoted by
choosing a favorable endpoint or replacing the frozen joint rule.

The [evaluation contract](../../stage-5/model_evaluation_contract_v1.json) specifies
2,000 paired circular moving-block draws, block length three months, seed 42,
2.5th/97.5th percentiles. Whole municipal panels move together; families and
persistence share indices within a horizon. Original S/S−1 contexts remain intact
at resampled joins. All 2,000 draws are valid for each stored interval. These are
candidatewise marginal intervals in one year, not simultaneous family intervals,
municipality-independent resampling or post-selection confidence. Twelve original
months and temporal dependence limit effective information; 2,000 draws do not
create 2,000 independent observations.

`uncertainty.csv` names the metrics but stores **candidate-minus-persistence** bounds.
Its reference [0, 0] rows are self-differences, not zero uncertainty in persistence.
There are no saved family-versus-family or cross-horizon intervals to establish
that their differences exceed uncertainty, nor stored final AP/AUROC/Brier intervals.
In particular, LightGBM T+1's small AUROC/Brier advantage over XGBoost cannot support
an inferential superiority claim.

## Operational burden and horizon comparison

The following are **derived descriptive ratios**, not additional frozen criteria:
false alerts/detected onset, emitted alerts/detected onset, and counts/76 complete
municipality-years. Alert-month share is emitted alerts/912. A ratio per detected
onset measures workload per detection; it does not assign each false alert to an
individual episode. Persistence T+1 has no detections, so its per-detection ratios
are undefined. Persistence T+2 has 4.40 false and 9.37 emitted alerts per detection.

| Procedure | False / detected | Alerts / detected | Alerts / municipality-year | False / municipality-year | Months under alert % |
| --- | --- | --- | --- | --- | --- |
| XGBoost T+1 | 8.05 | 15.91 | 4.61 | 2.33 | 38.38 |
| LightGBM T+1 | 6.41 | 11.85 | 5.30 | 2.87 | 44.19 |
| GAM T+1 | 7.55 | 16.05 | 4.22 | 1.99 | 35.20 |
| XGBoost T+2 | 6.02 | 9.77 | 6.17 | 3.80 | 51.43 |
| LightGBM T+2 | 6.11 | 9.64 | 6.97 | 4.42 | 58.11 |
| GAM T+2 | 6.55 | 9.85 | 8.04 | 5.34 | 67.00 |


For example, LightGBM T+1 gives 34/86 = 39.53% sensitivity and 218/403 = 54.09% FAR;
its 6.41 false alerts per detection do not mean 34 true alerts. GAM T+2 gives
62/86 = 72.09% sensitivity but 406/611 = 66.45% FAR and alerts in 67.00% of all
municipality-months. Relative to persistence T+2 it gains 32 detections while
adding 330 alerts and 274 false alerts. Higher sensitivity alone is inadequate.

The common target cohort permits a descriptive horizon comparison, but origins,
training cutoffs, probabilities and retained thresholds differ. From T+1 to T+2,
XGBoost gains 26 detections with 119 more alerts and 112 more false alerts;
LightGBM gains 21 with 127 and 118; GAM gains 42 with 290 and 255. T+2 AP/AUROC
are lower and Brier is worse for every family, despite higher onset sensitivity.
This is consistent with a more permissive alerting pattern, not evidence of greater
predictive discrimination. EXP00 cannot isolate how much of the sensitivity change
is caused by alert volume, horizon, threshold or other procedure differences.
Do not sum detections across horizons: the same 86 target onsets occur in both.

## Probabilities and retained calibration

AP, AUROC and Brier evaluate **monthly excess**, not the onset event. AP is
non-interpolated average precision and is not alert precision (1−FAR). Brier is
mean squared probability error against the 237/912 excess positives (25.9868%).
Persistence has deterministic scores, with AP/AUROC T+1 0.4746/0.7430 and T+2
0.4299/0.7166; its Brier is intentionally unavailable, not zero or a model-comparable
calibrated probability score.

| Procedure | AP | AUROC | Brier | Frozen threshold | Mean probability % |
| --- | --- | --- | --- | --- | --- |
| XGBoost T+1 | 0.6757 | 0.8189 | 0.1433 | 0.306252956390 | 33.36 |
| LightGBM T+1 | 0.6689 | 0.8192 | 0.1431 | 0.284423430136 | 33.14 |
| GAM T+1 | 0.6448 | 0.8093 | 0.1477 | 0.377124654723 | 33.21 |
| XGBoost T+2 | 0.5611 | 0.7638 | 0.1672 | 0.314685821533 | 36.00 |
| LightGBM T+2 | 0.5469 | 0.7585 | 0.1689 | 0.269266008230 | 35.92 |
| GAM T+2 | 0.5210 | 0.7465 | 0.1767 | 0.215988799475 | 36.59 |


All six retained decisions contain an available sigmoid calibrator fitted on
August–September 2023, but the November–December 2023 calibration comparison chose
**`original`**, reason `brier_not_improved`. Final/replayed probabilities equal
`probability_raw` for every candidate row: the sigmoid transformation was not applied.
Thresholds selected on February–March 2024 were retained unchanged. No calibrator
was fitted or selected during EXP00 replay.

The inherited probability choice and threshold were transferred to final models
refitted through late 2024. Their probability calibration did not receive a new
independent validation for those final fitted score distributions. Calling them
“calibrated probabilities” would overstate the evidence. Mean probabilities around
33% (T+1) and 36% (T+2) exceed observed excess prevalence 25.99%, a descriptive
aggregate overprediction signal, not a full reliability analysis or proof of its
cause. Small Brier differences do not compensate for the observed operational failure.

## Territorial and development evidence

Department figures below are descriptive, reconstructed from the same saved
predictions and reconciled with the existing breakdown metrics. They are not
independent replications or territory-specific acceptance tests.

| Procedure | Meta detected / 40 | Meta FAR % | Tolima detected / 46 | Tolima FAR % |
| --- | --- | --- | --- | --- |
| XGBoost T+1 | 13 | 40.21 | 9 | 62.73 |
| LightGBM T+1 | 18 | 44.08 | 16 | 65.10 |
| GAM T+1 | 11 | 38.55 | 9 | 57.75 |
| XGBoost T+2 | 23 | 51.72 | 25 | 71.31 |
| LightGBM T+2 | 26 | 52.38 | 29 | 73.38 |
| GAM T+2 | 28 | 54.44 | 34 | 75.95 |


Tolima has higher FAR for every candidate/horizon; the aggregate masks substantial
territorial differences. For GAM T+2, Tolima contributes 259/406 false alerts and
34/62 detections, versus Meta's 147 false alerts and 28 detections. This does not
identify a causal territorial mechanism.

Municipal counts are sparse: 28 of 76 municipalities have no 2025 onset, so their
onset sensitivity is undefined rather than zero. Every procedure has municipal
alert-month counts ranging from 0 to 12. LightGBM T+1 has 12 municipalities with
no alerts; GAM T+2 has four. The five municipalities with most false alerts account
for 33/218 for LightGBM T+1 and 51/406 for GAM T+2. Separately, the top five by
detections account for 12/34 and 17/62. These separately ranked summaries describe
concentration; they neither identify the same five places nor select deployment
locations. Monthly operational breakdowns also reconcile with `metrics.csv`; no
post-hoc month was selected as the scientific comparison.

The replay's development summaries use four windows identified by cutoffs
2018-12, 2020-12, 2022-12 and 2024-06, with equal-window means rather than pooled
annual rates. They are different populations and fitted procedures from C25.

| Procedure | Development Δ onset pp | Development Δ FAR pp | 2025 Δ onset pp | 2025 Δ FAR pp |
| --- | --- | --- | --- | --- |
| GAM T+1 | 17.47 | 4.61 | 23.26 | 6.72 |
| LightGBM T+1 | 29.19 | 7.01 | 39.53 | 13.78 |
| XGBoost T+1 | 17.08 | 3.98 | 25.58 | 10.26 |
| GAM T+2 | 22.65 | 3.97 | 37.21 | 19.47 |
| LightGBM T+2 | 20.13 | 4.69 | 29.07 | 16.42 |
| XGBoost T+2 | 14.61 | 3.89 | 20.93 | 14.65 |


Five development point summaries meet the utility constraints; LightGBM T+1 does
not. None of those development point results establishes research acceptance.
The final annual comparison fails for all six. Development uncertainty uses all
256 ordered whole-window bootstrap draws from four windows and labels its bounds
`descriptive_sensitivity_only_four_clusters_not_calibrated_CI`. They cannot be
substituted for the final paired intervals or establish prospective transfer.
The burden deterioration is confirmed; temporal prevalence changes, calibration
transfer and threshold transport are possible explanations requiring separate tests.

## How a later experiment can surpass this baseline

Keep persistence as the contractual primary reference at each horizon and retain
the historical candidate frontier as secondary context. For an excess-target
procedure evaluated under this same contract, the existing +10 pp onset-gain and
+5 pp FAR-increase limits and their paired-bound requirements remain applicable;
this document introduces no new minimum gain against a historical model.

A defensible improvement claim must:

1. Declare comparable target keys, onset definition and S−1 context, horizon,
   outcome availability and inclusion rules, or quantify their differences.
2. Improve onset detection against its prospectively declared comparator, satisfy
   the applicable frozen false-alert constraint, and report total alerts, false
   alerts, missed onsets and exposure. A larger alert volume alone is insufficient.
3. Provide paired uncertainty where support permits, retaining temporal/spatial
   dependence and distinguishing point utility from research acceptance. Unsupported
   intervals are missing evidence, not automatic acceptance.
4. Show how results vary across relevant horizons, periods and territories without
   selecting a favorable subset after inspection; preserve full traceability of
   data, code, model, calibration choice and decision thresholds.
5. Reserve independent, previously unused evidence for any confirmatory or deployment
   claim, and establish real input availability before claiming operational lead time.

**EXP00 is not automatically EXP01's causal control.** EXP00 evaluates all C25 rows,
monthly-excess probabilities and a monthly-excess FAR. EXP01's direct-onset design
uses an at-risk cohort, different years and target rules, with onset-based false
alerts. Their raw FAR, AP and Brier cannot be compared as if they measured the same
event on the same rows. Even onset sensitivity requires matched event support and
eligibility. A valid comparison must preserve or explicitly align those definitions,
alert units, missingness and denominators; the later experiment's frozen internal
control owns its primary contrast. Do not retune or repurpose 2025 to construct it.

## Interpretation limits and hypotheses

**Confirmed:** complete replay parity, six negative utility decisions, a detection/
burden frontier, territorial heterogeneity and poorer T+2 discrimination despite
more detections. These support the negative historical baseline.

**Interpretation:** the frozen procedures allocate substantial alert volume to
continuing excess and non-excess months, leaving inadequate operational onset
warning at the approved constraint. The observed development-to-2025 deterioration
is compatible with poor transport of thresholds/probability behavior.

**Limitations:** one consumed year; only 12 temporal observations for block
resampling; marginal intervals without family-selection guarantees; sparse local
onsets; raw probability transfer to refitted final models; retrospective input
availability; no independent endemic-channel forecasting arm; and no prospective
or causal design. Original scientific input provenance is checked through recorded
identities, not a fresh audit of the underlying private raw datasets. Reproducibility
of recorded outputs does not independently establish their scientific validity.

**Hypotheses for separately authorized experiments:** direct onset modeling could
improve the trade-off; threshold/probability transport might explain deterioration;
and territorial variation might warrant a prospectively specified design. EXP00
neither confirms these mechanisms nor authorizes new fitting or new selection.
Its previous statement that it “confirms the hypothesis” motivating a later
iteration is therefore replaced by this bounded descriptive interpretation.

## Audit coverage and source locators

This audit read SQLite through `mode=ro&immutable=1`, without an MLflow client/server
or database writes. It checked the seven runs, parent links, parameters, conceptual
tags, historical/latest metrics, timestamps and artifact URIs directly. It verified
all manifest payloads and the ten common files, all 7,296 saved prediction rows,
all eight procedure/reference count rows, AP/AUROC for all eight and Brier for all
six models. Independent arithmetic checked the six sensitivity and FAR values,
retained threshold application, raw probability identity, and available territorial,
municipal and monthly operational metrics. The 38 finite development means (plus
two unavailable persistence Briers) and 12 development utility differences reconcile.

An independent local reviewer reconstructed **all 16 saved uncertainty intervals**
from original predictions/context and existing month-index draws, using separate
count/percentile arithmetic rather than the production metric function; endpoints
match exactly. This verifies calculations, not an independent dataset. No RNG,
new threshold, model inference, fit, recalibration or scientific replay was run.
The prior documented protected replay test result (78 passed, zero failed, eight
warnings) is historical evidence, not a test suite repeated by this audit.

Local source aliases (paths are repository-relative):

- **H:** `artifacts/model_final_evaluation/768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35`.
- **R:** `tmp/kedro-migration/replay-runs/d68ad5b031432f9480fd31a646198e3a5a9d3d7237f7eb6aa2599af08335291f/stages/evaluation/f01fae3594249ab51fe3e5a19d3f8b88a0c9d2d59af648bddfcf4f01a63e8a10`.
- **S:** `tmp/kedro-migration/replay-mlflow`; SQLite is `S/tracking.sqlite`;
  receipt is `S/receipts/4a93225adb404e20a191a55b92f69457.json` and its uploaded
  copy is `S/artifacts/4a93225adb404e20a191a55b92f69457/artifacts/4a93225adb404e20a191a55b92f69457.json`.

| Claim | Source locator |
| --- | --- |
| Frozen design and authority | `protocol.json`; [champion policy](../../stage-5/champion_decision_policy_v1.json); [evaluation contract](../../stage-5/model_evaluation_contract_v1.json) |
| Historical integrity and fits | `H/manifest.json` → `files`, `identity`; `H/run_summary.json`; `H/fit_accounting.json`; `H/preflight.json` |
| Replay identity, counts and availability | `R/manifest.json`; `R/provenance.json` → `execution`, `authorities`, `evaluation.source_provenance`; `R/audit.json` |
| Annual results and decision | `H/comparison.csv`, keyed by `candidate,horizon`; corresponding annual rows in `H/metrics.csv` |
| Uncertainty | `H/uncertainty.csv`, keyed by `candidate,horizon,metric`; `H/t{1,2}_resampled_month_indices.csv`; [interval implementation](../../../../src/sat_dengue/final_evaluation/evaluation.py) |
| Counts, probabilities, burden and territorial summaries | `H/predictions.csv` plus `H/t{1,2}_evaluation_context.csv` and evaluation indices; `H/metrics.csv` scopes `annual,department,municipality,period` |
| Thresholds, probability choice and timing | `H/*_retained_decisions.json` → `retained_threshold`, `retained_calibrator`, target windows; `H/*_training_provenance.json` |
| Development comparison and uncertainty | `R/development_window_metrics.csv`, `development_comparison.csv`, `development_breakdown_metrics.csv`, `development_utility.csv`, `development_descriptive_uncertainty.csv` |
| Event and alert units | [metric definitions](../../../../src/sat_dengue/metrics.py); [calibration/threshold contract](../../stage-5/probability_calibration_thresholds_contract_v1.json) |

**Final scientific conclusion:** EXP00 reliably preserves a negative historical
baseline: excess predictions contain discriminatory signal and improve onset
sensitivity over persistence, but all six retained procedures violate the approved
false-alert constraint. Future work must improve that joint trade-off under aligned,
frozen definitions and adequate independent evidence. This audit leaves all six
`does_not_meet` decisions, G5 `NOT_APPROVED`, champion `not_selected`, and the
prohibition on scientific reuse of consumed 2025 unchanged.
