# EXP04 technical disposition

Scientific status: **NOT EXECUTED / NOT EVALUATED**.

Implementation status: **`EXP04_SCIENTIFIC_RUNNER_IMPLEMENTED_NOT_EXECUTED`**. The scientific policy runner, preflight, bound authorization and read-only bundle validator are implemented. This delivery did not execute EXP04, select a scientific policy or grant scientific approval.

H1, H1a, H1b and H1c: `NOT_EVALUATED`. The generated functional exercise verifies implementation behavior and output structure only; its synthetic metrics are not scientific evidence. No scientific EXP04 evaluation, private-source training, M00 regeneration or MLflow write occurred.

M00 of EXP03.1 remains the mandatory scientific reference. The existing [baseline manifest](BASELINE_MANIFEST.json) records `M00-REPLAY-v1` as `VERIFIED_OBSERVABLE_REPLAY`, with the original and replay identities preserved. The replay supplies fitted predictor/preparer/calibrator states and raw scores; absent original intermediate states remain `NOT_COMPARABLE`. Seed/configuration availability alone does not prove fitted-state equivalence. This correction reuses that evidence without replaying M00 or changing historical artifacts.

The approved scope uses consolidated retrospective SIVIGILA data and the approved symptom-onset date as canonical. Reconstructing actual historical notification availability and consolidation delays belongs to EXP06 and does not block EXP04. This assumption does not establish real-time historical availability. Full-horizon chronological separation, out-of-sample predictions and calibration → selection → freeze → evaluation order still apply.

The existing temporal audit accredits retrospective coverage for 12/24/36-month windows, which are `GENERATABLE`, not already generated or scientifically evaluated. Per cut and family, T+1 onset now requires 8/20/32 generated or replaced origins for 12/24/36 months; T+2 onset and the separate excess control each require 9/21/33. Calibration ends in May. Selection uses July–November targets for T+1 and August–November for T+2, with June first issuance and December first evaluation issuance. Valid original calibration scores can be reused only in February–May for T+1 and March–May for T+2, after exact identity/support/precision/cutoff checks. New row and class counts are calculated during preparation, not inferred from the original support arrays. These overlapping windows must not be summed. Missing scores require historical refits; applying a predictor to months it already used for training is invalid. The [implementation inventory](IMPLEMENTATION.md#oof-inventory-and-reuse) and the manifest identify every cut, family, horizon and objective.

A4 remains outside the implemented generator: `NOT_EVALUABLE` with `BLOCKED_EXPANDING_OOF_ORIGIN_UNDEFINED`. The current contract does not determine its first valid OOF origin. No origin is inferred and no further audit is initiated. C2 remains conditional on two predeclared supported chronological blocks; otherwise it is `NOT_EVALUABLE`, without moving any dates. Five focused synthetic cases supply technical evidence only; real data admission, native historical refits and the experiment itself have not run.

The original M00 monitored exposure remains intact. EXP04 common exposure uses identical eligible observable municipality-month keys/12 across compared arms; the two rates are named separately. A cohort, raw-score, label or denominator mismatch makes a contrast `NOT_EVALUABLE` rather than an apparent calibration improvement.

Development remains 2020, 2021 and 2022; 2024 remains retrospective stress after policy freeze and cannot select a policy; 2025 remains `NOT_EVALUABLE`. GAM, LightGBM and XGBoost remain comparators. T+1 retains one objective; T+2 retains primary onset and a separate excess control. The design's existing pre-execution scientific requirements remain pending; no policy was selected or promoted. See [implementation and execution instructions](IMPLEMENTATION.md) for capabilities and remaining dependencies.

G5: NOT_APPROVED

champion: not_selected
