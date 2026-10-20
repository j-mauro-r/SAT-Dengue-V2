# Engineering Standards

## Python Baseline

- Python 3.12 baseline.
- Type hints expected in maintained code paths.
- Ruff for linting and formatting checks.
- mypy for static type analysis.
- Google-style docstrings for public APIs where appropriate.
- Prefer SOLID/DRY while avoiding unnecessary abstractions.
- Prefer explicit configuration over scattered magic constants.

## Testing Principles

- Risk-based test strategy.
- Unit, data-quality, contract, integration, and E2E layers are recognized.
- Tests must validate behavior, not mirror implementation internals.
- PASS/FAIL/BLOCKED/UNVERIFIED evidence states are mandatory.

## Git and Collaboration

- Branch + PR workflow.
- Conventional Commits.
- Human Gate before merge.
- No direct work on main.
- No force push to protected/shared history.

## Documentation Discipline

- Single source of truth per topic.
- ADRs for material technical decisions.
- Resolve contradictions instead of accumulating duplicates.

## Performance Readiness

Local consolidation and preparation pipelines exist; production service budgets have not been measured. Record execution time and memory when they affect reproducibility. Establish latency/throughput targets for implemented training/runtime workloads when needed; do not introduce a benchmark system or present planned budgets as measurements.
