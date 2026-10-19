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

## Stage 2 bounded panel review

Synthetic regressions: `.venv/bin/python -m pytest tests/unit/test_stage2_panel_review.py -q`. They run without the large private snapshots. They cover independent joins, scenario removal, missingness, geography, non-swaps and calendar-adjacent support.

Local data reconstruction: run `scripts/stage2_panel_review.py` with `--phase panel`, `--phase analysis`, `--phase rules`, then `--phase validate`, using the project environment. This requires supplied local raw/reference files and writes aggregate ignored outputs only. Validation checks content and source hashes; existence alone is not scientific acceptance.

Also lint and format `scripts/stage2_panel_review.py` with Ruff, run the full unit suite and `mypy tests`, and run `scripts/check_markdown_links.py`. The new plan must pass scoped DWP conformance; report the pre-existing legacy-plan global failure separately without weakening or rewriting that historical gate.


## Clean-checkout CI installation

The Stage 2 project distribution is metadata-only: setuptools has an explicit empty package list, so `data/` and `notebooks/` are never auto-discovered as installable packages. The `dev` extra declares NumPy and pandas because the synthetic panel tests import them. This changes neither data publication policy nor analysis-population rules.

Validate packaging changes from a fresh Git archive/checkout in a separate temporary environment: install `.[dev]`, run `pytest tests/unit -q`, `ruff check tests`, `ruff format --check tests` and `mypy tests`; build a wheel with `pip wheel --no-deps .` and inspect that it contains no source datasets/notebooks. The three tests backed by ignored private analytical outputs are expected to skip in a public checkout; synthetic regressions still run. Keep a separate local full-suite check when those outputs are available. Never copy private datasets into CI to make these checks pass.
