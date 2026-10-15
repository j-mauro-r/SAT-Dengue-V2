# Validation and Evidence Operations

## Core Rule

No completion claim is valid without explicit evidence state.

## Evidence States

- PASS
- FAIL
- BLOCKED
- UNVERIFIED

## Required Validation Sequence (Foundation)

1. DWP conformance gate
2. CI-equivalent local quality checks
3. Documentation consistency checks
4. PITAGORAS exclusion scan
5. Secret/credential scan
6. Independent review evidence

## Command Mapping

1. DWP conformance gate
	- `bash .agents/skills/deepworkplan/verify/conformance.sh`
2. CI-equivalent local quality checks
	- `ruff check tests`
	- `ruff format --check tests`
	- `mypy tests`
	- `pytest tests/unit -v`
3. Documentation consistency checks
	- `find docs -type f -name '*.md' | sort`
	- `python3 scripts/check_markdown_links.py`
	- `git diff -- docs AGENTS.md README.md .github`
4. PITAGORAS exclusion scan
	- `grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp --exclude-dir=.github --include='*.py' --include='*.json' --include='*.toml' --include='*.sh' || true`
5. Secret pattern scan
	- `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true`
6. Independent review evidence
	- Store findings with severity, file references, and resolution notes in PR description and/or local analysis artifact.

## Evidence Invalidation

If a diff changes evidence-sensitive surfaces after validation, affected gates must be re-run.
