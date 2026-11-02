# EXP-BETA01 Phase 2 — entry gate evidence

Date: 2026-11-01. Status: **BLOCKED**.
Branch: `experiment/EXP-BETA01`. Incoming revision:
`df364e5f4bd1ed8b6af59da3fd2989ee4b126a6e`.

The Phase 2 request requires validation of Phase 1 before implementation and
requires stopping when that entry gate is blocked. The engineering checks pass,
but real canonical publication, physical Meta/Tolima coverage and eligibility
cannot be validated in this Cloud workspace. These are scientific prerequisites,
so the missing evidence cannot be treated as a harmless limitation or replaced
with fixture results. No Phase 2 code or scientific execution was started.

## Authority reviewed

- [Available design, version 1.1](DESING.md), especially sections 3.4 and Phase 2.
  This is the checked-in counterpart of the requested `DESING_Beta01.md`; that
  exact filename is absent.
- [Phase 1 implementation and limitations](PHASE1.md), its
  [pinned canonical contract](canonical_model_table_v1.json), canonical table
  builder, datasets, Kedro graph and configuration validation.
- Repository agent, governance and testing rules; historical M00 runner and
  [onset definitions](../../../../src/sat_dengue/experiments/onset.py).
- `KEDRO_ARCHITECTURE_AUDIT.md` is not available in this checkout. The design and
  Phase 1 report reference it. Direct source inspection verifies the available
  architecture; this does not claim to have inspected the missing audit.

## Mandatory Phase 1 checks

| Check | Observed evidence | State |
|---|---|---|
| Independent canonical Kedro pipeline | `canonical_model_table_v1` has its own source input, parameter input and publication output; the real CLI reaches that source boundary without invoking `replay` | PASS for registration/dispatch; real completion BLOCKED |
| Strict catalog/configuration admission | Both `catalog.yml` and `config_loader.CATALOG` contain the two canonical entries; the profile rejects tracking, experiment IDs and unsupported overrides | PASS |
| Keys, contract, identity, manifest and nine climate aggregates | Existing generated tests verify unique DANE/origin keys, preserved source values, all nine climate columns/signs, content identity, no overwrite and tamper rejection | PASS for engineering; private publication/integrity BLOCKED |
| Explicit features, targets, keys, metadata and controls; no future leakage | Fixed predictor allowlist, future-perturbation invariance, exact-calendar lags/H5 and role-tamper rejection are tested | PASS for engineering |
| Execution independent of `replay` | Existing SequentialRunner fixture passes; actual standalone CLI stops at a missing native manifest before table assembly | PASS for independence; real table production BLOCKED |
| Historical routes/contracts/publications preserved | Incoming Phase 1 diff against `808cdab` adds canonical entries/profile without changing historical graph definitions; configuration/bootstrap checks pass; this task changes documentation only | PASS for static/engineering compatibility; private byte parity UNVERIFIED |
| Physical Meta/Tolima coverage and national availability documented | Phase 1 explicitly records missing real evidence; this workspace has no required native inputs or canonical publication. Actual periods, populations and eligible rows cannot be verified | BLOCKED for real coverage; national eligibility UNVERIFIED |

**Entry gate: BLOCKED.** The absence of authenticated input bytes and a real
canonical table prevents establishing the scientific population required for
G0 and paired comparisons. Passing generated tests establishes implementation
behavior, not physical coverage or scientific validity. No structural Phase 1
repair, alternative source, Kedro redesign or synthetic scientific substitute
was introduced.

## Missing execution prerequisites

The following paths were checked for existence only and are absent:

- `data/processed/panel_mensual_dengue_clima.csv`
- `data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json`
- `data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json`
- `data/processed/canonical_model_table_v1/` — no canonical publication is available.

Restore the original three source artifacts with their authorized identities;
do not regenerate them to bypass existing pins. Re-run the existing independent
Phase 1 route and validate its manifest, coverage and eligibility before
reassessing this gate:

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run \
  --pipeline=canonical_model_table_v1 \
  --params=profile=canonical_model_table_v1,tracking=disabled
```

This command was attempted here: **exit 1 / BLOCKED** with
`canonical_stage2_sources: Required canonical source is missing:`
`data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json`.
It did not produce a canonical publication or train a model. Source contents
were not read. No `replay`, `__default__`, experiment or MLflow run was executed.

## Scientific preflight findings and arm disposition

The historical `exp03_1_runner.execute_matrix` fits once per scientific cell on
all eligible training rows, without a municipality-level fitting loop. The
[historical conclusions](../EXP03.1_add_pass_info/CONCLUSIONS.md) report 76
municipalities: 29 Meta and 47 Tolima. Thus the historical implementation already
pools municipalities; this is source/document evidence, not a fresh verification
of private fitted-state membership. G0 must not be described as introducing
pooling by itself. Its value must be distinguished from representation changes,
national expansion and territorial adaptation.

The historical onset helper requires observed non-excess at T for both horizons.
For T+2 it labels the transition from non-excess at T+1 to excess at T+2; an
ongoing episode is negative. Future outcomes are separate from operational
eligibility and must never enter predictors. This task did not change that rule.

| Arm/contrast | Execution state | Scientific disposition |
|---|---|---|
| R0 — M00/A0 on an identical Beta cohort | BLOCKED: no authenticated canonical cohort for matching frozen predictions | NO_EVALUABLE |
| G0 — pooled Meta/Tolima | BLOCKED: required real inputs/publication absent | NO_EVALUABLE |
| G1 — eligible national expansion | BLOCKED: no compatible national evidence verified | NO_EVALUABLE in this workspace; not a claim that national data do not exist elsewhere |
| L1 — regularized local adaptation | BLOCKED: no evaluated global base or chronological adaptation support | NO_EVALUABLE |
| Climate OFF/ON | BLOCKED: no common verified real cohort | NO_EVALUABLE |

Learning-global and adaptation-local hypotheses are both **NO_EVALUABLE**, not
`NO_RESPALDADA`. No verified Beta sensitivity, detections, false alerts,
municipality-year exposure, AP, Brier, territorial metrics or climate effect is
available. No comparative prediction/metric table is fabricated.

The available design still identifies formal Beta adoption of the reference
budget (at most one false alert per municipality-year) and the EXP04 minus-two
percentage-point margin as pending. Neither was used as a Beta approval rule.
Any later Beta protocol must freeze its own feature/cohort/split/adaptation and
selection rules before fitting. 2024 remains consumed retrospective stress;
no independent confirmation or 2025 validation is established here.

## Validation executed

| Command | Result |
|---|---|
| `KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest tests/unit/test_canonical_model_table.py -q` | PASS: 17 tests |
| `KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest tests/contracts/test_kedro_configuration.py tests/unit/test_repository_bootstrap.py -q` | PASS: 28 tests |
| `bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only` | PASS: 17 checks; no scoped-plan or all-plan conformance claim |
| Standalone canonical CLI above | BLOCKED: exit 1 on the missing native manifest |

The 45 tests use engineering fixtures; they do not establish real territorial
coverage or scientific performance. Warnings concern existing OmegaConf resolver
deprecations and Kedro dataset names. No full suite, real model fitting or
experiment execution was performed. No DWP plan was created and no later Beta
phase was started. Historical artifacts, saved preparers, contracts, pipelines
and scientific results remain unchanged. G5 remains `NOT_APPROVED`; champion
remains `not_selected`.


Documentation checks: the repository-wide Markdown checker reports **FAIL**
for eight existing references to the moved `experimentos.md`. Each failing
reference and missing target was checked against incoming `df364e5`: all eight
are inherited. All links in this report resolve (**PASS**). These unrelated
historical documents were not repaired. The final staged whitespace check is
recorded with the delivery; no Python implementation changed in this task.
