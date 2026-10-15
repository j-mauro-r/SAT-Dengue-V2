# PROD-04 — Dashboard Master User Story

## Status, Authority, and Purpose

**Document status: DRAFT — Phase B, pending Mauricio's review.**
**Human Gate for PROD-04: UNAPPROVED.** Prepared on 2026-10-15 in the existing Stage 1 PR #7. This is a product document, not a functional implementation or an implementation plan. No merge, contract freeze, G0/G1 approval, or Stage 1 completion is implied.

This document owns the master dashboard story, proposed screen behavior, chart selection, and acceptance criteria. [PROD-01](PROD-01-business-question.md) owns the business question and geography; [PROD-02](PROD-02-users.md) owns the primary user; [PROD-03](PROD-03-supported-decisions.md) owns the supported human decision. The [product baseline](../product-definition.md), [contract lifecycle](../../contracts/contract-lifecycle.md), and [master plan](../../roadmap/master-plan.md) remain authoritative for scientific scope and staged delivery.

The explicit current request authorizes drafting PROD-04 in the same PR. Phase A files were inspected at PR head `1bc5e11832518b74b8b4ce9968a75efb4b12789d` and are preserved. PROD-02/03 record approval; PROD-01 has a CLOSED/APPROVED heading alongside an UNAPPROVED body. This status inconsistency is not resolved by this document and does not grant any stage-gate approval.

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
| R03 | Without a new upload, retrieve the latest available prediction, including the last model-training result when that is the only available result. | USER REQUIREMENT |
| R04 | The API supplies the data needed for the endemic channel and all other charts. | USER REQUIREMENT |
| R05 | Show a monthly endemic channel with a projection line at T+1 and T+2. | USER REQUIREMENT; numeric projection feasibility requires resolution below |
| R06 | Select exactly two additional primary charts with rationale from real-world systems. | USER REQUIREMENT; selected designs are DRAFT PRODUCT DECISIONS |
| R07 | Remove the insights and recommendations section for now. | USER REQUIREMENT |
| R08 | Show audit information including date and time of the last data upload. | USER REQUIREMENT |
| R09 | Show the current date, distinct from the data period and upload date. | USER REQUIREMENT |
| R10 | Preserve separate T+1/T+2 traffic-light alerts, complementary information, municipal selection, and traceability. | Approved direction in PROD-01..03 and existing product baseline |

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

1. On dashboard opening, retrieve the latest available successful, persisted result for the selected context. Opening, refreshing, switching tabs, and changing municipality/horizon only retrieve data; they do not trigger inference or training.
2. If the only result is from model training/evaluation, display it with an explicit historical/model-training origin label and its real reference/target periods. Reuse a saved compatible result; never launch training merely to populate the dashboard or relabel a historical result as current operational inference.
3. The user selects a new monthly departmental file and explicitly initiates upload/processing. Show validation, processing, success, or failure. Merely selecting a file does not silently replace displayed results.
4. Validate department, reference period, municipal identifiers/coverage, and required data under the eventual Input Contract. Show actionable errors. A mixed/wrong-department file cannot contaminate the active department. Duplicate, revised, skipped, or out-of-order months require policy in PROD-05/08 rather than silently overwriting history.
5. After validation and successful inference/persistence, display the new result and matching audit context together. Retain prior successful results for history. Pending/failed attempts must not masquerade as the latest successful prediction.
6. On failure, retain the previous valid result with a visible failure/previous-result notice. Distinguish the latest upload attempt from the accepted dataset and from the dataset used by the displayed prediction. If no result exists, show a clear empty state and upload option.

For this draft, “latest” means the latest successful published result eligible for display, with explicit reference period and run time; corrections, historical training publications, and tie-breaking precedence remain OPEN DECISION in PROD-05/07. The API must identify the chosen result and its origin consistently; the client must not guess by sorting unrelated timestamps. This proposal does not require a fresh prediction for every scoped municipality when coverage is incomplete.

### Three Primary Visualizations

| Chart | User question | Proposed visual behavior and data |
|---|---|---|
| 1. Monthly endemic channel with observed cases and T+1/T+2 projection | How does the observed trajectory compare with expected seasonal levels, and what is projected next? | Selected municipality; month/year axis; case-count axis; observed line through T; API-provided endemic bands/thresholds with method labels; forecast boundary and visually distinct projection line at T+1/T+2. Dates must cross year boundaries correctly. Show uncertainty only when supplied with a defined method and coverage level. |
| 2. Probability of excess by horizon | How does estimated risk differ between next month and the following month? | Two bars or points for the selected municipality, T+1 and T+2 with actual target month/year; common 0–100% scale; values and alert labels. Show applicable API-supplied operational probability threshold(s), clearly distinguished from case-count thresholds. If thresholds differ by horizon, label each separately. |
| 3. Municipal predictive-alert map | Where in this department are signals concentrated for the selected future month? | Municipal choropleth for the active department; explicit T+1/T+2 toggle and target month; API-provided alert categories and compatible probabilities; legend distinguishes unavailable, insufficient-data, and ineligible municipalities from valid alert categories. Selection reveals municipality name/code, horizon, probability, alert, reference period, and run. Provide an equivalent municipality table for accessible inspection and map failure. |

Chart 3 is a visualization of predicted alert categories, not a case-count, incidence, or causal-risk map. Chart 2 compares horizons within a municipality, not departments with different periods. The map and equivalent table must disclose any municipalities using different periods/runs and exclude them from an apparently same-period comparison unless explicitly labeled; no silent mixing.

### Case Projection Is a Separate Scientific Requirement

**OPEN DECISION — material feasibility:** R05 requests numeric case projections on the case-count axis. The baseline objective is risk of excess/onset; a classifier's probability is not a case forecast. Do not convert 78% risk into 78 cases or multiply a probability by the endemic threshold to fabricate a line.

The required end state remains a validated API-supplied case projection for T+1/T+2, with target definition and provenance compatible with observed cases. Whether an existing model can supply it or a separately validated estimation method is necessary requires Mauricio's decision and later scientific evaluation; this document selects neither a regression model nor a new target. Until resolved, the channel may show observed data, endemic context, and labeled future month positions with “Case projection unavailable”; this is a degraded state, **not acceptance of R05 as complete**. Risk estimates remain on Chart 2. The final implementation cannot claim full story acceptance while R05 is unresolved.

### Freshness, Audit, and History

Display separate, clearly labeled values for:

- Today's date.
- Latest upload attempt: date/time and outcome, when known.
- Last accepted data upload: date/time and reference month, or “No user upload recorded”.
- Displayed prediction: reference month T, actual target months, input availability cutoff/as-of when known, generation date/time, result/run identifier, model version, and origin (operational inference or model-training/historical result).
- Upload/dataset association for that prediction; if the latest accepted upload has no successful prediction, state that the displayed result still belongs to the previous dataset.

Never invent an upload timestamp for a training result. Render available timestamps consistently with timezone; missing audit metadata is “Unavailable”, not today's date. A historical target month that has already passed must remain historical and be labeled accordingly. A quantitative stale-data tolerance is OPEN DECISION; displaying actual dates is required regardless of that policy. Provide read-only access to persisted prediction history with original periods/origins; selecting a historical result must visibly label historical mode and keep its associated audit metadata together.

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
- Observed monthly series; case definition/units; endemic bands and epidemiological thresholds with method, period, and geographic provenance; independently valid case projections and uncertainty metadata when available.
- Per-municipality/per-horizon probability, alert category, applicable operational probability threshold, actual target month, prediction availability/reason, origin, and run/model identity.
- Reference period, cutoff/as-of, generation timestamp, input dataset/upload association, upload timestamps/status, and retrievable prediction history.
- Map-compatible municipal identifiers, data and boundary-source/version association. Geometry delivery versus a separately versioned boundary asset remains an implementation decision; no external forecasting service or patient-level location is required.

The client renders and formats these values. It must not fit an endemic channel, invent probabilities/projections, select scientific thresholds, or compute new alert semantics from the mockup. Missing/contradictory data yields a visible unavailable/inconsistent state for the affected view. Exact fields, endpoints, file formats, validation codes, persistence mechanics, and response schemas belong to PROD-05..08 and the later contract/API stages. No new fields are frozen here.

## Acceptance Criteria — DRAFT Product Acceptance Contract

These are testable expectations for the future dashboard, not claims that software exists or tests have passed. Criteria covering proposed behavior become binding when Mauricio approves this document. Scientific/contract dependencies must be resolved before full implementation acceptance.

| ID | Given / When | Then |
|---|---|---|
| AC01 | The dashboard opens. | It exposes distinct Tolima and Meta tabs and identifies the active department; no Cali/Bucaramanga default or severe-dengue-only claim is inherited from the mock. |
| AC02 | The user switches departments after selecting a municipality. | Municipality options, results, map, coverage and audit belong to the new department; no previous department's data is presented as its own. Switching makes no inference/training request. |
| AC03 | A scoped municipality lacks sufficient data or eligibility. | It remains discoverable and displays its availability/reason; it is not omitted from coverage or assigned a low-risk alert by default. |
| AC04 | A saved successful result exists and no new file is uploaded. | Opening/reopening/refreshing retrieves that result with its original periods and metadata; no inference or training is triggered. |
| AC05 | Only a compatible persisted model-training result exists. | It is shown with training/historical origin, actual T/target dates and model/run identity; upload time is absent unless real, and expired horizons are labeled historical. |
| AC06 | No compatible saved result exists. | An empty state explains the absence and offers upload; the page fabricates neither example predictions nor a green alert. |
| AC07 | The user selects a file, then explicitly initiates processing. | The interface identifies department and candidate period, shows validation/processing state, and prevents accidental duplicate submission while pending; mere file selection does not replace results. |
| AC08 | Validation rejects a wrong/mixed department, invalid period/municipality or missing required data under the eventual contract. | A useful error identifies the issue; no invalid prediction is published or successful-upload status fabricated. Correction/duplicate-period policy follows PROD-05/08. |
| AC09 | Validation, inference and persistence succeed. | New results, dataset association and audit appear consistently; T+1/T+2 are relative to the accepted reference month, and previous successful results remain retrievable. |
| AC10 | Upload/inference fails, or a newer accepted dataset has no successful prediction. | Any prior valid result stays explicitly labeled as previous with its own dates; failure/latest-attempt status is visible and cannot overwrite its provenance. With no prior result, show the empty/error state. |
| AC11 | A municipality and a persisted result are selected. | Summaries expose separate T+1/T+2 alert labels, valid probabilities, target month/year, observed status, and data/run context; conflicting horizons remain separate and no automatic public-health action is prescribed. |
| AC12 | The endemic channel renders valid data. | Month/year labels, case units, observed line through T, supplied endemic bands/threshold legend, and a clear observed/forecast boundary are present for that municipality and case definition. |
| AC13 | Valid case projections are supplied for both horizons. | A distinct projection line plots T+1/T+2 on the same case-count scale with dated points and available uncertainty metadata. December T correctly produces January/February of the next year. |
| AC14 | Only risk probabilities, not validated case projections, are supplied. | No probability is plotted as case counts and no forecast line is fabricated. The chart states projection unavailable; R05/AC13 remain unmet, preventing full story acceptance. |
| AC15 | The probability chart renders. | T+1/T+2 use actual target month/year and a common 0–100% axis; values/labels match summaries and applicable API thresholds, with horizon-specific differences labeled. A case threshold is not shown as a probability cutoff. |
| AC16 | The municipal map horizon changes. | The map and legend identify that horizon and month; municipalities use matching API alerts, unavailable/ineligible states are distinct, and different periods/runs are disclosed rather than silently compared. |
| AC17 | A municipality is selected on the map or selector. | Selected-municipality summaries and Charts 1/2 agree; the departmental map retains context. The equivalent municipality table provides the same values/selection access if the map cannot render. |
| AC18 | A chart lacks data, the API fails, or a response conflicts with active context/run. | The affected view reports loading/error/unavailable/inconsistent state and a safe retry where applicable; no zero value, low-risk category, mismatched series, or mock data substitutes for missing information. |
| AC19 | The user inspects dates and audit. | Today's Bogota date, last upload attempt/status, last accepted upload, T, actual target months, generation time, origin, run/model and associated dataset are separately identifiable where available; missing metadata is explicitly unavailable. |
| AC20 | Dates are old or a historical prediction is selected. | Original dates/origin remain visible and historical mode is explicit; no date is refreshed merely by viewing. Any eventual staleness warning uses an approved policy. |
| AC21 | Probability thresholds, case thresholds or uncertainty are absent. | The interface says the relevant information is unavailable; it invents no 50% cutoff, P75 rule, 95% interval, onset/continuation label or green category. Uncertainty is named according to its validated meaning. |
| AC22 | The dashboard is inspected for the current scope. | Exactly the three selected primary visualizations are specified; no insights/recommendations panel, SHAP primary chart or generated intervention advice appears. Data-quality notices and factual legends remain allowed. |
| AC23 | The user navigates with keyboard or cannot distinguish colors. | Tabs, selectors, upload and history controls are operable; alert labels accompany color, legends identify series, and chart values are available as text or tables. On smaller screens all controls, dates and chart labels remain reachable/readable. |
| AC24 | The user changes municipality, horizon or prediction-history selection. | Values and metadata derive from the selected API context/result; the client neither retrains nor recomputes epidemiological thresholds or alert semantics. |

## Open Decisions, Dependencies, and Review Boundary

| Item | Required resolution / owner stage |
|---|---|
| Additional chart approval | Mauricio validates the horizon-probability chart and municipal predictive-alert map proposed here. External evidence does not replace this product decision. |
| Numeric T+1/T+2 case line | Mauricio resolves the output requirement with scientific feasibility evidence; compatible projection method/target must be validated before R05/AC13 can pass. Risk probability alone is insufficient. |
| Target, channel and coverage | Stage 2 freezes case/target definition, excess/onset/continuation, historical-channel method and valid municipal eligibility/data-quality/history rules. Department-wide geography does not guarantee every municipality a valid output. |
| Alert and probability semantics | Later modeling/evaluation and final contracts establish calibration, thresholds, alert categories and uncertainty meaning. No numerical alert policy is approved by this draft. |
| Loading and result precedence | PROD-05/07/08 specify revised/duplicate/out-of-order periods, partial municipal success, latest-result precedence and historical training-result publication rules. Reuse requires persisted compatible outputs. |
| Freshness | Mauricio reviews the proposed timezone/display and stale-data behavior; exact tolerated age is undecided. Actual dates and historical labeling are required. |
| Supporting information | PROD-06 specifies climatic context, valid explainability, audit display detail, and chart/table information without restoring the removed recommendations panel. |
| API and persistence | PROD-07/08 draft information contracts; Stage 6 freezes final contracts; subsequent API/dashboard stages implement and verify this story. No schema or endpoint is approved here. |

Out of scope for this PR update: functional dashboard/API/model/pipeline implementation, automatic interventions or notifications, access-role expansion, new DWP plans, PROD-05..08 authoring, changes to Stage 2+ documents, merge, and stage closure. This story describes future behavior; it is not eight separate implementation HUs.

Review stops at PROD-04. Mauricio may approve or correct this draft in PR #7 before progression to PROD-05. Full future story acceptance requires all applicable criteria, including the requested case-projection line; partial/degraded rendering is not a substitute for a resolved product/scientific requirement.
