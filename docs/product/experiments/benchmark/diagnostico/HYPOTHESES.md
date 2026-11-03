# Prioritized improvement hypotheses

These are hypotheses, not implemented remedies. The [diagnosis](ANALYSIS.md) and
[diagnostic summary](DIAGNOSTIC_SUMMARY.csv) supply the evidence. Only hypothesis 1
is recommended as the next experiment; none authorizes execution or changes G5.

| Priority | Hypothesis | Evidence and counterevidence | Potential / testability / data / complexity |
| --- | --- | --- | --- |
| 1 | A decision policy selected explicitly for the academic comparator/FAR objective may produce a more relevant detection–error trade-off than the frozen BETA load selector. | The current selector constrains onset FP/eligible-year, not excess FAR relative to CHANNEL. G0_OFF gains 71 channel-missed T+1 detections but adds 118 channel-avoided errors; net +52 TP/+94 FP. However, 59 TP coexist with 85 FP near the saved threshold; previous EXP04/BETA03 policies lost detection. No feasible improving policy has been demonstrated. | Direct documented objective mismatch; possible improvement, unknown magnitude. Testable with frozen scores and chronological roles. Models/policies exist, but complete G0 selection-score availability is not established by aggregate counts; recovery would need separate authorization. Low algorithmic complexity, substantial validation constraint. |
| 2 | Changing probability scale and conditional event composition contribute to decision instability across years/territories. | G0_OFF 2022 mean risk exceeds observed onset frequency by 11.19/7.81 pp, while R0 underpredicts; Meta/Tolima FAR differs despite similar or reversed FPR ordering. Yet G0_OFF selection-to-evaluation onset false-discovery improves in 2022, and calibration alone previously failed. | Could identify where transport fails. Existing evaluation predictions and H5 context are sufficient for description, not causal separation or confirmation. Moderate diagnostic complexity; independent temporal evidence is missing. |
| 3 | Low-count H5 boundary observations have limited information for distinguishing new onsets from non-events, affecting both missed and unnecessary alerts. | Among G0-only T+1 alerts, 107/118 FP and 62/71 TP lie within one case of target P75; both groups have median count/P75 of two. Shared model errors and missed onsets support limited discriminative information, but similarity does not prove label noise or lack of all useful features. | Could improve interpretation or reveal missing signal without assuming another architecture. Canonical counts/labels exist; independent episode adjudication does not. Moderate-to-high evidence acquisition complexity; predictive benefit unknown. |

## Minimal falsifiable checks

**1 — Recommended experiment.** Compare exactly one predeclared academic-aligned
selector against the existing BETA selector using the same frozen G0_OFF scores,
H5, cohorts and calibrator. Select only on earlier data; assess both horizons and
annual/department guardrails on an untouched later block. Document infeasibility
rather than relaxing strict detection conditions, FAR margin or missing-denominator
rules. Verify earlier selection scores first; any frozen-model inference to recover
them requires separate authorization. Do not treat consumed 2022/2024/2025 as an
independent confirmation set. No expected gain or alternative threshold has been
estimated in this diagnosis. The claim is weakened if no feasible earlier policy
exists, gains disappear out of time, or one horizon/territory pays in missed onsets.

**2 — Alternative, not the next selected experiment.** A frozen-procedure temporal
transport study would compare predeclared score reliability and conditional outcome
rates in chronological blocks, with fixed common-support descriptors and no fitting.
It must distinguish sampling/composition changes from changes in the score–outcome
relationship; separately fitted annual models alone cannot isolate either. A causal
claim would require stronger design than this descriptive comparison. Lack of an
independent later block limits any result to exploration.

**3 — Alternative, not the next selected experiment.** A blinded external review of
a prespecified, outcome-balanced sample of near-boundary and away-from-boundary
episodes could assess whether H5 transitions correspond to independently adjudicated
epidemiological onsets. Preserve H5 labels and all original predictions; do not select
only model errors or change thresholds after inspection. Without an independent event
reference, this hypothesis cannot be resolved by reanalyzing the same H5 outcomes.

The existing evidence does not justify another model-family search, automatic
recalibration, municipal exclusion, a second-stage error classifier, or threshold
tuning on this evaluation set. High probability, shared errors and boundary proximity
are observations, not proven mechanisms. G5 `NOT_APPROVED`; `champion: not_selected`.
