# SAT-Dengue V2 — Stage 2 Initial Recognition Report

## 0. Scope and stop point

Documentation consolidated on 2026-10-16. This report preserves historical recognition measurements and the corrected notebook's saved results; this revision did not rerun them. Current scope and field meanings are maintained in the [canonical matrix](DATA-01-Priority%20Field%20Matrix.md), decisions in the [methodological note](nota-metodologica.md), and file/source identities in the [provenance register](DATA-01-Source%20Provenance.md).

Approved scope: **residence in Tolima/Meta and symptom onset (`INI_SIN`)**. The earlier occurrence-based checks below are historical evidence, not the current attribution rule. Dates labelled `FEC_NOT` describe notification, not onset coverage.

Sections 2–7 retain the original full-file recognition, including its national/occurrence scope. Section 10 records the later residence-scoped EDA; its results do not retroactively change the earlier measurement scope. For example, national climate blanks and zero blanks in the bounded Tolima/Meta climate subset can both be true.

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
- **Approved decision:** explicitly confirmed human choice, separate from measured evidence.

## 1. Documentary references

### 1.1 Environmental dictionary and extraction workflow (project reference)

References consulted:
- [Environmental dictionary (E1)](https://github.com/j-mauro-r/microproyecto-tema3/blob/b63257c17f3064a0dcda6fcf4e7028fae4a43078/data/docs/diccionario_datos_ambiente_dengue.csv)
- [Extraction workflow (E2)](https://github.com/j-mauro-r/microproyecto-tema3/blob/b63257c17f3064a0dcda6fcf4e7028fae4a43078/data/docs/README.MD)
- [Extraction script (E3)](https://github.com/j-mauro-r/microproyecto-tema3/blob/b63257c17f3064a0dcda6fcf4e7028fae4a43078/data/docs/gee-query-dengue.py)

Version and lineage: the three environmental references are now pinned to commit `b63257c17f3064a0dcda6fcf4e7028fae4a43078` in the [provenance register](DATA-01-Source%20Provenance.md). E1 documents 18 fields; E2/E3 describe extraction. Matching headers do not establish this CSV's extraction run, and file modification time is not source publication time.

### 1.2 Official SIVIGILA definitions

The readable [INS dictionary 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf) and [2019 dengue form](https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf) support the definitions recorded in the canonical matrix. The earlier PDF-extraction failure was a tool limitation, not missing official semantics. CSV alias correspondence and applicability to all data years remain separate unresolved issues.

### 1.3 Scope of field verification

On 2026-10-16, only current headers and file identities were inspected; no patient records or EDA metrics were recalculated. The matrix distinguishes fields selected by the notebook, fields present but unused, and reference-only concepts. `CLASFINAL` is absent from current epidemiological headers; no equivalence with an export status field is established.

## 2. Inventory and file structure

### 2.1 File inventory

| File | Size (bytes) | Rows (excluding header) | Columns | Separator | Header |
|---|---:|---:|---:|---|---|
| `data/raw/dengue.csv` | 875,694,283 | 1,705,604 | 69 | `,` | Present |
| `data/raw/dengue_grave.csv` | 24,537,734 | 50,101 | 69 | `,` | Present |
| `data/raw/google_earth_engine.csv` | 1,714,041,810 | 7,751,898 | 18 | `,` | Present |

How counts were obtained:
- Size: `ls -l data/raw`
- Historical inventory rows: `wc -l` minus 1 header line; quoted newlines would invalidate this shortcut. Later EDA balance totals are from CSV parsing; neither was recomputed here.
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
- E1 documents the 18 environmental names; current headers and saved notebook checks confirm their presence. Definitions and export lineage are separate evidence.
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
- Official temporal definitions are documented in the canonical matrix. The mapping from export `ANO` to official `AÑO` and the event calendar remain to be verified.

Important interpretation guardrail:
- If `ANO` in inspected epidemiological CSV corresponds to official `AÑO` (epidemiological-week year), then mismatch against calendar year from `FEC_NOT` is **not automatically an error**.

### 4.3 Pending
- Export alias and calendar correspondence remain pending; official field meaning is no longer blocked by the earlier extraction tooling.
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
  - Interpretation limit: this grouping omits department and is not a national municipality-period key. Multiple individual cases per municipal period are expected; these counts do not diagnose duplicate cases.
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
- Verified definitions, version limits and export-mapping questions are maintained in the canonical matrix and source register.

### 5.3 Hypothesis
- A portion of `ANO`/`FEC_NOT` mismatches may be expected under epidemiological-week-year conventions.

### 5.4 Pending
- Exact duplicate full-row detection across all files was not run in this pass (would require heavier processing and explicit approval for deeper checks).
- Interpret the priority fields used by the EDA and case-definition work; the other columns remain inventoried without a requirement to research all 69 indiscriminately.
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
- The shared `CONSECUTIVE` values do not support an inclusion/exclusion inference until the identifier scope is known; no case-overlap conclusion is adopted.
- Potential epidemiology-climate linkage keys may involve municipality and time, but harmonization rules are required first:
  - municipality coding alignment (the historical occurrence candidate is superseded by approved residence: `COD_DPTO_R` + `COD_MUN_R` versus `mpio_cdpmp`)
  - temporal alignment (case date/epi week vs daily climate date)

### 6.4 Pending
- Relationship semantics (whether severe dengue is included in dengue by definition or operationally separate) need authoritative domain confirmation.
- Relationship semantics for `CONSECUTIVE` overlap require formal event-process clarification.
- Historical applicability and export lineage for fields actually used remain pending; unused columns are outside the priority interpretation scope.

## 7. Checks omitted and why
- Full EDA, visual profiling, joins, and aggregations: out of scope by instruction.
- Full deduplication/record linkage analysis: out of scope for this recognition pass.
- Final target (`Y`) definition and municipality eligibility decisions: out of scope for this step.

## 8. Remaining interpretation and provenance questions

1. Which source/export versions establish `ANO`/`AÑO`, `COD_MUN_R`/`MUN_PRO` and other required alias mappings?
2. What case-inclusion, adjustment and identifier rules avoid unsupported case counts or double counting?
3. What treatment should apply to missing onset, the 2013 date alerts and unknown municipal residence?
4. What official inventory validates territorial completeness, and what extraction run produced the climate CSV?
5. How will later work handle January 2020 and information availability at historical cutoffs?

Residence and symptom onset are already approved. The 76 municipalities are observed coverage, not an independently verified official denominator.

## 9. Consolidated documentary result

The [canonical priority matrix](DATA-01-Priority%20Field%20Matrix.md) replaces the duplicate matrix; the [provenance register](DATA-01-Source%20Provenance.md) separates current identities, saved-run metadata and unknown upstream lineage. This bounded documentation step is complete; data remediation and later Stage 2 decisions are not.

## 10. Brief update from the official notebook EDA increment (methodology-corrected run)

Notebook reference:
- [notebooks/01_stage2_residence_onset_eda.ipynb](../../../notebooks/01_stage2_residence_onset_eda.ipynb)

Scope reminder:
- This notebook increment is bounded to Stage 2 Data Understanding (no cleaning/imputation/integration/model training).
- `dengue` and `dengue_grave` were analyzed separately.
- Residence geography (Tolima/Meta) was used as approved scope.
- Symptom onset is the approved epidemiological reference, implemented with the confirmed `INI_SIN` header; no automatic replacement by `FEC_NOT` was applied.

Run traceability:
- Source headings and stable cell IDs, rather than ambiguous execution counters, are recorded in the provenance register.
- Fixed analysis cutoff: 2026-10-15. The saved run is dated 2026-10-15; this documentary review is dated 2026-10-16.
- Recorded input sizes/timestamps match the currently inspected files; hashes were first recorded during this consolidation, not at original execution.

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
  - The saved onset-after-notification breakdown concentrates these alerts in 2013; the cause remains unresolved.
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

## 11. Evidence classification summary

- **Saved data evidence:** historical dimensions, date ranges, department counts and corrected EDA outputs retained unchanged in this revision.
- **Header-only confirmation:** priority fields and file identities inspected on 2026-10-16; no new clinical/value validation.
- **Documented definitions:** the canonical matrix links official meanings to source versions while keeping export mappings separate.
- **Approved decisions:** residence and symptom onset for municipal Tolima/Meta outputs.
- **Pending:** upstream provenance, municipal inventory, historical alias/calendar correspondence, case-inclusion and identifier rules, anomaly/gap treatment, channel/target definition and training strategy.

Stage 2 remains open. No G2 approval, data transformation or new analysis follows from documentary consolidation.

## 12. DIVIPOLA-based territorial and continuity increment (executed 2026-10-16)

This section records the clean-kernel execution of the extended notebook logic that validates territorial coverage and temporal continuity against the supplied DIVIPOLA catalogs. It complements (and does not replace) historical sections above.

Executed artifact set:
- `data/interim/stage2_divipola_validation/divipola_catalog_validation.csv`
- `data/interim/stage2_divipola_validation/divipola_catalog_metadata.json`
- `data/interim/stage2_divipola_validation/divipola_department_municipality_counts.csv`
- `data/interim/stage2_divipola_validation/territorial_coverage_by_code.csv`
- `data/interim/stage2_divipola_validation/territorial_exceptions.csv`
- `data/interim/stage2_divipola_validation/territorial_summary_by_dataset.csv`
- `data/interim/stage2_divipola_validation/temporal_continuity_epi.csv`
- `data/interim/stage2_divipola_validation/temporal_continuity_climate.csv`
- `data/interim/stage2_divipola_validation/temporal_continuity_summary.csv`
- `data/interim/stage2_divipola_validation/coverage_controls_status.csv`

### 12.1 Observation

- DIVIPOLA catalog structure checks passed:
  - department payload rows: 33
  - municipality payload rows: 1,122
  - municipality declared conteo: 1,122 (matched)
  - duplicated `CODIGO_DPTO_MPIO`: 0
  - department-prefix mismatches between `CODIGO_DPTO_MPIO` and `CODIGO_DPTO`: 0
- Recomputed expected municipality universe for approved scope:
  - Meta (`50`): 29 municipalities
  - Tolima (`73`): 47 municipalities
  - Total expected official municipalities: 76
- Territorial summary by dataset (official-code basis):
  - `dengue`: expected-present 76, expected-absent 0, additional-valid-not-in-DIVIPOLA 0, row exceptions 383 (`unknown_code`)
  - `dengue_grave`: expected-present 71, expected-absent 5, additional-valid-not-in-DIVIPOLA 0, row exceptions 21 (`unknown_code`)
  - `climate`: expected-present 76, expected-absent 0, additional-valid-not-in-DIVIPOLA 0, row exceptions 0
- `dengue_grave` expected-absent official municipality codes:
  - `50245`, `50686`, `73152`, `73347`, `73461`
- Temporal continuity diagnostics were exported separately for epidemiological and climate files:
  - climate common window: 2007-01-01 to 2025-12-31
  - each expected municipality has 31 missing climate dates in the common window (January 2020 pattern), computed from data.

### 12.2 Interpretation

- The catalog files are internally consistent enough to be used as the territorial denominator for this bounded Stage 2 check.
- Territorial coverage is satisfactory for `dengue` and `climate` under the approved residence scope, but not fully satisfactory for `dengue_grave` because 5 expected official municipalities are absent.
- `unknown_code` row exceptions indicate records that cannot be mapped to valid official municipality codes under current evidence.
- Temporal continuity outputs support gap visibility, but they do not by themselves classify epidemiological silence as zero incidence.

### 12.3 Implication

- Territorial conclusions for downstream planning must keep file-level separation (`dengue`, `dengue_grave`, `climate`) and must keep code-validity diagnostics visible.
- Any later Stage 2/Stage 3 process using municipal coverage should carry the `dengue_grave` expected-absence caveat and the `unknown_code` exception volume as explicit risk.
- Climate January 2020 missing-date pattern is now a reproducible observed gap and should remain a documented limitation in temporal joins.

### 12.4 Pending decision

- Decide whether the 5 expected-absent `dengue_grave` municipalities represent true structural absence, source extraction boundaries, or coding/reporting behavior.
- Decide policy for handling `unknown_code` exceptions in in-scope residence records without mutating raw data in Stage 2.
- Decide whether external official metadata (download URL/date/version) for DIVIPOLA can be added to move catalog identity from local traceability to externally verifiable provenance.
- Stage 2 and G2 remain open; no model target or training strategy decision is made here.
