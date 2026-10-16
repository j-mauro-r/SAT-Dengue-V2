# SAT-Dengue V2 — Stage 2 Initial Recognition Report

## 0. Scope and stop point
This report documents a controlled first-pass, read-only recognition of:
- `data/raw/dengue.csv`
- `data/raw/dengue_grave.csv`
- `data/raw/google_earth_engine.csv`

This is an initial recognition checkpoint only. It does **not** close Stage 2 and does **not** approve G2 (Data & Target Freeze).

## 1. Inventory and file structure

### 1.1 File inventory

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

### 1.2 Minimal structural samples (PII-safe)
- Sample extraction method: `head -n 3`.
- For epidemiological files, sample rows were **not reproduced** in this report to avoid exposing potentially sensitive row-level details.
- For climate file, sample confirmed daily records with municipality and climate variables; one sampled row also showed empty climate fields.

## 2. Description by file (first-pass)

### 2.1 `data/raw/dengue.csv`
- Apparent structure:
  - 69 columns including event metadata, demographic fields, geography, dates, and case status fields.
  - `COD_EVE` observed as `210` in sampled/unique checks.
- Apparent unit of observation:
  - **Hypothesis:** one notified dengue case record (case-level row).
- Temporal fields observed:
  - `FEC_NOT`, `SEMANA`, `ANO`, plus other date columns.
- Geographic fields observed:
  - `COD_DPTO_O`, `COD_MUN_O`, department/municipality name fields for occurrence, residence, and notification.

### 2.2 `data/raw/dengue_grave.csv`
- Apparent structure:
  - Same 69-column header as `dengue.csv` (header equality check: yes).
  - `COD_EVE` observed as `220` in sampled/unique checks.
- Apparent unit of observation:
  - **Hypothesis:** one notified severe dengue case record.
- Temporal/geographic fields:
  - Same pattern as `dengue.csv`.

### 2.3 `data/raw/google_earth_engine.csv`
- Apparent structure:
  - 18 columns.
  - Includes `date`, `year`, `month`, `day_of_year`, geographic codes/names, and climate variables.
- Apparent unit of observation:
  - **Hypothesis:** one municipality-day climate record.
- Noted parsing caveat:
  - Quoted geographic names contain commas (for example district names), so CSV-aware parsing is required.

## 3. Temporal and geographic coverage

### 3.1 Confirmed (full-file checks)
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

### 3.2 Pending
- Coverage completeness by municipality over the full period is not confirmed yet.
- Alignment of epidemiological coverage (including 2026 dates in `FEC_NOT`) versus climate coverage ending 2025 is unresolved.

## 4. Basic quality signals (no correction performed)

## 4.1 Confirmed (full-file checks)
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

## 4.2 Hypothesis
- Some `ANO`/`FEC_NOT` mismatches may correspond to surveillance period conventions (for example epidemiological-week assignment) rather than raw data errors.

## 4.3 Pending
- Exact duplicate full-row detection across all files was not run in this pass (would require heavier processing and explicit approval for deeper checks).
- Dictionary/metadata validation for category codes, units, and abbreviations remains pending.

## 5. Preliminary compatibility between files

## 5.1 Confirmed
- `dengue.csv` and `dengue_grave.csv` share the same 69-column schema.
- Event code differs (`210` vs `220`), indicating separate event coding.
- A small overlap exists in `CONSECUTIVE` IDs between files:
  - shared IDs: 661
  - unique `CONSECUTIVE` IDs in `dengue_grave.csv`: 50,096
- Climate file provides daily date and municipality-level geographic keys (`dpto_ccdgo`, `mpio_cdpmp`).

## 5.2 Hypothesis
- Severe dengue may be represented as a related but not fully nested event stream relative to dengue, based on differing event codes and low `CONSECUTIVE` overlap.
- Potential epidemiology-climate linkage keys may involve municipality and time, but harmonization rules are required first:
  - municipality coding alignment (`COD_DPTO_O` + `COD_MUN_O` vs `mpio_cdpmp`)
  - temporal alignment (case date/epi week vs daily climate date)

## 5.3 Pending
- Relationship semantics (whether severe dengue is included in dengue by definition or operationally separate) need authoritative domain confirmation.
- Unit and aggregation-method confirmation for climate variables requires source documentation.

## 6. Checks omitted and why
- Full EDA, visual profiling, joins, and aggregations: out of scope by instruction.
- Full deduplication/record linkage analysis: out of scope for this recognition pass.
- Final target (`Y`) definition and municipality eligibility decisions: out of scope for this step.

## 7. Questions for review before next step
1. Which epidemiological date should anchor Stage 2 alignment (`FEC_NOT`, `INI_SIN`, or another date field)?
2. How should `ANO`/`FEC_NOT` mismatches be interpreted for this product context?
3. Is `COD_MUN_O = 000` considered unknown/invalid for downstream selection, and what policy applies?
4. Should municipality-level linkage use occurrence geography, residence geography, or notification geography?
5. What is the authoritative source for climate variable units and aggregation semantics in `google_earth_engine.csv`?

## 8. Proposed next small step
Run a **documentation-only field contract draft** (no data mutation, no joins) listing:
- candidate linkage fields,
- date-field options with pros/cons,
- explicit handling hypotheses for unknown municipality codes and year mismatches.

Rationale: this resolves key interpretation uncertainty before any deeper exploratory analysis.

## 9. Evidence classification summary
- **Confirmed:** file inventory, dimensions, date ranges, presence of Tolima/Meta, missingness counts, key-repetition counts, schema equality check.
- **Hypothesis:** row-level semantic interpretation, severe-vs-general dengue inclusion relationship, likely linkage strategy.
- **Pending:** definitive relation semantics, unit dictionaries, complete duplicate detection strategy, and downstream contract decisions.
