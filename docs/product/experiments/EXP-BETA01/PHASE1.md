# EXP-BETA01 Phase 1 — canonical data route

Status: **COMPLETED_WITH_LIMITATIONS** for engineering. Real publication and
coverage acceptance are **BLOCKED** by missing private Stage 2 artifacts.
This does not authorize Phase 2 or any model fitting.

The human Phase 1 request authorizes this bounded addition to
[DESING.md v1.1](DESING.md#32-canonical-model-table-v1-propuesta-conceptual).
The standalone `KEDRO_ARCHITECTURE_AUDIT.md` was unavailable; its architecture
constraints were checked against the current implementation and design.

## Run and publication

```bash
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run \
  --pipeline=canonical_model_table_v1 \
  --params=profile=canonical_model_table_v1,tracking=disabled
```

The profile rejects enabled tracking, experiment IDs and scientific overrides.
The unchanged tracking hook returns before importing MLflow. The graph consumes
only `canonical_stage2_sources` and `parameters`, and publishes the catalog output
`canonical_model_table_v1`. Both catalog authorities declare these entries.

The read-only source is `data/processed/panel_mensual_dengue_clima.csv`.
The existing pinned Stage 2 execution manifest and construction contract establish
its SHA-256, size, dimensions, full schema and scientific policies. The loader
verifies identities before and after reading; the publisher checks them again.
No raw notification/climate data, saved preparers or model artifacts are required.
No directory search, fallback source or implicit latest bundle is supported.

Publication uses the existing atomic `publish_bundle(..., existing_policy="error")`
mechanism under `data/processed/canonical_model_table_v1/<bundle_sha256>/`:

| File | Purpose |
|---|---|
| `canonical_model_table_v1.csv` | The only physical data table; sorted DANE municipality/origin keys |
| `contract.json` | Snapshot of the [pinned v1 contract](canonical_model_table_v1.json) |
| `columns.json` | Every column's role, dtype, observed nullability and source/derivation |
| `coverage.json` | Actual periods, departments, missingness and technical eligibility |
| `provenance.json` | Source identities, operational settings, Git revision/dirty state, code hashes, Python and package versions |
| `manifest.json` | Every payload's SHA-256/size and content-addressed bundle ID |

The publication contains no timestamps or random IDs. Identical inputs, code,
configuration and execution metadata produce identical bytes and identity.
A second identical publication is refused; existing bundles are never replaced.
The dataset reads only its own explicitly published identity and checks all files.

## Compact column dictionary and temporal rules

All Stage 2 columns remain in the new table with their original values and meaning.
No Stage 3 cohort filter, time split, feature recipe or imputation is applied.
Every column has exactly one role: `key`, `feature`, `target`, `control`, `metadata`.
Use `sat_dengue.canonical.table.predictor_matrix(table, schema)` to select the fixed
feature allowlist. Future consumers must verify the selected bundle and contract.
Dropping only `y_*` is insufficient to define X safely.

| Columns/block | Role | Construction and availability |
|---|---|---|
| `municipality_code`, `year_month` | key | DANE code and origin T; unique and non-null |
| Department code and validated names | metadata | Preserve the source; code must match DANE prefix |
| `dengue_notifications_count`, `dengue_grave_notifications_count`, `total_notifications_count` | feature | Consolidated counts at T; components sum to total |
| Count columns suffixed `_lag1`, `_lag2`, `_lag3`, `_lag12` | feature | Exact calendar lookup at T−k; gaps remain null |
| `p25_canal_t`, `p50_canal_t`, `p75_canal_t`, `zona_canal_t` | feature | Current H5 channel; five exact prior same-month years; verify against original values when supplied |
| `month_of_year` | feature | Calendar month of T, 1–12 |
| `p25_h5_t1/t2`, `p75_h5_t1/t2` | feature | Type-7 quantiles for the target month's five exact prior years, all at or before T; null unless all five exist |
| `history_valid_years_h5_t1/t2` | control | Number of available observations among those exact five years; no older-year substitution |
| `rain_mm_month_sum`, `surface_runoff_mm_month_sum` | feature | Original monthly sums, mm |
| `total_evaporation_mm_month_sum_ecmwf` | feature | Original ECMWF monthly sum, mm; preserve negative sign |
| `solar_radiation_mj_m2_month_sum` | feature | Original monthly sum, MJ/m² |
| `temp_mean_c_month_mean`, `dewpoint_mean_c_month_mean` | feature | Original monthly means, °C |
| `soil_water_l1_month_mean` | feature | Original Stage 2 soil-water level-1 mean and source units |
| `wind_u_ms_month_mean`, `wind_v_ms_month_mean` | feature | Original monthly wind-component means, m/s; preserve signs |
| `y_t1`, `y_t2`, if present | target | Original future H5 excess labels; no onset reinterpretation |
| Source `p75_t1/t2`, future status/evaluability, target periods, historical traces | control | Preserved for audit; some depend on future observation availability and must stay out of X |
| `in_epi_coverage`, `epi_count_status`, climate observed/expected/valid days and other source fields | control | Preserve coverage and traces; unknown fields never enter X automatically |

An observed zero keeps `zero_in_coverage`. Counts outside epidemiological coverage
remain null with `outside_epi_coverage_missing`. Inconsistent source semantics fail
validation; no new zero is created. A source zero retains Stage 2's within-coverage
notification convention; it does not prove independent reporting completeness.
Climate aggregates are preserved, including
nulls for incomplete months, and checked against per-variable valid-day counts.
Historical source `p75_t1/t2` is gated by future evaluability; the separate new H5
thresholds deliberately avoid that gate. This is retrospective consolidated data,
not evidence that values were available operationally on the original issue date.

## Coverage and limitations

`coverage.json` reports actual department codes and periods, missing values per
column, and separate Meta/Tolima municipality, observed-zero, missing-case,
complete-climate and complete-feature counts. Technical eligibility is complete
canonical features plus an observed target, counted separately per horizon;
it does not admit a scientific cohort or discard any row. Phase 2 must freeze its
own feature selection and eligibility rules, including any climate exclusion.

| Required real evidence | State | Missing input/action |
|---|---|---|
| Native source integrity and real canonical publication | BLOCKED | Curated panel plus the pinned execution manifest and construction contract listed below |
| Actual Meta coverage and eligibility | BLOCKED | Read and validate the identified panel; inspect generated `coverage.json` |
| Actual Tolima coverage and eligibility | BLOCKED | Same |
| Comparable national data | UNVERIFIED | No national panel supplied or ingested; assess in Phase 2 |
| Historical private payload byte preservation | UNVERIFIED | Private payloads unavailable; no historical files written by this change |
| Independent review and merge approval | UNVERIFIED | Human review of the PR; no merge performed |

Required local files (restore original bytes; do not regenerate or edit to bypass pins):

- `data/processed/panel_mensual_dengue_clima.csv`
- `data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json`
- `data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json`

The two native JSON identities remain owned by `datasets.stage2.NATIVE_IDENTITIES`.
A different source publication requires explicit review, never automatic selection.
Engineering fixtures only validate code behavior; their municipality counts, periods
and output hashes are not evidence about the private panel.

## Compatibility and validation evidence

- PASS: Kedro registry lists the new independent pipeline; the actual CLI reaches
  the verified input boundary and stops on missing native files (real run BLOCKED).
- PASS: focused canonical/configuration/Stage 2/bootstrap/preparation tests, **111 passed**;
  includes a SequentialRunner fixture publication, no-overwrite and tamper checks,
  source hash/schema parsing, future-perturbation invariance and exact-calendar gaps.
- PASS: bootstrap executes with optional modeling/tracking imports denied.
- PASS: scoped Ruff, format and mypy checks; detailed final commands in the PR.
- Legacy implementation, contracts, original Stage 2 files, 16 Stage 3 features,
  saved preparers, experiment routes, replay and `__default__` were not edited.
  Catalog and registry additions retain existing definitions. Bootstrap inventories
  include the new name; the base inventory also now lists the already-registered
  `exp04_oof` entry, whose omission caused the existing inventory assertion to fail.
- Global code/configuration fingerprints can change replay identities, as the
  design documents. No historical identity, bundle or checkpoint is overwritten.
- No real model/preparer fitting or Beta training, calibration, scientific evaluation,
  dashboards or Phase 2 work ran. An optional broader synthetic replay compatibility
  check was interrupted and is **UNVERIFIED**; it is not counted as passing evidence.
- FAIL (inherited): repository Markdown link check reports eight broken references
  to the old `docs/product/experiments/experimentos.md` location. The same eight
  failures are present at incoming branch commit `e0bf3b5`; that commit moved the
  catalogue to `docs/product/experimentos.md`. New Phase 1 links resolve. Scientific
  documents were not edited to repair this unrelated inherited move. CI may stop
  at Repository Quality until the existing link issue is resolved.
