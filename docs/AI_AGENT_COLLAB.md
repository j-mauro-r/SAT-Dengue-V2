# AI Agent Collaboration

## Collaboration Model

- One primary execution owner per task at a time.
- Independent reviewer checks risk, regressions, and validation evidence.
- Human owner resolves scope and merge decisions.

## Handoff Protocol

Every handoff includes:

- task objective and remaining scope,
- touched files,
- validation commands run and outcomes,
- open risks/blockers,
- recommended next action.

## Conflict Prevention

- Avoid parallel edits on the same file unless explicitly coordinated.
- Keep commits atomic by concern.
- Preserve traceability when rebasing/merging.

## Review Expectations

- Findings are reported by severity with concrete file references.
- High/critical findings are resolved or explicitly accepted by human authority.
