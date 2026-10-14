# Development Commands

## Current Verified Commands (Foundation Stage)

| Area | Type | Command |
|---|---|---|
| Harness conformance | full | `bash .agents/skills/deepworkplan/verify/conformance.sh` |
| Git status | full | `git status --short --branch` |
| Documentation inventory | scoped | `find docs -type f -name '*.md'` |
| File existence probe | scoped | `test -e docs/README.md && echo OK || echo MISSING` |

## Proposed Commands (Implementation Stage, Unverified)

| Area | Type | Command |
|---|---|---|
| Python tests | full | `pytest -q` |
| Python tests by scope | scoped | `pytest tests/test_placeholder.py -q` |
| Python lint | full | `ruff check .` |
| Python lint by scope | scoped | `ruff check docs` |
| Python type-check | full | `mypy src` |
| Python type-check by scope | scoped | `mypy docs` |

## Notes

- Proposed commands are intentionally non-authoritative until dependency manifests and source layout are added.
- Commands that require CI-only or container-only runtime must be labeled when introduced.
