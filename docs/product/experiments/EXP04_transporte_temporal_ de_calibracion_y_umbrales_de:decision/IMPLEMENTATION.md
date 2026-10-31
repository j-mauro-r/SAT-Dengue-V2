# EXP04 implementation

The [scientific design](DESING.md) owns intent. The [technical protocol](protocol.json) records the independent implementation boundary. It is not a frozen scientific execution protocol: M00 reconstruction and several scientific inputs remain unresolved. `G5: NOT_APPROVED`; `champion: not_selected`.

M00 of EXP03.1 is mandatory, including its exact V09 predictors, fixed family parameters, H5 labels and paired twelve-state cohort. No M01/M02 feature enters EXP04. Development is retrospective 2020–2022; 2024 is retrospective stress after policy freeze; 2025 is `NOT_EVALUABLE`.

The user's exposure decision preserves the original M00 monitored-month denominator for historical reproduction. EXP04's primary rate uses the same eligible observable municipality-month keys/12 for every compared arm. These rates are named and reported separately. Incompatible support or exposure makes a contrast `NOT_EVALUABLE`.

Independent components are implemented incrementally under local PLAN_052. Exactly five substantive controls cover design, baseline integrity, chronology, functional execution and reproducibility. Functional/generated results cannot validate H1/H1a/H1b/H1c. Scientific execution remains disabled while its prerequisites are unresolved.

## Reference reconstruction

`exp04_baseline.audit_baseline` checks the exact EXP03.1 bundle and manifest hashes, canonical M00 predictor order, configuration, seed and temporal roles. It opens existing result artifacts read-only and never reads private source datasets. The bundle contains final calibrated evaluation probabilities and alerts, but no original fitted predictor/preparer, calibrator coefficients, or raw calibration/selection/evaluation scores. The EXP03.1 runner fitted these states locally without persisting them. M00's reuse decision is `refitted`; EXP03 native models cannot therefore be silently substituted.

Reconstruction equivalence is **not verifiable from the available artifacts**. The diagnostic returns `BLOCKED_BASELINE` with the exact missing dependencies, original identity and a null reconstruction identity. Configuration/seed determinism alone cannot prove equality with an unsaved fitted state; inverse calibration is not used. No reconstruction fit was executed. Recovery requires the original fitted/raw-score artifacts and temporal/cohort provenance, or a separately authorized reconstruction protocol with verifiable correspondence. The `real_private_reads` discrepancy (8 versus 1) remains unresolved.

`paired_support` rejects changed truth or differing eligible keys with `NOT_EVALUABLE` and reports intersection support. `common_exposure` counts the supplied complete eligible observable municipality-month cohort/12, independent of alerts and scores. No fixed 76-municipality denominator is used. The historical M00 denominator is retained separately and never used to establish an EXP04 primary improvement.

## Independent temporal policies

`exp04.temporal_roles` requires explicit forecast/target/maturity dates and the latest training-label availability cutoff. It checks full T+1/T+2 month offsets, genuinely out-of-sample chronology, disjoint target-event roles, mature calibration/selection labels, and decision freeze before every evaluation issue date. Stress 2024 cannot fit/select and 2025 is rejected. Supplied provenance must ultimately be verified against original artifacts; passing date arithmetic does not authenticate missing M00 state.

`calibration_window` selects contiguous mature 12/24/36-month or expanding histories with observed positive/negative support. Gaps return `NOT_EVALUABLE`; no future months are borrowed. `fit_calibrator` reuses the original fixed sigmoid implementation; isotonic uses installed sklearn and requires an explicitly supplied minimum class support, otherwise `NOT_EVALUABLE`. Identity calibration is diagnostic-only for probability scores. No fallback is fitted automatically.

`threshold_policy` implements C0's existing whole-tie selector and C1 on common exposure; they coincide when all inputs match, which is an expected control rather than a claimed improvement. C2 requires at least two noninterleaved chronological blocks with both classes and enforces the budget in each block before maximizing joint detections. Null is the no-alert extreme. A0 historical replay uses the saved original threshold without reselection. These onset selectors reject excess-control use.

`evaluate_frozen` applies supplied state and threshold without fitting, retains full probabilities, uses common exposure for the primary rate and reports historical exposure/rate separately. It reuses existing AP/Brier/ECE/reliability and classification metrics, reports municipal macro sensitivity and false alerts by class, and keeps uncertainty `UNAVAILABLE` without an approved resampling protocol. Excess metrics have their own positives and no onset-budget criterion. Undefined scientific settings remain explicit; no confirmatory H1 classification is generated.
