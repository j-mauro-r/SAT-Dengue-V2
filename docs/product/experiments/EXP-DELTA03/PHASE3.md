# Phase 3 — verified manual execution and retrospective results

Mauricio reported successful manual EXP-DELTA03 execution on 2026-11-06.
Artifact verification is complete. The primary scientific result is
**NOT_SUPPORTED**; [CONCLUSIONS.md](CONCLUSIONS.md) owns interpretation and revised
decisions. PLAN_057 task2 is complete; task3 final acceptance additionally requires
independent Final Review and green CI on the documentary head. This record alone
does not assert DWP completion, merge approval, G5 approval or a selected champion.
PLAN_056 remains historically 7/8; its merge does not supply missing CI evidence.

## Executed identity and evidence

| Item | Verified value |
| --- | --- |
| Scientific source commit | `357a0611cbc10743266a25fd2b1c113858d3cb65` |
| Execution identity | `6a43d9ea1e619cfc412b5ce489c6f4ea1598d2f3b7795edcc64f68e256ce4bac` |
| Bundle | `1eb9f597b1b6757bcd58a9a762915c4154203551514b7ad5a9974b596bd36dae` |
| Manifest SHA-256 | `e2a060245dce07f6d1268e9e17ad0c6d01640999b4f84d148c68a73b5cd1f88f` |
| Parent MLflow | `d26b7237b8cf424a86fc901c64cc753e` |
| Native state | `COMPLETE`; 761 files, 579,904,606 bytes |
| Models / calibrators | 108 / 108; no HPO, one thread per model |
| Checkpoints / adjustment attempts | 540 / 216 (108 model, 108 calibrator) |
| Tracking | 109 `FINISHED` runs: one parent, 108 unique children |
| Actual manual scientific activity | 108 fits, 108 calibrations, 109 tracking writes |
| Kedro / duration | 11/11 tasks; 1,789 seconds, both reported by Mauricio |
| Retrospective regime | `RETROSPECTIVE_CONSOLIDATED`; `operational_PIT=false` |
| Governance | G5 `NOT_APPROVED`; champion `not_selected`; no deployment |

Results remain under `tmp/kedro-migration/exp-delta03-runs/<execution>/<bundle>`;
MLflow remains under `tmp/kedro-migration/replay-mlflow`. The final existing delivery
receipt is `tmp/exp-delta03-phase2/delivery/a97da8d293089399a796f1c8b37e4eff24f76cc2ed10797171203507809abf8a.json`,
status `AUTHORIZED_RETROSPECTIVE_COMPLETE`. The native result's activity counters
are a pre-tracking snapshot; the final receipt owns the 109 actual tracking writes.
The approximately 26.7-second MLflow span covers post-publication tracking only and
does not measure pipeline duration. A full console log was not supplied.

The [protocol](protocol.json) and [training contract](training-contract.json) are
the exact final **executed input bytes**, preserved at their run-bound hashes.
Their preparation-time status/zero counters/false automatic authorization flags
describe the freeze, not the later outcome. They cannot grant execution authority.
The separate exact-identity manual-only grant and Mauricio's launch provided that
authority; changing frozen input status after execution would break provenance.
This document owns observed completion and current scientific status.

The freeze retained XGBoost 80 trees/depth2/rate0.05/hist/seed1729/one thread,
regularized intercept calibration penalty1 using calibration only, and selection-
only B=1 false-onset alert per eligible municipality-year, floored to an integer
cap with complete score ties. All 108 selection policies satisfy their caps.
Thresholds were not retuned using evaluation outcomes. B=1 at selection is not
a guaranteed evaluation budget after temporal/geographic transport.

## Verification and preservation

Official task2 gate10 passed once. `SCIENTIFIC_EXECUTION_VERIFICATION.json` in
PLAN_057 `analysis_results/` records every native payload and checkpoint hash,
model bytes/metadata without loading models, calibration/policy/cohort identities,
4,223,973 saved prediction rows across roles/cells, support/count/Brier checks,
national/regional row correspondence, final receipt and read-only SQLite lineage,
parameter/metric projection and exact 109-run inventory. No fitting, recalibration,
model prediction, pipeline invocation or MLflow write occurred during verification.
Checkpoint integrity was inspected; no restart was invoked to demonstrate reuse.

380 prior immutable scientific/source files and 9,208 prior execution files
(9,588 total) retain their baseline hashes. The baseline's SQLite file is expected
to change by authorized additive publication: 518 prior runs plus 109 new runs =
627. All 109 new runs are FINISHED. One historical unrelated failed run remains.
No pre-execution logical SQL snapshot exists; exact preservation of every old SQL
field cannot be proved from a changed database file. This is an evidence limit,
not a claim that all 381 original files remain byte-identical.

The original 14 Phase1 matrix-bundle payloads, native manifest and source contract
also retain their approved hashes, separately verified after execution in
`PHASE1_POST_EXECUTION_PRESERVATION.json`; they are outside the 9,588-file inventory.

`SCIENTIFIC_ANALYSIS.json` independently recomputes counts, AP with whole score
ties, rank-based secondary AUROC, Brier and calibration diagnostics from saved
scores. It checks all 78 paired annual contrasts, their matched role/cohort hashes,
onset gains/losses and absolute/relative differences, plus 38 pooled contrasts.
Comparator totals reuse verified native aggregates and frozen comparator links;
no comparator was regenerated. Pooled AP/AUROC use concatenated observations,
not annual means. Saved uncertainty is reused without new bootstrap draws.
Protected row-level inputs, artifacts and local evidence stay ignored.

## Primary development result: Meta/Tolima, 2020–2022

Horizons remain separate. False-onset alerts and false-excess alerts use different
outcomes; at T+2 an alert can coincide with excess without the defined new onset.
Academic excess-FAR is false-excess alerts / emitted alerts. NE means undefined,
not zero. The frozen learned controls share evaluation keys; their complete role/
capacity equivalence is not asserted merely because policies mention B=1.

| Horizon | Arm | Detected / observed | Alerts | False onset | False excess | Sensitivity | Excess-FAR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | FULL_COMMON | 40/210 | 329 | 289 | 289 | 19.05% | 87.84% |
| T+1 | CHANNEL | 52/210 | 108 | 56 | 56 | 24.76% | 51.85% |
| T+1 | PERSISTENCE | 0/210 | 0 | 0 | 0 | 0.00% | NE |
| T+1 | R0 | 77/210 | 232 | 155 | 155 | 36.67% | 66.81% |
| T+1 | G0_OFF | 91/210 | 228 | 137 | 137 | 43.33% | 60.09% |
| T+1 | G0_ON | 97/210 | 258 | 161 | 161 | 46.19% | 62.40% |
| T+1 | G1 | 88/210 | 233 | 145 | 145 | 41.90% | 62.23% |
| T+2 | FULL_COMMON | 17/158 | 322 | 305 | 289 | 10.76% | 89.75% |
| T+2 | CHANNEL | 25/158 | 123 | 98 | 75 | 15.82% | 60.98% |
| T+2 | PERSISTENCE | 0/158 | 0 | 0 | 0 | 0.00% | NE |
| T+2 | R0 | 63/158 | 265 | 202 | 174 | 39.87% | 65.66% |
| T+2 | G0_OFF | 36/158 | 162 | 126 | 110 | 22.78% | 67.90% |
| T+2 | G0_ON | 43/158 | 170 | 127 | 112 | 27.22% | 65.88% |
| T+2 | G1 | 42/158 | 182 | 140 | 116 | 26.58% | 63.74% |

FULL_COMMON fails academic A (strictly more detections than CHANNEL), passes B
(strictly more than PERSISTENCE), and fails C (excess-FAR increase at most 0.05
absolute) at both horizons. CHANNEL detects 52/210 and 25/158; FULL_COMMON's FAR
increases are 35.99 and 28.78 percentage points. There is no primary acceptance.

Additional FULL_COMMON metrics (signed calibration bias = mean probability minus
observed onset frequency; ECE uses ten fixed probability bins):

| Stratum | Horizon | Rows | Missed onsets | Precision | AP | AUROC secondary | Brier | Calibration bias | ECE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | T+1 | 2200 | 170 | 12.16% | 0.1346 | 0.5759 | 0.0962 | 0.0647 | 0.0692 |
| development | T+2 | 2008 | 141 | 5.28% | 0.0921 | 0.5361 | 0.0762 | 0.0346 | 0.0449 |
| stress2024 | T+1 | 453 | 88 | 38.46% | 0.3604 | 0.6120 | 0.1892 | -0.1334 | 0.1334 |
| stress2024 | T+2 | 414 | 53 | 17.78% | 0.1695 | 0.5519 | 0.1291 | -0.0637 | 0.0655 |

Missed onsets/episodes here refer only to the admitted eligible cohort, not all
real outbreaks. Recorded anticipation is 1 or 2 months by the target definition;
it does not establish available-at-origin operational lead time. Native coverage
1.0 denotes retention of declared view rows, not all calendar months/territory.
Transmission-profile mapping is unbound and that secondary analysis is non-evaluable.

| Stratum | Horizon | Eligible municipality-years | Monitored municipality-years | False onset / eligible year | False onset / monitored year |
| --- | --- | --- | --- | --- | --- |
| development | T+1 | 183.333 | 228.000 | 1.576 | 1.268 |
| development | T+2 | 167.333 | 209.000 | 1.823 | 1.459 |
| stress2024 | T+1 | 37.750 | 76.000 | 0.636 | 0.316 |
| stress2024 | T+2 | 34.500 | 69.667 | 1.072 | 0.531 |

Eligible exposure counts admitted rows /12; monitored exposure comes from the
separate calendar ledger. The evaluation rates exceeding B=1 at development are
observed transport results, not a selection-cap violation.

## Annual FULL_COMMON support

2024 rows below are a separate consumed retrospective stress stratum and never
contribute to development estimates or threshold choice.

| Horizon | Year | Rows | Detected / observed | Alerts | False excess | AP | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 661 | 8/69 | 45 | 37 | 0.1514 | 0.0932 |
| T+1 | 2021 | 846 | 5/52 | 146 | 141 | 0.0571 | 0.0663 |
| T+1 | 2022 | 693 | 27/89 | 138 | 111 | 0.1805 | 0.1357 |
| T+1 | 2024 | 453 | 15/103 | 39 | 24 | 0.3604 | 0.1892 |
| T+2 | 2020 | 588 | 6/51 | 65 | 56 | 0.1090 | 0.0795 |
| T+2 | 2021 | 779 | 4/45 | 161 | 156 | 0.0494 | 0.0570 |
| T+2 | 2022 | 641 | 7/62 | 96 | 77 | 0.1108 | 0.0964 |
| T+2 | 2024 | 414 | 8/61 | 45 | 28 | 0.1695 | 0.1291 |

## Paired development contrasts

Each row compares the left variant with its declared right reference on identical
evaluation keys, horizon and years. Common ablations also match train/calibration/
selection roles; transfer deliberately changes learned geography and transformations.
Both arms use frozen B=1 selection policy; actual evaluation loads can differ.
Δ is left minus right. Relative detection change uses right detections as denominator;
on common support it also equals relative sensitivity change. Intervals are the
saved paired 95% sensitivity differences, in percentage points.

| Horizon | Left variant | Right reference | TP left/right | ΔTP (relative) | Δfalse onset | Δfalse onset / eligible year | 95% Δsensitivity (pp) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | HISTORY | FULL_COMMON | 47/40 | +7 (+17.5%) | -69 | -0.376 | [-4.87, 11.47] |
| T+1 | FULL_MINUS_THERMAL_HUMIDITY | FULL_COMMON | 42/40 | +2 (+5.0%) | -29 | -0.158 | [-3.25, 5.59] |
| T+1 | FULL_MINUS_RAINFALL_HYDROLOGY | FULL_COMMON | 42/40 | +2 (+5.0%) | +3 | +0.016 | [-0.95, 4.27] |
| T+1 | FULL_MINUS_NDVI | FULL_COMMON | 42/40 | +2 (+5.0%) | +19 | +0.104 | [-1.30, 5.31] |
| T+1 | FULL_MINUS_TERRAIN | FULL_COMMON | 42/40 | +2 (+5.0%) | -12 | -0.065 | [-2.17, 5.46] |
| T+1 | FULL_MINUS_DEMOGRAPHY | FULL_COMMON | 27/40 | -13 (-32.5%) | +22 | +0.120 | [-17.58, 5.68] |
| T+1 | FULL_MINUS_LAND_COVER | FULL_COMMON | 43/40 | +3 (+7.5%) | -19 | -0.104 | [0.00, 3.95] |
| T+1 | FULL_PLUS_SURFACE_WATER | WATER_REFERENCE | 19/19 | +0 (+0.0%) | +0 | +0.000 | [0.00, 0.00] |
| T+1 | FULL_ERA5_PRECIPITATION | ERA5_REFERENCE | 42/43 | -1 (-2.3%) | -12 | -0.065 | [-3.07, 1.88] |
| T+1 | TRANSFER_EXCLUDE_META_TOLIMA | TRANSFER_REFERENCE | 65/42 | +23 (+54.8%) | +33 | +0.180 | [-5.38, 24.18] |
| T+2 | HISTORY | FULL_COMMON | 24/17 | +7 (+41.2%) | -116 | -0.693 | [-8.94, 18.01] |
| T+2 | FULL_MINUS_THERMAL_HUMIDITY | FULL_COMMON | 15/17 | -2 (-11.8%) | -6 | -0.036 | [-6.45, 2.52] |
| T+2 | FULL_MINUS_RAINFALL_HYDROLOGY | FULL_COMMON | 25/17 | +8 (+47.1%) | +71 | +0.424 | [0.00, 14.91] |
| T+2 | FULL_MINUS_NDVI | FULL_COMMON | 22/17 | +5 (+29.4%) | +20 | +0.120 | [0.00, 10.67] |
| T+2 | FULL_MINUS_TERRAIN | FULL_COMMON | 17/17 | +0 (+0.0%) | +9 | +0.054 | [-3.82, 3.70] |
| T+2 | FULL_MINUS_DEMOGRAPHY | FULL_COMMON | 31/17 | +14 (+82.4%) | +181 | +1.082 | [1.74, 16.55] |
| T+2 | FULL_MINUS_LAND_COVER | FULL_COMMON | 19/17 | +2 (+11.8%) | +9 | +0.054 | [-2.70, 6.67] |
| T+2 | FULL_PLUS_SURFACE_WATER | WATER_REFERENCE | 12/12 | +0 (+0.0%) | +0 | +0.000 | [0.00, 0.00] |
| T+2 | FULL_ERA5_PRECIPITATION | ERA5_REFERENCE | 13/16 | -3 (-18.8%) | -55 | -0.329 | [-6.17, 0.00] |
| T+2 | TRANSFER_EXCLUDE_META_TOLIMA | TRANSFER_REFERENCE | 26/20 | +6 (+30.0%) | -115 | -0.687 | [-17.78, 26.88] |

Native `comparisons.json` and local `SCIENTIFIC_ANALYSIS.json` retain all 78 annual
matched-role contrasts, per-metric absolute/relative differences, paired gained/
lost/shared/missed onsets and all 38 stratum contrasts. The original 20 development
interval sets are evaluable: 76 municipalities, three episode-connected temporal
blocks, 1,000 valid paired draws per metric. All 18 stress interval sets are
`NO_EVALUABLE_INSUFFICIENT_CLUSTER_SUPPORT` (one block). No IID replacement,
new resampling, multiplicity correction or formal superiority claim is introduced.

Water uses its genuine paired WATER_REFERENCE cohort: evaluation rows T+1
646/831/124 and T+2 573/764/124 in 2020/2021/2022. The 124-row 2022 views use
genuine lagged 2021 observations; no later water values are filled. Four water2024
descriptors are explicitly unavailable, outside the 108 executable cells.

## Geography and separate 2024 stress

These FULL_COMMON views use saved predictions and the same frozen regional-selected
policy. National includes Meta/Tolima and must never be added to regional counts.
National frozen learned comparator scores are unavailable; no national comparison
with R0/G0/G1 is invented. National evaluation is secondary, not the controlling
regional academic result or spatial holdout (national training includes regional history).

| Stratum | Horizon | Scope | Rows | Detected / observed | Sensitivity | Precision | Excess-FAR | AP | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| development | T+1 | Meta | 809 | 26/99 | 26.26% | 18.57% | 81.43% | 0.2102 | 0.1076 |
| development | T+1 | Tolima | 1391 | 14/111 | 12.61% | 7.41% | 92.59% | 0.0898 | 0.0896 |
| development | T+1 | national | 33341 | 238/2834 | 8.40% | 20.53% | 79.47% | 0.1364 | 0.0795 |
| development | T+2 | Meta | 739 | 6/69 | 8.70% | 4.08% | 88.44% | 0.1314 | 0.0851 |
| development | T+2 | Tolima | 1269 | 11/89 | 12.36% | 6.29% | 90.86% | 0.0728 | 0.0710 |
| development | T+2 | national | 30513 | 117/1936 | 6.04% | 8.03% | 85.72% | 0.0888 | 0.0606 |
| stress2024 | T+1 | Meta | 215 | 7/47 | 14.89% | 35.00% | 65.00% | 0.3598 | 0.1804 |
| stress2024 | T+1 | Tolima | 238 | 8/56 | 14.29% | 42.11% | 57.89% | 0.3701 | 0.1971 |
| stress2024 | T+1 | national | 6957 | 153/1461 | 10.47% | 40.37% | 59.63% | 0.3396 | 0.1790 |
| stress2024 | T+2 | Meta | 204 | 3/27 | 11.11% | 10.71% | 78.57% | 0.1438 | 0.1173 |
| stress2024 | T+2 | Tolima | 210 | 5/34 | 14.71% | 29.41% | 35.29% | 0.2213 | 0.1405 |
| stress2024 | T+2 | national | 6283 | 47/818 | 5.75% | 16.26% | 62.28% | 0.1667 | 0.1159 |

In regional stress2024 CHANNEL detects 42/103 (T+1) and 21/61 (T+2), versus
FULL_COMMON 15/103 and 8/61. CHANNEL FAR is 40.85% /46.99%, versus 61.54% /62.22%:
increases 20.69 /15.23 pp. Academic A/C also fail in stress; its one-year support
cannot repair the negative development result. No stress CI is claimed.

## Documentary acceptance boundary

The existing PR79 remains open for Mauricio's merge decision. No model is promoted,
no G5/deployment authority is granted, and 2025 remains excluded. PLAN_057 Final
Review binds the complete PR diff, local evidence and the eventual final-head CI;
its ledger/receipt, rather than this narrative, owns final task acceptance.
No full local suite, synthetic E2E or previous task is repeated for this analysis.
