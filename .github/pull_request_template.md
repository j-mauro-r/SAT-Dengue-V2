## Goal

Describe the concrete outcome delivered by this PR.

## Source Of Authority

- Requirement or request:
- HU/task and acceptance criteria:
- DWP plan/task (if warranted; otherwise N/A with rationale):
- Applicable ADR/contract/policy:

## Scope

Included:

-

Not included:

-

## Changes

-

## Validation

Record command + result state (PASS/FAIL/BLOCKED/UNVERIFIED):

- [ ] `bash .agents/skills/deepworkplan/verify/conformance.sh`
- [ ] `ruff check tests`
- [ ] `ruff format --check tests`
- [ ] `mypy tests`
- [ ] `pytest tests/unit -v`
- [ ] `find docs -type f -name '*.md' | sort` and `git diff -- docs AGENTS.md README.md .github`
- [ ] `python3 scripts/check_markdown_links.py`
- [ ] `grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp --exclude-dir=.github --include='*.py' --include='*.json' --include='*.toml' --include='*.sh' || true`
- [ ] `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true`

## Evidence

Summarize command outputs and include any relevant links/screenshots.

## Risks And Limitations

-

## Independent Review

- [ ] Performed
- [ ] No open critical/high findings
- Reviewer summary:

## Human Gate

- [ ] Ready for Mauricio merge decision