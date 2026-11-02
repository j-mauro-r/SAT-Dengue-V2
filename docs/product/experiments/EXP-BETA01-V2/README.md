# EXP-BETA01 V2 — National G1 Without Climate

This bounded experiment asks whether adding eligible national training
observations improves direct H5 onset detection in the same Meta/Tolima
evaluation cohorts as BETA V1. The [protocol](protocol.json) is frozen in Git
before any real fit; [results](RESULTS.md) and [conclusions](CONCLUSIONS.md) are
updated only from the new real publication.

## Inputs and comparability

- [Original design](../EXP-BETA/DESING.md),
  [V1 protocol](../EXP-BETA01/protocol.phase2.json) and
  [V1 results](../EXP-BETA/RESULTS.md) remain unchanged.
- [National table](../../../data/canonical-national-table.md) bundle
  `c2267f61c7624f19ea7056c2d891512b12e85d81214145df1d31815d28fc3c29`;
  national manifest SHA-256
  `e801cf9b36b84ff0e0c8f336a88799d47f6e6bce9a6d1b155a1a37e20594afb4`.
- Frozen G0 OFF and R0 predictions come from V1 bundle
  `37a0cae62f4d3fa59cede281e032c9abd1b568a90933855b9eebd3b3d3fb5f4a`;
  the native R0 source must also be present and hash-verified.

All regional role keys, the 24 no-climate predictors and onset truths match V1
exactly. G0_MATCHED is therefore unnecessary: no regional control is refitted.
Training alone admits additional national rows. Calibration, threshold selection
and evaluation retain the frozen regional cohorts and original rules. The
adaptation-year role remains reserved but unused; no L1 adjustment is fitted.

The same fixed XGBoost parameters, calendar embargo, H5 definition, ≤1 false
alert per observed eligible municipality-year and descriptive −2 pp margin
against R0 apply. No evaluation result can choose a feature, hyperparameter or
policy rule. Positive predictor selection excludes the nine climate variables,
future targets and quality/geography metadata. Full input identity, cohort or
regional support mismatches stop fitting rather than substituting intersections.

## No-fit preflight, before protocol freeze

| Horizon | Evaluation year | Training rows | Regional rows | Additional rows | Total / additional territories | Additional origin months |
|---|---:|---:|---:|---:|---:|---:|
| T+1 | 2020 | 8,394 | 3,155 | 5,239 | 1,093 / 1,017 | 6 |
| T+1 | 2021 | 20,967 | 3,938 | 17,029 | 1,121 / 1,045 | 18 |
| T+1 | 2022 | 33,281 | 4,691 | 28,590 | 1,122 / 1,046 | 30 |
| T+1 | 2024 | 53,217 | 5,728 | 47,489 | 1,122 / 1,046 | 54 |
| T+2 | 2020 | 7,400 | 3,089 | 4,311 | 1,083 / 1,007 | 5 |
| T+2 | 2021 | 19,907 | 3,871 | 16,036 | 1,121 / 1,045 | 17 |
| T+2 | 2022 | 32,317 | 4,638 | 27,679 | 1,122 / 1,046 | 29 |
| T+2 | 2024 | 52,231 | 5,655 | 46,576 | 1,122 / 1,046 | 53 |

Every cell has two training/calibration classes and admissible nonregional
training observations. Additional history starts in 2016-06. For 2020 it ends in
2016-11 (T+1) or 2016-10 (T+2): seasonally incomplete support is a predeclared
limitation, not a reason to move the original dates. The comparison identifies
the effect of adding the available national observations; it cannot disentangle
geography, sample size, season and recency as separate causal mechanisms.

## Execution and replay

```bash
KEDRO_DISABLE_TELEMETRY=1 .venv/bin/kedro run \
  --pipeline=exp_beta01_v2 --params=profile=exp_beta01_v2,tracking=disabled
```

Five independent nodes prepare, fit G1, calibrate/select, predict and evaluate.
The publisher uses existing atomic no-overwrite controls under
`data/processed/exp_beta01_v2/<bundle_id>/`. Payloads contain native UBJ models,
all three arms' predictions, annual/department/pooled metrics, paired contrasts,
selection policies, raw held-out scores, support, protocol and provenance.
Repeated real execution is not the reproduction procedure: `reproduce` reloads
the identified native models and saved calibration offsets, reconstructs scores,
policies, predictions and metrics, and performs zero fits.

Serialized Arrow boolean masks are interpreted through an explicit strict
True/False adapter in this new reader. Published data and historical readers are
unchanged. Default, replay, V1, Stage 2/3, historical hooks and tracking remain
outside the new route.

## Validation and inherited limits

The focused V2/canonical/BETA/configuration/bootstrap test suite, scoped
Ruff/format/mypy and real no-fit preflight own this delivery's technical gates.
The strict directory inventory now records both the inherited national pipeline
and the new V2 directories; its test is unchanged.

The merged PR #70 had a separate inherited CI failure: the general data-domain
test rejects filesystem imports in `data/national_diagnostics.py`, introduced
before V2. It is not repaired by weakening that test or refactoring historical
diagnostics in this experiment. A local full private-preservation inventory also
expects older `traking-concluciones.md` bytes although current main already
contains later authorized documentation; its baseline is not altered. These
remain explicit integration/preservation limits, not evidence that V2's pinned
scientific input bundles changed. Relevant source/model/prediction hashes are
verified independently before and after execution.

2024 is reused retrospective stress; 2025 is forbidden. No statistical
superiority, G5 approval, champion selection, L1 national, NB2 national or later
policy experiment follows automatically. Merge requires personal review and
resolution or explicit disposition of relevant CI findings.
