# EXP03 — Selective history, channel and climate ablation

Frozen design; real execution requires independent authorization. Labels remain
conditioned on EXP01's five-year channel definition until prioritized experiment 2
(label sensitivity 5/7/9) is implemented and separately authorized. EXP01 is
prioritized experiment 1; EXP03 is prioritized experiment 3.

## Authority and normalized matrix

Mauricio explicitly authorized ten unique predictor sets and eleven contrasts.
`baseline_plus_complete_channel` is the canonical base+thresholds+recent-state+SIR
model. It also fulfills the semantic role `full_without_climate`; that role is
contrast metadata, never another variant, run, fit, calibration or artifact.
The climate-removal contrast is `full − baseline_plus_complete_channel`.
Duplicate predictor sets fail validation. Every variant retains municipality,
epidemiological history and season. No model or budget is selected from stress.

| Variant | Groups | Variables |
|---|---|---:|
| `baseline_history_season` | history, season, context | 12 |
| `baseline_plus_climate` | history, season, context, climate | 27 |
| `baseline_plus_complete_channel` | history, season, context, target_thresholds, recent_channel_state, sir | 19 |
| `baseline_plus_recent_channel_state` | history, season, context, recent_channel_state | 16 |
| `baseline_plus_sir` | history, season, context, sir | 13 |
| `baseline_plus_target_thresholds` | history, season, context, target_thresholds | 14 |
| `full` | history, season, context, target_thresholds, recent_channel_state, sir, climate | 34 |
| `full_without_recent_channel_state` | history, season, context, target_thresholds, sir, climate | 30 |
| `full_without_sir` | history, season, context, target_thresholds, recent_channel_state, climate | 33 |
| `full_without_target_thresholds` | history, season, context, recent_channel_state, sir, climate | 32 |

## Eleven paired contrasts

| Contrast | Left minus right | Semantic reuse |
|---|---|---|
| `added_target_thresholds` | `baseline_plus_target_thresholds` − `baseline_history_season` | none |
| `added_recent_channel_state` | `baseline_plus_recent_channel_state` − `baseline_history_season` | none |
| `added_sir` | `baseline_plus_sir` − `baseline_history_season` | none |
| `added_climate` | `baseline_plus_climate` − `baseline_history_season` | none |
| `added_complete_channel` | `baseline_plus_complete_channel` − `baseline_history_season` | none |
| `added_full` | `full` − `baseline_history_season` | none |
| `full_without_target_thresholds` | `full` − `full_without_target_thresholds` | none |
| `full_without_recent_channel_state` | `full` − `full_without_recent_channel_state` | none |
| `full_without_sir` | `full` − `full_without_sir` | none |
| `full_without_climate` | `full` − `baseline_plus_complete_channel` | {'right': 'full_without_climate'} |
| `removed_complete_channel` | `full` − `baseline_plus_climate` | none |

## Predictor inventory

Exact ordered groups, memberships and formulas are executable in
[protocol.json](protocol.json) and [the frozen matrix](ablation-matrix.frozen.yml).
The verified monthly panel is the raw source. Current and lagged channel values
are reconstructed, never taken from supplied legacy labels or percentiles.

| Predictor | Group | Formula / source transformation | Latest availability | Leakage limitation |
|---|---|---|---|---|
| `channel_excess_lag_1` | recent_channel_state | 1 if reconstructed same-month count > prior-five-year type-7 P75; current T or exact calendar T-1; unknown stays missing | T | future counts forbidden; exact historical calendar lookup only |
| `channel_excess_t` | recent_channel_state | 1 if reconstructed same-month count > prior-five-year type-7 P75; current T or exact calendar T-1; unknown stays missing | T | future counts forbidden; exact historical calendar lookup only |
| `channel_target_p25` | target_thresholds | Type-7 P25 of five same-calendar-month municipal dengue counts in years preceding target year; all source months <= T | T | future counts forbidden; exact historical calendar lookup only |
| `channel_target_p75` | target_thresholds | Type-7 P75 of five same-calendar-month municipal dengue counts in years preceding target year; all source months <= T | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_cambio_1m` | history | {"formula": "T minus T-1", "negative_values": "valid", "operation": "difference", "source": "dengue_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_grave_notifications_count` | history | Observed municipal raw value at T | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_lag_1` | history | {"missing": "preserve", "months": 1, "operation": "lag", "source": "dengue_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_lag_2` | history | {"missing": "preserve", "months": 2, "operation": "lag", "source": "dengue_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_lag_3` | history | {"missing": "preserve", "months": 3, "operation": "lag", "source": "dengue_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_media_3m` | history | {"centered": false, "min_observations": 3, "offsets_months": [0, 1, 2], "operation": "mean", "source": "dengue_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `dengue_notifications_count` | history | Observed municipal raw value at T | T | future counts forbidden; exact historical calendar lookup only |
| `dewpoint_mean_c_month_mean` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `escorrentia_lag_1` | climate | {"missing": "preserve", "months": 1, "operation": "lag", "source": "surface_runoff_mm_month_sum"} | T | retrospective consolidated climate availability UNPROVEN |
| `grave_lag_1` | history | {"missing": "preserve", "months": 1, "operation": "lag", "source": "dengue_grave_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `grave_lag_2` | history | {"missing": "preserve", "months": 2, "operation": "lag", "source": "dengue_grave_notifications_count"} | T | future counts forbidden; exact historical calendar lookup only |
| `lluvia_lag_1` | climate | {"missing": "preserve", "months": 1, "operation": "lag", "source": "rain_mm_month_sum"} | T | retrospective consolidated climate availability UNPROVEN |
| `lluvia_lag_2` | climate | {"missing": "preserve", "months": 2, "operation": "lag", "source": "rain_mm_month_sum"} | T | retrospective consolidated climate availability UNPROVEN |
| `mes_cos` | season | {"formula": "cos(2*pi*(month-1)/12)", "operation": "cyclic_calendar"} | T | future counts forbidden; exact historical calendar lookup only |
| `mes_sin` | season | {"formula": "sin(2*pi*(month-1)/12)", "operation": "cyclic_calendar"} | T | future counts forbidden; exact historical calendar lookup only |
| `municipality_code_feature` | context | Public DANE municipality code; categorical context; constant in every variant | T | future counts forbidden; exact historical calendar lookup only |
| `rain_mm_month_sum` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `rocio_lag_1` | climate | {"missing": "preserve", "months": 1, "operation": "lag", "source": "dewpoint_mean_c_month_mean"} | T | retrospective consolidated climate availability UNPROVEN |
| `sir_notification_ratio_t` | sir | Dengue notifications at T / mean of five prior same-calendar-month municipal notification counts; 0/0=0; positive/0 unavailable; any missing reference unavailable | T | future counts forbidden; exact historical calendar lookup only |
| `soil_water_l1_month_mean` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `solar_radiation_mj_m2_month_sum` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `surface_runoff_mm_month_sum` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `temp_mean_c_month_mean` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `temperatura_lag_1` | climate | {"missing": "preserve", "months": 1, "operation": "lag", "source": "temp_mean_c_month_mean"} | T | retrospective consolidated climate availability UNPROVEN |
| `temperatura_lag_2` | climate | {"missing": "preserve", "months": 2, "operation": "lag", "source": "temp_mean_c_month_mean"} | T | retrospective consolidated climate availability UNPROVEN |
| `total_evaporation_mm_month_sum_ecmwf` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `wind_u_ms_month_mean` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `wind_v_ms_month_mean` | climate | Observed municipal raw value at T | T | retrospective consolidated climate availability UNPROVEN |
| `zona_canal_lag_1` | recent_channel_state | {"missing": "preserve", "months": 1, "operation": "lag", "source": "zona_canal_t"} | T | future counts forbidden; exact historical calendar lookup only |
| `zona_canal_t` | recent_channel_state | Reconstruct municipal zone at T from dengue notifications C(T) and prior-five-same-month type-7 P25/P50/P75: EXITO if C<P25, SEGURIDAD if C<=P50, ALERTA if C<=P75, else EXCESO; missing current/history -> missing. P50 is the existing current-zone contract, not a new target-month predictor. | T | future counts forbidden; exact historical calendar lookup only |

Thresholds are type-7 P25/P75 from the five previous years of the target calendar
month. The target's observed cases, zone and label never enter X. P50 is absent.
Exact calendar lags never bridge missing months. Recent state includes current
and lagged zones and binary excess; duration is omitted because no existing
frozen reproducible duration predictor exists. Current excess is constant zero
within the operationally eligible cohort, and is retained as a controlled group.

SIR is explicitly adapted to V2 as an observed/expected **notification-count
ratio**, not census-population-standardized incidence. Its numerator is the
municipality's dengue count at T; its denominator is the mean of its five prior
same-calendar-month counts. The population reference is the same municipality's
historical notification baseline. No V1 population formula is copied. 0/0=0;
positive/0 and missing historical reference produce missingness, with exclusion
counts. Small denominators are not clipped; reporting/demographic changes can
confound the proxy. It must not be interpreted as population relative risk.

The fifteen existing climate variables use their frozen current/lag definitions.
For current-month aggregates, nominal availability is close of T; the historical
operational availability date is UNPROVEN. Therefore results can establish only
retrospective climate value. No assertion of real-time availability is made.

## Labels and temporal evaluation

EXP01's immutable labels are reused: T+1 requires Y(T)=0,Y(T+1)=1; exact T+2
requires Y(T+1)=0,Y(T+2)=1, while eligibility uses only Y(T)=0. The T+1 observation
is never a T+2 predictor. 2025 input is rejected by pure preparation and is
excluded by authorized raw admission before scientific typing.

| Cut | Train targets | Calibration targets | Selection targets | Evaluation targets |
|---|---|---|---|---|
| development_2020 | 2012-01 through 2018-12 | 2019-01 through 2019-06 | 2019-07 through 2019-12 | 2020-01 through 2020-12 |
| development_2021 | 2012-01 through 2019-12 | 2020-01 through 2020-06 | 2020-07 through 2020-12 | 2021-01 through 2021-12 |
| development_2022 | 2012-01 through 2020-12 | 2021-01 through 2021-06 | 2021-07 through 2021-12 | 2022-01 through 2022-12 |
| stress_2024 | 2012-01 through 2022-12 | 2023-01 through 2023-06 | 2023-07 through 2023-12 | 2024-01 through 2024-12 |

All roles use the existing horizon embargo: evaluation origins cannot precede
the previous role's last target. Cuts 2020, 2021 and 2022 supply unique development
OOF observations; 2024 is a separate retrospective stress assessment. Each OOF
prediction retains its source cut in the native audit, which is never uploaded.
All models/calibrators are fitted on strictly earlier roles.

Each variant is refitted once on the common all-predictor/evaluable cohort,
determined before X projection. Eleven contrasts reuse scores/canonical cell IDs.
Every integer selection false-alert cap is evaluated with whole score ties and
the existing deterministic onset-threshold rule. Pooled development contrasts
use the intersection of integer budgets supported by every development cut;
no budget is optimized on pooled OOF outcomes or on 2024.

Uncertainty uses 1000 paired municipality×calendar-year cluster draws, seed42,
percentile95 intervals. Municipality and year multiplicities weight paired onset
counts identically. Development requires at least three OOF years and two
municipalities, with onsets represented in all three years and at least two
municipalities; absence of this support blocks before reservation or fitting.
The count of valid bootstrap replicates is reported; zero-denominator resamples
are excluded. Per-cut one-year intervals remain unavailable; pooled development
intervals address this limitation. No IID fallback exists. Source-free preflight
verifies declared temporal support, not private-data readiness. After authorization,
common data support/classes are checked before any reservation, tracking or fit.

## Metrics, coverage and decisions

Each contrast retains separate identity, references, paired metrics and interval.
Variant metrics include AP, Brier, secondary AUROC, reliability bins/ECE and
assessment-only logistic calibration slope/intercept where estimable. Episode
metrics include sensitivity/precision, detected/missed episodes, false-alert count,
ratio, exposure-normalized burden and useful lead. Native strata include
municipality, department, target year and transmission profile. Transmission
profile uses the available three-month mean (low<=1, medium<=10, high>10);
it is a descriptive origin-time stratum, not a selected model feature.

Coverage is a separate secondary analysis of variant-specific raw availability:
rows, municipalities, months, department/profile summaries and missing reasons.
It does not change primary paired rows or trigger additional fits. A reduced
variant can recover coverage even when the primary common cohort excludes it.

Added-value flags require nonnegative sensitivity change in every development cut
and positive change in at least one. Removal candidates require no loss of detected
onsets in any development cut, no increase in realized false alerts, Brier or ECE,
and fewer variables. Zero allowed Brier/ECE increase is a conservative predeclared
interpretation of no material deterioration, not an equivalence margin. Every
candidate remains descriptive and requires prospective confirmation. No automatic
variant, family or budget selection, G5 approval or champion selection occurs.

## Execution and tracking

The exact maximum is dynamically derived: 10 variants × 3 families × 2 horizons ×
4 windows = **240** model/preparer/calibrator fits and child runs, plus one parent.
Contrasts add zero fits/runs/calibrations. Each child has a canonical cell hash;
contrast references resolve those hashes to the same existing child runs.

Authorization precedes file reads. File/manifest identities, tracking-root binding,
non-overlapping roots, symlink rejection, exclusive reservation, atomic publication
and no-overwrite behavior remain enforced. A new scientific identity invalidates
all former approvals, reservations, bundles and protocol pins; none are migrated.
Only closed aggregate frontiers/contrasts are uploaded once on the parent. The
native audit and municipality strata stay local; no row predictions, municipality
dimensions, raw data or absolute paths enter MLflow artifacts.
