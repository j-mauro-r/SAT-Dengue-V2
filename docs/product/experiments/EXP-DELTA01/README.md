# EXP-DELTA01 — constrained academic alert policy

**Status: `BLOCKED` at source admission, before implementation or scientific execution.**
This is a prerequisite report and a frozen design, not a completed Kedro experiment.
G5 remains `NOT_APPROVED`; `champion: not_selected`.

## Objective and authority

Compare exactly P0 (original BETA policy) and P1 (academic FAR-constrained policy)
using the same frozen regional G0_OFF probabilities, H5 outcomes and evaluation
observations. The only proposed intervention is threshold selection. The
[approved contract](../contrato.md) is authoritative; [protocol.json](protocol.json)
records the design before any DELTA metrics or policy selection.

The branch `experiment/EXP-DELTA01` starts at updated `origin/main`, commit
`447ef9fd85303de61848d2b01733d25c8ad8a935`, which integrates the academic benchmark
through PR #72. The contract and benchmark are present in that commit. No historical
experiment, predictor, source table, pipeline, hook or governance disposition is changed.

## Essential missing evidence

Section 6 of the authorized request requires verification of available out-of-sample
selection probabilities, including calibrator separation, **before implementation**.
It explicitly requires stopping scientific evaluation if those probabilities are
not persisted or verifiable. This essential admission condition is unmet:

- The original [BETA engine](../../../../src/sat_dengue/experiments/exp_beta01_engine.py)
  computes `raw_scores` for calibration, adaptation, selection and evaluation in
  `train()`. Its `predict()` uses calibrated selection scores in memory, but adds
  only **evaluation** rows to `predictions`. `evaluate()` persists those evaluation
  predictions, aggregate policies and model/cell metadata; it does not serialize
  per-observation selection probabilities or labels.
- [Role construction](../../../../src/sat_dengue/experiments/exp_beta01.py) establishes
  the intended separation: train through Y−4, calibrate in Y−3, select in Y−1,
  evaluate in Y, with the original origin embargo. The code supports the intended
  chronology but cannot authenticate absent probability files or their membership.
- [V2 publication](../../../../src/sat_dengue/datasets/exp_beta01_v2.py) does persist
  `scores-h*-*-selection.csv`. Those files are produced from **G1** cells, not G0.
  V2 copies frozen G0 **evaluation** predictions as references. It cannot substitute
  for the missing G0_OFF selection probabilities.
- The [benchmark diagnosis](../benchmark/diagnostico/ANALYSIS.md) already states
  that selection excess-FAR cannot be recovered from aggregate policy records;
  full earlier G0 selection-score availability was not established. Its suggested
  recovery through frozen-model inference requires separate authorization. The
  present request requires persisted verifiable scores; no recovery is executed here.
- None of the four private source folders pinned in the benchmark protocol, or the
  published benchmark folder, exists in this Cloud checkout. Consequently their
  manifests, real row membership and labels cannot be checked here. The original
  publisher's omission is established by code inspection; absence of an independent
  export elsewhere is **not** established.

Expected evaluation sizes (2,653/313 and 2,422/219 rows/onsets) are verified against
the committed benchmark protocol and reports only. They have **not** been verified
against private rows in this session. No cohort intersection or generated substitute
can discharge that requirement.

## Required local evidence and resumption

1. Supply the explicitly pinned original G0, canonical and benchmark bundles listed
   in `protocol.json`. Verify manifest identity, file membership and every payload
   hash without changing those publications.
2. Identify an **already persisted** G0_OFF selection export for all eight
   horizon/year cells. Supply its path, manifest hash, complete ordered keys,
   target months, onset labels and calibrated probabilities. Bind each cell to its
   original G0 model bytes, saved global intercept, calibration role and selection
   role; verify that the predictor and calibrator did not fit selection observations.
   Include immutable lineage sufficient to verify these claims rather than a
   self-declared out-of-sample flag. An export containing raw scores must also bind
   the original calibrated scores; this delivery does not regenerate probabilities.
3. Verify complete selection membership against `role_parts()` on the pinned common
   BETA cohort, including the original embargo and separation from calibration and
   evaluation. Check exact evaluation keys, labels, scores and P0 alerts against the
   pinned benchmark. Reconstruct CHANNEL with the existing origin-only H5 functions.
4. If that export exists and passes admission, bind its reviewed identity in a
   protocol revision **before** implementing/executing results. If it does not exist,
   retain `BLOCKED` and record the separate missing recovery requirement. Do not
   rerun training, calibration or inference as a workaround under this protocol.
5. After admission, implement the requested independent four-responsibility Kedro
   graph `exp_delta01`, reusing compatible benchmark readers, metrics and atomic
   publication. Perform focused technical validation, then the chronological real
   comparison and byte-identical reproduction on the pinned private inputs.

There is **no executable `exp_delta01` command yet**. Running BETA or V2 would train
models and cannot complete this handoff. `READY_FOR_LOCAL_EXECUTION` would be
incorrect: the essential score provenance is unresolved and the implementation
has deliberately not started. No additional experimental infrastructure is created.

## Evidence and validation

The blocked [results](RESULTS.md) and [conclusions](CONCLUSIONS.md) contain no new
scientific measurements. The [benchmark](../benchmark/README.md), its
[conclusions](../benchmark/CONCLUSIONS.md), [hypotheses](../benchmark/diagnostico/HYPOTHESES.md),
[BETA01 protocol](../EXP-BETA01/protocol.phase2.json),
[BETA01 conclusions](../EXP-BETA01/CONCLUSIONS.md) and
[analysis 7](../analisis-7.md) were reviewed as evidence, not modified.

PASS: JSON parsing, authority/protocol SHA-256 checks, agreement with committed
benchmark source pins and expected counts, missing-folder checks, Markdown links,
repository-only DWP conformance (17 checks), and changed-file secret/privacy checks.
The complete new-file diff is checked before commit. Ruff, formatting, mypy and runtime tests have no changed Python
surface to validate. Real source verification, scientific execution, independent
review and remote CI are not established by these documentation checks. No new DWP
implementation plan is opened while the essential admission condition is blocked.

Initial all-plan conformance on the supplied checkout passed (159 checks, 19
advisories); it is separate from the updated-main repository-only gate. Historical
plan records and their earlier reported dispositions are preserved.
