# SAT-Dengue V2

SAT-Dengue V2 is an AI-first, scientific-engineering repository for building an early warning system for dengue outbreaks in Colombia.

## Current Stage

See the [master plan](docs/roadmap/master-plan.md) for the dated implementation status, outstanding human gates and next bounded task. Kedro runs construction, preparation, saved-model replay and frozen evaluation. G5 is `NOT_APPROVED`, champion `not_selected`, and all six real decisions remain `does_not_meet`. The 2025 block is consumed evidence and cannot be used to train, adjust or select. Historical reproducibility is incomplete; this engineering migration grants no operational approval.

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

- An approved champion and operational inference pipelines
- Final API contracts and runtime implementation
- Dashboard runtime implementation
- End-to-end deployment workflows


## Local Kedro workflow

Use Python 3.12 and an isolated environment. `pyproject.toml` is the dependency
authority; every declared dependency is pinned. Base installation needs no modeling,
tracking or notebook extra:

```bash
python -m pip install .
kedro run --pipeline=foundation
# Scientific replay needs the optional modeling extra and local verified evidence:
python -m pip install '.[dev,modeling,tracking]'
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=replay
```

`replay` is the official one-command E2E. It performs zero real fits/refits,
calibration fits, searches or selection. The default remains `foundation`.
Available explicit graphs: `foundation`, `data`, `preparation`, `training_replay`,
`training_synthetic`, `evaluation_replay`, `evaluation_synthetic`, `replay`,
`replay_synthetic`; `__default__` aliases foundation. Synthetic graphs create their
own inputs and need no private data. Tracking is disabled unless explicitly enabled.

[Migration/restart/tracking and recovery](docs/operations/kedro-migration.md#current-cleanup-and-execution--session-8)
owns operating procedures and [the testing guide](docs/TESTING_GUIDE.md) owns CI,
mandatory local private parity and packaging checks. Retained notebooks are frozen
historical identity evidence, never production entrypoints. Replaced script facades
are recoverable through the disposition ledger and Git; do not execute old notebooks
or acquisition scripts to refresh scientific evidence.
