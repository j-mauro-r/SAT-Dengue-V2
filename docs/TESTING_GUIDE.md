# Testing and Validation Guide

## Validation Policy

Validation is mapped by touched surface and reported using explicit evidence states.

Evidence states:

- PASS
- FAIL
- BLOCKED
- UNVERIFIED

## Foundation Gate Set

### Prerequisite

- `python -m pip install --upgrade pip && pip install -e ".[dev]"`

### Full gate (required before merge)

- `bash .agents/skills/deepworkplan/verify/conformance.sh`
- `ruff check tests`
- `ruff format --check tests`
- `mypy tests`
- `pytest tests/unit -v`

### Security and policy scans (required)

- PITAGORAS exclusion scan:
  - `grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp --exclude-dir=.github --include='*.py' --include='*.json' --include='*.toml' --include='*.sh' || true`
- Secret pattern scan:
  - `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true`

### Documentation consistency checks (required)

- `python3 scripts/check_markdown_links.py`

## Surface-to-Gate Mapping

- `docs/**`, `AGENTS.md`, `.github/**` changes:
  - run full gate set above.
- `.agents/**` and DWP governance changes:
  - full gate set + DWP conformance is mandatory.
- Python source/tests changes (future stages):
  - full gate set plus scope-specific tests as required.

## Escalation Rule

If test mapping is ambiguous, run the full gate set.

## Scoped Commands, Mapping, Fallback (Documentation Standard 3.4)

Scoped commands:

- `git status --short --branch`
- `find docs -type f -name '*.md' | sort`
- `test -f docs/governance/ai-developer-first.md && echo OK || echo MISSING`

Mapping rule:

- Use scoped commands for fast local inspection.
- Use the full gate set for merge readiness and any material change.

Fallback rule:

- When command mapping is uncertain, default to the full gate set.
