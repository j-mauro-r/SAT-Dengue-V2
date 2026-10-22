# PROD-04 — Dashboard Master User Story

## Status, Authority, and Purpose

**Document status: CLOSED Stage 1 baseline, with an APPROVED product refinement dated 2026-10-21.**
**Human Gate: APPROVED for product scope and phased dashboard delivery.** Stage 1 remains closed. The 2026-10-21 refinement authorizes a read-only E2E MVP and prototype-first contract discovery. G5 was subsequently closed as `NOT_APPROVED`; no champion is selected and no runtime contract is frozen.

This document owns the master dashboard story, proposed screen behavior, chart selection, and acceptance criteria. [PROD-01](PROD-01-business-question.md) owns the business question and geography; [PROD-02](PROD-02-users.md) owns the primary user; [PROD-03](PROD-03-supported-decisions.md) owns the supported human decision. The [product baseline](../product-definition.md), [contract change governance](../../governance/ai-developer-first.md#contract-change-governance), and [master plan](../../roadmap/master-plan.md) remain authoritative for scientific scope and staged delivery.

Status labels throughout:

- **USER REQUIREMENT:** expressly requested behavior retained in the approved Stage 1 product baseline.
- **DRAFT PRODUCT DECISION:** product-level interpretation retained in the approved baseline; technical/scientific details still require their later gates.
- **RESEARCH EVIDENCE:** externally documented practice; does not approve a V2 decision.
- **OPEN DECISION / TO BE FROZEN IN LATER STAGE:** unresolved scope or scientific/contract definition, respectively.

## Master User Story

**As** an epidemiological-surveillance official of the Health Secretariat of Tolima or Meta,
**I want** to consult my department's municipal dengue situation and available T+1/T+2 risk estimates through a read-only dashboard,
**so that** I can identify signals warranting attention or preventive preparation and interpret their period, coverage, origin, model-governance status, and historical evaluation context before exercising human judgment.

A later write-enabled iteration may add monthly input processing and structured expert feedback. Those capabilities are not part of the first read-only E2E MVP.

A prediction supports the decision in PROD-03; it neither guarantees a peak nor automatically selects or executes a public-health action.

## Requirements and Reference Interpretation

| ID | Direction | Authority/status |
|---|---|---|
| R01 | Separate Tolima and Meta tabs; evaluate each department independently. Geographic scope includes all municipalities in each department; eligibility for a valid prediction remains subject to Stage 2. | USER REQUIREMENT and current PROD-01 |
| R02 | A later write-enabled iteration may offer upload of the latest month's departmental file, containing multiple municipalities. | USER REQUIREMENT retained outside the read-only MVP; exact input schema deferred |
| R03 | Without a new upload, retrieve the latest available prediction, including a persisted model-training result when that is the only available result, without retraining. | USER REQUIREMENT |
| R04 | The API supplies the data needed for the endemic channel and all other charts. | USER REQUIREMENT |
| R06 | Select exactly two additional primary charts with rationale from real-world systems. | USER REQUIREMENT; selected designs are DRAFT PRODUCT DECISIONS |
| R07 | Remove the insights and recommendations section for now. | USER REQUIREMENT |
| R08 | Show the reference period, prediction generation date/time, model version, and last data upload date/time. | USER REQUIREMENT |
| R09 | Show the current date, distinct from the data period and upload date. | USER REQUIREMENT |
| R10 | Preserve separate T+1/T+2 traffic-light alerts, complementary information, municipal selection, and basic traceability. | USER REQUIREMENT and existing product baseline |
| R11 | Deliver the first E2E MVP as a read-only vertical slice: persisted result -> API -> dashboard. No dashboard action writes data or triggers training/inference. | APPROVED PRODUCT DECISION — 2026-10-21 |
| R12 | Validate information hierarchy and comprehension through a prototype before freezing the Stage 6 product/prediction/API contracts. | APPROVED PRODUCT DECISION — 2026-10-21 |
| R13 | Show model-governance status and historically scoped evaluation context, including false alerts and onset detection with counts, denominators, period, geography, and horizon. | APPROVED PRODUCT DECISION — 2026-10-21; exact contract fields deferred |
| R14 | Defer expert decision/action feedback and persistence to a later write-enabled iteration. Feedback must remain distinct from the later observed epidemiological outcome. | APPROVED PRODUCT DECISION — 2026-10-21; storage contract deferred |

R05 has been removed following Mauricio's review. Numeric T+1/T+2 case-count projections are outside this story; the endemic channel remains, and future risk is shown through alerts and probabilities.

### Approved Delivery Sequence — 2026-10-21

1. Build a read-only prototype with representative, traceable persisted results and G5 `NOT_APPROVED` displayed as the actual Stage 5 governance state.
2. Validate with the primary user that observed channel state, predicted risk, horizons, limitations, and historical performance context are understandable.
3. Freeze the minimum read-only Product, Prediction, and API Contracts in Stage 6.
4. Implement persisted-result retrieval, API delivery, and dashboard presentation as the first E2E vertical slice.
5. Design the write-enabled monthly-input and expert-feedback iteration separately after the read-only MVP is accepted.

The prototype validates presentation and information needs; it is not a production dashboard, a scientific approval, or a substitute for contract freeze. Until G5 changes, any model output shown must be explicitly labeled evaluation/historical and `NOT_APPROVED` for product integration.

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

### Read-Only MVP and Later Write Capabilities

1. On dashboard opening, retrieve a persisted result for the selected context. Opening, refreshing, switching tabs, and changing municipality/horizon only retrieve data; they do not trigger inference, training, uploads, feedback writes, or other mutations.
2. Every displayed result identifies its origin, actual reference/target periods, model/procedure version, governance status, and evaluation versus operational purpose. Never present a historical/evaluation result as a current approved forecast.
3. When G5 is `NOT_APPROVED`, the interface presents that status and a clear limitation message. It may support review of Stage 5 evidence but must not imply that a champion is approved or that the alert is operationally authorized.
4. If no compatible result is available, explain the state without manufacturing a result or offering a write action inside the read-only MVP.

Monthly upload/inference and structured expert feedback remain approved future directions, governed by PROD-05 and later Stage 6 contracts. They will be implemented only in a separate write-enabled iteration. The future feedback record should link to a stable prediction identity and capture the user's disposition, intended action, rationale, actor, and time; the later observed epidemiological outcome remains a separate record and source of truth.

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
- Model/procedure version.
- Model-governance status, including `NOT_APPROVED` when applicable.
- Result purpose/origin: evaluation, historical, or later approved operational use.
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
- Basic audit information: stable prediction/result identity, reference period, generation timestamp, model/procedure version, governance status, result purpose/origin, and last upload timestamp.
- Historically scoped evaluation context: false alerts/alerts emitted and onsets detected/real onsets, with rate, counts, period, geography, horizon, and procedure identity. AP, AUROC, and Brier may be supplied for a secondary technical view.
- Map-compatible municipal identifiers, data and boundary-source/version association. Geometry delivery versus a separately versioned boundary asset remains an implementation decision; no external forecasting service or patient-level location is required.

The client renders and formats these values. It must not fit an endemic channel, invent probabilities or projected case counts, select scientific thresholds, or compute new alert semantics from the mockup. Missing/contradictory data yields a visible unavailable/inconsistent state for the affected view. Exact fields, endpoints, file formats, validation codes, persistence mechanics, and response schemas belong to PROD-05..08 and the later contract/API stages. No new fields are frozen here.

## Acceptance Criteria — Read-Only MVP

These criteria govern the prototype and first read-only vertical slice. Passing them does not approve G5 or convert evaluation outputs into operational forecasts.

| ID | Given / When | Then |
|---|---|---|
| AC01 | The dashboard opens or the user switches department. | Distinct Tolima and Meta tabs identify the active department; municipality options, results, map, and audit information correspond to that department. No write or inference is triggered. |
| AC02 | The user selects a municipality through the selector or map. | Summaries, endemic channel, probability chart, performance context, and governance status update consistently for that municipality. Municipalities without compatible results remain discoverable. |
| AC03 | A compatible persisted result exists. | The dashboard retrieves it without inference or retraining and shows its evaluation/historical/operational purpose, original periods, stable identity, and model/procedure version. |
| AC04 | No compatible result exists. | A clear state explains the absence; it is never represented as zero probability, low risk, an illustrative result, or an invitation to mutate data inside the read-only MVP. |
| AC05 | The governance state is `NOT_APPROVED`. | The dashboard shows `NOT_APPROVED`, explains that no champion is approved for product integration, and avoids operational language that presents the result as an authorized alert. |
| AC06 | A horizon result is displayed. | Separate T+1/T+2 values show labels as well as colors, probability, applicable threshold, and actual target month/year; observed epidemiological status remains distinct from predicted risk. |
| AC07 | The endemic channel has data. | It shows observed monthly cases through T and API-supplied endemic bands/thresholds. It never plots risk probability as case counts or recalculates the channel in the client. |
| AC08 | The probability comparison has data. | T+1/T+2 use actual target months and a common 0–100% scale. Operational probability thresholds are distinguished from endemic case thresholds, and missing values are not invented. |
| AC09 | The user views the municipal alert map or equivalent table. | Department, horizon, target month, supplied categories, and unavailable states are explicit and consistent across both representations. |
| AC10 | Historical performance context is shown. | False alerts and onset detection include numerator, denominator, rate, evaluation period, geography, horizon, and procedure. The interface never claims that a current prediction is a false alert before its outcome is observed. |
| AC11 | The user inspects freshness and traceability. | Today's Bogota date is separate from reference period, generation time, model/procedure version, result origin, governance status, and upload time. Missing metadata is explicit. |
| AC12 | The interface encounters loading, missing-data, inconsistency, or API errors. | The affected view explains its state without substituting mock data. Values remain accessible as text/tables, and controls and labels work with a keyboard and smaller screens. |
| AC13 | The prototype is reviewed before contract freeze. | The primary user can distinguish observed state from predicted risk, explain T+1/T+2, identify governance status and limitations, and interpret historically scoped false-alert/onset evidence. Required contract changes are recorded before Stage 6 freeze. |
| AC14 | The dashboard is inspected within the MVP scope. | It contains the endemic channel, T+1/T+2 comparison, municipal map/table, governance status, and performance context using API-supplied information. No upload, feedback write, insights/recommendations panel, autonomous advice, training, or scientific recomputation appears. |

The later write-enabled iteration will define separate acceptance criteria for monthly input processing and expert feedback. It must store user disposition/action separately from the subsequently observed epidemiological outcome.

## Open Decisions, Dependencies, and Review Boundary

| Item | Required resolution / owner stage |
|---|---|
| Retained chart direction | Mauricio's latest review retains the horizon-probability chart and municipal predictive-alert map. Exact arrangement and presentation remain subject to review of this draft. |
| Target, channel and coverage | Stage 2 freezes case/target definition, excess/onset/continuation, historical-channel method and valid municipal eligibility/data-quality/history rules. Department-wide geography does not guarantee every municipality a valid output. |
| Alert and probability semantics | Later modeling/evaluation and final contracts establish calibration, thresholds, alert categories and uncertainty meaning. No numerical alert policy is approved by this draft. |
| Monthly loading and feedback | Persisted-result reuse is part of the read-only MVP. PROD-05 and later Stage 6 contracts govern the separate write-enabled iteration for monthly input/inference and expert feedback. |
| Freshness | The proposed timezone/display convention remains subject to review. Actual dates and historical labeling are required; any detailed freshness policy belongs to later documents. |
| Supporting information | PROD-06 specifies climatic context, valid explainability, presentation of the four basic audit values, and chart/table information without restoring the removed recommendations panel. |
| API and persistence | PROD-07/08 provide draft semantics. The reviewed prototype informs the minimal read-only Stage 6 contracts. Feedback/input persistence remains a later contract. No schema or endpoint is approved here. |

This refinement does not implement a dashboard/API/model pipeline, approve G5, select a champion, authorize autonomous interventions, or freeze schemas. Numeric case-count projections remain outside the requirement. The read-only prototype and each later implementation slice require bounded review under the master plan.
