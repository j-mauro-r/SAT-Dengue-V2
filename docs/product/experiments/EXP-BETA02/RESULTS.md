# EXP-BETA02 — retrospective count forecast results

Date: 2026-11-02. Status: **COMPLETED_WITH_LIMITATIONS** for the bounded Phase 3
implementation and local execution. Human review and integration remain separate.

## Identified execution and comparability

The [protocol](protocol.json) was frozen in commit `61bd1e3` before any fitting.
The actual six-node Kedro run used clean source commit `037ad01`, tracking disabled,
with no historical predictor refits or canonical rebuild. All 16 NB2 fits
converged (125–241 iterations), dispersion 0.5515–0.9664, with no boundary fits.
The unchanged protocol, model family, features and policy were not retuned after
results. No neural model was trained.

Native publication:
`tmp/kedro-migration/exp-beta02-runs/1f0fffc450476c587ed109cb16d552933f832bd8a58d441a5265ee77f12e1468/`.
Its manifest identifies 27 payloads plus the manifest itself, including 16 native
JSON models, 10,150 count forecasts, 18,571 T+1 onset/reference rows, 48 count
strata and 84 onset strata. Inputs, code/runtime and protocol identities are bound
to the publication. Native payloads remain private/local and ignored by Git.

All eight R0 horizon/year cohorts match complete origin keys, target periods and
onset truths; no intersection was substituted. T+1 has 2,653 rows and 313 onsets;
T+2 has 2,422 rows and 219 known retrospective onset labels. Known T+2 labels
support cohort verification, not an evaluable joint onset probability from NB2.
Meta/Tolima and 2020/2021/2022/2024 are unchanged. No 2025 outcome is used.
2024 remains consumed retrospective stress; none of these years is independent
confirmation. Count forecasts are conditional on non-excess observed at T.

## Onset detection: primary R0 comparison

These pooled rates sum events and eligible target-month exposure across the four
fixed years. They are not unweighted averages of annual metrics. Exposure is
221.0833 eligible municipality-years. Original R0 alerts are reused unchanged.

| T+1 arm | Detected / onsets | Sensitivity | False alerts | FA / municipality-year | Brier |
| --- | ---: | ---: | ---: | ---: | ---: |
| R0 | 142 / 313 | 45.37% | 231 | 1.044855 | 0.109712 |
| NB OFF | 135 / 313 | 43.13% | 212 | 0.958914 | 0.095385 |
| NB ON | 152 / 313 | 48.56% | 222 | 1.004146 | 0.091055 |

NB OFF loses seven detections, a **-2.2364 percentage-point** sensitivity change
against R0, exceeding the approved -2 pp margin despite meeting the pooled load
budget. NB ON gains ten detections (+3.1949 pp), but **1.004146 exceeds 1** false
alert/municipality-year. Rounding this to 1.00 would conceal a budget failure.
Neither fixed setting meets the pooled joint criteria. Annual/department controls
fail in **19 of 24** NB T+1 year/Meta/Tolima/all strata. A lower Brier score alone
does not establish a better alert procedure.

**T+2 onset: NO_EVALUABLE.** Both count marginals and their exceedance probabilities
are available, but they do not identify the joint non-excess-to-excess trajectory.
No observed T+1 future state, independence product or excess-probability relabeling
was used to create a T+2 onset metric. Its onset scores and alerts remain missing.

Detailed annual/department sensitivity, detections, exposure, precision, AP,
Brier and load flags are in [ONSET_BY_STRATUM.csv](ONSET_BY_STRATUM.csv). R0 is the
primary reference; preserved Beta01 G0/L1 rows in that table are secondary context.
For example, Beta01 G0 ON also detects 152 T+1 onsets but emits 204 false alerts,
versus NB ON's 222. No mandatory G0/L1 reference or winner selection was imposed.
Training/calibration histories differ between procedures, preventing isolated
causal attribution of these differences to count modeling alone.

## Count accuracy and predictive distribution: secondary outcomes

Metrics are recomputed from pooled forecast rows, separately from alert utility.
Intervals use the NB2 discrete 5th/95th percentiles conditional on fitted parameters.

| Horizon | Climate | MAE | RMSE | Mean negative log score | 90% coverage | Mean interval width |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| T+1 | OFF | 4.3020 | 16.2728 | 1.9312 | 97.32% | 23.2107 |
| T+1 | ON | 3.8821 | 14.5866 | 1.9114 | 97.36% | 21.9932 |
| T+2 | OFF | 5.4989 | 18.8961 | 2.0728 | 97.65% | 30.7816 |
| T+2 | ON | 5.1251 | 20.8550 | 2.0444 | 97.81% | 28.8476 |

Climate ON reduces MAE and log score in these pooled comparisons; its T+2 RMSE
is worse. Coverage exceeds the nominal 90%, alongside wide intervals: coverage
alone must not be read as sharp or completely calibrated uncertainty. These
intervals exclude parameter and source-availability uncertainty. No R0 count
distribution exists, so this table does not show improved count accuracy versus
R0. [COUNT_BY_STRATUM.csv](COUNT_BY_STRATUM.csv) preserves all year/department rows.

## Verification, limitations and disposition

An actual second complete graph evaluation in memory reproduced **all 28 files
byte for byte**, without overwriting the publication. There were 16 unique fits
in the publication and 16 additional reproduction fits: **32 real NB2 fits**
across the two executions. The separate native-state replay performed zero fits,
verified all 10,150 forecasts and H5 probabilities/quantiles (maximum mean replay
round-trip discrepancy 5.7e-14), and independently rechecked the count and onset
strata from persisted rows. All payload/source hashes, current used-code hashes
and 437 inventoried historical files/permissions remain valid.

The focused generated regression batch passes 63 tests. Scoped Ruff/format/mypy,
Markdown links, diff and source secret checks pass. Logs and read-only verification
scripts remain under ignored `tmp/exp-beta02-*` and `tmp/verify-exp-beta02.py`.
The unrelated older private migration inventory discrepancy for the decision
register remains explicitly unmodified, as documented in the [implementation](README.md).

**Hypothesis: NO_RESPALDADA for this frozen marginal NB2 approach.** T+1 already
fails the joint acceptance controls; T+2 onset and a justified neural alternative
remain NO_EVALUABLE. This is not a proof that every possible count model is
ineffective. No further estimator, penalty or threshold search was triggered by
these results. Transmission profiles lack a validated source and remain
NO_EVALUABLE. Statistical noninferiority is UNAVAILABLE, superiority is
NOT_ESTABLISHED, G5 is NOT_APPROVED and champion remains not_selected.
R0 remains the primary research reference for a separately gated Phase 4.
