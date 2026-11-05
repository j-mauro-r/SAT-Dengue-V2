# EXP-DELTA03 Phase 1 — engineering handoff and scientific admission blockers

## State

Preparation infrastructure is implemented and exercised with generated sources and
the real identified CSV. **Phase 1 is not scientifically complete.** The [scientific reconciliation](SCIENTIFIC-RECONCILIATION.md) now reproduces
historical counts, H5 and frozen cohorts exactly. Binding that separate target
source into EXP-DELTA03 and choosing the availability regime remain unapproved;
every final training matrix is withheld. This is a preparation/data-quality execution, not a predictive
experiment. Protocol stays `draft`, execution `not_authorized`, G5 `NOT_APPROVED`
and champion `not_selected`. There were zero estimator fits, calibrations,
threshold selections, scientific model executions or MLflow writes.

Mauricio's subsequent Phase 1 request explicitly authorizes implementation on
`docs/exp-delta03-design` and the existing PR #78, including the two bounded CI
repairs. It supersedes the original documentation-only boundary for preparation,
without authorizing training, Phase 2 or merge. Local DWP
`PLAN_055_exp_delta03_phase1_preparation` records new execution evidence;
PLAN_054 remains unchanged. The scientific-readiness criterion stays open.

The executable [Phase 1 contract](phase1-contract.json) owns pinned admission,
source columns, metadata identities and preparation policy. [DESIGN](DESIGN.md),
[draft protocol](protocol.draft.json), [draft matrix](ablation-matrix.draft.yml)
and the [academic contract](../contrato.md) retain scientific authority.

## Admitted source and descriptive coverage

| Property | Verified value |
| --- | --- |
| Source SHA-256 | `1b4d3873f401cb7947b49f0c26023d843823d047aeb433b175de078daa6be486` |
| Bytes | 446,274,685 |
| Rows / original fields | 255,816 / 142 |
| Municipality-month grid | 1,122 municipalities × 228 months |
| Period | 2007-01 through 2025-12 |
| Meta (`50`) | 29 municipalities; 6,612 rows |
| Tolima (`73`) | 47 municipalities; 10,716 rows |
| Duplicate normalized keys / temporal gaps | 0 / 0 |

These are **descriptive grids**, not approved H5 learning/evaluation cohorts.
Raw dates are month-start `YYYY-MM-DD`; preparation normalizes to `YYYY-MM`,
retains DIVIPOLA text, verifies department prefixes and source calendars, and
orders deterministically. Admission hashes/parses/rehashes the same open file,
checks the pinned dictionary/header, exact grid and source identity, and rejects
external paths, symlinks, substitutions and contradictory identifiers. The CSV
and supplied metadata remain unchanged; no copy of the source CSV is published.

EDA inventories all 142 source variables: 5 identifiers, 83 descriptive-only,
14 target/future fields, 34 conditional sources, 5 excluded representations and
1 unresolved mixed MODIS mosaic. These are field dispositions, not a final
predictor-admission decision. The prepared feature contract has 55 names: two
included calendar controls, 36 conditional transformations and 17 unresolved
history/composition fields. No all-missing arm is published as an evaluated matrix.

The source profile reports 25 constant fields and 38 near-constant fields
(dominant non-null share at least 0.995), 19 exact redundant pairs and 43 numeric
pairs with absolute correlation at least 0.98 and at least 24 jointly observed
rows. NDVI mean/median correlation is approximately 0.9822. These are review
recommendations only: correlation never deletes fields or selects predictors.

Observed missingness includes 169 NDVI means, 240 population totals and 456 rows
for each primary rainfall/ERA5 temperature source. Water has 60,518 observed-zero,
127,117 observed-positive, 14,325 spatially unobserved and 53,856 out-of-coverage
rows. Its genuine temporal coverage ends in 2021. MODIS's 2025 missing coverage
is preserved, without extrapolation. Availability flags and actual source values
are reported separately; a populated flag does not prove publication availability.

CHIRPS/ERA5 total precipitation differ on 255,360 paired observed rows, with a
mean CHIRPS-minus-ERA5 difference of about −111.22 mm. Their daily-maximum
statistics also differ in spatial meaning. This does not establish either source
as scientifically superior or justify blending them. The two ENSO phase/event
fields contradict their numeric dictionary types and remain descriptive-only.
Negative annual population growth is a valid signed rate, not a bounded share.
A single snapshot cannot establish historical schema changes or release vintages.

## Exact blockers and minimum next decision

The original frozen regional table is admitted through its pinned manifest and
CSV identity only for read-only correspondence diagnostics. Among **17,328 shared
municipality-month keys**:

| New candidate field | Historical field | Different values | New missing / historical missing |
| --- | --- | --- | --- |
| `notificados_210` | `dengue_notifications_count` | 10,337 | 5,613 / 0 |
| `notificados_220` | `dengue_grave_notifications_count` | 5,982 | 5,613 / 0 |

The follow-up independently reconstructs both products with zero residual and
classifies the historical estimand as `HISTORICAL_ESTIMAND_RECONCILABLE`. Direct
field equivalence is false: producer geography is occurrence, historical V2 uses
residence. The older national diagnostic uses the approved absence-
as-zero assumption and INI_SIN-only date handling; this new product distinguishes
absence from observed zero and documents date-source fallbacks. These are now reproducibly traced
semantic differences, with exact reconstruction of both complete sources. Their
ordered numerical decomposition is not causal attribution or authorization to
alias occurrence counts as residence counts. No 210+220 sum, retained-count substitution, zero fill or
new cohort is silently adopted.

H5's five exact preceding same-month years, type-7 P75 and strict excess are
implemented and checked on generated inputs. Conditional diagnostic labels use
`notificados_210` only as a clearly unapproved candidate mapping; they are not
historical H5 correspondence evidence and are not published as final labels.
Historical controls now match all 16 complete selection/evaluation key/label/role
sets and all 182,886 national H5/onset rows. Final **EXP-DELTA03 target binding and
cohort admission remain UNAPPROVED**. This follow-up constructed no new-mart H5
labels; historical control hashes do not authorize a replacement source.

No supplied metadata demonstrates origin-specific release dates plus exact value
vintages for environmental/demographic sources. Production release evidence is
empty, so those values cannot become historically eligible predictors. An older
release cannot admit a revised current value: guards require matching snapshot
and field-vintage identities. Annual/static transforms consume explicit versioned
observations and select the last genuinely released value; current annual rows
cannot stand in for past vintages. No missing vintage is invented.

MODIS audit aggregation retains natural vegetation, crop, urban, bare/other and
**mixed mosaic separately**. This implements the latest human instruction. The
original proposed three-predictor composition is not frozen; no mosaic allocation
or final predictive vector is approved.

The source-correspondence investigation is complete. The next material decision
is [proposal A](SCIENTIFIC-RECONCILIATION.md#modis-composition-and-bounded-proposal-a):
preserve the pinned historical residence/INI_SIN labels, explicitly amend the
preparation to a consolidated-data retrospective ablation, and retain four
separate MODIS fractions with bare/other as reference. This proposal is not
adopted. Current conservative PIT admission permits only the two calendar
controls; neither meaningful climate ablation nor operational `E(T)` eligibility
is demonstrated. Alternatively, strict PIT completion needs actual historical
release/value archives. No source binding alone resolves this availability gap.
No training, Phase 2 or merge follows from this investigation.

## Implemented route and consumers

| Pipeline/profile | Nodes | Catalog output |
| --- | --- | --- |
| `exp_delta03_preflight` | `exp_delta03_verify_source` | `exp_delta03_admission` |
| `exp_delta03_preparation` | `exp_delta03_profile_source`, `exp_delta03_prepare_and_gate_matrices` | `exp_delta03_prepared` |
| `exp_delta03_synthetic` | `exp_delta03_generated_probe` | `exp_delta03_synthetic_receipt` |

The shared read-only input is `exp_delta03_sources`; `exp_delta03_context` retains
one admitted in-memory base and `exp_delta03_quality` carries profiling results.
Operational parameters are the exact pipeline profile and `tracking=disabled`;
scientific overrides and experiment IDs are rejected. Catalog paths are under
`tmp/exp-delta03-phase1/{preflight,products,synthetic}`. No `exp_delta03` training
executor is registered. Domain calculations are pure under `sat_dengue.data`;
filesystem/catalog serialization belongs to adapters and graph bindings are thin.

Commands from the repository root:

```bash
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipeline=exp_delta03_preflight --params=profile=exp_delta03_preflight,tracking=disabled
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipeline=exp_delta03_preparation --params=profile=exp_delta03_preparation,tracking=disabled
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run --pipeline=exp_delta03_synthetic --params=profile=exp_delta03_synthetic,tracking=disabled
```

These commands admit/profile/prepare or run a generated probe; they do not train.
Repeated identical publications verify exact bytes and reuse the immutable bundle;
changed payloads cannot overwrite it. An existing publication with tampered bytes,
unsafe membership or symlinks is rejected.

Implemented transforms include exact-calendar epidemiological lag machinery gated
on an explicit authorized mapping; T−1 climate values and strict T−3…T−1 windows;
CHIRPS primary and replacement-only ERA5 selectors; central-month ONI T−2 plus
release/vintage guards; lagged NDVI/observation flag, changes and training-only
municipal or national-month references; explicit as-of terrain/demography; separate
MODIS audit composition; and lagged observed-area-qualified water through 2021.
There is no interpolation, backfill, global imputation or epidemiological zero fill.

The 11 arm selectors cover HISTORY, FULL_COMMON, six block removals and water,
ERA5 and geographic-transfer sensitivities. Counts of declared transformations:
CALENDAR 2, HISTORY 12, THERMAL_HUMIDITY 9, RAINFALL_HYDROLOGY 7, ENSO 1, NDVI 6,
TERRAIN 2, DEMOGRAPHY 5, LAND_COVER 5 audit-only, SURFACE_WATER 1 and ERA5 5.
Removing a block removes every descendant/flag. Identifiers, labels, year and
structural coverage strings are outside the closed selectors.

Per-role common masks and ordered-key hashes are implemented for water/ERA5
reference pairs and territorial holdout. Unadmitted real H5 makes final membership
withheld, not an observed zero-support result. Generated tests exercise positive
pairing. Transfer excludes Meta/Tolima from all learned roles and evaluates only
those departments. Existing December-boundary origin embargo is retained; 2025
cannot enter development or evaluation and 2024 remains consumed stress evaluation.

## Evidence and acceptance ownership

The immutable native bundle contains admission, provenance/code/input hashes,
quality/inventory/missingness/redundancy/coverage, label and cohort diagnostics,
availability, transformations, paired memberships, block/matrix descriptors,
MODIS audit, leakage safeguards and explicit readiness blockers. Large/private
products stay ignored under `tmp/`; this handoff contains aggregate findings only.
The verified publication is:

- Bundle: `f7eef157279e4ce62b3faa4f506d0abdae4d7c8dd35619ec3be48ce3025675c8`.
- Manifest SHA-256: `472dd48bbc44f465bf96c217abada23496729bfc8d4f4dcbae0c38b90f98d099`.
- Root: `tmp/exp-delta03-phase1/products/<bundle-id>/`.
- Fourteen payloads, all hashes/readback verified; final matrix files: **zero**.
- Two complete real preparation computations reproduced identical payload bytes;
  the repeat verified/reused the existing immutable publication. Preflight also
  completed against the real source. No source file changed.
- Verified runtime: Python 3.12.11, pandas 3.0.6, NumPy 2.5.4. An outer local
  receipt additionally records the dependency-authority and complete payload hashes.

The pinned source registry contains download/consultation metadata and current
product versions, not origin-specific released value/vintage intervals. Its hash
is verified; those fields are not treated as historical availability proof.

Focused acceptance is owned by [the testing guide](../../../TESTING_GUIDE.md).
It covers generated admission/path mutations, schema/keys/calendar, future-prefix
invariance, versioned availability/as-of selection, H5/roles, block/transfer masks,
training-only references, missingness/redundancy, no-overwrite behavior and real
Kedro catalog/preparation integration. Remote CI owns the integral suite.

The two inherited CI repairs preserve scientific outputs: Shapely is a pinned dev
extra with a controlled missing-dependency error, and national diagnostic I/O/
SQLite/runtime identity moved to `sat_dengue.datasets.national_diagnostics`.
Its pure calculation module is hashed into execution identity. Frozen notebook 09
is unchanged; historical execution requires its historical checkout, not the
current adapter import path. Existing original metadata identities are preserved;
only the current pyproject engineering identity and generated constraints change.

The first integral CI run exposed an additional regression: frozen EXP01–EXP03
preflights rejected the dev-only pyproject addition. This was introduced by this
change and was investigated, not classified as inherited. The bounded engineering
amendment in the migration owner accepts only the exact reviewed new hash and
single literal Shapely line whose removal restores the exact original hash. Frozen
protocol pins and all other dependency bytes remain unchanged. Any other authority
edit fails closed. The focused structural/catalog/admission regression selection
passed 63 tests without fitting, calibrating or opening private source contents.


## Focused validation and independent review

PASS: final affected-surface selection, **107 tests**, including real generated
Kedro preparation/synthetic sessions, new admission/EDA/temporal/block contracts,
bootstrap/configuration, both inherited repairs and the exact directory contract.
The generated geography repair separately passed 12 tests; one private MGN test
requires the unavailable shapefile reader and is not generated evidence. Changed-
file Ruff/format/mypy passed for 23 Python files; JSON, changed Markdown links,
diff whitespace and privacy scans passed. Isolated Shapely/NumPy installation and
geometry calculation passed. No full local suite or predictive run was invoked.

A broader existing local preservation check remains **FAIL** on
`docs/product/traking-concluciones.md`: its current SHA-256
`22ac09f604f86b0af8a216fa6b9bc4cbfd23d29d119403020059969710e517da`
is byte-identical to the task's starting Git blob, while the old private baseline
expects `5255150d71a44655e6159a44784bdffba9bf85f5769caa515c0bcbd4827f43ab`.
This is demonstrated inherited local evidence drift, not a new Phase 1 code
failure or a waived PASS. That expanded selection had 133 passes and this one
failure; private/history checks were not weakened or rewritten. Data-free GitHub
CI retains its existing inventory-absent boundary. Two historical all-plan DWP
failures also remain separately disclosed; repo-only/new-plan results are distinct.

Independent read-only review found and closed six medium issues: exact value/
vintage binding, actual as-of selection, role-specific paired masks, transport
NDVI reference, relocated pure-code execution identity and unsupported dependency
extras in the preserved-pin exporter. Documentation authority/import paths were
reconciled. Re-review reported no unresolved critical/high/medium findings and
recommended the bounded PR update only. Source readiness remains unapproved.

Required CI is observed on the final PR head and recorded in the PR/evidence;
local tests and this technical handoff do not substitute for it. Mauricio retains
the merge decision. Phase 2 is not started.


## Scientific reconciliation follow-up

[The scientific report](SCIENTIFIC-RECONCILIATION.md) owns the new findings,
reviewable alternatives, required decision and reproducible artifact names.
The original engineering bundle above remains immutable. A separate diagnostic
publication under `tmp/exp-delta03-phase1/scientific-reconciliation/` binds the
correspondence, 280 historical role/scope hash controls, 37-entry vintage ledger,
MODIS audit and readiness decision. The local pointer is
`tmp/exp-delta03-phase1/reconciliation-publication.json`.

No final EXP-DELTA03 cohort or matrix was silently substituted. MODIS is excluded
from current primary PIT admission under the explicit conservative rule; its
four-part retrospective encoding is a pending proposal. The original matrix
selectors remain draft/withheld: calendar-only FULL_COMMON and HISTORY would be
identical and would not test climate utility. Scientific readiness still fails.

The scientific follow-up passed 48 focused checks (including generated Kedro
sessions and manifest/payload-tampering controls), with no full local suite.
Independent final re-review has no unresolved critical/high/medium findings.
The companion computation repeated with identical payloads and immutable reuse;
readiness still exits1 for the explicit scientific gates.
