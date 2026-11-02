# EXP-BETA01 Phase 2 — retrospective results

Date: 2026-11-01. Delivery: **COMPLETED_WITH_LIMITATIONS**.
[Protocol and implementation](PHASE2_IMPLEMENTATION.md) define the fixed comparison.
This is a local real-data result; updating Git does not transfer private artifacts.

## Identified evidence and population

Result bundle: `37a0cae62f4d3fa59cede281e032c9abd1b568a90933855b9eebd3b3d3fb5f4a`,
under `tmp/kedro-migration/exp-beta01-runs/` locally.
Canonical source: `ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98`.

All eight horizon/year cohorts exactly match the identified historical R0 keys and
onset truths. Each fixed climate/arm contrast uses the same observations. There are
25,375 persisted prediction rows: 20,300 G0/L1 rows and 5,075 reused R0 rows.
No individual patient records are included in this report or committed to Git.

| Target year | T+1 at-risk rows | T+2 at-risk rows | Interpretation |
| --- | ---: | ---: | --- |
| 2020 | 661 | 588 | Retrospective development comparison |
| 2021 | 846 | 779 | Retrospective development comparison |
| 2022 | 693 | 641 | Retrospective development comparison |
| 2024 | 453 | 414 | Previously consumed retrospective stress |

The horizon totals are 2,653 T+1 rows/313 onsets and 2,422 T+2 rows/219 onsets.
Exposure is 221.0833 and 201.8333 observed eligible municipality-years respectively.
All four years are reused retrospective evidence. No 2025 row is evaluated and no
independent confirmation, operational availability or champion is established.

## Pooled descriptive results

The table sums detections, onsets, false alerts and exposure across the four fixed
years. Rates are recomputed from those totals, not averaged across cells.
R0's original predictions/alerts are reused unchanged; all arms' rates use the same
Beta exposure denominator. Historical R0 fit/calibration windows differ from Beta's
new separated adaptation procedure, so this compares procedures, not pooling alone.

| Arm | Climate | Horizon | Detected / onsets | Sensitivity | False alerts | FA / municipality-year |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| R0 | historical | T+1 | 142 / 313 | 45.37% | 231 | 1.045 |
| G0 | OFF | T+1 | 146 / 313 | 46.65% | 179 | 0.810 |
| G0 | ON | T+1 | 152 / 313 | 48.56% | 204 | 0.923 |
| L1 | OFF | T+1 | 138 / 313 | 44.09% | 175 | 0.792 |
| L1 | ON | T+1 | 152 / 313 | 48.56% | 210 | 0.950 |
| R0 | historical | T+2 | 86 / 219 | 39.27% | 256 | 1.268 |
| G0 | OFF | T+2 | 62 / 219 | 28.31% | 161 | 0.798 |
| G0 | ON | T+2 | 67 / 219 | 30.59% | 152 | 0.753 |
| L1 | OFF | T+2 | 67 / 219 | 30.59% | 164 | 0.813 |
| L1 | ON | T+2 | 64 / 219 | 29.22% | 167 | 0.827 |

Although all new arms meet the aggregate load budget, T+2 sensitivity falls by
8.68–10.96 percentage points against R0. This exceeds the accepted −2 pp margin.
Aggregate T+1 improvement therefore does not establish joint success across
horizons, years or departments. No model is promoted.

## Adaptation and climate

With climate ON, L1 detects exactly the same 152 T+1 onsets as G0 but emits six
additional false alerts. For T+2 it detects three fewer onsets and emits 15 more
false alerts. With climate OFF, L1 loses eight T+1 detections while reducing false
alerts by four; it gains five T+2 detections with three more false alerts. These
mixed directions do not demonstrate a stable benefit of department adaptation.
The approved descriptive joint sensitivity/load check against R0 fails in 43 of
the 48 L1 horizon/year/department-or-total strata.

For G0, climate ON versus OFF adds six detections and 25 false alerts in T+1
(+1.92 pp sensitivity), and adds five detections while reducing false alerts by
nine in T+2 (+2.28 pp). This bounded contrast is compatible with useful climate
signal for this representation, without proving a general climate advantage.
It does not rescue the T+2 loss against R0 or the mixed territorial/year controls.
L1's climate contrast is likewise not uniformly beneficial across horizons.

Detailed year/Meta/Tolima results, AP, Brier, precision, exposure and budget flags
are persisted in `metrics.csv` (120 rows); `contrasts.csv` has 96 matched descriptive
contrasts; `comparisons_r0.json` records the fixed R0 margin and load checks.
The supplementary aggregate stratum table is [RESULTS_BY_STRATUM.csv](RESULTS_BY_STRATUM.csv).
No validated transmission-profile field exists in the canonical contract, so
profile results are `NO_EVALUABLE`; no proxy profile was invented.

## Hypothesis dispositions and uncertainty

- **Learning global: NO_EVALUABLE.** Historical M00 already pooled municipalities.
  G0 changes representation and temporal fitting roles; it cannot isolate a benefit
  from introducing pooling. G1 has no compatible identified national source.
- **Local adaptation: NO_RESPALDADA** for this fixed retrospective matrix. It fails
  the predeclared descriptive sensitivity/load controls and does not improve the
  joint outcome consistently. This does not prove that every possible adaptation
  is ineffective; no alternative penalty/support rule was tried after results.
- **G1: NO_EVALUABLE.** No national source was substituted or generated.

Statistical noninferiority is **UNAVAILABLE**, and superiority is **NOT_ESTABLISHED**.
No inferential interval or formal power claim is made from four reused years.
Descriptive compliance in a cell is not a statistical no-inferiority result.
G5 remains `NOT_APPROVED`, champion remains `not_selected`. The bounded phase is
complete with these negative/mixed findings; no Phase 3/4 execution follows.
