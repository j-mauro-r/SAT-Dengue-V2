# EDA-EXP02 — Phase A: anticipatory signal and source audit

**Audit date: 2026-11-03. Phase A: `READY_WITH_LIMITATIONS`.**
The [inventory of 45 signals and prerequisites](SIGNAL_INVENTORY.csv) and
[conclusions](PHASE_A_CONCLUSIONS.md) identify two conditional opportunities for
Phase B design. Neither has demonstrated incremental predictive value. No Phase B,
EXP-DELTA02, feature construction, statistical association analysis or training
was started.

## Objective and boundaries

Which epidemiological, spatial, climatic or territorial information observed
before an outbreak onset could add information beyond SAT-Dengue's investigated
inputs? This audit establishes source presence, historical coverage, prior work,
representation overlap and timing constraints. It does not estimate associations,
effects, predictive gains or new policies.

The audit covers the frozen **1,122-territory DIVIPOLA inventory**. The academic
evaluation population remains **76 municipalities: Meta 29 and Tolima 47**, under
the [academic contract](../contrato.md). Current inventory membership does not
certify historical boundaries or identical territorial status throughout history.
H5 remains an experimental onset definition, G5 `NOT_APPROVED`, and
`champion: not_selected`.

PR [#74](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/74) was verified `MERGED`
into `main` on 2026-11-03 (merge commit
`75294af0899665ebb54bb422267beaabec14e6f3`). `main` was fetched and fast-forward
checked with a clean worktree; `analysis/EDA-EXP02` was created at that commit.
The three audit deliverables are implemented directly; no DWP execution plan or
stage-gate change is required. Mauricio additionally authorized only the new
directory entry in `docs/operations/repository-disposition.json` so the existing
repository structure check can pass. Existing entries and tests are unchanged.

## Audit method

1. Read current contracts and published conclusions before inspecting data.
2. Trace signal families to frozen feature inventories; consult only calculation
   code needed to distinguish existing formulas and timing.
3. Read explicitly identified local manifests, dictionaries and coverage reports.
   Verify national/regional publication payload hashes, then inspect their CSVs
   only for keys, periods, missingness and existing eligibility masks. Do not
   derive proposed episode or spatial variables.
4. Compare source-record presence with the complete calendar; a source zero is
   not proof of active negative reporting. Separate retrospective calculation
   safety from demonstrated operational availability.
5. Inspect official external documentation only. External datasets, geometries
   and municipal profile memberships were not downloaded or joined.
6. Retain each opportunity's evidence, novelty, support gap and stop conditions.
   Use categorical decisions, without invented scores or gain estimates.

Only aggregates enter this directory. Municipal rows, case records, identifiers,
scores and private source exports remain local. Temporary audit receipts are
under ignored `tmp/eda-exp02/`; they are disposable, not a new analysis system.

## Reviewed internal sources

Source IDs below are also used in the CSV. Paths to private files are locators,
not public download links. Prior conclusions were read as evidence; their
experiments and the EDA notebook were not rerun.

| ID | Source and use |
| --- | --- |
| I01 | [Academic contract](../contrato.md): onset/excess distinction, cohorts, T+1/T+2, consumed years and timing |
| I02 | [EDA-EXP01 README](../EDA-EXP01/README.md), [findings](../EDA-EXP01/FINDINGS.md), [conclusions](../EDA-EXP01/CONCLUSIONS.md): all seven chapters, including municipal support and climate |
| I03 | [EXP03 frozen matrix](../EXP03_feature_ablation/ablation-matrix.frozen.yml), [conclusions](../EXP03_feature_ablation/CONCLUSIONS.md), `src/sat_dengue/experiments/exp03_features.py`: lags, current/lagged means and differences, channel, ratios and climate |
| I04 | [EXP03.1 design](../EXP03.1_add_pass_info/DESIGN.md), [conclusions](../EXP03.1_add_pass_info/CONCLUSIONS.md), `src/sat_dengue/experiments/exp03_1_features.py`: six-month state counts and semester changes |
| I05 | [EXP04 conclusions](../EXP04_transporte_temporal_%20de_calibracion_y_umbrales_de%3Adecision/CONCLUSIONS.md): calibration/decision transport and detection cost |
| I06 | [BETA01 conclusions](../EXP-BETA01/CONCLUSIONS.md), [regional canonical contract](../EXP-BETA01/canonical_model_table_v1.json): regional inputs and departmental adaptation |
| I07 | [BETA01 V2 conclusions](../EXP-BETA01-V2/CONCLUSIONS.md): national training expansion with unchanged features, not spatial-neighbor features |
| I08 | [BETA02 conclusions](../EXP-BETA02/CONCLUSIONS.md): notification count distributions, onset versus marginal excess |
| I09 | [DELTA01 conclusions](../EXP-DELTA01/CONCLUSIONS.md), [results](../EXP-DELTA01/RESULTS.md): frozen-score policy feasibility and transport |
| I10 | [Benchmark conclusions](../benchmark/CONCLUSIONS.md), [diagnosis](../benchmark/diagnostico/ANALYSIS.md), [hypotheses](../benchmark/diagnostico/HYPOTHESES.md): shared errors and prior research questions |
| I11 | [National table owner](../../../data/canonical-national-table.md), [contract](../../../data/canonical_model_table_national_v1.json), [acceptance](../../../data/canonical-national-validation.md): source chronology, approved zero rule and eligibility |
| I12 | [Stage 2 construction](../../stage-2/CH1-dataset-construction-candidate.md), [69-field dictionary](../../stage-2/DATA-01-Priority%20Field%20Matrix.md): residence/onset, AREA and notification/adjustment dates |

The local physical read used these exact identities, never an implicit latest:

| Local source | Identity / relevant files |
| --- | --- |
| National canonical publication (N) | `data/processed/canonical_model_table_national_v1/c2267f61c7624f19ea7056c2d891512b12e85d81214145df1d31815d28fc3c29/`; CSV, `coverage.json`, `columns.json`, `contract.json`, `manifest.json` and department/year eligibility |
| Regional canonical publication (R) | `data/processed/canonical_model_table_v1/ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98/`; CSV, coverage, dictionary, contract and manifest |
| Stage 2 (S2) | `data/processed/panel_mensual_dengue_clima.csv`; `data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json` and `candidate_construction_contract_v1.json` |
| National notifications (S1) | `data/interim/canonical-nacional-data/aa25e8cee5fd9cdaa4bf/`; `execution_summary.json`, `municipality_eligibility.csv`, reconciliation, missingness and duplicate summaries |
| Climate union (C2) | `data/interim/canonical-nacional-data/climate_step2_v1/climate_union_manifest.json`; CHIRPS daily rainfall and ERA5-Land daily aggregates; original source plus January 2020 complement |

N CSV SHA-256 is
`66c58d862f397b7953f7b32cfb6399330acc86e0acab1b5e3a6e809ea4b392d0`;
R CSV is `d1c3d0d28bd3ee1b51e6e2975b69d9f617077f7f4036b5422c4dc1585289cf47`;
S2 panel is `aa8a00dd25e63d3961c9fc779f66645d8a8b4abe6276f7fe601f36234c460d26`.
S1 and C2 source identities are inherited from the pinned N manifest.

## Coverage: presence, history and eligibility

The following are audit counts from S1 and N/R, not new scientific results.
S1 presence is restricted to **2011-06–2024-12**; full-export counts have a
different denominator and must not replace this window.

| Measure | National inventory | Meta + Tolima |
| --- | ---: | ---: |
| Inventory/calendar territories | 1,122 | 76 |
| Territories with at least one general-dengue source row in window | 1,103 | 76 |
| Territories with at least one severe-dengue source row in window | 790 | 71 |
| Territories with any notification in every one of 163 months | 36 | 8 |
| Calendar months without either notification stream | 106,384 / 182,886 | 3,542 / 12,388 |
| Canonical rows / distinct origin months | 182,886 / 163 | 12,388 / 163 |
| Current H5 observed rows | 120,126 | 12,388 |
| All-nine-climate complete rows / territories | 182,560 / 1,120 | 12,388 / 76 |
| Existing G1_NO_CLIMATE T+1 / T+2 rows | 92,735 / 92,061 | 8,130 / 8,091 |
| Existing G1_WITH_CLIMATE T+1 / T+2 rows | 92,584 / 91,911 | 8,130 / 8,091 |

All 1,122 territories have at least one row under each NO_CLIMATE mask; climate
masks retain 1,120. All 76 regional municipalities have rows under every mask.
Regional complete-climate rows split **Meta 4,727; Tolima 7,661**. Regional
T+1 masks split **3,038 / 5,092**; T+2 **3,027 / 5,064**. These are all-window
technical counts, not the benchmark's evaluation cohort or approval to train.

N counts contain no nulls because the approved D2/D3 calendar supplies zeros.
The 19 territories without any source notifications are retained. Neither their
zeros nor complete masks demonstrate surveillance completeness. Source counts
describe notifications, not deduplicated patients, confirmed infections or
independently adjudicated episodes. S1 retains possible duplicate identifiers;
5,663 in-window notifications have unresolved geography. Extraction completeness
and historical boundary correspondence remain unverified (I11).

Outside the original 76, H5 history starts **2016-06** (1,046 territories);
within them N borrows approved pre-window R history and H5 is available from
**2011-06**. N has **62,760** missing current-channel rows. Each count stream's
lag1/2/3/12 has **1,046 / 2,092 / 3,138 / 12,552** missing rows, respectively,
all outside the original 76. The corresponding first complete outside-region
origins are 2011-07, 2011-08, 2011-09 and 2012-06. Missing onset labels near
history/window boundaries remain missing; they are never negative examples.

R and the S2 panel have **17,936 rows**, 76 municipalities × 236 months,
**2006-06–2026-01**. All nine climate variables are complete in **17,328 rows**,
**2007-01–2025-12**; each has **608** missing rows at the uncovered edges.
Current H5 has **13,376** observed rows, **2011-06–2026-01**. These later rows
are source history only: this audit does not admit 2025/2026 as an independent
evaluation period or extend N beyond 2024.

### Nine existing climate variables

Each variable has the same verified N/R periods and missingness above. National
missingness is **326 per variable**, two insular territories × 163 months;
no zero filling or imputation is allowed. C2 documents daily source history
2007-01-01–2025-12-31; that range alone does not establish per-territory coverage.

| CSV ID | Canonical field | Unit / calendar-month aggregation |
| --- | --- | --- |
| C01 | `rain_mm_month_sum` | mm/month; sum |
| C02 | `surface_runoff_mm_month_sum` | mm/month; sum |
| C03 | `total_evaporation_mm_month_sum_ecmwf` | mm/month; sum, ECMWF sign retained |
| C04 | `solar_radiation_mj_m2_month_sum` | MJ/m²/month; sum |
| C05 | `temp_mean_c_month_mean` | °C; mean |
| C06 | `dewpoint_mean_c_month_mean` | °C; mean |
| C07 | `soil_water_l1_month_mean` | m³/m³; mean |
| C08 | `wind_u_ms_month_mean` | m/s; mean |
| C09 | `wind_v_ms_month_mean` | m/s; mean |

Every aggregate requires all calendar days for that variable. No monthly sum is
accepted from incomplete daily support. EDA-EXP01 C7.1 found all nine variables
at T on **2,653 T+1 / 2,422 T+2** frozen regional rows, plus complete predefined
T−1/T−2/T−3 temperature/rain/soil lags. Its weak, inconsistent associations,
overlapping alert groups and sparse near-P75 support remain the scientific
result; national coverage does not reverse `INSUFFICIENT_EVIDENCE` (I02/I03).

## External documentary candidates

All entries below are **`EXTERNAL_CANDIDATE`**, accessed 2026-11-03. Documentation
availability is verified to the extent stated; municipal joins, historical
release vintages and completeness for 1,122/76 are **UNVERIFIED**. No claim that
these covariates are already in N, R or S2 follows.

| ID | Official documentation | What it establishes / unresolved requirement |
| --- | --- | --- |
| E01 | [DANE MGN municipality catalogue through ICDE](https://www.icde.gov.co/datos-y-recursos/marco-geoestadistico-nacional-municipio) | DANE municipal geometry source exists. Select a historical version, validate DIVIPOLA crosswalk/topology and confirm coverage before proposing adjacency or distances. |
| E02 | [DANE municipal population projections](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) | Page lists municipal area series for 2005–2017 and 2018–2042, revised 2025-08-08. Annual total/urban-rural denominators are potential inputs; these revised values cannot be assumed known at earlier T. |
| E03 | [MSPS/INS stratification methodology, 2022](https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/VS/ED/VSP/lineamiento-metodologico-estimacion-poblacion-arbovirosis-colombia-2020-2023.pdf) | Official municipal-risk methodology exists. It describes a 2013 endemicity exercise and subsequent changes. A methodology is not a dated municipal membership panel usable before every origin. |
| E04 | [INS 2023 surveillance guidelines, Annex 4](https://www.ins.gov.co/BibliotecaDigital/lineamientos-nacionales-2023.pdf) | Municipal transmission lists are documentarily identified. Annex extraction, complete code membership, classification lookback and exact original release date were not validated; do not use these lists in 2020–2022 by backdating the edition. |
| E05 | [NOAA CPC historical ONI](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/) | Index history begins in 1950; overlapping three-month seasons and revisable values. Page specifies monthly updates by the fifth and notes RONI now governs official monitoring. Historical release vintages remain necessary. |
| E06 | [INS entomological report, 2021](https://www.ins.gov.co/BibliotecaDigital/informe-tecnico-entomologico-de-arbovirosis-colombia-2021.pdf) | Describes local inspection indices and field-presence records for 2007–2021. It does not establish a complete municipal-month panel, comparable survey effort or timely delivery to this project. |
| E07 | [JRC Global Surface Water documentation](https://global-surface-water.appspot.com/download) | Historical monthly assets through 2021 and separate 2022–2024 assets exist. Release/reprocessing differences and observation support must be audited; open surface water is not a direct measure of domestic containers. |
| E08 | [USGS SRTM 1 arc-second specification](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-digital-elevation-shuttle-radar-topography-mission-srtm-1) | Elevation raster from the February 2000 mission, about 30 m. Municipal summaries, historical product availability and population-relevant exposure are not yet verified. |

The climate extraction scripts refer to private DANE-derived Earth Engine assets,
including a 2025 MGN recovery asset. Those locators establish how climate was
extracted, not a locally admitted adjacency source or historical geometry
equivalence. No polygon/raster/OD dataset was found in the inspected `data/`
file inventory. No mobility or epidemiological connectivity source was admitted.
Residence-versus-notification municipalities in case records do not measure travel.

## Availability at origin and inventory conventions

The CSV is the unique signal decision matrix. It has one row per conceptual
signal/family and adds timing/lineage fields to the requested minimum schema:
`original_source`, `observed_period`, `publication_date`, `update_frequency`,
`regional_application`, `transformations`, `leakage_risk`, `evidence`, and
`source_status`. Signal IDs remain stable across the three deliverables.

- `AVAILABLE_INTERNAL`: existing column(s), controlled input or implemented
  historical formula explicitly identified in the antecedent; not a claim that
  every historical formula is materialized in N/R.
- `DERIVABLE_NOT_BUILT`: ingredients exist; the proposed representation does not.
- `EXTERNAL_CANDIDATE`: only documentary source discovery, no admitted dataset.
- `NOT_AVAILABLE`: no suitable input identified or future information forbidden.
- `availability_in_T=VERIFIED` is reserved here for deterministic calendar season.
  `UNVERIFIED` means the actual historical publication/notification availability
  is not demonstrated, even when all observation dates are ≤T.
  `NOT_AVAILABLE` applies to future outcomes at T.

An offset ≤0 in a contract is a calculation rule, not evidence of historical
delivery. `INI_SIN` is event time. `FEC_NOT` describes notification;
`FEC_AJU` may be the latest adjustment rather than first entry; `FEC_ARC_XL`
is export generation. None alone supplies full revision vintages (I12).
Raw outcome-gated `p75_t1/t2` remain controls: use only independently origin-safe
`p25_h5_t1/t2` and `p75_h5_t1/t2` for any later authorized predictor design.
Future onset/excess/counts and final episode duration are unavailable at T.

`PRIORITIZE` means a bounded **conditional design opportunity**, not approved
features or evidence of predictive gain. `CONDITION` keeps an unresolved input
or representation outside the shortlist. `DO_NOT_REPEAT` preserves prior work;
`DISCARD_INFEASIBLE` concerns the stated representation/data situation, not a
universal claim that the underlying phenomenon is useless.

## Validation and limits

Required checks are documentation/CSV checks under the
[testing guide](../../../TESTING_GUIDE.md). No model tests, notebook execution,
Kedro replay, association statistics or full suites are needed for these files.
The audit checks key uniqueness and coverage, not the scientific correctness of
every underlying measurement. Existing cohort masks are counted, not recomputed.
New episode/spatial-signal eligibility and sufficient event support remain
unmeasured until a separately authorized design fixes their definitions.

Validation results and the independent-review/CI handoff are recorded in the PR.
Repo-only conformance is separate from all-plan conformance: the initial global
gate failed on two historical records, `PLAN_012_retire_experimental_eda`
(unresolved critical-review record) and
`PLAN_stage2_data_understanding_initial_recognition` (mixed legacy lifecycle).
These records were not changed or waived. Scoped-plan conformance is N/A.
