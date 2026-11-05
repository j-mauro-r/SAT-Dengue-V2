# EXP-DELTA02-R1 — fixed MGN 2018 spatial epidemiological revision

Frozen on 2026-11-03 before feature construction, fitting, policy selection, or
evaluation. Authority: Mauricio's explicit EXP-DELTA02-R1 request. Lineage:
`experiment/EXP-DELTA02-R1` starts at `bfc10b5` and imports the unchanged
EXP-DELTA02 commit `b3c982f` as an explicit dependency.

## Hypothesis and evidence status

Recent dengue activity in municipalities that share a positive-length boundary
with a target municipality may improve detection of new T+1 H5 onsets without
exceeding the academic false-alert margin. This is one retrospective exploratory
test on consumed 2020, 2021, 2022, and 2024 periods. It cannot establish
statistical superiority, independent temporal validation, prospective efficacy,
or point-in-time operational availability.

R1 does not revise EXP-DELTA02. The original `NOT_EVALUABLE` result, protocol,
results, conclusions, provenance, source specification, audit implementation,
and tests remain immutable. R1 records the newly authorized assumption that
DANE MGN 2018 is a fixed retrospective geographic approximation for every
period. Its boundaries are not claimed to be historically exact.

## Fixed geography and feature

Use only the pinned official DANE MGN 2018 municipal polygon members from the
original source bundle. Do not retrieve, compare, repair, snap, buffer, simplify,
or substitute another geography. A municipality is a neighbor when its polygon
shares a boundary segment of strictly positive native-CRS length with the target:

- retain all national neighbors, including municipalities outside Meta/Tolima;
- exclude the target municipality and point-only contacts;
- retain every MGN 2018 relation, including the nine relations that differed in
  the original cross-vintage audit;
- never select a neighbor using outcomes, correlations, or prior model errors.

For target municipality `i` and origin month `T`, add exactly one predictor:

```text
neighbor_dengue_mean_lag1(i,T) = mean(C(j,T-1) for j in N(i))
```

`C` is the national canonical general-dengue notification count. The graph and
neighbor denominator are fixed. Every required neighbor-month must have an
admitted row and a non-missing count. Otherwise the feature remains missing and
records its coverage reason. Absence is never converted to a confirmed zero.
No alternative lag, window, transform, population standardization, weighting,
distance rule, graph union/intersection, or partial-neighbor mean is allowed.

## Candidate and chronology

Train exactly one pooled candidate: G0_OFF plus
`neighbor_dengue_mean_lag1`. Reuse BETA01's common complete ON cohort,
non-climate ordered predictors, categorical zone encoding, missing-value rules,
XGBoost family, pooled-intercept calibration, selection-only whole-tie policy,
and deterministic configuration. The fixed estimator has 80 trees, depth 2,
learning rate 0.05, `hist` tree method, seed 1729, and one job. Do not fit local
municipal or departmental adaptations.

For target year `Y`, use the inherited roles without adaptation:

| Role | Target period |
| --- | --- |
| Train | through `Y-4` |
| Calibration | `Y-3` |
| Unused gap | `Y-2` |
| Policy selection | `Y-1` |
| Evaluation | `Y` |

The existing origin embargo applies at every boundary. Only observations known
through T−1 may enter the new feature for origin T. Labels and target-month
counts are outcomes only. No evaluation output may change a predictor, neighbor,
missingness rule, model parameter, calibration rule, policy objective, or
threshold.

## Frozen comparison

Retain 76 Meta/Tolima municipalities, H5, P75, origins without excess at T,
horizon T+1 only, 2,653 municipality-origin rows, and 313 onsets over
2020/2021/2022/2024. Candidate and comparators must have identical ordered keys
and truths. CHANNEL, PERSISTENCE, R0, and original G0_OFF scores, policies, and
alerts are read-only.

The academic FAR is false alerts relative to target excess divided by all
alerts. It is not FPR and not onset false discovery. Report onset false alerts
separately. The pooled joint decision requires:

- A: candidate detections are strictly greater than CHANNEL detections;
- B: candidate detections are strictly greater than PERSISTENCE detections;
- C: candidate FAR-excess is no more than CHANNEL FAR-excess plus 0.05.

Historical pooled values are reconciliation controls only: CHANNEL 94/313 at
47.49% FAR; R0 142/313 at 61.93%; G0_OFF 146/313 at 55.08%. They cannot select
or alter the R1 policy.

## Outputs and disposition

Report rows, onsets detected/missed, sensitivity, alerts, false onset alerts,
false excess alerts, FAR-excess, FAR delta from CHANNEL, false alerts per eligible
municipality-year, AP/Brier when defined, and A/B/C separately and jointly. Emit
pooled, year, department, and year-department strata. Pair against G0_OFF to
count gained/lost onsets and added/removed false alerts. Quantify feature
missingness by year and department without changing denominators.

Private row-level feature, prediction, model, policy, and manifest payloads are
written atomically to one content-addressed ignored publication under
`data/processed/exp_delta02_r1/`. Reproduction must yield identical payload
bytes. Committed documents contain aggregate evidence only.

The final scientific disposition is exactly one of `EXPLORATORY_IMPROVEMENT`,
`NOT_SUPPORTED`, or `NOT_EVALUABLE`. A pooled pass does not imply stability or
operational efficacy. G5 remains `NOT_APPROVED`; champion remains
`not_selected`. No EXP-DELTA03 or T+2 work follows automatically.

## Fail-closed preflight

Before any fit, verify every identity in [sources.json](sources.json), the
MGN 2018 member inventory, exact 76 target codes, unique national codes and
municipality-month keys, feature chronology/coverage, inherited predictor and
parameter contracts, chronological role support, complete frozen comparator
keys/truths, H5/P75 cohort counts, and original publication preservation. A
failure raises an execution error before XGBoost construction. It is not
silently converted into `NOT_EVALUABLE` and never triggers source substitution.
