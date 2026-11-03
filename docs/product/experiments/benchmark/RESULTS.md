# Academic benchmark results

**BENCHMARK_COMPLETED_WITH_LIMITATIONS.** No candidate meets the three academic
conditions at pooled T+1; all four meet them at pooled T+2. These are descriptive,
retrospective results on the frozen BETA common cohorts. They do not establish
stability in every year/department, statistical superiority or operational readiness.

The [protocol](protocol.json) and [methodology/identities](README.md) were fixed
before calculation. All tables derive from [METRICS_BY_STRATUM.csv](METRICS_BY_STRATUM.csv)
and [PAIRED_COMPARISONS.csv](PAIRED_COMPARISONS.csv). The denominator is 2,653
observations at T+1 and 2,422 at T+2; exposure is 221.0833 and 201.8333 eligible
municipality-years, respectively. All arms cover all observations within a horizon.

## Pooled primary counts and rates

FAR is measured against **target excess**; FA-onset includes alerted continuations
at T+2. Load is FA-onset per eligible municipality-year.

| Horizon | Arm | Onsets | Detected | Missed | Sensitivity | Alerts | FP-excess | FAR-excess | FA-onset | Load |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | CHANNEL | 313 | 94 | 219 | 30.03% | 179 | 85 | 47.49% | 85 | 0.384 |
| T+1 | G0_OFF | 313 | 146 | 167 | 46.65% | 325 | 179 | 55.08% | 179 | 0.810 |
| T+1 | G0_ON | 313 | 152 | 161 | 48.56% | 356 | 204 | 57.30% | 204 | 0.923 |
| T+1 | G1_OFF | 313 | 141 | 172 | 45.05% | 328 | 187 | 57.01% | 187 | 0.846 |
| T+1 | PERSISTENCE | 313 | 0 | 313 | 0.00% | 0 | 0 | undefined | 0 | 0.000 |
| T+1 | R0 | 313 | 142 | 171 | 45.37% | 373 | 231 | 61.93% | 231 | 1.045 |
| T+2 | CHANNEL | 219 | 46 | 173 | 21.00% | 206 | 114 | 55.34% | 160 | 0.793 |
| T+2 | G0_OFF | 219 | 62 | 157 | 28.31% | 223 | 130 | 58.30% | 161 | 0.798 |
| T+2 | G0_ON | 219 | 67 | 152 | 30.59% | 219 | 126 | 57.53% | 152 | 0.753 |
| T+2 | G1_OFF | 219 | 61 | 158 | 27.85% | 243 | 139 | 57.20% | 182 | 0.902 |
| T+2 | PERSISTENCE | 219 | 0 | 219 | 0.00% | 0 | 0 | undefined | 0 | 0.000 |
| T+2 | R0 | 219 | 86 | 133 | 39.27% | 342 | 204 | 59.65% | 256 | 1.268 |

## Joint academic conditions, separate from BETA

A: more detections than CHANNEL. B: more than PERSISTENCE (zero at both horizons).
C: FAR-excess difference <=+5 pp. BETA combines its onset-load limit with the
sensitivity margin versus R0 and does not replace A/B/C.

| Horizon | Model | Delta detections/channel | Delta FAR/channel (pp) | A | B | C | Academic | BETA pooled |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | R0 | +48 | +14.44 | PASS | PASS | FAIL | DOES_NOT_MEET | FAIL |
| T+1 | G0_OFF | +52 | +7.59 | PASS | PASS | FAIL | DOES_NOT_MEET | PASS |
| T+1 | G0_ON | +58 | +9.82 | PASS | PASS | FAIL | DOES_NOT_MEET | PASS |
| T+1 | G1_OFF | +47 | +9.53 | PASS | PASS | FAIL | DOES_NOT_MEET | PASS |
| T+2 | R0 | +40 | +4.31 | PASS | PASS | PASS | MEETS | FAIL |
| T+2 | G0_OFF | +16 | +2.96 | PASS | PASS | PASS | MEETS | FAIL |
| T+2 | G0_ON | +21 | +2.19 | PASS | PASS | PASS | MEETS | FAIL |
| T+2 | G1_OFF | +15 | +1.86 | PASS | PASS | PASS | MEETS | FAIL |

T+1 models add 47–58 detected onsets but exceed CHANNEL's FAR by 7.59–14.44 pp;
all fail C. At T+2 they add 15–40 detected onsets with FAR increases of 1.86–4.31 pp;
all meet A/B/C. No candidate meets both horizons. The T+2 finding is narrower than
“better onset alerts under BETA”: those complementary controls fail for every model
at T+2. R0 has the largest T+2 detection count (86) and also the highest onset load
(1.268); this is not an automatic model-selection decision.

The T+2 CHANNEL emits 206 alerts: 46 detect an onset, 46 identify an excess that is
not a new onset, and 114 target a non-excess month. Thus its academic FAR is 114/206
(55.34%), while onset false discovery is 160/206 (77.67%). G0_ON has 67 onset,
26 continuation and 126 non-excess alerts. Confusing those definitions changes the
scientific question. T+1 onset and target excess coincide on the non-excess-at-T cohort.

## Paired differences versus R0

These are exactly paired observations, not comparisons between historical aggregate
reports. Negative delta FA means fewer false alerts; negative delta sensitivity means
lost detections. R0 and BETA procedures differ, so these are procedure contrasts,
not causal estimates of one architectural or geographic component.

| Horizon | Model | Delta detected | Delta sensitivity (pp) | Delta FA-onset | Delta FP-excess | Delta FAR (pp) |
| --- | --- | --- | --- | --- | --- | --- |
| T+1 | G0_OFF | +4 | +1.28 | -52 | -52 | -6.85 |
| T+1 | G0_ON | +10 | +3.19 | -27 | -27 | -4.63 |
| T+1 | G1_OFF | -1 | -0.32 | -44 | -44 | -4.92 |
| T+2 | G0_OFF | -24 | -10.96 | -95 | -74 | -1.35 |
| T+2 | G0_ON | -19 | -8.68 | -104 | -78 | -2.11 |
| T+2 | G1_OFF | -25 | -11.42 | -74 | -65 | -2.45 |

G0_OFF and G0_ON improve both pooled T+1 detection and false-alert counts versus R0,
but still miss the academic FAR margin versus CHANNEL. At T+2 the BETA variants
lose 19–25 detections versus R0 while reducing onset false alerts by 74–104. Their
academic compliance does not negate that trade-off. G1 does not dominate G0_OFF:
it loses five detections with eight more onset false alerts at T+1, and loses one
with 21 more at T+2. A lower FAR ratio alone does not establish fewer false alerts.

## Temporal and territorial controls

Each entry below is **delta detected / delta FAR-excess in pp / academic status**
versus CHANNEL. `yes` means all A/B/C pass. These are predeclared descriptive
strata, not additional independent experiments.

| Horizon | Year | R0 | G0_OFF | G0_ON | G1_OFF |
| --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | +13 / +12.34 / no | +14 / +2.84 / yes | +19 / +6.28 / no | +14 / +6.70 / no |
| T+1 | 2021 | +3 / +18.37 / no | +0 / +18.43 / no | +2 / +15.45 / no | -2 / +20.45 / no |
| T+1 | 2022 | +9 / +14.04 / no | +25 / +10.86 / no | +24 / +13.71 / no | +24 / +12.18 / no |
| T+1 | 2024 | +23 / +13.06 / no | +13 / +2.45 / yes | +13 / +3.03 / yes | +11 / +3.37 / yes |
| T+2 | 2020 | +13 / -1.64 / yes | +3 / +7.38 / no | +2 / -2.77 / yes | +1 / -4.06 / yes |
| T+2 | 2021 | +7 / +0.26 / yes | -1 / +0.61 / no | +2 / +5.30 / no | +2 / -6.41 / yes |
| T+2 | 2022 | +18 / +15.83 / no | +9 / +13.51 / no | +14 / +13.22 / no | +14 / +14.81 / no |
| T+2 | 2024 | +2 / -8.03 / yes | +5 / -14.20 / yes | +3 / -18.42 / yes | -2 / -9.28 / no |

| Horizon | Department | R0 | G0_OFF | G0_ON | G1_OFF |
| --- | --- | --- | --- | --- | --- |
| T+1 | Meta | +19 / +9.75 / no | +27 / +1.79 / yes | +34 / +5.56 / no | +27 / +1.79 / yes |
| T+1 | Tolima | +29 / +16.91 / no | +25 / +11.62 / no | +24 / +13.36 / no | +20 / +14.90 / no |
| T+2 | Meta | +7 / +2.44 / yes | -2 / +3.68 / no | +3 / +1.27 / yes | +0 / -2.95 / no |
| T+2 | Tolima | +33 / +4.72 / yes | +18 / +1.95 / yes | +18 / +2.53 / yes | +15 / +4.50 / yes |

All models fail in 2022 at both horizons. At T+1, G0_OFF passes in 2020/2024;
G0_ON and G1_OFF only in 2024; R0 never passes annually. At T+2, R0 passes in
2020/2021/2024, G0_OFF only in 2024, G0_ON in 2020/2024, and G1_OFF in 2020/2021.
G0_ON's 2021 FAR increase is 5.30 pp and therefore fails the fixed 5-pp boundary.
G1's lower 2024 T+2 FAR cannot compensate for detecting two fewer onsets than CHANNEL.

At pooled department level, T+1 compliance is restricted to G0_OFF/G1_OFF in Meta.
At T+2, R0/G0_ON meet in both departments; G0_OFF/G1_OFF meet only in Tolima.
G1 ties CHANNEL's Meta T+2 detections and fails the strictly-greater condition.
Equal pooled counts do not imply identical alerts.

The stricter year-by-department views yield these counts of compliant strata out
of eight; the full counts, denominators and differences remain in the CSVs:

| Horizon | R0 | G0_OFF | G0_ON | G1_OFF |
| --- | --- | --- | --- | --- |
| T+1 | 3/8 | 2/8 | 3/8 | 2/8 |
| T+2 | 3/8 | 1/8 | 4/8 | 3/8 |

## Secondary probabilities

AP/Brier use onset, not target excess. Pooled values do not establish within-year
ranking improvement: [analysis 7](../analisis-7.md) shows that G1's T+1 AP improves
when years are combined despite worsening in each individual year. The benchmark
preserves those same probabilities; it performs no model evaluation on new data.

| Horizon | Model | Onset precision | AP | Brier |
| --- | --- | --- | --- | --- |
| T+1 | G0_OFF | 44.92% | 0.309268 | 0.094352 |
| T+1 | G0_ON | 42.70% | 0.303683 | 0.094855 |
| T+1 | G1_OFF | 42.99% | 0.334520 | 0.092204 |
| T+1 | R0 | 38.07% | 0.260911 | 0.109712 |
| T+2 | G0_OFF | 27.80% | 0.173767 | 0.079653 |
| T+2 | G0_ON | 30.59% | 0.170863 | 0.080261 |
| T+2 | G1_OFF | 25.10% | 0.188141 | 0.078766 |
| T+2 | R0 | 25.15% | 0.161573 | 0.088390 |

## Limits and provenance

This answers the newly clarified academic comparison, not the former V1 code's
zone-based comparator or its FPR metric. The original report was not needed under
Mauricio's explicit clarification. Current H5 and the BETA cohort are preserved;
none of these results rewrites earlier experimental conclusions.

The same years have informed previous development; 2024 is consumed stress and
2025 was consumed by EXP00 and is excluded here. Data are consolidated rather than
historical release vintages. H5 is experimental, coverage is restricted to eligible
Meta/Tolima rows, and comparisons do not prove timely availability, external outbreak
validity, statistical superiority/noninferiority, clinical benefit or national generalization.
There is no independent temporal or prospective confirmation. See
[conclusions](CONCLUSIONS.md) and [reproduction evidence](README.md).

G5 `NOT_APPROVED`; `champion: not_selected`.
