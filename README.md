# SAT-Dengue V2

SAT-Dengue V2 is an AI-first, scientific-engineering repository for building an early warning system for dengue outbreaks in Colombia.

## Current Stage

Stage 0 — Engineering Foundation (closure evidence pending). Stage 0 remains IN PROGRESS and G0 is UNVERIFIED pending independent review evidence; the merged foundation package and green main CI are recorded in `docs/roadmap/master-plan.md`. Stage 1 — Product Definition is next after G0 passes.

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
- `docs/roadmap/master-plan.md`: single durable master plan for Stages 0–10
- `docs/governance/dwp.md`: DWP adoption and conformance evidence

## Foundation Constraints

- SAT-Dengue V2 is independent from V1 implementation history.
- V1 may be consulted only as reference.
- Dashboard functionality must be defined before final API contract freeze.
- PITAGORAS is explicitly excluded.
- Large datasets remain external (Kaggle/local/Colab); not committed to Git.

## Working Model

1. Reconnaissance of authority sources
2. Define a bounded user story (HU) with scope, acceptance criteria, validation, and evidence; use DWP only when the concrete HU/task warrants it
3. Incremental implementation, one bounded objective at a time
4. Validation and evidence
5. Independent review
6. PR and Human Gate decision

`docs/roadmap/master-plan.md` is the single durable master plan. A project-wide DWP Full Master Plan is not required or created; DWP Full plans per Stage are deprecated and will not be created. Development proceeds by HUs, without executing an entire Stage or project in a single prompt.

## What Is Not Implemented Yet

- Production-ready data pipelines
- Final API contracts and runtime implementation
- Dashboard runtime implementation
- End-to-end deployment workflows
