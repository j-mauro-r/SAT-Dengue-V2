# AI Diff Reviewer Extension — SAT-Dengue-V2

## Repository Context

This repository is in foundation stage and is currently harness-first.
Primary risk in this stage is governance drift (unsafe rules, missing validation, or hidden scope expansion), not runtime defects.

## Review Priorities

1. Security and secret handling violations.
2. Any change that weakens validation gates or bypasses evidence requirements.
3. Scope creep outside explicit user request.
4. Introduction of PITAGORAS artifacts or references.
5. Non-reproducible install commands (unpinned refs, remote pipe-to-shell patterns).

## Severity Guidance

### Critical

- Credential/private key exposure in committed files.
- Destructive or unsafe command guidance (`git reset --hard`, secret exfiltration patterns).
- Changes that silently disable or falsify required validation gates.

### High

- Missing or incorrect DWP flow routing that can mis-execute plans.
- Incorrect gitignore rules causing sensitive or temporary artifacts to be committed.
- Unpinned external install references in governance docs.

### Medium

- Incomplete onboarding docs that break agent reproducibility.
- Catalog drift between `.agents/docs/` and actual command/agent files.

### Low

- Clarity, style, or consistency issues without operational risk.

## Repository-Specific Rules

- Treat `AGENTS.md` and `docs/TESTING_GUIDE.md` as control-plane files: changes require strict scrutiny.
- Flag any placeholder-like guidance that can confuse execution, even if syntactically valid.
- Prefer evidence-backed comments tied to concrete files and commands in this repo.
