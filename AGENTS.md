# SAT-Dengue-V2 — Agent Entry Point

DWP standard: 7.0.0 (installed skill 7.8.1)

## Repository Purpose

SAT-Dengue-V2 is in Stage 2 — Data Understanding. Mauricio confirmed Stage 1 closure after merging PR #7. Stage 2/G2 remain open; historical G0 independent-review evidence remains UNVERIFIED. See `docs/roadmap/master-plan.md` for the authoritative current status and pending work. This repository is the AI-first execution and governance layer for building the SAT-Dengue V2 product under CRISP-ML(Q), DWP, and GitHub workflows.

## Start Here

1. Read `docs/README.md`.
2. Read `docs/governance/ai-developer-first.md`.
3. Confirm branch state: `git status --short --branch`.
4. Run conformance gate: `bash .agents/skills/deepworkplan/verify/conformance.sh`.

## Authority Model (highest to lowest)

1. Explicit human-approved decisions and ADRs
2. Governance policies
3. Product/data/model/API contracts
4. Active requirements and task contracts
5. Architecture and methodology docs
6. DWP plans for current work
7. Implementation diffs
8. Validation evidence

Authoritative references:

- `docs/governance/ai-developer-first.md`
- `docs/decisions/adr-0001-foundation-boundaries.md`
- `docs/contracts/contract-lifecycle.md`
- `docs/roadmap/master-plan.md`
- `docs/governance/dwp.md`

## Mandatory Rules

- Language: commit messages, docs, and reports in English.
- Commit style: Conventional Commits `type(scope): description`.
- Stage scopes: `docs`, `governance`, `dwp`, `agents`, `infra`.
- Validate by touched surface using `docs/TESTING_GUIDE.md`.
- Never include secrets or credentials in logs/commits.
- Write only inside this repository.
- PITAGORAS is out of scope and must not be introduced.

## Quick Commands

| Goal | Command |
|---|---|
| Branch status | `git status --short --branch` |
| DWP conformance | `bash .agents/skills/deepworkplan/verify/conformance.sh` |
| Ruff lint (tests) | `ruff check tests` |
| Ruff format check (tests) | `ruff format --check tests` |
| mypy (tests) | `mypy tests` |
| pytest unit tests | `pytest tests/unit -v` |
| PITAGORAS runtime/config scan | `grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp --exclude-dir=.github --include='*.py' --include='*.json' --include='*.toml' --include='*.sh' || true` |
| Secret pattern scan | `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true` |

## DWP Invocation

Use local command delegators:

- Create plan: `/dwp-create`
- Execute plan: `/dwp-execute`
- Resume plan: `/dwp-resume`
- Plan status: `/dwp-status`
- Conformance verify: `/dwp-verify`

`docs/roadmap/master-plan.md` is the single durable master plan for Stages 0–10. Do not require or create a project-wide DWP Full Master Plan or DWP Full per Stage; per-Stage Full plans are deprecated.

Execute incrementally by user stories (HUs), each with bounded scope, acceptance criteria, validation, and evidence. Use DWP only when a concrete HU/task warrants it because of complexity, risk, dependencies, or work across sessions. Direct edit requests should be implemented directly unless the user requests a DWP flow. Do not execute a whole Stage or project in one prompt.

## Validation Baseline (Foundation)

- DWP conformance: `bash .agents/skills/deepworkplan/verify/conformance.sh`
- Lint tests: `ruff check tests`
- Format checks: `ruff format --check tests`
- Type checks: `mypy tests`
- Unit tests: `pytest tests/unit -v`

## Human Gate Boundaries

Escalate for human decision when:

- Product scope changes materially.
- Contract/data/security boundaries change.
- Merge/release approval is needed.
- Authority sources conflict.

## Local State Notes

- Runtime plan state is local in `.dwp/` (except tracked `.dwp/config.json`).
- Disposable artifacts belong in `tmp/`.
