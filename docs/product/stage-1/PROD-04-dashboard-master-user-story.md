# PROD-04 — Dashboard Master User Story

## Status, Authority, and Purpose

**Document status: DRAFT — Phase B, pending Mauricio's review.**
**Human Gate for PROD-04: UNAPPROVED.** Prepared on 2026-10-15 in the existing Stage 1 PR #7. This is a product document, not a functional implementation or an implementation plan. No merge, contract freeze, G0/G1 approval, or Stage 1 completion is implied.

This document owns the master dashboard story, proposed screen behavior, chart selection, and acceptance criteria. [PROD-01](PROD-01-business-question.md) owns the business question and geography; [PROD-02](PROD-02-users.md) owns the primary user; [PROD-03](PROD-03-supported-decisions.md) owns the supported human decision. The [product baseline](../product-definition.md), [contract lifecycle](../../contracts/contract-lifecycle.md), and [master plan](../../roadmap/master-plan.md) remain authoritative for scientific scope and staged delivery.

The latest explicit request authorizes revising PROD-04 in the same PR: retain the dashboard views, simplify operational and audit detail, remove numeric case-count projections, and consolidate visible acceptance criteria. The complete document remains subject to review. Phase A files were inspected at PR head `1bc5e11832518b74b8b4ce9968a75efb4b12789d` and are preserved. PROD-02/03 record approval; PROD-01 has a CLOSED/APPROVED heading alongside an UNAPPROVED body. This status inconsistency is not resolved by this document and does not grant any stage-gate approval.

Status labels throughout:

- **USER REQUIREMENT:** expressly requested behavior, preserved as direction; not approval of this entire document.
- **DRAFT PRODUCT DECISION:** proposed interpretation or design, requiring Mauricio's review.
- **RESEARCH EVIDENCE:** externally documented practice; does not approve a V2 decision.
- **OPEN DECISION / TO BE FROZEN IN LATER STAGE:** unresolved scope or scientific/contract definition, respectively.

## Master User Story

**As** an epidemiological-surveillance official of the Health Secretariat of Tolima or Meta,
**I want** to consult my department's municipal dengue situation and T+1/T+2 risk estimates, use the latest available prediction without uploading again, and explicitly load a new monthly departmental file when available,
**so that** I can identify signals warranting attention or preventive preparation and interpret their period, coverage, and origin before exercising human judgment.

A prediction supports the decision in PROD-03; it neither guarantees a peak nor automatically selects or executes a public-health action.

## Requirements and Reference Interpretation

| ID | Direction | Authority/status |
|---|---|---|
| R01 | Separate Tolima and Meta tabs; evaluate each department independently. Geographic scope includes all municipalities in each department; eligibility for a valid prediction remains subject to Stage 2. | USER REQUIREMENT and current PROD-01 |
| R02 | Offer upload of the latest month's departmental file, containing multiple municipalities. | USER REQUIREMENT; exact input schema deferred |
| R03 | Without a new upload, retrieve the latest available prediction, including a persisted model-training result when that is the only available result, without retraining. | USER REQUIREMENT |
| R04 | The API supplies the data needed for the endemic channel and all other charts. | USER REQUIREMENT |
| R06 | Select exactly two additional primary charts with rationale from real-world systems. | USER REQUIREMENT; selected designs are DRAFT PRODUCT DECISIONS |
| R07 | Remove the insights and recommendations section for now. | USER REQUIREMENT |
| R08 | Show the reference period, prediction generation date/time, model version, and last data upload date/time. | USER REQUIREMENT |
| R09 | Show the current date, distinct from the data period and upload date. | USER REQUIREMENT |
| R10 | Preserve separate T+1/T+2 traffic-light alerts, complementary information, municipal selection, and basic traceability. | USER REQUIREMENT and existing product baseline |

R05 has been removed following Mauricio's review. Numeric T+1/T+2 case-count projections are outside this story; the endemic channel remains, and future risk is shown through alerts and probabilities.

### Mockup Provenance and Boundaries

Inspected on 2026-10-15: [live reference mockup](https://dengue-watch-pro.lovable.app/) and both images recovered from the referenced conversation (`image(4).png`, full dashboard; `image(5).png`, charts and recommendations). Images are reference material, not new repository assets. The live page was inspected in a browser after text retrieval could not render it.

Retain the reference's hierarchy: prominent alerts and probability summaries, observed situation, a large historical/endemic chart, two supporting visualizations, and visible freshness information. Replace its Cali/Bucaramanga city navigation with Tolima/Meta tabs plus municipal selection. Replace its SHAP panel with the proposed municipal alert map; retain a horizon-probability chart adapted to the selected municipality. Remove the insights/recommendations panel.

Do not adopt the mock's illustrative 50% cutoff, P25/P50/P75 channel construction, 95% intervals, example case totals, probabilities, dates, SHAP values, or the title's restriction to severe dengue as approved V2 definitions. The formal case/target definition is deferred to Stage 2. Visual resemblance is a design reference, not pixel-exact acceptance or evidence of model performance.

## Proposed Dashboard Experience — DRAFT

### Context and Navigation

- A header identifies SAT-Dengue V2 and displays today's date in `America/Bogota` (DRAFT display convention).
- Tolima and Meta each have a tab. Each shows its own municipality inventory, data period, available predictions, loading action, and audit context. Switching tabs cannot carry over another department's results.
- A municipality selector drives the selected municipality's summaries, endemic channel, and horizon-probability chart. The map provides departmental context; selecting a municipality on it updates that same selection.
- All municipalities in geographic scope remain discoverable, including those ineligible or lacking data. No prediction is a distinct availability state, never a low-risk color. Display available/eligible coverage against the full departmental inventory, without implying universal predictive coverage.
- Summaries show alert label plus color for each horizon, probability when valid, target month/year, observed reference month and cases, and observed position against the endemic channel when available. Observed status and predicted alert are distinct concepts. No department-level probability is inferred by averaging municipal probabilities.

### Load, Reuse, and Update

1. On dashboard opening, retrieve the latest available persisted prediction for the selected context. Opening, refreshing, switching tabs, and changing municipality/horizon only retrieve data; they do not trigger inference or training.
2. If only a compatible persisted model-training result exists, display it with a historical/model-training label and its actual reference and target periods. Never launch training merely to populate the dashboard or present historical results as current forecasts.
3. The user selects a monthly departmental file and explicitly initiates upload/processing. Show clear validation, processing, completion, or error feedback; mere file selection does not update results.
4. After successful processing, show the available prediction and its basic audit information. If no prediction is available, explain that state and offer the monthly upload action.

Detailed upload validation, persistence, and result-selection policies belong to PROD-05..08. This master story defines only the visible upload and reuse experience.

### Three Primary Visualizations

| Chart | User question | Proposed visual behavior and data |
|---|---|---|
| 1. Monthly endemic channel with observed cases | How does the observed trajectory compare with expected seasonal levels? | Selected municipality; month/year axis; case-count axis; observed line through reference month T; API-provided endemic bands/thresholds with method labels. T+1/T+2 risk is presented in the alerts and probability chart, with actual target months, rather than as projected case counts. |
| 2. Probability of excess by horizon | How does estimated risk differ between next month and the following month? | Two bars or points for the selected municipality, T+1 and T+2 with actual target month/year; common 0–100% scale; values and alert labels. Show applicable API-supplied operational probability threshold(s), clearly distinguished from case-count thresholds. If thresholds differ by horizon, label each separately. |
| 3. Municipal predictive-alert map | Where in this department are signals concentrated for the selected future month? | Municipal choropleth for the active department; explicit T+1/T+2 toggle and target month; API-provided alert categories and compatible probabilities; legend distinguishes unavailable, insufficient-data, and ineligible municipalities from valid alert categories. Selection reveals municipality name/code, horizon, probability, alert, reference period, and generation date. Provide an equivalent municipality table for accessible inspection and map failure. |

Chart 3 is a visualization of predicted alert categories, not a case-count, incidence, or causal-risk map. Chart 2 compares horizons within a municipality, not departments with different periods. The map and equivalent table identify the displayed reference and target periods so users can interpret the departmental context.

### Freshness, Audit, and History

Show today's date separately from these four basic audit values:

- Reference period of the displayed prediction (month/year T).
- Prediction generation date/time.
- Model version.
- Last data upload date/time, or “No user upload recorded” when appropriate.

Use consistent timezone labels. Missing metadata is “Unavailable”; never substitute today's date or invent an upload timestamp for a model-training result. T+1/T+2 displays identify their actual target months. Historical results retain their original dates and are visibly labeled historical. Read-only prediction history remains within the product baseline; its detailed information treatment belongs to PROD-06.

## Evidence-Informed Chart Selection

The sources below were inspected on 2026-10-15. Evidence supports the information needs; chart forms, monthly horizons, and V2 semantics are project proposals. No source establishes that these specific charts improve outcomes in Tolima/Meta.

| Primary source and locator | RESEARCH EVIDENCE | DRAFT PRODUCT DECISION and limit |
|---|---|---|
| Sanchez Tejeda et al. (2023), [EWARS operational implementation in Mexico](https://journals.plos.org/globalpublichealth/article?id=10.1371/journal.pgph.0001691), Introduction, Fig. 1 and caption; Integrated epidemiological surveillance section | EWARS displays endemic context, observed/predicted cases, outbreak probabilities and calibrated alarm cutoffs. The paper describes national surveillance integration and weekly local outputs. | Use a separate horizon-probability chart alongside the endemic channel, making probability thresholds distinct from case thresholds. Two monthly bars are our design; neither its weekly horizon, case definition, model, performance nor response protocol transfers to V2. |
| [Infodengue dashboard](https://info.dengue.mat.br/), “Epidemiological situation by state” and municipality report entry | Its state view offers incidence maps, case counts and municipal epidemiological situation; municipal reports provide alert levels and historical series. | Add a municipal alert map within each departmental tab for geographic review. Using *future* T+1/T+2 V2 predictions on that map is our proposal, not a claim that Infodengue's current-situation maps implement identical forecasts. |
| [Infodengue system description](https://info.dengue.mat.br/informacoes/), reporting-delay correction and transmission classification sections | The system distinguishes notified cases from delay-adjusted nowcasts and publishes weekly analyses through reports, dashboards and API. | Explicitly distinguish observed, forecast and unavailable values and disclose their dates. V2 does not adopt Infodengue nowcasting or alert definitions by citing them. |
| [WHO/TDR EWARS-csd overview](https://tdr.who.int/activities/ewars-csd), “Our work” | Describes piloting/implementation and Mexico's integration into national surveillance. | Confirms EWARS as an operational comparator, not just a UI example. It does not establish V2 readiness or effectiveness. |

**Selection rationale (inference from evidence):** the endemic channel answers the temporal epidemiological question; the probability chart makes the two lead times directly comparable; the municipal map adds the spatial question needed by a departmental user. The three views are complementary. Their exact arrangement requires product review.

**Alternatives considered:** the mock's SHAP chart could aid explanation but depends on a validated model and well-defined local/global attribution semantics. Relevant climatic context and valid explainability remain in the wider product baseline; deferring a dedicated SHAP or climate chart does not silently remove those capabilities. PROD-06 will define their reviewable information treatment. A raw municipal case-count ranking alone favors larger populations and is less aligned with the future-risk question; an incidence chart would need valid population denominators. Neither is selected among the two primary additions in this draft.

The [WHO 2020 dashboard guide landing page](https://www.who.int/publications/i/item/9789240003750) was verified as a relevant publication, but its full PDF could not be retrieved (403). No page-specific claim from that guide is relied upon; the accessible operational paper supplies the detailed EWARS evidence above.

## API Information Responsibilities — DRAFT, Not a Frozen Schema

The API must supply consistent, display-ready domain information for:

- Department/municipality identity, full geographic inventory and prediction eligibility/coverage.
- Observed monthly series through reference month T; case definition/units; endemic bands and epidemiological thresholds with method, period, and geographic provenance.
- Per-municipality/per-horizon probability, alert category, applicable operational probability threshold, actual target month, prediction availability/reason, historical/model-training labeling where applicable, and model version.
- Basic audit information: reference period, generation timestamp, model version, and last upload timestamp.
- Map-compatible municipal identifiers, data and boundary-source/version association. Geometry delivery versus a separately versioned boundary asset remains an implementation decision; no external forecasting service or patient-level location is required.

The client renders and formats these values. It must not fit an endemic channel, invent probabilities or projected case counts, select scientific thresholds, or compute new alert semantics from the mockup. Missing/contradictory data yields a visible unavailable/inconsistent state for the affected view. Exact fields, endpoints, file formats, validation codes, persistence mechanics, and response schemas belong to PROD-05..08 and the later contract/API stages. No new fields are frozen here.

## Acceptance Criteria — DRAFT Product Acceptance Contract

These are testable expectations for the future dashboard, not claims that software exists or tests have passed. Criteria covering proposed behavior become binding when Mauricio approves this document. Scientific/contract dependencies must be resolved before full implementation acceptance.

| ID | Given / When | Then |
|---|---|---|
| AC01 | The dashboard opens or the user switches department. | Distinct Tolima and Meta tabs identify the active department; municipality options, results, map and audit information correspond to that department. |
| AC02 | The user selects a municipality through the selector or map. | Summaries, endemic channel and probability chart update consistently for that municipality; the map retains departmental context. Municipalities without predictions remain discoverable. |
| AC03 | A saved prediction exists and no new file is uploaded. | Opening or refreshing retrieves it without inference or retraining. If only a compatible persisted model-training result exists, show its historical origin and original periods. |
| AC04 | No prediction is available for the selected municipality/context. | A clear state explains the absence and offers monthly upload; missing or ineligible predictions are never shown as zero probability, low risk or illustrative results. |
| AC05 | The user selects a monthly departmental file and explicitly initiates processing. | Selection alone does not update results; the interface shows understandable validation, processing, completion or error feedback and displays the available prediction after successful processing. |
| AC06 | A valid prediction is displayed. | Separate T+1/T+2 alerts show labels as well as colors, valid probabilities and actual target month/year; the observed epidemiological status remains distinct from predicted risk. |
| AC07 | The endemic channel has data. | It shows the selected municipality's observed monthly cases through T, month/year labels, case units, and API-supplied endemic bands/thresholds with a legend. It requires no numeric T+1/T+2 case projection and never plots risk probability as case counts. |
| AC08 | The probability comparison chart has data. | T+1/T+2 use actual target months and a common 0–100% scale; values and alert labels agree with summaries. Supplied operational probability thresholds are distinguished from endemic case thresholds; missing values or thresholds are not invented. |
| AC09 | The user views the municipal alert map or changes its horizon. | The active department, selected T+1/T+2 horizon and target month are explicit; API-supplied alert categories and unavailable states have distinct labels. An equivalent municipality table supports inspection and selection when the map cannot render. |
| AC10 | The user inspects freshness or a historical result. | Today's Bogota date is separate from the reference period, generation date/time, model version and last upload date/time. Original dates remain visible, missing metadata is explicit, and historical results are labeled accordingly. |
| AC11 | The user interacts with the dashboard, including loading, missing-data or API-error states. | The affected view explains its state without substituting mock data, zero values or low-risk alerts. Available chart values are accessible as text/tables, and controls and labels remain readable and operable with a keyboard and on smaller screens. |
| AC12 | The dashboard is inspected within the approved scope. | It contains the endemic channel, T+1/T+2 probability comparison and municipal alert map, using API-supplied domain information. No insights/recommendations panel or automatic intervention advice appears; navigation does not retrain or recompute scientific thresholds. |

## Open Decisions, Dependencies, and Review Boundary

| Item | Required resolution / owner stage |
|---|---|
| Retained chart direction | Mauricio's latest review retains the horizon-probability chart and municipal predictive-alert map. Exact arrangement and presentation remain subject to review of this draft. |
| Target, channel and coverage | Stage 2 freezes case/target definition, excess/onset/continuation, historical-channel method and valid municipal eligibility/data-quality/history rules. Department-wide geography does not guarantee every municipality a valid output. |
| Alert and probability semantics | Later modeling/evaluation and final contracts establish calibration, thresholds, alert categories and uncertainty meaning. No numerical alert policy is approved by this draft. |
| Monthly loading and reuse | PROD-05..08 define detailed operational policies and contracts. This story retains explicit monthly upload and reuse of persisted predictions without retraining. |
| Freshness | The proposed timezone/display convention remains subject to review. Actual dates and historical labeling are required; any detailed freshness policy belongs to later documents. |
| Supporting information | PROD-06 specifies climatic context, valid explainability, presentation of the four basic audit values, and chart/table information without restoring the removed recommendations panel. |
| API and persistence | PROD-07/08 draft information contracts; Stage 6 freezes final contracts; subsequent API/dashboard stages implement and verify this story. No schema or endpoint is approved here. |

Out of scope for this PR update: functional dashboard/API/model/pipeline implementation, automatic interventions or notifications, access-role expansion, new DWP plans, PROD-05..08 authoring, changes to Stage 2+ documents, merge, and stage closure. This story describes future behavior; it is not eight separate implementation HUs.

Review stops at PROD-04. Mauricio may approve or correct this draft in PR #7 before progression to PROD-05. Future story acceptance is assessed against the 12 visible-behavior criteria above. Numeric case-count projections are not a requirement or an acceptance dependency for this story.
