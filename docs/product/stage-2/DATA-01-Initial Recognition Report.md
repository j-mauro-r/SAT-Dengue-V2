# SAT-Dengue V2 — Stage 2 Initial Recognition Report

## 0. Scope and stop point
This report documents a controlled first-pass, read-only recognition of:
- `data/raw/dengue.csv`
- `data/raw/dengue_grave.csv`
- `data/raw/google_earth_engine.csv`

This is an initial recognition checkpoint only. It does **not** close Stage 2 and does **not** approve G2 (Data & Target Freeze).

Evidence labels used in this report:
- **Confirmed in data:** directly observed in inspected CSV files during this recognition.
- **Documented in source:** described by referenced documentation.
- **Hypothesis:** plausible interpretation not yet validated end-to-end.
- **Pending:** unresolved check or decision.

## 1. Documentary references

### 1.1 Environmental dictionary and extraction workflow (project reference)

References consulted:
- https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv
- https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/README.MD
- https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/gee-query-dengue.py

Version/period identified from those references:
- The repository view reports recent updates around commit `c0b5b13` (as shown in GitHub file pages).
- `gee-query-dengue.py` is configured with `START_YEAR = 2018` and `END_YEAR = 2024`.

Documented in source:
- A data dictionary exists for 18 environmental fields, including:
  - Temporal fields (`date`, `year`, `month`, `day_of_year`).
  - DIVIPOLA geographic codes (`dpto_ccdgo`, `dpto_cnmbr`, `mpio_ccdgo`, `mpio_cdpmp`, `mpio_cnmbr`).
  - Nine climate variables with type, units, source, definitions, and usage comments.
- The extraction script documents dataset sources and transformations (for example Kelvin to Celsius, meters to mm, J/m² to MJ/m²/day, and ECMWF evaporation sign convention).
- The README documents an operational flow for Earth Engine extraction and monthly CSV exports.

Limitations:
- These references are external to this repository and were not used as proof of provenance of `google_earth_engine.csv`.
- Similarity of column names is **not** sufficient to confirm origin.

### 1.2 Official SIVIGILA dictionary reference

Reference consulted:
- https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf

Documented in source (scope expectation):
- The official dictionary is expected to provide technical names, types, lengths, allowed values, and validations.
- The requested interpretation for `AÑO` is epidemiological-week year (not strictly calendar year).

Limitation in this session:
- Direct machine-readable text extraction from this PDF was not successful with available local tooling, so the exact clause could not be quoted in-session.
- Therefore, the `ANO` ↔ official `AÑO` correspondence is incorporated as a documented reference target and remains pending direct textual verification in this workspace.

### 1.3 Dengue event-specific guideline reference

Reference consulted:
- https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf

Documented in source (scope expectation):
- Event categories in scope: 210 (dengue), 220 (severe dengue), 580 (dengue mortality).
- Intended as reference for complementary variables and event-specific categories.

Limitation in this session:
- Direct text extraction from this PDF was also not successful with available local tooling, so event-specific wording and validation rules could not be quoted verbatim.

## 2. Inventory and file structure

### 2.1 File inventory

| File | Size (bytes) | Rows (excluding header) | Columns | Separator | Header |
|---|---:|---:|---:|---|---|
| `data/raw/dengue.csv` | 875,694,283 | 1,705,604 | 69 | `,` | Present |
| `data/raw/dengue_grave.csv` | 24,537,734 | 50,101 | 69 | `,` | Present |
| `data/raw/google_earth_engine.csv` | 1,714,041,810 | 7,751,898 | 18 | `,` | Present |

How counts were obtained:
- Size: `ls -l data/raw`
- Rows: `wc -l` minus 1 header line
- Columns: header split count and CSV DictReader field count

Version/ambiguity check:
- `find data -type f \( -name 'dengue.csv' -o -name 'dengue_grave.csv' -o -name 'google_earth_engine.csv' \) | sort`
- Result: one unique path per required file (no ambiguous duplicate versions found inside `data/`).

### 2.2 Minimal structural samples (PII-safe)
- Sample extraction method: `head -n 3`.
- For epidemiological files, sample rows were **not reproduced** in this report to avoid exposing potentially sensitive row-level details.
- For climate file, sample confirmed daily records with municipality and climate variables; one sampled row also showed empty climate fields.

## 3. Description by file (first-pass)

### 3.1 `data/raw/dengue.csv`
- Apparent structure:
  - 69 columns including event metadata, demographic fields, geography, dates, and case status fields.
  - `COD_EVE` observed as `210` in sampled/unique checks.
- Apparent unit of observation:
  - **Hypothesis:** one notified dengue case record (case-level row).
- Temporal fields observed:
  - `FEC_NOT`, `SEMANA`, `ANO`, plus other date columns.
- Geographic fields observed:
  - `COD_DPTO_O`, `COD_MUN_O`, department/municipality name fields for occurrence, residence, and notification.

### 3.2 `data/raw/dengue_grave.csv`
- Apparent structure:
  - Same 69-column header as `dengue.csv` (header equality check: yes).
  - `COD_EVE` observed as `220` in sampled/unique checks.
- Apparent unit of observation:
  - **Hypothesis:** one notified severe dengue case record.
- Temporal/geographic fields:
  - Same pattern as `dengue.csv`.

### 3.3 `data/raw/google_earth_engine.csv`
- Apparent structure:
  - 18 columns.
  - Includes `date`, `year`, `month`, `day_of_year`, geographic codes/names, and climate variables.
- Apparent unit of observation:
  - **Hypothesis:** one municipality-day climate record.
- Noted parsing caveat:
  - Quoted geographic names contain commas (for example district names), so CSV-aware parsing is required.

Documented in source:
- The project environmental dictionary documents the same 18 field names with units and sources.
- The extraction script and README describe a municipality-day extraction process compatible at schema level.

Confirmed in data vs documented in source distinction:
- **Confirmed in data:** `google_earth_engine.csv` has 18 columns matching the observed names.
- **Documented in source:** there is a published process and dictionary for similarly named environmental outputs.
- **Pending:** provenance linkage between this specific CSV file and that external process is not confirmed in this report.

Differences identified between references and inspected files:
- Reference script period is configured as 2018–2024, while inspected climate CSV covers 2007-01-01 to 2025-12-31.
- Reference README export examples include 2007 monthly files, which differs from script configuration and suggests workflow evolution or multiple runs.
- Asset naming differs between reference README (`municipio-dane-optimized`) and reference script (`municipios-dane-optimized`).

## 4. Temporal and geographic coverage

### 4.1 Confirmed in data (full-file checks)
- `dengue.csv`
  - `FEC_NOT` parsed date range: 2006-05-05 to 2026-03-27.
  - `ANO` range observed: 2007 to 2025.
  - `SEMANA` values observed: 01 to 53.
  - Presence of Tolima and Meta confirmed by name and by row counts:
    - `Departamento_ocurrencia = TOLIMA`: 135,272 rows
    - `Departamento_ocurrencia = META`: 109,072 rows
- `dengue_grave.csv`
  - `FEC_NOT` parsed date range: 2006-12-25 to 2026-03-27.
  - `ANO` range observed: 2007 to 2025.
  - `SEMANA` values observed: 01 to 53.
  - Presence of Tolima and Meta confirmed by row counts:
    - `Departamento_ocurrencia = TOLIMA`: 2,785 rows
    - `Departamento_ocurrencia = META`: 2,056 rows
- `google_earth_engine.csv`
  - `date` range: 2007-01-01 to 2025-12-31.
  - Unique dates: 6,909 over a span of 6,940 calendar days.
  - Presence of Tolima and Meta confirmed:
    - `dpto_cnmbr = TOLIMA`: 324,723 rows
    - `dpto_cnmbr = META`: 200,361 rows

### 4.2 Documented in source
- Environmental dictionary describes `year` as calendar year in climate records.
- SIVIGILA dictionary reference is expected to define official field semantics for surveillance datasets, including temporal fields.
- Requested interpretation for official `AÑO`: epidemiological-week year.

Important interpretation guardrail:
- If `ANO` in inspected epidemiological CSV corresponds to official `AÑO` (epidemiological-week year), then mismatch against calendar year from `FEC_NOT` is **not automatically an error**.

### 4.3 Pending
- Direct textual confirmation of the official `AÑO` definition from the cited PDF remains pending due extraction limitations in this session.
- Coverage completeness by municipality over the full period is not confirmed yet.
- Alignment of epidemiological coverage (including 2026 dates in `FEC_NOT`) versus climate coverage ending 2025 is unresolved.
- Even with epidemiological-week-year semantics, not all date anomalies or out-of-period records are explained.

## 5. Basic quality signals (no correction performed)

### 5.1 Confirmed in data (full-file checks)
- Essential-field missingness:
  - `dengue.csv`
    - `FEC_NOT`, `SEMANA`, `ANO`, `COD_MUN_O`, `Departamento_ocurrencia`: 0 missing
    - `Municipio_ocurrencia`: 5 missing
  - `dengue_grave.csv`
    - `FEC_NOT`, `SEMANA`, `ANO`, `COD_MUN_O`, `Departamento_ocurrencia`, `Municipio_ocurrencia`: 0 missing
  - `google_earth_engine.csv`
    - `date`, `year`, `month`, `mpio_cdpmp`, `mpio_cnmbr`: 0 missing
    - `rain_mm_day`: 13,818 missing
    - `temp_mean_c`: 13,818 missing
    - Rows with all main climate variables missing: 12,484
- Candidate key repetition checks:
  - Epidemiological candidate key used: `ANO + SEMANA + COD_MUN_O`
    - `dengue.csv`: 193,567 distinct values, 123,725 repeated key values, max frequency 3,406
    - `dengue_grave.csv`: 19,687 distinct values, 4,822 repeated key values, max frequency 201
  - Interpretation: repeated key values are expected if rows are case-level; this is **not** declared as an error.
- Additional consistency signals:
  - `ANO` vs parsed year from `FEC_NOT` mismatch:
    - `dengue.csv`: 25,210 rows
    - `dengue_grave.csv`: 692 rows
  - `COD_MUN_O = 000`:
    - `dengue.csv`: 7,602 rows
    - `dengue_grave.csv`: 533 rows
  - Rows with `Municipio_ocurrencia` containing `MUNICIPIO DESCONOCIDO`:
    - `dengue.csv`: 6,277
    - `dengue_grave.csv`: 426

### 5.2 Documented in source
- The official SIVIGILA dictionary reference (2018–2020) is expected to provide temporal validation semantics.
- The dengue event reference (2019) is expected to define event-level category behavior for 210/220/580.

### 5.3 Hypothesis
- A portion of `ANO`/`FEC_NOT` mismatches may be expected under epidemiological-week-year conventions.

### 5.4 Pending
- Exact duplicate full-row detection across all files was not run in this pass (would require heavier processing and explicit approval for deeper checks).
- Full 69-column epidemiological mapping against official dictionaries/instructives remains pending.
- Historical applicability check is pending: official references consulted are period-bounded (for example 2018–2020 and 2019), while inspected data span includes other years.

## 6. Preliminary compatibility between files

### 6.1 Confirmed in data
- `dengue.csv` and `dengue_grave.csv` share the same 69-column schema.
- Event code differs (`210` vs `220`), indicating separate event coding.
- A small overlap exists in `CONSECUTIVE` IDs between files:
  - shared IDs: 661
  - unique `CONSECUTIVE` IDs in `dengue_grave.csv`: 50,096
- Climate file provides daily date and municipality-level geographic keys (`dpto_ccdgo`, `mpio_cdpmp`).

### 6.2 Documented in source
- Dengue-specific guide reference covers events 210, 220, and 580.
- Distinct event codes are documented categories, but code distinction alone does not prove mutually exclusive record sets between files.

### 6.3 Hypothesis
- Severe dengue may be represented as a related but not fully nested event stream relative to dengue, based on differing event codes and low `CONSECUTIVE` overlap.
- Potential epidemiology-climate linkage keys may involve municipality and time, but harmonization rules are required first:
  - municipality coding alignment (`COD_DPTO_O` + `COD_MUN_O` vs `mpio_cdpmp`)
  - temporal alignment (case date/epi week vs daily climate date)

### 6.4 Pending
- Relationship semantics (whether severe dengue is included in dengue by definition or operationally separate) need authoritative domain confirmation.
- Relationship semantics for `CONSECUTIVE` overlap require formal event-process clarification.
- Applicability and coverage of official references across all 69 epidemiological columns and all years in the inspected files remain pending.

## 7. Checks omitted and why
- Full EDA, visual profiling, joins, and aggregations: out of scope by instruction.
- Full deduplication/record linkage analysis: out of scope for this recognition pass.
- Final target (`Y`) definition and municipality eligibility decisions: out of scope for this step.

## 8. Questions for review before next step
1. Can we obtain a directly extractable/citable copy of the official SIVIGILA dictionary and dengue guideline PDFs to validate clauses in-session?
2. Should `ANO` be formally mapped to official `AÑO` (epidemiological-week year) for this project, and with what exception rules?
3. What policy should be applied to in-scope residence rows with missing/invalid/non-identifiable municipality codes in downstream Stage 2 denominator definitions?
4. What evidence will be accepted to confirm provenance (or non-provenance) of `google_earth_engine.csv` relative to external extraction workflows?
5. How will we validate the 69-column epidemiological mapping against official references, including historical applicability outside 2018–2020/2019 windows?

## 9. Proposed next small step
Prepare a **documentation-only priority field matrix** (do not execute yet) with columns:
- Original column name in CSV.
- Intended meaning.
- Source reference URL.
- Source version/period.

Status update:
- Completed in this Stage 2 increment as `docs/product/stage-2/DATA-01-Priority Field Matrix.md`.

## 10. Brief update from the official notebook EDA increment (methodology-corrected run)

Notebook reference:
- [notebooks/01_stage2_residence_onset_eda.ipynb](../../../notebooks/01_stage2_residence_onset_eda.ipynb)

Scope reminder:
- This notebook increment is bounded to Stage 2 Data Understanding (no cleaning/imputation/integration/model training).
- `dengue` and `dengue_grave` were analyzed separately.
- Residence geography (Tolima/Meta) was used as approved scope.
- `INI_SIN` was kept as the onset-date candidate for epidemiological diagnostics, without automatic replacement by `FEC_NOT`.

Run traceability:
- Runtime and reproducibility metadata: notebook code cell 3.
- Header and schema checks: notebook code cell 4.
- Residence filtering controls and synthetic tests: notebook code cell 6.
- Epidemiological quality and `INI_SIN` diagnostics: notebook code cells 7 and 8.
- Climate coverage/gap diagnostics: notebook code cells 9 and 10.
- Evidence-state and key-metric summary: notebook code cell 11.

Key confirmed outputs (aggregated):
- In-scope residence records (Tolima + Meta):
  - `dengue`: 235,501 of 1,705,604 total (Meta 106,457; Tolima 129,044).
  - `dengue_grave`: 4,619 of 50,101 total.
- `INI_SIN` quality in-scope:
  - `dengue` missing: 7 records total (Meta 6, Tolima 1); invalid parse count 0.
  - `dengue_grave` missing: 0; invalid parse count 0.
- Notification delay signal (`FEC_NOT - INI_SIN`, in-scope comparable pairs):
  - Negative delays appear in `dengue` (Meta 3,597; Tolima 4,959) and were kept as observed evidence.
  - `dengue_grave` has 0 records with `INI_SIN > FEC_NOT` under current in-scope filters.
  - No automatic replacement of `INI_SIN` by `FEC_NOT` was applied.
- Comparison against previously reported 8,556 consistency alerts:
  - Recomputed `INI_SIN > FEC_NOT` total alerts (all datasets, Tolima+Meta in-scope): 8,556.
  - Difference vs prior reported value: 0.
- Climate file (`google_earth_engine.csv`) diagnostics under in-scope residence-derived expected municipalities:
  - Rows in target departments by code: 525,084.
  - Overlap window (epidemiology vs climate): 2007-01-01 to 2025-12-31 (6,940 days).
  - Expected municipalities from epidemiology: 76; observed in climate: 76.
  - Expected-without-climate: 0; climate-without-epidemiology: 0.
  - Missingness in prioritized climate variables: 0 for all 9 variables.
  - Zero-value profile separated from missingness: `rain_mm_day` zero proportion 44.6858%; `surface_runoff_mm_day` zero proportion 0.5239%; remaining prioritized variables 0 zero proportion.
  - Gap-pattern control: all 76 expected municipalities share the same computed 31 missing dates (2020-01-01 to 2020-01-31); this was computed from data, not hardcoded.
  - Duplicate municipality-date keys: 0.

Coverage-control states from notebook checks:
- `PASS`: expected municipalities are not restricted to `INI_SIN`-interpretable records.
- `PASS`: source windows and overlap window are explicit and reconciled.
- `PASS`: missing-date counts are computed, not fixed constants.
- `PASS`: municipality gap-pattern comparison is explicit (`unique_gap_pattern_count = 1`).
- `PASS`: no automatic `INI_SIN` substitution by `FEC_NOT`.
- `BLOCKED`: official municipality inventory completeness baseline (no official in-repo inventory artifact).

Open items preserved after notebook execution:
- Official municipality completeness baseline remains **BLOCKED** (no in-repo official municipality inventory artifact for direct benchmarking).
- Final target definition and modeling decisions remain **UNVERIFIED** and out of scope for this Stage 2 increment.

Suggested first scope for that matrix:
- Temporal fields (`ANO`, `SEMANA`, `FEC_NOT`, `INI_SIN`).
- Geographic keys (`COD_DPTO_O`, `COD_MUN_O`, `mpio_cdpmp`).
- Event/category fields (`COD_EVE`, key status/classification fields).

Rationale: this resolves interpretation uncertainty before deeper exploratory analysis or any integration decision.

## 11. Evidence classification summary
- **Confirmed in data:** file inventory, dimensions, date ranges, presence of Tolima/Meta, missingness counts, key-repetition counts, schema equality check.
- **Documented in source:** external environmental dictionary/workflow references; expected official SIVIGILA and dengue guideline scope.
- **Hypothesis:** row-level semantic interpretation, severe-vs-general dengue inclusion relationship, and partial explanation of `ANO` vs `FEC_NOT` differences.
- **Pending:** direct textual verification from official PDFs in this workspace, full 69-column official mapping, historical applicability across all years, definitive relation semantics, and provenance confirmation for `google_earth_engine.csv`.
