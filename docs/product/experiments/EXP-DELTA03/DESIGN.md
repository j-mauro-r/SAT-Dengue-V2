# EXP-DELTA03 — National climate and environmental block ablation

## State and authority

| Field | Value |
| --- | --- |
| Experiment | `EXP-DELTA03` |
| Status | `design` |
| Execution | `not_authorized` |
| Protocol | `APPROVED_FOR_PHASE2_IMPLEMENTATION`; real execution unapproved |
| Real training / calibration performed for this experiment | **0 / 0** |
| Real scientific executions / permanent MLflow writes | **0 / 0** |
| G5 / champion | `NOT_APPROVED` / `not_selected` |

Mauricio approved [proposal A](PHASE1-AUTHORIZATION.md) for consolidated-data
retrospective Phase 1 preparation on the same branch and PR #78. Historical V2
residence/INI_SIN labels, approved calendar assumptions, H5/cohorts/roles, temporal
controls,2025 exclusion and separate consumed2024 stress remain fixed. The
[handoff](PHASE1.md) owns actual matrices, reproduction and gates. Mauricio
subsequently authorized [Phase 2 implementation](PHASE2.md) and generated-only
validation under PLAN_056. The [training contract](training-contract.json) owns
the approved bundled freeze under [Phase 2 authority](PHASE2-AUTHORIZATION.md); it preserves the original Phase 1
scope. Real model/calibrator fits, scientific predictions, permanent tracking,
Phase 3 and merge remain unauthorized. The [separate annex](ANNEX.md) records prepared cohorts and pending executable inputs. Historical release/value vintages
and operational E(T) availability remain unproved; no PIT or deployment inference
may follow. The [reconciliation](SCIENTIFIC-RECONCILIATION.md) disproves aliasing
new-mart occurrence fields as historical residence counts.
2025 is already consumed and cannot provide independent confirmation. The proposed
2020/2021/2022/2024 comparisons are also consumed retrospective evidence.

The [academic contract](../contrato.md) controls H5, geography, comparators and
acceptance. [Governance](../../../governance/ai-developer-first.md),
[ADR 0001](../../../decisions/adr-0001-foundation-boundaries.md), the
[master plan](../../../roadmap/master-plan.md) and
[testing guide](../../../TESTING_GUIDE.md) retain their respective ownership. The requested legacy
`docs/governance.md` does not exist; the [documentation map](../../../README.md)
identifies the current governance owner above.

[EXP-DELTA01](../EXP-DELTA01/README.md) demonstrates threshold infeasibility and
FAR transport limits on fixed scores. [EXP-DELTA02-R1](../EXP-DELTA02-R1/PROTOCOL.md)
is a distinct G0_OFF-plus-neighbor intervention whose negative conclusion is
preserved. This experiment proposes a newly trained national climate XGBoost;
it does not extend that candidate. [EXP03](../EXP03_feature_ablation/DESIGN.md)
informs architecture (finite group matrices, common budgets, immutable bundles),
without importing its execution authorization, numerical budget or model grid.
The [protocol](protocol.draft.json) and
[matrix](ablation-matrix.draft.yml) encode the approved Phase 2 implementation
choices and remaining execution gates; filenames retain their historical identity.
They are documentary schemas, not accepted runtime configuration.

## Scientific question and estimands

Which climatic, environmental, territorial and demographic variable groups add
incremental ability to anticipate H5 onsets at T+1 and T+2 when an XGBoost model
is trained nationally and applied to Meta and Tolima, holding the observation
cohort and false-alert budget fixed?

- **Temporal generalization:** fit on earlier national observations and assess
  later target periods. Final scoring is exclusively Meta/Tolima, so this design
  cannot establish nationwide evaluation performance.
- **Geographic transfer:** primary national pooled training may include permitted
  historical Meta/Tolima rows. A secondary complete territorial holdout excludes
  both departments from every learned component and policy-development role.
- **Incremental information:** paired removal of one block from `FULL_COMMON`
  measures conditional predictive utility, not a causal effect of climate or a
  marginal variable importance. SHAP/importance cannot replace ablation.

Hypothesis H1: `FULL_COMMON` adds onset detections over existing learning
comparators at the same predeclared false-alert budget. H2: removing useful
blocks consistently reduces paired detection utility across years/departments.
H3: surface water adds information on its smaller genuinely covered population.
None is tested in this delivery. A block-level finding may motivate a separately
frozen second stage of individual ablations within material blocks; no search
across every column or evaluation-driven variable selection is authorized.

## Geography, cohort and chronology

Primary training pools all admitted national municipalities. Meta (`50`) and
Tolima (`73`) can enter only through their allowed historical training,
calibration and selection rows. No evaluation-period observation enters any of
those learned roles, including national observations outside the target region.
Evaluation is exclusively the frozen Meta/Tolima population.

For the secondary `TRANSFER_EXCLUDE_META_TOLIMA`, exclude departments 50/73
from training, fitted climatologies/transformations, calibration and threshold
selection; apply the frozen procedure to the same target evaluation rows.
Target municipalities may supply their own already available past predictor
values, never outcomes to a fitted component. This evaluates transport of the
whole procedure, including calibration/policy, and does not replace the primary
comparison. It must not use target labels to choose a transferable threshold.

H5 uses the five exact preceding same-calendar-month years, type-7 P75, and
strict excess above P75. Every historical reference used by a predictor must
already precede or equal origin T. Define `E(t)` as the evaluable H5 excess state:

- T+1 onset: `E(T)=0` and `E(T+1)=1`.
- T+2 onset: `E(T)=0`, `E(T+1)=0` and `E(T+2)=1`.

Future states are outcomes only; a continuation is never another onset. H5 is
experimental, not an externally validated epidemiological outbreak identity.
Eligible rows have known non-excess at T and an evaluable exact-calendar outcome.
The original approved D2/D3 historical calendar zeros are retained; no new-mart
absent record is automatically a zero. Missing labels,
insufficient five-year H5 history or unresolved source correspondence cannot be
imputed into cohort membership.

For target evaluation year Y, propose these **target-year** roles:

| Y | Training through | Calibration | Embargo (unused for fitting/policy) | Threshold selection | Evaluation |
| --- | --- | --- | --- | --- | --- |
| 2020 | 2016 | 2017 | 2018 | 2019 | 2020 |
| 2021 | 2017 | 2018 | 2019 | 2020 | 2021 |
| 2022 | 2018 | 2019 | 2020 | 2021 | 2022 |
| 2024 | 2020 | 2021 | 2022 | 2023 | 2024 |

In general: training through Y−4, calibration Y−3, embargo Y−2, selection Y−1,
evaluation Y. Freeze the definitive years, training start and exact original
origin embargo in the final protocol. Horizon-aware boundaries must ensure both
origins and label endpoints respect their roles; never split a horizon-crossing
row merely by origin year. The existing role/embargo owner is referenced by
[DELTA01 revision 2](../EXP-DELTA01/protocol.revision-2.json). Permitted history
from gap months may supply origin-safe features but must not become learning or
adaptation samples. Roles can overlap across separate rolling experiments;
they are not independent replications. A past evaluation year appearing in a
later predeclared role cannot drive any protocol revision.

Freeze one ordered row-key/label/cohort hash per horizon/year/role before arm
construction. All primary removal arms retain identical rows, labels and weights,
even when a feature is missing. Do not use complete-case filtering by arm.
Frozen R0/G0/G1 comparisons require exact historical key/label/role correspondence:
T+1 2,653 rows/313 onsets and T+2 2,422 rows/219 onsets are historical reconciliation
controls, **not asserted counts for the new dataset**. If correspondence fails,
block the primary learning-comparator claim until an approved matched-cohort
resolution is frozen. No silent intersection, refit or substitution of comparators.

## Source admission and metadata evidence

The immutable input is
`data/sources/dataset_v3/mart_dengue_colombia_canonico_municipio_mes_v1_1_0.csv`.
Metadata/schema-only inspection on 2026-11-05 verified:

| Property | Observed / expected |
| --- | --- |
| SHA-256 | `1b4d3873f401cb7947b49f0c26023d843823d047aeb433b175de078daa6be486` |
| Bytes | 446,274,685 |
| Rows / columns | 255,816 / 142 |
| Municipalities / months | 1,122 / 228 |
| Raw period range | `2007-01-01` to `2025-12-01` |
| Duplicate `divipola_municipio + periodo_mes` | 0 |
| Header vs ordered canonical dictionary | exact match |
| Main manifest entry hash / bytes | match |

No outcome distribution, feature association, fit, calibration or experiment was
computed. Source documentation reports NDVI missing in 169 rows; no MODIS land
cover in 13,464 rows of 2025; water out of temporal coverage in 53,856 rows of
2022–2025 and spatially unobserved in another 14,325 rows; island climate gaps;
and unresolved historical geography. Those are supplied metadata, not newly
measured scientific results.

Phase 1 must verify hash, size, manifest entry, ordered 142-column schema, unique
key, code format, monthly continuity and declared coverage. The manifest names
its original producer path `data/curated/...`; admission must explicitly bind
that entry to the byte-identical local `data/sources/dataset_v3/...` copy. Do not
assume the other 72 producer paths are locally present or verified.

The source guide says `AAAA-MM`, but actual cells are `AAAA-MM-DD` with day 01.
Parse strictly, reject invalid/non-month-start dates and normalization collisions,
then serialize canonical `YYYY-MM`. Preserve DIVIPOLA as five-character text;
validate department membership by admitted codes, never names. Derive year/month
from normalized period and reconcile source `anio`/`mes` as metadata. Year,
identifiers, quality strings, source/version tags and future outcome-availability
flags are not predictors. Use `sin(2π month/12)` and `cos(2π month/12)` as common
calendar controls for every arm, including `HISTORY`.

The canonical CSV dictionary contains inconsistent water coverage (one fraction
row says through 2024) and unrelated availability references (e.g. climate/water
fields pointing to MODIS flags). The guide, release, final report and water fact
manifest agree on **water only through 2021**. Keep these discrepancies in the
admission report and require a field-level resolved mapping before a final
protocol; never rewrite source metadata or infer feature availability from the
incorrect dictionary references.

## Authorized retrospective transformations

The [Phase 1 contract](phase1-contract.json) and
[source ledger](RETROSPECTIVE-SOURCES.json) bind the approved preparation regime.
Consolidated snapshots preserve event observation windows and training-only
references; event-time lags do not establish historical publication availability.
Original ledger statuses remain unchanged: calendar2 PIT,33 RETROSPECTIVE_ONLY,
terrain2 UNVERIFIED. Operational use would require separate released-value,
origin-state and boundary evidence. No release date is fabricated by approval.

### HISTORY and calendar controls

Use only pinned historical `dengue_notifications_count`,
`dengue_grave_notifications_count` and `total_notifications_count` at exact
lags1,2,3,12. Verify total count identity; use the original approved residence/
INI_SIN and D2/D3 calendar assumptions. The new mart epidemiological fields remain
audit-only. No contemporaneous count/result, retained count, death/incidence,
date-register, spatial-neighbor, identifier, year or target enters X. `E(T)` is
retrospective eligibility, not a contemporaneous predictor or proven operational
state. National expansion applies to main training only; main calibration,
selection and evaluation retain the exact frozen regional Meta/Tolima keys.

### Compact monthly climate

Retain these ten sources, each in one nonoverlapping block:

| Block | Sources | Proposed outputs |
| --- | --- | --- |
| `THERMAL_HUMIDITY` | `temp_media_c`, `amplitud_termica_media_c`, `vpd_medio_kpa`, `radiacion_total_mj_m2`, `viento_medio_ms` | All T−1; 3-month means for temperature, VPD, radiation, wind |
| `RAINFALL_HYDROLOGY` | `humedad_suelo_capa1_media_m3_m3`, `precipitacion_chirps_total_mm`, `precipitacion_chirps_max_diaria_mm`, `racha_seca_chirps_max_dias_promedio` | All T−1; soil 3-month mean; total-rain 3-month sum; dry-spell 3-month maximum |
| `ENSO` (common climate control) | `oni_3m_c` | Availability-safe lagged ONI; no Niño 3.4 duplicate |

For ordinary monthly x, `lag1(T)=x(T−1)`; `mean3/sum3/max3(T)` covers exactly
T−3,T−2,T−1 within municipality, with all three observed periods required.
A gap yields missing, never a shortened window, a cross-municipality shift or
zero rain. The monthly CHIRPS daily-maximum statistic remains lag1 only; it is
an areal mean of pixel daily maxima, not a municipal extreme-event maximum.
These definitions avoid ambiguity about summing daily maxima.

ONI is assigned to its **central** month: ONI(m) includes m+1. Do not treat
ONI(T−1) as ending in T−1. Approved retrospective lag is central month T−2
(window T−3…T−1). Publication delay and ERSST revision/vintage availability
remain unproved; this event-time window is not a release-time claim. No current/future
ENSO phase or persistent-event labels; no recomputation using future windows.

CHIRPS is primary. `FULL_ERA5_PRECIPITATION` replaces, never concatenates, CHIRPS
total/daily maximum/dry-spell with `precipitacion_total_mm`,
`precipitacion_max_diaria_mm`, `racha_seca_max_dias`, respectively, retaining the
same lag/window operators and soil humidity. Differences in spatial aggregation
must be disclosed. Refit both members of this secondary contrast on an identical
predeclared common-coverage subset in every role; never compare a restricted
ERA5 arm with the unrestricted primary `FULL_COMMON`.

Exclude `transpiracion_vegetacion_total_mm_signo_era5`: source metadata warns its
band is misidentified as open-water evaporation. Unit/distribution checks alone
cannot admit it without source identity resolution. Evaporation/potential
evapotranspiration are outside the initial block. A later signed-flux sensitivity
must validate source meaning, units and distribution; convert a verified upward
negative flux as `magnitude_mm = -signed_mm`, rename it explicitly and test
sign/units/conservation. Do not blindly apply absolute value or clip anomalies.

### NDVI

Retain `ndvi_medio`, `ndvi_desviacion`, `ndvi_disponible`; omit `ndvi_mediana`.
Use lag1 mean and deviation, strict mean3 of `ndvi_medio`,
`ndvi_medio(T−1) − ndvi_medio(T−2)`, and seasonal anomaly of lag1 mean relative
to the training-only municipality/calendar-month mean. Require a documented
training support rule: at least one finite training observation per group;
absent reference stays missing, with group support counts published. This is
a preparation rule, not a claim of statistical robustness or class support. In territorial holdout, held-out municipal
climatologies cannot be fitted on target data: use a training-national month
reference for **both members** of the transport contrast and label that estimand
change. Freeze support/reference choice before execution.

Use `ndvi_disponible(T−1)` as a genuine observation flag in the approved
retrospective snapshot; no historical release-time claim follows. Keep native missing values; no global interpolation or
imputation. NDVI is already scaled in the mart; do not multiply again by 0.0001.
Removing NDVI removes all descendants and its availability flag.

### Static terrain

Use only `altitud_media_m` and `pendiente_media_grados`; record SRTM source,
static nature, geometry vintage and spatial lineage. Omit medians, slope-fraction
thresholds and redundant statistics. Static measurement does not prove historical
boundary correspondence. Approval permits the fixed retrospective measurement/
current geometry only; the historical correspondence limitation remains explicit.

### Demography (secondary interpretation)

Propose `log1p(poblacion_total)`,
`log1p(densidad_poblacional_hab_km2)`, `porcentaje_urbanizacion`,
`porcentaje_0_4`, `porcentaje_65_mas`. Preserve missing; reject invalid negative
population/density rather than transform silently. Do not add equivalent age
counts or complementary percentages. Demographic effects are secondary even
when the admitted block is in the proposed full vector.

Use the exact previous calendar observation year from the admitted consolidated
snapshot. Verify within-year consistency and use its December row; a missing year
stays missing, with no older-year fallback. This explicitly approved retrospective
join is not a historical published projection vintage. Density's MGN2021 area
remains a boundary limitation. Keep native missing values and unchanged cohorts.

### Annual MODIS land cover

Audit five parts: natural vegetation (forest+shrub+savanna/grassland+wetland),
agriculture (crop), urban, bare/other (bare soil+snow/ice+MODIS water), and the
separate mixed crop/natural mosaic. The five parts close to100 within1e-4 percentage
points; centered rank4 and many exact zeros preclude choosing log-ratios without
a material zero-handling decision. **Approved predictors are natural, agriculture,
urban and mosaic; bare/other is the omitted reference.** No mosaic redistribution,
pseudocount or monthly-JRC equivalence is implied.

Use the exact previous complete observation year, with native missing aggregates,
no missing-year fallback and no2025 imputation. This is consolidated retrospective
use; historical release/value availability remains unverified. All five audit
parts and source composition diagnostics remain preserved in the reconciliation.

### Surface water (retained secondary contrast)

Retain the block for a specific covered-period experiment. JRC monthly coverage
ends in **2021**. Never impute, extrapolate or fill a later source observation.
A January2022 origin may use the genuine December2021 lagged observation.
`fuera_cobertura_temporal` and structural availability flags cannot be predictors
or hidden year encodings. `FULL_COMMON` never depends on water for eligibility.

Propose only `fraccion_agua_superficial_pct_area_observada(T−1)` as the water
predictor; retain `area_agua_superficial_m2`, `area_observada_m2` and coverage
states for quality control, not additional redundant inputs. Require observed
area >0 and genuine water observation (zero observed water is valid). Use an
genuine event-time lag under the approved retrospective regime; historical
release/vintage evidence remains unproved.

Contrast `FULL_COMMON` versus `FULL_COMMON + SURFACE_WATER`
(`FULL_PLUS_SURFACE_WATER`). Restrict **both** models' training, calibration,
selection and evaluation to the same genuinely covered feature rows, target
periods and observation keys. Prepared water pairs have support in2020/2021 and
partial2022 (including January origins with December2021 observations). Both2024
water comparisons are explicitly unavailable; the main2024 stress fold remains.
No missing water metrics are emitted as zero. A future model phase must separately
freeze class/calibration support and refit both restricted arms under authorization.
Water results remain secondary and cannot substitute for general contract results.

## Frozen missingness safeguards

No global imputation. XGBoost uses native missing-value routing. Keep observation
availability flags only with legitimate, origin-safe meaning; prohibit structural
coverage/year, source-version and future-label flags. Never impute epidemiological
outcomes or out-of-coverage water. A separately approved dense alternative model
must fit its imputer on training only. No dense alternative is included here.
Missing features do not change the primary cohort by arm; missing required labels
or historical comparator parity block the affected comparison. Report coverage
and missingness by role/year/department without optimizing exclusions.

## Proposed Kedro architecture

These pipeline identifiers were proposed in the original design. Phase 1 now
registers preflight, preparation and synthetic graphs as documented in the
[handoff](PHASE1.md); the real training executor remains unregistered:

| Pipeline | Future responsibility | Boundary |
| --- | --- | --- |
| `exp_delta03_preflight` | Source identity/schema/role/availability and authorization checks | No model construction, fit, reservation or tracking write |
| `exp_delta03_synthetic` | Generated-only feature, role, tie, leakage, pairing and publisher checks | Isolated temporary artifacts/store; no real data or permanent experiment |
| `exp_delta03` | Frozen real procedure after all gates and explicit authorization | Manual scientific execution by Mauricio only |

Conceptual dependency graph (feature builders are independent branches after
normalization; this list does not require a long chain of dependent feature nodes):

```text
verificar_fuente → normalizar_llaves_y_calendario
  ├→ construir_historia_epidemiologica
  ├→ construir_bloque_climatico
  ├→ construir_bloque_ndvi
  ├→ construir_terreno
  ├→ construir_demografia
  ├→ construir_cobertura_suelo
  └→ construir_agua_superficial
→ ensamblar_matriz_comun → generar_roles_temporales
→ entrenar_variantes_ablation → calibrar_probabilidades
→ seleccionar_umbrales → evaluar_contrato → publicar_bundle → registrar_mlflow
```

Role metadata must be available to feature builders before fitting any training
statistic, even though the assembled role audit is shown later. Separate pure
`fit_reference(training)` from `transform(history, reference, origin)`; a full
matrix must never be globally transformed before splitting learned statistics.

Keep domain functions pure and Kedro-independent, nodes small/cohesive/reusable,
catalog and profile/matrix configuration separate from code, one implementation
per transformation, SOLID and DRY. Variants select registered blocks and descendants;
do not duplicate pipelines per arm. No scientific logic in hooks or datasets;
I/O adapters only validate/read/write typed artifacts. No versioned absolute paths.
Publish content-addressed bundles atomically with no overwrite, including input,
normalized/prepared output, protocol/matrix/code/config/runtime/cohort/model/
calibrator/policy hashes and lineage. MLflow is an isolated aggregate-only mirror
of a verified native bundle; no private keys, row predictions or paths are logged.
No tracking writes occur in this documentation session.

## Model, ablation and policy design

The experimental base is **national climate XGBoost**, not G0_OFF. Propose one
binary classifier per horizon targeting its exact H5 onset label (`onset_T1` or
`onset_T2` above), not monthly excess; preserve the approved historical target assignment.
The approved implementation fixes `objective=binary:logistic`, `n_estimators=80`, `max_depth=2`,
`learning_rate=0.05`, `tree_method=hist`, `random_state=1729`, `n_jobs=1`.
No hyperparameter search, early stopping on evaluation or arm-specific parameters.
All arms use exactly the same explicit estimator configuration and row weights;
All explicit defaults and row-weight rules are frozen in training-contract.json;
exact dependency/runtime versions remain part of separate future execution admission. Each arm/horizon/year
is recalibrated on its own authorized calibration partition only. Calibration uses the approved regularized intercept, penalty1 and minimum one
observation per class. No evaluation-dependent calibration or tuning is permitted.

The [matrix](ablation-matrix.draft.yml) defines 8 common-cohort arms (`HISTORY`,
`FULL_COMMON` and six removals), plus three secondary sensitivities: restricted
water pair, restricted ERA5 precipitation pair and territorial holdout with its
matched FULL reference. `ENSO` and calendar stay common within the six removals;
`HISTORY` keeps only history/calendar, so full-vs-history measures all additions
jointly. Thermal removal also removes its radiation/wind descendants; rainfall
removal includes soil humidity. These broad block labels describe combined tests,
not isolated mechanisms.

For each removal measure arm minus `FULL_COMMON` at the **same false-onset-alert
budget**, with eligible municipality-years `D = eligible rows / 12` and common
selection limit `floor(B × D)`. The approved numerical **B=1** is frozen for implementation under
PHASE2-AUTHORIZATION.md. Maximize selection
onset detections subject to that limit; keep full score ties (`score >= threshold`),
then fewer false onset alerts, fewer total alerts, higher threshold. The approved
training contract fixes support, null no-alert and no-selection-positive handling. FAR/precision with zero
alerts are undefined, never zero. Unsupported cells cannot be pooled away.

Thresholds are selected only in Y−1, persisted before evaluation, and never
retuned on Y. A common development budget does **not** guarantee identical
realized false alerts in Y. Report both realized load differences and detection
differences. Do not force equal evaluation counts by label-based reselection or
claim equal realized load when it diverges. A secondary diagnostic at matched
realized load would need a separately labeled, predeclared descriptive procedure;
it cannot choose thresholds or establish primary success.

Mandatory comparators remain CHANNEL, PERSISTENCE, frozen R0, G0_OFF, G0_ON and
G1. G0_OFF is only a contractual comparator. Preserve historical predictions and
policies; no refits/recalibrations. Verify the inherited learning policies use the
same B, denominator and selection population before claiming budget-matched gains.
If they do not, retain their original academic comparison and mark the
budget-matched learning claim blocked pending an explicitly frozen score-only
selection procedure with admitted Y−1 scores. Never assert frozen alerts share
an arbitrary new budget. CHANNEL and PERSISTENCE keep their contractual rules:
CHANNEL compares known cases(T) with origin-safe H5 P75 for the target month;
PERSISTENCE projects known E(T), hence no alerts on this non-excess risk set.
No threshold optimization of these two rules.

## Evaluation and success

For each horizon, year, department and year×department, plus complete pooled
horizon results, report onset sensitivity; detected/missed/observed onsets;
paired gained/lost/shared onsets; onset precision; academic excess-FAR; false
excess and false onset alert counts; false onset alerts per eligible municipality-
year; emitted alerts; AP and Brier for onset probabilities; reliability/calibration
summaries; feature/cohort coverage; class support and all undefined denominators.
The [experiment synthesis](../experimentos.md) also requires transmission-profile
reporting. Retain secondary descriptive detection/load/coverage results by the
inherited transmission profile, using a classification identity frozen from
permitted historical data before evaluation. Freeze its vintage, mapping and
training-only derivation if needed; no evaluation-defined profiles, new profile
models or profile-specific thresholds. If historical profile correspondence is
unavailable, report that analysis as pending/non-evaluable without filtering the
primary cohort or inventing classifications.

Deterministic comparator AP/Brier need not be invented. Academic FAR is
`count(alert and target excess=0) / count(alert)`, distinct from false onset
alerts and from FPR. Retain evaluation excess states separately from onset labels.

Use paired municipality resampling and temporal blocks, shared across compared
arms, to quantify detection/load/AP/Brier differences. Freeze block length,
replicate count, clustering and interval method before results. Preserve serial
and within-municipality dependence; disclose sparse support, rolling-window
overlap and multiple exploratory contrasts. No independent-confirmation or
statistical-superiority claim follows merely from a positive point estimate.

For **each T+1 and T+2**, preserve simultaneous contractual A/B/C:

1. More detected onsets than CHANNEL.
2. More detected onsets than PERSISTENCE.
3. Excess-FAR increase over CHANNEL no greater than **0.05 absolute** (five
   percentage points), using evaluation FAR for final acceptance only.

Experimental utility additionally requires detections over the existing learning
comparators under a verified common budget, consistent evidence across years and
both departments, and honest realized-load differences. A block adds value when
removing it consistently reduces paired utility. The approved analysis is
descriptive only; no formal superiority/materiality or champion conclusion. The water result applies only
to its coverage population. Failed/undefined required cells remain visible;
partial pooling cannot replace the complete primary horizon. No result selects
a champion, grants G5, proves prospective availability or authorizes deployment.

## Future implementation in three separately authorized phases

| Phase | Future scope | Exit condition |
| --- | --- | --- |
| **1 — Data admission and preparation** | Freeze/admit the dataset and feature mapping; Kedro catalog; normalization; origin-safe transformations/blocks; schema, key, coverage and leakage checks; H5/frozen-cohort parity | Reproducible prepared matrices and identities, demonstrated absence of future predictor information, **zero real fits**. Approved retrospective provenance, exact parity and reproduced matrices required; no operational PIT claim |
| **2 — Training and ablation implementation** | Implement national XGBoost and matrix; separated training/calibration/selection; generated synthetic/integration checks; isolated temporary MLflow tracking | Technically ready pipeline; **zero permanent scientific execution before explicit authorization**; counts of models/calibrators/runs documented; generated fits cannot masquerade as scientific evidence |
| **3 — Scientific execution and evaluation** | Freeze runtime; preflight; independent review; authorization bound to clean commit, final protocol/matrix, input hashes, environment and isolated MLflow store; **manual execution by Mauricio**; contract evaluation and traceable MLflow registration; then conclusions/registry updates | Reproducible traceable results; scientific conclusions separated from technical results. G5/champion unchanged unless a later independent human decision changes them |

Only the approved retrospective Phase 1 preparation is exercised; actual matrix
and gate evidence is recorded in the handoff. No predictive results are produced. Phase 2 must not use the real dataset as a
synthetic fixture. Phase 3 cannot reuse another experiment's authorization/store
identity or treat a preflight receipt as execution approval.

Historical initial estimate (water2020/2021 only), **not the current prepared-view
count, a reservation or an execution budget**:
8 common arms × 4 years × 2 horizons = 64 model fits and 64 calibrators;
water pair × 2 years × 2 horizons = 8+8; ERA5 pair × 4×2 = 16+16; territorial
holdout plus matched national-reference pair × 4×2 = 16+16. Total up to
**104 real predictors and 104 calibrators**, with zero comparator refits.
A proposed one-parent/one-child-per-cell tracking layout would yield up to
105 runs, without separate calibrator runs. Identical source/config/cohort cells
may be deduplicated only by identity, never by favorable results. All counts,
calibration multiplicity and tracking shape must be recalculated/frozen in Phase 2
after definitive years, support and reference choices; zero are created here.
This paragraph preserves the historical initial104/105 estimate. The verified
Phase 2 derivation supersedes it:108 supported future predictors/calibrators,
four unsupported water2024 descriptors and109 parent/child runs; see
[annex inventory](ANNEX-PREPARATION.json).

## Pending decisions before final protocol or execution

| Decision | Required resolution |
| --- | --- |
| Historical source/H5/cohorts | Resolved for preparation through proposal A and exact native parity; preserve the pinned sources and original admission masks |
| Operational availability | Unproved; proposal A permits retrospective preparation only. Any operational PIT/deployment inference requires new evidence and authority |
| Retrospective block admission | Resolved for preparation: FULL_COMMON48, HISTORY14, four-part MODIS; preserve missingness and closed selectors |
| Years and pair populations | Phase 1 descriptors frozen for 2020/2021/2022/2024; executable national coverage-restricted annex inputs remain pending |
| Model/calibration | APPROVED_FOR_PHASE2_IMPLEMENTATION in training-contract.json; pin exact future dependency/runtime versions before Phase 3 |
| Alert policy/comparators | B=1, ties/support/no-alert handling approved; exact comparator joins and verified budget equivalence remain required |
| Statistical interpretation | Paired municipality/episode-connected annual-block uncertainty approved; descriptive only,2024 separate,no IID rows; missing historical profile mapping remains non-evaluable |
| Composition/references | Resolved for preparation: separate mosaic, bare/other reference, finite training-group support, matched national-month transfer references; future modeling support remains pending |
| Publication/tracking | Implemented native/isolated tracking;108 supported cells/109 runs derived; exact future commit/runtime/store/resource identity requires separate approval |
| Authority | Phase 2 implementation freeze approved; independent final review/CI and separate exact-identity Phase 3 grant remain required |

The Phase 2 approval is explicit and bounded by PHASE2-AUTHORIZATION.md. Missing
scientific inputs and future execution authority are never inferred from technical
validation. No conclusions, real execution, permanent tracking or merge follows.
