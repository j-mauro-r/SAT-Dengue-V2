# EXP-BETA — integral scientific closure

**Status: COMPLETED_WITH_LIMITATIONS** for the approved bounded retrospective
program, locally executed and verified on 2026-11-02. The four mandatory phases
are implemented and scientifically checked; conditional exclusions and unresolved
scientific questions remain explicit. This does not approve merge, deployment,
G5 or a champion. Mauricio personally reviews PR #67; no merge was performed.

## Objective and valid comparisons

[DESING.md](DESING.md) asks whether pooled learning, count distributions and
false-alert-aware decisions improve onset sensitivity while controlling load in
Meta/Tolima. Its original pending-implementation notes are historical design
metadata; explicit subsequent human instructions authorized these four phases.

The canonical table preserves climate and legacy source semantics. EXP-BETA01
tests pooled G0 and regularized department adaptation L1, with/without climate.
EXP-BETA02 tests one fixed pooled NB2 count family, with/without climate.
EXP-BETA03 tests a constrained global decision policy and a development-supported
regularized department policy on frozen R0 scores. Each experiment owns its
protocol, graph, publication and conclusions; no historical output was rewritten.

Primary comparisons use unchanged R0 and identical H5 onset labels, municipalities,
origins/targets and eligible exposure. The paired evaluation cohorts contain
2,653 T1 rows/313 onsets and 2,422 T2 rows/219 onsets over 2020/2021/2022/2024.
Climate ON/OFF share keys and truth. R0 already pools the 76 municipalities:
G0 is not evidence of national transfer. Beta01/02 fitting/calibration roles differ
from R0, so those comparisons concern full procedures; they do not isolate a
causal effect of one model component. Beta03 isolates threshold changes on the
same probabilities. Never compare metrics from different cohorts as equivalent.

All decisions retain <=1 false alert per eligible municipality-year and a
-2 percentage-point **descriptive** sensitivity margin against R0, with annual
and department controls. R0's original broader monitored-exposure selection
contract remains intact; new paired rates use the common eligible denominator.

## Findings

| Fixed procedure | Horizon | Detected / onsets | False alerts | FA / eligible municipality-year | Sensitivity difference vs R0 |
|---|---|---:|---:|---:|---:|
| R0 | T1 | 142 / 313 | 231 | 1.044855 | reference |
| Beta01 G0, climate OFF | T1 | 146 / 313 | 179 | 0.809649 | +1.28 pp |
| Beta01 G0, climate ON | T1 | 152 / 313 | 204 | 0.922729 | +3.19 pp |
| Beta01 L1, climate OFF | T1 | 138 / 313 | 175 | 0.791557 | -1.28 pp |
| Beta01 L1, climate ON | T1 | 152 / 313 | 210 | 0.949868 | +3.19 pp |
| Beta02 NB2, climate OFF | T1 | 135 / 313 | 212 | 0.958914 | -2.24 pp |
| Beta02 NB2, climate ON | T1 | 152 / 313 | 222 | **1.004146** | +3.19 pp |
| Beta03 GLOBAL | T1 | 96 / 313 | 136 | 0.615153 | -14.70 pp |
| R0 | T2 | 86 / 219 | 256 | 1.268373 | reference |
| Beta03 GLOBAL | T2 | 57 / 219 | 175 | 0.867052 | -13.24 pp |

Positive findings are limited: some Beta01 T1 pooled procedures improve observed
detection and load together, and NB2 supplies reproducible count distributions.
They do not establish a stable accepted improvement. Beta01 L1 fails joint controls
in **43/48** horizon/year/department/climate strata; its local-adaptation hypothesis
is **NO_RESPALDADA**. All new Beta01 T2 sensitivities lose 8.68-10.96 pp versus R0.
National/global-transfer evidence remains **NO_EVALUABLE**, not negative.

The fixed NB2 onset approach is **NO_RESPALDADA**: climate OFF loses 2.24 pp at T1;
ON exceeds the pooled budget, even though rounding to 1.00 would hide the failure.
It fails **19/24** T1 year/department/climate strata jointly. Count MAE/RMSE and
predictive coverage are secondary; 97.3-97.8% coverage of nominal 90% intervals
with wide widths is not proof of useful sharpness. No R0 count distribution exists
for a direct count-error comparison. NB2 T2 marginal excess is available, but
onset is **NO_EVALUABLE** because no valid joint transition distribution was fitted.
No independence assumption or observed future state was substituted.

Beta03 reduces pooled false alerts by 95 at T1 and 81 at T2, at the cost of 46
and 29 additional missed onsets. Only **8/24** GLOBAL strata jointly pass; its
policy hypothesis is **NO_RESPALDADA**. Development-supported department adjustment
was evaluated only for both 2020 horizons; **0/6** matched strata jointly pass.
Brier/AP remain unchanged because thresholding does not change probabilities.

Temporal and territorial failures prevent pooled compliance from selecting a
champion. In Beta03 the 2021/2022 global decisions equal R0; 2020 and consumed
2024 stress lose substantial sensitivity. Despite its pooled budget, GLOBAL
exceeds 1 FA/year in Meta T1/2022, Tolima T1/2024 and both departments T2/2022.
The per-experiment aggregate tables retain every evaluated year/territory;
partial department totals must never be compared to full-program totals.

## Design compliance matrix

| Phase | Component | State | Real evidence | Limitations |
|---|---|---|---|---|
| 1 | Canonical Model Table / independent Kedro route | IMPLEMENTADO_Y_VALIDADO | Pinned 17,936 x 70 table; 76 municipalities; CSV, contract, columns and coverage reproduced byte for byte from identified Stage 2 | Consolidated notifications; 608 climate-missing municipality-months; no national source |
| 2 | G0/L1 and climate ON/OFF vs R0 | IMPLEMENTADO_Y_VALIDADO | [Beta01 results](RESULTS.md); 16 unique saved models, 20,300 scores replayed and 120 strata reconciled again | Same geographic pooling as R0; local gain not supported jointly |
| 2 | National transfer / transmission profiles | NO_EVALUABLE | Only Meta 29 and Tolima 47 municipalities; no validated time-safe profile | Cannot test national-transfer or profile hypotheses |
| 3 | Parsimonious NB2 and H5 risk vs R0 | IMPLEMENTADO_Y_VALIDADO | [Beta02 results](../EXP-BETA02/RESULTS.md); 16 unique models; 10,150 native forecasts; 48 count and 84 onset strata reconciled again | Fixed marginal family; T1 joint decision rejected |
| 3 | Joint NB2 T2 onset | NO_EVALUABLE | Marginal T2 forecasts retained separately from missing onset | A joint trajectory is not identified; explicit allowed limitation, not a fabricated negative |
| 3 | DeepAR/GRU | CONDICIONAL_NO_JUSTIFICADO | No independently demonstrated sequence-remediable limitation or additional unconsumed evaluation support | Four reused temporal blocks do not warrant escalation; no conclusion against all neural methods |
| 4 | Global constrained frozen-score policy | IMPLEMENTADO_Y_VALIDADO | [Beta03 results](../EXP-BETA03/RESULTS.md); real four-node graph, 30 paired contrasts, nine byte-identical reproduced files | Negative joint result; future load can exceed development cap |
| 4 | Regularized department rule | IMPLEMENTADO_Y_VALIDADO / NO_EVALUABLE | Triggered on development only for 2020 T1/T2; six paired strata; global fallback elsewhere | Other cuts lack predeclared heterogeneity/support; profiles unavailable |
| 4 | Additional FP-aware learning | CONDICIONAL_NO_JUSTIFICADO | Zero development false positives >=0.8 in eight cells; only one independent policy block per frozen predictor | No hard-negative/asymmetric refit; no second classifier or DRL |
| All | Independent confirmation / statistical noninferiority | NO_EVALUABLE | 2024 explicitly consumed stress; no 2025 claim | Statistical uncertainty UNAVAILABLE; no superiority |

## Reproduction and preservation

Canonical bundle ID:
`ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98`.
The individual result owners record full protocol hashes, source identities,
native publication IDs, execution commits, commands and aggregate reports:
[Beta01](PHASE2_IMPLEMENTATION.md), [Beta02](../EXP-BETA02/README.md),
[Beta03](../EXP-BETA03/README.md).

Real execution, zero-fit native rechecks and deterministic reproduction are
distinct evidence. Beta01 performed 64 actual historical fits across its documented
execution/reproduction/correction sequence, with 16 unique model identities per
publication; Beta02 performed 32 including reproduction, with 16 unique models;
Beta03 performed zero. This closure did not repeat earlier fits or alter old
protocols, manifests, data, results, models, replay/default or Stage 2/3.

The final preservation check validates all 437 original inventoried files with
their hashes/sizes/modes plus all 27 Beta02 payloads. Native R0 replay checks 96
parent cells; exact canonical labels and frozen R0 scores pair in all eight
Beta03 cuts. All nine Beta03 files reproduce identically, and overwrite is rejected.
The focused technical batch passes 70 tests; CI #67 owns full public validation.
Private data are intentionally absent from GitHub; code checkout alone cannot
reproduce these scientific metrics without the exact authorized inputs.

The separately supplied legacy private migration inventory still rejects the
decision register that changed before these experiments. That inherited mismatch
was not reset or waived; it is distinct from current source/output preservation.
Repository-only DWP conformance passes; the all-plan audit has two inherited
failures (PLAN_012 unresolved review and legacy Stage 2 lifecycle), neither silently
treated as a current code defect or waived. Human independent review remains open.

## Scientific closure and future work

The mandatory bounded comparisons are complete and reproducible, with legitimate
non-evaluable/conditional components documented. The program does **not** establish
a procedure that preserves the joint sensitivity/load criteria consistently across
time and territory. Maintain **G5 NOT_APPROVED** and **champion: not_selected**.

H5 is a frozen retrospective proxy; consolidated notifications, selected complete
cohorts and reused years limit transfer. Few independent temporal events leave
statistical noninferiority **UNAVAILABLE** and superiority **NOT_ESTABLISHED**.
No causal, clinical, prospective, operational or deployment claim follows.

Future separately authorized work should first obtain mature independent time
blocks, validated wider sources/profiles and reporting-availability evidence.
A coherent joint count trajectory or targeted learning intervention would need
its own development justification and untouched validation. The current negative
results do not authorize another model, automatic champion selection or an
unlimited sequence of experiments.
