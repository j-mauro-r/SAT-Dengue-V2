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
3. DWP planning: create/adjust plan before non-trivial multi-file work.
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

## Evidence States

- PASS: check executed and succeeded.
- FAIL: check executed and failed.
- BLOCKED: check could not run due external blocker.
- UNVERIFIED: check not executed yet.

No completion claim is valid without explicit evidence state.

## Codex Operating Rules

- Use progressive disclosure: load only necessary context for each task.
- Do not treat chat text as durable authority.
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

- DWP is the execution contract for significant work.
- Plans define tasks, acceptance criteria, validation gates, and final review.
- Runtime plan state in .dwp is local; durable project-level direction is mirrored in versioned docs.

## Explicit Exclusions

- PITAGORAS is out of scope.
- This policy does not authorize functional product implementation by itself.
