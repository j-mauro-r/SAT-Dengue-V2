# EXP03 — Information value for exact-onset prediction

**Scope revision implemented; generated-data validation passed; scientific execution not authorized.**

[alcance.md](alcance.md) is the authoritative specification for the expansion
requested after review of EXP00 and EXP01. It defines the questions, finite variant
matrix, temporal roles, alert policy, diagnostics, result contract and acceptance
checks. Implement from that specification rather than from individual chat excerpts.

## Scientific objective

Determine the incremental value of lagged history, current epidemiological state,
historical target-month thresholds, channel context, notification observed/expected
ratios and climate for exact-onset prediction at T+1/T+2. Evaluate detection jointly
with false-alert burden, temporal/territorial stability, calibration and coverage.

The main risk set remains known Y(T)=0. Removing current predictors does not remove
this eligibility dependency. A T-only variable can provide useful early warning;
event-time lags alone do not prove historical publication availability or causality.

## Bounded work packages

| Package | Revised requirement | Scope boundary |
| --- | --- | --- |
| Primary ablation | 16 unique sets; four primary and 12 secondary contrasts; three fixed families; T+1/T+2; four historical cuts | 384 onset fits, no hyperparameter search |
| Target control | Base and full excess controls at T+2, paired with onset | 24 additional fits; no duplicate T+1 task |
| Diagnostic evaluation | Historical profiles, micro/macro results, error types, coverage, calibration and paired development uncertainty | Reuse fitted predictions; no territorial models |
| Availability sensitivity | One-month stale-input diagnostic on two specified variants, with explicit eligibility limitation | Zero additional fits; no claim of real-time validity |
| Consumed 2025 benchmark | All 102 terminal model cells frozen before 2024/2025 outputs, separate inference-only path | Zero refits, recalibrations or threshold selections |
| Scientific delivery | Protected native predictions, thresholds, contrasts, group/coverage/transport tables and decision-oriented conclusions | Aggregate-only MLflow projections under existing policy |

The revised planned maximum is **408 fits**. Every new fit must map to a declared
variant/objective/family/horizon/cut. Contrasts and aliases reuse fitted cells.
The primary false-alert budget is fixed at 1.0 before execution by human decision.
Its experimental comparison meaning, frozen exposure formula and D=38 example
are defined in [the budget policy](alcance.md#one-budget-explicit-exposure).

Development uses rolling 2020, 2021 and 2022 OOF cuts with earlier calibration and
selection roles. These overlap in training and are not independent replications.
2024 remains separate retrospective stress. 2025 remains excluded from development
and is available only for the consumed benchmark after immutable terminal artifacts
are frozen. Neither year supplies blind or prospective confirmation.

Continuous model/threshold adaptation, models per profile, a full availability
study and new label-definition selection are outside this expansion. EXP02 owns
label sensitivity. Five-year labels remain the conditional reference here.

## Historical implementation and migration boundary

The implementation reviewed at `52e13a4af73add8acd1c87b42d413e0e967235d3` has ten
unique sets, eleven contrasts and 240 cells. Its
[original design](https://github.com/j-mauro-r/SAT-Dengue-V2/blob/52e13a4af73add8acd1c87b42d413e0e967235d3/docs/product/experiments/EXP03_feature_ablation/DESIGN.md)
remains inspectable in Git. The historical protocol and matrix remain inspectable at that reviewed Git revision;
their legacy canonical protocol hash is
`c2f445e767b36dfac5acebca865775d793a93c2a75dc05d829bce82257b57396`.

The current [protocol](protocol.json) and [matrix](ablation-matrix.frozen.yml)
encode the expanded revision. [Implementation traceability](IMPLEMENTATION.md)
maps every scope section to components, tests and native outputs. Legacy ten-set
aliases and approvals cannot execute the revision. Generated validation is
engineering evidence only; scientific execution, G5 and merge require their
separate authority.

## Primary-budget decision — 2026-10-27

Mauricio approved the following rationale before any EXP03 execution:

> A primary budget of 1.0 false onset alert per monitored municipality-year is fixed
> to provide a common, interpretable and reproducible criterion for comparing variants.
> The value is conservative and is established before executing EXP03. It does not
> represent validated operational capacity, clinical equivalence or a deployment threshold.

Protocol [2.0.0](protocol.v2.0.0.json) is immutable historical blocker evidence
(canonical SHA-256 `f806f3897a8dbef2bea01333626ee943e45aec9892f91607ca899f003e55beaf`).
Current [2.0.1](protocol.json) fixes only the approved budget decision and provenance
(canonical SHA-256 `18ce612581d710245294f3966187178e697df1972d45b460f54be7cc2f4d1611`).
Its registry and matrix use that new identity. Historical null/pending fields in
2.0.0 intentionally remain evidence, not active instructions. Schema remains v1;
the patch preserves the matrix, contrasts, exposure and temporal contracts.
The frozen selection limit is `floor(B_primary × D)`; 76 municipalities over six
covered months give `D=38` municipality-years and a limit of 38 false onset alerts.
No retrospective budget optimization or automatic model/champion selection is allowed.
G5 remains `NOT_APPROVED`; champion remains `not_selected`.

PLAN_045 versions this decision separately because PLAN_044 covers operational
preparation only. Its original failed readiness gate is preserved. After merge,
restart operational preparation on the new commit: wheel, runtime, preflight,
independent review, separate authorization, then deliver the manual command to
Mauricio. No existing approval or runtime identity may be reused.
