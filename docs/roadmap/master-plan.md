# SAT-Dengue V2 Master Roadmap (Durable Mirror)

This document is the durable project-level mirror of the DWP master planning direction. It summarizes stage goals, dependencies, and stage gates without storing runtime task state.

## DWP Master Plan Status

The durable roadmap is defined here. The operational DWP Full Master Plan for the complete SAT-Dengue V2 lifecycle must exist separately in local `.dwp/` state and be traceable by plan ID. Until that project-level plan is created and verified, its status is **UNVERIFIED**.

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
