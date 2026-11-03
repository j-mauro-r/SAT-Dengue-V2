# EDA-EXP01 — conclusions and research priority

**Completed with limitations.** Existing results support several interacting
constraints, without establishing a unique causal explanation of SAT-Dengue's
limitations. [Eight quantified findings](FINDINGS.md) distinguish new descriptive
calculations from corroborated historical results. G5 remains `NOT_APPROVED`;
`champion: not_selected`.

## 1. Is discrimination insufficient?

There is useful signal and incomplete separation. G0_OFF annual onset AUROC is
0.775–0.830 at T+1 and 0.713–0.763 at T+2; true/false outcomes overlap within
each annual procedure. All four predictors jointly miss 32/89 and 29/62 onsets
in 2022. DELTA also found no admissible scalar-threshold policy in two required
historical cells. These facts justify investigating limited local separability,
especially T+2/2022, but do not prove that every policy or predictor would fail.
AP variation also reflects prevalence. No new model is selected.

## 2. What is known about calibration and temporal transport?

Calibration in the large changes sign: G0_OFF overpredicts 2022 onset frequency
by 11.19/7.81 pp and underpredicts 2024 by 12.26/7.53 pp. Annual model/calibrator
identities differ; this is not a clean fixed-model drift experiment. T+1/2022
has the highest AUROC despite failure of the academic margin. DELTA's fixed P1
selection policy transports C in only three of six available cells, with two
mandatory policies absent. Its complete primary comparison remains `NO_EVALUABLE`.
Neither a new calibration method nor a stricter threshold is automatically justified:
EXP04 and BETA03 already document detection costs under their separate protocols.

## 3. How much of the territorial difference relates to prevalence?

For pooled T+1 G0_OFF, the Tolima−Meta excess-FAR gap is 13.94 pp. A symmetric
three-factor accounting decomposition attributes +9.28 pp to prevalence, +3.98
to excess sensitivity and +0.68 to FPR. At a common 11.80% prevalence, FARs become
52.58%/57.27%, leaving 4.69 pp. The decomposition and standardization are different
accounting summaries, not interchangeable causal percentages.

At T+2 the observed +1.95 pp gap reverses to −4.28 pp at common excess prevalence.
Tolima's lower prevalence offsets its better pooled excess sensitivity/FPR.
Thus a general claim of inferior Tolima prediction is unsupported. Annual controls
and DELTA's differing departmental responses further limit pooled interpretations.

## 4. Do transmission profiles differ with sufficient support?

This cannot be established: the admitted sources have no temporally validated
transmission classification. Departments describe geography, not validated profiles.
Municipal rates vary, but 273/300 T+1 and 294/298 T+2 municipality-years have fewer
than three onsets. Median Wilson sensitivity/FAR reference widths are 79.35 pp
among defined rates, even before accounting for dependence. This is insufficient
support for selecting municipal thresholds. A future historically defined grouping
could be investigated only with its own source, temporal validity and support audit;
no grouping is constructed from these evaluation errors.

## 5. What do near-P75 errors reveal?

They expose shared ambiguity, not a validated correction rule. At T+1,
107/118 model-only false alerts and 62/71 model-only true detections are within
one case of target P75. P75=0 and equality also occur in both groups. EXP02's
documented H5/H9 sensitivity shows label identity can change substantially, but
does not establish H5 error or validate a different epidemiological target.
H5, boundary observations and all municipalities remain unchanged.

## 6. Which hypothesis should come next?

**Priority hypothesis:** limited local onset separation, together with changing
epidemiological composition, constrains transport of the academic alert margin
across periods. This has more support than a claim that a new global threshold,
calibrator or municipal policy alone will resolve the problem. The evidence does
not identify one intervention with a demonstrated expected gain.

The immediate decision is to define an independent evaluation opportunity and
adequate historically fixed strata before choosing an intervention. Any later
experiment needs separate human authorization and a predeclared protocol. These
consumed years cannot supply independent confirmation. No automatic EXP-DELTA02
recommendation or execution follows from this analysis.

| Priority / possible research line | Evidence | Main uncertainty | Potential improvement | Complexity / prerequisite |
| --- | --- | --- | --- | --- |
| 1. Joint audit of local ranking, composition and decision transport in independent periods | Annual score overlap, shared misses, calibration sign changes, 3/6 P1 transport, exact territorial decomposition | Cannot separate composition, procedure effects, reporting availability and H5 validity here | Could identify the component worth intervening on; gain unquantified | Moderate analytical complexity; requires independent period and temporal provenance |
| 2. Probability-calibration transport under a fixed predeclared decision criterion | Large calibration gaps; EXP04's calibration/detection trade-off | Recalibration may lose detections without improving margin | Plausible conditional benefit; no established joint improvement | Moderate; freeze objective and independent evaluation before any fitting |
| 3. Additional discriminative information, particularly T+2 | Lower T+2 AUROC and shared missed onsets; EXP03 information effects are conditional | Unknown availability and incremental signal | Potentially useful, magnitude unknown | High; separate data/protocol approval, no evaluation-led feature search |
| 4. Policy by historically validated transmission profile | Departmental differences and prevalence accounting | No valid classification; sparse events and intervals | Speculative; pooled differences do not establish benefit | High support burden; historical grouping and independent evaluation required |
| 5. New global scalar threshold on the same scores | DELTA tested this family; two cells infeasible and T+1 detection losses | Alternative constraint/policy would change the scientific question | Unsupported as a general remedy | Low computation, high risk of recycling evaluation evidence |
| 6. Revise H5 or filter small-P75 alerts | EXP02 sensitivity; boundary features shared by errors/successes | No external outbreak truth; true detections may be removed | Unknown and unvalidated | High scientific complexity; external adjudication and separate approval required |

The ordering reflects evidential support and unmet prerequisites, not numerical
confidence scores or a forecast of improvement. No statistical superiority,
causal effect, prospective performance or sanitary efficacy is established.

## Limits of the decision

Only 2020/2021/2022/2024 frozen Meta–Tolima cohorts are analyzed: 2,653/313 and
2,422/219 observations/onsets. 2024 is consumed stress, and 2025 is excluded and
already consumed elsewhere. Historical consolidated data do not establish
availability at forecast origin. Different annual model identities, changing
eligibility and shared temporal shocks confound simple drift explanations.
Wilson intervals are descriptive binomial references; no defensible independent
temporal uncertainty is manufactured by resampling municipalities. Historical
EXP03/EXP04/BETA summaries are context, not additional paired replications.

The contribution of EDA-EXP01 is a more precise evidential diagnosis, particularly
prevalence accounting and municipal support, while preserving every prior result
and all scientific approval boundaries.

## Chapter 7 — conclusions of the climate analysis

This appendix addresses the separately authorized climate question; the six
original answers, research ordering and limits above remain unchanged.

### 1. Are climatic differences observable between real onsets and false alerts?

Yes, some descriptive medians and distributions differ, but direction and magnitude
depend on year, horizon, department and season. At T+1, G0_OFF detected-onset versus
false-excess temperature median differences range **−0.45 to +3.09 °C** across
the eight year/department cells, with positive direction in **5/8**. Precipitation
differences range **−109.93 to +26.23 mm/month**, with positive direction in **4/8**.
Conditional percentile distributions overlap for TP, FP, FN and TN in G0_OFF and
CHANNEL. T+2 continuation alerts are retained separately from onset detections
and excess errors. These are alert-selected groups, not evidence that climate
adds discrimination to a fitted predictor.

### 2. Does any lag associate consistently across years and territories?

No variable/lag has a common sign across all eight year/department cells in either
horizon under the raw Spearman or month-centered rank diagnostic. Temperature at
T has a weak positive T+1 tendency in 7/8 cells; the four predefined temperature
lags share a similar weak centered tendency. This does not identify a winning lag
or four independent replications. Rainfall and soil water vary more strongly in
direction across cells; conditioning on origin month changes some raw patterns.
All T/T−1/T−2/T−3 results remain visible without significance filtering or selection.

### 3. Does climate distinguish near-P75 outcomes descriptively?

There is substantial overlap after balancing year, department and origin month.
At T+1 the balanced near-boundary true/false temperature medians differ by only
**+0.058 °C**, and precipitation by **−7.15 mm/month**. At T+2 the differences
are **+2.661 °C** and **−46.30 mm/month**, but wide interquartile ranges overlap,
and only 14 common cells contain 15 true detections and 29 false alerts.
These distributions do not validate a climate filter or a decision cutoff.
The original ±1-case proximity, H5, scores, policies and populations are preserved.

### 4. What prevents claiming a new feature would improve the model?

All climate observations are retrospectively consolidated; coverage does not prove
origin-time availability. The same consumed years and municipalities are reused,
lags are correlated and outcomes are experimental H5 labels. Department/season
controls do not remove municipal climatology, altitude, surveillance or other
confounding. Common-cell support is sparse: only one T+1 cell and zero T+2 cells
have at least three true detections and three false alerts. Conditioning on alert
status can itself create associations. No predictive incremental comparison,
independent confirmation, recalibration or feature experiment was performed.

EXP03 provides a further caution under its different protocol: lagged climate's
T+2 boosting detection gains were accompanied by additional false-alert burden
and reversed under 2024 stress. Those historical results are context, not a
quantitative effect pooled with this EDA and not proof that every climatic
representation is ineffective.

### 5. Is there sufficient basis for a controlled climate experiment?

**Scientific disposition: `INSUFFICIENT_EVIDENCE`.**

The extension leaves a weak temperature-related hypothesis open but does not
establish a stable lag, useful near-boundary separation or expected incremental
benefit sufficient to recommend a climatic EXP-DELTA02 as the next intervention.
This disposition concerns support for that recommendation; it is not a test of
the null hypothesis that climate is unrelated to dengue or has no predictive value.

If humans later authorize a controlled climate study, it would require a predeclared
representation/lag, origin-time availability evidence, sufficient events and an
independent evaluation opportunity with detection and false-alert burden assessed
together. Those prerequisites are unfulfilled here. No new experiment is registered
or executed, and the original Chapters 1–6 priority is unchanged.

The climate findings and their support are in the separate
[Chapter 7 findings](FINDINGS.md#chapter-7--climate-findings); source/publication
identity and preservation replay are in [README](README.md).
G5 `NOT_APPROVED`; `champion: not_selected`.

## Scientific closure — EDA-EXP01

### Scientific state

| Scope / gate | Final scientific state |
| --- | --- |
| Main exploratory analysis, Chapters 1–6 | `COMPLETED_WITH_LIMITATIONS` |
| Chapter 7 climate extension | `INSUFFICIENT_EVIDENCE` |
| G5 | `NOT_APPROVED` |
| Champion | `not_selected` |

EDA-EXP01 is scientifically concluded for its authorized exploratory questions.
The eight original findings and five climate findings remain the quantitative
record. Closure consolidates their interpretation and limits; it does not authorize
adoption of a model, alert policy, climatic feature or new experiment. PR #74
integration, independent review and Mauricio's merge decision are separate gates.

### Key conclusions

1. **Territorial composition matters.** For G0_OFF T+1 the Tolima–Meta excess-FAR
   gap is **13.94 pp**. Symmetric accounting attributes **9.28 pp** to prevalence;
   common-prevalence standardization leaves **4.69 pp**. At T+2 the standardized
   gap reverses to **−4.28 pp**. This describes rate composition, not its causes.
   [F1–F2](FINDINGS.md).
2. **Predictors contain signal but share failures.** Annual G0_OFF onset AUROC
   is **0.775–0.830** at T+1 and **0.713–0.763** at T+2. In 2022 all four
   predictors miss **32/89** and **29/62** onsets, respectively. Complementary
   G0_OFF/CHANNEL detections and shared errors preclude a single-component or
   uniform-dominance explanation. [F3 and F8](FINDINGS.md).
3. **Temporal transport is unresolved.** Calibration-in-the-large gaps change
   from **+11.19/+7.81 pp** in 2022 to **−12.26/−7.53 pp** in 2024 (T+1/T+2).
   Only **3/6** available DELTA P1 policies retain the academic FAR margin in
   evaluation; two mandatory cells have no feasible policy. The complete primary
   P1 comparison remains `NO_EVALUABLE`, not an approving or rejecting result
   for every alternative policy. [F4–F5](FINDINGS.md),
   [DELTA quantitative owner](../EXP-DELTA01/RESULTS.md).
4. **The data do not justify 76 independent municipal thresholds.**
   **273/300** T+1 and **294/298** T+2 observed municipality-years contain fewer
   than three onsets. Sparse events, undefined rates and unvalidated transmission
   profiles prevent translating geographic heterogeneity into stable municipal
   policies. [F6](FINDINGS.md).
5. **P75 proximity is shared by errors and useful detections.** At T+1,
   **107/118** G0-only false alerts and **62/71** G0-only true detections lie
   within one case of target P75. The boundary does not justify eliminating these
   alerts or changing H5. [F7](FINDINGS.md).
6. **Climate supplies no sufficiently supported, consistent separator here.**
   Nine variables were examined at T; temperature, precipitation and soil water
   additionally used the predefined T−1/T−2/T−3 lags. Temperature at T has a weak
   positive T+1 association in **7/8** year/department cells, but no variable/lag
   has a uniform direction across all eight. Near-P75 comparison has **32/14**
   common T+1/T+2 strata, with ≥3 observations per group in only **1/0** strata.
   Distributional overlap and this limited support yield `INSUFFICIENT_EVIDENCE`
   for a climatic follow-up recommendation, not proof of no possible climate value.
   [C7.1–C7.5](FINDINGS.md#chapter-7--climate-findings),
   [EXP03 context under its distinct protocol](../EXP03_feature_ablation/CONCLUSIONS.md).

### Lessons to retain in future work

- Distinguish excess-FAR, onset false alerts, FPR, event prevalence and exposure;
  retain their numerators, denominators and undefined values.
- Assess discrimination, calibration and alert-policy performance separately;
  better ranking or probability calibration alone does not establish useful alerts.
- Evaluate T+1 and T+2 independently, including the distinction between onset
  and continuation at T+2.
- Control temporal, territorial and seasonal composition descriptively before
  interpreting pooled contrasts; such controls do not establish causality.
- Report municipal event support and uncertainty before using municipal rates
  to motivate a policy; extreme rates with few events are not stable profiles.
- Do not infer incremental predictive value from a climate variable's biological
  plausibility or an observed alert-group association.
- Preserve consumed-year status. Repeated analysis of 2020/2021/2022/2024, or
  previously consumed 2025 elsewhere, cannot supply new independent confirmation.

### Hypotheses and research decisions

| Hypothesis investigated | Evidence obtained | Scientific state | Consequence for future research |
| --- | --- | --- | --- |
| Prevalence contributes to territorial FAR differences | T+1 prevalence contribution 9.28 pp; standardization leaves 4.69 pp; T+2 reversal | Descriptively supported; causal mechanism unidentified | Retain composition controls and event-specific denominators |
| Existing scores contain useful but incomplete onset separation | Annual AUROC above 0.5, shared missed onsets and overlapping outcomes | Descriptively supported; a unique bottleneck is not identified | Examine ranking, composition and policy jointly before choosing an intervention |
| An aligned scalar-threshold policy provides complete, stable academic compliance | Two DELTA cells infeasible; only 3/6 available policies transport C | Complete P1 comparison `NO_EVALUABLE`; general adoption unsupported | Preserve failed cells; do not relax constraints or recycle evaluation for selection |
| Seventy-six independent municipal thresholds are justified | Few annual events and no validated transmission profiles | Insufficient support | Do not recommend independent municipal thresholds |
| Near-P75 alerts can be eliminated as an error-specific group | Boundary context occurs in both false alerts and additional detections | Not supported by this EDA | Preserve these alerts and H5; no boundary filter is justified |
| Additional climate features are a supported next intervention | Weak, variable associations; overlapping distributions and sparse common cells | `INSUFFICIENT_EVIDENCE` | Do not automatically execute a climatic EXP-DELTA02; retain the hypothesis without feature or lag selection |
| Additional anticipatory information could resolve some shared missed signal | Shared misses and conditional historical information contributions leave an unresolved question | Open; incremental value untested | Any epidemiological-signal audit is a separate investigation requiring explicit authorization and a predeclared scope |

No new experiment, data reconstruction, feature selection or signal audit is
created or authorized by this closure. The earlier research-priority matrix
remains unchanged; no expected gain is established for a specific intervention.

### Limits retained at closure

The analysis reuses previously consumed retrospective years, with no independent
temporal confirmation. Consolidated epidemiological and climate observations do
not demonstrate availability at the historical forecast origin. Annual models
and calibrators have different identities, so between-year changes do not isolate
drift of a fixed predictor. Repeated municipal months and shared temporal shocks
limit inferential uncertainty; the reported Wilson intervals remain descriptive
binomial references.

Near-P75 climate comparisons have reduced common-cell support and do not remove
municipal or alert-selection confounding. No historically validated transmission
profile is available. H5 remains an experimental definition without external
outbreak adjudication. These limitations remain part of the scientific result,
not unresolved instructions to repeat this EDA or approval to adopt a new method.
