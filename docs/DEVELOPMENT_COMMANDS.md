# Development Commands

## Environment Bootstrap

| Area | Type | Command |
|---|---|---|
| Install dev dependencies | full | `python -m pip install --upgrade pip && pip install -e ".[dev]"` |

## Foundation Commands

| Area | Type | Command | Expected State |
|---|---|---|---|
| DWP conformance | full | `bash .agents/skills/deepworkplan/verify/conformance.sh` | PASS required |
| Lint tests | full | `ruff check tests` | PASS required |
| Format check tests | full | `ruff format --check tests` | PASS required |
| Type check tests | full | `mypy tests` | PASS required |
| Unit tests | full | `pytest tests/unit -v` | PASS required |
| Repo status | scoped | `git status --short --branch` | informational |
| Documentation inventory | scoped | `find docs -type f -name '*.md' | sort` | informational |

## Governance and Security Checks

| Area | Type | Command |
|---|---|---|
| PITAGORAS runtime/config exclusion | scoped | `grep -RIn "PITAGORAS" . --exclude-dir=.git --exclude-dir=.dwp --exclude-dir=.github --include='*.py' --include='*.json' --include='*.toml' --include='*.sh' || true` |
| Secret pattern scan | scoped | `grep -RInE 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|AIza[0-9A-Za-z_-]{35}|-----BEGIN (RSA|OPENSSH|EC) PRIVATE KEY-----' . --exclude-dir=.git --exclude=skills-lock.json || true` |
| Markdown link consistency | scoped | `python3 scripts/check_markdown_links.py` |

## Notes

- Run full foundation commands before merge on documentation/governance pull requests.
- Re-run affected checks after evidence-sensitive diffs.
