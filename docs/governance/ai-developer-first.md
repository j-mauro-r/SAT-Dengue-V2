# AI Developer First Governance for SAT-Dengue V2

## Purpose

This policy defines how SAT-Dengue V2 is executed under an AI Developer First model where humans steer, agents execute, and the repository is the durable system of record.

## Roles

- Mauricio (human owner): defines product intent, approves material decisions, and authorizes merges.
- Implementing agent: executes approved scope with evidence-based validation.
- Independent reviewer: validates risk, regressions, and evidence quality before merge recommendation.
- CI pipeline: enforces automated quality checks on existing repository surfaces.

## Authority Hierarchy

1. Approved human decisions (explicit in issue/request/ADR)
2. Governance policies and ADRs
3. Contract definitions (product/data/engineering contracts)
4. Active requirements and user stories
5. Architecture and methodology guides
6. DWP plans and task contracts
7. Implementation changes
8. Test and validation evidence

## Operating Flow

1. Reconnaissance: read relevant authority sources and current repository state.
2. Preflight: define scope, non-goals, risks, and validation strategy.
3. HU/task scoping: define bounded scope, acceptance criteria, validation, and evidence. Create/adjust a DWP plan only when that concrete HU/task warrants it because of complexity, risk, dependencies, or work across sessions.
4. Implementation: execute one bounded objective at a time.
5. Validation: run mapped gates and update evidence.
6. Independent review: reviewer evaluates findings and residual risk.
7. Pull Request: summarize scope, evidence, and limitations.
8. CI execution: verify repository-quality and quality gates.
9. Human Gate: Mauricio decides merge/no-merge.
10. Reconciliation: update docs/evidence if post-review changes occurred.

## Autonomy Boundaries

Agents may:

- Perform routine implementation and documentation decisions within approved scope.
- Select scoped validation from the testing map.
- Propose options when ambiguity remains.

Agents must escalate when:

- Product scope or acceptance criteria changes materially.
- Data policy, privacy, or security boundaries are affected.
- Merge/release decisions are required.
- Required authority source is missing or contradictory.

## Contract Change Governance

The [master plan](../roadmap/master-plan.md) owns contract maturity and freeze order. Product contracts define user-visible behavior; data/feature contracts define input and transformation rules; model/prediction contracts define output interpretation and traceability; API contracts define request/response behavior after scientific/product alignment.

Material changes require an explicit rationale, an update to the owning contract or decision record, validation impact analysis and human approval. Implemented candidate contracts and passing tests do not automatically freeze product or scientific boundaries. Preserve explicit authorization already given; routine documentation reconciliation does not require a second approval.

## Evidence States

- PASS: check executed and succeeded.
- FAIL: check executed and failed.
- BLOCKED: check could not run due external blocker.
- UNVERIFIED: check not executed yet.

No completion claim is valid without explicit evidence state.

## Codex Operating Rules

- Use progressive disclosure: load only necessary context for each task.
- Explicit human instructions in the current session authorize work. Record consequential scientific/scope decisions in their durable owner; do not treat an earlier assistant suggestion or copied conversation as human approval.
- Keep AGENTS as map/index, not encyclopedia.
- One DWP task equals one independently verifiable objective.
- Re-run invalidated gates after evidence-sensitive diffs.
- Never introduce PITAGORAS.
- SAT-Dengue V1 is reference-only, never copy wholesale.

## Review Rules

- Implementer is not the only reviewer.
- Findings are reported by severity with concrete file references.
- High/critical findings must be resolved or explicitly accepted by human authority.
- Tests passing does not automatically imply acceptance.

## Git/GitHub Role

- Work on feature branches with pull requests.
- Use Conventional Commits.
- Do not push directly to main.
- Do not force-push protected/shared history.

## DWP Role

- `docs/roadmap/master-plan.md` is the single durable master plan for all Stages 0–10, dependencies, gates, and stage progress.
- Do not require or create a project-wide DWP Full Master Plan. DWP Full plans per Stage are deprecated and will not be created.
- Execute incrementally through user stories (HUs), with scope, acceptance criteria, validation, and evidence; do not execute a whole Stage or project in a single prompt.
- DWP provides an execution contract only when a concrete HU/task warrants it. Choose the plan format appropriate to that objective.
- Such plans define tasks, acceptance criteria, validation gates, and final review. Runtime plan state in `.dwp/` is local; HU/task evidence belongs in the issue/PR and stage status in the master plan.

## Explicit Exclusions

- PITAGORAS is out of scope.
- This policy does not authorize functional product implementation by itself.

## Task Handoff

Keep one implementation owner per task. Handoffs identify objective, remaining work, touched files, validations and unresolved risks. Independent reviewers report severity, concrete references and resolution notes. Preserve existing work; coordinate before concurrent edits.
