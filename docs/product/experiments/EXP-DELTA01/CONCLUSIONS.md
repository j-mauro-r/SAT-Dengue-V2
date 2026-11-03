# EXP-DELTA01 — scientific closure

## State and scientific decision

- Execution: `COMPLETED`.
- Primary hypothesis EXP-DELTA01-H1: `NO_EVALUABLE`.
- P1: not enabled for general adoption.
- P0: preserved as the historical reference, without a new adoption decision.
- G5: `NOT_APPROVED`.
- Champion: `not_selected`.

EXP-DELTA01 asked whether an academic alert policy could improve contractual
compliance over the original BETA policy using exactly the same G0_OFF probabilities.
The only intervention was historical threshold selection. Models, calibrators,
evaluation scores, H5 and the original Meta/Tolima cohorts remained fixed.
Mauricio's [revision 2 approval](AUTHORIZATION.md) admitted the previously recovered
selection scores; the source-admission blocker was resolved before execution.

`NO_EVALUABLE` means no admissible P1 threshold exists for two mandatory cells:
T+1/2022 and T+2/2024. Under the frozen full-cohort rule, neither complete P1
horizon can be evaluated. This is a policy-feasibility finding, not an implementation
failure or missing source. Unavailable alerts remain unavailable, rather than zero;
partial years cannot replace either primary comparison. The primary hypothesis is
neither supported nor formally rejected. This bounded experiment is scientifically
closed with reproducible evidence; integration and merge approval remain separate.

## Main results

The quantitative owner is [RESULTS.md](RESULTS.md); it takes precedence over earlier
interpretations. The complete P0 baselines are:

| Horizon | Detected / observed onsets | Sensitivity | Excess FAR | Academic result | Complete P1 comparison |
| --- | --- | --- | --- | --- | --- |
| T+1 | 146/313 | 46.65% | 55.08% | Fails C | `NO_EVALUABLE` |
| T+2 | 62/219 | 28.31% | 58.30% | Meets A/B/C in aggregate | `NO_EVALUABLE` |

P0 T+1 exceeds CHANNEL FAR by 7.5909 percentage points; P0 T+2 exceeds it by
2.9562 points, within the allowed five-point margin. Aggregate T+2 compliance
does not establish stability across years or departments. Annual P1 findings
below are local comparisons, not complete pooled P1 results.

## Five critical findings

### H1 — Selection infeasibility under the defined policy class

For T+1/2022, the minimum development FAR with a detection is **60%**, above the
**59.5454545%** ceiling. None of 510 unique score thresholds is feasible.
For T+2/2024, the corresponding minimum is **33.33%**, above **30.49%**;
none of 259 thresholds is feasible. Both cells have the required outcome classes
and defined CHANNEL FAR: the problem is not insufficient support. No-alert has
undefined FAR and is not an admissible fallback.

This establishes infeasibility for the approved scalar-threshold policy, whole-tie
rules and frozen scores. It does not prove that every alternative policy would fail.
No margin relaxation, cohort reduction or evaluation-based fallback is justified
within this experiment.

### H2 — T+1 false-alert reductions sacrifice detections

In the three evaluable T+1 cells, P1 loses **19 detections in 2020**, **two in 2021**
and **28 in 2024**. False excess alerts fall by 30, eight and 28, respectively.
The lower false-alert burden therefore does not preserve onset detection and does
not, by itself, justify adoption. No partial-year total substitutes for the missing
2022 policy or establishes a complete-horizon improvement.

### H3 — Local T+2 gains carry additional alert burden

In 2021, P1 gains **15 detections**, adds **46 false excess alerts** and **47 false
onset alerts**, and meets A/B/C where P0 did not. In 2022 it gains **six detections**
(17 to 23 of 62), adding **12 false excess alerts** and **14 false onset alerts**.
Its FAR falls from 63.51% to 62.77%, but remains 12.77 percentage points above
CHANNEL's 50%, so C still fails. T+2/2020 is unchanged. These gains do not recover
the missing T+2/2024 policy or establish general superiority.

### H4 — Historical margin compliance does not ensure temporal transport

All six available P1 policies satisfy their development FAR constraint. **Three
fail C in evaluation:** T+1/2021, T+2/2020 and T+2/2022. Selection on historical
data therefore does not guarantee transport of the academic margin. The margin
is an additive five percentage points against CHANNEL, not a relative 5% increase.
A lower absolute FAR can still fail when CHANNEL FAR also falls, as in T+2/2022.
These observations do not identify the cause of the temporal variation.

### H5 — Territorial responses differ

In T+2/2022, **Meta gains three detections**; its FAR falls from 50.00% to 44.12%
and all three conditions are met. **Tolima also gains three detections**, but FAR
rises from 71.74% to 73.33% and C remains unmet. This is heterogeneous behavior,
not evidence of territorial stability. It cannot be extrapolated to every
municipality, other years or nationwide performance. Complete department-pooled
P1 comparisons remain non-evaluable because the mandatory cells are unavailable.

## Five lessons for SAT-Dengue decisions

1. **Probabilities and alert policies are distinct components.** The same scores
   produce different detection/load trade-offs under different thresholds, while
   AP/Brier remain unchanged. SAT-Dengue should evaluate probability quality and
   decision-policy compliance separately; threshold changes are not new predictors.
2. **A policy optimized for another budget need not meet the academic contract.**
   BETA's onset false-alert load budget differs from the CHANNEL excess-FAR margin.
   Future authorized work must state its event, denominator, comparator and budget
   before selection; compliance under one objective cannot stand in for the other.
3. **Lower FAR can cost relevant onsets.** T+1's paired losses make that cost
   explicit. Adoption decisions must retain gained/lost detections and absolute
   false-alert counts alongside FAR, rather than accept a favorable ratio alone.
4. **The margin against CHANNEL can deteriorate over time.** Development feasibility
   is a prerequisite, not evidence of future compliance. SAT-Dengue must retain
   separate development/evaluation audits and cannot tune thresholds on a failed
   evaluation period while presenting it as independent validation.
5. **Aggregation can hide territorial differences.** Meta and Tolima respond
   differently even when their detection gains match. Future decisions must retain
   year/department controls and the original eligible populations; pooled compliance
   cannot authorize municipal or territorial extrapolation.

## Implications for future research

- **What is unsupported or ruled out within this scope?** General adoption of this
  P1 is unsupported, as is assuming an admissible threshold exists in every required
  cell. Reducing false alerts alone is not a demonstrated general improvement.
  These findings do not rule out every policy family or establish that G0_OFF is
  irreparable; the primary hypothesis remains `NO_EVALUABLE`.
- **What evidence is retained?** The frozen P0 reference, original model/calibrator
  identities, all 4,386 recovered selection scores, 5,075 evaluation observations,
  chronological memberships, exhaustive candidate frontiers, frozen thresholds,
  paired decisions and temporal/territorial audits remain available. Existing
  reproduction evidence and the benchmark provide the traceable starting point;
  they are not new independent replications each time they are consulted.
- **What questions remain open?** Whether an independently authorized policy could
  be feasible and preserve useful detection; whether any gain would transport to
  independent periods and territories; and what roles predictor quality, calibration,
  cohort composition, data availability or H5 validity play in observed errors.
  These are untested questions, not established explanations or selected techniques.
- **What should not be reopened without justification?** Do not repeat the same
  benchmark, score recovery, frozen model fits, calibration or cohort/H5 construction
  merely to obtain a favorable closure. Reopening a component requires a concrete
  unresolved scientific question, explicit authorization and appropriate validation.
  Preserve failed cells; do not retrospectively relax their margin or support rules.

No successor experiment or new technique is selected here. Any later experiment
requires an independent human authorization and a protocol defined before results.

## Limitations that remain after closure

- Results are retrospective on previously used 2020/2021/2022/2024 observations.
  There is no independent temporal confirmation; 2024 is consumed stress and 2025
  is excluded, not a fresh reserve. Statistical superiority is not established.
- Consolidated data do not demonstrate historical operational availability at the
  forecast origin, prospective performance or sanitary effectiveness.
- H5 remains an experimental epidemiological definition, without external validation
  as an outbreak identity. Conclusions apply to the original eligible cohorts.
- Selection scores were recovered by inference with frozen original models and
  calibrators. No original selection arrays or digest are available for direct historical
  comparison. Exact evaluation replay establishes consistency with those artifacts,
  not independent authentication of absent historical arrays.
- There is insufficient evidence to attribute the underlying problems causally to
  the predictor, calibration or policy. This comparison identifies decision changes
  on fixed scores, not a unique cause of project-wide errors or temporal variation.
- Excess FAR is false excess alerts divided by emitted alerts; it is different from
  the count of false onset alerts. Continuation alerts can be correct for excess
  while false for onset, particularly at T+2. Neither quantity substitutes for the
  other; FAR is undefined when no alert is emitted.

## Traceability and preserved scientific identities

Standing references are the [academic contract](../contrato.md),
[initial protocol](protocol.json), [authorized revision 2](protocol.revision-2.json),
[authorization](AUTHORIZATION.md), [score recovery evidence](SCORE_RECOVERY.md),
[DELTA results](RESULTS.md), [academic benchmark conclusions](../benchmark/CONCLUSIONS.md)
and its [diagnosis](../benchmark/diagnostico/ANALYSIS.md). The benchmark diagnosis
motivated the threshold comparison; DELTA results resolve that bounded question
without turning earlier hypotheses about causes into established findings.

The artifact identities below are copied unchanged from `RESULTS.md`:

- Results: `data/processed/exp_delta01/d5c482b64e0d44e5012b20d24baa73d14f829ca4857bb2e2e53870ab3a82a284`.
  Manifest SHA-256: `a6f67b769cc52365da097ffa1b2709452252f0b7e9a5e6a6644c70a7f1cb0a92`.
- Selection freeze: `data/processed/exp_delta01/selection_freezes/e99f60fed004de212b4310d1114ad60e51b097a48ea7e251d2fbc41b8935d2b0`.
  Manifest SHA-256: `592a166956fdf536ea247eae6d99f3d01e6674ea8b030f2ef91ab34e7b6ddbad`.
- Recovered selection: `data/processed/exp_delta01/recovered_selection/b2e8256c9c37f8ecdb5f895ccd6d936cfb11f3896adc654ecab3c386bf57acc1`.

This closure changes no numeric result, protocol, prediction or scientific artifact.
See [README.md](README.md) for the recorded execution and reproduction procedure.
