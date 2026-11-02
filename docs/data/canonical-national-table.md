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
