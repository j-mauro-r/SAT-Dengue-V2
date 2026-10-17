# SAT-Dengue V2 — Case Date and Geographic Modeling Strategy

Original review: 2026-10-15. Documentary reconciliation: 2026-10-16.

This note owns approved scientific choices, the previously reviewed literature context and remaining methodological decisions. Field definitions belong to the [canonical matrix](DATA-01-Priority%20Field%20Matrix.md), numerical findings to the [recognition report](DATA-01-Initial%20Recognition%20Report.md), and file/reference identities to the [provenance register](DATA-01-Source%20Provenance.md). Existing diagnostics were rerun during reconciliation; no new scientific analysis or model training was added. Stage 2 remains open and G2 is not approved.

## 1. Approved decisions and open policies

| Topic | Status | Definition |
|---|---|---|
| Product geography | Approved by Mauricio | Municipalities belonging to Tolima and Meta. |
| Output unit | Approved product scope | Municipality and T+1/T+2 horizon. Department tabs collect municipal results; they do not prescribe training granularity. |
| Epidemiological date | Approved by Mauricio | Symptom onset, using `INI_SIN`, confirmed in both input headers and inspected in the saved EDA. |
| Official meaning of `INI_SIN` | Documented by INS | Symptom onset; export-version applicability and date-quality treatment remain separate checks. |
| Missing/invalid onset policy | Pending | No automatic replacement by `FEC_NOT` is approved. |
| Case geography | Approved by Mauricio | Municipality of residence in Tolima or Meta. Occurrence and notification do not replace this attribution. |
| Municipal prediction eligibility | Pending data quality | Geographic inclusion does not guarantee enough history, coverage or quality for a valid prediction. Missing predictions must be explicit. |
| Training unit | Pending comparison | Shared, departmental and municipal fitting remain alternatives; no automatic separate-model rule is approved. |

The [INS dictionary 2018–2020](https://www.ins.gov.co/Direcciones/Vigilancia/Lineamientosydocumentos/3.%20Diccionario_de_datos_Sivigila%202018_2020.pdf) distinguishes symptom onset from notification. Its documented format does not establish the physical format or historical export lineage of our files.

Onset determines the period assigned to a case. Availability determines whether that case could have been used at a historical prediction cutoff. A later notification must not become information assumed known at an earlier cutoff. Notification helps assess availability but cannot reconstruct all subsequent adjustments by itself.

## 2. Previously reviewed project sources

### Expert-session notes

External private reference: `Sesion_1_con_Experto_Notas.docx`, sections 3–4.

The notes advise against starting with independent models for all Colombian municipalities and suggest a bounded pilot, possibly three municipalities chosen objectively. They describe municipality → time series → features → model → T+2 risk and suggest considering symptom onset.

The notes contain no explicit rule equivalent to “two cities require two independent models.” Municipal output does not prove separately fitted parameters. These are consolidated notes rather than a verbatim transcript; absence of that instruction does not prove the expert never expressed it. The historical pilot suggestion does not override the approved Tolima/Meta scope.

### Degree-project proposal

External private reference: `Formato-propuesta_Proyecto-de-grado-Mauricio.pdf`, pages 3–7.

The proposal describes a municipality-month panel, XGBoost/LightGBM/GAM comparison, T+1/T+2 horizons and temporal evaluation with municipal and aggregate results. It does not explicitly fix shared or independently fitted models. A municipal panel alone does not settle that choice.

### Earlier microproject

External private reference: `Reporte_Entrega3_final-2.docx`, section 3.1 and source table.

The report describes two input rows, Cali and Bucaramanga, passed to the Champion to generate four predictions: two municipalities and two horizons. It also documents `INI_SIN` with notification fallback. This is precedent for joint inference, not proof of each artifact's training provenance. Neither those cities nor the fallback policy automatically transfers to V2.

## 3. Previously reviewed literature

These summaries retain the earlier review; this consolidation did not perform a new exhaustive audit of papers, supplements or code.

| Study | Documented geographic strategy | Implication and limitation for V2 |
|---|---|---|
| [Beal et al., 2025](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2024GH001325), sections 2.1–2.3 | Separate city/month models for Cali, Cúcuta, Medellín and Leticia, with different horizons, motivated by seasonal differences. | Local-model precedent for incidence. Its horizons and leave-one-year-out validation are not automatically equivalent to V2 outbreak-onset forecasting under operational temporal validation. |
| [Schlesinger et al., 2024](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2024.1323618/full), introduction and sections 2.3–2.5 | EWARS-csd supports joint municipal modeling with spatiotemporal covariance; configurations are evaluated and optimized locally for 11 municipalities in Bolívar and Cesar. | Shared information and local tuning can coexist. Local calibration does not prove independent fitting. The indicator is weekly hospitalizations. |
| [Wu et al., 2025](https://www.pnas.org/doi/10.1073/pnas.2422335122), results and methods | Location-level forecasts include local and cross-province methods; VAR variants fit by country. Country-specific and general ensemble configurations are compared. | Global evaluation or shared hyperparameters do not establish a universal fitted model. The target is provincial case counts. |
| [Umaña et al., 2026](https://publichealth.jmir.org/2026/1/e79914), methods | Endemic-channel analysis aggregates by occurrence municipality and symptom-onset week, with departmental replication. | Supports considering onset and occurrence, but does not decide predictive-model count. Occurrence in that study does not override V2's approved residence attribution. |
| [Velandia et al., 2026](https://www.nature.com/articles/s41598-026-63542-8), experimental framework and results | National HDG compared with independent LDG fits in five departments, using chronological splits that can retain the same municipalities across periods. | Direct precedent for shared-versus-departmental comparison. U-Net++ spatial risk classification differs from T+1/T+2 outbreak-onset prediction and does not prove transfer to unseen municipalities. |

The review establishes no universal requirement for one model per municipality. Territorial heterogeneity and local performance still need evaluation under shared fitting. These studies do not identify a winning strategy for our data without comparison.

## 4. Alternatives for later evaluation

All alternatives retain municipality-month rows and municipal outputs. Departmental fitting does not mean predicting only a summed departmental total.

| Alternative | Training population | Potential benefit | Risk to examine |
|---|---|---|---|
| Shared Tolima + Meta | Eligible municipal series from both departments | Shares evidence when local outbreak onsets are scarce | Aggregate scores can hide persistent local errors. |
| One fit per department | Tolima municipal series separately from Meta series | Allows different departmental relationships without splitting every series | Less shared evidence; no guarantee of within-department homogeneity. |
| One fit per municipality | Each eligible municipal series separately | Local specialization | Limited months and independent outbreak onsets may weaken fitting, calibration and evaluation. |

These benefits and risks are methodological reasoning, not experimental results. Individual notification counts are not the number of municipality-month training examples after aggregation and lag construction. Concentration of notifications in large cities alone does not determine their influence on the eventual panel; target and weighting choices matter.

Geographic training granularity is separate from the number of algorithms or horizon-specific artifacts. A shared approach can still use different T+1/T+2 artifacts. One monthly inference job can apply shared models or route rows to previously fitted local models; job count does not determine training unit.

## 5. Comparison proposal, pending approval and evidence

Later modeling may compare shared and departmental fitting with identical municipalities, periods, labels, features, horizons and temporal splits. Consider municipal fitting selectively where history and independent onset counts support comparison; no new hierarchical system or nationwide training is proposed.

Fit transformations, feature selection, channels and calibration without future information. Report detected/total onsets, false alarms, PR-AUC and calibration by horizon, department and municipality, alongside municipal averages and aggregate results. Select for stability and local usefulness; specify the selection rule before inspecting the final test block. Municipal endemic channels remain contextual references, with method, windows and zero handling still pending.

This proposal chooses no winner and authorizes no training during Stage 2.

## 6. Current data-quality boundaries

Residence and symptom onset are approved decisions. Official meanings are documented; historical aliases, case eligibility and information-availability rules remain pending.

Saved EDA described onset quality, the 2013 temporal alerts and a shared January 2020 climate gap. It established neither causes nor correction policies. The supplied DIVIPOLA snapshot establishes 76 expected municipalities; dengue and climate contain all 76, while severe dengue contains 71. Code formatting alone does not establish catalogue membership. Climate at residence does not prove where infection was acquired.

No silent fallback dates, discarded year, climate imputation, deduplication or union of dengue streams is approved.

## 7. Completed documentary consolidation

On 2026-10-16 both field matrices were merged into the indexed DATA-01 matrix, stale statements reconciled, current headers checked and file/reference identities recorded. Earlier INS PDF-extraction difficulty is no longer treated as missing official semantics. Verified reference definitions and unproven export lineage remain distinct.

Private sources remain named references; no copies or synchronized `sources/` files were modified. The notebook was subsequently extended with DIVIPOLA diagnostics and rerun; raw inputs were preserved. This note does not claim a new audit of every paper's code, supplements or figures.

## 8. Next bounded work

Investigate source/export evidence for the 2013 anomaly and January 2020 gap, resolve the recorded municipal-code exceptions and establish required-field and case-count semantics before channel and target work. Outbreak onsets can only be counted after channel/label definition and validation.

Later architecture choices must follow that evidence rather than dashboard tab count. Stage 2 remains open; G2 is not approved.

## 2013 source comparison

Mauricio is obtaining the original 2013 SIVIGILA download for comparison with the current export. The comparison has not occurred. Swapping onset and notification when onset is later remains an unapproved hypothesis: reversed order alone does not establish a column swap. Preserve original dates and defer any correction policy until source comparison and sensitivity evidence are reviewed.
