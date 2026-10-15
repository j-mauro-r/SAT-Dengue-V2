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

## Planning policy (2026-10-15)

- `docs/roadmap/master-plan.md` is the single durable master plan for Stages 0–10, dependencies, gates, and stage progress.
- A project-wide DWP Full Master Plan is not required and will not be created. The previous requirement and its UNVERIFIED plan status are superseded; no master-plan ID is required for G0.
- DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally by bounded user stories (HUs), each with scope, acceptance criteria, validation, and evidence. Do not implement a whole Stage or project in a single prompt.
- Use DWP only when a concrete HU/task warrants it because of complexity, risk, dependencies, or work across sessions, choosing the appropriate plan format.
- This policy changes planning scope, not the required validation, independent review, or Human Gate.

## Foundation package history and current evidence

- Historical branch: `docs/foundation-package-v1`.
- A local DWP Full plan was used for the bounded Foundation Package work under `.dwp/plans/`; it is historical task evidence, not a prerequisite for future Stage plans.
- [PR #5](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/5) was merged into `main` on 2026-10-14 (America/Bogota), merge commit `1abbc08b8429c15b9145119da13cfc955da03067`.
- Its earlier missing-baseline-object and feature-branch synchronization notes describe the pre-merge local clone. They are no longer active instructions or G0 blockers.
- [Main CI run 38790310683](https://github.com/j-mauro-r/SAT-Dengue-V2/actions/runs/38790310683) passed on commit `4e816d43e92638f773f26bdb2d0ec8929ffeb4c2`: Repository Quality (including DWP conformance, documentation links, and scans), Python Quality, and Unit Tests.
- Stage 0 remains **IN PROGRESS — closure evidence pending**; G0 remains **UNVERIFIED**. PR #5 has no submitted reviews or discussion comments as inspected on 2026-10-15, and its description leaves independent review pending. No independent review artifact was found in the repository. CI success and merge history do not establish that review evidence.
- Remaining closure action and the authoritative stage status are recorded in `docs/roadmap/master-plan.md`. The DWP onboarding PASS above does not by itself mean G0 PASS.
