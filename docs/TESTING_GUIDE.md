# Testing and Validation Guide

## Current Repository State

There is no application source tree, package manifest, or runtime-specific test framework yet.

## Current Verified Gates

### Full validation

- Command: `bash .agents/skills/deepworkplan/verify/conformance.sh`
- Working directory: repository root
- Purpose: validate AI-first harness conformance (AGENTS/docs/.agents/.dwp contract)
- Current status: runnable and used as primary objective gate

### Scoped validation

- Command: `test -e docs/README.md && echo OK || echo MISSING`
- Working directory: repository root
- Scope model: single path existence check
- Status: proposed/unverified (utility command, not yet adopted as mandatory gate)

## Source-to-Test Mapping (Current)

- `AGENTS.md`, `docs/`, `.agents/commands/`, and `.agents/docs/` changes map to harness conformance gate.
- Governance-only edits in `docs/governance/` still require conformance check before completion.

## Blind Spots and Escalation Paths

Blind spots in current stage:

- No runtime test suite for data/ML/business logic yet.
- No package-level lint/type gates yet.

Escalation/full-run triggers:

- Any change under `.agents/skills/` or command delegation files.
- Any change in DWP contract files (`AGENTS.md`, `.dwp/config.json`, `.gitignore` DWP rules).
- Any change touching planned dependency/toolchain definition.

Fallback statement:

- When mapping is uncertain, run full gate: `bash .agents/skills/deepworkplan/verify/conformance.sh`.

## Proposed Toolchain (Target, Unverified)

This section defines the first implementation-ready baseline once Python source is introduced.

### Proposed full commands

- `pytest -q`
- `ruff check .`
- `mypy src`

### Proposed scoped commands

- `pytest tests/test_placeholder.py -q`
- `ruff check docs`
- `mypy docs`

### Proposed conventions

- Unit tests first, with deterministic fixtures.
- Integration tests for data contracts, persistence seams, and API boundaries.
- End-to-end tests only for high-value workflows.

No proposed command is marked as verified until executed in this repository after toolchain scaffolding.
