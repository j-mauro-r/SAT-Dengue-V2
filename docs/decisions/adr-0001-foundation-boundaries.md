# ADR-0001: Foundation Boundaries and Product Direction

## Status

Accepted

## Date

2026-10-14

## Context

SAT-Dengue V2 requires a durable foundation package before product implementation. Prior harness work exists and must be adapted, not rebuilt from scratch.

## Decision

- SAT-Dengue V2 is an independent implementation (not a clone of V1).
- Principal product components are:
  1. ML predictive system
  2. API
  3. End-user dashboard
- Scientific methodology is CRISP-ML(Q).
- Engineering execution layer is DWP + Codex + Git/GitHub + GitHub Actions.
- PITAGORAS is explicitly excluded.
- Dashboard functionality is defined before final API contract freeze.
- Large datasets stay external (Kaggle/local/Colab), not committed to Git.
- DVC + S3 are deferred until demonstrated need.

## Consequences

- Foundation pull requests remain documentation/governance-first.
- Functional implementation starts only after staged planning and contract maturation.
- Validation and review discipline are mandatory from stage zero.
