# EXP04 implementation

The [scientific design](DESING.md) owns intent. The [technical protocol](protocol.json) records the independent implementation boundary. It is not a frozen scientific execution protocol: the [baseline manifest](BASELINE_MANIFEST.json) now resolves the observable M00 reference as `M00-REPLAY-v1`, while temporal/OOF evaluability and scientific inputs remain unresolved. `G5: NOT_APPROVED`; `champion: not_selected`.

M00 of EXP03.1 is mandatory, including its exact V09 predictors, fixed family parameters, H5 labels and paired twelve-state cohort. No M01/M02 feature enters EXP04. Development is retrospective 2020–2022; 2024 is retrospective stress after policy freeze; 2025 is `NOT_EVALUABLE`.

The user's exposure decision preserves the original M00 monitored-month denominator for historical reproduction. EXP04's primary rate uses the same eligible observable municipality-month keys/12 for every compared arm. These rates are named and reported separately. Incompatible support or exposure makes a contrast `NOT_EVALUABLE`.

Independent components are implemented incrementally under local PLAN_052. Exactly five substantive controls cover design, baseline integrity, chronology, functional execution and reproducibility. Functional/generated results cannot validate H1/H1a/H1b/H1c. Scientific execution remains disabled while its prerequisites are unresolved.

## Execution

Use the existing Kedro mechanism with explicit tracking-disabled technical profiles:

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipelines=exp04_preflight --params=profile=exp04_preflight,tracking=disabled
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipelines=exp04_functional --params=profile=exp04_functional,tracking=disabled
```

The Kedro outputs are in-memory `exp04_preflight_result` and `exp04_functional_result`. No new source dataset, storage service, tracking backend or catalog layer is introduced. Profiles must match the pipeline; enabled tracking and a registered experiment ID are rejected before tracker construction. The historical pipelines retain their bindings. EXP04's real scientific pipeline is intentionally unavailable while temporal/OOF support and the scientific protocol are unresolved.

For inspectable local JSON output, the same runner exposes:

```sh
.venv/bin/python -m sat_dengue.experiments.exp04_runner --dry-run --output tmp/exp04-readiness
.venv/bin/python -m sat_dengue.experiments.exp04_runner --functional --output tmp/exp04-functional
```

Choose a new output directory each time. Existing directories, external paths and symlinks are rejected. The unchanged original-only dry-run returns `BLOCKED_BASELINE`/`BLOCKED_DESIGN` and per-arm/cut `NOT_EVALUABLE` without fitting, calibrating or selecting thresholds; it does not consume the new replay reference. The updated manifest separately records `VERIFIED_OBSERVABLE_REPLAY` for M00 and `BLOCKED_TEMPORAL_OOF` for EXP04. A nonzero exception reports altered identities or invalid input; a successfully reported blocked readiness status is not a scientific PASS.

The generated fixture exercises both horizons and all independent A/B/C factors over fixed input scores. Its A0/B0/C0 controls are explicitly generated fixtures, **not reproduced M00**. It uses a single generated score family; it does not claim GAM/LightGBM/XGBoost results. Isotonic minimum support, dates, ECE bins, fixed diagnostic threshold and known synthetic monitoring exposure are labeled functional-fixture settings, not approved scientific choices. D remains `NOT_EVALUABLE` without independent nested selection. The excess table is a separate fixed-threshold structural diagnostic with no onset-budget selection.

`result.json` contains unrounded predictions, date provenance, input/code/configuration/environment hashes, frozen calibrator and threshold records, paired contrasts, year/department metrics, reliability bins, score distributions and explicit unavailable uncertainty/profile/dispersion states. It retains both named exposure rates. Outputs remain ignored under `tmp/`; they are never historical experiment evidence or MLflow results.

## Reference reconstruction

`exp04_baseline.audit_baseline` checks the exact EXP03.1 bundle and manifest hashes, canonical M00 predictor order, configuration, seed and temporal roles. It opens existing result artifacts read-only and never reads private source datasets. The bundle contains final calibrated evaluation probabilities and alerts, but no original fitted predictor/preparer, calibrator coefficients, or raw calibration/selection/evaluation scores. The EXP03.1 runner fitted these states locally without persisting them. M00's reuse decision is `refitted`; EXP03 native models cannot therefore be silently substituted.

Identity with absent original intermediate states remains `NOT_COMPARABLE`. The completed EXP03.1 replay supplies fitted predictor/preparer/calibrator states and raw scores, with `EXACT_OBSERVABLE_REPLAY` over all 96 cells and 60,207 predictions, including 36 M00 cells. Configuration/seed determinism alone cannot prove equality with an unsaved fitted state; inverse calibration is not used. No fit was executed for this documentary update. The `real_private_reads` discrepancy (8 versus 1) remains unresolved.

The [baseline manifest](BASELINE_MANIFEST.json) records the verified `M00-REPLAY-v1` identity, hashes and original-state limitations. M00 is `VERIFIED_OBSERVABLE_REPLAY`; EXP04 remains `BLOCKED_TEMPORAL_OOF`. The technical protocol retains the original scientific identity and its conditional equivalence requirement; its generated contract and original-only diagnostic are unchanged by this documentary update.

The original parent tracking metadata also lacks an exact numerical runtime/native-library environment identity. Pinned dependency requirements and unchanged source parameters do not establish the original installed numerical environment. It remains `NOT_COMPARABLE`; the replay environment is recorded separately, and this historical limitation does not block the verified observable reference.

`paired_support` rejects changed truth or differing eligible keys with `NOT_EVALUABLE` and reports intersection support. `common_exposure` counts the supplied complete eligible observable municipality-month cohort/12, independent of alerts and scores. No fixed 76-municipality denominator is used. The historical M00 denominator is retained separately and never used to establish an EXP04 primary improvement.

## Independent temporal policies

`exp04.temporal_roles` requires explicit forecast/target/maturity dates and the latest training-label availability cutoff. It checks full T+1/T+2 month offsets, genuinely out-of-sample chronology, disjoint target-event roles, mature calibration/selection labels, and decision freeze before every evaluation issue date. Stress 2024 cannot fit/select and 2025 is rejected. Supplied provenance must ultimately be verified against persisted evidence; passing date arithmetic does not authenticate missing label-maturity or training-label availability dates.

`calibration_window` selects contiguous mature 12/24/36-month or expanding histories with observed positive/negative support. Gaps return `NOT_EVALUABLE`; no future months are borrowed. `fit_calibrator` reuses the original fixed sigmoid implementation; isotonic uses installed sklearn and requires an explicitly supplied minimum class support, otherwise `NOT_EVALUABLE`. Identity calibration is diagnostic-only for probability scores. No fallback is fitted automatically.

`threshold_policy` implements C0's existing whole-tie selector and C1 on common exposure; they coincide when all inputs match, which is an expected control rather than a claimed improvement. C2 requires at least two noninterleaved chronological blocks with both classes and enforces the budget in each block before maximizing joint detections. Null is the no-alert extreme. A0 historical replay uses the saved original threshold without reselection. These onset selectors reject excess-control use.

`evaluate_frozen` applies supplied state and threshold without fitting, retains full probabilities, uses common exposure for the primary rate and reports historical exposure/rate separately. It reuses existing AP/Brier/ECE/reliability and classification metrics, reports municipal macro sensitivity and false alerts by class, and keeps uncertainty `UNAVAILABLE` without an approved resampling protocol. Excess metrics have their own positives and no onset-budget criterion. Undefined scientific settings remain explicit; no confirmatory H1 classification is generated.

## Reused, adapted and new components

| Disposition | Component | EXP04 role |
|---|---|---|
| REUSE_UNCHANGED | EXP03 canonical V09 protocol/family parameters/seed | Exact baseline configuration; no new predictors or native-family tuning |
| REUSE_UNCHANGED | EXP03 native sigmoid and EXP03.1 metrics/selector | Fixed logistic correction, C0/C1 whole ties, AP/Brier/ECE and reliability |
| ADAPT | Existing Kedro registry/configuration/tracking hook | Two small technical bindings with tracking disabled and lazy scientific imports |
| ADAPT | Existing metric interfaces | Explicit common/historical exposure, municipal macro sensitivity and separate objective labels |
| NEW | EXP04 baseline audit | Pin original bundle/manifest and report reconstruction dependencies without refitting |
| NEW | EXP04 policy functions | Mature exact windows, chronology, isotonic adapter, C2 block constraint and paired-support rejection |
| NEW | EXP04 functional runner | Deterministic generated fixture, provenance and structured local output |

No historical experiment implementation or bundle is modified. Cohort construction, predictor fitting and original model reload are not duplicated: scientific integration with the replay artifacts remains unimplemented and gated by temporal/OOF evidence and the scientific protocol.

## Remaining scientific dependencies

Replay raw scores and fitted states are now preserved; absent original intermediates remain `NOT_COMPARABLE`. Nested chronological roles and mature prior OOF history still need verified support. The manifest's read-only assessment finds only 6 calibration months for T+1 and 5 for T+2 per predictor: 12/24/36-month windows are `NOT_EVALUABLE`, and expanding-window temporal evaluability is `UNKNOWN` because maturity and freeze chronology are unverified. Selection/evaluation roles and different predictor snapshots were not pooled. Territorial loss tolerance, material FA-increase definition, isotonic support and resampling settings need a pre-execution scientific protocol. Confirmatory H1 and D therefore remain unavailable. A future real execution needs registration, source/authorization binding and a separately frozen protocol; these are not implied by a functional PASS or observable replay.
