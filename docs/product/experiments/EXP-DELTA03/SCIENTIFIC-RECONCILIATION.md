# EXP-DELTA03 — scientific source reconciliation

## Current decision

Source outcome: **`HISTORICAL_ESTIMAND_RECONCILABLE`**, not equivalence of the
new mart fields. Phase 1 remains incomplete. No final matrix, target-source
substitution, retrospective protocol amendment or predictive MODIS encoding has
been adopted. Scientific execution remains `not_authorized`.

The historical residence-based outcome can be reproduced exactly from the same
immutable microdata. The current mart instead measures notifications assigned to
occurrence geography, with a different date/absence policy. Choosing which target
source EXP-DELTA03 will consume is a material contract binding. Calendar controls
are the only presently demonstrable point-in-time predictors; they cannot support
the intended climate ablation. Current excess `E(T)` also comes from consolidated
notifications, whose operational availability at T is unverified.

This report supplements [the Phase 1 handoff](PHASE1.md). It preserves the
[academic contract](../contrato.md), original predictive results and PLAN_054.
PLAN_055 continues at `T-final-review`, with scientific readiness unsatisfied.

## Evidence and reproducibility

The local companion `tmp/exp-delta03-phase1/reconcile_science.py` imports only pure
producer parsers, streams notifications and reuses the existing strict admission
and atomic publisher. No producer entry point/writer, model, fitter, calibrator,
notebook or MLflow writer is invoked. The reusable calculations and generated
tests are `data/exp_delta03_reconciliation.py` and its unit-test owner.

Run from the repository root, with the read-only sibling producer available:

```bash
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/python -B tmp/exp-delta03-phase1/reconcile_science.py
.venv/bin/python -B tmp/exp-delta03-phase1/check_readiness.py
```

The second command is expected to exit **1** under the current authorization.
Requested evidence names remain under `tmp/exp-delta03-phase1/`:

| Product | Consumer |
| --- | --- |
| `source-correspondence.json` | Notification semantics, reconstruction and estimand decision |
| `source-correspondence-summary.csv` | Municipality/year and department/month discrepancy audit |
| `h5-parity.json` | Historical H5/frozen-label parity and new-input impact |
| `cohort-parity.json` | Complete selection/evaluation sets and national controls |
| `cohort-key-hashes.json` | Historical role/key/label hashes, explicitly not new experiment admission |
| `vintage-ledger.json` | Source/version/date evidence and conservative primary dispositions |
| `modis-composition-analysis.json` | Annual closure, zeros and encoding alternatives |
| `scientific-readiness-decision.json` | Current failing gates and bounded human proposal |

Additional national, water-support and aggregate municipality-month audit files
explain those products. `reconciliation-inputs.json` binds 90 read-only input
identities, analysis code and post-analysis preservation checks. A content-addressed
bundle contains the reports and reproducible companion; its identity is in
`reconciliation-publication.json`. Repeated identical analysis verifies/reuses the
immutable publication. Earlier bundles and engineering evidence remain preserved.
No raw patient record or identifier is exported.

Frozen manifest admission enforces existing authority hashes before trusting
payload records: regional `03744548…261d8`, national `e801cf9b…94afb4`, benchmark
`4ca5b835…15f2f`, recovered selection `9261b170…bb4b6`, and Stage 2 execution
`241aa320…213a`. Payloads and input identities are verified separately. The
producer fact key set is reconstructed from the independent union of raw-derived
occurrence keys, including event-specific zeros only on that observed union.

## Notification correspondence

Both repositories contain byte-identical source streams:

- Event 210: 1,705,604 records; SHA-256
  `58d277cfef7a60c28d488eefe4e7a1a7bf0f7b0df3dd88245971cd7b3d32c84b`.
- Event 220: 50,101 records; SHA-256
  `3d60e96ccbedc35a19a8f5f54be8d786aa599813259c914f131522bf17dd1d70`.

They are notification records, not proven unique patients/episodes or a
confirmed-only population. Both transformations count their source stream;
neither deduplicates patients nor sums 210 with 220. Current source domains
contain probable notifications and no `AJUSTE=6` or `D`. Upstream extraction
completeness and the historical export recipe remain unverified.

The [INS 2019 notification form](https://www.ins.gov.co/BibliotecaDigital/210_220_580_Dengue_2019.pdf)
identifies 210 as dengue and 220 as severe dengue, with separate occurrence,
residence, consultation, symptom-onset and notification fields. The
[INS 2024 protocol](https://www.ins.gov.co/buscador-eventos/Lineamientos/Pro_Dengue.pdf)
describes probable and confirmed notifications. Those dated documents support
concept definitions; they do not establish a constant export specification over
2007–2025 or released historical snapshots. Local public copies and their hashes
are retained with the evidence.

| Rule | Historical V2 | New mart producer |
| --- | --- | --- |
| Geography | `COD_DPTO_R + COD_MUN_R`, residence | `COD_DPTO_O + COD_MUN_O`, occurrence |
| Date | `INI_SIN` only | Valid 2007–2025 `INI_SIN`, otherwise `FEC_CON`, then `FEC_NOT` |
| Missing month | Explicit approved calendar-zero assumption | No observed fact row remains missing in the full-grid left join |
| Geography repair | Approved catalog/window; unresolved records remain unassigned | Two explicit documented code equivalences; no residence fallback |

The producer code is `scripts/build_dengue_municipio_mes.py` with its DIVIPOLA
validator. Historical rules are traced through V2 consolidation, national
diagnostics, frozen manifests and approved canonical contracts. Source identities,
code, dictionaries, reports, export scripts and registry metadata were inspected
read-only; no historical source was rewritten.

Independent reconstruction matches **all 100,451 producer fact keys**, both
fields across **all 255,816 new-mart keys including missingness**, all **17,936
regional historical keys**, and both counts on all **182,886 national keys**.
There are zero unexplained reconstruction residuals. The same raw snapshot rules
out differing input revisions as the explanation *between these two products*;
it does not prove either upstream extract was unrevised at historical origins.

For the 17,328 common regional keys:

| Event | Different | New missing, old zero | New missing, old positive | Both observed but different |
| --- | ---: | ---: | ---: | ---: |
| 210 | 10,337 | 5,345 | 268 | 4,724 |
| 220 | 5,982 | 5,590 | 23 | 369 |

All 76 municipalities and years 2007–2025 are affected. Meta/Tolima differences
are respectively 3,701/6,636 for 210 and 1,995/3,987 for 220. New missing keys are
1,842 in Meta and 3,771 in Tolima. Changing locality affects 4,991/389 count cells;
date priority/range affects 13/3. These latter counts overlap and are **not
additive causal attribution**. The explicit ordered arithmetic decomposition has
zero residual; audit zero representation is never adopted as a new label rule.

Full outer membership retains 608 regional-only keys and 238,488 mart-only keys.
The broader national comparison has 182,886 shared keys, no national-only keys
and 72,930 mart-only keys. New-vs-national differences are 133,686/108,985 for
210/220, with 107,655 new missing keys. Unmatched keys are reported, not hidden by
a convenient intersection or used to redefine a cohort.

## H5, cohorts and chronology

Only the **already approved historical source** was used for H5 reconstruction.
No new-mart H5 label was constructed in this follow-up. Five exact prior
same-month years, type-7 P75 and strict excess reproduce all 13,376 known regional
current thresholds, including their missingness, without discrepancy. The national
control matches current P75 and both onset columns on all 182,886 keys.

All **16 complete frozen selection/evaluation cells** reproduce exact key sets,
labels and roles. This includes evaluation controls T+1 2,653/313 and T+2
2,422/219 rows/onsets. Original predictor-complete cohorts match full reconstructed
eligible sets; no key intersection or removal is needed. Separate hashes cover
120 regional and 160 national role/scope controls, including transfer exclusions.
They are historical controls, not a newly authorized EXP-DELTA03 cohort freeze.
Nationwide evaluation-role hashes describe diagnostic grids; final evaluation
remains exclusively Meta/Tolima.

The original 76 territories first have current H5 in **2011-06**. The other
1,046 first have it in **2016-06**, because their approved national calendar starts
in 2011-06; no unapproved pre-window history is imported from the new mart.
Eligible historical origins stop in 2024-11/2024-10 for T+1/T+2. Missing years are
not replaced; threshold equality is non-excess; absent records retain their
source-specific semantics. Generated tests exercise missing years, ties,
boundaries and unavailable outcomes.

Target-year roles remain training through Y−4, calibration Y−3, embargo Y−2,
selection Y−1 and evaluation Y, with the inherited December origin embargo.
2024 remains consumed stress evaluation; 2025 cannot enter development/evaluation.
Main national controls retain permitted Meta/Tolima histories; transfer controls
exclude both from learned roles and evaluate on them separately.

Substituting new count inputs threatens an H5 dependency on **2,645/2,653 T+1**
and **2,420/2,422 T+2** frozen evaluation rows; 2,017/1,929 respectively encounter
a missing new count. This measures changed/missing inputs, **not computed changes
in unauthorized onset labels**. Numerical coincidences would not establish the
same residence-based epidemiological estimand.

## Vintages and the minimum admissible subset

The 37-entry ledger covers every requested family and distinct demographic
version/period. It records 2 `VERIFIED_POINT_IN_TIME` calendar controls, 33
`RETROSPECTIVE_ONLY` records and 2 `UNVERIFIED` terrain records; none is promoted
to `STATIC_VERIFIED`. Unverified/retrospective inputs are excluded from primary
PIT admission under Mauricio's explicit conservative-exclusion instruction.

CHIRPS and ERA5 export requests/downloads in November 2026 do not identify
origin-specific released values. NOAA's source is current ERSSTv6; its
[documented historical ONI revisions](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_change.shtml)
also preclude treating a current historical series as its original real-time
values. NDVI, land cover and water have current product identities without
release archives. Population/urbanization/age versions contain reported 2025
publication/revision metadata, not the historical projection vintages required
by earlier origins. SRTM's static measurement does not establish historical
applicability of its current municipal geometry/aggregation.

`FEC_NOT`, `FEC_AJU` and `FEC_ARC_XL` are inspected as notification, adjustment and
export fields. They do not recover an immutable historical notification snapshot,
including missing/deleted/changed records. Consequently consolidated `E(T)` does
not prove operational eligibility known at T, even with calendar-only predictors.

Only `month_sin` and `month_cos` are individually admissible PIT predictors.
Calling their identical vectors `FULL_COMMON` and `HISTORY` would not test climate
utility. No meaningful PIT climate matrix can be published from current evidence.
Strict PIT completion requires actual released-value archives, including the
origin-state dependency; a retrospective alternative requires explicit amendment.

Water remains secondary and genuine observations end in 2021. Both 2024 folds
have **zero** observed lag-one water support in selection and evaluation. Do not
impute, interpret this as zero observed water, or remove the 2024 primary fold.

## MODIS composition and bounded proposal A

There are 20,196 complete municipality-years (1,122 × 2007–2024), with all 2025
annual values missing. Five separate audit parts sum to 100 within 1e−4 percentage
points; centered rank is four. The 1,308 strict boundary excursions are floating
roundoff, with zero bound violations beyond that tolerance. Annual zero counts
are 28 natural, 15,893 agricultural, 5,912 urban, 15,204 bare/other and 17,495
mixed-mosaic observations. Monthly replicas are not independent annual samples.

All three requested encodings were considered. Omitting a reference preserves
the mosaic's meaning; excluding mosaic changes what remains unrepresented;
log-ratios require a material zero-handling choice. Multiple defensible encodings
exist. **No predictive encoding is selected.** MODIS is currently excluded from
the primary PIT vector for lack of vintage evidence, so its encoding does not
block that conservative disposition.

Recommended **proposal A**, not adopted:

1. Bind labels to the pinned V2 residence/INI_SIN source and existing approved
   D2/D3 calendar, original history context, H5 and cohort/role identities. Keep
   current occurrence notifications audit-only; do not alias them as residence.
2. Explicitly amend Phase 1/protocol/DWP acceptance to a **consolidated-data
   retrospective ablation**, preserving event-time causality and training-only
   transformations, while recording snapshots as `RETROSPECTIVE_ONLY`. Make no
   operational PIT claim. This is a proposed requirement change, not a passing
   result under today's PIT gate or permission to invent release dates.
3. For that retrospective vector, retain natural, agricultural, urban and mixed
   mosaic fractions separately; omit bare/other as reference and audit all five.
   Use no arbitrary mosaic redistribution, pseudocount or future annual value.
4. Retain genuine common-support water only in supported secondary cells;
   unsupported 2024 water comparisons remain unavailable. Preserve main cohorts,
   2024 stress status and the exclusion of 2025.

Alternatively, retain strict PIT requirements and obtain historical archives.
Using new occurrence labels instead would require a separately defined
retrospective target, absence policy, new cohort freeze and recomputation of every
baseline on the same labels/cohorts/cuts under future authorization. Frozen V2
metrics could not be presented as matched comparisons.

Approval of proposal A would authorize a bounded **preparation-contract revision
only**. It would not approve training, calibration, thresholds, hyperparameters,
Phase 2, G5, champion selection or merge. Current contracts and failing readiness
remain in force until Mauricio decides.

## Scoped validation and review

Focused scientific/preparation and generated Kedro-session checks passed 48 tests,
including local generated manifest/payload-tampering controls. Existing temporal,
H5, availability, block, leakage and deterministic publisher tests were reused.
No full local suite was run. Changed Python and document gates are scoped; final
remote CI is observed on the published PR head and recorded in the PR/evidence.

Independent read-only review closed two medium evidence guards: enforcing frozen
manifest authority hashes and independently deriving the complete producer key
union. Final source/docs/snapshot review has no unresolved critical/high/medium
findings. The complete final analysis repeated with identical payload bytes and
verified immutable reuse. No final matrices were published; `check_readiness.py`
returned its intended exit1 and false scientific-admission gates.
