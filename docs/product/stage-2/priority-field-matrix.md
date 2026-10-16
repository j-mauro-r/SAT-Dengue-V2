# SAT-Dengue V2 — Priority Field Matrix

Documentary revision: 2026-10-15. Companion to the [initial recognition report](DATA-01-Initial%20Recognition%20Report.md), within DATA-01; this does not replace the roadmap's DATA-02 reproducible-download task.

This matrix supports interpretation before data preparation. It is not a frozen Data Contract, a full 69-column dictionary, or an authorization to clean, join or model data. CSVs are absent from this checkout. No headers, values or counts were newly inspected; historical observations are attributed to the previous report.

## 1. Decisions and evidence status

- **Approved by Mauricio:** symptom onset is the case-period reference, with `INI_SIN` as the candidate column; prediction scope is the municipalities of Tolima and Meta, at T+1/T+2.
- **Previously reported header:** cited in the recognition report or its execution record, not reverified in this revision.
- **Reference-only name:** present in documentation; existence in the current CSV is unverified. Names must not be silently renamed or treated as observed headers.
- **Documented meaning:** supported by a source; does not establish export mapping or data quality.
- **Pending:** an unresolved mapping, empirical check or policy. No automatic fallback, exclusion, case-union rule or training granularity is approved here.

All municipalities remain in geographic product scope. Data-quality eligibility controls whether a valid prediction can be emitted; missing evidence must not become zero risk.

## 2. Source register

| ID | Source and version | What it supports and limits |
|---|---|---|
| R | [Initial recognition report](DATA-01-Initial%20Recognition%20Report.md) and earlier execution record | Historical CSV observations. They do not replace a versioned header manifest or fresh verification. |
| S | [INS SIVIGILA dictionary 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf) | Official definitions and technical names. Viewer pages 29–38 cover basic data; pages 98–102 cover dengue. Applicability outside this edition and correspondence to export aliases remain pending. |
| D | [INS dengue form and instructions, 2019](https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf) | Event categories and section 7.1 clinical classification. The form does not establish export identifiers or cross-file case uniqueness. |
| E | [Environmental dictionary](https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/diccionario_datos_ambiente_dengue.csv), [workflow README](https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/README.MD), [extraction script](https://github.com/j-mauro-r/microproyecto-tema3/blob/main/data/docs/gee-query-dengue.py) | Project reference with 18 fields, units and transformations. Reviewed on 2026-10-15 using mutable `main` links; no extraction-run snapshot or lineage to our CSV is confirmed. |

The earlier inability to extract INS PDFs is a tool limitation from that session. Official meanings below were subsequently checked in the readable sources; their CSV mappings remain separately pending. All interpretations must be checked against the edition applicable to the data year.

## 3. Temporal fields

| CSV name or candidate | Header evidence | Meaning and source | V2 use and remaining question |
|---|---|---|---|
| `INI_SIN` | Reference-only in this revision; cited in the historical V1 report, not profiled in R | Symptom onset, S | Approved temporal reference. Verify current header, format, completeness and invalid dates; fallback policy remains open. |
| `FEC_NOT` | Previously reported, R | Notification date, S | Retain for timing and availability checks; not the selected case-period anchor. It does not reconstruct all later revisions. |
| `ANO` → official `AÑO` | `ANO` previously reported, R; alias mapping pending | Epidemiological-week year, S | Do not equate automatically with notification's calendar year. Verify export mapping and year-boundary conventions before interpreting discrepancies. |
| `SEMANA` | Previously reported, R | Epidemiological week, S | Verify which event date generated it. Monthly product aggregation must follow the approved onset-date rule. |
| `FEC_AJU` | Reference-only, S | Record-entry/adjustment timestamp, S | Determine whether the export has it and what history survives. Not approved as a substitute for onset or a full as-of snapshot. |
| `date`, `year`, `month`, `day_of_year` | `date`, `year`, `month` previously inspected; `day_of_year` described structurally, R | Calendar date and components, E | Match climate to the chosen period only after provenance and aggregation rules are resolved. |

Assigning a case to its symptom-onset month and deciding when it became available are separate operations. Later analysis must avoid using late reports or later adjustments as if already known at an earlier forecast cutoff. Rules for late reports, incomplete recent months and missing onset remain pending.

## 4. Geographic fields

| CSV name or candidate | Header evidence | Meaning and source | Pending mapping or decision |
|---|---|---|---|
| `COD_DPTO_O` | Previously reported, R | Occurrence department, S | Candidate for attribution; occurrence has not yet been selected over residence or notification. |
| `COD_MUN_O` → official `COD_MUN` in this edition | CSV name previously reported, R; official name differs, S | Department-dependent occurrence municipality code, S | Verify alias and width. Do not claim this edition literally defines `COD_MUN_O` or assign its `COD_MUN` a different geography from a newer version. |
| `Departamento_ocurrencia`, `Municipio_ocurrencia` | Previously reported, R | Occurrence labels as described in R; export derivation unverified | Useful for reconciliation. Names must not replace a validated geographic code. |
| `COD_DPTO_R`, `MUN_PRO` | Reference-only, S | Residence department and municipality, S | Identify exact CSV names and differences from occurrence before selecting geography. |
| Notification department/municipality — exact CSV names pending | R mentions notification geography but does not enumerate its headers | Separate attribution candidate | Locate the export fields and source version; do not infer them from suffixes, provider codes or a similarly named occurrence field. |
| `mpio_cdpmp` | Previously reported, R; documented in E | Full municipal DIVIPOLA identifier, E | Candidate climate linkage key; verify format, vintage and correspondence to epidemiological codes. |
| `dpto_ccdgo`, `mpio_ccdgo` | Described in R and E; header-only confirmation pending | Department code and within-department municipality code, E | Preserve as identifiers; define padding and composition only after checking the actual export. |
| `dpto_cnmbr`, `mpio_cnmbr` | Previously reported, R | Department and municipality labels, E | Reconcile with codes. Do not join by labels when a validated code is available. |

Scope membership will be determined using the epidemiological geography selected for case attribution. Historical occurrence-based Tolima/Meta counts do not prove residence- or notification-based coverage. No filtering has been executed here.

The historical grouping `ANO + SEMANA + COD_MUN_O` omits department. Its counts are retained for traceability but cannot establish national municipality-period uniqueness or duplicated cases. A complete geographic-period grouping still allows many individual cases; identifying duplicate cases is a different question.

## 5. Identifiers and classification

| CSV name or candidate | Header evidence | Meaning and source | Pending rule |
|---|---|---|---|
| `CONSECUTIVE` | Previously reported, R | Export identifier; uniqueness domain is unknown | Establish stability across files, years, events and revisions before interpreting overlap. No case-level inclusion conclusion follows from the 661 shared values. |
| `COD_EVE` | Previously reported, R | Event identity; 210 dengue, 220 severe dengue, 580 dengue mortality, D | Different codes do not prove disjoint cases. Presence of 580 in these CSVs has not been established. |
| `TIP_CAS` | Reference-only, S | Initial case classification, S | Verify current header and approved case eligibility. Do not treat every notification as a confirmed case by default. |
| `AJUSTE` | Reference-only, S | Case follow-up/classification adjustment, S | Verify the export and historical encoding before deciding inclusion or exclusions. |
| `CLASFINAL` or its export alias | Reference-only technical name, S; clinical categories also in D section 7.1 | Final dengue severity category | Confirm actual CSV name and category values. Severity, confirmation status and predicted outbreak onset are different concepts. |

The final case-count definition and dengue/severe-dengue relationship remain unresolved. Clinical classification fields help define historical eligibility; they do not define the future outbreak target `Y` on their own. No personal identifiers or patient-level examples are reproduced.

## 6. Environmental definitions from the project reference

All rows below are **documented in E**. Their presence is reported structurally in R, and rain/temperature blanks were counted previously; this is not a new header or value check. No listed definition establishes this CSV's provenance.

| Field | Documented quantity | Unit | Review needed |
|---|---|---|---|
| `rain_mm_day` | CHIRPS daily precipitation, municipal spatial mean | mm/day | Confirm extraction lineage and future monthly aggregation. |
| `temp_mean_c` | ERA5-Land daily air temperature at 2 m, municipal mean | °C | Confirm conversion and missing-data handling. |
| `dewpoint_mean_c` | ERA5-Land daily dewpoint at 2 m, municipal mean | °C | Confirm conversion and missing-data handling. |
| `soil_water_l1_mean` | ERA5-Land daily surface-layer soil water | m³/m³ | Confirm layer and extraction version. |
| `surface_runoff_mm_day` | ERA5-Land daily runoff accumulation | mm/day | Confirm meter-to-mm conversion. |
| `total_evaporation_mm_day_ecmwf` | ERA5-Land daily evaporation accumulation, ECMWF sign | mm/day | Preserve sign pending interpretation; do not silently invert it. |
| `wind_u_mean_ms` | ERA5-Land daily east-west wind component at 10 m | m/s | Confirm component convention and future aggregation. |
| `wind_v_mean_ms` | ERA5-Land daily north-south wind component at 10 m | m/s | Confirm component convention and future aggregation. |
| `solar_radiation_mj_m2_day` | ERA5-Land daily downward solar energy accumulation | MJ/m²/day | Confirm J-to-MJ conversion and aggregation. |

Script settings 2018–2024 differ from the reported CSV interval 2007–2025. README examples and asset naming also differ from the script. These are lineage questions, not proof that the data are wrong. The 31 absent calendar dates implied by R and rows with blank climate values are distinct issues to investigate later by municipality.

## 7. Geographic model strategy remains open

### Documentary evidence already reviewed

| Study | Evidence relevant to model granularity |
|---|---|
| [Beal et al., 2025](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GH001325), sections 2.1–2.3 | Separate models by city/month and forecast horizon. Incidence prediction and validation design differ from V2. |
| [Schlesinger et al., 2024](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2024.1323618/full), introduction and sections 2.3–2.5 | EWARS-csd supports joint municipal modeling with local configuration evaluation. Local tuning does not establish fully independent fits. |
| [Wu et al., 2025](https://www.pnas.org/doi/10.1073/pnas.2422335122), methods | Includes location-specific and cross-location methods; VAR variants fit by country. A global evaluation is not proof of a single universal fitted model. |
| [Umaña et al., 2026](https://publichealth.jmir.org/2026/1/e79914), methods | Uses symptom onset and occurrence-based geographic aggregation for endemic-channel assessment; does not select a predictive training granularity. |
| [Velandia et al., 2026](https://www.nature.com/articles/s41598-026-63542-8), experimental framework | Compares one national model with independent departmental models. Its spatial risk-classification task is not V2's T+1/T+2 outbreak-onset task. |

The expert's consolidated session notes recommend a bounded municipal pilot but contain no explicit requirement equivalent to “two cities require two independent models.” They are not a verbatim transcript. The degree proposal defines a municipality-month panel without fixing training granularity. These source interpretations were reviewed with Mauricio on 2026-10-15; neither changes his Tolima/Meta scope.

### Options for later evaluation

| Option | Training population | Municipal output preserved? |
|---|---|---|
| Shared | Eligible municipalities from Tolima and Meta together | Yes |
| Departmental | One fit using Tolima municipalities; another using Meta municipalities | Yes; does not mean predicting only departmental totals |
| Municipal | One fit per eligible municipal series | Yes; requires enough local history and outbreak onsets |

**Proposal, not an approved architecture:** compare shared versus departmental fitting under identical temporal splits, labels and feature definitions. Consider municipal models selectively when sufficient evidence exists. Report performance by municipality, department and horizon, including onset counts, false alarms and calibration. An aggregate score must not hide persistent local failure. Define selection criteria before consulting the final test block.

One monthly inference job can apply shared models or route rows to local models. The number of jobs, geographic training unit and number of horizon-specific artifacts are separate choices. No training, architecture selection or new experiment is performed by this matrix.

## 8. Review gate and next bounded step

1. Review the documentary mappings and resolve geography, missing-onset policy and case-inclusion/identifier semantics where evidence permits.
2. On the next separately scoped inspection, verify exact headers without exposing row-level data; record export version and aliases. Resolve `COD_MUN_O` versus official `COD_MUN` explicitly.
3. After authorization, inspect onset-date quality, report delays and municipal coverage within the selected Tolima/Meta geography. Define `Y` before attempting to measure outbreak-onset availability for model design.

No new scripts, dependencies, CSV profiling, transformations, model training or full EDA are part of this deliverable. Stage 2 remains open and G2 is not approved.
