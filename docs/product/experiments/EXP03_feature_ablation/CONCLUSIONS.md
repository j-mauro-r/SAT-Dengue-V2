# EXP03 conclusions — scope revised, results pending

## Evidence status

- Scope specification: defined in [alcance.md](alcance.md).
- Revised implementation and generated-data validation: **PENDING**.
- Revised protocol hash and independent implementation review: **PENDING**.
- Numeric primary alert budget: **PENDING**, required before scientific execution.
- Scientific execution and results for this scope: **PENDING**.
- Hypothesis outcome: **NOT_EVALUATED**.
- G5: `NOT_APPROVED`. Champion: `not_selected`.

The scope update is based on public code and the consolidated EXP00/EXP01
conclusions cited in alcance.md. It does not train models, recalibrate, inspect
private scientific rows, create scientific approvals or write permanent MLflow.
The old implementation's reported 94 passing generated-data tests and zero real
fits describe that engineering delivery, not this expanded experiment.

## Questions the eventual results must answer

1. Does adding current state improve onset detection beyond lagged history, and
   does removing it from the full model change that conclusion?
2. Do lagged climate and target-month historical thresholds contribute at the
   fixed selection-budget policy? What is the realized false-alert trade-off?
3. Are effects consistent across development years, horizons, Meta/Tolima and
   historical transmission profiles, with adequate support and uncertainty?
4. Do T+2 excess controls primarily alert on continuations, and how does their
   common-onset utility compare with direct-onset training?
5. What coverage and performance change under the prespecified stale-input
   diagnostic, and what remains unknowable about actual availability?
6. How do the same frozen terminal artifacts behave in 2024 and consumed 2025?

## Required conclusion format after an authorized run

Every claim must identify its contrast/cell, counts and denominators, exposure,
fixed budget/threshold, paired detection and realized-burden differences,
uncertainty/support, affected years/territories, and native artifact locator.
Lead with a compact decision table, followed by:

- **Confirmed findings:** directly supported recorded comparisons.
- **Interpretations:** plausible explanations, separated from causal claims.
- **Limitations:** unknown availability, sparse groups, correlated/multiple
  comparisons, complete-case selection and conditional three-year uncertainty.
- **Hypotheses:** bounded follow-up questions that require another version/run.

Allowed dispositions include consistent retrospective contribution, conditional
benefit, additional detection at additional burden, current-state dependence,
candidate simplification, and inconclusive. Do not infer equivalence from a
non-significant contrast or operational capacity from a selected threshold.
A negative or inconclusive result can still answer the thesis question well.

Keep development 2020-2022, stress 2024 and consumed benchmark 2025 distinct.
The 2024-2025 aggregate is descriptive context only. Unknown labels and undefined
metrics remain unavailable. Single-horizon event counts cannot be summed across
T+1/T+2 as independent episodes. All results remain conditional on the current
five-year label definition until a versioned replication follows EXP02.

## Historical identity

The unchanged [legacy protocol](protocol.json) has SHA-256
`c2f445e767b36dfac5acebca865775d793a93c2a75dc05d829bce82257b57396`.
Its ten sets / eleven contrasts / 240 cells are superseded as the implementation
target by the scope revision's sixteen sets / sixteen ablation contrasts /
408 maximum fits (including two T+2 objective controls). These are planned
counts, not execution results. See [DESIGN.md](DESIGN.md) for the migration boundary.
