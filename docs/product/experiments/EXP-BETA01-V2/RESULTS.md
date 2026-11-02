# EXP-BETA01 V2 — Results

Execution: **`COMPLETED_WITH_LIMITATIONS`**, 2026-11-02. Scientific hypothesis:
**`NO_RESPALDADA`**. This is real retrospective evidence from the identified
publication; generated fixtures are only technical checks. Integration remains
subject to personal review and disposition of inherited CI findings.

## Frozen execution and identities

The [protocol](protocol.json) and code were committed before the first real fit:
`83ab1ae08647f2dbcf848f1228cc17ef6d87dcae`. Protocol SHA-256:
`2ebfcc7060cdd39926cb6ff9f6cdf301e436bdd4c067bb0ca8533863b7c950bb`.
Execution used that clean commit, the identified national table and frozen G0/R0
sources. No criterion, period, feature, hyperparameter or policy rule was changed
after seeing G1 results.

V2 bundle: `a4fdd4d955f867c49a8142a334e989e084c30587262fac4e1940a2b8d9190d6e`
under `data/processed/exp_beta01_v2/`. Manifest SHA-256:
`9fc80bfc0fae23f73f49c9e87afb3704a8fc5e19f8c7c924fe89505b94305e60`.
The manifest binds 40 payloads: eight UBJ models, held-out scores, predictions,
metrics, comparisons, policies/cell states, preflight, protocol and provenance.
There were **8 real XGBoost fits and 8 global intercept calibrations**, zero G0,
R0 or G0_MATCHED fits, zero territorial adaptations and zero climate-ON fits.

## Actual training support

The [pre-fit support table](TRAINING_SUPPORT.csv) records all eight cells;
[role support](ROLE_SUPPORT.csv) records all 40 chronological role cells, their
origin/target boundaries, embargo and observations actually used. G0_MATCHED was
unnecessary because all regional role keys, 24 predictors and truths match V1
exactly. Only additional training observations differ.

| Horizon | Evaluation year | G1 training rows | Regional control rows | Additional rows | Total / additional territories | Additional origin range |
|---|---:|---:|---:|---:|---:|---|
| T+1 | 2020 | 8,394 | 3,155 | 5,239 | 1,093 / 1,017 | 2016-06–2016-11 |
| T+1 | 2021 | 20,967 | 3,938 | 17,029 | 1,121 / 1,045 | 2016-06–2017-11 |
| T+1 | 2022 | 33,281 | 4,691 | 28,590 | 1,122 / 1,046 | 2016-06–2018-11 |
| T+1 | 2024 | 53,217 | 5,728 | 47,489 | 1,122 / 1,046 | 2016-06–2020-11 |
| T+2 | 2020 | 7,400 | 3,089 | 4,311 | 1,083 / 1,007 | 2016-06–2016-10 |
| T+2 | 2021 | 19,907 | 3,871 | 16,036 | 1,121 / 1,045 | 2016-06–2017-10 |
| T+2 | 2022 | 32,317 | 4,638 | 27,679 | 1,122 / 1,046 | 2016-06–2018-10 |
| T+2 | 2024 | 52,231 | 5,655 | 46,576 | 1,122 / 1,046 | 2016-06–2020-10 |

All cells met the predeclared support rule; none was moved to a different period.
2020 adds only six/five origin months. National support is thus not uniformly
available from the regional 2011 start; this comparison does not separately
identify causal effects of municipality count, season, recency and geography.

## Identical evaluation populations

The evaluation universe is the original 29 Meta and 47 Tolima municipalities.
Actual at-risk cohorts are identical to frozen V1 and native R0: **2,653 rows and
313 H5 onsets for T+1; 2,422 rows and 219 onsets for T+2**. G1/G0/R0 together
produce 15,225 prediction rows. Exposure is rows/12: 221.083333 and 201.833333
eligible municipality-years, not 76 × four calendar years.

Not every municipality contributes an at-risk observation in every cell: 2024
contains 72 T+1 and 70 T+2 municipalities. This is the original cohort, not a
new post-result exclusion. H5 onset is a retrospective proxy, not independently
validated clinical outbreak truth. No 2025 observation enters a fitted or
evaluated role; 2024 remains consumed retrospective stress.

## Pooled descriptive results

Counts and exposure are summed, and rates recomputed; annual rates are not
averaged. All comparisons use identical keys and outcomes.

| Horizon | Arm | Detected / onsets | Sensitivity | False alerts | FA / municipality-year | Precision | AP | Brier |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T+1 | R0 frozen | 142 / 313 | 45.37% | 231 | 1.044855 | 0.380697 | 0.260911 | 0.109712 |
| T+1 | G0 frozen OFF | 146 / 313 | 46.65% | 179 | 0.809649 | 0.449231 | 0.309268 | 0.094352 |
| T+1 | G1 national OFF | 141 / 313 | 45.05% | 187 | 0.845835 | 0.429878 | 0.334520 | 0.092204 |
| T+2 | R0 frozen | 86 / 219 | 39.27% | 256 | 1.268373 | 0.251462 | 0.161573 | 0.088390 |
| T+2 | G0 frozen OFF | 62 / 219 | 28.31% | 161 | 0.797688 | 0.278027 | 0.173767 | 0.079653 |
| T+2 | G1 national OFF | 61 / 219 | 27.85% | 182 | 0.901734 | 0.251029 | 0.188141 | 0.078766 |

G1 versus G0 loses **5 detections and adds 8 false alerts in T+1** (−1.60 pp
sensitivity); it loses **1 detection and adds 21 false alerts in T+2** (−0.46 pp).
Both aggregate primary outcomes are worse. AP and Brier improve in both
horizons, but neither is the adopted joint alert criterion.

Against R0, G1 T+1 loses one detection (−0.32 pp) and removes 44 false alerts;
it meets the aggregate ≤1 load and −2 pp descriptive margin. In T+2 it loses
25 detections (−11.42 pp) while removing 74 false alerts: the margin fails despite
aggregate load compliance. Precision is also lower than G0 in both horizons.

## Temporal and department controls

| Horizon | Year | Rows / onsets | G1 detected | G1 FA | Sensitivity | FA / municipality-year |
|---|---:|---:|---:|---:|---:|---:|
| T+1 | 2020 | 661 / 69 | 32 | 59 | 46.38% | 1.071104 |
| T+1 | 2021 | 846 / 52 | 8 | 24 | 15.38% | 0.340426 |
| T+1 | 2022 | 693 / 89 | 48 | 62 | 53.93% | 1.073593 |
| T+1 | 2024 | 453 / 103 | 53 | 42 | 51.46% | 1.112583 |
| T+2 | 2020 | 588 / 51 | 13 | 34 | 25.49% | 0.693878 |
| T+2 | 2021 | 779 / 45 | 7 | 20 | 15.56% | 0.308087 |
| T+2 | 2022 | 641 / 62 | 22 | 86 | 35.48% | 1.609984 |
| T+2 | 2024 | 414 / 61 | 19 | 42 | 31.15% | 1.217391 |

| Horizon | Department | Rows / onsets | G1 detected | G1 FA | Sensitivity | FA / municipality-year |
|---|---|---:|---:|---:|---:|---:|
| T+1 | Meta | 1,024 / 146 | 74 | 66 | 50.68% | 0.773438 |
| T+1 | Tolima | 1,629 / 167 | 67 | 121 | 40.12% | 0.891344 |
| T+2 | Meta | 943 / 96 | 25 | 72 | 26.04% | 0.916225 |
| T+2 | Tolima | 1,479 / 123 | 36 | 110 | 29.27% | 0.892495 |

The [90-row full stratum table](RESULTS_BY_STRATUM.csv) includes G1, frozen G0
and R0, all years/departments and pooled results, with Brier, AP and precision.
The [60 paired contrasts](COMPARISONS_BY_STRATUM.csv) include sensitivity,
detections, false alerts, load, Brier and AP differences. The formal descriptive
margin is against R0; the analogous G0 pairwise diagnostic is supplementary,
not a statistical noninferiority result.

G1 fails the adopted R0 joint criterion in **20/24 annual strata** (annual total,
Meta, Tolima across two horizons), and **24/30** when pooled department/total
strata are also counted. Within annual department-only strata it fails 12/16.
These strata overlap and are not independent statistical experiments. No winner
is selected from a better pooled average or a better secondary metric.

## Reproduction and technical status

Eight saved models were reloaded with no new fit or recalibration. Raw held-out
scores, selected policies, prediction CSV, metric CSV, contrasts and conclusions
reproduce exactly, byte for byte. All 48 comparable annual G0/R0 metric rows
match the frozen source to 1e-15 numeric tolerance; keys, truths and alerts match
exactly. All historical input/payload hashes remain unchanged.
The recorded XGBoost, scikit-learn, NumPy, pandas and Kedro package versions also
match those of the frozen V1 execution.

Real publication readback, replacement refusal and tampered-payload refusal pass.
Detailed local verification is under
`data/interim/exp_beta01_v2/a4fdd4d955f867c49a8142a334e989e084c30587262fac4e1940a2b8d9190d6e/`.
Only aggregate evidence is versioned; native models and municipality-level
predictions remain private.

The focused 66-test suite, Ruff/format/mypy, Markdown links, whitespace and
repo-only conformance pass. This is not an all-CI approval: inherited
data-diagnostics filesystem layering and local old-document preservation
findings remain explicitly identified in [README](README.md). The missing
directory inventory entry was reconciled without changing its test. No test or
historical baseline was weakened to obtain a favorable result.
