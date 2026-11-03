# Scientific error diagnosis of the academic benchmark

**P1:** G0_OFF's T+1 FAR fails because its additional alerts contain substantially
more non-excess outcomes than CHANNEL's, despite detecting more onsets. The failure
is distributed across municipalities and weighted unevenly across years. Tolima has
higher FAR, but nearly the same FPR as Meta; false-alert counts alone do not identify
worse discrimination or a causal territorial mechanism.

**P2:** In 2022 every model satisfies the two detection conditions and fails the FAR
condition. This is not a universal loss of detection or simply the year with the
highest absolute FAR. The channel improves relative to 2021, model alert volumes
increase, and model probability scales and outcomes vary. Both shared errors and
predictor-specific errors remain substantial, especially at T+2.

This is a descriptive analysis of the [approved contract](../../contrato.md),
[frozen benchmark protocol](../protocol.json), [results](../RESULTS.md),
[conclusions](../CONCLUSIONS.md), [metrics](../METRICS_BY_STRATUM.csv) and
[paired comparisons](../PAIRED_COMPARISONS.csv). It changes no labels, scores,
thresholds, cohorts or previous conclusions. No benchmark workflow was rerun.
The selected findings and denominators are in [DIAGNOSTIC_SUMMARY.csv](DIAGNOSTIC_SUMMARY.csv);
prioritized hypotheses are in [HYPOTHESES.md](HYPOTHESES.md).

## P1: where G0_OFF exceeds the T+1 FAR limit

CHANNEL emits 179 alerts, detects 94 onsets and makes 85 excess false alerts:
FAR=85/179=47.4860%. G0_OFF emits 325 alerts, detects 146 and makes 179 false
alerts: FAR=179/325=55.0769%. The contractual limit is 52.4860%, so the gap above
the permitted margin is **2.5909 pp**. At T+1, target excess and onset coincide
within this non-excess-at-T cohort. No false-alert denominator is replaced by
negative months or municipality-years.

### Temporal accounting

The last column attributes the pooled gap relative to the **single pooled** limit
L=85/179+0.05: contribution_g = 100*(FP_g - L*alerts_g)/325. These signed terms
sum to +2.5909 pp. They are an arithmetic decomposition, not hypothetical removed
alerts, causal effects, or each year's pass/fail decision. Annual FAR is not averaged.

| Year | Rows | Onsets | Detected | Alerts | FP | G0 FAR | CHANNEL FAR | Pooled-gap contribution (pp) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | 661 | 69 | 32 | 82 | 50 | 60.98% | 58.14% | +2.14 |
| 2021 | 846 | 52 | 10 | 37 | 27 | 72.97% | 54.55% | +2.33 |
| 2022 | 693 | 89 | 49 | 109 | 60 | 55.05% | 44.19% | +0.86 |
| 2024 | 453 | 103 | 55 | 97 | 42 | 43.30% | 40.85% | -2.74 |

2022 has the most false alerts (60/179=33.52%), but 2021 and 2020 contribute more
positive weight to the pooled gap; 2024 offsets it. This does not mean 2020 fails
its own annual rule: G0_OFF passes in 2020 and 2024, and fails in 2021 and 2022.
In 2021 it only ties CHANNEL's ten detections and also fails condition A. The
largest error count, largest local FAR gap and largest pooled accounting contribution
are different quantities. No single year explains the whole failure.

### Territory, exposure and municipality concentration

| Department | Rows | Onsets | TP | Alerts | FP | Onset prevalence | Sensitivity | FPR | FAR | Gap contribution (pp) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Meta | 1024 | 146 | 74 | 140 | 66 | 14.26% | 50.68% | 7.52% | 47.14% | -2.30 |
| Tolima | 1629 | 167 | 72 | 185 | 113 | 10.25% | 43.11% | 7.73% | 61.08% | +4.89 |

Tolima accounts for 113/179 false alerts (63.13%) and 1,629/2,653 opportunities
(61.40%). Its FPR is 7.73%, close to Meta's 7.52%; its FAR is 61.08% versus
47.14%. Lower onset prevalence (10.25% versus 14.26%) and lower sensitivity
(43.11% versus 50.68%) accompany the higher FAR. The identity
FAR = FPR*(1-prevalence)/(sensitivity*prevalence + FPR*(1-prevalence)) describes
this composition; it does not identify why prevalence or sensitivity differs.
Tolima fails its own pooled academic rule; Meta passes.

The seven municipalities with at least six excess false alerts account for 51/179
errors (28.49%) over 241/2,653 opportunities (9.08%). Errors occur in 56 of the 76
municipalities. This is concentration with a broad residual, not a justification
for excluding locations or choosing municipal thresholds.

| DIVIPOLA | Municipality | Rows | Negative rows | Eligible years | Alerts | TP | FP | FPR | FAR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 73226 | CUNDAY | 33 | 30 | 2.75 | 12 | 2 | 10 | 33.33% | 83.33% |
| 50325 | MAPIRIPÁN | 30 | 22 | 2.50 | 12 | 3 | 9 | 40.91% | 75.00% |
| 50577 | PUERTO LLERAS | 41 | 37 | 3.42 | 9 | 2 | 7 | 18.92% | 77.78% |
| 73563 | PRADO | 31 | 21 | 2.58 | 12 | 5 | 7 | 33.33% | 58.33% |
| 73030 | AMBALEMA | 41 | 36 | 3.42 | 11 | 5 | 6 | 16.67% | 54.55% |
| 73148 | CARMEN DE APICALÁ | 31 | 27 | 2.58 | 9 | 3 | 6 | 22.22% | 66.67% |
| 73483 | NATAGAIMA | 34 | 27 | 2.83 | 9 | 3 | 6 | 22.22% | 66.67% |

Rates have small denominators, reflect eligible opportunities rather than complete
calendar follow-up, and carry no municipality-ranking significance claim. The full
municipal/year/arm aggregates remain in the private diagnostic publication.

### Added detections and added errors

All four groups below partition the same 2,653 observations. Counts of true/false
outcomes in alert groups refer to the arm(s) that actually alert; neither is not an
alert group. CHANNEL-only rows have a saved G0 score below its own threshold.

| Alert membership | Rows | Onset outcomes | Non-excess outcomes |
| --- | --- | --- | --- |
| CHANNEL_only | 43 | 19 | 24 |
| G0_only | 189 | 71 | 118 |
| both | 136 | 75 | 61 |
| neither | 2285 | 148 | 2137 |

G0_OFF adds **71** detections missed by CHANNEL but loses **19** detected by CHANNEL:
net +52. It adds **118** false alerts while avoiding **24** channel false alerts:
net +94. The shared false alerts are **61/179=34.08% of G0's errors** and
61/85=71.76% of CHANNEL's. Of the 189 model-only alerts, 118/189=62.43% are false;
24/43=55.81% of channel-only alerts are false. Both/neither groups are not additional
independent evidence.

| Group | Rows | G0 median p | Median p-threshold | Median cases(T) | Median target P75 | Median ratio, P75>0 | Exact equality | Within one case | P75=0 | Meta/Tolima |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G0_only_FP | 118 | 0.301 | 0.043 | 2.0 | 2.0 | 1.000 | 82/118 | 107/118 | 20 | 37/81 |
| CHANNEL_only_FP | 24 | 0.125 | -0.057 | 16.5 | 13.5 | 1.163 | 0/24 | 10/24 | 6 | 10/14 |
| both_FP | 61 | 0.308 | 0.094 | 4.0 | 2.0 | 1.500 | 0/61 | 33/61 | 8 | 29/32 |
| G0_only_TP | 71 | 0.291 | 0.065 | 2.0 | 2.0 | 1.000 | 46/71 | 62/71 | 11 | 37/34 |

The median ratio excludes zero P75; those rows are counted separately, not assigned
an artificial ratio. Model-only FP are mainly ALERTA (63) or SEGURIDAD (54), plus
one EXITO; model-only TP include 41 ALERTA, 28 SEGURIDAD and two EXITO. No row has
current EXCESO. The two labels mean different positions in the origin's channel,
not the target-month threshold used by CHANNEL.

Model-only errors concentrate near small target thresholds: 107/118 lie within
one case, and 82 equal P75 exactly. However, 62/71 additional detections are also
within one case and 46 equal P75. Medians of cases and target P75 are two in both
groups. These features describe the shared ambiguity at the boundary; they do not
validate an error filter or establish H5 mislabeling. Tolima contributes 81/118
model-only FP, but only 34/71 model-only TP; Meta contributes 37 to each.

Origin-month counts also differ: model-only FP peak in August (18), followed by
July (14); additional TP are spread across months, with nine each in March and
December. Across all G0 alerts, July/August each contribute 25 FP over 231/232
eligible observations, but their FARs differ (25/36=69.44% versus 25/45=55.56%).
Month, year and municipality composition are confounded; this is not evidence of
a climatic or external seasonal cause.

### Are errors confined to the frozen threshold?

Distance means the original probability minus its own frozen year/horizon threshold.
The disjoint 0–0.05, >0.05–0.15 and >0.15 bands were defined before calculation.
Absolute p>=0.5 and p>=0.8 are additional descriptive views, not candidate alert rules.
No retained/rejected-alert scenario or alternative-policy performance was calculated.

| Descriptive band | Alerts | TP | FP | False fraction within band |
| --- | --- | --- | --- | --- |
| near_saved_threshold_0_to_0.05 | 144 | 59 | 85 | 59.03% |
| margin_above_0.05_to_0.15 | 125 | 59 | 66 | 52.80% |
| margin_above_0.15 | 56 | 28 | 28 | 50.00% |
| probability_ge_0.5 | 33 | 16 | 17 | 51.52% |
| probability_ge_0.8 | 0 | 0 | 0 | undefined |

**85/179=47.49%** of errors lie within 0.05 of the saved threshold; 94 lie farther
away. At p>=0.5 there are 17 FP and 16 TP; no G0_OFF T+1 score reaches 0.8.
The pooled FP score median is 0.304 versus 0.286 for TP, but this mixes separately
fitted/calibrated annual procedures and does not prove reversed within-year ranking.
At the fixed 2022 cut the medians are 0.439 for FP and 0.456 for TP. Errors are
neither purely numerical ties nor entirely confined to low probabilities, and the
near-threshold region contains many true detections too.

## P2: what is observable about 2022?

### Support and target prevalence

These are conditional prevalences in the frozen eligible cohort, not department-wide
incidence. Years have different numbers of eligible months; T+1/T+2 are different
populations. Increased observed prevalence cannot be inferred from raw onset counts alone.

| Horizon | Year | Rows | Onsets | Onset rate | Excess months | Excess rate | Median cases(T) | Median target P75 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 661 | 69 | 10.44% | 69 | 10.44% | 1.0 | 4.0 |
| T+1 | 2021 | 846 | 52 | 6.15% | 52 | 6.15% | 1.0 | 4.0 |
| T+1 | 2022 | 693 | 89 | 12.84% | 89 | 12.84% | 1.0 | 3.0 |
| T+1 | 2024 | 453 | 103 | 22.74% | 103 | 22.74% | 4.0 | 7.0 |
| T+2 | 2020 | 588 | 51 | 8.67% | 72 | 12.24% | 1.0 | 4.0 |
| T+2 | 2021 | 779 | 45 | 5.78% | 56 | 7.19% | 1.0 | 4.0 |
| T+2 | 2022 | 641 | 62 | 9.67% | 101 | 15.76% | 1.0 | 3.0 |
| T+2 | 2024 | 414 | 61 | 14.73% | 119 | 28.74% | 4.0 | 7.0 |

2022 is above 2020/2021 in onset prevalence but below 2024. The median origin count
remains one as in 2020/2021, while median target P75 is three instead of four;
2024 has medians four and seven. This supports a composition difference, not a
causal outbreak-frequency or data-quality explanation. No external climate,
intervention or reporting-change evidence is introduced.

### Why every model fails the joint rule

For 2022, all models detect strictly more onsets than CHANNEL (24 at T+1, eight
at T+2) and persistence (zero). They fail **condition C only** at the annual pooled
level. The admissible FARs are 49.19% and 55.00%, respectively.

| Horizon | Arm | TP | Sensitivity | Alerts | FP-excess | FP-onset | FAR-excess | Above permitted FAR (pp) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | CHANNEL | 24 | 26.97% | 43 | 19 | 19 | 44.19% | reference |
| T+1 | G0_OFF | 49 | 55.06% | 109 | 60 | 60 | 55.05% | +5.86 |
| T+1 | G0_ON | 48 | 53.93% | 114 | 66 | 66 | 57.89% | +8.71 |
| T+1 | G1_OFF | 48 | 53.93% | 110 | 62 | 62 | 56.36% | +7.18 |
| T+1 | R0 | 33 | 37.08% | 79 | 46 | 46 | 58.23% | +9.04 |
| T+2 | CHANNEL | 8 | 12.90% | 42 | 21 | 34 | 50.00% | reference |
| T+2 | G0_OFF | 17 | 27.42% | 74 | 47 | 57 | 63.51% | +8.51 |
| T+2 | G0_ON | 22 | 35.48% | 87 | 55 | 65 | 63.22% | +8.22 |
| T+2 | G1_OFF | 22 | 35.48% | 108 | 70 | 86 | 64.81% | +9.81 |
| T+2 | R0 | 26 | 41.94% | 120 | 79 | 94 | 65.83% | +10.83 |

The 2022 model FARs are generally **lower than 2021**, not uniformly worse in
absolute terms. CHANNEL's FAR falls from 54.55% to 44.19% at T+1 and from 73.08%
to 50.00% at T+2, making the relative contract more demanding. G0_OFF alert volume
rises from 37 to 109 (T+1) and from 19 to 74 (T+2). These observations explain the
arithmetic failure without proving why the alerts differ.

At T+2 CHANNEL's 42 alerts comprise eight onset, 13 continuation and 21 non-excess
outcomes. G0_OFF's 74 comprise 17 onset, ten continuation and 47 non-excess outcomes.
For R0/G0_ON/G1_OFF, continuation-alert counts are 15/10/16. Excess FAR and onset
false discovery therefore cannot be interchanged.

### Regional differences are not uniform

| Horizon | Department | Arm | Rows | Onsets | TP | FP-excess | Alerts | FPR-excess | FAR-excess |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | Meta | CHANNEL | 210 | 49 | 13 | 8 | 21 | 4.97% | 38.10% |
| T+1 | Meta | G0_OFF | 210 | 49 | 30 | 25 | 55 | 15.53% | 45.45% |
| T+1 | Meta | G0_ON | 210 | 49 | 31 | 29 | 60 | 18.01% | 48.33% |
| T+1 | Tolima | CHANNEL | 483 | 40 | 11 | 11 | 22 | 2.48% | 50.00% |
| T+1 | Tolima | G0_OFF | 483 | 40 | 19 | 35 | 54 | 7.90% | 64.81% |
| T+1 | Tolima | G0_ON | 483 | 40 | 17 | 37 | 54 | 8.35% | 68.52% |
| T+2 | Meta | CHANNEL | 194 | 32 | 5 | 10 | 23 | 7.14% | 43.48% |
| T+2 | Meta | G0_OFF | 194 | 32 | 7 | 14 | 28 | 10.00% | 50.00% |
| T+2 | Meta | G0_ON | 194 | 32 | 11 | 16 | 35 | 11.43% | 45.71% |
| T+2 | Tolima | CHANNEL | 447 | 30 | 3 | 11 | 19 | 2.75% | 57.89% |
| T+2 | Tolima | G0_OFF | 447 | 30 | 10 | 33 | 46 | 8.25% | 71.74% |
| T+2 | Tolima | G0_ON | 447 | 30 | 11 | 39 | 52 | 9.75% | 75.00% |

All models fail the regional FAR limit at T+1 in both departments. At T+2 G0_ON
passes in Meta (45.71% FAR versus CHANNEL 43.48%, with 11 versus five detections);
all other model/department combinations fail C. Hence “2022 fails everywhere”
would be false. Tolima's higher FAR coexists with a lower G0_OFF excess FPR:
T+1 7.90% versus Meta 15.53%; T+2 8.25% versus 10.00%. The target prevalence and
true-positive composition matter, as in P1.

For G0_OFF T+1, Villavicencio, Mapiripán, Cunday and Ortega each contribute four
FP (16/60 together), over 8/8/12/11 eligible observations and 6/5/12/10 negative
observations. Their FPRs range from 33.33% to 80.00%, with very small denominators.
For T+2, Valle de San Juan contributes four FP over nine rows/eight negatives;
San Juan de Arama, Anzoátegui and Icononzo contribute three each over 7/11/11 rows
and 3/11/11 negatives. These contributors differ by horizon; no municipal removal
or permanent ranking is justified. The private municipal table retains all models,
all years, exposure and negative-outcome denominators.

### Shared difficulty and model-specific errors

The following counts are unique municipality-origin observations. Rows with errors
from several models are counted once, unlike sums of model-specific false alerts.
The four predictors are related procedures, not four independent replications.

| Horizon | Outcome | Opportunities | 0 models | 1 model | 2 models | 3 models | 4 models |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | non_excess | 604 | 510 | 29 | 14 | 27 | 24 |
| T+1 | non_onset | 604 | 510 | 29 | 14 | 27 | 24 |
| T+1 | onset | 89 | 32 | 6 | 9 | 14 | 28 |
| T+2 | non_excess | 540 | 413 | 62 | 28 | 15 | 22 |
| T+2 | non_onset | 579 | 432 | 69 | 31 | 17 | 30 |
| T+2 | onset | 62 | 29 | 7 | 10 | 4 | 12 |

At T+1 there are 94 distinct excess-error rows: 65 (69.15%) are shared by at least
two models, including 24 shared by all four. At T+2 there are 127: 65 (51.18%) are
shared by at least two, including 22 shared by all four. Counting false *onset*
alerts instead yields 147 T+2 rows and 30 shared by all four. Shared failure is
substantial but does not account for all errors.

| Horizon | Model | Exclusive FP-excess | Exclusive FP-onset | Exclusive detected onsets |
| --- | --- | --- | --- | --- |
| T+1 | R0 | 9 | 9 | 3 |
| T+1 | G0_OFF | 2 | 2 | 0 |
| T+1 | G0_ON | 4 | 4 | 0 |
| T+1 | G1_OFF | 14 | 14 | 3 |
| T+2 | R0 | 34 | 37 | 4 |
| T+2 | G0_OFF | 4 | 5 | 0 |
| T+2 | G0_ON | 7 | 7 | 0 |
| T+2 | G1_OFF | 17 | 20 | 3 |

R0 and G1 each uniquely detect three T+1 onsets; at T+2 they uniquely detect four
and three. G0_OFF/ON have no uniquely detected 2022 onsets relative to the union
of the other three models, although they detect onsets some individual comparators
miss. This does not evaluate an ensemble. All four miss 32/89 T+1 and 29/62 T+2
onsets; 57/89 and 33/62 are detected by at least one. The unresolved problem includes
shared missed signal as well as unnecessary alerts.

### Probability scale, ranking and saved decision policy

The table reports G0_OFF's complete-cohort score distribution and saved threshold.
Each year uses a separately fitted/calibrated procedure, so between-year scale
changes are not a clean drift experiment with one fixed predictor.

| Horizon | Year | p25 score | Median score | p75 score | Saved threshold | Mean p | Observed onset rate | AP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 0.060 | 0.092 | 0.136 | 0.185 | 11.04% | 10.44% | 0.342 |
| T+1 | 2021 | 0.052 | 0.099 | 0.130 | 0.250 | 10.71% | 6.15% | 0.199 |
| T+1 | 2022 | 0.154 | 0.228 | 0.299 | 0.357 | 24.04% | 12.84% | 0.455 |
| T+1 | 2024 | 0.061 | 0.084 | 0.128 | 0.150 | 10.48% | 22.74% | 0.525 |
| T+2 | 2020 | 0.048 | 0.064 | 0.090 | 0.115 | 7.24% | 8.67% | 0.277 |
| T+2 | 2021 | 0.050 | 0.081 | 0.110 | 0.201 | 8.72% | 5.78% | 0.226 |
| T+2 | 2022 | 0.116 | 0.171 | 0.216 | 0.262 | 17.48% | 9.67% | 0.211 |
| T+2 | 2024 | 0.047 | 0.064 | 0.083 | 0.106 | 7.21% | 14.73% | 0.361 |

G0_OFF overpredicts the whole-cohort onset frequency in 2022 by 11.19 pp at T+1
and 7.81 pp at T+2. Mean predicted risk versus observed frequency diagnoses only
calibration in the large; it does not identify the full reliability curve or explain
the operating point. At T+1 its alerted subset has mean p=46.87% and observed onset
frequency=44.95%, a much smaller gap. At T+2 those values are 32.05% and 22.97%.
Fixed-width probability-bin counts and means are retained privately.

The same direction does not apply to R0: its 2022 mean scores are only 4.42%/3.96%,
below observed onset frequencies 12.84%/9.67%, with thresholds 0.05065/0.04068.
G0_ON/G1_OFF instead have means 24.35%/22.91% at T+1 and 18.37%/15.67% at T+2.
A universal “2022 overconfidence” explanation is therefore unsupported. G0_OFF's
T+1 AP is 0.455, above 2020/2021 and below 2024; T+2 AP is 0.211, its lowest year.
AP comparisons also depend on prevalence and do not alone isolate ranking change.

Saved 2022 G0_OFF policies were selected on 2021 target months. At T+1 selection
recorded 20 TP/68 FP (FAR-onset 77.27%); evaluation records 49/60 (55.05%). At
T+2 selection recorded 16/61 (79.22%); evaluation records 17/57 (77.03%). The T+2
comparison here deliberately uses *onset* false discovery at both stages; selection
excess-FAR cannot be recovered from these aggregate policy records alone. Do not
substitute the 63.51% evaluation excess-FAR in that comparison. The evaluation's
improved false-discovery fractions contradict a simple claim that FAR deteriorated
from selection in 2022, even though the eligible-year onset load rises slightly
above one in evaluation.

The verified policy maximizes detected onsets under <=1 onset false alert per
eligible municipality-year. It does **not** constrain FAR relative to CHANNEL.
This establishes an objective mismatch with the academic benchmark, not proof that
another policy could meet all conditions. Individual G0 selection-score distributions
were not reconstructed; no inference, recalibration or threshold optimization occurred.

## Integrated interpretation and limits

1. P1 is partly concentrated in Tolima and weighted by 2020/2021, but errors span
   56 municipalities and all years. 2022 contributes the most FP, not the largest
   pooled-gap accounting term. Different claims require different denominators.
2. Only 34.08% of G0_OFF T+1 FP are shared with CHANNEL. The additional alerts
   recover real onsets but contain many failures near small target P75 values.
3. Near-threshold errors are common, not a majority under the fixed 0.05 definition;
   higher scores also fail, and true detections occupy the same bands and contexts.
4. The 2022 annual failure is shared at the decision-criterion level, but territories,
   error identities, probability scales and horizon-specific rankings differ.
5. Objective mismatch is directly documented. Temporal/territorial probability
   variation and overlap of successful/unsuccessful alerts support investigating
   decision transport and local ranking. They do not establish a unique cause.
6. These data cannot distinguish altered predictor–outcome relations, changing
   sample composition, reporting vintages, H5 validity and model/calibrator effects.
   Claims about climate, sanitary interventions or external epidemics would require
   evidence not supplied here. No causal or statistical-superiority claim is made.

The diagnosis is exploratory on reused 2020/2021/2022/2024 observations. 2024 is
consumed stress; 2025 was consumed by EXP00 and is not a fresh reserve. Cohort size,
non-excess selection and known-outcome filters differ over time; exposure is observed
eligible rows/12, not complete municipality-years. Quantiles/bands are descriptions,
not confidence intervals or independent replications. Small municipal denominators,
repeated observations and outcome-selected groups preclude causal interpretation.

[Analysis 5](../../analisis-5.md) showed that reducing burden through calibration
can lose detections; [analysis 6](../../analisis-6.md) preserved the distinction
between scientific validity and technical reproducibility; [analysis 7](../../analisis-7.md)
warned against equating pooled AP/Brier with better annual decisions. This diagnosis
localizes errors and clarifies the academic objective mismatch without reversing
those conclusions or treating repeated interpretations as new independent evidence.

## One recommended next experiment, not executed

Prioritize a **frozen-G0_OFF decision-policy comparison aligned with the academic
contract**, with the old BETA selector as control. Preserve H5, predictors, scores,
calibration and evaluation keys; choose any candidate policy solely on earlier
selection data using the academic detection/FAR conditions. Predeclare feasibility,
uncertainty, year/department controls and handling of undefined FAR. Do not fit a new
predictor or tune against this diagnosis. Earlier G0 selection scores must first be
verified, or recovered through separately authorized frozen-model inference; aggregate
policy counts alone cannot support the experiment. An intact independent period is
needed for confirmation; otherwise any chronological historical comparison remains
exploratory. If no feasible selection policy or independent support exists, report
that rather than relaxing conditions. No winning threshold or expected gain is claimed.

This recommendation is justified by a directly observed mismatch in selection
objective, not by proof that stricter alerts will improve the frontier. The known
losses under EXP04/BETA03 and the overlap between near-threshold TP/FP are reasons
for caution. [HYPOTHESES.md](HYPOTHESES.md) gives the bounded alternatives; only the
first is recommended for the next authorized experiment. G5 `NOT_APPROVED`;
`champion: not_selected` remain unchanged.

## Reproducibility and validation

Branch `contrato_del_proyecto`; initial HEAD `ee7800f1c06eb428fee41fdbe038994725d2c26e`.
The private source is the explicitly requested benchmark bundle
`6cfc7bcf565ebdf7ff11ab3ff79d6d91ce7d2f392958c76aa55d310ba27b6c48`, manifest SHA-256
`4ca5b8359c914fc080c80ebf538d7d11bf1c76aa783d9434c1832d478ff15f2f`.

Private diagnostic evidence resides under
`data/processed/benchmark/diagnostico/874ef99634db44e0e71a3aba9b7195f8762ff5f9327ef0394d27ce77fc8e116c/`:
`tables.json`, `municipal_summary.csv`, fixed `settings.json` and `manifest.json`.
It records 22 verified source identities and the analysis script hash. No full
source dataset or individual predictions were duplicated. The municipal CSV is
aggregate evidence with private handling; public tables contain only selected
aggregate counts, never municipality-month rows or individual probabilities.

```bash
.venv/bin/python data/processed/benchmark/diagnostico/analyze_v1.py
.venv/bin/python data/processed/benchmark/diagnostico/report_v1.py
```

These are diagnostic/report scripts, not the benchmark runner. Repetition verifies
or reuses identical diagnostic bytes; changed bytes cannot overwrite an existing
publication. The report script creates only the three requested public files and
refuses differing existing content. No source data are written.

PASS: source manifest/body identity and all six payloads; public/private aggregate
parity; exact six-arm pairing; all 180 benchmark count/rate rows reconciled; 30,450
row-arm records retained; signed contribution sums and overlap partitions; repeated
diagnostic execution reproduced identical bytes. Independent arithmetic verified the
principal overlap, concentration and 2022 consensus results. Scoped script lint,
Markdown links, whitespace/privacy checks and repo-only conformance are recorded
at handoff. The all-plan gate retains two inherited failures (PLAN_012 unresolved
review evidence and legacy Stage 2 mixed lifecycle), separate from this analysis.
