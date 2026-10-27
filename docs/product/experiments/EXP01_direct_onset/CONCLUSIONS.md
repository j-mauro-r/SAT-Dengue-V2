# EXP01 — Direct prediction of episode onset

## Decision and evidence status

**Status: real execution completed and verified; results available with reservations.**
**Hypothesis classification: `INCONCLUSIVE`. G5: `NOT_APPROVED`. Champion: `not_selected`.**

**Confirmed:** direct-onset training does not improve T+1 in this experiment: the two
labels are identical within the shared non-excess-at-origin cohort, and all recorded
paired results coincide. At T+2, changing the target changes performance, but gains
vary with family, year and budget. Some 2020 development points detect more onsets
without more realized false alerts; none does so in 2022. Positive 2024 points are
retrospective stress evidence, not confirmation. Every paired confidence interval
is unavailable under the frozen dependence-aware rule.

**Interpretation:** EXP01 identifies where target choice can matter, but does not
establish a consistent, uncertainty-supported improvement at comparable false-alert
burden. Retain the paired excess control; do not switch objectives or select a
champion from these results. `INCONCLUSIVE` denotes insufficient evidence under the
frozen acceptance rule, not a broken bundle or a failed execution.

This document distinguishes **Confirmed** artifact-backed findings,
**Interpretation** supported explanations, **Limitation** constraints on inference,
and **Hypothesis** proposals requiring another authorized experiment. Numerical
results below are real EXP01 outputs; synthetic interface tests are not scientific
evidence here.

## Traceability and integrity

The [frozen protocol](protocol.json) owns the design. Identity comes from the native
manifest/provenance and MLflow receipt; `result.json` owns consolidated scientific
results; SQLite verifies tracking. The complete 36-case Cartesian design was
reviewed: two objectives × three families × two horizons × three windows.

| Identity | Verified value |
| --- | --- |
| Parent execution, UTC | 2026-10-26 23:15:45.894–23:33:10.321 |
| Executed commit, clean at run | `8bfd505ed2e74848b7c913be265b756ecc742edb` |
| MLflow container / scientific tag | `sat-dengue-bounded-v1` / `experiment_id=EXP01` |
| Parent UUID | `0cdad10bd8d440a6901b5570ae5aa288` |
| Tracking state | One parent and 36 correctly linked children, all `FINISHED`, active, tagged `verified`; `kind=real`, pipeline `exp01` |
| Canonical protocol SHA256 | `6be81e1b3226abc85cce94dcae7dba0c687282b7e0bc816ec460d033e445925b` |
| Pinned data-manifest identity (`data_version`; MLflow `input_sha256`) | `241aa320e2df20d1d4613c50c61d32b60f161a10d76931721131c93a544a213a` |
| Aggregate input-fingerprint identity (`data_sha256`) | `f449320b81e2b9961dc8e956609936d48ef518c36c2b63d35f6264dac9951ee3` |
| Bundle ID | `e566ad549441bc10602b44b59163815b0360018ca214824a3e9ef74d4e3bb608` |
| `result.json` SHA256 / bytes | `dc02130ff47b6b005548e6e14fbe4269374e2a8ad398151eda95e8187511b209` / 197,520,161 |
| `provenance.json` SHA256 / bytes | `846635db7539e9aea229c88e1af0127eb5f62ad9e9ba56bd333719f480942b40` / 22,690 |

Exact repository-relative sources:

- Bundle: `tmp/kedro-migration/exp01-runs/e566ad549441bc10602b44b59163815b0360018ca214824a3e9ef74d4e3bb608/`, containing `manifest.json`, `provenance.json`, `result.json` only.
- MLflow receipt: `tmp/kedro-migration/replay-mlflow/receipts/0cdad10bd8d440a6901b5570ae5aa288.json`; its uploaded parent artifact is byte-identical.
- Database: `tmp/kedro-migration/replay-mlflow/tracking.sqlite`, queried with `mode=ro&immutable=1`, without an MLflow client/server or migration.

**Confirmed:** manifest sizes and payload hashes match; the canonical manifest body
produces the directory/bundle ID. Protocol, data, commit, configuration, code and
environment identities agree between provenance, receipt and all relevant run
parameters. All 144 recorded public code/configuration hashes match the executed
commit; runtime and code inventories reproduce their recorded digests. Parent-child
IDs, run names, timestamps, artifact URIs, parameters and tags were extracted from
SQLite. Each child's AP, AUROC and Brier matches both metric history and latest
metrics exactly. All 18 arm pairs share cohort, ordered-predictor and role-data
hashes, including missingness, plus identical coverage. No material inconsistency
was found among these sources.

**Limitation:** this is an artifact/code audit, not a second experiment or a fresh
hashing of private scientific input files. Aggregate data-fingerprint identity and
pinned manifest identity are different objects, not competing hashes of one file.
No individual predictions are supplied; AP, AUROC, Brier, learned thresholds and
paired uncertainty cannot be independently recomputed from absent row probabilities.
Their stored values and implementation/lineage are checked, not reconstructed.

## Question, primary comparison and frozen design

**Question:** does learning exact episode onset detect more onsets than learning
monthly excess under the same development false-onset-alert cap?

There is **no single preselected winning family, horizon or budget**. The primary
comparison is the **entire matched-budget frontier**, separately for each family,
horizon and development window (2020 and 2022). Each family uses its first
predeclared Stage 4 configuration, with seed 42 and one thread. Family/horizon/budget
variation is prespecified sensitivity analysis; 2024 is reported separately as
stress. No evaluation-selected operating point is promoted to the primary result.

| Family | Frozen configuration |
| --- | --- |
| XGBoost | 80 estimators; depth 2; eta 0.05; lambda 1; alpha 0; max_bin 128; min_child_weight 5 |
| LightGBM | 80 estimators; 7 leaves; depth 3; learning_rate 0.05; lambda_l1 0; lambda_l2 1; max_bin 128; min_data_in_leaf 20 |
| GAM | n_knots 4; C 0.1 |

Both arms use the same operational cohort, evaluable intersections, ordered 29
predictors, train-only preparation, target-time partitions, family configuration,
seed, sigmoid method and decision rule. Their fitted probability targets differ
at T+2; onset alert utility always uses the same exact-onset label.

| Window | Training targets | Calibration targets | Threshold-selection targets | Evaluation targets / interpretation |
| --- | --- | --- | --- | --- |
| `development_2020` | 2012-01–2018-12 | 2019-01–2019-06 | 2019-07–2019-12 | 2020-01–2020-12; retrospective development |
| `development_2022` | 2012-01–2020-12 | 2021-01–2021-06 | 2021-07–2021-12 | 2022-01–2022-12; retrospective development |
| `stress_2024` | 2012-01–2022-12 | 2023-01–2023-06 | 2023-07–2023-12 | 2024-01–2024-12; known-year retrospective stress |

The horizon-dependent embargo requires origins at or after the preceding role's
target end. At T+2 it excludes 76 first-month target candidates in each calibration,
selection and evaluation window; evaluated target months therefore begin in February.
T+1 has no such excluded boundary month. Later windows intentionally include earlier
development evaluation years in training; these are rolling retrospective fits,
not independent prospective replications.

## Targets, calendar handling and usable support

`Y` denotes general-dengue count strictly above the same-calendar-month type-7 P75
of the previous five years, retaining epidemic years. Both horizons require observed
`Y(T)=0` at issuance; unknown current states are ineligible.

- **T+1:** onset is `Y(T)=0 and Y(T+1)=1`. Inside this cohort it is exactly the
  excess target `Y(T+1)`, explaining the identical training problem and recorded results.
- **T+2:** onset is `Y(T+1)=0 and Y(T+2)=1`. T+1 state is used only retrospectively
  to construct labels/evaluability. It is neither a predictor nor an operational
  eligibility filter. Origins with an earlier T+1 onset remain as negative exact-T+2
  onset examples, including continued excess.

**Confirmed by the executed code and paired hashes:** raw admission removes origins
after 2024-12, discards supplied labels/channel before semantic use, rebuilds the
historical channel, and derives T-or-earlier features. The ordered predictor projection
excludes future targets and `earlier_onset_t1`; all declared offsets are at most zero.
Missing exact-calendar history/outcomes are unavailable, never bridged or filled as
negative labels. No future outcome is admitted as X in this implementation.
**Limitation:** this does not establish that consolidated inputs were actually published
by historical issuance dates; retrospective real-time availability remains unproven.

Usable rows are identical for both arms and all three families within a horizon/window:

| Window | Horizon | Train | Calibration | Selection | Evaluation | Real onsets | Selection caps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| development_2020 | T+1 | 4358 | 227 | 149 | 661 | 69 | 0–102 |
| development_2022 | T+1 | 5395 | 424 | 422 | 693 | 89 | 0–388 |
| stress_2024 | T+1 | 6934 | 218 | 192 | 453 | 103 | 0–141 |
| development_2020 | T+2 | 4353 | 207 | 128 | 588 | 51 | 0–106 |
| development_2022 | T+2 | 5370 | 355 | 355 | 641 | 62 | 0–325 |
| stress_2024 | T+2 | 6930 | 193 | 153 | 414 | 61 | 0–128 |

Sources: `children[*].coverage`, `.operational_reference.real_onsets`, and frontier
budget keys. The population is 76 municipalities in departments 50 (Meta) and 73
(Tolima). Each nominal evaluation year has 912 municipality-month candidates before
eligibility/embargo. Operational and evaluable row counts coincide after these exclusions;
all reported evaluation frontiers have zero unavailable outcomes and missing predictions.
This is completeness within the recorded scope, not evidence of timely source reporting.

## Primary results across the full frontier

**T+1 — confirmed equivalence.** Across all nine family/window pairs and all 1,902
paired budget points, thresholds, detected onsets, false alerts, burden and utility
metrics are identical between arms; the sensitivity difference is exactly 0 pp.
The budgets are 0–102 in 2020, 0–388 in 2022 and 0–141 in 2024. Distinct training runs
were still performed; equality is not evidence of frozen-model reuse.

**T+2 — conditional gains, no consistent superiority.** The following summarizes
all 1,686 paired points, covering every integer budget. Differences are onset minus
excess; pp means percentage points. Gain/loss/tie counts refer only to detected
onsets. The last column lists **all** budgets where detections increase and realized
evaluation false alerts do not increase; this is a descriptive burden check, not a
new acceptance threshold or an operating-policy recommendation.

| Period | Family | B range | Gain / loss / tie points | Δ sensitivity, pp range | Δ false-alert count range | B with gain and no more false alerts |
| --- | --- | --- | --- | --- | --- | --- |
| Dev 2020 | xgboost | 0–106 | 51 / 39 / 17 | -17.65 to +11.76 | -51 to +82 | 60–63 |
| Dev 2020 | lightgbm | 0–106 | 16 / 78 / 13 | -27.45 to +9.80 | -95 to +51 | 24–25, 38–40 |
| Dev 2020 | gam | 0–106 | 63 / 30 / 14 | -15.69 to +21.57 | -36 to +67 | 29–31, 87–89 |
| Dev 2022 | xgboost | 0–325 | 59 / 147 / 120 | -17.74 to +12.90 | -59 to +109 | None |
| Dev 2022 | lightgbm | 0–325 | 94 / 194 / 38 | -16.13 to +8.06 | -72 to +137 | None |
| Dev 2022 | gam | 0–325 | 93 / 139 / 94 | -16.13 to +14.52 | -53 to +62 | None |
| Stress 2024 | xgboost | 0–128 | 41 / 54 / 34 | -29.51 to +13.11 | -54 to +30 | 40–43 |
| Stress 2024 | lightgbm | 0–128 | 65 / 58 / 6 | -16.39 to +29.51 | -44 to +53 | 16–19, 36–44, 48–61 |
| Stress 2024 | gam | 0–128 | 60 / 48 / 21 | -19.67 to +14.75 | -53 to +50 | 51–63 |

**Interpretation:** all three families have both positive and negative T+2 differences
in every period. In 2020, gains with no extra false alerts occur at only 4 XGBoost,
5 LightGBM and 6 GAM budget points. In 2022, **every positive detection difference
also incurs more false alerts**, for every family. In 2024 there are more favorable
segments, especially for LightGBM, but stress-only results cannot establish a champion.
Neighboring budgets often repeat one threshold/policy: counts are not independent
trials, success probabilities or statistical votes. Range endpoints can occur at
different budgets; do not combine the maximum gain with the minimum burden.

No pooled budget-weighted success score is used. Different selection supports make
absolute budget counts incomparable across years. The two development windows remain
separate; stress is not averaged into development evidence.

## Decision rule, realized burden and worked comparisons

For each development cap B, select whole score ties maximizing selection onset
detections subject to false onset alerts ≤ B; ties prefer fewer false alerts, then
fewer total alerts, then the higher threshold. `threshold=None` means no alerts.
The selected arm-specific thresholds are transferred unchanged to evaluation.
B is an absolute cap on **selection** false alerts, not an evaluation guarantee,
false-positive rate, monetary budget or common probability cutoff.

The bundle does not retain selection scores or achieved selection confusion counts,
so compliance cannot be independently recalculated here. Complete budget sequences
and the verified executed selector enforce the frozen rule; evaluation counts expose
its realized burden. Equal development caps must never be called equal realized burden.

The following XGBoost examples are arithmetic/operational illustrations, not a
post-hoc primary configuration. B=10 is displayed consistently across periods; the
2020 T+2 B=60 example additionally illustrates an exact equal-realized-false-alert
point from the complete favorable-segment table above.

| Case (XGBoost) | Arm | Threshold | Detected / real | Missed | Sensitivity | Alerts | False alerts | Precision | FAR | False / exposure-year |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 T+1 B=10 | excess | 0.365934 | 9/69 | 60 | 13.04% | 42 | 33 | 21.43% | 78.57% | 0.599 |
| 2020 T+1 B=10 | onset | 0.365934 | 9/69 | 60 | 13.04% | 42 | 33 | 21.43% | 78.57% | 0.599 |
| 2020 T+2 B=60 | excess | 0.426955 | 28/51 | 23 | 54.90% | 268 | 240 | 10.45% | 89.55% | 4.898 |
| 2020 T+2 B=60 | onset | 0.232428 | 29/51 | 22 | 56.86% | 269 | 240 | 10.78% | 89.22% | 4.898 |
| 2022 T+2 B=10 | excess | 0.052889 | 10/62 | 52 | 16.13% | 69 | 59 | 14.49% | 85.51% | 1.105 |
| 2022 T+2 B=10 | onset | None | 0/62 | 62 | 0.00% | 0 | 0 | NA | NA | 0.000 |
| 2024 T+2 B=10 | excess | 0.531295 | 4/61 | 57 | 6.56% | 28 | 24 | 14.29% | 85.71% | 0.696 |
| 2024 T+2 B=10 | onset | 0.224534 | 5/61 | 56 | 8.20% | 36 | 31 | 13.89% | 86.11% | 0.899 |

**Manual arithmetic checks:**

- 2020 T+1, B=10: both arms detect 9/69 = 13.04%, miss 60, and emit 42 alerts;
  false-alarm ratio is 33/42 = 78.57%, precision 9/42 = 21.43%.
- 2020 T+2, B=60: detections rise 28→29 of 51, a difference of
  `(29−28)/51 × 100 = 1.96 pp`, at exactly 240 false alerts in both arms.
  There are 268→269 total alerts; false-alarm ratios are 240/268 = 89.55%
  and 240/269 = 89.22%. Equal false burden still entails very high burden:
  `240/(588/12) = 4.898` false alerts per evaluable municipality-year.
- 2022 T+2, B=10: the direct arm emits no alerts and detects no onset; this loses
  10 detections relative to excess, rather than improving utility by avoiding alerts.
- 2024 T+2, B=10: 4→5 detections come with 24→31 false alerts and 28→36 total
  alerts. That +1.64 pp cannot establish an improvement under comparable false burden.

`false_alarm_ratio` is **false onset alerts / alerts with known onset outcome**;
it is not `FP/(FP+TN)`. `excess_false_alarm_ratio` instead calls an alert false only
when monthly excess is absent, so continuing episodes differ between the two metrics.
All stored frontier outcomes are known here, making the first denominator equal to
`emitted_alerts`. An alert is a municipality/exact-target-month action; an episode
is one known 0→1 transition. Within one horizon, unique target keys make
`detected_onsets=detected_episodes` and, for these complete outcomes,
`emitted_alerts−false_alerts=detected_onsets`. This verified identity must not be
assumed for unknown labels, repeated alert sequences or pooling horizons. Continued
excess months add no onsets. No episode total is formed by adding T+1 and T+2.

Burden per municipality-year uses **evaluable row exposure / 12**, not all 76 full
years; eligibility reduces exposure. Nominal useful lead is one or two months for
detected onsets, and unavailable without detections. It does not measure actual
publication latency or usable intervention time.

### Territorial consistency

Stored department and municipality aggregates reconcile to every frontier total.
They do not justify a universal territorial benefit. For the equal-false-alert
2020 T+2 XGBoost B=60 example, Meta detects 11→11 onsets while false alerts fall
121→114; Tolima detects 17→18 while false alerts rise 119→126. The extra detection
and false-burden redistribution are localized, despite equal aggregate false alerts.
At 2024 T+2 XGBoost B=10, Meta detects 3→5 with false alerts 12→26, while Tolima
detects 1→0 with false alerts 12→5. Aggregate gains can conceal local deterioration.
Municipality denominators may have zero onsets; their sensitivity is then unavailable,
not zero. Territorial support cannot repair the missing independent-year uncertainty.

## Probability metrics and calibration

There were **36 newly fitted out-of-time sigmoid calibrators**, one per arm/family/
horizon/window, following newly fitted train-only models/preparers. The method and
family settings were frozen; fitted calibrators and frontier thresholds were not
reused from EXP00 or a previous fitted experiment. No outer-training refit follows
calibration, and real single-class calibration has no identity fallback.

At T+2, AP, AUROC, Brier and reliability bins use **each arm's own target**. A smaller
onset Brier does not show a better excess forecast, nor a gain on one common event.
The following paired values are excess / onset, each against its own outcome; they
are complementary diagnostics, not a model ranking or cross-target improvement score.

| Period | Family | AP E / O | AUROC E / O | Brier E / O | ECE E / O |
| --- | --- | --- | --- | --- | --- |
| Dev 2020 | xgboost | 0.1877 / 0.1154 | 0.6587 / 0.5950 | 0.1950 / 0.1002 | 0.3007 / 0.1452 |
| Dev 2020 | lightgbm | 0.1786 / 0.1116 | 0.6355 / 0.5653 | 0.1957 / 0.1002 | 0.3007 / 0.1452 |
| Dev 2020 | gam | 0.1684 / 0.1139 | 0.6034 / 0.5795 | 0.1974 / 0.1002 | 0.3019 / 0.1452 |
| Dev 2022 | xgboost | 0.3588 / 0.1586 | 0.7168 / 0.6064 | 0.1438 / 0.0906 | 0.1065 / 0.0572 |
| Dev 2022 | lightgbm | 0.3416 / 0.1640 | 0.7145 / 0.5868 | 0.1438 / 0.0907 | 0.1066 / 0.0573 |
| Dev 2022 | gam | 0.3306 / 0.1222 | 0.7053 / 0.5872 | 0.1436 / 0.0906 | 0.1065 / 0.0572 |
| Stress 2024 | xgboost | 0.3626 / 0.1835 | 0.6365 / 0.5982 | 0.2229 / 0.1313 | 0.1599 / 0.0758 |
| Stress 2024 | lightgbm | 0.3550 / 0.1964 | 0.6227 / 0.6149 | 0.2227 / 0.1313 | 0.1572 / 0.0758 |
| Stress 2024 | gam | 0.3692 / 0.1936 | 0.6433 / 0.6085 | 0.2195 / 0.1312 | 0.1506 / 0.0757 |

At T+1 the two events coincide, and each family's probability metrics are exactly
equal across arms. For compactness, these are ranges across the three fixed families:

| Evaluation year | AP range | AUROC range | Brier range | ECE range |
| --- | --- | --- | --- | --- |
| 2020 | 0.1651–0.1854 | 0.6455–0.6656 | 0.1341–0.1362 | 0.2074–0.2121 |
| 2022 | 0.3082–0.3475 | 0.7285–0.7466 | 0.1190–0.1191 | 0.0855–0.0857 |
| 2024 | 0.3235–0.3301 | 0.6413–0.6579 | 0.1856–0.1862 | 0.1198–0.1204 |

**Confirmed:** ten equal-width calibration-bin counts reconcile to each case's
sample size; their weighted absolute probability–frequency deviations reproduce
reported ECE. As an aggregate diagnostic, T+2 onset mean predicted probability is
approximately 0.232 versus observed 0.0867 in 2020, 0.0394–0.0395 versus 0.0967 in
2022, and 0.223 versus 0.1473 in 2024 across families. Thus out-of-time sigmoid fitting
did not ensure transported calibration. **Interpretation:** temporal prevalence/
score-distribution change is compatible with these discrepancies, but is not causally
established. AP is grouped-tie noninterpolated average precision; AUROC remains
complementary. None overrides episode detection and burden.

## Paired uncertainty and acceptance

**Confirmed:** all 7,176 arm-frontier records (3,588 paired points) contain
`paired_interval={"interval": null, "status": "insufficient_cluster_support"}`.
For example, `children[19].frontier[60].paired_interval` is unavailable despite the
+1.96 pp point difference. The frozen bootstrap requests paired municipality clusters
× calendar-year blocks, 1,000 replicates, seed 42 and a percentile 95% interval; it
requires at least two municipalities **and two target years**. Every configured
evaluation is one year, including both development windows, so the implementation
returns unavailable before resampling. This is not a zero-width interval, a 0–0
interval, or evidence of no uncertainty. No substitute IID bootstrap or pooled-year
interval was manufactured from aggregate records.

The [protocol](protocol.json) explicitly does **not** transfer DEC-125's 10 pp
persistence criterion to the onset-versus-excess comparison. It defines no approved
numerical superiority threshold for this head-to-head; point findings without
required dependence-aware support remain `insufficient_evidence` and require human
scientific review. Accordingly, `SUPPORTED` or `PARTIALLY_SUPPORTED` is not justified
by selecting favorable caps; `NOT_SUPPORTED` would overstate a general negative
finding despite conditional T+2 gains. The overall classification is `INCONCLUSIVE`,
with a confirmed T+1 equivalence result and descriptive T+2 heterogeneity.

The deterministic persistence reference is evaluated on the same non-excess cohort:
all cases emit zero alerts and detect zero onsets. Its false-alarm ratio is undefined
(0/0), not zero; Brier/calibration are explicitly not applicable. The secondary
five-percentage-point excess-FAR guardrail against persistence therefore cannot be
assessed, and is not permission for extra onset-versus-excess false alerts.
EXP00 remains a secondary historical reference with incompatible cohort and consumed
2025 targets; its saved predictions are not used as the paired control.

## Execution counters and the 2024/2025 question

**Confirmed:** native `result.json` records `synthetic=false`, `real_model_fits=36`,
`real_preparer_refits=36`, `calibrator_fits=36`, and `synthetic_interface_fits=0`.
The real runner invokes both native fitting adapters and sigmoid calibration for
each of the 36 cases; the counter/lineage/finished-state evidence is consistent with
real fitting, not frozen-model reproduction. These are recorded counts, not a new
execution or a count inferred from displayed UI defaults.

The selected EXP01 parent has **no metric rows**; each child has exactly AP, AUROC
and Brier. All five queried names—`real_model_fits`, `real_preparer_refits`,
`calibrator_fits`, `hyperparameter_search`, `threshold_selection`—are **absent** in
EXP01's SQLite metrics, not recorded zeros. The tracking adapter intentionally
omits real fit counters under its replay-oriented allowlist; validated counts remain
native. The code performs no hyperparameter search, but it does select thresholds
on selection data across the frontier. A displayed zero for threshold selection
must not be interpreted as no selection. These logging semantics limit observability;
no observed counter inconsistency establishes an invalid scientific run.

No selected EXP01 run name, parameter or tag contains a 2025 period. All target-year
groups in the result are 2020, 2022 or 2024; child window names match them. The frozen
protocol's `classification`, implementation-status and pending-execution prose describe
its original delivery and remain immutable historical metadata; actual completion is
established by the real bundle/receipt and finished tracking. This resolves the old
pending conclusion without rewriting the protocol.

“Consumed” means previously examined information that cannot be treated as fresh blind
confirmation; it does not mean that EXP01 trains on 2025. Full source-file integrity
hashes can cover bytes containing 2025 without consuming those rows scientifically.
The raw-reader cutoff and preparation/role guards exclude 2025 from EXP01 X, labels,
fitting, calibration, threshold selection and evaluation. 2024 contributes past or
current information to its retrospective stress evaluation but never fitting,
calibration or selection. Prior same-calendar-month observations supply the five-year
channel; supplied future channel/labels are discarded. No future-predictor leakage
or temporal protocol deviation was found in the executed code/recorded aggregate
roles. **Limitation:** absent row predictions and no private-data reprocessing prevent
an independent row-level reconstruction; neither 2024 nor 2025 is blind confirmation.

## Decisions, limits and next hypotheses

**Decisions enabled by EXP01:**

1. Keep a single interpretation of T+1 within the `Y(T)=0` risk set: changing its
   target name cannot create a distinct classification problem. Do not credit a
   direct-onset modeling advantage there.
2. Retain paired excess as the T+2 control. Preserve the full burden frontier and
   report period/territorial trade-offs; do not deploy a budget or family selected
   because it happens to win on 2020, 2022 or stress 2024.
3. Treat calibration transport and uncertainty support as unresolved design issues.
   A future protocol must predefine an operational false-alert budget, a defensible
   superiority decision and dependence-aware uncertainty with adequate time support.
4. Keep **G5 `NOT_APPROVED`** and **champion `not_selected`**, as both protocol and
   result specify. Private support checks having passed in this completed execution
   do not supply prospective validation, historical availability, a usable persistence
   FAR guardrail or authorization to promote a model.

**Material limitations:** single-year intervals are unavailable; no single approved
head-to-head numerical acceptance threshold exists; neighboring frontier points are
correlated; realized false burden often differs despite equal selection caps;
T+2 loses boundary rows; local effects vary; retrospective availability is unproven;
no individual prediction artifact enables independent probability-metric/threshold
recalculation; and fitting counters are not fully surfaced in MLflow. Native integrity
and exact tracking correspondence support interpretation of the stored experiment,
not an audit of historical data publication or an independent scientific rerun.

**Hypotheses for a separate, predeclared experiment:** determine whether T+2 target
change improves onset utility at a chosen operational burden across multiple genuinely
unobserved years; distinguish prevalence shift from sigmoid compression/calibration
sample effects; and test whether territorial heterogeneity persists with sufficient
onset support. Any redesign of risk sets, windows, calibration or target semantics
requires separate authorization. Reserve genuinely unobserved future information;
do not relabel consumed retrospective periods as prospective evidence.

**Final scientific conclusion:** direct-onset learning is equivalent to excess learning
at T+1 in this design and produces mixed, budget-dependent T+2 trade-offs. The few
development segments with equal or lower realized false burden do not recur in 2022,
and no paired confidence interval is available. EXP01 is a verified completed
retrospective experiment whose superiority hypothesis remains **`INCONCLUSIVE`**;
it supports targeted follow-up design, not champion selection or G5 approval.

## Audit and exact result locators

For compact traceability, define `C(window,horizon,family,objective)` as the unique
entry of `result.json.children` with those four fields. `C.frontier[B]` is the record
whose `selection_false_alert_budget=B`; the integer sequence is complete. The full
frontier table uses every such record, never only the examples. Probability tables
use `C.average_precision`, `.auroc`, `.brier`, and `.calibration.expected_calibration_error`;
coverage uses `C.coverage`; references use `C.operational_reference`; territorial
examples use `C.frontier[B].by_group.department`.

- Worked T+1 check: children 0/1, frontier 10 (2020 XGBoost).
- Worked equal-burden T+2 check and interval: children 18/19, frontier 60.
- Adverse 2022 T+2 check: children 24/25, frontier 10.
- Stress T+2 check: children 30/31, frontier 10.
- Frozen primary rule: `protocol.comparison.budget`, `.metrics.primary`,
  `.acceptance.primary`, `.acceptance.uncertainty` and `.design`.
- Semantics: [onset labels/partitions](../../../../src/sat_dengue/experiments/onset.py),
  [paired execution](../../../../src/sat_dengue/experiments/exp01.py),
  [metrics/frontier/bootstrap](../../../../src/sat_dengue/experiments/onset_evaluation.py),
  [raw admission](../../../../src/sat_dengue/experiments/exp01_inputs.py), and
  [tracking](../../../../src/sat_dengue/tracking/exp01.py), verified against the executed commit.

The read-only audit checked all 36 cases, 18 pairs and 7,176 arm-frontier records;
count/ratio arithmetic, all group sums, calibration-bin ECE, paired deltas and
coverage were reconciled. No predictions were reconstructed and no AP/AUROC/Brier
or bootstrap was rerun. Local supporting extracts/checks are in ignored
`tmp/exp01-scientific-conclusions/`; original scientific inputs and MLflow remain
unchanged. Only this conclusions document is revised.
