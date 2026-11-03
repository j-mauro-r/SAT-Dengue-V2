# EXP-DELTA01 results

**Execution: completed and reproduced. Primary hypothesis: `NO_EVALUABLE`.**
The four-node Kedro graph ran under [authorized revision 2](protocol.revision-2.json).
The original G0_OFF evaluation probabilities, P0 thresholds/alerts, H5 and full cohorts
are preserved. No inference, fitting or recalibration was performed in DELTA.

## Complete primary cohorts

| Horizon | Policy | Rows / onsets | Detected | Sensitivity | Alerts | False excess / FAR | False onset / FA per eligible municipality-year | A / B / C | Academic result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | P0 | 2653 / 313 | 146 | 46.65% | 325 | 179 / 55.08% | 179 / 0.809649 | 1 / 1 / 0 | DOES_NOT_MEET |
| T+1 | P1 | 2653 / 313 | unavailable | unavailable | unavailable | unavailable / unavailable | unavailable / unavailable | unavailable / unavailable / unavailable | NO_EVALUABLE |
| T+2 | P0 | 2422 / 219 | 62 | 28.31% | 223 | 130 / 58.30% | 161 / 0.797688 | 1 / 1 / 1 | MEETS |
| T+2 | P1 | 2422 / 219 | unavailable | unavailable | unavailable | unavailable / unavailable | unavailable / unavailable | unavailable / unavailable / unavailable | NO_EVALUABLE |

CHANNEL detects 94/313 and 46/219 onsets at T+1/T+2; its excess FAR is
47.4860% / 55.3398%. PERSISTENCE emits no alerts and detects zero onsets on these
current-non-excess cohorts; its FAR is undefined. P0 exceeds CHANNEL detections in
both horizons, but T+1 exceeds its FAR by 7.5909 pp and fails C. P0 T+2's difference
is 2.9562 pp and the complete pooled baseline already meets A/B/C.

P1 has no admissible development threshold in T+1/2022 and T+2/2024. Per the frozen
rule, all rows and P0 remain present, unavailable P1 alerts are null (not false),
and neither complete primary horizon may be replaced by a partially pooled cohort.
P1 primary probabilities remain identical to P0; AP/Brier are still defined because
they depend on scores, not on an available alert policy. AP/Brier are calculated
once per shared stratum and attached to both policies: pooled T+1 AP 0.3092681819016528,
Brier 0.09435222153781342; T+2 AP 0.1737667909570269, Brier 0.07965280809844288.

## Exhaustive selection feasibility

| Cell | Selection rows / onsets | Unique score thresholds | Feasible thresholds | Minimum FAR with a detection | Allowed FAR |
| --- | --- | --- | --- | --- | --- |
| T+1 / 2022 | 846 / 52 | 510 | 0 | 60.00% | 59.55% |
| T+2 / 2024 | 371 / 72 | 259 | 0 | 33.33% | 30.49% |

Both cells have both onset classes and both excess classes and defined CHANNEL FAR.
Failure is **no feasible threshold**, not missing data or insufficient support.
Every unique score threshold, with whole ties, was exhaustively checked. No-alert
was included as an undefined-FAR, infeasible candidate. No fallback or evaluation-led
reselection was introduced. The tiny T+1/2022 gap is still outside the inclusive
5 pp margin: the exact ceiling is 59.5454545%, not 60%.

## Annual comparison on unchanged cohorts

| Horizon | Year | Department | Onsets | Detected P0 → P1 | Excess FAR P0 → P1 | Academic P0 → P1 |
| --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | Pooled | 69 | 32 → 13 | 60.98% → 60.61% | MEETS → DOES_NOT_MEET |
| T+1 | 2021 | Pooled | 52 | 10 → 8 | 72.97% → 70.37% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+1 | 2022 | Pooled | 89 | 49 → unavailable | 55.05% → unavailable | DOES_NOT_MEET → NO_EVALUABLE |
| T+1 | 2024 | Pooled | 103 | 55 → 27 | 43.30% → 34.15% | MEETS → DOES_NOT_MEET |
| T+2 | 2020 | Pooled | 51 | 15 → 15 | 71.01% → 71.01% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2021 | Pooled | 45 | 4 → 19 | 73.68% → 74.07% | DOES_NOT_MEET → MEETS |
| T+2 | 2022 | Pooled | 62 | 17 → 23 | 63.51% → 62.77% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2024 | Pooled | 61 | 26 → unavailable | 32.79% → unavailable | MEETS → NO_EVALUABLE |

These are cell-level descriptive controls, not substitutes for the incomplete
primary comparison. Sensitivity is detected/onsets in each row.

## Paired gains and losses

| Horizon | Year | Gained / lost onset detections | Δ false excess alerts | Δ false onset alerts | Δ emitted alerts |
| --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 0 / 19 | -30 | -30 | -49 |
| T+1 | 2021 | 0 / 2 | -8 | -8 | -10 |
| T+1 | 2022 | unavailable / unavailable | unavailable | unavailable | unavailable |
| T+1 | 2024 | 0 / 28 | -28 | -28 | -56 |
| T+2 | 2020 | 0 / 0 | 0 | 0 | 0 |
| T+2 | 2021 | 15 / 0 | 46 | 47 | 62 |
| T+2 | 2022 | 6 / 0 | 12 | 14 | 20 |
| T+2 | 2024 | unavailable / unavailable | unavailable | unavailable | unavailable |

All differences are P1 minus P0 on the same keys. False excess alerts count alerts
when the target is not in excess. False onset alerts additionally count continuation
alerts; they are different quantities at T+2. T+2/2022 sensitivity rises from
17/62 = 27.42% to 23/62 = 37.10%, while false excess/onset alerts increase from
47/57 to 59/71. FAR falls slightly from 63.51% to 62.77%, but CHANNEL is 50%:
the 12.77 pp difference still fails C.

## Temporal and territorial controls

| Horizon | Year | Department | Onsets | Detected P0 → P1 | Excess FAR P0 → P1 | Academic P0 → P1 |
| --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | Meta | 26 | 12 → 6 | 57.14% → 60.00% | MEETS → DOES_NOT_MEET |
| T+1 | 2020 | Tolima | 43 | 20 → 7 | 62.96% → 61.11% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+1 | 2021 | Meta | 24 | 6 → 4 | 66.67% → 69.23% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+1 | 2021 | Tolima | 28 | 4 → 4 | 78.95% → 71.43% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+1 | 2022 | Meta | 49 | 30 → unavailable | 45.45% → unavailable | DOES_NOT_MEET → NO_EVALUABLE |
| T+1 | 2022 | Tolima | 40 | 19 → unavailable | 64.81% → unavailable | DOES_NOT_MEET → NO_EVALUABLE |
| T+1 | 2024 | Meta | 47 | 26 → 12 | 33.33% → 14.29% | MEETS → DOES_NOT_MEET |
| T+1 | 2024 | Tolima | 56 | 29 → 15 | 50.00% → 44.44% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2020 | Meta | 17 | 4 → 4 | 79.31% → 79.31% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2020 | Tolima | 34 | 11 → 11 | 65.00% → 65.00% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2021 | Meta | 20 | 2 → 9 | 75.00% → 69.70% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2021 | Tolima | 25 | 2 → 10 | 72.73% → 77.08% | DOES_NOT_MEET → MEETS |
| T+2 | 2022 | Meta | 32 | 7 → 10 | 50.00% → 44.12% | DOES_NOT_MEET → MEETS |
| T+2 | 2022 | Tolima | 30 | 10 → 13 | 71.74% → 73.33% | DOES_NOT_MEET → DOES_NOT_MEET |
| T+2 | 2024 | Meta | 27 | 10 → unavailable | 34.62% → unavailable | DOES_NOT_MEET → NO_EVALUABLE |
| T+2 | 2024 | Tolima | 34 | 16 → unavailable | 31.43% → unavailable | MEETS → NO_EVALUABLE |

In 2022 T+2, Meta gains three detections (7→10), false excess alerts rise 14→15,
and FAR falls 50.00%→44.12%, meeting all three criteria versus CHANNEL FAR 43.48%.
Tolima also gains three detections (10→13), but false excess alerts rise 33→44
and FAR increases 71.74%→73.33%, versus CHANNEL 57.89%; it continues to fail C.
There is no demonstrated territorial stability, and missing primary cells also
prevent complete P1 department-pooled claims.

## Development-to-evaluation transport

| Horizon | Evaluation year | Frozen P1 threshold | Selection CHANNEL FAR | Selection P1 FAR | Evaluation CHANNEL FAR | Evaluation P1 FAR | Evaluation C |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 0.25858983208357533 | 33.33% | 36.11% | 58.14% | 60.61% | 1 |
| T+1 | 2021 | 0.2746485589198247 | 58.14% | 61.67% | 54.55% | 70.37% | 0 |
| T+1 | 2022 | unavailable | 54.55% | unavailable | 44.19% | unavailable | unavailable |
| T+1 | 2024 | 0.20342642621367116 | 35.19% | 40.00% | 40.85% | 34.15% | 1 |
| T+2 | 2020 | 0.11462376510073843 | 34.48% | 33.33% | 63.64% | 71.01% | 0 |
| T+2 | 2021 | 0.14484159372720484 | 63.64% | 68.55% | 73.08% | 74.07% | 1 |
| T+2 | 2022 | 0.24729996295085496 | 73.08% | 77.67% | 50.00% | 62.77% | 0 |
| T+2 | 2024 | unavailable | 25.49% | unavailable | 46.99% | unavailable | unavailable |

Each of the six available thresholds satisfies its own development constraint,
using only that cell's historical selection block. Only three satisfy evaluation C:
T+1/2020, T+1/2024 and T+2/2021. A lower absolute evaluation FAR need not preserve
the relative CHANNEL margin: T+2/2022 FAR falls from 77.67% in development to
62.77%, yet evaluation CHANNEL falls to 50%, so C fails. Development compliance
provides no guarantee of future compliance. Evaluation did not affect any threshold.

## Artifacts and verification

- Results: `data/processed/exp_delta01/d5c482b64e0d44e5012b20d24baa73d14f829ca4857bb2e2e53870ab3a82a284`.
- Result manifest SHA-256: `a6f67b769cc52365da097ffa1b2709452252f0b7e9a5e6a6644c70a7f1cb0a92`.
- Threshold freeze: `data/processed/exp_delta01/selection_freezes/e99f60fed004de212b4310d1114ad60e51b097a48ea7e251d2fbc41b8935d2b0`;
  manifest SHA-256 `592a166956fdf536ea247eae6d99f3d01e6674ea8b030f2ef91ab34e7b6ddbad`.
- Recovery source: `data/processed/exp_delta01/recovered_selection/b2e8256c9c37f8ecdb5f895ccd6d936cfb11f3896adc654ecab3c386bf57acc1`.

The private publication contains all 10,150 paired policy rows (5,075 keys twice),
60 metric strata, 30 paired-change strata, eight policies/transport audits and the
complete candidate frontier. All eight full selection sets (4,386 scores) were
consumed without reconstruction. Detailed keys/scores stay under ignored `data/`.

PASS: four-node Kedro run; exact P0/P1 keys/labels/probabilities; original P0 equality;
source/role identities and temporal separation; independent exhaustive selection;
independent counts in all 60 strata; all 10 publication payloads reproduced byte
for byte; immutable freeze readback; actual result overwrite refusal; source hashes
preserved. DELTA made zero inference calls, fits or calibrations. Tests, validation
commands and review/integration status are in [README.md](README.md).

All years were previously analyzed. 2024 is consumed stress, 2025 is excluded,
H5 remains experimental, and operational historical availability/statistical
superiority are not established. G5 `NOT_APPROVED`; `champion: not_selected`.
