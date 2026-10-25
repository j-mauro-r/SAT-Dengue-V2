# Kedro migration, execution and historical preservation

## Current cleanup and execution — Session 8

The active implementation is `src/sat_dengue`. Kedro owns orchestration; domain
modules own calculations; datasets own verified I/O and atomic immutable publication;
explicit optional MLflow hooks own allowlisted metadata. The executable
[repository disposition registry](repository-disposition.json) owns the resolved
inventory and retained adapters. The separate [cleanup correspondence](kedro-cleanup-identities.json)
verifies original baseline blobs, pre-cleanup blobs at
`861b36966cec26d1d2b36edee4d6ada6d5bc0930`, and final identity/absence. Earlier closed
mappings remain byte-identical and are verified simultaneously, never rewritten.
The 67 authorized paths are a ceiling, not a deletion list. Final validation and
commit receipts remain local in PLAN_030 `analysis_results/session8/HANDOFF.md`.

```bash
python -m pip install .                         # base: configuration/bootstrap
python -m pip install '.[dev,modeling,tracking]' # optional scientific/tracking tools
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=replay
kedro run --pipeline=replay_synthetic --params=profile=replay_synthetic
```

Every dependency pin is declared in `pyproject.toml`; requirements files select
extras and generated constraints derive from that authority. The `notebook` extra
is historical compatibility tooling; no notebook kernel is required by replay or CI.
Base imports/registers all graphs without importing modeling or tracking packages.
The default remains foundation. The [testing guide](../TESTING_GUIDE.md) owns the
complete synthetic selection, required fail-closed private acceptance, wheel checks
and source/test mapping. Dataset names/catalog/checkpoint schemas are unchanged.

Sequential restart verifies complete source/contract/code/environment/configuration,
ordered ancestors and every immutable stage payload before reuse. A changed code
identity starts a new execution; never copy or rename old checkpoints to obtain reuse.
Failure before final publication cannot certify success. Missing/tampered ancestors
fail closed; uncheckpointed publication conflicts require inspection. There is no
concurrent writer/cache service or automatic scientific repair. Run DWP writers,
gates, projections and renders sequentially too.

Tracking is explicitly opt-in and requires its extra:

```bash
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/mlflow \
  kedro run --pipeline=replay --params=tracking=enabled
```

The [security owner](../SECURITY.md#bounded-local-mlflow-tracking) defines the allowlist.
Only aggregate metrics, identities and safe pointers are stored; no raw rows, X/Y,
private absolute paths, secrets, native components or duplicate scientific bundles.
Success follows independent final publication verification; failures/aborts are
FAILED/KILLED, duplicate verified publications are KILLED, and RUNNING after process
death certifies nothing. Tracking-disabled execution requires no MLflow import.

### Historical recovery and retained surfaces

Use each registry entry's exact Git revision/path and both blob/SHA-256 identities.
For example, inspect the pre-cleanup tree with
`git show 861b36966cec26d1d2b36edee4d6ada6d5bc0930:<path>`; inspect original baseline
bytes with `git show 89d538c93ff20824c96c7fe0929baaa9d900e999:<path>`. Write recovery
copies only to ignored repository scratch and verify their identities. Native
scientific bundles require the existing local evidence; Git alone cannot restore
private payloads. Never overwrite live code, historical hashes or native manifests.

Notebooks 03–08 remain physically frozen for source-code identity readers and
historical regression checks. They have zero active production entrypoints; no
notebook is executed by replay, CI or current commands, and no report notebook is
generated. Their old script-import commands describe the recoverable historical
tree only. The EDA03 report and January Earth Engine recipe have complete Git
recovery pointers; no duplicate archive is needed. The January incorporation Python
tool remains historical provenance/regression code, not an authorized acquisition
command. Existing experimental-EDA archive bytes are unchanged.

Two thin Stage 2 facades remain because legacy readiness/source fingerprints still
read their fixed paths. Stage 2 visual/traceability helpers retain observed unique
historical safeguards. Their actual consumers, owners and measurable retirement
conditions are in the registry. Retained package legacy I/O engines serve fixed
native component loading and synthetic historical regressions; current scientific
equations have single domain owners. No historical fitting command is current.

### Scientific status and remaining debt

All 2,553 original identities and 45 physical native bundles remain protected.
G5 `NOT_APPROVED`, champion `not_selected`, six real `does_not_meet` decisions,
consumed-2025 restrictions, 13 source exceptions and 17 immutable KEEP/UNVERIFIED
bundles are unchanged. Zero real fits/refits/calibration/search/selection. Existing
outer-refit/calibrator/as-of/uncertainty limitations remain; no full historical
reproducibility, operational approval or performance improvement is claimed.

Kedro dotted dataset warnings are retained because renaming would change catalog,
identity and checkpoint surfaces. Naming the partial node would modify pipeline
assembly outside the 18 authorized consumers, so it remains bounded presentation
debt. MLflow/SQLAlchemy `noload` deprecation is upstream debt; no dependency update.
Whole-directory legacy-script diagnostics include historical EDA formatting/type
debt; maintained-tool quality is enumerated separately from immutable historical
regression sources. No lint suppression is introduced to hide it. Final Review's
broader legacy-script gate remains a separate pending task and may require a new
protected-path decision. Skills disposition: none; pinned tools and locks unchanged.

## Historical migration records

The session records and initial proposed ledger below describe their recorded
checkpoints. Their Pending statuses and old notebook/CLI commands are historical;
the executable registry above owns current dispositions and execution. Preserve
the original failed gates and dated scientific evidence.


## Current Session 2 authority

Mauricio authorized only T-foundation on 2026-10-22, starting from clean commit
`32f96a69521c24b1f9dc2117c1a31b2851d45d72` on `refactor/kedro-migration`.
The original revision-2 request was subsequently amended by explicit human reply
“Autorizar la enmienda acotada” after the two dependency metadata files were found
inside the protected inventory. The official local DWP helper recorded revision 3
`acb5cf72402bbe261e5a3875fb3f25b25cad592bc4008efb0dec17baea62fbde`, amendment seq 31 and
approval seq 32; T-foundation starts at seq 33. The amendment changes only its
configuration/dependency acceptance and metadata preservation boundary. Earned
T-baseline evidence remains historical fact, and no later task is authorized.

[ADR-0002](../decisions/adr-0002-kedro-orchestration-boundary.md) owns the architecture
and dated official compatibility sources. The five approved scientific JSON
authorities, G5 NOT_APPROVED, champion not_selected and consumed-2025 prohibition
remain unchanged. No Stage 2 migration or real-data fit occurs in this session.

The following Session 1 sections preserve their original historical authorization
and evidence. Their “no Session 2” restrictions describe those earlier sessions;
the present explicit instruction authorizes the bounded foundation above.


## Session 1 authority and boundaries

Mauricio authorized T-baseline only on 2026-10-22. Engineering baseline:
`89d538c93ff20824c96c7fe0929baaa9d900e999` on `refactor/kedro-migration`, initially clean.
This commit is not claimed as the producer of historical scientific artifacts.
The local DWP 7.8.1 materialization records `Mauricio / plan_authorship`.
No Kedro installation, real fit, data replacement, file removal or Session 2 work
is authorized here. G2/G3/G4 retain their accepted states; G5 remains
`NOT_APPROVED` and champion `not_selected`. Consumed 2025 is replay evidence only.

## Approved T-baseline amendment — 2026-10-22

Mauricio explicitly approved revision **2**, contract
`3183d0df6b93ff606663c7fa93b5a3c69d4a2f3f9a8e7c74f26713bb5c9e4deb`,
through the repository-local `/dwp-refine` flow. Its parent is revision 1,
`eb451f9c295e908bfc087ca746834e8b2ec88cbd921b4d0db36f19f06475b609`.
The official amendment and renewed approval preserve the original failed gate;
only fresh revision-2 evidence can close T-baseline. The authorized work ends
there. T-foundation, Session 2 and Kedro installation remain outside authorization.

The [executable approved scope](kedro-baseline-scope.json) records all 12 active
bundle manifest paths, the 13 exact historical source path/SHA-256 exceptions
listed below, and the 17 affected historical bundle manifests and fingerprints.
Its SHA-256 is `5f16db6458a771fd2ee32197247b3331ecd5f57b148319e7ba99ba806cc9165f`,
pinned in the revised DWP contract and harness. This is an approved narrowing of
the reconstruction obligation. It grants no new scientific decision.

Complete source recovery remains mandatory for the active chain, derived from
protected manifest dependency hashes: `active_missing=[]`. Historical recovery
still examines every native manifest and every recovered source object. Its
missing set must equal the closed 13-entry list exactly. An additional missing
source, changed exception path/hash, or altered coverage receipt fails. The
harness does not skip the historical reconstruction test.

Every affected historical bundle remains **KEEP / UNVERIFIED**. Its source
reproducibility is unverified even though its stored payload hashes are protected.
Retirement, modification and use as equivalence evidence are forbidden. The
executable dispositions reject changed status, mutation permission or equivalence
permission; replay receipts must name exactly the approved active chain. Full
historical reproducibility **cannot be claimed**. Neither complete historical
replay nor source recovery for these exceptions is an achieved outcome.

After the LightGBM 4.7 process exits (also on failure/timeout), the parent process
independently reads all 2,553 protected files and compares their size and SHA-256
with the pinned original `baseline.json`. It also enumerates all entries under
each protected bundle and checks its original manifest and bundle identity.
Replacement, removal, additional files/directories, symlinks and identity changes
fail. The Python `open()` audit hook remains an additional guard, not the evidence
for post-replay preservation. Synthetic tests cover same-size replacement through
`os.replace`, deletion, extra/nested files, identity changes and symlinks.

Observed receipts are local: `tmp/kedro-migration/source-coverage-observed.json`,
`post-replay-4.7.0.json` and `compatibility-4.7.0.json`. The post-replay receipt
records scan start/end timestamps, result, counts and method; a failure records
its error and still fails pytest. The DWP runner owns acceptance evidence under
`gates/T-baseline/`; the amendment handoff and evidence index are in
`analysis_results/session1_amendment/`. These are separate from the original
checkpoint evidence in `analysis_results/session1/`.

G5 remains `NOT_APPROVED`, champion `not_selected`, and 2025 remains consumed;
selection, tuning and training on 2025 are forbidden. The native replay guard
blocks fit/selection/publication entrypoints and receipts require zero new real
fits. Source recovery and inference use existing local environments only.

## Comparison contract declared before execution

Keys, categories, feature order, labels, missingness masks, alerts, cohort order
and scientific decisions must match exactly. Numeric comparison starts at
`rtol=1e-8, atol=1e-10`; historical zero-tolerance saved-model round trips and
byte-for-byte bundle verification remain stricter. No tolerance may be relaxed
after inspecting differences. CPU inference uses one thread; saved native models
and JSON preparers do not fit. Potential cross-runtime floating arithmetic and
serialization differences are reported separately, with identical libraries other
than LightGBM in the compatibility candidate. No training randomness is introduced.

## Baseline evidence and runtime

The ignored `tmp/kedro-migration/baseline.json` inventories 2553
protected files (21,821,925,628 bytes), all
368 tracked paths, input/contract/notebook/code hashes, 45
bundle manifests and installed versions. SHA-256:
`d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3`.
Evidence logs belong to `.dwp/plans/PLAN_030_kedro_architecture_migration/analysis_results/session1/`.
Private rows are never included in this record. Local artifacts must accompany any
cross-host handoff; Git alone cannot restore them.

The existing `.venv` uses Python 3.12.11 and LightGBM 4.6.0. Isolated copies in
`tmp/kedro-migration/historical46/` and `candidate47/` preserve the original
runtime. Only the candidate receives LightGBM 4.7.0 and its required Narwhals 2.27.1 dependency.
The candidate uses an explicit `PYTHONPATH` overlay at `tmp/kedro-migration/lightgbm47/`;
the copied 4.6 distribution remains inactive there, without uninstalling files. Environment installation logs
and package snapshots remain local. Baseline unit suite: **277 passed**, eight
existing deprecation warnings, no failures (9.86 s).

## Disposition ledger

These are proposed later actions, never permission to remove files in Session 1.
`Verified` means the KEEP decision has been reviewed, not that a future migration
has passed parity. `Pending` means replacement/consumer review is still required.
Each row is owned by the implementing agent for its named stage, with Mauricio
owning scientific/governance decisions. Recovery is the pinned Git object plus the
local immutable artifact inventory, never an assumed regenerated equivalent.
Unknown and newly discovered paths default to **KEEP** until reviewed.
Textual consumer searches miss dynamic imports and external notebook users; the
prerequisites explicitly require owning-stage integration tests before retirement.

| Path | Proposed action | Reason | Current consumers | Replacement / destination | Prerequisite before mutation | Recovery | Status |
|---|---|---|---|---|---|---|---|
| `.agents/README.md` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/README.md` | Pending |
| `.agents/agents/architect.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/architect.md` | Pending |
| `.agents/agents/debugger.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/debugger.md` | Pending |
| `.agents/agents/executor.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/executor.md` | Pending |
| `.agents/agents/perf-optimizer.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/perf-optimizer.md` | Pending |
| `.agents/agents/qa.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/qa.md` | Pending |
| `.agents/agents/reviewer.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/reviewer.md` | Pending |
| `.agents/agents/security-auditor.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/docs/skills_agents_catalog.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/agents/security-auditor.md` | Pending |
| `.agents/commands/agent-create.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/agent-create.md` | Pending |
| `.agents/commands/branch.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/branch.md` | Pending |
| `.agents/commands/code-review.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/code-review.md` | Pending |
| `.agents/commands/commit.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/commit.md` | Pending |
| `.agents/commands/dwp-create.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-create.md` | Pending |
| `.agents/commands/dwp-execute.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-execute.md` | Pending |
| `.agents/commands/dwp-refine.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-refine.md` | Pending |
| `.agents/commands/dwp-resume.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-resume.md` | Pending |
| `.agents/commands/dwp-status.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-status.md` | Pending |
| `.agents/commands/dwp-upgrade.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-upgrade.md` | Pending |
| `.agents/commands/dwp-verify.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/dwp-verify.md` | Pending |
| `.agents/commands/pr.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/pr.md` | Pending |
| `.agents/commands/skill-create.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/commands/skill-create.md` | Pending |
| `.agents/docs/COMMANDS_REFERENCE.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/docs/COMMANDS_REFERENCE.md` | Pending |
| `.agents/docs/skills_agents_catalog.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/docs/skills_agents_catalog.md` | Pending |
| `.agents/settings.json` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.agents/settings.json` | Pending |
| `.claude` | KEEP | Single instruction owner through symlinks | `.agents/README.md`, `docs/governance/dwp.md` | `Existing symlink target` | Verify targets without duplicating instructions | `89d538c93ff2:.claude` | Verified |
| `.cursor` | KEEP | Single instruction owner through symlinks | `.agents/README.md`, `docs/governance/dwp.md` | `Existing symlink target` | Verify targets without duplicating instructions | `89d538c93ff2:.cursor` | Verified |
| `.dwp/config.json` | KEEP | Unclassified or unaffected; retain until individually reviewed | `AGENTS.md`, `docs/governance/dwp.md` | `Same path` | Explicit review before any mutation | `89d538c93ff2:.dwp/config.json` | Pending |
| `.github/dependabot.yml` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.github/dependabot.yml` | Pending |
| `.github/pull_request_template.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/workflows/ci.yml`, `scripts/check_markdown_links.py` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.github/pull_request_template.md` | Pending |
| `.github/workflows/ci.yml` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.github/workflows/ci.yml` | Pending |
| `.gitignore` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/workflows/ci.yml` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.gitignore` | Pending |
| `.review/extension.md` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/governance/dwp.md`, `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:.review/extension.md` | Pending |
| `AGENTS.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/README.md`, `.agents/settings.json`, `.github/pull_request_template.md`, `.github/workflows/ci.yml`; 14 more (local consumers.json) | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:AGENTS.md` | Pending |
| `CLAUDE.md` | KEEP | Single instruction owner through symlinks | `docs/governance/dwp.md` | `Existing symlink target` | Verify targets without duplicating instructions | `89d538c93ff2:CLAUDE.md` | Verified |
| `README.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/pull_request_template.md`, `.github/workflows/ci.yml`, `AGENTS.md`, `docs/README.md`; 11 more (local consumers.json) | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:README.md` | Pending |
| `data/sources/Divipola-departamentos.md` | KEEP | Source provenance evidence | Owning directory / no direct textual reference found; review before change | `Same path` | No source mutation authorized | `89d538c93ff2:data/sources/Divipola-departamentos.md` | Verified |
| `data/sources/Divipola-municipios.md` | KEEP | Source provenance evidence | `docs/product/stage-2/CH1-dataset-construction-candidate.md`, `scripts/january_2020_climate_incorporation.py`, `scripts/stage2_panel_review.py`, `scripts/training_preparation/pipeline.py`; 3 more (local consumers.json) | `Same path` | No source mutation authorized | `89d538c93ff2:data/sources/Divipola-municipios.md` | Verified |
| `data/sources/divipola-provenance.json` | KEEP | Source provenance evidence | `docs/archive/experimental-eda/stage-2/DATA-01-Source Provenance.md`, `scripts/validate_stage2_training_readiness.py`, `tests/unit/test_consolidated_dataset_pipeline.py` | `Same path` | No source mutation authorized | `89d538c93ff2:data/sources/divipola-provenance.json` | Verified |
| `docs/README.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/workflows/ci.yml`, `AGENTS.md`, `README.md`, `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/README.md` | Pending |
| `docs/SECURITY.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/SECURITY.md` | Pending |
| `docs/TESTING_GUIDE.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/settings.json`, `.review/extension.md`, `AGENTS.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/TESTING_GUIDE.md` | Pending |
| `docs/architecture/system-overview.md` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/architecture/system-overview.md` | Pending |
| `docs/archive/experimental-eda/README.md` | KEEP | Historical evidence or accepted foundation decision | `scripts/stage2_derived_recompute_reconciliation.py`, `scripts/stage2_panel_review.py` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/README.md` | Verified |
| `docs/archive/experimental-eda/manifest.json` | KEEP | Historical evidence or accepted foundation decision | Owning directory / no direct textual reference found; review before change | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/manifest.json` | Verified |
| `docs/archive/experimental-eda/notebooks/01_stage2_residence_onset_eda.ipynb` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/notebooks/01_stage2_residence_onset_eda.ipynb` | Verified |
| `docs/archive/experimental-eda/notebooks/02_stage2_monthly_sensitivity_associations.ipynb` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/notebooks/02_stage2_monthly_sensitivity_associations.ipynb` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-01-2013-date-inconsistency-investigation.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-01-2013-date-inconsistency-investigation.md` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-01-Initial Recognition Report.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-01-Initial Recognition Report.md` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-01-Priority Field Matrix.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-01-Priority Field Matrix.md` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-01-Source Provenance.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-01-Source Provenance.md` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-02-monthly-sensitivity-associations.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-02-monthly-sensitivity-associations.md` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-03-panel-review.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-03-panel-review.md` | Verified |
| `docs/archive/experimental-eda/stage-2/DATA-04-retrospective-use-rules.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/DATA-04-retrospective-use-rules.md` | Verified |
| `docs/archive/experimental-eda/stage-2/nota-metodologica.md` | KEEP | Historical evidence or accepted foundation decision | `docs/archive/experimental-eda/manifest.json` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/archive/experimental-eda/stage-2/nota-metodologica.md` | Verified |
| `docs/data/data-policy.md` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/SECURITY.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/data/data-policy.md` | Pending |
| `docs/decisions/adr-0001-foundation-boundaries.md` | KEEP | Historical evidence or accepted foundation decision | `AGENTS.md` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/decisions/adr-0001-foundation-boundaries.md` | Verified |
| `docs/governance/ai-developer-first.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/workflows/ci.yml`, `AGENTS.md`, `README.md`, `docs/TESTING_GUIDE.md`; 1 more (local consumers.json) | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/governance/ai-developer-first.md` | Pending |
| `docs/governance/dwp.md` | UPDATE | Synchronize affected execution/installation references at owning task | `AGENTS.md`, `README.md`, `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/governance/dwp.md` | Pending |
| `docs/operations/harness-documentation-audit-2026-10-20.md` | KEEP | Historical evidence or accepted foundation decision | Owning directory / no direct textual reference found; review before change | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/operations/harness-documentation-audit-2026-10-20.md` | Verified |
| `docs/operations/stage2-pr-reconciliation.md` | KEEP | Historical evidence or accepted foundation decision | `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/operations/stage2-pr-reconciliation.md` | Verified |
| `docs/operations/validation-and-evidence.md` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/operations/validation-and-evidence.md` | Pending |
| `docs/product/product-definition.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/product-definition.md` | Verified |
| `docs/product/stage-1/PROD-01-business-question.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-01-business-question.md` | Verified |
| `docs/product/stage-1/PROD-02-users.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-02-users.md` | Verified |
| `docs/product/stage-1/PROD-03-supported-decisions.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-03-supported-decisions.md` | Verified |
| `docs/product/stage-1/PROD-04-dashboard-master-user-story.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-04-dashboard-master-user-story.md` | Verified |
| `docs/product/stage-1/PROD-05-new-period-flow.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-05-new-period-flow.md` | Verified |
| `docs/product/stage-1/PROD-06-ui-information.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-06-ui-information.md` | Verified |
| `docs/product/stage-1/PROD-07-draft-prediction-contract.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-07-draft-prediction-contract.md` | Verified |
| `docs/product/stage-1/PROD-08-draft-input-contract.md` | KEEP | Independent product/research authority | Owning directory / no direct textual reference found; review before change | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/product/stage-1/PROD-08-draft-input-contract.md` | Verified |
| `docs/product/stage-2/CH1-dataset-construction-candidate.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/product/stage-2/CH1-dataset-construction-candidate.md` | Pending |
| `docs/product/stage-2/DATA-01-Priority Field Matrix.md` | UPDATE | Synchronize affected execution/installation references at owning task | `docs/archive/experimental-eda/manifest.json`, `docs/product/traking-concluciones.md` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/product/stage-2/DATA-01-Priority Field Matrix.md` | Pending |
| `docs/product/stage-2/Informe_EDA_03_vista_revisada.ipynb` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/product/stage-2/Informe_EDA_03_vista_revisada.ipynb` | Pending |
| `docs/product/stage-3/README.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/product/stage-3/README.md` | Pending |
| `docs/product/stage-3/milestone-1-validation.md` | KEEP | Historical evidence or accepted foundation decision | Owning directory / no direct textual reference found; review before change | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/product/stage-3/milestone-1-validation.md` | Verified |
| `docs/product/stage-3/milestone-2-validation.md` | KEEP | Historical evidence or accepted foundation decision | Owning directory / no direct textual reference found; review before change | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/product/stage-3/milestone-2-validation.md` | Verified |
| `docs/product/stage-3/milestone-3-validation.md` | KEEP | Historical evidence or accepted foundation decision | Owning directory / no direct textual reference found; review before change | `Same path` | No rewrite of historical evidence | `89d538c93ff2:docs/product/stage-3/milestone-3-validation.md` | Verified |
| `docs/product/stage-3/training_preparation_contract_v1.json` | KEEP | Authoritative scientific contract or policy; immutable in this session | `docs/product/stage-4/model_engineering_contract_v1.json`, `scripts/model_training/contract.py`, `scripts/training_preparation/contract.py`, `tests/unit/test_final_evaluation.py` | `Same path` | Separate human authority for semantic changes | `89d538c93ff2:docs/product/stage-3/training_preparation_contract_v1.json` | Verified |
| `docs/product/stage-4/README.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/product/stage-4/README.md` | Pending |
| `docs/product/stage-4/model_engineering_contract_v1.json` | KEEP | Authoritative scientific contract or policy; immutable in this session | `docs/TESTING_GUIDE.md`, `docs/product/stage-5/probability_calibration_thresholds_contract_v1.json`, `docs/product/traking-concluciones.md`, `scripts/model_evaluation/contract.py`; 2 more (local consumers.json) | `Same path` | Separate human authority for semantic changes | `89d538c93ff2:docs/product/stage-4/model_engineering_contract_v1.json` | Verified |
| `docs/product/stage-5/README.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/product/stage-5/README.md` | Pending |
| `docs/product/stage-5/champion_decision_policy_v1.json` | KEEP | Authoritative scientific contract or policy; immutable in this session | `docs/product/stage-5/model_evaluation_contract_v1.json`, `docs/product/stage-5/probability_calibration_thresholds_contract_v1.json`, `scripts/model_evaluation/decision_policy.py` | `Same path` | Separate human authority for semantic changes | `89d538c93ff2:docs/product/stage-5/champion_decision_policy_v1.json` | Verified |
| `docs/product/stage-5/model_evaluation_contract_v1.json` | KEEP | Authoritative scientific contract or policy; immutable in this session | `scripts/model_assessment/loading.py`, `scripts/model_assessment/pipeline.py`, `tests/unit/test_final_evaluation.py`, `tests/unit/test_model_evaluation.py` | `Same path` | Separate human authority for semantic changes | `89d538c93ff2:docs/product/stage-5/model_evaluation_contract_v1.json` | Verified |
| `docs/product/stage-5/probability_calibration_thresholds_contract_v1.json` | KEEP | Authoritative scientific contract or policy; immutable in this session | `docs/TESTING_GUIDE.md`, `scripts/model_evaluation/contract.py` | `Same path` | Separate human authority for semantic changes | `89d538c93ff2:docs/product/stage-5/probability_calibration_thresholds_contract_v1.json` | Verified |
| `docs/product/traking-concluciones.md` | KEEP | Scientific decision IDs and approval boundaries | `AGENTS.md`, `docs/archive/experimental-eda/manifest.json`, `docs/operations/harness-documentation-audit-2026-10-20.md` | `Same established path` | New scientific decision requires human authority | `89d538c93ff2:docs/product/traking-concluciones.md` | Verified |
| `docs/research/colombia-dengue-outbreak-events.md` | KEEP | Independent product/research authority | `docs/product/traking-concluciones.md` | `Same path` | Only fix a demonstrated broken technical reference | `89d538c93ff2:docs/research/colombia-dengue-outbreak-events.md` | Verified |
| `docs/roadmap/master-plan.md` | UPDATE | Synchronize affected execution/installation references at owning task | `.agents/settings.json`, `.github/workflows/ci.yml`, `.review/extension.md`, `AGENTS.md`; 3 more (local consumers.json) | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/roadmap/master-plan.md` | Pending |
| `docs/standards/engineering-standards.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/standards/engineering-standards.md` | Pending |
| `docs/standards/ml-scientific-standards.md` | UPDATE | Synchronize affected execution/installation references at owning task | Owning directory / no direct textual reference found; review before change | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:docs/standards/ml-scientific-standards.md` | Pending |
| `notebooks/03_consolidated_dataset_pipeline.ipynb` | RETIRE | Production sequencing will move to the DAG; preserve executed history | `docs/architecture/system-overview.md`, `docs/product/stage-2/CH1-dataset-construction-candidate.md`, `docs/roadmap/master-plan.md`, `scripts/stage2_notebook_visual_assets.py`; 3 more (local consumers.json) | `Git baseline/native evidence; archive only unique outputs` | T-e2e pass and notebook evidence recovery verified | `89d538c93ff2:notebooks/03_consolidated_dataset_pipeline.ipynb` | Pending |
| `notebooks/04_training_preparation_pipeline.ipynb` | RETIRE | Production sequencing will move to the DAG; preserve executed history | `docs/architecture/system-overview.md`, `docs/product/stage-3/README.md`, `scripts/training_preparation/development.py`, `scripts/training_preparation/notebook_execution.py`; 2 more (local consumers.json) | `Git baseline/native evidence; archive only unique outputs` | T-e2e pass and notebook evidence recovery verified | `89d538c93ff2:notebooks/04_training_preparation_pipeline.ipynb` | Pending |
| `notebooks/05_baseline_models.ipynb` | RETIRE | Production sequencing will move to the DAG; preserve executed history | `docs/product/stage-4/README.md`, `scripts/model_training/pipeline.py` | `Git baseline/native evidence; archive only unique outputs` | T-e2e pass and notebook evidence recovery verified | `89d538c93ff2:notebooks/05_baseline_models.ipynb` | Pending |
| `notebooks/06_candidate_models.ipynb` | RETIRE | Production sequencing will move to the DAG; preserve executed history | `docs/product/stage-4/README.md`, `scripts/model_training/candidates.py` | `Git baseline/native evidence; archive only unique outputs` | T-e2e pass and notebook evidence recovery verified | `89d538c93ff2:notebooks/06_candidate_models.ipynb` | Pending |
| `notebooks/07_probability_calibration_thresholds.ipynb` | RETIRE | Production sequencing will move to the DAG; preserve executed history | `docs/product/stage-5/README.md`, `scripts/model_evaluation/pipeline.py` | `Git baseline/native evidence; archive only unique outputs` | T-e2e pass and notebook evidence recovery verified | `89d538c93ff2:notebooks/07_probability_calibration_thresholds.ipynb` | Pending |
| `notebooks/08_model_evaluation.ipynb` | RETIRE | Production sequencing will move to the DAG; preserve executed history | `docs/product/stage-5/README.md`, `scripts/model_assessment/pipeline.py` | `Git baseline/native evidence; archive only unique outputs` | T-e2e pass and notebook evidence recovery verified | `89d538c93ff2:notebooks/08_model_evaluation.ipynb` | Pending |
| `notebooks/gee_recover_january_2020.js` | KEEP | Unclassified or unaffected; retain until individually reviewed | Owning directory / no direct textual reference found; review before change | `Same path` | Explicit review before any mutation | `89d538c93ff2:notebooks/gee_recover_january_2020.js` | Pending |
| `pyproject.toml` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/workflows/ci.yml`, `scripts/model_evaluation/contract.py`, `scripts/model_evaluation/pipeline.py`, `scripts/model_training/contract.py`; 7 more (local consumers.json) | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:pyproject.toml` | Pending |
| `requirements-modeling.txt` | UPDATE | Synchronize affected execution/installation references at owning task | `.github/workflows/ci.yml`, `docs/TESTING_GUIDE.md`, `docs/product/stage-4/README.md`, `scripts/model_training/candidates.py` | `Same owner; Kedro paths only after implementation` | Owning task parity; preserve governance and historical facts | `89d538c93ff2:requirements-modeling.txt` | Pending |
| `scripts/check_markdown_links.py` | KEEP | Maintained repository validator | `.github/pull_request_template.md`, `.github/workflows/ci.yml`, `docs/TESTING_GUIDE.md`, `docs/operations/harness-documentation-audit-2026-10-20.md`; 1 more (local consumers.json) | `Same path` | No scientific migration needed | `89d538c93ff2:scripts/check_markdown_links.py` | Verified |
| `scripts/evaluation_metrics.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-5/README.md`, `docs/product/stage-5/model_evaluation_contract_v1.json`, `scripts/final_evaluation/evaluation.py`; 3 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/evaluation_metrics.py` | Pending |
| `scripts/final_evaluation/__init__.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/final_evaluation/__init__.py` | Pending |
| `scripts/final_evaluation/cohorts.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_final_evaluation.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/final_evaluation/cohorts.py` | Pending |
| `scripts/final_evaluation/evaluation.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_final_evaluation.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/final_evaluation/evaluation.py` | Pending |
| `scripts/final_evaluation/execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-5/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/final_evaluation/execution.py` | Pending |
| `scripts/final_evaluation/pipeline.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/final_evaluation/pipeline.py` | Pending |
| `scripts/final_evaluation/protocol.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_final_evaluation.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/final_evaluation/protocol.py` | Pending |
| `scripts/january_2020_climate_incorporation.py` | KEEP | Acquisition provenance requires individual review | `docs/archive/experimental-eda/README.md`, `tests/unit/test_january_2020_climate_incorporation.py` | `Same path; possible archive after review` | Prove unique recovery and no active consumers | `89d538c93ff2:scripts/january_2020_climate_incorporation.py` | Pending |
| `scripts/model_assessment/__init__.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/__init__.py` | Pending |
| `scripts/model_assessment/comparison.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_model_assessment.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/comparison.py` | Pending |
| `scripts/model_assessment/execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/execution.py` | Pending |
| `scripts/model_assessment/input_validation.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_model_assessment.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/input_validation.py` | Pending |
| `scripts/model_assessment/loading.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/loading.py` | Pending |
| `scripts/model_assessment/pipeline.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/protocol.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/pipeline.py` | Pending |
| `scripts/model_assessment/policy.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/evaluation.py`, `tests/unit/test_final_evaluation.py`, `tests/unit/test_model_assessment.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/policy.py` | Pending |
| `scripts/model_assessment/proposal.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_model_assessment.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_assessment/proposal.py` | Pending |
| `scripts/model_evaluation/__init__.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/__init__.py` | Pending |
| `scripts/model_evaluation/availability.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/cohorts.py`, `scripts/model_assessment/policy.py`, `scripts/model_assessment/proposal.py`, `tests/unit/test_model_assessment.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/availability.py` | Pending |
| `scripts/model_evaluation/contract.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/pipeline.py`, `scripts/model_assessment/execution.py`, `scripts/model_assessment/loading.py`, `tests/unit/test_model_assessment.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/contract.py` | Pending |
| `scripts/model_evaluation/decision_policy.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/evaluation.py`, `scripts/model_assessment/comparison.py`, `scripts/model_assessment/pipeline.py`, `scripts/model_assessment/policy.py`; 2 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/decision_policy.py` | Pending |
| `scripts/model_evaluation/execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-5/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/execution.py` | Pending |
| `scripts/model_evaluation/internal_evidence.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/internal_evidence.py` | Pending |
| `scripts/model_evaluation/notebook_execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-5/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/notebook_execution.py` | Pending |
| `scripts/model_evaluation/pipeline.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/pipeline.py`, `scripts/model_assessment/loading.py`, `tests/unit/test_model_evaluation.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_evaluation/pipeline.py` | Pending |
| `scripts/model_training/__init__.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/__init__.py` | Pending |
| `scripts/model_training/candidate_families.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/pipeline.py`, `scripts/model_evaluation/internal_evidence.py`, `scripts/model_evaluation/pipeline.py`, `tests/unit/test_candidate_families.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/candidate_families.py` | Pending |
| `scripts/model_training/candidate_notebook.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-4/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/candidate_notebook.py` | Pending |
| `scripts/model_training/candidate_preparation.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_candidate_families.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/candidate_preparation.py` | Pending |
| `scripts/model_training/candidate_selection.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_candidate_families.py`, `tests/unit/test_xgboost_candidate.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/candidate_selection.py` | Pending |
| `scripts/model_training/candidate_suite.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/model_evaluation/pipeline.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/candidate_suite.py` | Pending |
| `scripts/model_training/candidates.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/candidates.py` | Pending |
| `scripts/model_training/contract.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/model_assessment/loading.py`, `scripts/model_evaluation/contract.py`, `scripts/model_evaluation/internal_evidence.py`, `scripts/model_evaluation/pipeline.py`; 3 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/contract.py` | Pending |
| `scripts/model_training/events.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/cohorts.py`, `scripts/model_assessment/loading.py`, `scripts/model_evaluation/pipeline.py`, `tests/unit/test_model_metrics.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/events.py` | Pending |
| `scripts/model_training/execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-4/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/execution.py` | Pending |
| `scripts/model_training/gam_adapter.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_candidate_families.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/gam_adapter.py` | Pending |
| `scripts/model_training/lightgbm_adapter.py` | MIGRATE | Preserve existing domain logic and safeguards | Owning directory / no direct textual reference found; review before change | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/lightgbm_adapter.py` | Pending |
| `scripts/model_training/loading.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/model_assessment/loading.py`, `scripts/model_evaluation/pipeline.py`, `tests/unit/test_model_evaluation.py`, `tests/unit/test_model_metrics.py`; 2 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/loading.py` | Pending |
| `scripts/model_training/metrics.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/evaluation_metrics.py`, `scripts/model_evaluation/pipeline.py`, `tests/unit/test_candidate_families.py`, `tests/unit/test_model_assessment.py`; 2 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/metrics.py` | Pending |
| `scripts/model_training/notebook_execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-4/README.md`, `scripts/final_evaluation/execution.py`, `scripts/model_assessment/execution.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/notebook_execution.py` | Pending |
| `scripts/model_training/persistence.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/execution.py`, `scripts/final_evaluation/pipeline.py`, `scripts/final_evaluation/protocol.py`, `scripts/model_assessment/execution.py`; 8 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/persistence.py` | Pending |
| `scripts/model_training/pipeline.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/model_evaluation/pipeline.py`, `tests/unit/test_model_evaluation.py`, `tests/unit/test_model_metrics.py`, `tests/unit/test_model_training.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/pipeline.py` | Pending |
| `scripts/model_training/references.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/pipeline.py`, `scripts/model_assessment/loading.py`, `scripts/model_evaluation/pipeline.py`, `tests/unit/test_final_evaluation.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/references.py` | Pending |
| `scripts/model_training/xgboost_adapter.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_candidate_families.py`, `tests/unit/test_xgboost_candidate.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/model_training/xgboost_adapter.py` | Pending |
| `scripts/stage2_consolidated_dataset_pipeline.py` | ADAPT | Preserve existing domain logic and safeguards | `docs/architecture/system-overview.md`, `docs/product/stage-2/CH1-dataset-construction-candidate.md`, `scripts/validate_stage2_training_readiness.py`, `tests/unit/test_consolidated_dataset_pipeline.py`; 1 more (local consumers.json) | `src/sat_dengue/data/; datasets/legacy_* compatibility helpers` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/stage2_consolidated_dataset_pipeline.py` | Migrated; thin adapter retained until T-cleanup |
| `scripts/stage2_derived_recompute_reconciliation.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/archive/experimental-eda/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/stage2_derived_recompute_reconciliation.py` | Pending |
| `scripts/stage2_manifest_traceability.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/archive/experimental-eda/README.md`, `scripts/stage2_panel_review.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/stage2_manifest_traceability.py` | Pending |
| `scripts/stage2_monthly_sensitivity_analysis.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/archive/experimental-eda/README.md`, `docs/archive/experimental-eda/stage-2/DATA-02-monthly-sensitivity-associations.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/stage2_monthly_sensitivity_analysis.py` | Pending |
| `scripts/stage2_notebook_visual_assets.py` | KEEP | Report/test consumers still active | `scripts/training_preparation/development.py`, `scripts/training_preparation/temporal.py`, `scripts/validate_stage2_training_readiness.py`, `tests/unit/test_stage2_notebook_visual_assets.py`; 1 more (local consumers.json) | `Review reporting need in T-cleanup` | Verified replacement and consumer search | `89d538c93ff2:scripts/stage2_notebook_visual_assets.py` | Pending |
| `scripts/stage2_panel_review.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/archive/experimental-eda/README.md`, `docs/archive/experimental-eda/stage-2/DATA-03-panel-review.md`, `docs/archive/experimental-eda/stage-2/DATA-04-retrospective-use-rules.md`, `scripts/stage2_derived_recompute_reconciliation.py`; 1 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/stage2_panel_review.py` | Pending |
| `scripts/training_preparation/__init__.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/product/stage-3/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/__init__.py` | Pending |
| `scripts/training_preparation/audit.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-3/README.md` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/audit.py` | Pending |
| `scripts/training_preparation/contract.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/product/stage-3/README.md`, `scripts/final_evaluation/cohorts.py`, `scripts/model_training/loading.py`, `tests/unit/test_candidate_families.py`; 3 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/contract.py` | Pending |
| `scripts/training_preparation/development.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-3/README.md`, `scripts/final_evaluation/execution.py`, `scripts/model_training/persistence.py`; 2 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/development.py` | Pending |
| `scripts/training_preparation/eligibility.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_training_preparation.py`, `tests/unit/test_training_temporal.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/eligibility.py` | Pending |
| `scripts/training_preparation/features.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/cohorts.py`, `tests/unit/test_final_evaluation.py`, `tests/unit/test_training_preparation.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/features.py` | Pending |
| `scripts/training_preparation/notebook_execution.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-3/README.md`, `tests/unit/test_training_temporal.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/notebook_execution.py` | Pending |
| `scripts/training_preparation/persistence.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/model_training/persistence.py`, `tests/unit/test_training_preparation.py`, `tests/unit/test_training_temporal.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/persistence.py` | Pending |
| `scripts/training_preparation/pipeline.py` | MIGRATE | Preserve existing domain logic and safeguards | `scripts/final_evaluation/cohorts.py`, `scripts/final_evaluation/execution.py`, `scripts/final_evaluation/pipeline.py`, `scripts/final_evaluation/protocol.py`; 11 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/pipeline.py` | Pending |
| `scripts/training_preparation/preprocessing.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/product/stage-3/README.md`, `scripts/model_training/candidate_preparation.py`, `tests/unit/test_training_temporal.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/preprocessing.py` | Pending |
| `scripts/training_preparation/temporal.py` | MIGRATE | Preserve existing domain logic and safeguards | `docs/TESTING_GUIDE.md`, `docs/product/stage-3/README.md`, `scripts/model_training/candidate_selection.py`, `scripts/model_training/events.py`; 2 more (local consumers.json) | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/temporal.py` | Pending |
| `scripts/training_preparation/validation.py` | MIGRATE | Preserve existing domain logic and safeguards | `tests/unit/test_training_preparation.py` | `src/sat_dengue equivalent module; then retire old entry` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/training_preparation/validation.py` | Pending |
| `scripts/validate_stage2_training_readiness.py` | ADAPT | Preserve existing domain logic and safeguards | `docs/product/stage-2/CH1-dataset-construction-candidate.md`, `scripts/training_preparation/development.py`, `scripts/training_preparation/eligibility.py`, `tests/unit/test_stage2_training_readiness.py`; 1 more (local consumers.json) | `src/sat_dengue/data/; datasets/legacy_* compatibility helpers` | Per-stage parity and all import consumers moved | `89d538c93ff2:scripts/validate_stage2_training_readiness.py` | Migrated; thin adapter retained until T-cleanup |
| `skills-lock.json` | KEEP | Unclassified or unaffected; retain until individually reviewed | `.github/pull_request_template.md`, `.github/workflows/ci.yml`, `AGENTS.md`, `docs/TESTING_GUIDE.md`; 1 more (local consumers.json) | `Same path` | Explicit review before any mutation | `89d538c93ff2:skills-lock.json` | Pending |
| `tests/unit/test_candidate_families.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_candidate_families.py` | Pending |
| `tests/unit/test_consolidated_dataset_pipeline.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/product/stage-2/CH1-dataset-construction-candidate.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_consolidated_dataset_pipeline.py` | Pending |
| `tests/unit/test_final_evaluation.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_final_evaluation.py` | Pending |
| `tests/unit/test_january_2020_climate_incorporation.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_january_2020_climate_incorporation.py` | Pending |
| `tests/unit/test_markdown_links.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_markdown_links.py` | Pending |
| `tests/unit/test_model_assessment.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md`, `docs/product/stage-5/README.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_model_assessment.py` | Pending |
| `tests/unit/test_model_evaluation.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_model_evaluation.py` | Pending |
| `tests/unit/test_model_metrics.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_model_metrics.py` | Pending |
| `tests/unit/test_model_training.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_model_training.py` | Pending |
| `tests/unit/test_repository_bootstrap.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_repository_bootstrap.py` | Pending |
| `tests/unit/test_stage2_manifest_traceability.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_stage2_manifest_traceability.py` | Pending |
| `tests/unit/test_stage2_monthly_sensitivity_outputs.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_stage2_monthly_sensitivity_outputs.py` | Pending |
| `tests/unit/test_stage2_notebook_visual_assets.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_stage2_notebook_visual_assets.py` | Pending |
| `tests/unit/test_stage2_panel_review.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_stage2_panel_review.py` | Pending |
| `tests/unit/test_stage2_training_readiness.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_stage2_training_readiness.py` | Pending |
| `tests/unit/test_training_preparation.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md`, `docs/product/stage-3/milestone-1-validation.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_training_preparation.py` | Pending |
| `tests/unit/test_training_temporal.py` | UPDATE | Retain regression coverage while adapting import ownership | `docs/TESTING_GUIDE.md` | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_training_temporal.py` | Pending |
| `tests/unit/test_xgboost_candidate.py` | UPDATE | Retain regression coverage while adapting import ownership | Owning directory / no direct textual reference found; review before change | `Same tests plus mapped integration coverage` | Owning stage replacement passes equivalent safeguards | `89d538c93ff2:tests/unit/test_xgboost_candidate.py` | Pending |

| `.agents/skills/**` (188 tracked files) | KEEP | Indivisible pinned dependency, DWP 7.8.1 / reviewer 3.3.14 | Local command delegators | Same subtree | No vendor edits/upgrades authorized | `89d538c93ff2:.agents/skills`; inventory digest `679590a186332d2dededbbe106ac21bc91b6ad71c8251f893cbad7659e54550f` | Verified |

### Ignored and non-file surfaces

| Path or indivisible group | Proposed action | Reason / current consumers | Destination | Condition before modification | Recovery | Status |
|---|---|---|---|---|---|---|
| `data/raw/**`, ignored `data/sources/**` | KEEP | Scientific inputs; Stage 2 / source provenance | Same directories | Never alter in this migration | Baseline hashes plus original private copies | Verified |
| `data/interim/**`, `data/processed/**`, `artifacts/**` | KEEP | Historical/active native bundles consumed by Stages 2–5 and tests | Same paths; future outputs get new IDs | Required private parity before any dependent code migration | Baseline hashes and original local payloads | Verified |
| `.dwp/**` except tracked config | KEEP | Official local plan history and evidence | Same paths | Only official helpers for journal/projections; no old-plan repair | Existing local history/private backup | Verified |
| `.venv/**` | KEEP | User runtime, historical LightGBM 4.6 | Same path | No substitution or in-place package changes | Captured package inventory; existing environment | Verified |
| `tmp/**` | KEEP | May contain unique historical evidence; session snapshots and environments | Same paths | Individually review recovery and active writers before later disposal | Existing files; session reconstruction recipes | Pending |
| `.pytest_cache/**`, `.mypy_cache/**`, `.ruff_cache/**`, `**/__pycache__/**` | KEEP | Tool runtime caches | Same paths this session | No cleanup in Session 1 | Regenerable by respective tools | Pending |
| `docs/contracts/`, `docs/methodology/`, `tests/contracts/`, `tests/fixtures/` | KEEP | Existing empty or unused directories need later review | Same directories until T-cleanup | Exact emptiness/consumer check; no removal now | Baseline directory inventory | Pending |
| `.git/**`, other checkouts | KEEP / out of scope | Repository history and unrelated work | Unchanged | No history rewrite or external cleanup | Existing Git database | Verified |
| All unlisted ignored/unknown paths | KEEP | Unknown ownership or recovery | Unchanged | Explicit individual review | Existing path; no deletion authorized | Pending |

### New Session 1 surfaces

`tests/conftest.py` registers explicit private-evidence opt-in and deselects private
tests in normal CI. `tests/integration/test_migration_parity.py` and narrowly scoped
helpers own baseline identity, strict comparison, runtime and no-fit replay tests.
The existing CI test job also selects this harness without private opt-in. This
document owns disposition/provenance/recovery. The testing guide receives the
new source-to-test mapping; the documentation index links this owner. Local
inventory, runtime copies and reconstructed snapshots remain ignored.

Skills disposition: **none** — the installed DWP/reviewer catalogue already covers
execution and review; this bounded harness is repository code, not a reusable skill.
Documentation decision: **update** this owner, the testing map and documentation
index; add the synthetic harness to the existing CI test command. Preserve
scientific contracts, decisions and historical results unchanged.

## Historical Session 1 checkpoint — before amendment, 2026-10-22

**Scientific artifact preservation PASS; final saved-component compatibility PASS;
complete historical source reconstruction BLOCKED.** T-baseline is not accepted,
no task completion is claimed, and T-foundation must not start. The checkpoint
commit is explicitly requested by the Session 1 authorization even when a concrete
blocker remains; it does not approve migration or waive the failed evidence gate.

| Check | Observed result | Evidence / limitation |
|---|---|---|
| Original unit baseline | PASS, 277 tests, eight pre-existing warnings | `unit-before.log`; no pre-existing test failure |
| Protected bytes | PASS, 2,553 files, 21,821,925,628 bytes | Pinned baseline inventory; checked again by required gate |
| Native bundle payloads | PASS, 45 manifests and their complete payload sets | Baseline integration test; no regeneration or repair |
| Historical code | 79/92 distinct path/hash records recovered; 25 complete snapshots, 17 blocked, three suite manifests without own code | `reconstruction-local.json` |
| Current final dependency chain | All recorded source hashes recovered across 12 bundles | `source-coverage.json`; producer commit absent, never inferred |
| LightGBM 4.6.0 | PASS, exact native replay | Six models/preparers, 5,472 candidate predictions plus 1,824 persistence rows, 37 payloads, zero new fits |
| LightGBM 4.7.0 + Narwhals 2.27.1 | PASS, exact native replay | Same complete cohorts, saved decisions, metrics, draws and bytes; no tolerance relaxation |
| Synthetic comparison/guard tests | PASS, 20 tests | Missing evidence, zero selected comparisons, tampering, schema/order, masks, decisions and fit/write refusal |
| Ruff / format / mypy | PASS | Tests and shared conftest; 22 Python files |
| Markdown links / diff whitespace | PASS | Owning docs and repository link checker |
| Policy/secret scans | PASS, no matches | Explicit tracked/new file sets; ignored scientific data and installed runtime dependencies not emitted |
| Repo-only DWP conformance | PASS, 17 checks | `repo-conformance.log` |
| PLAN_030 conformance | PASS, eight checks, one semantic-review advisory | Structure/records, not acceptance of T-baseline |
| All-plan DWP conformance | FAIL, two inherited issues | PLAN_012 unresolved critical-review record; legacy initial-recognition mixed lifecycle; no historical record changed |

The replay executes hash-matched historical code from import-support revision
`268667c51839a8d653c6c9f7514a224725c6c8d8`, with each recovered file mapped to its own
Git object or preserved DWP snapshot. This is **not a recorded producer revision**:
none of the 45 native manifests records one. File hashes, including normalized
notebook-code representations, are the available historical identities. The final
replay verifies 23 actually executed scientific source files against the active
12-bundle dependency chain, with fit and publication guards and read-only I/O.

This result concerns the six frozen final packages. It does not claim replay of
every older development model or execution of the complete old orchestration graph.
In particular, live `run_final()` dependency identities must not be rewritten to
accept current contracts or requirements. Compatibility is a separate observation
against immutable saved components; the historical LightGBM 4.6 identities remain.
The dated Stage 5 dependency-reconciliation text is preserved as earlier evidence;
this migration record owns the new bounded compatibility observation.

Early diagnostic failures are retained in `baseline-check.log` and
`compatibility-first.log`: the harness initially counted only the six candidate
summary rows and omitted the two persistence rows; the 4.7 isolated runtime lacked
its newly required Narwhals dependency. Those harness/runtime issues were corrected
without changing historical files or scientific tolerances. The later run passed
both runtimes (`compatibility-final.log`); the official DWP gate is the authoritative
final acceptance attempt.

### Original source-recovery blocker and now-approved closed exceptions

These 13 missing versions belong to older bundles outside the currently consumed
final chain. Searches covered referenced Git history, all 1,450 retained Git objects,
and available DWP/scratch source snapshots. Missing bytes were not reconstructed
from prose, newer code or expected output. All affected bundles remain **KEEP**.
At the original checkpoint, exact recovery or a separate human amendment was
required. Revision 2 now supplies that bounded amendment; these exact 13 entries
remain unverified and may not be expanded. Never count unchanged payload hashes
as proof of historical code.

| Missing source path | Required SHA-256 |
|---|---|
| `notebooks/07_probability_calibration_thresholds.ipynb` | `07a6a18546be1e96636414dac4cd91b63edc16980272b5a810c8649e114e9aed` |
| `notebooks/07_probability_calibration_thresholds.ipynb` | `c1c86cf3989efb220d97b541b2d35c702aab069fb8cc6724253fc2d4d80679fb` |
| `scripts/model_assessment/proposal.py` | `f8f8d94a67a5099f4fb92797b5c4fab8074266a95426edd1207e1e766477c840` |
| `scripts/model_evaluation/contract.py` | `5f6724f5ebf5c49645ff7771121fe9beb5db80dff3f3d12752456a968b0414b7` |
| `scripts/model_evaluation/pipeline.py` | `0e332c42a9bc476a83114c15f030707b2ea96a5742451c67c8fbdb7d89bd43c1` |
| `scripts/model_evaluation/pipeline.py` | `408c91a426af57a3ab6ef36d33c0f6dbb97bb5af98355c61ceadabf04956267b` |
| `scripts/model_training/candidate_suite.py` | `893d188d336df958ac684cc5a8f4c6ca0ec5346efcfde9fddf76f9aa0416041e` |
| `scripts/model_training/loading.py` | `49c5ab5231b92e75b78cddc6053e6ce31d01a9404354f4d5bcc1587de843e2cc` |
| `scripts/model_training/metrics.py` | `c4815e8e5289428bb530d6dd2d0a5627ae2008ffb595b2ed42419c4fc5037fcc` |
| `scripts/model_training/notebook_execution.py` | `c4810716069eed67f9db0c2c6077393c519d2c7fb4fc9c109d694d546c3e56da` |
| `scripts/model_training/notebook_execution.py` | `e8381389c8ff1b8b7a5e40a660c8bc7750803da729ee981ab94357b88fd290b3` |
| `scripts/model_training/pipeline.py` | `9a0f940e5867ddffbce287ea520feeffbd0d6893cd89a71a73d202cdc4a19111` |
| `scripts/model_training/pipeline.py` | `b9838d5fb331b7ebf815a69a31eb4cbbd80535dccf1a88a837e44ba20f2cd1c2` |

### Recovery and next-session boundary

Keep `tmp/kedro-migration/` and the local PLAN_030 directory: the inventory, content
objects, per-bundle snapshots, environment copies, package metadata, diagnostics
and recipes are not in Git. `analysis_results/session1/evidence-index.json` hashes
those local records. No existing file was moved, retired or archived. All proposed
MIGRATE/UPDATE/RETIRE rows remain pending their owning task's equivalence and
consumer checks; unclassified paths remain KEEP. The broad disposition map is a
reviewable proposal, not permission for cleanup.

The local environment recipe uses the current Python 3.12.11 interpreter to create
two `venv --without-pip` environments and copies `.venv/lib/python3.12/site-packages`
into each, excluding caches. The 4.7 candidate additionally uses only the isolated
overlay installed with these pinned requirements:

```bash
TMPDIR="$PWD/tmp/kedro-migration" PIP_CACHE_DIR="$PWD/tmp/kedro-migration/pip-cache" \
  .venv/bin/python -m pip install --target tmp/kedro-migration/lightgbm47 \
  --no-deps lightgbm==4.7.0 narwhals==2.27.1
```

That command documents recovery for an absent overlay; do not reinstall into the
user runtime or overwrite an existing overlay. `runtimes.json` records every
installed distribution and the unchanged user LightGBM 4.6.0. The test harness
sets the candidate's overlay explicitly; a plain candidate interpreter without
that setting still sees the copied 4.6 package.

Under the approved revision-2 amendment, resume **only T-baseline**:

```text
/dwp-resume PLAN_030_kedro_architecture_migration
```

Re-anchor with the official ledger/context helpers, verify the preserved inventory,
verify active recovery and the closed exceptions, and run the live revision-2 gate
through `ledger.py` (the original session1 runner targets revision 1 and must not
be reused for this amendment).
A passing synthetic suite does not authorize Session 2. Do not install Kedro or
start T-foundation in this authorization. Future code moves must compare original
code against preserved snapshots while keeping scientific inputs/bundles immutable;
the Session 1 live-tree preservation test cannot simply be weakened or removed.
Independent full migration review remains the later T-final-review task, not a
claim made by this implementation checkpoint.

### Final touched-surface reconciliation

Eight tracked paths belong to Session 1: this migration record, `docs/README.md`,
`docs/TESTING_GUIDE.md`, `tests/conftest.py`, the three integration harness modules,
and `.github/workflows/ci.yml`. The only CI change adds the synthetic harness to
the existing unit-test selection; no CI dependency, permission, trigger or remote
state changes. This narrowly extends the planned surface to satisfy synthetic CI
coverage now; broader packaging/Kedro CI remains T-cleanup work. The exact combined
CI command is validated locally. No pre-existing unrelated edit existed.

The user environment preservation check compares 20,403 non-bytecode files in
site-packages against the untouched historical copy: zero differences.
The final source scan found no producer revision fields in any of the 45 manifests.

The required compound gate ran through the official DWP runner at journal sequence
4 and exited 1: **277 unit tests passed; 24 integration tests passed; one historical
source-reconstruction test failed**. The complete log is
`gates/T-baseline/004-bash--lc-python--m-pytest-tests-unit--q.log`.
The subsequent final CI selection passed **297 tests, five private tests deselected**,
with eight existing warnings (`ci-selection.log`). Ruff, format, mypy, Markdown and
conformance were run separately after the final CI/doc changes and their original
exit codes are in `supplementary-results.json`. No retry can recover missing source
bytes; the failed criterion remains open. The CI-only selection change does not
change the scientific comparison sources or evidence from gate 4, and it is not
used to turn that failed gate into accepted evidence.

## Session 2 foundation implementation and dependency authority

The used modules are `sat_dengue.__init__`, `__main__`, `settings`, `config_loader`,
`configuration`, `datasets` and `pipeline_registry`. The only implemented pipeline
is `foundation` (also the safe default), containing one configuration resolution
node. No empty scientific pipelines, starter data, generic interfaces or template
folders are created. Existing scripts and notebooks remain in place.

YAML supplies only the operational profile and tracking mode. Both merged
environment YAML and runtime parameters must select `foundation` / `disabled`;
extra keys, scientific overrides, unknown profiles and catalog replacement fail.
The input dataset reads the five fixed JSON authorities using kedro-datasets,
checks their approved byte hashes before and after loading, and collects execution
provenance. The pure resolver contains no Kedro/MLflow imports or I/O. The output
dataset publishes a content-hashed read-only snapshot atomically without replacing
an existing run. Scientific values appear only as values read from their JSON
source, never as YAML copies. Future graphs must consume resolved configuration
after snapshot publication; their scientific behavior remains unimplemented here.

`pyproject.toml` is the single declaration authority. `requirements-modeling.txt`
selects `.[modeling]`; `requirements-dev.txt` selects all validation extras and the
generated constraints. Direct pins include Python 3.12 support, Kedro 1.7.0,
kedro-datasets 9.6.0, PyYAML 6.0.3, optional MLflow 3.17.2, NumPy 2.5.4, pandas 3.0.6,
SciPy 1.18.1, scikit-learn 1.7.2, XGBoost 3.0.5, LightGBM 4.7.0,
threadpoolctl 3.7.0 and Narwhals 2.27.1. The original user environment and both
preserved 4.6/4.7 reference environments remain untouched.

Resolved constraints are generated from an isolated pip installation and identify
the source pyproject SHA-256. They are not independently edited version policy.
The following commands operate only in a new repository-local environment;
do not replace the historical environments:

```bash
python -m venv tmp/kedro-migration/foundation
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
export PIP_CACHE_DIR="$PWD/tmp/pip-cache"
export KEDRO_DISABLE_TELEMETRY=yes
export PYTEST_DEBUG_TEMPROOT="$PWD/tmp/kedro-migration"
python -m pip install -r requirements-dev.txt
python -m pip check
kedro run --pipeline=foundation
```

For an intentional dependency update, edit the canonical pyproject, resolve all
extras in a *new* isolated environment, run
`python scripts/export_kedro_constraints.py`, then validate the regenerated
constraints through a clean install. Update the engineering metadata ledger and
re-run acceptance. Do not hand-maintain divergent requirements pins. The observed
constraints target Python 3.12.11/macOS arm64; Linux CI resolves the canonical
direct pins and still requires its own platform/native validation.

PyYAML is a direct base dependency because the experiment registry resolver imports
`yaml`. PLAN_032 promotes the already-resolved 6.0.3 version to a direct pin without
changing its version or any other resolved version. The official exporter updates
the pyproject authority hash; the requirements entrypoints continue deriving all
pins from pyproject and generated constraints. The current engineering fingerprint
is updated separately from immutable original metadata.

The wheel contains the package only. Run from the repository root with external
`conf/base` and scientific JSON files available; standalone wheel installation
does not distribute data or claim scientific E2E execution. Snapshots are ignored
at `tmp/kedro-migration/runs/<run_id>/resolved.json`; each records source/config/
constraints hashes, Git revision/dirty state, package versions, authority documents
and original hashes, resolved operational values, run identity and UTC time.
No MLflow service, adapter or autologging is activated. Telemetry is explicitly
disabled in the command above and the plugin is excluded in project settings.

### Approved two-file metadata preservation

The immutable original `baseline.json` still has SHA-256
`d86338cd34dcde884e2be9d102271969d0f3b52f57b8ffdebd1829771977a5b3`.
Its original metadata is preserved in Git at
`32f96a69521c24b1f9dc2117c1a31b2851d45d72`:

| Original path | Bytes | Original SHA-256 |
| --- | ---: | --- |
| `pyproject.toml` | 1029 | `7814ce9485a506dd691d86dd8b99b6e61d94f5695579833744bdc5c7e43d8a3f` |
| `requirements-modeling.txt` | 167 | `fa26f3fc467c81c64b95d02856ff1e9f3bc06cafb1d0761e448f3b79cd46729d` |

The [engineering identity ledger](kedro-foundation-metadata.json) records those
originals and exact current fingerprints. The harness checks the fixed revision's
Git blobs against the original inventory and then the two current files against
the ledger. It rejects an expanded exception set, changed origin/revision, changed
current bytes, or any drift among the other 2,551 protected files. Exact bundle
membership and native identities remain checked. No scientific file is remapped,
no baseline is rewritten and no historical bundle becomes equivalence evidence.

### Session 2 actual dispositions

These decisions supersede only the matching pending rows for this session.
All other proposed migrations/retirements remain pending.

| Surface | Action / owner | Consumers and validation | Recovery |
| --- | --- | --- | --- |
| `pyproject.toml`, `requirements-modeling.txt` | UPDATE / T-foundation | Package/pip consumers; separate engineering identities, bootstrap/dependency tests and original-blob verification | Original Git revision and metadata ledger above |
| `requirements-dev.txt`, `docs/operations/kedro-foundation-constraints.txt`, `scripts/export_kedro_constraints.py` | CREATE / T-foundation | Full isolated environment, generated constraints and exact direct-pin agreement | Canonical pyproject; regenerate only in a validated clean environment |
| `src/sat_dengue/**`, `conf/base/**` | CREATE / T-foundation | Used configuration graph, strict loader and I/O adapters; contract/startup/wheel checks | This foundation commit; no replaced scientific source |
| `docs/operations/kedro-foundation-metadata.json` | CREATE / approved amendment | Exact original/current metadata mapping; bounded synthetic mutation tests | Original immutable baseline and pinned Git blobs |
| `tests/unit/test_repository_bootstrap.py`, `tests/contracts/test_kedro_configuration.py` | UPDATE / CREATE, T-foundation | Installed package, merged config, authority rejection, atomic snapshots, dependency and metadata boundaries | Previous bootstrap in starting HEAD; new behavioral contracts in this commit |
| `tests/integration/migration_support.py`, `tests/integration/test_migration_parity.py` | UPDATE / approved amendment | Original metadata verification plus unchanged original-file/native-bundle controls; full private and synthetic migration suites | Starting HEAD and original baseline; no scientific tolerance/exception change |
| `.github/workflows/ci.yml` | UPDATE / T-foundation | Immediately include src in Ruff/format/mypy, collect configuration contracts and fetch history for original metadata Git blobs; no private CI evidence | Starting HEAD workflow |
| `.gitignore` | UPDATE / T-foundation | Ignore used local configuration and packaging output | Starting HEAD |
| `docs/decisions/adr-0002-kedro-orchestration-boundary.md` | CREATE / T-foundation | Accepted bounded architecture and dated official sources | Linked immutable ADR-0001 |
| `docs/architecture/system-overview.md`, `docs/TESTING_GUIDE.md`, this migration record | UPDATE / respective document owner | Implemented boundaries, touched-surface gates, source/installation and preservation decisions | Starting HEAD; historical sections retained |
| `.dwp/plans/PLAN_030_kedro_architecture_migration/**` | UPDATE local / DWP helpers | Revision 3 approval, observed gates, projections and Session 2 handoff | Original revision chain/journal and preserved Session 1 evidence |
| `tmp/kedro-migration/foundation`, new run snapshots and wheel validation environments | CREATE ignored / T-foundation | New installation and startup evidence only | Session 2 receipts; preserve all original runtimes/snapshots |

No file is deleted, moved, retired or archived. ADR-0001 and pinned skills are
unchanged. Skills disposition: none; existing local DWP helpers suffice. Session 3
still needs separately authorized Stage 2/preparation migration and parity; this
foundation does not establish historical reproducibility or approve a champion.

## Stage 2 execution — Session 3

The `data` pipeline now owns Stage 2 construction. Run from the repository root
with the preserved isolated foundation environment:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
kedro run --pipeline=data --params=profile=data
```

The default remains the foundation graph. Tracking stays disabled. The data graph
publishes and reloads an explicit verified configuration snapshot before scientific
computation. Its 11 nodes resolve configuration, scope, normalize daily climate,
consolidate notifications, aggregate notification counts and climate, construct the
panel, compute targets, compute the current channel, audit readiness and assemble
provenance. Domain calculations live in `src/sat_dengue/data/`; the thin node
exports and graph assembly live in `src/sat_dengue/pipelines/data/`.

| Catalog entry | Adapter / explicit data |
| --- | --- |
| `configuration_inputs` | Existing read-only scientific JSON authorities and engineering provenance |
| `resolved_configuration` | `PublishedConfigurationDataset`: atomic snapshot, then exact-instance reload |
| `stage2_sources` | `Stage2SourcesDataset`: pinned construction contract, native execution manifest, DIVIPOLA and source identities |
| `stage2_epi_raw` | `Stage2RawCsvDataset`: ordered, read-only general/severe notification chunks |
| `stage2_climate_raw` | `Stage2RawCsvDataset`: read-only daily climate chunks |
| `stage2_consolidated` | `Stage2ConsolidatedDataset`: atomic no-replace streaming CSV, then explicit verified reload |
| `stage2_bundle` | `Stage2BundleDataset`: atomic isolated engineering bundle with verified payload membership and hashes |

Only these entries require persistence or input adapters. Intermediate scope,
frames, counts, traces, eligibility and diagnostics are explicit in-memory Kedro
outputs. Operational source paths and chunk sizes are in the validated catalog;
scientific YAML overrides remain rejected. The existing local construction JSON
is pinned and included in the resolved snapshot; it is not copied into a second
scientific authority. Missing private sources/contracts fail the data run.

Each invocation creates `tmp/kedro-migration/data-runs/<run_id>/consolidated.csv`
and a `bundle/` containing `panel.csv`, `y_history.csv`, `channel_history.csv`,
`eligibility.csv`, `readiness.json`, `construction.json`, `summary.json` and
`manifest.json`. Readiness audits development eligibility and exclusions; it does
not build Stage 3 features, fit transformations or train models. The bundle links
the original input/native-document hashes, consolidated bytes and resolved
configuration hash; its new engineering identity never replaces a native identity.
Existing bundles cannot be overwritten or selected through an implicit latest.
Partial failed runs remain isolated without a completed bundle manifest.

`data/consolidation.py` and `data/readiness.py` retain the existing calculations;
`data/validation.py` checks contract/key/month coverage and `data/workflow.py`
composes them without filesystem or framework imports. Legacy notebook audit,
reuse-verification and I/O helpers are retained in `datasets/legacy_consolidation.py`
and `datasets/legacy_readiness.py`. The old consolidation `run_pipeline` and CLI
route to the single Kedro graph; custom chunk sizes are recorded as engineering
I/O settings. `--dry-run` uses disposable isolated output storage. Historical
`--reuse-existing` remains accepted but never reuses or overwrites an old bundle.

The two original script paths are thin import/CLI adapters. Notebook 03 and
Stage 3 eligibility/fingerprint consumers still reference them; their physical
retirement belongs to T-cleanup after consumer migration. Readiness's legacy CLI
continues its historical notebook audit and can report changed engineering-code
fingerprints; it is not the new data-pipeline readiness entrypoint. No historical
notebook is re-executed to refresh that evidence. The unchanged manifest-transition,
derived-reconciliation and retired EDA scripts remain historical/test surfaces;
the data pipeline verifies current identities and reconciles newly derived counts
without replaying their old source-mutating orchestration.

Mauricio's closed Session 3 preservation amendment is recorded by local DWP 7.8.1
as revision 4, parent revision 3 `acb5cf72402b...`. Exactly
`scripts/stage2_consolidated_dataset_pipeline.py` and
`scripts/validate_stage2_training_readiness.py` have new engineering identities in
[kedro-data-identities.json](kedro-data-identities.json). Their original bytes are
verified against the immutable baseline at Git revision
`f837c9fa27dd2244307786156895794fc3158434`. This adds to the existing two dependency
metadata mappings; every other protected file and all native bundles stay intact.
No baseline, scientific rule, tolerance or closed historical source exception was
changed. The 13 exceptions and 17 KEEP / UNVERIFIED bundles remain excluded from
equivalence; full historical reproducibility is not claimed.

Validation ownership is in the [testing guide](../TESTING_GUIDE.md). Private parity
runs the actual Kedro CLI and compares every consolidated row (including raw 2013
dates), all panel/trace rows, schemas, masks, targets, current channel, source
coverage, eligibility and provenance. It covers the complete January 2020 and
cross-year cohorts. New manifests differ only as separately identified engineering
provenance. Reports and execution logs are local under PLAN_030
`analysis_results/session3/`; per-run complete comparisons are in `parity.json`.
G5 remains NOT_APPROVED, champion not_selected, zero real fits; T-preparation and
all later tasks are outside this session.

The construction record CH1 and the canonical field matrix are themselves protected
scientific baseline files. Their original bytes are retained; current engineering
execution is documented here and in the testing guide/data policy. The session's
preservation amendment authorizes no documentation exception. Existing chapter
execution references describe their preserved construction evidence, while this
section owns the new operational route. No source semantics were rewritten.

## Stage 3 execution — Session 4

Only T-preparation was authorized for this session, starting from clean
`refactor/kedro-migration` at `925a784eb20d082efd7e166ab1b6fa35c8505a57`.
The [Stage 3 owner](../product/stage-3/README.md) describes current scientific
behavior and the eight unchanged temporal windows. DEC-135 owns current G2/G3
approval; dated milestone reports and notebook bytes remain historical evidence.

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=preparation --params=profile=preparation
```

The actual seven-node graph resolves and publishes configuration, emits explicit
producer/consumer cutoffs, derives complete antecedents, audits eligibility,
selects temporal partitions, replays verified saved states and publishes the bundle.
Domain modules `contract`, `features`, `validation`, `eligibility`, `temporal`,
`preprocessing`, `serialization` and `workflow` contain no framework or filesystem
imports. The existing migrated readiness functions own policy and row selection;
independent pinned native/reference comparisons validate their complete cohorts.

| Catalog entry | Role |
| --- | --- |
| `configuration_inputs`, `parameters` | Approved JSON documents and operational `preparation` / `disabled` profile |
| `resolved_configuration` | Publish/reload this execution's verified immutable snapshot |
| `preparation_sources` | Exact Stage 2 manifest/products, typed development panel and source-year policy |
| `saved_preparers` | Explicit native development/temporal identities and all 16 saved states |
| `preparation_bundle` | Atomic immutable output under `tmp/kedro-migration/preparation-runs/<bundle-id>/` |

Native development `2ab12a21172a1cc49ff4fe713c1ff5199f1c7569354c300ed7cb2579ff0ffe24`
and temporal `a41c1252e81090eec60db2b0bc0089aeee5c96bc645ea9766225eb45e7bc1d97`
are explicitly identified in the adapter. There is no directory search or `latest`.
Stage 2 manifest identity, all source fingerprints, exact native membership and
saved-state hashes are checked before use and before publication. Code/config/Git/
runtime and original identities are bound through the resolved snapshot. New run
and bundle identities never rewrite native manifests.

The 117 engineering payloads contain all 99 original development/temporal payloads
byte for byte, plus 16 keyed split-control tables, schema and provenance. X, Y,
keys, controls, schema, transformation state and provenance remain separate.
The complete 16,948 development rows, 11,856 eligible examples per horizon, all
eight windows, 29/114-column matrices, vocabularies, parameter values and training-X
fingerprints are covered. The private CLI test denies fit calls throughout actual
Kedro execution; no real model fit or real preparer refit occurs. New fits are
exercised only by deterministic synthetic tests. Unavailable labels/origins,
2025 fitting roles, changed windows/cutoffs/order/schema/alignment/state and changed
manifest or bundle bytes are negative tests that must fail.

### Session 4 dispositions and preserved originals

The eleven modified `scripts/training_preparation/` modules remain thin import/CLI
adapters. Features/validation/preprocessing resolve to the pure package; contract,
input parsing, legacy review/execution and persistence resolve to
`datasets/legacy_preparation/`. Legacy temporal loading verifies and returns the
explicit saved native identity without fitting. Development/temporal CLIs run the
Kedro graph. Notebook 04, Stage 4 loading/candidate-selection/preparation, Stage 5
cohort/assessment/evaluation and regression tests still consume these import paths.
Their retirement belongs to T-cleanup after consumer migration. No scientific
file, notebook, saved preparer or bundle is retired here.

Local DWP 7.8.1 `/dwp-refine` helpers retain revision 4 and record the closed Session 4
preservation amendments. Revision 5 introduced the eleven script mappings; revision 6
pins final adapter bytes and the explicitly requested active Stage 3 README update,
which was also protected. The [exact mapping](kedro-preparation-identities.json)
contains only these twelve changed protected paths, with original/current sizes and
SHA-256. All originals are recoverable at initial Session 4 revision
`925a784eb20d082efd7e166ab1b6fa35c8505a57` and match unchanged `baseline.json`.
No scientific contract, acceptance criterion, tolerance, cohort, source exception or
Stage 4 scope changes. The comparator verifies these originals from Git and current
engineering identities separately; the 2,537 other physical originals and all
45 native bundles stay unchanged. The earlier four preservation mappings remain.

The [testing guide](../TESTING_GUIDE.md#kedro-stage-3-preparation-migration-session-4)
owns executable validation. Detailed logs, exact engineering identities, complete
parity receipts, actual file/consumer inventory and the Session 4 handoff remain
local under PLAN_030 `analysis_results/session4/`. Initial failed checks remain as
repair evidence. Skills disposition: no new skill or pinned skill modification.
G5 remains `NOT_APPROVED`, champion `not_selected`; the 13 source exceptions and
17 KEEP / UNVERIFIED bundles stay closed. Full historical reproducibility is not
claimed. T-training, tracking, cleanup, push, merge, release and publication were
not started by this session.

## Stage 4 execution — Session 5

The maintained model rules now live in `src/sat_dengue/model_training/` and the
shared metric owner is `src/sat_dengue/metrics.py`. Kedro orchestrates two distinct
pipelines. The default pipeline remains the configuration-only foundation.

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=training_synthetic --params=profile=training_synthetic
KEDRO_DISABLE_TELEMETRY=yes python -m kedro run --pipeline=training_replay --params=profile=training_replay
```

`training_synthetic` generates its fixture internally, checks every supplied value
against that deterministic fixture, and runs the approved bounded selection for
XGBoost, LightGBM and GAM (31 synthetic fits). It has no real source dataset input.
Its four nodes resolve configuration, generate cases, fit synthetic models and
assemble the engineering publication. Unknown profiles, families, grids and
scientific authority identities fail closed.

`training_replay` has three nodes: resolve configuration with verified native
provenance, replay saved components, and assemble publication. The
`training_sources` catalog entry loads only explicitly pinned inputs through
`datasets/training_legacy.py`. That single compatibility loader verifies native
manifest hashes, payloads and membership, loads eight development windows and
uses the existing frozen cohort builder as an I/O compatibility consumer. It
loads 40 development models (three full families and two saved XGBoost ablations)
and six frozen components. Saved preparers are transformed without refitting.
No module registry aliases or executable object snapshots are needed: XGBoost
uses native JSON, LightGBM native text, and GAM numeric JSON plus saved spline
state. Each model is serialized/restored and its complete predictions compared.

Call-level guards surround the loader and replay node, rejecting fit, _fit,
training/search and threshold-selection entrypoints even through aliases. The
private CLI acceptance guards the whole process. Real fit/search/ablation counts
are zero; the synthetic graph is the only new fitting route. The future default
E2E route must retain this inference-only boundary. Calibration, threshold policy
and final evaluation remain owned by their existing modules for T-evaluation.

`training_bundle` publishes a new, atomic, non-overwriting engineering identity
under `tmp/kedro-migration/training-runs/`. Its manifest records every payload,
configuration identity and zero real-fit counts. Provenance retains original
native manifests and payload identities, Stage 2 inputs, Stage 3 manifest and the
accepted freeze proposal. Reads require an explicit publication, exact membership
and hashes; there is no implicit latest artifact. Tracking stays disabled.

Complete comparison covers 16,720 development candidate predictions, 6,688
reference predictions, 160 candidate metric rows, 64 reference metric rows,
56 equally weighted horizon summaries, 5,472 frozen raw candidate probabilities
and 1,824 persistence predictions. Metrics retain non-interpolated AP with tied
scores, Brier, onset denominators independent of missing predictions and FAR over
issued alerts. Missing/zero support stays non-evaluable. Current domain adapters
also run independently under frozen LightGBM 4.6 and current 4.7, with exact model
roundtrips and prediction equality. Existing historical full final-output replay
remains separate evidence, including decisions and final metrics; this session
adds no final evaluation implementation or scientific selection.

The closed [training identity mapping](kedro-training-identities.json) preserves
21 original Git blobs from `4e9c47025c73297ca066a8f2874bb94046fc7e4b`, their sizes
and SHA-256, exact current adapter/README identities, and implementation owners.
The original baseline digest stays unchanged. Across Sessions 2–5, 37 original
files are preserved as verified Git blobs and separately mapped engineering
identities; the other 2,516 originals remain physically unchanged. All 2,553
original identities and all 45 native bundle identities/memberships are checked.
The 13 historical missing-source exceptions and 17 KEEP / UNVERIFIED bundles
remain excluded from equivalence; full historical reproducibility is not claimed.

The 19 `scripts/model_training/` modules and `scripts/evaluation_metrics.py`
remain thin import/CLI adapters. Notebook 05 and the candidate notebooks, model
assessment, final evaluation, their protocol/decision helpers, and existing
regression tests still consume these interfaces. Retain them until T-cleanup
verifies all consumers. Real legacy build entrypoints now return explicitly
verified frozen results; synthetic regression fixtures retain their bounded
orchestration. No notebooks, native components, evidence or scientific files are
retired. See [the testing owner](../TESTING_GUIDE.md#kedro-stage-4-model-migration-session-5)
for the exact gates. Skills disposition: none; pinned dependencies are unchanged.

G2/G3 follow DEC-135; G4 follows DEC-132. G5 remains NOT_APPROVED, champion remains
not_selected, and consumed 2025 is prohibited for training, search, tuning or
selection. This bounded session does not authorize tracking, later E2E work,
cleanup, push, merge, release or publication.

## Session 5 correction — base bootstrap and independent tests

The registry constructs all six graphs without importing model implementations.
Training node functions and dataset load/save operations defer scientific imports
until the selected training route executes. Missing modeling dependencies produce
a localized `sat-dengue-v2[modeling]` requirement; foundation, data and preparation
registration do not require that extra. Dependency declarations remain unchanged.
The single native loader and inference-only guard remain the replay boundary.

Repository-local test workspaces now use `repo_tmp_path`, which creates the ignored
parent explicitly and cleans only each test's own isolated directory. Clean archive
validation starts without `tmp/`, and base-only wheel validation executes foundation
without modeling installed. Evidence belongs to PLAN_030's local
`analysis_results/session5_correction/`. This correction refreshes engineering
validation only, retains 5/10 completed tasks and does not start T-evaluation.


## Stage 5 execution — Session 6

Only T-evaluation is authorized, starting at clean commit
`5e16166d17ed8c8db935756ac269d69de28de376` after fresh clean-archive and actual
base-only foundation guarantees passed. The [Stage 5 owner](../product/stage-5/README.md)
now documents the ten-node `evaluation_replay` and eleven-node `evaluation_synthetic`
graphs. Foundation remains default; no MLflow/tracking, E2E composition or cleanup.

The fixed final bundle `768406f872f4b859756b4603d684b965841e8c37a0f00c7f34618786dfa76e35`,
proposal `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`,
assessment `0f26a4eb97ad37075f3fba2d8da0afd55cf3450db945e8f9cb86d7dccac2f257`
and calibration/development bundle
`dcab7855d25e6982d9afb21cc4bf50831cb48095fa2d7181afe3b5661b910cfd` remain
read-only native inputs. The loader checks exact manifest/payload membership,
retained proposal/components, actual source inputs and original authorization.
New configuration/source/code identities belong only to engineering publications.

| Dataset / dependency | Owner |
| --- | --- |
| `configuration_inputs`, `parameters`, `resolved_configuration` | Existing authority input and immutable snapshot adapters |
| `evaluation_sources` | Lazy read-only `FrozenEvaluationSourcesDataset`; three explicit pinned native manifests |
| `evaluation_synthetic_sources` | Internally generated in-memory fixture; no real-source input |
| Verified proposal → cohorts/availability → raw inference → retained calibration → alerts | Pure `model_evaluation`, `model_assessment`, `final_evaluation` functions composed by `pipelines/evaluation` |
| Final metrics/uncertainty and independent development replay/assessment → frozen policy | Pure domain functions; no real fitting/search/selection or champion ranking |
| `evaluation_bundle` | Atomic immutable `EvaluationBundleDataset`, ignored `tmp/kedro-migration/evaluation-runs/` |

Shared metric equations remain in `metrics.py`. Pure functions receive their
policy explicitly; retained legacy adapters supply old default-policy I/O for
active callers. Old library real-fit routes reject consumed-evidence execution;
retained CLI adapters invoke guarded replay. Synthetic legacy regression engines
operate only in isolated fixture repositories. No global module aliases, generic
plugin framework or universal base class is introduced.

Twenty-two script paths and the active Stage 5 README receive separate engineering
identities under the [closed evaluation mapping](kedro-evaluation-identities.json).
Their original Git bytes at the initial revision remain verified against the
unchanged baseline; every earlier mapping remains closed. Current code locations
and consumers are recorded before mutation in local session6/originals-consumers.json,
and the final surface is reconciled from Git. No path is retired or notebook run.

Complete comparisons include every internal/outer development inference row,
selected calibration representation, retained threshold/alert and all final
probabilities, cohort rows, denominators, metrics, paired draws and six decisions.
The original development sigmoid bound and migration metric tolerances are
retained; no sampling or tolerance expansion. G5 NOT_APPROVED, champion not_selected,
consumed-2025 restrictions, the outer-refit/calibrator limitation, all 13 exceptions
and 17 KEEP / UNVERIFIED dispositions remain. Exact counts, hashes, observed gates,
independent preservation and limitations belong to session6/HANDOFF.md. The
[testing guide](../TESTING_GUIDE.md) owns commands. Stop before T-tracking.

## Optional local tracking — Session 7 / T-tracking

`settings.HOOKS` registers `TrackingHooks`. Disabled execution returns before any
MLflow import. Enabled evaluation/training runs use a narrow `LocalTracking` adapter;
scientific guards accept the explicit operational enabled/disabled switch without
changing scientific JSONs, metrics, thresholds, cohorts or decisions. The hook's
completion boundary reloads the published bundle; `tracking/lineage.py` independently
checks identity, complete membership, every payload and configuration before emitting
approved metadata and candidate/horizon aggregates. Native bundles remain authority.

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
# Install the existing pinned optional extra in an isolated environment if absent:
python -m pip install -e '.[dev,modeling,tracking]'
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/mlflow \
  KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=evaluation_synthetic \
  --params=profile=evaluation_synthetic,tracking=enabled
# A second permitted observability profile changes logging metadata only:
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/mlflow-diagnostic \
  SAT_DENGUE_TRACKING_PROFILE=diagnostic KEDRO_DISABLE_TELEMETRY=yes \
  kedro run --pipeline=evaluation_synthetic \
  --params=profile=evaluation_synthetic,tracking=enabled
# Explicit no-tracking requires no MLflow installation or store:
kedro run --pipeline=evaluation_synthetic \
  --params=profile=evaluation_synthetic,tracking=disabled
```

`standard` and `diagnostic` are the only observability profiles; neither changes
science. The store contains `tracking.sqlite`, `artifacts/` and generated `receipts/`.
SQLite uses an explicit local URI; no ambient remote tracking URI is used. The local
artifact repository extension stores `satlocal:/tmp/...` logical URIs, preventing
MLflow 3.17.2 from normalizing them into private absolute paths. It delegates file
persistence to MLflow's local repository, accepts only typed lineage receipts,
rejects directory uploads and requires explicit local scratch download destinations.
This single extension exists because native file-URI normalization violates the
privacy boundary; it is pinned to the installed MLflow API and has actual consumers.

Each pipeline execution has a deterministically named parent; evaluation creates six
candidate/horizon children only after independent publication verification. Runs
record code revision/dirty status, Python/environment identities, approved contract
and policy hashes, metric-definition hash, input/configuration/bundle identities,
seed, cohort/window, mode and safe native pointer. Children add family/horizon,
classification and allowlisted aggregate AP/AUROC/Brier/FAR/onset/count metrics.
Real-adjustment counters remain zero. Arbitrary fields, artifact bytes and private
paths are rejected; [security policy](../SECURITY.md#bounded-local-mlflow-tracking)
owns exclusions. Comparison of synthetic runs proves interface equivalence only.

Logging failure is explicit and retains the verified native output for recovery.
Prepublication errors and aborts cannot produce FINISHED runs. A repeated logging
request for the same verified bundle does not create another successful parent or
copy native payloads. Sequential orchestration is required; this is not a concurrent
run-locking service. Foundation remains the default with tracking disabled. Enabled
tracking currently certifies training/evaluation scientific publications; other
standalone graphs require the later complete replay publication boundary.

Consumers/dispositions: retain all existing scripts/notebooks/adapters and closed
preservation mappings. New tracking modules serve only settings/hooks and integration
tests. Current operational validators gain enabled/disabled support; configuration
negatives retain rejection of unknown tracking modes. Base bootstrap also denies
MLflow. CI installs the existing tracking extra and includes its synthetic tests;
no dependency declaration or scientific source identity is changed. Source/test
ownership is in the [testing guide](../TESTING_GUIDE.md#bounded-mlflow-tracking-session-7).
Official API references: [MLflow client](https://mlflow.org/docs/latest/api_reference/python_api/mlflow.client.html)
and [tracking concepts](https://mlflow.org/docs/latest/ml/tracking/).

## Composed replay and restart — Session 7 / T-e2e

The public command composes 37 nodes, including existing stages and explicit bridges:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
export PYTHONPATH="$PWD:$PWD/src"
export KEDRO_DISABLE_TELEMETRY=yes
kedro run --pipeline=replay
```

The default remains the small foundation graph. Selecting `replay` explicitly
binds the replay profile even with the default `profile: foundation`. No notebook
execution, copied intermediates or optional tracking service is required. Modeling
extras and the already verified local source/native inventory are required. Missing
private evidence fails closed. Complete current construction feeds preparation;
complete preparation parity precedes saved-component training replay; complete
training parity precedes frozen evaluation; complete evaluation parity precedes the
final commit. Where the existing native loaders require original preparation or
components, the bridge first verifies equality of the newly produced full cohort.
This permits their read-only reuse without introducing another scientific path.
All real stages execute under fit/refit/calibration/search/selection denial.

`pipelines/replay` expands the existing scientific graphs under four namespaces.
`datasets/replay_sources` owns stage bridges; `replay_identity` owns explicit
execution/checkpoint identities; `replay_parity` compares complete real outputs;
`replay` delegates immutable stage publication and writes the final lineage receipt.
These modules are orchestration/persistence adapters. The existing domain functions
remain independent of Kedro and MLflow. Catalog registrations are explicit and
validated; raw iterators use assign semantics instead of deep-copying generators.

The ignored `SAT_DENGUE_REPLAY_ROOT` defaults to
`tmp/kedro-migration/replay-runs`. Each execution identity binds mode, validated
operational configuration, approved contracts, every original source/native payload,
source and loaded package code, every retained Python script adapter, environment
and Git revision. A changed legitimate
code/environment/configuration identity creates a fresh execution directory and
cannot reuse old checkpoints. Changed pinned scientific contracts/inputs are
rejected. Each ordered checkpoint binds all preceding manifests, its configuration
snapshot, complete manifest/schema/membership and every payload size/SHA-256. No
implicit latest, timestamp-only matching or automatic Kedro cache is used.

Repeating the command with unchanged identities verifies and reuses completed
stages. Consolidated streaming output also has an explicit verified checkpoint.
Final publication uses atomic no-replace publication with identical-byte reuse;
all published files are immutable. Its only payloads are audit, lineage and resolved
configuration, pointing to the four verified stage publications. No native models,
CSVs or whole stage bundles are copied into this final receipt or MLflow.

A failure after computation but before final publication leaves complete stage
checkpoints and no partial final bundle. Restart verifies the full lineage and
commits once, without recomputation or synthetic refits. A missing ancestor,
altered intermediate/configuration or conflicting publication fails closed.
Uncheckpointed stage-publication failures require explicit inspection, rather than
scanning for a latest bundle. One orchestrator must run these writers sequentially;
this is not a concurrent distributed cache or a general garbage collector.

Synthetic execution is separate and consumes no private sources or native bundles:

```bash
kedro run --pipeline=replay_synthetic --params=profile=replay_synthetic
# Optional local tracking requires explicit opt-in and its optional extra:
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow \
  kedro run --pipeline=replay --params=tracking=enabled
```

The synthetic construction/preparation fixture supplies complete daily coverage and
fits only sixteen train-role fixture preparers. Training uses the existing strict
internal fixture and bounded three-family procedure. Its actual saved models and
preparers feed both horizons of the existing evaluation fixture. The T+1 fixture
models are feature-compatible interface probes for T+2, not scientific candidates.
The preparation/training/evaluation fixtures retain their deliberately separate
scientific calendars; the real path supplies full historical cohort equality.
Synthetic deterministic equality cannot substitute for the real parity gate.

Tracking hooks verify the final receipt before handing its evaluation publication
to the existing allowlisted local tracker. The parent includes only the additional
pipeline identity hash, and six candidate/horizon children. A failed final publication
cannot produce success; a verified retry cannot produce a second successful run.
Process death can still leave RUNNING metadata, which certifies nothing. Native
publications remain authoritative. Scientific limitations, consumed 2025, G5
NOT_APPROVED, champion not_selected, the 13 historical exceptions and 17 immutable
KEEP / UNVERIFIED bundles remain unchanged. Session 7 stops before cleanup or Final
Review; no runtime model approval, deployment or release follows from this replay.
