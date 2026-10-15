# SAT-Dengue V2 Master Roadmap (Durable Mirror)

This document is the durable project-level mirror of the DWP master planning direction. It summarizes stage goals, dependencies, and gates without storing runtime task state.

## Stage Plan

### Stage 0 — Engineering Foundation

Deliverables:
- Governance model
- Knowledge architecture
- Cross-cutting standards
- DWP-enabled workflow

Gate:
- Foundation documentation and validation baseline accepted.

### Stage 1 — Product Definition

Deliverables:
- Product goals and user workflow definition
- Dashboard functional requirements baseline

Dependency:
- Stage 0 complete.

### Stage 2 — Data Understanding

Deliverables:
- Data source characterization
- Target definition hypotheses

Dependency:
- Stage 1 product direction available.

### Stage 3 — Data Engineering

Deliverables:
- Reproducible data preparation design
- Data quality controls

Dependency:
- Stage 2 understanding and data/target decisions.

### Stage 4 — Model Engineering

Deliverables:
- Candidate model implementations
- Experiment protocol execution

Dependency:
- Stage 3 pipelines and quality controls.

### Stage 5 — Evaluation and Quality Assurance

Deliverables:
- Temporal validation and comparative evidence
- Champion candidate recommendation

Dependency:
- Stage 4 candidate runs complete.

### Stage 6 — Product Contract Freeze

Deliverables:
- Finalized information/output contracts
- API boundary freeze inputs

Dependency:
- Stage 5 evidence and product constraints.

### Stage 7 — API

Deliverables:
- API implementation aligned to frozen contracts

Dependency:
- Stage 6 contract freeze.

### Stage 8 — Dashboard

Deliverables:
- Dashboard implementation aligned to product requirements and API contracts

Dependency:
- Stage 7 API readiness.

### Stage 9 — E2E and Deployment

Deliverables:
- End-to-end validation and deployment readiness

Dependency:
- Stage 7 and 8 complete.

### Stage 10 — Monitoring, Maintenance, Final Review

Deliverables:
- Monitoring and maintenance operating model
- Final governance and quality review

Dependency:
- Stage 9 complete.

## Ordering Constraint (non-negotiable)

Product Definition -> Dashboard requirements -> draft information contracts -> Data Understanding -> Data/target freeze -> Data Engineering -> modeling -> QA/champion -> final contracts -> API -> Dashboard -> E2E/deployment
