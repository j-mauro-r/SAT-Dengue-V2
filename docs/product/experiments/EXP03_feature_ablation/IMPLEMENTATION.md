# EXP03 complete-scope implementation and traceability

Engineering validation **PASS (generated data only)**. Scientific execution is **NOT_AUTHORIZED**;
`B_primary=1.0` is human-approved before execution, G5 is `NOT_APPROVED`, champion is `not_selected`.
The scope owner remains [alcance.md](alcance.md). Synthetic estimator fits and
synthetic benchmark rows demonstrate software behavior, never scientific findings.

## Requirement → component → acceptance test → artifact → evidence

| Scope | Requirement | Component | Generated acceptance tests | Native output | Status |
| --- | --- | --- | --- | --- | --- |
| §1 | Preserve consolidated EXP00/EXP01 and invalidate legacy identities | Protocol v2, registry, preflight | `test_exp03.py`, registry contracts | Versioned protocol/receipt | PASS_GENERATED |
| §2 | Finite questions, conditional predictive contribution, no new searches/models | `exp03_revision.py` | `test_exp03_revision.py` canonical tamper checks | Variant inventory and report | PASS_GENERATED |
| §3 | Exact calendar onset/excess, known Y(T)=0; T+1 never admits T+2 | `exp03_features.py`, historical `onset.py` | Revision and causality suites | Native labels, eligibility, error types | PASS_GENERATED |
| §3 | No future observation affects an earlier origin; stored outcome injection differs from raw-count perturbation | Feature recipes and source-event dates | `test_exp03_causality.py` | Recipe provenance, audit keys | PASS_GENERATED |
| §4 | B/U/L/Z/R-/R0/F/C-/Cm formulas; current removal eliminates equivalent encodings | Canonical recipes; native adapter | Revision, causality and persistence suites | Inventory and feature schema | PASS_GENERATED |
| §4 | Finite log1p observed/expected with zero flag, missing distinct from zero | Ratio recipe | Zero/missing/positive-zero gate tests | Coverage/reason counters | PASS_GENERATED |
| §4 | 16 unique variants; P1–P4 and S1–S12; V00/V09 excess at T+2 only | `cell_grid`, composition validator | Derived counts and duplicate/forbidden-control tests | Matrix; 408 cells, 102 terminal identities | PASS_GENERATED |
| §5 | Exact four temporal cuts, origin embargo, separate fit/calibration/selection | `role_parts`, two-phase engine | Role boundary and future-label tests | Source-cut predictions and exclusions | PASS_GENERATED |
| §5 | Fixed normalized B, floor(B×D), whole ties/no-alert and exact selection replay | Admission and `select_threshold` | Evaluation, reporting and input-integration suites | Native selection predictions; threshold evidence | PASS_GENERATED |
| §5 | Missing B blocks before sources, reservation or adjustment | Preflight and both runner boundaries | Source-free denial tests | Pending-budget preflight | PASS_GENERATED |
| §6 | Same union cohort for all arms and controls; pre-gate monitored/eligible/common exposures | Cohort builder and cluster ledger | Feature, evaluation and reporting tests | Exposure, coverage, exclusions, potential recovery | PASS_GENERATED |
| §6 | 60-month cut-specific profiles; 48-month coverage, 50% zero rule, type-7 tertiles, collapsed strata | `historical_profiles` | Profile cutoff/ties/missingness tests | Frozen membership, boundaries and continuous summaries | PASS_GENERATED |
| §6 | No-fit stale-input stress; conditional gate versus strict inability to issue; unsupported inputs | Feature recipe, frozen support audit | Causality and native persistence tests | Error/delay table and effective source dates | PASS_GENERATED |
| §7 | Counts, onset utility, objective-labelled raw/calibrated metrics, micro/macro/equal-year and groups | `exp03_evaluation.py` | Undefined metrics, denominators and grouped-coverage tests | Group, reliability and contrast source tables | PASS_GENERATED |
| §7 | Paired two-way municipal/year OOF bootstrap including exposure-only clusters | `paired_interval` | Exposure perturbation, valid-draw and reserved-year rejection tests | Metric-specific intervals and resampling audit | PASS_GENERATED |
| §7 | Tri-state benefit/burden/department/profile/support; no equivalence or automatic winner | Contrast assembly/guardrails | Sparse and adverse cases; objective-target distinction | Decision rows and paired effect plots | PASS_GENERATED |
| §8 | All terminal artifacts frozen before either stress output; native reload equivalence | `exp03_persistence.py` and two-phase engine | All-family roundtrip, full grid and tamper checks | Native models; freeze/reload receipt | PASS_GENERATED |
| §8 | Inference-only consumed benchmark; zero fits/calibration/search/threshold selection | `exp03_benchmark.py`, separate raw adapter | Benchmark and benchmark-input suites | Separate annual/common-month/count-pooled transport | PASS_GENERATED |
| §8 | Coverage/maturity/as-of provenance and prior-role embargo; historical EXP01 guard preserved | `exp03_inputs.py`, admission boundary | Readiness-before-reader, raw identity and 2025 guard tests | Explicit not-evaluable results or governed coverage | PASS_GENERATED |
| §9 | All receipt/inventory/prediction/selection/contrast/group/exposure/delay/transport/model outputs | Reporting and atomic dataset publication | Bundle semantic reconstruction, manifest/symlink/duplicate tests | Complete protected bundle and report | PASS_GENERATED |
| §9 | Plot source tables, paired uncertainty/burden, group effects, calibration and abstention | Reporting generator | Substantive synthetic output tests | SVG plots and adjacent CSVs | PASS_GENERATED |
| §9 | Native municipal rows protected; closed aggregate-only MLflow and honest counters | Tracking v2 | Isolated synthetic tracking privacy/tamper tests | Aggregate parent artifact; native rows stay local | PASS_GENERATED |
| §10 | Generated-only validation and independent review; no old approval reuse | Focused suites and review receipt | Acceptance suites; v2 admission/identity | Validation evidence and updated PR | PASS_GENERATED |

The frozen-source combined gate passed **170 tests**, Ruff, formatting, mypy,
Markdown links and canonical contract checks. Final presentation-only refinements
passed **19 reporting checks**, scoped quality and actual SVG/PNG inspection,
reusing the validated predictions without additional fits. Separately, **25 public repository
disposition contracts passed**. The [independent review](REVIEW.md) resolved all
material findings. [Validation and publication evidence](VALIDATION.md) separates
local engineering checks from remote CI and future private-data validation.

## Derived matrix and engineering choices

`exp03_revision.build_design` is the single recipe/composition source.
`cell_grid` includes objective in cell identity and derives 384 onset + 24 excess
cells, 408 total, with 102 terminal cells. Contrasts reuse those predictions:
204 pooled-development/stress comparison records (192 ablations plus 12 objective
controls), with per-year diagnostics. The 102 terminal fits are part of the 408;
benchmark inference does not add fits. Undefined or harmful results are retained.

The current Z excess flag is identically zero inside known Y(T)=0 eligibility;
it is retained for auditable group semantics, with no learned value claimed.

The delay changes the whole current recipe to T−1: current difference becomes
count(T−1)−count(T−2), and current mean uses T−1,T−2,T−3. Independent B/L/R-/C-
recipes retain their original dates. This prevents an artificial zero difference
from substituting only one arithmetic operand. Y(T) is still required separately.

CSV is the native tabular equivalent of the specified parquet files. Safe native
family bytes and JSON state replace unsafe object snapshots. Native raw and
calibrated scores retain full float precision for threshold reconstruction.
Every terminal cell is reloaded and compared on pre-evaluation selection rows at
absolute tolerance 1e-12, relative tolerance zero, before opening stress outputs.

## Reproduce and inspect the generated example

Run from the repository with modeling extras installed:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m sat_dengue.experiments.exp03_contract --check
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m sat_dengue.experiments.exp03_demo --output tmp/exp03-generated-example
```

The second command creates generated notifications/climate, fits the declared
fixed families only on those fixtures, persists all 102 terminal cells, evaluates
the generated 2025 benchmark, and creates `report.md`, SVGs and all native tables.
It never loads scientific sources or starts MLflow. The output is marked
`synthetic_generated_data`; no approval, scientific reservation or real run ID is
created. Protected full bundles remain ignored under repository `tmp/`.

## Historical preservation and future admission

Legacy ten-set/240-cell protocol SHA-256:
`c2f445e767b36dfac5acebca865775d793a93c2a75dc05d829bce82257b57396`,
retained in Git at `01ce215c2d7738efe3a664e869ae87a3dd7199a6`.
The revised protocol, matrix, registry and v2 result/approval schemas invalidate
legacy approval reuse. Existing tracking-store pins are never silently rewritten.
EXP00/EXP01 identities/protocols/results remain unchanged; main's consolidated
conclusions were merged. EXP02 remains the label-sensitivity owner.

Before any future scientific execution, choose B with its units/rationale under
human authority, freeze and review that new protocol identity, and obtain a clean
reviewed v2 authorization. Coverage/maturity must be established in governed source
provenance under `coverage.exp03_consumed_2025_readiness` with explicit
`governed_coverage` and `maturity_verified` booleans. Calendar dates alone do not
supply that evidence. Missing evidence produces per-cell not-evaluable transport.
Private-data parity, publication vintages, actual capacity, real scientific
results and any later prospective confirmation remain pending authorization.

## Operational admission contract

The operational sequence is **structural preflight → authorization → verified
admission**. This changes the execution boundary, not scientific protocol 2.0.1
or its canonical hash `18ce612581d710245294f3966187178e697df1972d45b460f54be7cc2f4d1611`.
The frozen budget remains 1.0; 408 cells include 102 terminal cells, yielding one
parent and 408 children (409 expected runs).

1. **Structural preflight:** validates the public protocol, configuration, catalog,
   declared canonical paths, installed runtime and separate result/tracking roots.
   It returns `status="structural_pass"`, `execution_ready=false` and
   `source_identity_status="pending_authorized_verification"`. It neither opens
   nor hashes scientific inputs. `expected_source_sha256` is explicitly the
   reviewed `NATIVE_IDENTITIES` pin for the Stage 2 manifest, a root of trust for
   its output records; it is not an observed hash of the panel CSV. The existing
   `data_version` field remains an expected-manifest identity alias. The descriptor
   names this origin and the separately pinned DIVIPOLA catalog. Private reads,
   fits/calibrations, reservations and MLflow writes stay zero.
2. **Authorization:** a new EXP03-only record under the existing
   `exp03-execution-approval-v2` schema must additionally contain
   `structural_receipt_sha256=digest(receipt)`. This canonical digest binds the
   entire receipt: commit, protocol/version, budget, configuration, runtime/code,
   expected source identities, MLflow root, output path and counts. Existing
   approvals lacking that field fail closed. It authorizes verification; it does
   not claim that actual input bytes have already been verified. `authorize`
   reruns structural preflight for freshness without opening scientific inputs.
3. **Verified admission:** only after authorization, authenticate the manifest
   bytes against their expected pin before parsing it. Require exact governed
   output paths, reject symlinks/traversal/external paths and verify all dependent
   payload hashes plus the separately pinned catalog. Validate the necessary
   consumed-column schema through the unchanged EXP01 raw-input adapter. Return
   `source_identity_status="verified"`, distinct expected/observed manifest hashes
   and observed per-file fingerprints. Only after schema admission is the receipt
   status `verified` and deterministic cohort preparation allowed to reach the
   execution-reservation boundary.

The parser consumes temporary verified copies under ignored
`tmp/exp03-admission-snapshots`, with owner-only directory/file permissions.
Each bounded-memory copy is hashed from the same open descriptor and compared
against the approved identity before the parser can see it. Copies are deleted
on success or failure. Replacing and restoring an original file during parsing
cannot substitute its new values into the verified snapshot. Original paths are
rechecked after parsing and immediately before reservation/MLflow; persistent
source changes fail closed. Snapshot copies are private transient inputs, not
scientific publications or MLflow artifacts. Operational disk estimates must
include one temporary copy of admitted inputs.

The later consumed-2025 path checks the terminal freeze, revalidates the manifest
before reading coverage/maturity, and uses a new verified snapshot if that path
is evaluable. It does not change 2024/2025 eligibility, fitting or inference rules.
The receipt and final native provenance retain the observed identities,
`source_admission` and `admission_sha256`; real-result validation/publication rejects
missing or contradictory admission lineage. Aggregate-only MLflow privacy remains
unchanged. Admission failures and pre-reservation failures carry explicit zero
reservation/run-write/fit/calibration/publication counters. Failures after tracking
or fitting starts do not claim those earlier effects were zero.

After this correction is merged, resume PLAN_044 on the new clean commit: rebuild
wheel/runtime, verify checkout/wheel/installation correspondence and preservation
hashes, run one standalone structural preflight, obtain independent operational
review, create a fresh full-receipt-bound approval, validate `authorize(receipt)`,
then validate admission without calling `execute_authorized`. Record before/after
protected-store identities and provide Mauricio the separately authorized manual
command. Authorization-time structural rechecks are required freshness checks,
not scientific execution. No operational approval is created by this PR.
