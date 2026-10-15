# DWP adoption record for SAT-Dengue-V2

Status: PASS (DWP v7 installed and onboarded)
Verification date: 2026-10-14

## Scope

- Repository: SAT-Dengue-V2
- Adopted line: DWP v7
- Onboard mode: inline onboarding for fresh-empty individual repository.

## Official sources used

- https://deepworkplan.com/spec
- https://deepworkplan.com/changelog
- https://deepworkplan.com/.well-known/dwp-trust.json
- https://github.com/DailybotHQ/deepworkplan-skill/releases
- https://raw.githubusercontent.com/DailybotHQ/deepworkplan-skill/main/docs/INSTALLATION.md
- https://raw.githubusercontent.com/DailybotHQ/deepworkplan-skill/main/CHANGELOG.md

## Installed versions

- DeepWorkPlan skill: v7.8.1 (`.agents/skills/deepworkplan/SKILL.md`)
- AI Diff Reviewer skill (required local review): v3.3.14 (`.agents/skills/ai-diff-reviewer/SKILL.md`)
- skills-lock refs: `deepworkplan@v7.8.1`, `ai-diff-reviewer@v3.3.14`

## Procedures executed

DeepWorkPlan install (official pinned):

- `npx --yes skills add https://github.com/DailybotHQ/deepworkplan-skill/tree/v7.8.1 --skill deepworkplan -y`

AI Diff Reviewer install (official pinned):

- `npx --yes skills add https://github.com/DailybotHQ/ai-diff-reviewer/tree/v3.3.14 --skill ai-diff-reviewer -y`

Onboarding actions completed:

- Generated AI-first index and governance docs (`AGENTS.md`, `docs/` standard set).
- Generated local harness kit (`.agents/agents`, `.agents/commands`, `.agents/docs`, `.agents/settings.json`).
- Established canonical symlinks (`CLAUDE.md -> AGENTS.md`, `.claude -> .agents`, `.cursor -> .agents`).
- Added required review extension (`.review/extension.md`) and Flow A local review mode.
- Scaffolding and ignore rules for `.dwp/` and `tmp/` with tracked `.dwp/config.json`.

## Verification commands used

- `grep -n '^version:' .agents/skills/deepworkplan/SKILL.md`
- `grep -n '^version:' .agents/skills/ai-diff-reviewer/SKILL.md`
- `ls -la CLAUDE.md .claude .cursor`
- `git check-ignore -v .dwp tmp`
- `bash .agents/skills/deepworkplan/verify/conformance.sh`
- `grep -RIn "<skill-path>|<path>|<path_or_module>|your command here|TODO" AGENTS.md docs .agents/commands .agents/docs .review || true`
- `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true`

## Validation status

- DWP installed correctly: PASS
- Exact installed versions queryable: PASS
- Repository configured as AI-first harness: PASS
- Required local review installed (Flow A): PASS
- DWP conformance gate (`verify/conformance.sh`): PASS (`Verdict: CONFORMANT`)
- Placeholders in generated docs/commands: PASS (none found)
- Secrets/credentials introduced: PASS (none found by pattern scan)

## Versioned files related to DWP onboarding

- `AGENTS.md`, `CLAUDE.md`
- `docs/` standard onboarding set
- `.agents/` harness files and installed skills
- `.claude` and `.cursor` symlinks
- `.review/extension.md`
- `.dwp/config.json`
- `.gitignore`
- `skills-lock.json`

## Ignored local DWP/runtime state

- `.dwp/*` except `.dwp/config.json`
- `tmp/`

## Explicitly not executed

- Optional Flow B CI workflow for AI Diff Reviewer
- Optional addons (devcontainer, dailybot, dependency-upgrade, design-system, agentkit, herdr, vim)
- Project functional implementation (notebooks, models, API, dashboard)
- PITAGORAS setup

## Foundation package execution notes

- Branch used for this package: `docs/foundation-package-v1`.
- DWP full plan for this work was created locally under `.dwp/plans/` before implementation.
- Traceability discrepancy detected: requested baseline commit `5950021cb8a5eab49d5d5cba82f157568c216d0b` is not present in this local clone (`git cat-file -t` reports missing object).
- Resolution used: continue from current repository head with discrepancy explicitly recorded for human review.