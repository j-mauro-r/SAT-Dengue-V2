# SAT-Dengue V2 Master Plan

This document is the single durable master plan for the project. It defines all Stages 0–10, their goals, dependencies, gates, and stage-level progress. Runtime task state remains local.

## Planning and Execution Policy

- A project-wide DWP Full Master Plan is not required and will not be created.
- DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally through bounded user stories (HUs), each with scope, acceptance criteria, validation, and evidence. Do not execute an entire Stage or the project in a single prompt.
- Use DWP only when a concrete HU/task warrants an execution plan because of complexity, risk, dependencies, or work across sessions. Select the appropriate plan format for that bounded objective.
- Record stage progress and gate evidence here; record HU/task acceptance and validation in its issue/PR. No separate DWP master-plan ID is a prerequisite for G0.

## Current Status — 2026-10-20

Implementation and human gate approval are separate. Current bounded work is on `Stage4/Model-Engineering`, PR #15, following preparation implementation `2e1c919`. Stage 4 delivery 1 references were delivered at `57323fc`; PLAN_021 corrects their previously accredited AP and event evaluation. Implementation progress is not a scientific freeze or gate approval.

| Stage / gate | Implementation state | Gate / evidence state |
|---|---|---|
| Stage 0 foundation / G0 | Foundation delivered in PR #5 | Historical dedicated independent foundation review remains UNVERIFIED. Later reviews do not retroactively supply it. |
| Stage 1 product definition / G1 | Delivered in PR #7 | CLOSED by Mauricio's explicit confirmation; final runtime schemas remain unfrozen. |
| Stage 2 data understanding / G2 | Notebook 03 consolidation, Y, current channel state and bounded EDA implemented and reviewed | G2 OPEN: no explicit Data & Target Freeze recorded. Retired notebooks 01/02 are historical; notebook 03 is the current pipeline. |
| Stage 3 data engineering / G3 | Technical preparation completed: notebook 04, 16 derived features, temporal partitions and reusable train-only preparers | G3 OPEN: PLAN_018 technical closure and tests are evidence, not human gate approval. |
| Stage 4 model engineering / G4 | Shared references corrected in PLAN_021; first XGBoost candidate and notebook06 executed under PLAN_022 / draft PR #15 | G4 OPEN. LightGBM/GAM, operational thresholds and scientific acceptance remain pending. |
| Stages 5–10 / G5–G10 | NOT STARTED | Model comparison, champion, final product contracts, API/dashboard and deployment remain future work. |

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

### Next bounded work — close the handoff, then model

1. Present the existing data/target and preparation evidence for an explicit G2/G3 disposition. Do not equate this documentation update with approval or restart completed EDA. The previously planned 5/7/9-year target sensitivity has no completed evidence here; Mauricio must decide its disposition for the freeze rather than an agent silently deleting it or declaring it completed.
2. Use the corrected reference evaluation, approved selection policy and PLAN_022 XGBoost evidence for the next separately scoped candidate delivery; LightGBM/GAM and scientific gate dispositions remain pending. Reuse notebook 04 modules, saved preparation state and keyed X/Y; select the representation required by each estimator.
3. Keep objectives from 2025-01 reserved. Compare candidates using the same development windows; evaluate calibration, false alarms and outbreak onsets as specified by the product/scientific decisions. No final-block tuning.
4. Update this status table when a bounded milestone or human gate decision changes. Put scientific decisions in the register, executable schemas in contracts and command details in the testing guide; do not copy their inventories here.

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
- Final Input Contract
- Final Feature Contract
- Final Prediction Contract
- Final API Contract

Dependency:
- Stage 5 evidence and product constraints.

Gate G6 — Product Contracts Frozen:
- Product/model/API boundaries are versioned and approved for implementation.

### Stage 7 — API

Deliverables:
- API implementation aligned to frozen contracts
- Contract and integration tests

Dependency:
- Stage 6 contract freeze.

Gate G7 — API Contract Pass:
- API contract, validation, inference integration, and persistence behavior pass.

### Stage 8 — Dashboard

Deliverables:
- Dashboard implementation aligned to product requirements and API contracts
- New-period upload/inference workflow
- Read-only refresh behavior

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
- New-period input -> validation -> inference -> persistence -> API -> dashboard flow passes end to end.

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
