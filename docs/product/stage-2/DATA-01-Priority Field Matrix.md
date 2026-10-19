# SAT-Dengue V2 — Canonical Field Dictionary and Priority Matrix

Revision: 2026-10-17. Status: complete inventory of the current epidemiological export fields; working interpretations for Data Understanding; G2 is not approved.

This file is the **single source of truth for field definitions** for `data/raw/dengue.csv` and `data/raw/dengue_grave.csv`. Both files share the same 69-column ordered header; section 3 documents every column once and applies to both files. Do not maintain a second field dictionary or a competing appendix elsewhere. The existing environmental definitions remain in this document for the companion climate input. Full field coverage does not mean every definition, export transformation or historical encoding has been resolved, and does not freeze a Data Contract.

Related records: [recognition and saved results](DATA-01-Initial%20Recognition%20Report.md), [methodological decisions](nota-metodologica.md), [source provenance](DATA-01-Source%20Provenance.md), and [official notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb). Those records own analytical results, decisions, lineage and execution respectively; they should reference this file for meanings rather than duplicate a dictionary.

## 1. Approved decisions, scope and evidence

- **Approved:** attribute cases by residence municipality and symptom onset (`INI_SIN`), within Tolima and Meta; municipal outputs at T+1/T+2.
- No automatic substitution of missing/invalid onset by `FEC_NOT` is approved.
- Case eligibility, deduplication, event union, missing-onset treatment, municipal eligibility, target construction and training granularity remain open. This dictionary records evidence; it does not authorize a new cleaning or inclusion policy.
- **H (current audit, 2026-10-17):** headers and selected aggregate value domains were read from the local CSVs; neither raw file nor the notebook was modified or executed by that audit. Every record had 69 fields: 1,705,604 dengue records and 50,101 severe-dengue records. COD_EVE was exclusively 210 and 220 respectively. These are record counts, not deduplicated or exclusively confirmed case counts.
- **N:** saved notebook outputs are separate evidence. Its epidemiological selected columns are CONSECUTIVE, COD_EVE, FEC_NOT, INI_SIN, SEMANA, ANO, COD_DPTO_R, COD_MUN_R, Departamento_residencia and Municipio_residencia. Other columns below were not thereby analyzed by the notebook.
- H matched the epidemiological hashes in the provenance register: dengue `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b`; severe dengue `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70`. Hash equality identifies local bytes, not upstream authenticity.

Definition status in section 3: **D** = official concept documented; **A** = official concept documented under a different technical name/candidate export alias; **U** = institutional mention or observed pattern exists, but an adequate operational definition is unresolved. D does not prove the export/enrichment recipe, catalogue vintage or applicability to all years. There are 63 D/A entries and six U entries: CONSECUTIVE, GRU_POB, confirmados, va_sispro, Estado_final_de_caso and nom_est_f_caso. None should be reported as entirely absent from institutional publications; the gap is usable operational documentation.

Priority is analytical, not an official INS mandatory-field flag: **P0** resolve for trustworthy case counting, municipal/onset attribution or historical availability; **P1** reconciliation, provenance and diagnostic context; **P2** demographic or contextual interpretation before downstream use. P0 does not authorize excluding records, and P2 does not authorize dropping columns. Preserve raw identifiers and original values; trimming used for diagnostics must not silently rewrite source data. Blank strings, whitespace-only values, explicit sentinels and numeric zero are distinct.

## 2. Source register and historical limits

S/D/E1–E3 retain the IDs used in the provenance register. B/X/M/P/A/C are additional definition references for this dictionary; they do not establish extraction lineage.

| ID | Official/reference source | Authority and limit |
|---|---|---|
| S | [INS technical dictionary 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf) | Individual basic data, viewer pp. 29–38; dengue, pp. 98–102. Version-bounded record structure. |
| D | [INS dengue form/instructions, 2019](https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf) | Event 210/220/580 and clinical severity; not an export-alias manifest. |
| C | [INS event coding/validation 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/2.%20Codificaci%C3%B3n_de_eventos_Sivigila%202018-2020.pdf) | Event-specific week-date and allowed-classification rules, p. 5. Do not extrapolate to all historical years without checking editions. |
| B | [INS basic-data instructions 2024](https://www.ins.gov.co/buscador-eventos/Lineamientos/Datos%20B%C3%A1sicos%202024.pdf), [basic-data dictionary](https://www.ins.gov.co/BibliotecaDigital/diccionario-datos-basicos-sivigila.pdf) | Basic concepts, notification source, stratum and conditional gestational weeks. Retrieval/text availability varies; not an immutable export-version snapshot. |
| X | [INS Excel-output structures](https://www.ins.gov.co/BibliotecaDigital/diccionario-xls-.pdf) | Technical output concepts, population flags, military catalogue fields and decoded labels. Publication/crawl date is not proof of the applicable data year. |
| M | [INS application user manual, version 01, 2023-09-08](https://www.ins.gov.co/BibliotecaDigital/manual-sivigila.pdf) | Indigenous-group lookup, multiple population memberships and output-date semantics. |
| P | [INS collection/processing manual, 2026-01-02](https://www.ins.gov.co/conocenos/sig/SIG/MNL-R02.4030-004.pdf) | Initial-entry/latest-adjustment date, Excel-generation date and decoded output labels. Does not document the current CSV generation recipe. |
| A | [INS-published Valle del Cauca operational research plan 2025, Annex 1, viewer pp. 98–100](https://www.ins.gov.co/Portalweb2025/Plan_Investigaci%C3%B3n_Operativa_Valle%20del%20Cauca_2025.pdf) | Supporting inventory of export names, not the controlling dengue dictionary. Contains tautological labels, duplicates and incorrect descriptions; never overrides technical S/B/M/P definitions. |
| E1–E3 | Pinned environmental dictionary, workflow and extraction script in the [provenance register](DATA-01-Source%20Provenance.md) | Project references for the 18 climate fields; not INS epidemiological definitions. |
| H / N | Current read-only CSV audit / [saved notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb) | Empirical schema/domains / saved diagnostics. Neither establishes an official rule. |

Exact source-to-export lineage remains pending across the 2007–2025 epidemiological-year range. The PDF previously linked as `diccionario-datos-sivigila-2026-VF.pdf` could not be retrieved in the audit and is not verified evidence here. Current manuals cannot retroactively certify every historical encoding.

## 3. Complete epidemiological field dictionary — both CSVs

All 69 names below preserve exact spelling and order from both current headers. Encoding descriptions distinguish official domains from observed export representations; an official generic domain is not blanket event-specific permission. All dates remain raw text in the CSV; date rules below describe interpretation, not a newly enforced parser.

| # | Exact CSV field | Meaning | Encoding / representation | Status; evidence | Priority / unresolved interpretation |
|---|---|---|---|---|---|
| 1 | `CONSECUTIVE` | Export sequence/record identifier candidate. | Text identifier; uniqueness and stability are unknown. | U; A/H | P0: identity; never assume patient or episode uniqueness. |
| 2 | `COD_EVE` | INS event code. | Observed: 210 in dengue; 220 in dengue_grave. | D; S/D/H | P0: preserve event identity; different codes do not prove disjoint cases. |
| 3 | `FEC_NOT` | Notification date. | Date; current export uses day/month/year plus time text. | D; S/H | P0: reporting delay/availability; never replace onset automatically. |
| 4 | `SEMANA` | Epidemiological week under the event's applicable Colombian calendar. | Official range 1–53; C specifies onset as the reference for 210/220. | D; S/C | P1: verify export assignment; ISO week comparison is descriptive only. |
| 5 | `ANO` | Candidate export alias of technical AÑO: epidemiological-week year. | Year code, not automatically notification calendar year. | A; S/A | P1: verify alias lineage and year-boundary rules with SEMANA. |
| 6 | `COD_PRE` | Health-service provider code. | S specifies a 10-character provider identifier. | D; S | P1: provider provenance; preserve leading zeros. |
| 7 | `COD_SUB` | Provider sub-index identifying site or territory. | S specifies two characters. | D; S | P1: use with COD_PRE; not a municipal attribution key. |
| 8 | `EDAD` | Patient age in the unit specified by UNI_MED. | Integer magnitude; not necessarily years. | D; S | P2: interpret jointly with UNI_MED and applicable edition. |
| 9 | `UNI_MED` | Age measurement unit. | 0 not applicable; 1 years; 2 months; 3 days; 4 hours; 5 minutes. | D; S | P2: do not analyze EDAD as years without conversion rules. |
| 10 | `SEXO` | Recorded sex. | M male; F female; I indeterminate in S. | D; S | P2: preserve source categories. |
| 11 | `COD_PAIS_O` | Country of occurrence code. | Country identifier; three characters observed. | D; S/H | P1: occurrence context, not nationality or residence. |
| 12 | `COD_DPTO_O` | Department of occurrence code. | Two-character territorial identifier. | D; S/H | P1: pair with COD_MUN_O; not the approved scope filter. |
| 13 | `COD_MUN_O` | Municipality of occurrence; S names it COD_MUN. | Three-character local municipality component observed. | A; S/A/H | P1: requires department; do not treat as nationally unique. |
| 14 | `AREA` | Area of occurrence of the case. | 1 municipal seat; 2 populated centre; 3 rural in S. | D; S | P2: not automatically residence area. |
| 15 | `OCUPACION` | Patient occupation code. | S uses CIUO-88/four characters; current export has lengths 4, 5 and 8. | D; S/H | P2: historical catalogue/transformations unresolved; no universal width rule. |
| 16 | `TIP_SS` | Health-insurance regime. | C contributory; S subsidized; P exception; E special; N uninsured; I indeterminate/pending. | D; S | P2: historical code validity remains edition-dependent. |
| 17 | `COD_ASE` | Code of the health administrator responsible for care. | Reference-table identifier; S specifies six characters. | D; S | P2: interpret with TIP_SS and historical administrator catalogue. |
| 18 | `PER_ETN` | Ethnic affiliation. | 1 Indigenous; 2 ROM/Gitano; 3 Raizal; 4 Palenquero; 5 Black/Mulatto/Afro-Colombian; 6 other. | D; S/M | P2: distinct from GP_INDIGEN and GRU_POB. |
| 19 | `GRU_POB` | Institutional sources identify a population-group field; export code semantics unresolved. | Observed nonblank codes after trimming: 5, 7, 9, 13, 14, 16. | U; A/H | P1: locate historical codebook; do not decode through nom_grupo or GP_*. |
| 20 | `nom_grupo` | Name of the Indigenous group of affiliation; technical NOM_GRUPO. | Text label; applicable in the Indigenous ethnic-group context. | D; S/M/H | P2: not the description of GRU_POB. |
| 21 | `estrato` | Socioeconomic stratum; technical ESTRATO/ESTRATO_. | 1–6; current export also contains blanks and SIN DATO. | A; X/B/H | P2: SIN DATO is a missingness marker, not a seventh stratum. |
| 22 | `GP_DISCAPA` | Population-group membership: person with disability. | 1 yes; 2 no. | D; S/X | P2: membership flag; not mutually exclusive with other GP_*. |
| 23 | `GP_DESPLAZ` | Population-group membership: displaced person. | 1 yes; 2 no. | D; S/X | P2: same membership semantics. |
| 24 | `GP_MIGRANT` | Population-group membership: migrant. | 1 yes; 2 no. | D; S/X | P2: does not define country of residence or occurrence. |
| 25 | `GP_CARCELA` | Population-group membership: person deprived of liberty; historical prison population. | 1 yes; 2 no. | D; S/X | P2: terminology varies by edition. |
| 26 | `GP_GESTAN` | Population-group membership: pregnant person. | 1 yes; 2 no. | D; S/X | P2: governs applicability of sem_ges. |
| 27 | `sem_ges` | Gestational age in weeks; technical SEM_GES/SEM_GES_. | B specifies 1–45 when GP_GESTAN is yes; blank is not zero. | A; B/X | P2: historical applicability and conditional completeness pending. |
| 28 | `GP_INDIGEN` | Population-group membership: person experiencing homelessness; historically indigent. | 1 yes; 2 no. | D; S/X | P2: does not mean Indigenous ethnicity. |
| 29 | `GP_POBICFB` | Population-group membership: children under ICBF care. | 1 yes; 2 no. | D; S/B | P2: preserve exact export spelling; do not silently rename ICFB to ICBF. |
| 30 | `GP_MAD_COM` | Population-group membership: community mother. | 1 yes; 2 no. | D; S/X | P2: membership flag. |
| 31 | `GP_DESMOVI` | Population-group membership: demobilized person. | 1 yes; 2 no. | D; S/X | P2: membership flag. |
| 32 | `GP_PSIQUIA` | Population-group membership: person in a psychiatric institution. | 1 yes; 2 no. | D; S/X | P2: not a general mental-health diagnosis. |
| 33 | `GP_VIC_VIO` | Population-group membership: victim of armed violence. | 1 yes; 2 no. | D; S/X | P2: do not broaden to every type of violence without evidence. |
| 34 | `GP_OTROS` | Population-group membership: other population group. | 1 yes; 2 no. | D; S/X | P2: not a missing-value code. |
| 35 | `fuente` | Source/mode of surveillance notification; technical FUENTE. | 1 routine; 2 institutional active search; 3 intensified surveillance; 4 community active search; 5 investigations. | D; B/X | P1: not the dataset provider; one 0 observed in dengue needs review. |
| 36 | `COD_PAIS_R` | Country of residence code. | Three characters when populated; blanks occur in both exports. | D; A/H | P1: do not silently fill with country of occurrence. |
| 37 | `COD_DPTO_R` | Patient residence department code. | Two characters observed; scope: 50 Meta and 73 Tolima. | D; S/H | P0: approved department attribution; historical catalogue validity pending. |
| 38 | `COD_MUN_R` | Patient residence municipality; S names it MUN_PRO. | Three-character local component observed; requires COD_DPTO_R. | A; S/A/H | P0: approved municipal attribution; preserve original text and validate catalogue. |
| 39 | `COD_DPTO_N` | Department of the notifying unit. | Two characters observed. | D; A/P/H | P1: notification geography, not patient residence. |
| 40 | `COD_MUN_N` | Municipality of notification. | Five characters in every row; prefix agrees with COD_DPTO_N after padding. | D; A/H | P1: already includes department in this export; do not prepend it again. |
| 41 | `FEC_CON` | Date the patient consulted for the notified event. | Date; technical individual-case definition takes precedence over erroneous A wording. | D; S/B | P0: temporal consistency context; not provider establishment date. |
| 42 | `INI_SIN` | Date of symptom onset. | Date; chronological consistency is separate from successful parsing. | D; S | P0: approved case-period anchor; missing/invalid-date policy remains open. |
| 43 | `TIP_CAS` | Initial case classification. | Generic codes 1–5; see section 4 for labels and event-specific restrictions. | D; S | P0: case inclusion must not assume every notification is confirmed. |
| 44 | `PAC_HOS` | Hospitalization indicator. | 1 yes; 2 no. | D; S | P1: hospitalization is distinct from severity classification. |
| 45 | `FEC_HOS` | Hospitalization date. | Conditioned on hospitalization; S requires date on/after consultation. | D; S | P1: check conditional completeness; no automatic date correction. |
| 46 | `CON_FIN` | Final vital condition recorded for the event. | 0 unknown/no response; 1 alive; 2 dead. | D; S | P1: vital status, not confirmation status or dengue severity. |
| 47 | `FEC_DEF` | Date of death. | Conditioned on death; S requires date on/after consultation. | D; S | P1: no inference of causal attribution from date alone. |
| 48 | `AJUSTE` | Follow-up/classification adjustment. | 0, 3, 4, 5, 6, 7, D in S; see section 4. | D; S/D | P0: 0 and 7 are not discard codes; eligibility/precedence still pending. |
| 49 | `FECHA_NTO` | Date of birth. | Date; not notification or symptom-onset date. | D; S | P2: sensitive demographic field; no patient-level examples. |
| 50 | `CBMTE` | Underlying cause of death. | ICD-10 code in S; conditional on death. | D; S | P1: not equivalent to COD_EVE or confirmation classification. |
| 51 | `FEC_ARC_XL` | Date the Excel output was generated. | Export metadata; does not establish the first availability of every record. | D; P/M | P0: availability/provenance context; distinct from FEC_ARC_PL. |
| 52 | `FEC_AJU` | Initial entry date when unadjusted; date of the latest adjustment otherwise. | Date; documentation does not guarantee time precision or full revision history. | D; P/S | P0: cannot reconstruct complete as-of snapshots alone. |
| 53 | `FM_FUERZA` | Force code. | X: 1 GAB; 2 CGF; 3 EJC; 4 ARC; 5 FAC; 6 HMC; 7 POL; 8 SIN. | D; X/S | P2: catalogue code, not a yes/no military-membership indicator. |
| 54 | `FM_UNIDAD` | Military unit code. | Reference to the military-unit catalogue. | D; X/S | P2: not the unit name; historical catalogue pending. |
| 55 | `FM_GRADO` | Military rank code. | Reference to the military-rank catalogue. | D; X/S | P2: preserve text and leading zeros; catalogue/version pending. |
| 56 | `confirmados` | Institutional label: confirmed; generation rule not documented. | Observed 0/1; empirical state correspondence in section 5. | U; A/H | P0: do not promote the observed formula to an official rule. |
| 57 | `va_sispro` | Field associated nominally with SISPRO; operational meaning unknown. | Observed constant 1 in both files; no verified value dictionary. | U; A/H | P1: do not describe as SISPRO validation or successful linkage. |
| 58 | `Estado_final_de_caso` | Institutional label: final case status; derivation unverified. | Observed 2, 3, 5; empirical labels in section 5. | U; A/H | P0: not CLASFINAL; verify classification/revision precedence. |
| 59 | `nom_est_f_caso` | Observed text label paired with Estado_final_de_caso. | Probable; laboratory confirmed; epidemiological-link confirmed. | U; A/H | P0: observed decoding is not a verified export specification. |
| 60 | `Nombre_upgd` | Name of the notifying primary data-generating unit; technical NOM_UPGD. | Text label; exact export alias lineage pending. | A; X/P | P1: reconcile with provider codes; not patient geography. |
| 61 | `Pais_ocurrencia` | Country-of-occurrence label. | Text; catalogue-derived concept; exact enrichment recipe unknown. | D; A/X | P1: use with occurrence country code, not nationality. |
| 62 | `Nombre_evento` | Event name; technical NOM_EVE. | Observed DENGUE / DENGUE GRAVE respectively. | A; X/A/H | P1: reconcile with COD_EVE. |
| 63 | `Departamento_ocurrencia` | Department-of-occurrence label. | Text; occurrence geography. | D; A/P | P1: reconcile with codes; not the approved attribution filter. |
| 64 | `Municipio_ocurrencia` | Municipality-of-occurrence label. | Text; occurrence geography. | D; A/P | P1: names do not uniquely identify municipalities nationally. |
| 65 | `Pais_residencia` | Country-of-residence label. | Text; residence geography. | D; A/X | P1: distinguish absent label from an inferred country. |
| 66 | `Departamento_residencia` | Residence department label. | Text; use to check the residence code. | D; A/P | P0: conflicting labels must not silently override codes. |
| 67 | `Municipio_residencia` | Residence municipality label. | Text; display/reconciliation attribute. | D; A/P | P0: a validated municipal code defines grouping; label variants must not split it. |
| 68 | `Departamento_Notificacion` | Department-of-notification label. | Text; preserve exact capital N in export name. | D; A/P | P1: notifying-unit geography, not occurrence/residence. |
| 69 | `Municipio_notificacion` | Municipality-of-notification label. | Text; preserve exact header case. | D; A/P | P1: reconcile with the five-character COD_MUN_N. |

## 4. Official coding rules and geographic/date interpretation

### 4.1 Classification, adjustment and severity are different axes

S defines initial TIP_CAS codes: 1 suspected; 2 probable; 3 laboratory confirmed; 4 clinically confirmed; 5 epidemiological-link confirmed. AJUSTE codes are 0 no adjustment/initial entry/not applicable; 3 laboratory confirmed; 4 clinically confirmed; 5 epidemiological-link confirmed; 6 discarded; 7 other adjustment; D discarded for data-entry error. Keep AJUSTE as text so D is representable. Never equate 0 with discarded or 7 with confirmed.

C's dengue rows permit probable/laboratory/link confirmation for 210 and probable/laboratory confirmation for 220; clinical confirmation is not permitted in those rows. Discard is a separate allowed outcome. These are edition-specific restrictions, not evidence that every generic TIP_CAS code is permitted for either event in every year. H observed TIP_CAS {2,3,5} and AJUSTE {0,3,5,7} in each export. The 607 severe-dengue records with final state 5, and 81 dengue records with CON_FIN 2, need year/version/process reconciliation; they are review signals, not automatic historical-error findings or approved exclusions.

D/S define CLASFINAL as final **clinical severity**: 1 dengue without warning signs; 2 dengue with warning signs; 3 severe dengue; 0 not applicable is restricted to event 580 in S. CLASFINAL is absent from both current headers. No alias to Estado_final_de_caso is established. CON_FIN is vital status, not either of these classification axes. PAC_HOS is hospitalization, not a substitute for severity.

The INS [2025 epidemiological-period-I dengue report](https://www.ins.gov.co/buscador-eventos/Informesdeevento/DENGUE%20PE%20I%202025%20.pdf) describes combining 210/220, excluding adjustment 6/D and reviewing repeated episodes using clinical information. This supplies operational context, not an approved union/deduplication recipe for these local exports. Different event codes and overlapping CONSECUTIVE values alone do not determine case overlap.

### 4.2 Geography and exact names

Residence remains the approved attribution. Current H widths after trimming are COD_DPTO_O/R/N = 2, COD_MUN_O/R = 3, and COD_MUN_N = 5, for every record in both files. Notification municipality is already the full five-character identifier in this export; its prefix matches the department code. Do not construct a seven-character key by prepending COD_DPTO_N. Residence/occurrence municipality components require the corresponding department, after validation against an applicable catalogue. This observed representation does not establish the width of every future export.

S names occurrence municipality COD_MUN and residence municipality MUN_PRO. Candidate mappings are COD_MUN_O and COD_MUN_R respectively; suffix similarity alone does not prove cross-version lineage. A's code/label descriptions and H support the working concepts. Names are reconciliation/display attributes; they must not replace a conflicting valid code or split one municipal code into separate groups. The notebook's initial municipal summary still groups by department, code **and name**; this dictionary's code-based identity rule is not proof that every notebook grouping implements it. No notebook repair was performed in this documentary change.

Preserve COD_DPTO_R + COD_MUN_R for scope and identity; scope is 50/Meta and 73/Tolima. Current catalogue membership does not establish historical boundaries. N reports zero name fallbacks and zero department code/name conflicts for its saved run; its fallback code branch is not an approved future attribution policy. AREA remains occurrence area even when the analysis uses residence. The historical ANO + SEMANA + COD_MUN_O grouping omitted department and does not prove municipal uniqueness or duplicate cases.

### 4.3 Dates, availability and schema changes

C identifies symptom onset as the week reference for 210 and 220 in the consulted edition. Official event semantics are therefore documented; verification that this export's ANO/SEMANA implements them, uses the Colombian calendar and respects boundary years is still pending. ISO/calendar-year comparisons alone do not validate it. Monthly attribution uses INI_SIN under the approved decision.

FEC_CON is patient consultation date. A's provider-establishment wording is a documentary error in that context; do not copy it into this dictionary. Technical consistency rules in S place onset on/before consultation, consultation on/before notification, and hospitalization/death on/after consultation where applicable. Violations are diagnostic signals, not permission to swap dates.

P/M explain FEC_AJU as initial entry when unadjusted or latest adjustment otherwise, and FEC_ARC_XL as Excel-generation date. Do not promise timestamp precision, a revision log or first-availability reconstruction from either. The export's day/month/year strings with time suffixes differ from the technical YYYY-MM-DD representation; a rendering difference alone is not a semantic date error. Keep event time separate from knowledge available at a forecast cutoff. N's seven missing dengue onset dates and 8,556 onset-after-notification alerts concern its Tolima/Meta residence subset, not a new national count.

OCUPACION has 4-, 5- and 8-character values in both files; determine year/catalogue/transformations before decoding or enforcing S's historical four-character CIUO-88 structure. nom_grupo is an Indigenous-group label, not GRU_POB's label. GP_INDIGEN is homelessness, not Indigenous ethnicity. GP_* use 1 yes/2 no and permit multiple memberships (M); missingness must not be converted into no. Population-group terminology varies by edition. estrato includes SIN DATO (3,303 dengue; 21 severe dengue), distinct from codes 1–6 and blanks. fuente is a surveillance-notification mode, not upstream file provenance; its lone observed 0 in dengue is outside the cited 1–5 domain and remains unresolved.

## 5. Empirical derived-state correspondence and unresolved definitions

The following is **H evidence for these exact local bytes**, with spaces removed in memory for comparison. It is not an INS algorithm or an approved eligibility policy.

| Estado_final_de_caso | nom_est_f_caso | confirmados | dengue records | dengue_grave records |
|---|---|---|---:|---:|
| 2 | Probable | 0 | 701,166 | 18,061 |
| 3 | Confirmado por laboratorio | 1 | 891,471 | 31,433 |
| 5 | Confirmado por Nexo Epidemiológico | 1 | 112,967 | 607 |

In all observed records, final state equals TIP_CAS when AJUSTE is 0 or 7, and equals AJUSTE otherwise; confirmados is 1 exactly for observed final states 3/5. va_sispro is constant 1. These relations do not establish validity for unseen states, other events or future exports. In N's residence scope, probable records number 147,297 for dengue and 1,786 for severe dengue. The notebook's all-notification counts remain descriptive counts, not exclusively confirmed cases, deduplicated episodes or a finalized incidence target.

| Unresolved field | Missing official/export specification | Permitted interpretation now |
|---|---|---|
| CONSECUTIVE | Generator, uniqueness domain and stability across years/events/files/revisions. | Traceability candidate only; shared values do not prove shared patients. |
| GRU_POB | Historical code labels, effective years and relationship to multiple GP_* flags. | Population-group concept only; observed codes remain undecoded. |
| confirmados | Official formula and handling of every initial/adjustment state. | Observed indicator/state correspondence only. |
| va_sispro | Meaning of values and processing/validation/linkage semantics. | Opaque system/export field; constant 1 is not proof of validation. |
| Estado_final_de_caso | Official derivation, precedence, scope and effective editions. | Empirical confirmation-status codes; no CLASFINAL equivalence. |
| nom_est_f_caso | Official label catalogue and derivation/version. | Empirical labels paired with state codes. |

A only provides nominal or tautological descriptions for these fields and contains an erroneous duplicate country/UPGD description. It cannot close these gaps. For the other 63 entries, official conceptual support also does not certify source transformations or uniform applicability across all years. Further evidence must refine this file rather than create another dictionary.

## 6. Environmental fields

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

Saved outputs show no empty values in the nine climate variables within the inspected subset. Historical audit evidence preserves that the original local snapshot lacked January 2020 rows for all 76 municipalities; PLAN_010 later incorporated recovered January 2020 municipality-day rows for the local supplied dataset. Absent dates, empty cells and zeros are different conditions. The previously reported 44.6858% rain-zero proportion is an EDA observation, not a missingness rate or proof of source quality.

## 7. Review status and remaining work

Completed in this revision: the former priority-only epidemiological tables have been replaced by one ordered, complete 69-field dictionary for both CSVs; official concepts, aliases, empirical observations and six unresolved operational definitions are distinguished; priorities, coding rules, geographic widths, temporal semantics and references are consolidated here. Environmental definitions remain in section 6. No second dictionary or parallel appendix was created.

Pending: exact export/extraction lineage; historical dictionaries, occupation/military/territorial catalogues; six unresolved operational definitions; case inclusion and episode linkage; reporting availability and late revisions; onset-date anomalies/treatment; upstream provenance/completeness checks for recovered January 2020 climate rows; municipal eligibility and target/channel definition. Observed patterns and rule conflicts do not approve cleaning, filtering, joining or imputing records. Model strategy remains a later methodological decision.

Validation for this documentation revision: exact 69-field coverage and ordered equality must be checked against both actual CSV headers; six U entries must be counted explicitly; local Markdown links and repository-required documentation gates must be checked. Validation outcomes are reported separately from scientific approval. This update does not execute the notebook, change raw files, select a model or approve Stage 2/G2.
