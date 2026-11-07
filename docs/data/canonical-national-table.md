# National Canonical Table V1

The independent `canonical_model_table_national_v1` route builds a municipality ×
origin-month research table from the approved national notification calendar and
climate complement. The [versioned contract](canonical_model_table_national_v1.json)
owns its columns, roles, chronology, source identities and eligibility rules.

```bash
KEDRO_DISABLE_TELEMETRY=1 .venv/bin/kedro run \
  --pipeline=canonical_model_table_national_v1 \
  --params=profile=canonical_model_table_national_v1,tracking=disabled
```

The route is absent from default/replay execution and performs zero model fits.
It requires the explicitly pinned local Step 1 execution
`aa25e8cee5fd9cdaa4bf`, the Step 2 climate union manifest and the original BETA
publication. It neither discovers a latest bundle nor executes the data-local
Step 2 Python script. It verifies the declarative union's components and streams
them with the existing monthly aggregation semantics.

## Construction and availability

The output retains 1,122 territories and 163 origin months, 2011-06 through
2024-12 (182,886 rows). Counts are notifications, not deduplicated patients. Zero
notification months remain zero under the approved D2/D3 assumptions. The 5,663
in-window notifications with unresolved geography remain separately accounted
for in Step 1; they receive no invented municipality assignment.

The fixed national calendar has no approved pre-2011 observations outside the
original 76 municipalities. For those 76 only, pre-window counts from the pinned
BETA table provide H5/lag context; future BETA rows and labels are not used. The
`history_context` column makes this asymmetry explicit. Other territories retain
missing H5 until five exact prior same-month years are available, starting in
2016-06. No municipality is dropped because it has many epidemiological zeros.

Climate uses sums for rainfall, runoff, evaporation and solar energy; means for
temperature, dewpoint, soil water and U/V wind. Each variable requires all days of
its calendar month. All-missing or incomplete sums remain null, and ECMWF
evaporation signs are preserved. Island climate missingness remains explicit;
the epidemiological zero assumption is never applied to climate.

## Safe logical views

The contract's positive predictor list preserves BETA V1. Current counts, exact
lags, monthly climate and origin-safe H5 thresholds are available retrospectively
at T; H5 target-month reference observations must precede or equal T. Direct
`onset_T1`/`onset_T2`, future counts, future Y and outcome availability are targets
or controls. `sat_dengue.canonical.national.predictor_matrix` refuses positive
availability offsets and selects only declared predictor columns.

`g1_no_climate_t1/t2` and `g1_with_climate_t1/t2` are per-row eligibility masks,
not extra physical datasets. Both require complete epidemiological predictors,
known exact-calendar onset, current non-excess and in-window targets; climate ON
also requires all nine complete climate aggregates. Pair any climate comparison
on the intersection of its cohorts. These masks do not authorize training.

The BETA evaluation years 2020/2021/2022/2024, target-based training/calibration/
adaptation/selection/evaluation boundaries and origin embargo remain unchanged.
The publication includes coverage for those roles; no 2025 outcome is used.

## Publication and comparison

The existing atomic publisher writes one identified folder under
`data/processed/canonical_model_table_national_v1/<bundle_id>/`. Repeated saves to
an existing identity fail rather than replacing files. The single national CSV
is accompanied by its contract, column dictionary, provenance, manifest,
eligibility summary, department/year summary, temporal-role coverage and BETA
comparison. All artifacts and upstream sources have SHA-256 identities.

Every common equivalent column on the original 76 municipalities is reconciled
on shared keys. Counts, H5, states, lags, onset labels and cohort masks require
exact agreement. Climate differences at or below 1e-10 are reported as floating
serialization precision, including affected municipalities/months and maximum
absolute differences; a larger discrepancy blocks publication. Legacy
outcome-gated fields for 2025 targets are intentionally missing in this table and
cannot admit a training row. Any unexplained material discrepancy blocks the
publication. The original BETA table is never rewritten.

The source report files remain local under
`data/interim/canonical-nacional-data/`. Private data must not be committed.
Snapshot identity does not establish official extraction completeness,
historical boundary applicability, immutable upstream climate product versions
or operational point-in-time availability. Preserve these limits in any future
G1 protocol; the original EXP-BETA protocols and findings remain unchanged.

The [2026-11-02 real local acceptance](canonical-national-validation.md) records
the explicit final publication, exact parity scope, technical eligibility and
reproduction/preservation evidence.

## National V4 through December 2025

`canonical_model_table_national_v4` is the additive national source intended for
SAT-Dengue V3 and a future `sat-dengue-v3-through-2025-v1` release. The external
experimental V3 added variables without demonstrated value and is excluded from
this construction. No external V3 or EXP-DELTA03 expanded mart is read.

Mauricio's 2026-11-07 request authorizes this bounded extension: the same 1,122
national V1 territories, 175 monthly origins from 2011-06 through 2025-12, and
196,350 unique municipality-month rows. All original national V1 columns retain
their names, order, units and physical types; seven temporal control columns are
appended. No new predictor family or methodological change is introduced.

V4 reconstructs residence/`INI_SIN` notification aggregates from the two pinned
raw SIVIGILA CSVs. It reuses V2 admission, no-deduplication, zero-calendar, climate,
H5, excess and direct-onset functions. The approved climate union includes the
pinned January 2020 national gap supplement; CHIRPS
`UCSB-CHG/CHIRPS/DAILY` and `ECMWF/ERA5_LAND/DAILY_AGGR` are known collection
references, not verified immutable original product vintages. The final national
V1 publication fixes territory identity. Regional V1 contributes only approved
pre-window H5 context for its original 76 municipalities and serves as an
independent Meta/Tolima parity reference; its later rows are never copied.

```bash
KEDRO_DISABLE_TELEMETRY=1 .venv/bin/kedro run \
  --pipeline=canonical_model_table_national_v4 \
  --params=profile=canonical_model_table_national_v4,tracking=disabled
```

The independent graph is excluded from default/replay and all training routes.
It admits explicit content identities, reconstructs raw aggregates, validates
both parities and only then publishes atomically under
`data/processed/canonical_model_table_national_v4/<bundle_sha256>/`.
An existing identity is never replaced. The CSV, schema, effective inherited
contract, long-form `temporal_roles.csv`, parity and provenance have individual
SHA-256 records in `manifest.json`. Generation time, Git revision and actual code
hashes are recorded separately from the deterministic table bytes.

### Maturity and learned-role boundaries

The panel deliberately ends in 2025-12 even though the raw snapshot contains
some January 2026 notifications. T+1 targets run 2011-07–2026-01; T+2 targets run
2011-08–2026-02. T+1 can mature through origin 2025-11, T+2 through 2025-10.
Targets outside the panel retain null excess/onset labels and future counts,
false evaluability and stable `target_outside_panel` status. A mature target can
still have `insufficient_history`; maturity and evaluability are distinct.

Origin and horizon-specific scientific roles mark 2025 origins **or targets**
`consumed_retrospective_evidence`. Historical roles describe evidence and grant
no training authorization. The shared Kedro preparation boundary invokes
`require_learnable`: it rejects 2025 or later origins/targets for training,
preparer fitting, learned imputation/scaling, feature/hyperparameter selection,
calibration, threshold selection and champion selection. Unknown chronology,
roles or maturity metadata fail closed. Existing frozen training contracts and
source pins stay unchanged; V4 is not wired into a fitting graph.

### Parity interpretation and redistribution

All national V1 keys and columns are compared after independent reconstruction
under V1's original end date, including physical dtypes and missingness. Extended
V4 common rows also match except for explicitly enumerated target-dependent
fields whose 2025 outcomes were outside V1's panel. Those necessary maturity
changes are reported by column, never silently normalized. Origin-safe H5
features do not change. Regional Meta/Tolima comparison uses every shared column
and key over the common period, with existing numeric-container differences
reported. Regional V1 extends through 2026-01: its January 2026 labels differ
for 76 municipalities at T+1 origin 2025-12 and T+2 origin 2025-11. V4 retains
null labels for these deliberately excluded targets; every affected column and
origin is explicitly classified as a necessary coverage incompatibility. Only climate serialization differences at or below the already
approved absolute tolerance 1e-10 are accepted; other material differences block
publication.

All CSVs remain private and ignored. Neither aggregation nor this request grants
redistribution rights. Hugging Face publication remains **pending license
review**. Existing limits on official extraction completeness, unresolved
geography, historical territorial applicability, pre-window H5 asymmetry and
operational point-in-time availability remain in the manifest. No training,
calibration, model selection or permanent MLflow write is part of this route.
