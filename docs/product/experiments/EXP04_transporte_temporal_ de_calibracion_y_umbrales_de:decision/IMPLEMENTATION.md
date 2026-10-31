# EXP04 implementation

Status: **`EXP04_ALL_HISTORICAL_REFITS_FIXED_NOT_EXECUTED`**. Historical OOF generation is implemented; no scientific EXP04 execution or evaluation is reported. G5 remains `NOT_APPROVED`; champion remains `not_selected`.

The [scientific design](DESING.md) and [experiment scope](../experimentos.md) remain unchanged. The [baseline manifest](BASELINE_MANIFEST.json) preserves the pinned original and `M00-REPLAY-v1` identities and records the authorized EXP04 calendar. The [technical component protocol](protocol.json) remains the historical independent-component contract, not a newly frozen scientific execution protocol.

## Scope and reference

EXP04 uses consolidated retrospective SIVIGILA data, the approved canonical symptom-onset date, H5 and the exact ordered M00/EXP03 V09 predictor vector, transformations, family parameters and seed. GAM, LightGBM and XGBoost remain comparators. T+1 has one onset objective; T+2 has primary onset and a separate excess control. Development is 2020, 2021 and 2022; 2024 is stress-only after policy freeze; 2025 remains `NOT_EVALUABLE`.

Actual historical notification availability and consolidation delays belong to EXP06. OOF provenance explicitly assumes consolidated target labels at target-month end; these dates do not assert observed operational availability. Full-horizon chronological exclusion remains mandatory. No operational dates are invented.

M00 remains `VERIFIED_OBSERVABLE_REPLAY`, with absent original intermediate states `NOT_COMPARABLE`. Existing replay observables and original identities are preserved; neither M00 nor EXP03.1 is refitted, replaced or overwritten. New EXP04 historical fits have their own predictor/preparer identities. The historical `real_private_reads` discrepancy remains recorded in the manifest; this implementation does not re-audit it.

## Authorized calendar

For each evaluation year E, calibration uses exactly 12/24/36 target months ending in May of E−1. Its start is June of E−2/E−3/E−4 respectively.

| Horizon | Last calibration target | Selection issues | Selection targets | First evaluation issue | Evaluation targets |
|---|---|---|---|---|---|
| T+1 | May E−1 | June–October E−1 | July–November E−1, 5 months | December E−1 | January–December E |
| T+2 | May E−1 | June–September E−1 | August–November E−1, 4 months | December E−1 | February–December E |

Calibration freezes on May 31 and selection on November 30. Issuance dates use the existing month-start convention. The unchanged `temporal_roles` validator enforces the strict May→June and November→December transitions, disjoint target events, full horizon and `training_cutoff < forecast_issue_date`. It never accepts equality.

Historical `roles` support arrays in the manifest remain evidence about the original replay. `authorized_EXP04_roles` records the new calendar separately; new row/class counts are null until calculated from actual eligible support. No old row count is relabeled as support for a changed role.

## OOF inventory and historical refits

Every row applies independently to all four authorized cuts and all three families. Values count target-month/origin jobs requiring generation or replacement, not municipality predictions.

| Objective | Retained origin jobs | For 12 months | For 24 months | For 36 months |
|---|---|---|---|---|
| T+1 onset | 0 | 12 | 24 | 36 |
| T+2 onset | 0 | 12 | 24 | 36 |
| T+2 excess control | 0 | 12 | 24 | 36 |

The previous real attempt stopped before any refit or publication because retained scores did not exactly reproduce their saved predictors' output. Exact reuse is now disabled for all calibration origins, including the 120 previously classified as retained. All origins use historical refits; numerical validation was not relaxed. The defensive `retained_scores()` checks, including `np.array_equal`, remain intact and are never called during generation. A0 and the original M00, M00-REPLAY-v1 and EXP03.1 artifacts remain intact and are not regenerated or overwritten.

`exp04_oof.calendar` preserves the 846 jobs of the original inventory and marks all of them `historical_refit`. The 120 converted jobs retain their original reference-cell context as provenance only; their scores and fitted state come from new historical fits. Jobs remain shared across overlapping windows and, where the job context is identical, cuts. June calibration targets are excluded. Windows overlap: never sum their job counts. Every new predictor/preparer identity binds its historical job, configuration and training-key support as well as its fitted state.

Each new fit uses only eligible training targets strictly before its issuance month, starting at the frozen historical training boundary. The existing native fitter refits the preparer on those training rows only. M00 features, parameters, seed and H5/paired twelve-state eligibility remain unchanged. Missing training, class, key or window support fails explicitly; future rows never fill a gap.

Configuration-derived expectations, checked by the focused synthetic cases:

- 36 cut/family/horizon/objective groups and 108 A1/A2/A3 window cells.
- 846 unique historical predictor/preparer refits after sharing identical origins across cuts and windows.
- Zero retained origin jobs: 846 unique score-origin jobs in total, representing 1,296 group-month uses before window reuse.
- Individual prediction rows equal the sum of actual eligible municipality rows over unique jobs. Preflight reports this count as unknown until preparation; no fixed 76-municipality multiplier is used. Positives and negatives are likewise calculated, not invented.

A4/expanding remains `NOT_EVALUABLE`: its first valid OOF origin is undefined and no expanding generator is implemented. 2025 and unauthorized objectives, horizons or windows are rejected.

## Existing components and wiring

`exp04_execution.prepare` reuses EXP03.1 preparation, coverage and `paired_cohort`, including its twelve-state eligibility. `fit_native` supplies the existing family implementations and train-only preparer. Persisted replay frames use the existing lossless frame serializer. Native state uses `model.native` plus JSON preparer/feature state, under the existing protected `tmp` path and `result.json` publication convention.

Each score records municipality, origin/target, family, horizon, objective, cut/window memberships, role, training-target cutoff, predictor/preparer/configuration identities, baseline identity, unrounded raw score, truth and a content hash. Per-job records retain key hashes, observed row counts and historical-refit provenance. Publication adds a checksummed manifest and native model inventory; reload checks file membership, hashes, score identities, dates, counts, predictor/preparer identities and complete window support. No pickle, tracker or second storage service is introduced.

`policy_inputs` connects each OOF history and the shortened original raw selection/evaluation roles to the unchanged `temporal_roles` and `calibration_window` functions. `evaluate_policy` connects an explicitly predeclared policy to the existing calibrator, onset selector and frozen evaluator. Excess control stays separate and uses its frozen reference control threshold without onset-budget reselection. No window, calibrator or final composition is selected automatically. A0's original saved state/threshold remain historical reference artifacts, not silently regenerated states.

C2 runs only if existing predeclared chronological blocks pass the unchanged two-block/class-support requirement. Without that partition/support, C2 is `NOT_EVALUABLE`; no dates are moved and no partition is invented to make it pass. Isotonic support, ECE bins, nested policy selection and confirmatory settings remain subject to the design's existing pre-execution protocol. D stays unavailable without independent nested selection. This OOF delivery does not choose those scientific inputs or classify H1.

## Future commands — not executed in this delivery

Source-free preflight reports the configuration-derived calendar and counts without opening scientific inputs, replay bundles or MLflow:

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m sat_dengue.experiments.exp04_runner --dry-run
```

After separate authorization for real source access and historical fitting, generate the OOF bundle in a fresh directory:

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m sat_dengue.experiments.exp04_runner --oof-execute --output tmp/exp04-oof-NEW
```

The same entry point is wired to the existing Kedro registry, with tracking disabled:

```sh
SAT_DENGUE_EXP04_OUTPUT=tmp/exp04-oof-NEW KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipelines=exp04_oof --params=profile=exp04_oof,tracking=disabled
```

The command verifies the pinned replay and existing source admission/snapshot mechanism before preparation or fitting. It generates OOF scores and checks all policy-input windows before publication; it does not execute phases A/B/C/D or automatically fit calibrators/select policies. Full scientific policy execution still requires the existing scientific protocol freeze and separate authorization.

Read-only bundle validation, using the identity returned by publication:

```sh
.venv/bin/python -m sat_dengue.experiments.exp04_runner --validate tmp/exp04-oof-NEW --bundle-id RETURNED_BUNDLE_ID
```

The historical `--functional` mode remains a generated component fixture; `--dry-run --baseline PATH` retains the original-only baseline diagnosis. Neither substitutes for the new OOF bundle. No real pipeline, source loader, historical fit, permanent MLflow write or historical artifact modification occurred in this delivery.

## Focused validation

The five existing synthetic cases cover strict boundaries and horizons, 846 refits and zero retained jobs without duplicate origins, generation without reuse, defensive historical checks, native state persistence and integrity, and expanding/2025 rejection:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -m pytest tests/integration/test_exp04_oof.py -q
```

These cases use small generated tables and a deterministic fitter double; they do not read private data or fit native scientific models. Calibration/evaluation adapters are exercised on generated scores only. Modified-file Ruff, formatting, focused mypy and `git diff --check` supplement those five cases. No full suite or DWP check is part of this delivery.
