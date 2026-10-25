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

The [master plan](../roadmap/master-plan.md) owns current progress; this document owns the planning policy and installation baseline. Installation PASS does not imply current all-plan conformity or G0 approval. [Validation operations](../operations/validation-and-evidence.md) separates current checks from historical audit outcomes.

Use `conformance.sh --repo-only` to check the harness, `--plan <path>` for the bounded plan, and the default invocation for the repository plus all local plans. Run the proportional gate selected by [the testing guide](../TESTING_GUIDE.md) before merge and disclose legacy failures separately; never rewrite historical journals to turn them green. No new plan is needed merely to refresh a status paragraph or merge duplicate prose.

## Gate evidence reuse

Plan task gates must be ordered from focused and cheap to broad and expensive. After a broad
gate passes at a specific commit and environment, do not rerun a narrower subset already
subsumed by that evidence. Reuse the recorded result unless relevant code, configuration or
the environment changed; the prior run failed or was interrupted; or the narrower command
exercises a genuinely different boundary. Record the reason before any exception. This rule
prevents post-suite repetition without allowing cached evidence to survive an
evidence-sensitive change.

No historical plan contract, journal or terminal result was rewritten to make these controls pass.


## Sequential migration writers

PLAN_030 uses the local contract/journal helpers. A bounded human-approved cleanup
correspondence preserves original and pre-cleanup Git blobs separately from final
engineering identities; earlier mappings and scientific/native evidence stay fixed.
Use one DWP writer at a time for gates, observations, amendments, projections and
renders. Do not manually repair journals/state/views or treat a cached result as a
fresh gate after an evidence-sensitive change. The accepted Session 7 incident and
minimal recovery remain preserved historical evidence; no further repair is implied.
