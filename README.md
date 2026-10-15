# SAT-Dengue V2

SAT-Dengue V2 is an AI-first, scientific-engineering repository for building an early warning system for dengue outbreaks in Colombia.

## Current Stage

Foundation stage. The repository is focused on governance, planning discipline, documentation architecture, and validation standards before product runtime implementation.

## Product Direction

Target product components:

1. ML predictive system
2. API
3. End-user dashboard

Scientific objective:

- Anticipate dengue outbreak risk for approximately T+1 and T+2 months using epidemiological, temporal, and climatic signals.

## Methodological and Engineering Stack

- CRISP-ML(Q) for scientific lifecycle
- Deep Work Plan (DWP) for execution contracts
- Git/GitHub + GitHub Actions for collaboration and CI
- AI Developer First governance model for human/agent operation

## Repository Navigation

Primary entry points:

- `AGENTS.md`: operating map for coding agents
- `docs/README.md`: authority map and documentation index
- `docs/governance/ai-developer-first.md`: governance policy
- `docs/roadmap/master-plan.md`: durable staged roadmap mirror
- `docs/governance/dwp.md`: DWP adoption and conformance evidence

## Foundation Constraints

- SAT-Dengue V2 is independent from V1 implementation history.
- V1 may be consulted only as reference.
- Dashboard functionality must be defined before final API contract freeze.
- PITAGORAS is explicitly excluded.
- Large datasets remain external (Kaggle/local/Colab); not committed to Git.

## Working Model

1. Reconnaissance of authority sources
2. DWP plan creation for significant work
3. Scoped implementation
4. Validation and evidence
5. Independent review
6. PR and Human Gate decision

## What Is Not Implemented Yet

- Production-ready data pipelines
- Final API contracts and runtime implementation
- Dashboard runtime implementation
- End-to-end deployment workflows
