# DWP Adoption and Planning Policy

## Installation baseline — 2026-10-14

| Component | Installed version / location |
|---|---|
| DeepWorkPlan | 7.8.1, `.agents/skills/deepworkplan/SKILL.md` |
| Declared repository standard | 7.0.0 |
| AI Diff Reviewer | 3.3.14, `.agents/skills/ai-diff-reviewer/SKILL.md` |

The installation baseline passed on 2026-10-14. `skills-lock.json` records pinned refs. Local command delegators, `.agents/docs/` catalogues, `CLAUDE.md -> AGENTS.md`, `.claude`/`.cursor` links and `.review/extension.md` provide the harness. The reviewer uses local Flow A; optional CI review/addons were not installed by that baseline.

Pinned installation references (historical, not instructions to reinstall):

- [DeepWorkPlan v7.8.1](https://github.com/DailybotHQ/deepworkplan-skill/tree/v7.8.1).
- [AI Diff Reviewer v3.3.14](https://github.com/DailybotHQ/ai-diff-reviewer/tree/v3.3.14).

## Planning and evidence ownership

- The [master plan](../roadmap/master-plan.md) is the single stage-level plan and progress record.
- Work incrementally by bounded HU/task. No project-wide Full DWP or Full plan per Stage is required or created.
- Use a DWP when task complexity/risk/dependencies justify it, or when Mauricio explicitly requests one. Direct edits can proceed directly under `AGENTS.md`.
- Follow local create/execute/refine/resume/status/verify delegators and the installed skill's versioned lifecycle. Do not mix plan generations or fabricate gate evidence.
- `.dwp/` contains ignored local runtime history, except tracked `.dwp/config.json`. Retired experimental EDA is discoverable through the historical archive in the documentation index; the active scientific decision register and current audit remain indexed separately. Historical plan locations, contracts and journals are retained unchanged; retirement notices are additive and do not rewrite past gates.
- Planning policy does not waive validation, independent review, human merge approval or explicit no-publication restrictions.

## Current status versus historical installation

Stage 2 is active following Mauricio's confirmation of Stage 1 closure. Installation PASS does not imply present conformity of all local plans or G0 approval. See [current validation](../operations/validation-and-evidence.md) for the legacy mixed-lifecycle failure and PLAN_003 narrative/ledger discrepancy; see the master plan for the unresolved historical G0 review evidence.

No historical plan contract, journal or terminal result was rewritten to make these controls pass.
