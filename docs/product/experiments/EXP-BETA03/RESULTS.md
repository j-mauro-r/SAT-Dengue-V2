# EXP-BETA03 — retrospective policy results

Status: **COMPLETED_WITH_LIMITATIONS** for the bounded scientific comparison;
the hypothesis is **NO_RESPALDADA** under the frozen joint controls. No champion
was selected. Human PR review and merge remain separate, pending gates.

## Identity and acceptance

Real four-node Kedro execution on 2026-11-02 used clean commit
`04a2716934d89a53e635fbcb2c28120489c3599a`. The [protocol](protocol.json) was frozen
at `8fc0a8e`, before any new policy evaluation. Native R0 selection/evaluation
roles were verified against the canonical table, without modifying either.

Publication:
`tmp/kedro-migration/exp-beta03-runs/9f25fb41dc069f8c2680381bc6d02b1a032d7d1e6152d457ecd94827481c76fe/`.
Manifest SHA-256:
`f95c1d27e89e7fd04a8f1a5d7d62c2049de08ef5c0b19c196be3d49c9c770cfc`.

The publication contains eight payloads plus manifest, 11,399 prediction rows,
54 horizon/year/department metric strata and 30 paired comparisons. All nine
files reproduced **byte for byte** through a second full graph with an in-memory
sink. Both executions performed **zero estimator/calibrator fits**. An actual
second publication was rejected without changing the original destination.

Read-only acceptance independently recomputed thresholds with the existing
native whole-tie selector, applied local shrinkage/caps, reconstructed every
alert and reconciled all metrics/paired criteria. Exact keys, targets, truths
and scores match R0; canonical H5 onset T2 remains a direct transition label.
All 437 inventoried historical files retain original hashes, sizes and modes;
all 27 Beta02 payloads remain identical and read-only. Parent R0 native replay
verifies all 96 captured cells and their manifest linkage, with zero fits.

## Global policy versus the unchanged R0 policy

Both rows per horizon use exactly the same eligible keys, labels, probabilities
and denominator. R0 retains its historical threshold/alerts; its original
selection used broader monitored exposure. GLOBAL reuses the same constrained
algorithm with Beta's eligible exposure. This is a denominator/policy comparison,
not an improvement in fitted probabilities or a historical-contract violation.

| Horizon | Policy | Detected / onsets | Sensitivity | False alerts | FA / eligible municipality-year | Sensitivity difference vs R0 |
|---|---|---:|---:|---:|---:|---:|
| T+1 | R0 | 142 / 313 | 45.37% | 231 | 1.044855 | reference |
| T+1 | GLOBAL | 96 / 313 | 30.67% | 136 | 0.615153 | -14.70 pp |
| T+2 | R0 | 86 / 219 | 39.27% | 256 | 1.268373 | reference |
| T+2 | GLOBAL | 57 / 219 | 26.03% | 175 | 0.867052 | -13.24 pp |

GLOBAL removes 95 false alerts at T1 and 81 at T2, but misses 46 and 29 additional
onsets respectively. The pooled budget holds; the -2 pp margin fails for both
horizons. Only **8/24** global horizon/year/department strata satisfy both
descriptive criteria. No policy is selected as an accepted improvement.

| Evaluation year | T1 R0 detected / FA | T1 GLOBAL detected / FA | T2 R0 detected / FA | T2 GLOBAL detected / FA |
|---|---:|---:|---:|---:|
| 2020 | 31 / 74 | 13 / 20 | 25 / 75 | 10 / 24 |
| 2021 | 13 / 35 | 13 / 35 | 12 / 33 | 12 / 33 |
| 2022 | 33 / 46 | 33 / 46 | 26 / 94 | 26 / 94 |
| 2024, consumed stress | 65 / 76 | 37 / 35 | 23 / 54 | 9 / 24 |

The unchanged decisions in 2021/2022 are reported as equivalence on those cuts,
not as invented new gains. Department controls reveal failures hidden by pooling:
GLOBAL T1 FA rates are 1.028571 in Meta/2022 and 1.210084 in Tolima/2024; T2/2022
rates are 2.597938 in Meta and 1.395973 in Tolima. Development feasibility does
not guarantee a future realized budget. The complete
[aggregate table](METRICS_BY_STRATUM.csv) preserves all territories and years.

Scores are unchanged: T1 pooled Brier 0.109712 and AP 0.260911; T2 Brier 0.088390
and AP 0.161573 for both R0 and GLOBAL. Better thresholded precision alone is
insufficient to satisfy the joint sensitivity/load decision.

## Conditional alternatives

Both departments met the frozen support/heterogeneity trigger only for **2020**,
in both horizons. DEPARTMENT was compared only there; the other six cells remain
`NO_EVALUABLE` for an incremental territorial comparison and fall back to GLOBAL.
No duplicate fallback arm was presented as another experiment.

| Matched 2020 cohort | R0 detected / FA | GLOBAL detected / FA | DEPARTMENT detected / FA | Department sensitivity difference vs R0 |
|---|---:|---:|---:|---:|
| T1, 69 onsets | 31 / 74 | 13 / 20 | 10 / 14 | -30.43 pp |
| T2, 51 onsets | 25 / 75 | 10 / 24 | 11 / 31 | -27.45 pp |

DEPARTMENT satisfies none of its **6** matched horizon/department strata jointly.
Its partial pooled totals must not be compared against all-year R0 totals.
This is a negative result for this fixed regularized rule on supported cuts,
not proof against every territorial policy or against missing profiles.

Across all eight original development selection roles there are **zero false
positives with calibrated score >=0.8**, hence zero recurrent municipal errors
at that predeclared confidence level. Moreover, each frozen predictor has only
one six-month policy selection block, with no independent recurrence and untouched
policy block. Additional asymmetric learning or hard-negative mining is
`CONDICIONAL_NO_JUSTIFICADO`, unexecuted. It has no invented performance result.
No second classifier or reinforcement learning was introduced.

## Limits and validation

Seven new generated-only acceptance tests plus the mapped regression checks
pass: **70 tests**, with 25 inherited framework warnings. Scoped Ruff, formatting,
mypy (10 files), Markdown and whitespace checks pass. These technical checks
remain separate from the real execution and native reproduction above.

2020-2022 are reused retrospective development and 2024 is consumed stress;
none is independent confirmation. No 2025 target was evaluated. Statistical
noninferiority is **UNAVAILABLE**, superiority **NOT_ESTABLISHED**. Consolidated
notifications and H5 are retrospective proxies, not independently validated
clinical onset or operational availability. Sparse temporal blocks cannot justify
prospective, causal, or deployment claims. Preserve G5 **NOT_APPROVED** and
champion **not_selected**. See the [program closure](../EXP-BETA/CONCLUSIONS.md).
