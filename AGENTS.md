# SAT-Dengue-V2 — Agent Entry Point

DWP standard: 7.0.0 (onboarded 2026-10-14; skill 7.8.1)

## Repository Purpose

SAT-Dengue-V2 is currently in foundation stage. The repository is prepared as an AI-first engineering harness for building the next generation of SAT-Dengue using Deep Work Plan, Codex/Copilot, GitHub, GitHub Actions, and CRISP-ML(Q).

## Documentation Index

| Document | Purpose |
|---|---|
| [docs/README.md](docs/README.md) | Master index for technical repository documentation. |
| [docs/PRODUCT_SPEC.md](docs/PRODUCT_SPEC.md) | Product intent, users, success criteria, and non-goals. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Current harness architecture and planned solution layers. |
| [docs/STANDARDS.md](docs/STANDARDS.md) | Coding, branching, review, and documentation standards. |
| [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md) | Validation strategy, mapped gates, scoped/full commands, and proposed test stack. |
| [docs/DEVELOPMENT_COMMANDS.md](docs/DEVELOPMENT_COMMANDS.md) | Canonical command reference for setup, validation, and operations. |
| [docs/SECURITY.md](docs/SECURITY.md) | Security handling, data boundaries, and secret rules. |
| [docs/PERFORMANCE.md](docs/PERFORMANCE.md) | Performance posture and budget strategy for upcoming components. |
| [docs/AI_AGENT_ONBOARDING.md](docs/AI_AGENT_ONBOARDING.md) | First-session onboarding checklist for coding agents. |
| [docs/AI_AGENT_COLLAB.md](docs/AI_AGENT_COLLAB.md) | Multi-agent collaboration and handoff protocol. |
| [docs/governance/dwp.md](docs/governance/dwp.md) | DWP adoption governance record and version evidence. |

## Repository Structure

```text
SAT-Dengue-V2/
├── AGENTS.md
├── CLAUDE.md -> AGENTS.md
├── docs/
│   ├── governance/
│   ├── PRODUCT_SPEC.md
│   ├── ARCHITECTURE.md
│   ├── STANDARDS.md
│   ├── TESTING_GUIDE.md
│   ├── DEVELOPMENT_COMMANDS.md
│   ├── SECURITY.md
│   ├── PERFORMANCE.md
│   ├── AI_AGENT_ONBOARDING.md
│   └── AI_AGENT_COLLAB.md
├── .agents/
│   ├── agents/
│   ├── commands/
│   ├── docs/
│   ├── settings.json
│   └── skills/
├── .dwp/
│   ├── plans/
│   ├── config.json
│   └── onboard/
└── tmp/
```

## Mandatory Rules

- Language: all commit messages, docs, and agent reports must be in English.
- Commit style: use Conventional Commits `type(scope): description`.
- Allowed scopes in this stage: `docs`, `governance`, `dwp`, `agents`, `infra`.
- Validation rule: select gates from touched surface using [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md). If mapping is ambiguous, run full validation gate.
- Logging rule: never include secrets, tokens, personal data, or credentials in logs, reports, or commits.
- Repository boundary: write only inside this repository; never mutate external repositories from this context.
- Reporting: progress reports must not block work execution.
- PITAGORAS is out of scope and must not be introduced.

## Quick Commands

Current repository has no application runtime or dependency manifest yet. Commands below are real and runnable for the present stage.

| Goal | Scope | Command | Status |
|---|---|---|---|
| DWP conformance check | full | `bash .agents/skills/deepworkplan/verify/conformance.sh` | verified |
| Git working tree check | full | `git status --short --branch` | verified |
| Inspect generated docs | scoped | `find docs -type f -name '*.md'` | verified |
| Check one path exists | scoped | `test -e docs/README.md && echo OK || echo MISSING` | verified |
| Python tests (`pytest -q`) | full | `pytest -q` | proposed/unverified |
| Python tests by target (`pytest tests/test_placeholder.py -q`) | scoped | `pytest tests/test_placeholder.py -q` | proposed/unverified |
| Lint (`ruff check .`) | full | `ruff check .` | proposed/unverified |
| Lint by target (`ruff check docs`) | scoped | `ruff check docs` | proposed/unverified |
| Type check (`mypy src`) | full | `mypy src` | proposed/unverified |
| Type check by target (`mypy docs`) | scoped | `mypy docs` | proposed/unverified |

## Deep Work Plans — Invocation

Structured work runs through the local DWP flows (`.agents/commands/dwp-*` delegators; flows live in `.agents/skills/deepworkplan/`; discovery is local and does not require network).

| Intent | Route |
|---|---|
| plan this work / create a plan | `/dwp-create` |
| execute / run the plan | `/dwp-execute` |
| continue interrupted plan | `/dwp-resume` |
| plan status / what is left | `/dwp-status` (read-only) |
| verify repo/plan conformance | `/dwp-verify` (read-only) |
| direct edit request (fix/rename/update) | execute directly; do not silently convert to plan |

Hosts without slash commands invoke the same flows with `#deepworkplan-*` or plain text. `trust`/`auto` allows unattended continuation inside the selected flow only; it is not a flow selector.

## Local Security Review

- Local reviewer skill installed: `.agents/skills/ai-diff-reviewer` (v3.3.14).
- Active mode: Flow A (local review baseline).
- Extension file: `.review/extension.md`.
- CI Flow B is optional and not enabled in this onboarding run.

## Working Principles

- Own outcomes end-to-end, including validation evidence.
- Investigate locally before escalating.
- Decide routine implementation details autonomously within scope.
- Escalate only when authority, scope, or requirements are unclear.
- Ask approvals with concrete options, risks, and recommendation.
- Recover from blockers with fallback plans before pausing progress.
- Respect explicit scope, constraints, and non-goals.
- Apply rigor proportionate to risk and blast radius.
- Communicate directly, with precise status and evidence.
- Never claim done without running and reporting relevant checks.

## Scratch and Plan State

- `.dwp/` stores DWP working state and plan artifacts.
- `tmp/` is for disposable local scratch output.
