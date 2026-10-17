# SAT-Dengue V2 Master Plan

This document is the single durable master plan for the project. It defines all Stages 0–10, their goals, dependencies, gates, and stage-level progress. Runtime task state remains local.

## Planning and Execution Policy

- A project-wide DWP Full Master Plan is not required and will not be created.
- DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally through bounded user stories (HUs), each with scope, acceptance criteria, validation, and evidence. Do not execute an entire Stage or the project in a single prompt.
- Use DWP only when a concrete HU/task warrants an execution plan because of complexity, risk, dependencies, or work across sessions. Select the appropriate plan format for that bounded objective.
- Record stage progress and gate evidence here; record HU/task acceptance and validation in its issue/PR. No separate DWP master-plan ID is a prerequisite for G0.

## Current Status — 2026-10-16

| Stage / gate | Current state | Basis |
|---|---|---|
| Stage 0 foundation / G0 | Foundation delivered; G0 review evidence UNVERIFIED | PR #5 merged; historical CI passed. A dedicated independent foundation review has not been established. This evidence gap is retained, not retroactively waived. |
| Stage 1 product definition / G1 | CLOSED by human confirmation | Mauricio explicitly confirmed Stage 1 closure after merging PR #7 and directed progression to Stage 2. Product scope is approved; final input/prediction/API schemas remain unfrozen. |
| Stage 2 / G2 | IN PROGRESS / OPEN | Recognition, residence/onset EDA and municipal-coverage diagnostics completed. See [current results](../product/stage-2/DATA-01-Initial%20Recognition%20Report.md). No Data & Target Freeze is approved. |
| Stages 3–10 | NOT STARTED; gates UNVERIFIED | Preparation, modeling and runtime product implementation remain future work. |

The human-authorized progression to Stage 2 is recorded separately from the unresolved historical G0 evidence. No new gate approval is inferred from code execution or from this audit.

### Completed Stage 2 work and next decisions

- Documentary definitions consolidated; residence in Tolima/Meta and symptom onset (`INI_SIN`) are approved.
- Bounded EDA and DIVIPOLA territorial/continuity diagnostics completed with exceptions. Supplied DANE provenance is recorded; diagnostic completion does not establish complete reporting or historical boundary validity.
- **Next:** investigate the 2013 onset-after-notification anomaly. Mauricio is downloading the original 2013 SIVIGILA source; comparison has not yet occurred. Date swapping is a hypothesis, not an approved correction.
- Then resolve January 2020 climate absence, missing-onset and case-inclusion/identifier policies, municipal eligibility, historical availability/leakage rules, endemic-channel method, target Y and Data Contract.
- Model granularity remains open. Stage 3 requires explicit G2 approval.

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
