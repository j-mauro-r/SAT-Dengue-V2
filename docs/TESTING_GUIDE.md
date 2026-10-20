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

## Stage 2 data integrity and retired experimental EDA

The [experimental EDA](archive/experimental-eda/README.md) was retired on 2026-10-19. Its notebooks, reports and pending rerun instructions are historical. Do not run the old panel/analysis/rules phases as the default Stage 2 workflow. New analysis requires a new bounded task and current acceptance criteria; retirement does not approve scientific outputs or close G2.

Keep all existing tests enabled. Synthetic regressions (`.venv/bin/python -m pytest tests/unit/test_stage2_panel_review.py -q`) run without private snapshots and preserve independent-join, missingness, geography, non-swap and calendar-adjacent safeguards. The three tests against ignored historical monthly-association outputs remain artifact-consistency checks; their passing status does not make those results current analytical evidence. The historical analytical scripts stay at their import paths with deprecation docstrings and unchanged logic because tests and local historical validators depend on them.

Active data-integrity safeguards: `.venv/bin/python -m pytest tests/unit/test_january_2020_climate_incorporation.py tests/unit/test_stage2_manifest_traceability.py -q`. These verify incorporation/traceability behavior on test fixtures; they do not download or reintegrate source data. Run the full unit suite, Ruff checks, `mypy tests` and `scripts/check_markdown_links.py` under the foundation gate policy above. Also lint/format any touched Python script.

For this archival migration, local PLAN_012 validates the path/hash manifest, byte-identical notebooks, restricted report transformations, unchanged script logic, original data/evidence hashes and preserved historical plan records. It is a one-time migration check, not a new recurring scientific gate. New DWP work must pass scoped conformance; report pre-existing legacy-plan global failures separately without rewriting their records or weakening validation.

## Clean-checkout CI installation

The Stage 2 project distribution is metadata-only: setuptools has an explicit empty package list, so `data/` and `notebooks/` are never auto-discovered as installable packages. The `dev` extra declares NumPy and pandas because the synthetic panel tests import them. This changes neither data publication policy nor analysis-population rules.

Validate packaging changes from a fresh Git archive/checkout in a separate temporary environment: install `.[dev]`, run `pytest tests/unit -q`, `ruff check tests`, `ruff format --check tests` and `mypy tests`; build a wheel with `pip wheel --no-deps .` and inspect that it contains no source datasets/notebooks. The three tests backed by ignored private analytical outputs are expected to skip in a public checkout; synthetic regressions still run. Keep a separate local full-suite check when those outputs are available. Never copy private datasets into CI to make these checks pass.

## Training preparation inputs (milestone 1)

The [preparation contract and workflow](product/stage-3/README.md) map
`scripts/training_preparation/**`, notebook 04 and its preparation contract to
`.venv/bin/python -m pytest tests/unit/test_training_preparation.py -q`.
Synthetic tests reject schema/type/nullability errors, duplicate keys, missing
months/municipalities, invalid categories/coverage, forbidden predictors and
fingerprint tampering. No private input is needed for those tests.

Run `.venv/bin/python -m scripts.training_preparation.audit` for read-only local
validation of existing notebook 03 products, including manifest SHA-256 checks.
This requires the private local products and never regenerates them. For a
preservation audit, provide `--baseline <path>` with a pre-task fingerprint map.
Execute notebook 04 cells sequentially with the repository environment; only
aggregate evidence and contract roles are displayed. Run the full foundation
gates, lint/format the new modules and check Markdown links for this surface.
Use `--basetemp=tmp/pytest-training-preparation` when test artifacts must remain
inside the repository. Report historical global DWP failures separately from
`conformance.sh --plan .dwp/plans/PLAN_018_training_data_preparation`.

## Deterministic development features (milestone 2)

The same `tests/unit/test_training_preparation.py` also covers two-municipality
isolation, row-order invariance, December/January boundaries, exact missing-month
lookups, first observations, valid negative changes, complete T/T−1/T−2 means,
January-phased cycles, future perturbation, reserved outcome masking, preservation
of current climate signs, immutable atomic publication, corruption rejection and
invalidation after data/config/code changes. Use repository-local `--basetemp`.

Run the following to publish an immutable development bundle and then recompute
all bytes, audit real horizon eligibility against the existing policy, and verify
original scientific hashes:

```bash
.venv/bin/python -m scripts.training_preparation.development
.venv/bin/python -m scripts.training_preparation.development --verify \
  --baseline .dwp/plans/PLAN_018_training_data_preparation/analysis_results/input_baseline.json
```

No reserved reference features or model training is generated. Full foundation
gates remain required. Check new modules with
`.venv/bin/mypy --explicit-package-bases scripts/training_preparation`, plus
required `mypy tests`, Ruff lint/format and Markdown links. Notebook 04 must remain
code-only and execute sequentially; its summaries are development aggregates only.

## Temporal partitions, inference preparers and executed notebook (milestone 3)

`tests/unit/test_training_temporal.py` maps the temporal/preprocessing/execution
modules to eight synthetic window/horizon comparisons against the existing
reference, causal target/origin boundaries, training-only parameters under
validation perturbation, explicit missing/unknown categories, JSON/CSV inference
roundtrips, rejected Y/controls and stable notebook code/output identities.
Run alongside all earlier preparation regressions and the full foundation gate:

```bash
.venv/bin/python -m pytest tests/unit/test_training_preparation.py tests/unit/test_training_temporal.py -q
.venv/bin/python -m scripts.training_preparation.temporal
.venv/bin/python -m scripts.training_preparation.temporal --verify \
  --baseline .dwp/plans/PLAN_018_training_data_preparation/analysis_results/input_baseline.json
.venv/bin/python -m scripts.training_preparation.notebook_execution --execute
.venv/bin/python -m scripts.training_preparation.notebook_execution --verify
```

The baseline flag uses local plan evidence and may be omitted on another checkout;
manifest/hash verification still applies. Notebook commands require the optional
`notebook` extra declared in pyproject; synthetic tests do not require private data
or notebook runtime packages. Use repository-local `--basetemp` for pytest. Run
Ruff and explicit-package-bases mypy for all preparation modules, required
`mypy tests`, Markdown links, policy scans and scoped DWP conformance. Saved
notebook outputs must match the current artifacts and an actual new-kernel receipt.

No final-block objective may enter adjustment or comparisons. All eight real
partitions must agree with reference key sets; 456 T+1 and 380 T+2 validation
examples per cutoff are expected for the current data, not forced sample limits.
Configured six-month target intervals and actual horizon-specific origin/target
support are reported separately. No predictor training is part of these checks.
