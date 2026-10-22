# SAT-Dengue V2 Master Plan

This document is the single durable master plan for the project. It defines all Stages 0–10, their goals, dependencies, gates, and stage-level progress. Runtime task state remains local.

## Planning and Execution Policy

- A project-wide DWP Full Master Plan is not required and will not be created.
- DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally through bounded user stories (HUs), each with scope, acceptance criteria, validation, and evidence. Do not execute an entire Stage or the project in a single prompt.
- Use DWP only when a concrete HU/task warrants an execution plan because of complexity, risk, dependencies, or work across sessions. Select the appropriate plan format for that bounded objective.
- Record stage progress and gate evidence here; record HU/task acceptance and validation in its issue/PR. No separate DWP master-plan ID is a prerequisite for G0.

## Current Status — 2026-10-21

Implementation and human gate approval are separate. Mauricio accepted G4 and exact freeze proposal `66d7208066476b027721182d185770d2522dfe5d891caf4b3b2759177dcc5e09`; PLAN_028 then executed the authorized frozen 2025 evaluation without retuning. On 2026-10-21 Mauricio accepted the scientific disposition G5 `NOT_APPROVED`: Stage 5 is closed, no champion is selected, and model integration remains blocked. The approved next product step is a prototype-first, read-only E2E MVP that presents traceable persisted evaluation results and their `NOT_APPROVED` status without claiming operational prediction.

| Stage / gate | Implementation state | Gate / evidence state |
|---|---|---|
| Stage 0 foundation / G0 | Foundation delivered in PR #5 | Historical dedicated independent foundation review remains UNVERIFIED. Later reviews do not retroactively supply it. |
| Stage 1 product definition / G1 | Delivered in PR #7 | CLOSED by Mauricio's explicit confirmation; final runtime schemas remain unfrozen. |
| Stage 2 data understanding / G2 | Notebook 03 consolidation, Y, current channel state and bounded EDA implemented and reviewed | G2 OPEN: no explicit Data & Target Freeze recorded. Retired notebooks 01/02 are historical; notebook 03 is the current pipeline. |
| Stage 3 data engineering / G3 | Technical preparation completed: notebook 04, 16 derived features, temporal partitions and reusable train-only preparers | G3 OPEN: PLAN_018 technical closure and tests are evidence, not human gate approval. |
| Stage 4 model engineering / G4 | References corrected in PLAN_021; XGBoost in PLAN_022; three families and two controlled XGBoost ablations executed in PLAN_023 / draft PR #15 | G4 ACCEPTED by Mauricio for the exact PLAN_028 proposal/protocol on 2026-10-21. This does not approve a champion or G5. |
| Stage 5 / G5 | PLAN_027 corrected development calibration/threshold availability; PLAN_028 executed and reproduced six frozen final model/preparer procedures over the complete 2025 block. All six candidate/horizon procedures are `does_not_meet`. | CLOSED with Mauricio's accepted disposition G5 `NOT_APPROVED`; champion `not_selected`. The 2025 block is consumed for this comparison. |
| Stage 6 / G6 | Prototype-first read-only product discovery is approved. The prototype and minimal contracts may use persisted historical/evaluation results with visible `NOT_APPROVED` governance status. Operational model integration remains BLOCKED. | G6 OPEN; no champion may be connected to API or dashboard. |
| Stages 7–10 / G7–G10 | NOT STARTED | API/dashboard model integration, deployment and later gates remain future work. |

Mauricio authorized the bounded preparation implementation before a formal G2 freeze was recorded. Record that actual progression without inventing a past approval. Stage dependencies below remain the acceptance order; branch names, plan completion and passing tests do not themselves close gates.

The separate local `PLAN_019_notebook04_runtime_acceptance` completed actual fresh-kernel execution and real-artifact acceptance (3/3 criteria), preserving scientific sources. Stage 4 PLAN_020 then implemented simple references under explicit bounded authority. Its accredited AP/onset results require PLAN_021's correction; the historical approval is preserved rather than rewritten. The approved selection policy is owned by the Stage 4 contract/README and DEC-123. No candidate search, final-block comparison or champion is authorized by the corrective delivery.

### Current deliverables and authoritative evidence

| Delivered scope | Evidence owner | What it does not establish |
|---|---|---|
| Source decisions, residence/onset, supplied 2013 records unchanged, all notification classifications and coverage zeros | [Scientific decision register](../product/traking-concluciones.md), DEC-113/114/118/120/122 | Certified reporting completeness or historical operational availability |
| All 69 source-field definitions and explicit unresolved semantics | [Active canonical matrix](../product/stage-2/DATA-01-Priority%20Field%20Matrix.md) | Selection of all fields as predictors; six insufficient operational definitions remain explicit |
| Individual consolidated file, monthly climate panel, Y T+1/T+2 and current four-zone channel | [Notebook 03](../../notebooks/03_consolidated_dataset_pipeline.ipynb), [construction record](../product/stage-2/CH1-dataset-construction-candidate.md) and local construction contract/manifest | Final model suitability or G2 approval |
| 16 derived candidates, 28 deterministic features, 29 raw model inputs, separate X/Y and eight temporal windows | [Preparation workflow and contract](../product/stage-3/README.md), [final technical evidence](../product/stage-3/milestone-3-validation.md), notebook 04 | Predictive utility, estimator compatibility or performance |
| Executed code-only notebook, immutable artifact identities and training-only transformations | Same preparation evidence and local PLAN_018 journal/review | A trained or deployed predictor |

The five-value channel rule is **five historical observations of the same calendar month from the five years before the target year**, with required month-level history and no future periods. Entire historical years need not have closed (DEC-122). November 2024 → January 2025 can use January 2020–2024. Current `zona_canal_t` describes T; future Y remains an outcome, never an input. General dengue defines the initial target; severe dengue stays separate. Combining streams for Y is a later experiment.

January 2020 climate has been recovered/incorporated for the 76 reviewed municipalities (2,356 municipality-days). Monthly aggregation, numerical percentiles, evaluability, current zones and temporal selection are implemented; they are no longer blank implementation tasks. Source lineage and retrospective-availability limits remain explicit in their evidence owners.

### Next bounded work

1. Present the existing data/target and preparation evidence for an explicit G2/G3 disposition. Do not equate this documentation update with approval or restart completed EDA. The previously planned 5/7/9-year target sensitivity has no completed evidence here; Mauricio must decide its disposition for the freeze rather than an agent silently deleting it or declaring it completed.
2. Build and review a read-only dashboard prototype using representative, traceable persisted evaluation data and the accepted G5 `NOT_APPROVED` governance status. The prototype validates comprehension and information hierarchy; it does not freeze contracts or approve a model.
3. Use the reviewed prototype to freeze the minimal read-only Product, Prediction, and API Contracts in Stage 6. Then implement the persisted-result -> API -> dashboard vertical slice. Keep monthly input/inference and expert-feedback persistence as a later write-enabled iteration.
4. If further scientific work is authorized, use a separate bounded plan and protocol for the single recommended experiment: conservative shared-threshold selection with nested rolling temporal development. Do not optimize on consumed 2025 results; require a later independent period or predeclared nested outer validation.

Historical experiments, old PR reconciliation instructions and local plan failures are provenance, not a recurring analysis backlog. Reopen an analysis only for a concrete unresolved question that affects the next decision. No new EDA chapter is required by this documentation audit.

### Historical foundation evidence

- [PR #5](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/5) merged on 2026-10-14, commit `1abbc08b8429c15b9145119da13cfc955da03067`.
- [Main CI run 38790310683](https://github.com/j-mauro-r/SAT-Dengue-V2/actions/runs/38790310683) passed on commit `4e816d43e92638f773f26bdb2d0ec8929ffeb4c2`; this is dated CI evidence, not current full-workspace conformity.
- Independent foundation review remains UNVERIFIED. Current audit/review does not claim to supply the missing historical review.

## Stage Plan

### Stage 0 — Engineering Foundation

Deliverables:
- Governance model
- Knowledge architecture
- Cross-cutting standards
- DWP-enabled workflow

Gate G0 — Engineering Foundation Ready:
- Foundation documentation accepted.
- DWP conformance passes.
- Repository validation baseline is green.
- Independent review evidence is recorded under the governance and validation policies.

### Stage 1 — Product Definition

Deliverables:
- Product goals and user workflow definition
- Dashboard functional requirements baseline
- Draft information needs for input/output contracts

Dependency:
- Stage 0 complete.

Gate G1 — Product Contract Ready:
- User, decision-support goals, dashboard capabilities, and inference workflow are approved.

### Stage 2 — Data Understanding

Deliverables:
- Data source characterization
- Data quality profile
- Endemic-channel analysis
- Target definition
- Data Contract draft/freeze
- Target Freeze

Dependency:
- Stage 1 product direction available.

Gate G2 — Data & Target Freeze:
- Data sources, temporal rules, target definition, and leakage constraints are approved.

### Stage 3 — Data Engineering

Deliverables:
- Reproducible data preparation pipeline
- Data quality controls
- Temporal split implementation
- Feature contract baseline

Dependency:
- Stage 2 Data & Target Freeze.

Gate G3 — Data Engineering Ready:
- Reproducible training dataset and quality/anti-leakage checks pass.

### Stage 4 — Model Engineering

Deliverables:
- Baseline implementations
- XGBoost candidate
- LightGBM candidate
- GAM candidate
- Planned ablation experiments
- Experiment tracking evidence

Dependency:
- Stage 3 pipeline and contracts ready.

Gate G4 — Candidate Models Ready:
- Candidate models and baselines complete under a common evaluation protocol.
- PLAN_023 adds LightGBM and Bernoulli/logit additive GAM, preserving the approved
  AP/Brier/simplicity policy and all eight cohorts. Notebook05/06 use fresh kernels;
  five experiments (three full candidates, two fixed-parameter XGBoost ablations)
  provide40 saved outer models,3,344 predictions each and territorial support.
- Frozen budget264 fits per run; the budget-guard correction requires a second
  identical run,528 actual fits in two preserved identities. No search expansion.
- Technical results and limitations: [Stage4 evidence](../product/stage-4/README.md).
  This supplies candidate-readiness evidence without accepting G4 or choosing a champion.
- Stage5 handoff: review temporal/territorial variation, calibration and an approved
  operational alert criterion; establish the reserved-evaluation protocol before
  accessing objectives from2025-01. Retrospective availability remains unproven.

### Stage 5 — Evaluation and Quality Assurance

Deliverables:
- Temporal validation and comparative evidence
- Calibration and threshold evidence
- Outbreak-onset evaluation
- Champion candidate recommendation

Dependency:
- Stage 4 candidate runs complete.

Gate G5 — Champion Approved:
- Champion recommendation is evidence-backed and approved for product integration.

### Stage 6 — Product Contract Freeze

Deliverables:
- Reviewed read-only dashboard prototype and resolved information hierarchy
- Final Input Contract for the implemented product slice
- Final Feature Contract
- Final Prediction Contract
- Final API Contract
- Explicit boundary for the later write-enabled input/feedback iteration

Dependency:
- Stage 5 evidence and product constraints.

Gate G6 — Product Contracts Frozen:
- The primary user has reviewed the read-only prototype.
- Product/model/API boundaries for the first vertical slice are versioned and approved for implementation.
- Model integration remains contingent on an approved G5 champion.

### Stage 7 — API

Deliverables:
- Read-only API implementation aligned to frozen contracts
- Persisted-result retrieval without training/inference side effects
- Contract and integration tests

Dependency:
- Stage 6 contract freeze.

Gate G7 — API Contract Pass:
- API contract, validation, inference integration, and persistence behavior pass.

### Stage 8 — Dashboard

Deliverables:
- Read-only dashboard MVP aligned to product requirements and API contracts
- Governance/performance context and explicit unavailable states
- Read-only refresh, filtering, and navigation behavior
- Write-enabled upload/inference and expert-feedback workflow only in a later approved iteration

Dependency:
- Stage 7 API readiness.

Gate G8 — Dashboard Functional Pass:
- Approved user journeys and dashboard acceptance criteria pass.

### Stage 9 — E2E and Deployment

Deliverables:
- End-to-end validation
- Packaging/deployment readiness
- Deployment evidence for the academic environment

Dependency:
- Stages 7 and 8 complete.

Gate G9 — E2E / Deployment Pass:
- First milestone: persisted approved result -> read-only API -> dashboard flow passes end to end.
- A later write-enabled milestone, when approved, validates input -> inference -> persistence and separate feedback capture end to end.

### Stage 10 — Monitoring, Maintenance, Final Review

Deliverables:
- Monitoring and maintenance operating model
- Retraining guidance
- Final governance, scientific, and product review

Dependency:
- Stage 9 complete.

Gate G10 — Final Review Pass:
- No unresolved critical/high findings and final evidence package is complete.

## Ordering Constraint (non-negotiable)

Product Definition -> Dashboard requirements -> draft information contracts -> Data Understanding -> Data/Target Freeze -> Data Engineering -> modeling -> QA/Champion -> final contracts -> API -> Dashboard -> E2E/deployment -> monitoring/final review
