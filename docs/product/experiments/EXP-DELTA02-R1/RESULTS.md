# EXP-DELTA02-R1 results

Execution date: 2026-11-03. Scientific disposition: `NOT_SUPPORTED`.

The fixed R1 procedure completed on the exact pinned private sources and was
reproduced byte-for-byte. It evaluated the frozen T+1 cohort of 2,653
municipality-origin rows and 313 onsets in 76 Meta/Tolima municipalities. The
immutable private bundle is
`1d2665c4a348ddcf9aa270336cb89f27b490d6292c393f8ef88b4c98c84a57d8`;
its manifest SHA-256 is
`33a8b2d21cb7b97aa7015a1ffcf419528a327127b648cb3bcaefbc4325f01975`.

## Pooled comparison

| Arm | Detected / 313 | Sensitivity | Alerts | False excess alerts | FAR-excess | False alerts / municipality-year | AP | Brier | Budget met |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CHANNEL | 94 | 0.3003 | 179 | 85 | 0.4749 | 0.3845 | n/a | n/a | yes |
| PERSISTENCE | 0 | 0.0000 | 0 | 0 | undefined | 0.0000 | n/a | n/a | yes |
| R0 | 142 | 0.4537 | 373 | 231 | 0.6193 | 1.0449 | 0.2609 | 0.1097 | no |
| G0_OFF | 146 | 0.4665 | 325 | 179 | 0.5508 | 0.8096 | 0.3093 | 0.0944 | yes |
| R1_SPATIAL | 147 | 0.4696 | 333 | 186 | 0.5586 | 0.8413 | 0.3095 | 0.0943 | yes |

Academic conditions A and B pass: R1 detects more onsets than CHANNEL and
PERSISTENCE. Condition C fails: its 55.86% FAR-excess is above CHANNEL's 47.49%
plus the fixed five-point margin (52.49%). The joint academic status is therefore
`DOES_NOT_MEET`. Against G0_OFF, R1 gains one onset but adds seven false excess
alerts; FAR-excess increases 0.78 percentage points. AP changes by +0.00022 and
Brier by -0.00003, which is not evidence of statistical superiority.

## Candidate strata

Department 50 is Meta and 73 is Tolima. FAR is false excess alerts divided by
all alerts; it is not FPR or onset false-discovery rate.

| Year | Department | Rows | Onsets | Detected | Sensitivity | Alerts | False excess alerts | FAR-excess | False alerts / municipality-year | AP | Brier | Budget met |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| all | all | 2,653 | 313 | 147 | 0.4696 | 333 | 186 | 0.5586 | 0.8413 | 0.3095 | 0.0943 | yes |
| all | 50 | 1,024 | 146 | 75 | 0.5137 | 144 | 69 | 0.4792 | 0.8086 | 0.4136 | 0.1038 | yes |
| all | 73 | 1,629 | 167 | 72 | 0.4311 | 189 | 117 | 0.6190 | 0.8619 | 0.2302 | 0.0884 | yes |
| 2020 | all | 661 | 69 | 32 | 0.4638 | 82 | 50 | 0.6098 | 0.9077 | 0.3423 | 0.0823 | yes |
| 2020 | 50 | 281 | 26 | 12 | 0.4615 | 28 | 16 | 0.5714 | 0.6833 | 0.4413 | 0.0710 | yes |
| 2020 | 73 | 380 | 43 | 20 | 0.4651 | 54 | 34 | 0.6296 | 1.0737 | 0.3077 | 0.0906 | no |
| 2021 | all | 846 | 52 | 10 | 0.1923 | 37 | 27 | 0.7297 | 0.3830 | 0.1995 | 0.0558 | yes |
| 2021 | 50 | 318 | 24 | 6 | 0.2500 | 18 | 12 | 0.6667 | 0.4528 | 0.2603 | 0.0648 | yes |
| 2021 | 73 | 528 | 28 | 4 | 0.1429 | 19 | 15 | 0.7895 | 0.3409 | 0.1700 | 0.0504 | yes |
| 2022 | all | 693 | 89 | 50 | 0.5618 | 117 | 67 | 0.5726 | 1.1602 | 0.4550 | 0.1037 | no |
| 2022 | 50 | 210 | 49 | 31 | 0.6327 | 59 | 28 | 0.4746 | 1.6000 | 0.5770 | 0.1482 | no |
| 2022 | 73 | 483 | 40 | 19 | 0.4750 | 58 | 39 | 0.6724 | 0.9689 | 0.3274 | 0.0843 | yes |
| 2024 | all | 453 | 103 | 55 | 0.5340 | 97 | 42 | 0.4330 | 1.1126 | 0.5251 | 0.1695 | no |
| 2024 | 50 | 215 | 47 | 26 | 0.5532 | 39 | 13 | 0.3333 | 0.7256 | 0.5977 | 0.1610 | yes |
| 2024 | 73 | 238 | 56 | 29 | 0.5179 | 58 | 29 | 0.5000 | 1.4622 | 0.4749 | 0.1771 | no |

## Paired change from G0_OFF

R1 and G0_OFF produce identical alerts in 2020, 2021, and 2024. In 2022, R1
adds eight alerts: one detects an onset and seven are false relative to both the
onset and excess targets. Meta accounts for the gained onset and three false
alerts; Tolima adds four false alerts and no onset. There are no lost onsets or
removed false alerts in any reported stratum.

| Stratum | Gained onsets | Lost onsets | Added false excess alerts | Removed false excess alerts |
| --- | ---: | ---: | ---: | ---: |
| pooled | 1 | 0 | 7 | 0 |
| Meta pooled | 1 | 0 | 3 | 0 |
| Tolima pooled | 0 | 0 | 4 | 0 |
| 2020 all/Meta/Tolima | 0 | 0 | 0 | 0 |
| 2021 all/Meta/Tolima | 0 | 0 | 0 | 0 |
| 2022 all | 1 | 0 | 7 | 0 |
| 2022 Meta | 1 | 0 | 3 | 0 |
| 2022 Tolima | 0 | 0 | 4 | 0 |
| 2024 all/Meta/Tolima | 0 | 0 | 0 | 0 |

## Feature coverage

The MGN 2018 graph has 460 directed target-neighbor edges, including 66
external municipalities, with 3–12 neighbors per target-origin. The feature is
available for 481/2,653 rows (18.1%) and remains missing for 2,172 rows (81.9%)
because at least one fixed neighbor count is unknown. No partial-neighbor mean
or absent-to-zero conversion is used.

| Year | Available | Missing | Availability |
| --- | ---: | ---: | ---: |
| 2020 | 130 | 531 | 19.7% |
| 2021 | 48 | 798 | 5.7% |
| 2022 | 85 | 608 | 12.3% |
| 2024 | 218 | 235 | 48.1% |
| all | 481 | 2,172 | 18.1% |

## Reproduction and limits

`--publish` and `--reproduce` independently regenerated the same complete
payload inventory and byte identity. The publication contains four fitted
XGBoost models, temporal role/policy records, predictions, metrics, comparisons,
coverage, paired changes, conclusions, source identities and execution
provenance. The committed report contains aggregates only.

This is retrospective exploratory evidence on consumed years. MGN 2018 is one
fixed approximation, not proof of historically exact boundaries. Consolidated
notification tables do not establish point-in-time operational availability.
The very high honest feature missingness limits interpretation, and no untouched
period remains here for independent confirmation.
