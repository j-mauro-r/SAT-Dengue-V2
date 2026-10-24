# SAT-Dengue-V2 — Agent Entry Point

DWP standard: 7.0.0 (installed skill 7.8.1)

## Repository Purpose

SAT-Dengue-V2 builds a monthly dengue early-warning system under CRISP-ML(Q), DWP and GitHub workflows. Read `docs/roadmap/master-plan.md` for implementation progress, open human gates and the next bounded task. Do not infer stage approval from a branch name or completed plan.

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
| Official scientific E2E | `kedro run --pipeline=replay` |
| Ruff lint | `python -m ruff check src tests` |
| Ruff format | `python -m ruff format --check src tests` |
| Types | `python -m mypy src tests` |
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

## Validation Ownership

`docs/TESTING_GUIDE.md` owns required gates and source-to-test mapping. Quick Commands above are shortcuts, not a second validation policy. Report repo-only, scoped-plan and all-plan conformance separately; historical plan failures must not be presented as current code failures or silently waived.

## Human Gate Boundaries

Escalate for human decision when:

- Product scope changes materially.
- Contract/data/security boundaries change.
- Merge/release approval is needed.
- Authority sources conflict.

## Documentation Ownership

- `docs/README.md` maps topics to their single owner; follow those links selectively.
- Scientific choices belong in `docs/product/traking-concluciones.md`; executable input/feature rules belong in their current contracts.
- Dated audit reports and retired EDA are historical evidence, not standing work instructions. Do not restart them to refresh old outputs.
- Tool manuals under `.agents/skills/` are pinned dependencies, not project specifications; do not edit or prune them as project prose.

## Local State Notes

- Runtime plan state is local in `.dwp/` (except tracked `.dwp/config.json`).
- Disposable artifacts belong in `tmp/`.


Current scientific execution is Kedro; notebooks are frozen historical identity
evidence. Use the migration/testing owners for restart, optional tracking, base
versus modeling/tracking extras, maintained-script checks and required private parity.
Run DWP writers/gates/projections/renders sequentially. No real adjustment or new
scientific approval follows from replay. Retire a path only through its resolved
disposition and verified original/current correspondence; preserve all pinned tools.
