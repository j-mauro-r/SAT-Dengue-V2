# Engineering Standards

## Language and Communication

- Repository documentation and commit messages are English-only.
- Status updates must include objective evidence (command output summary or file diff summary).

## Version Control

- Use feature branches; do not work on `main` directly.
- Use Conventional Commits: `type(scope): description`.
- Current recommended scopes: `docs`, `governance`, `dwp`, `agents`, `infra`.

## Change Discipline

- Prefer minimal, reviewable diffs.
- Do not introduce scope creep outside explicit user request.
- Never introduce PITAGORAS-related files/configuration.

## Validation Discipline

- Select gates from touched surface, as defined in [TESTING_GUIDE.md](TESTING_GUIDE.md).
- If scoped gates are ambiguous, run full gate.
- Do not mark tasks complete without validation evidence.
