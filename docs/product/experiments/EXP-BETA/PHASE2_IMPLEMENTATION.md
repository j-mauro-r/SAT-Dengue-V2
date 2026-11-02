# EXP-BETA01 Phase 2 — independent global/local comparison

Status: **COMPLETED_WITH_LIMITATIONS**, local real-data execution on 2026-11-01.
This delivery follows the [historical Cloud entry-gate record](PHASE2.md), which
is preserved unchanged. It implements only EXP-BETA01; Beta02/03 are not started.
Scientific findings and limitations are in [RESULTS.md](RESULTS.md).

## Authority and Phase 1 gate

The available authority is [DESING.md v1.1](DESING.md), particularly §§3.4 and 4.
The requested names `DESING_Beta01.md` and `KEDRO_ARCHITECTURE_AUDIT.md` remain
absent. The checked-in design and actual graph/catalog/source code were inspected;
this does not claim inspection of the unavailable standalone audit.

**Phase 1 gate: PASS_WITH_LIMITATIONS.** Local real-data acceptance verified the
original three Stage 2 identities, the independent canonical route, the new bundle,
all 51 source columns, unique DANE/month keys, nine climate aggregates, separated
roles and origin-safe features. The source contains all 29 Meta and 47 Tolima
municipalities, each with 236 months from 2006-06 through 2026-01. Technical feature
support starts in 2011-06; national availability remains unverified. Initial
history/climate gaps do not affect the declared common Beta evaluation cohorts.

Canonical bundle:
`ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98`.
The exact canonical manifest hash and optional frozen R0 identity are pinned in
[protocol.phase2.json](protocol.phase2.json); its SHA-256 is pinned in the reader.
No latest-directory selection or automatic rebuild is supported.

The prior Phase 1 evidence remains locally ignored under
`tmp/exp-beta01-phase1-validation/2026-11-01/`; 111 focused tests passed there.
This task rechecked the actual publication before editing. The new focused
regressions also exercise Phase 1/configuration/bootstrap behavior.

## Frozen comparison

Mauricio explicitly adopted the joint ≤1 false alert/municipality-year budget and
−2 percentage-point sensitivity margin **against R0** before real Beta fitting.
[DEC-137](../../traking-concluciones.md#dec-137-adopt-exp-beta01-sensitivityload-criteria-before-fitting)
records that decision. Descriptive compliance does not establish statistical
noninferiority or superiority; no acceptance criterion was changed after results.

- One predeclared existing XGBoost configuration: 80 depth-2 trees, learning rate
  0.05, fixed seed and one CPU thread; no parameter search or early stopping.
- Both horizons require known non-excess at T. The shared historical onset helper
  labels T+1 excess and, for T+2, a non-excess→excess transition at T+2. Continuing
  outbreaks and starts already at T+1 are not new T+2 onsets.
- X uses the canonical positive allowlist. `zona_canal_t` has a fixed ordinal map;
  no encoder/scaler is fitted on future data. Source targets/evaluability/history
  traces never enter X. No imputation or canonical-table mutation occurs.
- OFF removes exactly the nine original climate columns; ON/OFF share the complete
  ON cohort, targets, temporal roles, hyperparameters and threshold-selection rule.
- For target evaluation year Y: training ends Y−4; pooled intercept calibration
  uses Y−3; regularized department adaptation uses Y−2; policy selection uses Y−1.
  Every later role embargoes origins before the preceding role's target end.
  All municipalities share those cutoffs. T+2 therefore excludes January targets
  at each role boundary. These Beta windows are explicit, not inherited from a
  historical reader. Historical R0 retains its original training procedure.
- Evaluation years are 2020, 2021, 2022 and consumed retrospective stress 2024.
  No 2024 result selects a configuration. No 2025 target/state is constructed,
  fitted, selected or evaluated by Beta. No independent confirmation is claimed.
- G0 pools Meta and Tolima. G1 is `NO_EVALUABLE`: the pinned publication has no
  compatible national observations. G0 is consequently the sole available global
  source; L1 adapts each fixed OFF/ON version separately, without choosing one on
  evaluation outcomes. There are no municipality-specific estimators.
- L1 estimates one residual log-odds intercept per department, penalty 10, with
  at least 24 adaptation rows and three observations in each outcome class.
  Insufficient support returns offset zero, preserving the global prediction.
- R0 reuses the explicitly pinned, immutable EXP03.1 M00/XGBoost onset predictions.
  Native hashes and lineage are verified. Pairing requires exact full keys and
  equal truths per horizon/year; no intersection substitutes for an unmatched
  cohort. The historical runner already fitted on pooled municipality rows;
  G0's representation/procedure is a new control, not evidence of novel pooling.

The alert threshold is selected only on past selection rows to maximize detected
onsets under the fixed budget, retaining whole score ties. Ties prefer fewer false
alerts and then the higher threshold. A no-alert policy is always feasible.
Exposure is observed eligible target-month rows / 12, consistently recomputed for
all arms, including R0. Zero-onset strata have undefined sensitivity/AP, not zero.
Department/year breakdowns remain decisive even if aggregate exposure meets budget.

## Kedro integration and local execution

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run \
  --pipeline=exp_beta01 \
  --params=profile=exp_beta01,tracking=disabled
```

The five nodes are `beta_prepare`, `beta_train`, `beta_adapt`, `beta_predict`, and
`beta_evaluate`. `exp_beta01_sources` supplies the explicitly identified canonical
bundle and optional identified R0; `exp_beta01_bundle` publishes a new destination.
Both strict catalog authorities and the operational profile recognize this route.
Enabled tracking, experiment IDs and scientific runtime overrides are rejected.
Optional estimator/metric imports occur only at execution boundaries; base
registration still works with modeling/tracking imports denied. MLflow is not used.
`replay`, `__default__`, historical profiles, preparers and contracts are unchanged.

The existing canonical immutable publisher is reused without editing it. Publication
uses atomic no-overwrite writes under `tmp/kedro-migration/exp-beta01-runs/<bundle_id>/`.
It stores native XGBoost models, calibration/adaptation states, exact feature lists,
role bounds/counts, policies, municipality-origin predictions, all metric strata,
paired contrasts, R0 comparisons, conclusions, protocol and provenance. Every
payload is bound by SHA-256/size and a content-addressed manifest. Sources and used
code are reverified before publication. New code is under `experiments/exp_beta01*`,
`datasets/exp_beta01.py` and `pipelines/exp_beta01/`; legacy scientific modules are
reused only for onset definitions, serialization and immutable publication.

## Execution, verification and delivery boundaries

Real CLI: **PASS**, 5/5 nodes. Primary publication has 16 real G0
estimator fits, 16 global intercept calibrations and 32 territorial intercepts;
L1 shares G0 models and R0 is never refitted. The complete real graph was repeated
to memory for reproducibility: all 26 payloads were byte-identical, requiring
16 additional fits, with no publication replacement. An initial publication and
its reproduction are also preserved: local review corrected the L1 verdict to
use the approved R0 reference instead of G0. All predictions, metrics, policies,
protocol and model bytes stayed identical. Total task execution was 64 estimator
fits across two publications and two reproductions, not 64 distinct scientific
candidates. No criterion or parameter changed after results. Run provenance records starting Git
revision `935a5ca` with a dirty worktree and exact hashes of every used source
file; the delivery receipt verifies correspondence with the committed code.

- PASS: 55 focused tests in the existing harness, including ten new generated-only
  Beta tests. They cover onset/continuation, embargo, target isolation, paired
  climate cohorts, shrinkage/fallback, whole-tie policy, exposure, R0 mismatch,
  graph/profile boundaries, protocol tampering, deterministic fitting and immutable
  publication/tamper rejection. Generated runs are explicitly marked synthetic
  and record zero real-model fits; no generated metric is scientific evidence.
- PASS: scoped Ruff/format and mypy; base registration without optional imports;
  independent real manifest checks, saved-native-model score replay for all 20,300
  Beta predictions and recomputation of all 120 metric strata.
- PASS: exact full R0/Beta cohort matching in all eight horizon/year cells.
- PASS: preservation of 1,039 original private/canonical/tracking/R0 files, checked
  before/after by SHA-256 and size. No historical model experiment was rerun.
- Repository-only DWP conformance: PASS, 17 checks. Scoped-plan: N/A, no plan
  created. The two inherited all-plan failures remain separate historical findings.
- Repository Markdown check: FAIL on the same eight inherited stale links to the
  moved experiment catalogue. These unrelated historical documents were not edited.
- Independent reviewer and merge approval remain pending. No merge is performed.

Private inputs, canonical publication, native model/result bundles and detailed
local verification scripts/logs remain ignored by Git. The local evidence directory
is `tmp/exp-beta01-phase2/`. GitHub receives code, protocol and aggregate reports;
updating the branch does not provision private data in Cloud. Cloud must receive
the exact canonical bundle and original source identities through an authorized
private mechanism. Missing canonical data fails closed; missing optional frozen R0
makes that comparator unavailable rather than fabricating it.
