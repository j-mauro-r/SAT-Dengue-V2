# SAT-Dengue V2 — Canonical Priority Field Matrix

Revision: 2026-10-16. Status: working definitions for Data Understanding; G2 is not approved.

This is the single field-definition reference for the bounded Stage 2 EDA. It consolidates the former `priority-field-matrix.md` and the previously indexed DATA-01 matrix. It does not replace the roadmap's DATA-02 download task or freeze a Data Contract.

Related records: [recognition and saved results](DATA-01-Initial%20Recognition%20Report.md), [methodological decisions](nota-metodologica.md), [source provenance](DATA-01-Source%20Provenance.md), and [official notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb).

## 1. Approved decisions and evidence labels

- **Approved:** case attribution uses municipality of residence and symptom onset (`INI_SIN`), within Tolima and Meta. Outputs remain municipal at T+1/T+2.
- **Header confirmed:** present in the current CSV header inspected on 2026-10-16. This is not a value-domain or clinical-quality assessment.
- **Saved EDA evidence:** observed in the committed notebook outputs, not recomputed during this consolidation.
- **Documented definition:** supported by an identified reference; export aliases and historical applicability are separate questions.
- **Pending:** an unverified mapping, source lineage, value rule or policy; it must not be silently treated as approved.

No automatic replacement of missing/invalid onset dates by notification is approved. Municipal eligibility, case inclusion, deduplication, target definition, climate aggregation and training granularity remain open. A municipality in geographic scope is not guaranteed a valid prediction.

## 2. Sources and version boundaries

Use source IDs in the [provenance register](DATA-01-Source%20Provenance.md): S (INS dictionary 2018–2020), D (INS dengue form 2019), E1–E3 (pinned environmental dictionary, workflow and script), N (saved notebook), and H (current header-only check).

Definitions from S and D were readable and verified. The earlier extraction-tool failure is historical, not an unresolved official definition. Their applicability to every year in our exports remains pending. Only the priority fields below are interpreted; the remaining columns are inventoried by header count without speculative definitions.

## 3. Epidemiological fields used by the EDA

All ten field names below are present in both epidemiological CSV headers (H) and in the notebook's selected columns (N).

| CSV field | Working meaning / source | Intended role | What remains pending |
|---|---|---|---|
| `INI_SIN` | Symptom onset, S | Approved case-period reference | Syntactic interpretability is distinct from consistency. Saved EDA has 7 missing dengue values and 8,556 onset-after-notification alerts; treatment is unresolved. |
| `FEC_NOT` | Notification date, S | Delay and availability diagnostics | Not a substitute for onset; cannot reconstruct every later revision. |
| `ANO` | Candidate export alias of S `AÑO`, the epidemiological-week year | Source temporal reference | Verify export lineage and its assignment rule. A calendar-year or ISO comparison alone is not official validation. |
| `SEMANA` | Epidemiological week, S | Source temporal reference | Confirm event-date and Colombian-calendar correspondence; do not assume ISO equivalence. |
| `COD_DPTO_R` | Residence department, S | Departmental scope | Current code uses 50/Meta and 73/Tolima. Current DIVIPOLA membership was checked in the executed diagnostic; historical catalogue applicability remains pending. |
| `COD_MUN_R` | Residence municipal code; S calls the residence field `MUN_PRO` | Municipal identity together with department | Header and current catalogue membership diagnostics are confirmed; alias lineage and historical applicability remain pending. Preserve original text and distinguish format checks from catalogue validation. |
| `Departamento_residencia` | Residence label in the export, H/N | Cross-check and display | Derivation/version not established. A label must not silently override a conflicting code. |
| `Municipio_residencia` | Residence label in the export, H/N | Display and reconciliation | Do not group identical codes separately because labels differ. |
| `COD_EVE` | Event code; D identifies 210 dengue, 220 severe dengue and 580 mortality | Keep the two inputs distinct | Separate event codes do not prove mutually exclusive cases; presence of 580 in these files is not established. |
| `CONSECUTIVE` | Export record identifier candidate, H/N | Traceability diagnostic only | No verified uniqueness domain across years, events, files or revisions. Its overlap is not proof of patient/case overlap or exclusion. |

Residence is selected. Occurrence and notification geography are context, not alternative scope filters. The saved corrected run reports zero name-fallback records and zero department code/name conflicts. Its fallback branch still exists in code; this documentation does not approve it as a future attribution policy.

## 4. Present fields reserved for subsequent case-definition work

Header-only checks confirm `TIP_CAS`, `AJUSTE`, `FEC_AJU`, `confirmados`, `Estado_final_de_caso`, and `nom_est_f_caso` in both inputs. They are not profiled or selected by this EDA.

| CSV field | Documented concept or limit | Pending use |
|---|---|---|
| `TIP_CAS` | Initial classification, S | Verify historical encodings before deciding which notifications count. |
| `AJUSTE` | Follow-up/classification adjustment, S | No inclusion/exclusion or revision-precedence rule is approved. |
| `FEC_AJU` | Entry/adjustment timestamp, S | Determine actual export semantics and whether history survives. |
| `confirmados`, `Estado_final_de_caso`, `nom_est_f_caso` | Export fields with no verified definition in this review | Do not infer meanings or assume equivalence from names. |
| `CLASFINAL` | Final dengue severity in S/D; **absent** from both current headers | No export alias is established. In particular, do not equate it automatically with `Estado_final_de_caso`. |

S uses `COD_MUN` for occurrence municipality and `MUN_PRO` for residence in this edition. Current headers instead include `COD_MUN_O` and `COD_MUN_R`, plus `COD_DPTO_N`, `COD_MUN_N`, `Departamento_Notificacion` and `Municipio_notificacion`. These headers are confirmed, but this consolidation does not approve cross-version aliases or use notification for attribution.

The historical grouping `ANO + SEMANA + COD_MUN_O` omitted department. Its counts are retained only in the historical report; they do not establish national municipal uniqueness or duplicate cases. Multiple cases can legitimately share a complete municipal-period grouping.

## 5. Environmental fields

All 18 names below are confirmed in the current climate header (H) and checked in saved notebook header outputs (N). Definitions and units are from E1. This agreement is schema compatibility, not proof that E3 generated this CSV.

| Field | Reference meaning / unit | EDA role |
|---|---|---|
| `date` | Calendar date, YYYY-MM-DD | Climate time axis |
| `year`, `month`, `day_of_year` | Calendar components | Header checked; not loaded by the climate diagnostic |
| `dpto_ccdgo`, `mpio_ccdgo` | Department and local municipal codes | Department loaded; local code header checked only |
| `mpio_cdpmp` | Full municipal DIVIPOLA code | Municipal comparison key; supplied current vintage recorded, historical applicability pending |
| `dpto_cnmbr`, `mpio_cnmbr` | Department/municipality labels | Cross-check and display |
| `rain_mm_day` | CHIRPS rainfall, mm/day | Missing-versus-zero diagnostics |
| `temp_mean_c` | ERA5-Land air temperature at 2 m, °C | Missing-versus-zero diagnostics |
| `dewpoint_mean_c` | ERA5-Land dewpoint at 2 m, °C | Missing-versus-zero diagnostics |
| `soil_water_l1_mean` | ERA5-Land surface-layer soil water, m³/m³ | Missing-versus-zero diagnostics |
| `surface_runoff_mm_day` | ERA5-Land daily runoff, mm/day | Missing-versus-zero diagnostics |
| `total_evaporation_mm_day_ecmwf` | ERA5-Land daily evaporation, mm/day, ECMWF sign | Sign interpretation remains explicit; no inversion approved |
| `wind_u_mean_ms`, `wind_v_mean_ms` | ERA5-Land wind components at 10 m, m/s | Missing-versus-zero diagnostics |
| `solar_radiation_mj_m2_day` | ERA5-Land daily solar energy, MJ/m²/day | Missing-versus-zero diagnostics |

E1/E3 describe municipal spatial averaging and unit conversions. Daily accumulations and daily means must not be aggregated identically by assumption; future monthly rules remain pending. The script's configured period and asset naming differ from the saved climate export context; see provenance.

Saved outputs show no empty values in the nine climate variables within the inspected subset, while all 76 observed municipalities lack January 2020. Absent dates, empty cells and zeros are different conditions. The previously reported 44.6858% rain-zero proportion is an EDA observation, not a missingness rate or proof of source quality.

## 6. Scope of completed consolidation and remaining review

Completed: both matrices reconciled into this file; used-field headers confirmed without reading patient records; source definitions distinguished from export mappings; source identities recorded; approved residence/onset decisions made consistent.

Pending: historical municipal-catalogue applicability; export and extraction lineage; historical dictionary applicability; 2013 date anomaly; January 2020 recovery/treatment; case inclusion and identifier semantics; missing-onset policy; municipal eligibility; channel/target definition and information-availability rules. Model comparison remains a later evidence-based decision described in the methodological note.

No raw data were corrected or joined. Notebook diagnostics were extended and re-executed; see the recognition report. Stage 2 remains open; G2 is not approved.
