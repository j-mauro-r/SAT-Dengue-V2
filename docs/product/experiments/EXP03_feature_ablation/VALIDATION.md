# EXP03 engineering validation and publication evidence

Current protocol: 2.0.1; primary budget fixed by the [human decision](DESIGN.md#primary-budget-decision--2026-10-27).
The earlier review/validation records below describe protocol 2.0.0 and remain historical evidence;
their hashes and test counts do not certify the budget patch. Scientific execution remains unauthorized.


**Engineering PASS on generated data; scientific results NOT_EVALUATED.**
`B_primary=1.0` is fixed in scientific protocol 2.0.1; no new scientific execution,
private-data exploration, permanent MLflow write, scientific reservation/approval,
champion selection, G5 approval or merge was performed.

## Frozen identities and matrix

- Scope authority: [alcance.md](alcance.md).
- Revised canonical protocol SHA-256: `f806f3897a8dbef2bea01333626ee943e45aec9892f91607ca899f003e55beaf`.
- Legacy protocol SHA-256: `c2f445e767b36dfac5acebca865775d793a93c2a75dc05d829bce82257b57396`.
- Derived matrix: 16 unique sets, 384 onset cells + 24 excess controls = 408 fits;
  102 terminal cells included in those fits. Four primary/twelve secondary ablations
  and two objective comparisons reuse predictions, producing 204 pooled/stress
  contrast records. There is no duplicate T+1 excess fit.
- Three fixed families, both horizons, three overlapping development OOF cuts and
  one separate 2024 stress cut; 2025 is frozen inference only.
- Main `f48f3d4b5a3aa9f67cc4d31dc02424d327f610fb` was merged without conflicts.
  Consolidated EXP00/EXP01 conclusions are preserved; their protocols and science
  code remain byte-identical to main. EXP02 was not modified.

## Executed evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Combined EXP03 generated suites, experiment registry, Kedro configuration and base bootstrap | PASS: 170 tests, 30 dependency/deprecation warnings | DWP gate sequence 7; 497.73 seconds |
| Core scoped Ruff lint and formatting | PASS | 33 formatted files checked |
| Final report rendering and source-summary checks | PASS: 19 focused tests | Native predictions reused, zero additional fits; scoped Ruff/format/mypy PASS |
| Scoped mypy including source and acceptance tests | PASS | 32 source/test files checked |
| Canonical matrix/protocol generation check | PASS | Reproduces the hash and derived counts above |
| Markdown links and diff whitespace | PASS | Repository link checker and `git diff --check` |
| Public repository-disposition contracts | PASS: 25 tests | Missing pinned Git objects were fetched; historical identities were not edited |
| Changed-file secret/runtime scans; EXP00/EXP01 preservation | PASS | Diff/source-only scans; no private input or permanent tracking store was read |
| Repository DWP conformance | PASS | 17 checks, no advisory |
| Scoped-plan / all-plan DWP conformance | PASS with advisories | Recorded separately; final task closure is derived from the journal |
| Wheel build and installed-runtime boundary | PASS | Installed wheel runs foundation and rejects optional modeling imports during registration |
| Independent method/code review | PASS | [Durable review](REVIEW.md), 14 findings resolved; same-backend independent agent |

The combined command is documented in the [testing guide](../../../TESTING_GUIDE.md).
All estimator adjustments use generated notifications/climate; full-example native
models/preparers/calibrators are synthetic engineering artifacts. The source-free
budget tests prove denial before private readers, approval evaluation, reservations
or fitting. Native and aggregate fit counters distinguish fitted-but-unavailable
cells and missing versus present zeros. Phase counters reconcile development,
terminal stress and zero-fit benchmarking.

The original performance/debug attempts remain recorded as interrupted, not PASS.
Numerical grouping now avoids copying date-audit DataFrames and reuses each
horizon/cut exposure ledger; this does not change cohorts, estimators or estimands.
No historical plan gate or protected migration identity was rewritten.

## Inspect the complete synthetic example

The full protected example is generated under `tmp/exp03-generated-example/`.
Final bundle ID: `f9f0241e00528c74e3ed19e364558ddc63ca00666b807106b2301ea27ef3bbe3`.
It preserves the validated fit producer and separately records the final renderer
hash. The report-only refinement used zero additional fits. Coverage and transport
SVGs were rendered to PNG and visually inspected; all 102 terminal cells remain
in the annual transport source.
Its entry point is `report.md`; it includes all native CSV/JSON tables, source-date
provenance, reloadable terminal artifacts, checksum manifest and standalone SVGs.
The example includes adverse effects, undefined metrics and unknown sparse-group
guardrails. It is explicitly synthetic and contains no scientific finding.

Reproduce with:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m sat_dengue.experiments.exp03_demo --output tmp/exp03-generated-example
```

A populated native bundle is required: empty placeholders do not pass validation.
Existing output manifests are never overwritten. Its actual generated-data,
code/runtime, protocol and freeze identities remain inside its native receipt.
Protected native rows, municipality diagnostics and model bytes are not committed
or uploaded to MLflow. Only explicitly synthetic, allowlisted aggregates are used
by isolated tracking tests.

## Remote publication and pending scientific work

Publish only to `feature/exp03-complete-feature-ablation` / existing PR #34,
without force push or merge. GitHub API GraphQL and REST queries returned
`Forbidden` in this environment; remote CI and PR-body updates must be reported
from observed results, never inferred from local PASS or publication.

Remaining scientific tasks are exclusively future authorized work: choose numeric
B and its interpretation, review/freeze that identity and clean environment,
verify private source coverage/maturity and historical publication availability,
run the actual 408-cell experiment and consumed benchmark, and interpret real
results. Private parity and actual capacity are unverified. The implemented
benchmark emits explicit not-evaluable records when provenance is insufficient.
G5 stays `NOT_APPROVED`; champion stays `not_selected`.

## Consumed-2025 transport validation correction (PR #34)

The reviewed baseline `171f0af6b40b06edb8ab08d71f96335af5cf7ed5` inspected
`year`, while the benchmark producer emitted `target_year`. A generated-data
reproduction using the baseline `_validate_tables` accepted an annual 2025 row
with `evidence_type=prospective_confirmation` and `model_fits=99` through both
`write_bundle` and `validate_bundle`. The reload fixture regenerated native JSON,
CSV, annual presentation summary, payload hashes and bundle identity; rejection
was not masked by an integrity failure. Local evidence is retained in ignored
`tmp/exp03-transport-reproduction.log`.

The shared writer/reloader validator now requires canonical `target_year`.
Year-only legacy rows are rejected; a redundant `year` is explicitly normalized
and must agree. Annual/common-month 2024 rows require `retrospective_stress`,
2025 rows require `consumed_retrospective_benchmark`, and `2024-2025` requires
`count_pooled_descriptive` / `descriptive_consumed_2024_2025_context`.
Supplied target months must agree with that period. All periods require the five
explicit integer-zero fit/search/threshold-selection counters, including valid
reason-bearing `not_evaluable` rows. Missing, null, boolean and non-integer
counter values are rejected. The producer now explicitly names its unavailable
annual view, and the old reporting fixture uses its real `target_year` schema.

Validation: **461 generated-only tests PASS** (22 dependency warnings), covering
the new producer-shaped regression suite, reporting, benchmark, revision,
experiment-registry and Kedro-configuration contracts. Scoped Ruff, formatting,
mypy and canonical protocol/matrix checks PASS. The regression suite checks both
publication boundaries and re-signs altered synthetic artifacts to exercise
semantic rejection. No private source, real scientific execution or permanent
MLflow store was used. Models, features, labels, budget, windows, matrix and
scientific methods are unchanged; the canonical protocol SHA above is unchanged.
At that validation of protocol 2.0.0, `B_primary` was pending (superseded by 2.0.1);
G5 was `NOT_APPROVED`, champion `not_selected`.

## EXP02 integration conflict resolution — 2026-10-27

Integrated main `f13ae214eee83fb59bff22780710dc03137ecbf0` into the existing
EXP03 branch through a normal merge. The nine conflicts retain both experiments'
catalog entries, registered identities, profile guards, artifact validators,
bootstrap expectations, documentation and disposition directories. The automatic
pipeline-registry and tracking-hook merges were also inspected. No scientific
protocol or frozen matrix was changed.

Focused integration evidence:

- 99 configuration, registry, disposition, EXP01/EXP02 catalog, EXP02 tracking and
  EXP03 aggregate-validation checks passed in the existing pinned foundation
  environment. One additional bootstrap check initially rejected that environment's
  historical package metadata (`0.1.0` versus source `0.2.0`); the same check passed
  in the existing `0.2.0` development environment, without changing either runtime.
- 19 additional checks passed for EXP03 source-free admission/preflight guards,
  EXP02 protocol preservation and isolated EXP00/EXP01 tracking. The 408-cell native
  generated-estimator fixture was intentionally excluded from this merge check;
  GitHub owns the full required validation.
- Base bootstrap registered EXP00 replay and all EXP01/EXP02/EXP03 graphs without
  importing optional modeling/tracking modules, and executed only foundation.
- Scoped Ruff, formatting and mypy passed for the seven merged shared Python
  modules/tests. Markdown links and diff whitespace passed.
- The canonical EXP03 contract check retained 384 onset cells plus 24 excess
  controls, 408 total and 102 terminal cells, at the unchanged protocol hash above.
- Source/document comparisons confirmed EXP00/EXP01/EXP02 scientific modules,
  protocols and conclusions remain byte-identical to current main. Tests used an
  isolated worktree with no private data or permanent MLflow store.

Remote CI for the resulting merge commit must be observed separately. This bounded
integration check is not a new independent scientific review or real-run approval.
At that integration check, the budget, scientific authorization and PR merge decision
were pending. The budget is now resolved by protocol 2.0.1; authorization remains separate.

## Protocol 2.0.1 budget correction — 2026-10-27

PLAN_045 records the separate versioned decision resolving PLAN_044's historical
budget blocker. The original operational failed gate remains intact; no operational
task was resumed. Current and prior canonical hashes are recorded in
[the decision owner](DESIGN.md#primary-budget-decision--2026-10-27).

- PASS: protocol/matrix check; **384 onset + 24 excess = 408 cells; 102 terminal cells**.
- PASS: **36 focused tests**, two unrelated generated-fit/reservation cases deselected,
  five existing dependency warnings. Command: `.venv/bin/python -m pytest tests/contracts/test_exp03_budget.py tests/unit/test_exp03.py tests/integration/test_exp03_input_integration.py::test_pending_budget_blocks_before_authorization_or_any_raw_read -k 'not probe_counts and not reservation_survives' -q`.
- PASS: Ruff, formatting and mypy on all seven modified/added Python files.
- PASS: JSON/YAML parsing, Markdown links, diff whitespace and diff secrets/private-path scan.
- PASS: independent read-only [review](REVIEW.md#protocol-201-budget-decision-review--2026-10-27).
- PASS: repository-only DWP conformance. Scoped PLAN_045 closure is recorded locally.
  Global initial conformance failed on two pre-existing historical plan issues;
  those failures are not current-code failures and were not waived or repaired.

The first focused attempts exposed a test mock that incorrectly intercepted EXP01's
whole-registry validation. The fixture now captures EXP01's valid identity before
mutating EXP03; the final focused selection passed. Original failure logs remain
in the local DWP journal.

No scientific execution, native-estimator probe, fits/calibrations, private-data read,
operational preflight, `approval.json`, runtime build or MLflow write occurred.
GitHub owns full tests, wheels and general checks; remote status is reported in
the PR handoff, not inferred from these scoped results. After merge, restart the
operational sequence on the new commit as specified by DESIGN.md.
