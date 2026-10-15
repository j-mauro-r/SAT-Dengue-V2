# SAT-Dengue V2 Master Plan

This document is the single durable master plan for the project. It defines all Stages 0–10, their goals, dependencies, gates, and stage-level progress. Runtime task state remains local.

## Planning and Execution Policy

- A project-wide DWP Full Master Plan is not required and will not be created.
- DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally through bounded user stories (HUs), each with scope, acceptance criteria, validation, and evidence. Do not execute an entire Stage or the project in a single prompt.
- Use DWP only when a concrete HU/task warrants an execution plan because of complexity, risk, dependencies, or work across sessions. Select the appropriate plan format for that bounded objective.
- Record stage progress and gate evidence here; record HU/task acceptance and validation in its issue/PR. No separate DWP master-plan ID is a prerequisite for G0.

## Current Status (2026-10-15)

- Stage 0: **IN PROGRESS — closure evidence pending**.
- Gate G0: **UNVERIFIED** pending independent review evidence required by governance.
- Current Stage: **Stage 0 — Engineering Foundation (closure)**.
- Next Stage: **Stage 1 — Product Definition**, after G0 passes.
- Stages 1–10: **NOT STARTED**; their gates are **UNVERIFIED**.

### G0 Evidence

| Criterion | State | Evidence |
|---|---|---|
| Foundation documentation accepted | PASS | [PR #5](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/5) merged on 2026-10-14 (America/Bogota), merge commit `1abbc08b8429c15b9145119da13cfc955da03067`. |
| DWP conformance | PASS | [Main CI run 38790310683](https://github.com/j-mauro-r/SAT-Dengue-V2/actions/runs/38790310683), commit `4e816d43e92638f773f26bdb2d0ec8929ffeb4c2`: DWP conformance step succeeded. |
| Repository validation baseline | PASS | Same main CI run: Repository Quality, Python Quality, and Unit Tests succeeded, including documentation links and policy/security scans. |
| Independent review evidence | UNVERIFIED | PR #5 has no submitted reviews or discussion comments as inspected on 2026-10-15; its description still marks current-head review pending. No independent review artifact was found in the repository. |

Remaining closure action: supply or perform the independent review required by `docs/governance/ai-developer-first.md` and `docs/operations/validation-and-evidence.md`, resolve or explicitly accept any high/critical findings, and record the evidence. Then update Stage 0 to DONE, G0 to PASS, and Current Stage to Stage 1. The merged PR's historical synchronization warning is no longer an active blocker. This documentation change still requires its own validation, independent review, and Human Gate before merge.

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
