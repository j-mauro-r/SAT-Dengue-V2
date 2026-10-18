# SAT-Dengue V2 — Stage 2 Recognition and Coverage Results

Updated: 2026-10-16. **Stage 2 active; G2 open.** This is the current results reference, replacing accumulated recognition/EDA addenda and the superseded initial brief. Diagnostic completion is separate from data-quality approval.

## Scope and evidence

Case attribution is **residence in Tolima/Meta**, with **symptom onset (`INI_SIN`)** as the approved epidemiological date. Dengue and severe dengue remain separate. Analysis cutoff stays fixed at 2026-10-15; rerun time is not the analytical cutoff.

- [Official notebook](../../../notebooks/01_stage2_residence_onset_eda.ipynb): calculations and saved outputs.
- [Date inconsistency investigation](DATA-01-2013-date-inconsistency-investigation.md): bounded analysis of 8,556 `INI_SIN > FEC_NOT` records using 2012-2014 references.
- [Canonical field matrix](DATA-01-Priority%20Field%20Matrix.md): meanings and unresolved export aliases.
- [Source provenance](DATA-01-Source%20Provenance.md): snapshot identities and lineage limits.
- [Methodological note](nota-metodologica.md): scientific decisions and literature.
- [Master plan](../../roadmap/master-plan.md): stage progress and next work.

No raw correction, date replacement, imputation, case-stream union, channel construction, target definition or training was performed. Raw data remain restricted under the [data policy](../../data/data-policy.md); outputs contain aggregates only.

## Input inventory

| Input | Historical parsed/inventoried rows | Columns | Scope caveat |
|---|---:|---:|---|
| `dengue.csv` | 1,705,604 | 69 | National input; residence scope is smaller. |
| `dengue_grave.csv` | 50,101 | 69 | Same header, separate event stream. |
| `google_earth_engine.csv` | 7,751,898 | 18 | Full climate snapshot; target-department diagnostics are separate. |

Initial line-count estimates are historical; epidemiological totals are also reconciled by the parsed notebook balance. CSV-aware parsing is required. `INI_SIN`, `FEC_NOT`, residence codes and labels are present in both epidemiological inputs. `CLASFINAL` is absent; no export-status alias is assumed.

## Epidemiological findings

| Dataset / department | Residence records | Missing onset | Unparseable onset | Onset after notification |
|---|---:|---:|---:|---:|
| Dengue — Meta | 106,457 | 6 | 0 | 3,597 |
| Dengue — Tolima | 129,044 | 1 | 0 | 4,959 |
| Severe dengue — both | 4,619 | 0 | 0 | 0 |

The 8,556 temporal alerts remain concentrated in onset months of 2013. The diagnostic executed successfully; date consistency is **not approved**. No automatic substitution or exchange of `INI_SIN` and `FEC_NOT` occurred.

High case concentrations in Ibagué and Villavicencio do not alone establish their eventual influence on a municipality-month training panel. Training unit and weighting are unresolved.

## DIVIPOLA territorial comparison

Supplied catalog structure and current code membership were checked. The expected universe contains **29 Meta + 47 Tolima = 76 municipalities**. Source URLs, download date and reported version are now recorded with explicit human-supplied attribution in the provenance register.

| Input | Expected municipalities present | Expected absent | Additional valid codes outside catalogue | Unknown-code records |
|---|---:|---:|---:|---:|
| Dengue | 76 | 0 | 0 | 383 |
| Severe dengue | 71 | 5 | 0 | 21 |
| Climate | 76 | 0 | 0 | 0 |

Severe-dengue municipalities without records: **El Calvario (50245), San Juanito (50686), Casabianca (73152), Herveo (73347) and Murillo (73461)**. Absence does not establish zero cases, incomplete reporting or municipal ineligibility. Those interpretations require further evidence.

The stricter territorial-quality control remains **FAIL** because unresolved exceptions remain. This is an executed diagnostic finding, not an unavailable catalogue or failed notebook execution. The old inventory-absent `BLOCKED` messages have been retired. Diagnostic work is complete with exceptions; all-data completeness is not claimed.

## Temporal and climate coverage

Municipal epidemiological continuity is described separately for each input using onset dates, explicit source windows, observed months and months without records. Months before/after the observed series are distinct from internal gaps. Neither empty periods nor absent severe-dengue municipalities are converted into confirmed zero cases.

Climate diagnostics cover 525,084 target-department rows. The common epidemiological/climate window is 2007-01-01 through 2025-12-31 (6,940 days). All 76 municipalities share 31 dates without climate rows: January 2020. In the inspected target-department subset, nine prioritized climate variables have no empty values and municipality-date duplicates are zero. Rainfall zeros are 44.6858%; runoff zeros are 0.5239%.

Missing dates, empty cells and observed zeros are different. Earlier national climate blanks do not contradict zero blanks in this bounded subset. The cause and treatment of January 2020 remain unresolved. A current DIVIPOLA snapshot does not prove unchanged territorial boundaries throughout the historical series.

## Reproducible aggregate evidence

The notebook exports to `data/interim/stage2_divipola_validation/` (ignored local evidence, regenerated by execution):

| Artifact | Question answered |
|---|---|
| `divipola_catalog_metadata.json` | Which snapshots and supplied provenance were used? |
| `divipola_catalog_validation.csv`, `divipola_department_municipality_counts.csv` | Is catalogue structure consistent, and what is expected? |
| `territorial_coverage_by_code.csv` | Which expected codes occur in each input? |
| `territorial_exceptions.csv`, `territorial_summary_by_dataset.csv` | Which absences and unresolved codes remain? |
| `temporal_continuity_epi.csv`, `temporal_continuity_climate.csv` | What history is present by municipality and input? |
| `coverage_controls_status.csv` | Which current territorial/continuity controls pass or fail? |

The redundant `temporal_continuity_summary.csv` export was retired; its identical control content is maintained only in `coverage_controls_status.csv`. Saved notebook outputs retain the key evidence when ignored CSVs are unavailable in a clean checkout.

## Interpretation safeguards

Occurrence-based national counts from initial recognition are historical and do not govern residence scope. Grouping `ANO + SEMANA + COD_MUN_O` omitted department and could not establish duplicate cases. Shared `CONSECUTIVE` identifiers do not establish overlap between case streams until identifier semantics are verified. Official epidemiological-year definitions do not alone validate an export alias or ISO/calendar comparison.

## Next decisions and stop point

1. **2013 source comparison completed:** PLAN_004/006 compared supplied annual references. PLAN_006 found zero genuine non-equal swapped pairs. Source authenticity and correct dates remain unresolved; see the [current panel review](DATA-03-panel-review.md).
2. Resolve January 2020 climate absence, missing-onset policy, unresolved municipal codes and reporting/zero distinctions.
3. Define case inclusion, adjustment/identifier semantics, municipal eligibility and information availability at historical cutoffs.
4. Establish channel, target Y, leakage rules and Data Contract before G2 review. Geographic training strategy remains open.

The initial brief's restrictions have been superseded only by explicitly authorized bounded increments. This audit authorizes reconciliation and rerunning existing diagnostics; it does not authorize deeper anomaly analysis or data remediation. Stage 2 remains open and G2 is not approved.
