# AI Agent Collaboration

## Ownership Model

- One execution owner per active task.
- Reviewers validate evidence, constraints, and scope adherence.
- Escalations go to repository owner only for scope/authority blockers.

## Handoff Protocol

Every handoff must include:

- Goal and scope boundaries.
- Files touched and pending files.
- Validation commands run and outcomes.
- Open risks and recommended next action.

## Conflict Avoidance

- Do not run parallel edits over the same file unless explicitly coordinated.
- Prefer atomic commits by concern.
- Rebase/merge decisions must preserve audit trail and validation evidence.
