# Academic benchmark conclusions

**BENCHMARK_COMPLETED_WITH_LIMITATIONS.** Under the clarified academic contract,
**all four frozen models comply descriptively at pooled T+2, and none complies at
pooled T+1**. No model complies at both horizons or across all annual/territorial
controls. This is a completed retrospective comparison, not scientific or operational
approval. [Results and paired evidence](RESULTS.md), [frozen protocol](protocol.json).

## What the comparison establishes

1. **T+1: greater detection, excessive FAR increment.** CHANNEL detects 94/313
   onsets (30.03%) at 47.49% FAR-excess. R0/G0_OFF/G0_ON/G1_OFF detect 142/146/152/141,
   respectively, but their FAR increments are +14.44/+7.59/+9.82/+9.53 pp. All beat
   CHANNEL and persistence on detected onsets and all fail the fixed +5-pp FAR limit.
   G0_OFF is closest to the limit; that does not authorize adjusting its threshold.
2. **T+2: all four meet the aggregate academic rule.** CHANNEL detects 46/219
   onsets (21.00%) at 55.34% FAR-excess. The models detect 86/62/67/61, with FAR
   increments +4.31/+2.96/+2.19/+1.86 pp. R0 detects the most; G1 has the smallest
   FAR increment. These are distinct trade-offs, not a single dominant model.
3. **The new result does not contradict the BETA dispositions.** At T+2 R0's onset
   false-alert load exceeds one per eligible municipality-year. G0/G1 meet the
   load budget but lose more than two sensitivity points versus R0. Thus none
   meets the complementary pooled BETA criteria, even though all meet the academic
   rules versus CHANNEL/persistence. The comparator, event denominator and acceptance
   rule determine which question a result answers.
4. **FAR-excess does not measure false onset alerts.** CHANNEL's 206 T+2 alerts
   include 46 onsets, 46 continuations and 114 non-excess months. FAR counts only
   the last category; onset false alerts count the latter two. G1's T+2 FAR is
   lower than G0_OFF's despite having more excess false alerts (139 versus 130)
   and more onset false alerts (182 versus 161), because it emits more alerts
   (243 versus 223). A favorable ratio alone cannot establish a lower workload.
5. **Persistence is a structurally weak reference on this population.** It emits
   no alerts because current excess is excluded. Its FAR is undefined. Condition B
   is satisfied by any model detecting an onset; CHANNEL provides the substantive
   anticipatory baseline here. The two rules are not identical: CHANNEL emits
   179 and 206 alerts at T+1/T+2 on the same observations.

All counts and denominators are retained in [metrics](METRICS_BY_STRATUM.csv);
all model-minus-reference deltas are in [paired comparisons](PAIRED_COMPARISONS.csv).

## Stability and historical model comparisons

Every model fails the academic criteria in 2022 at both horizons. At T+2 no model
passes all four annual controls: R0 passes three, G0_OFF one, G0_ON two and G1_OFF
two. R0/G0_ON pass both pooled department controls, while G0_OFF/G1_OFF fail in
Meta. Year-by-department compliance is at most 4/8 for any T+2 model. Aggregate
compliance therefore does not establish reliable transfer across time and territory.

Against R0, G0_OFF/ON add four/ten T+1 detections with 52/27 fewer onset false alerts.
At T+2 they lose 24/19 detections with 95/104 fewer false alerts. G1 loses one T+1
and 25 T+2 detections versus R0; it also fails to improve G0_OFF's detection/false
alert pair at either horizon. The academic benchmark supplies a missing traditional
comparator; it does not reverse the [national-transfer finding](../EXP-BETA01-V2/CONCLUSIONS.md)
or the [BETA V1 limitations](../EXP-BETA/CONCLUSIONS.md).

## Limits and next scientific question

The CHANNEL inequality and P75=0 behavior were clarified before metrics. They differ
from the inspected V1 zone implementation; the academic FAR also differs from V1's
FPR. This is an explicitly authorized contract evaluation with current H5, not an
unannounced repair or identical replay of the old academic software.

Consolidated retrospective data cannot establish availability at the forecast origin.
H5 is not an externally validated outbreak identity. Cohorts exclude excess at T and
missing outcomes/predictors; conclusions apply to those eligible regional observations,
not all municipality-months or all Colombia. Horizons have different cohorts and
onset counts. Previously consumed evaluation years, including 2024 stress and EXP00's
2025 block, do not constitute independent temporal confirmation. No uncertainty
analysis here establishes superiority or statistical noninferiority.

**A new training experiment is not needed to answer this academic question.** The
requested comparison is now available. Before proposing one, the saved paired records
can support a bounded analysis of which onsets and excess/onset errors are shared,
especially the 2022 failures and the T+1 FAR gap. That would be a separate analysis
of existing predictions, not permission to tune on these evaluation years. Any later
claim of generalization would require independent temporal/availability evidence;
changing architecture or optimizing thresholds on this benchmark would not supply it.

The [publication and validation record](README.md) preserves exact identities and
zero training/calibration/threshold-search execution. **G5 remains `NOT_APPROVED`;
`champion: not_selected`.**
