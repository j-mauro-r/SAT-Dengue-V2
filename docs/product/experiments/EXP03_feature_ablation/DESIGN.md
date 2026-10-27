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
The numeric primary false-alert budget remains a pre-execution decision; it is
not inferred from an assumed health-service capacity or favorable evaluation points.

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
