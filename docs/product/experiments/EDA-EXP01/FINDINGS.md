# EDA-EXP01 — findings

All new calculations come from the executed
[notebook](../../../../notebooks/eda_experimental_results.ipynb) and the identified
private derived publication in [README](README.md). Tables below name its payloads.
Horizon populations are not combined. Rates are descriptive on consumed years.

## F1 — Most of the pooled T+1 territorial FAR gap is associated with prevalence

- **Observation:** similar FPR does not imply similar FAR.
- **Evidence:** G0_OFF Meta/Tolima have 1,024/1,629 eligible rows, 146/167 onsets,
  74/72 detections and 66/113 false alerts. FPR is 7.52%/7.73%; sensitivity
  50.68%/43.11%; prevalence 14.26%/10.25%; FAR 47.14%/61.08%.
  The 13.9382 pp Tolima−Meta FAR gap decomposes into prevalence **+9.2785 pp**,
  sensitivity **+3.9778 pp** and FPR **+0.6819 pp**. At common prevalence 11.7980%,
  FAR is 52.5790%/57.2696%, leaving **4.6905 pp**.
- **Source:** `department.csv`, `decomposition.csv`, Chapter 2; same benchmark rows.
- **Interpretation:** lower event prevalence accounts arithmetically for much of
  Tolima's larger fraction of alerts that are false. Sensitivity also contributes.
- **Limitation:** accounting substitutions do not identify why prevalence or
  predictor behavior differs. Pooled department populations have different year mixes.
- **Consequence:** examine composition before proposing territorial thresholds;
  prevalence standardization does not eliminate all T+1 behavioral difference.

## F2 — T+2 changes the territorial interpretation

- **Observation:** excess and onset lead to different explanations at T+2.
- **Evidence:** Meta/Tolima have 154/194 target excesses over 943/1,479 rows,
  52/78 false excess alerts over 91/132 alerts and FAR 57.14%/59.09%.
  Excess sensitivities are 25.32%/27.84%; onset sensitivities 23.96%/31.71%.
  The observed FAR gap **+1.9481 pp** decomposes into prevalence **+6.2363**,
  excess sensitivity **−2.2925** and excess FPR **−1.9958 pp**. At common excess
  prevalence 14.3683%, the gap reverses to **−4.2844 pp**.
- **Source:** `department.csv`, `decomposition.csv`, Chapter 2.
- **Interpretation:** lower Tolima excess prevalence offsets its more favorable
  pooled excess sensitivity/FPR. A uniform story of worse territorial prediction
  would miss this horizon-specific composition.
- **Limitation:** onset probabilities are not excess probabilities; the decomposition
  explains excess-FAR arithmetic only. Thirty-one G0_OFF continuation alerts are
  correct for excess and false for onset.
- **Consequence:** preserve both events and their denominators in any later protocol.

## F3 — Useful ranking coexists with unresolved score overlap and shared misses

- **Observation:** signal exists, but does not separate all relevant outcomes.
- **Evidence:** annual G0_OFF onset AUROC ranges **0.7754–0.8301** at T+1 and
  **0.7127–0.7627** at T+2. AP ranges **0.1995–0.5251** and **0.2110–0.3607**,
  with annual onset prevalences 6.15%–22.74% and 5.78%–14.73% respectively.
  In 2022, all four models miss **32/89** T+1 and **29/62** T+2 onsets.
  Among distinct non-excess observations falsely alerted by any model, **65/94**
  and **65/127** are shared by at least two models.
- **Source:** `discrimination.csv`, `real_class_quantiles.csv`, `score_ecdf.csv`,
  `score_quantiles.csv`, `multiplicity.csv`; Chapters 3–5, Figures 2/6.
- **Interpretation:** a policy-only explanation is incomplete; some missed signal
  and overlapping classes are shared. T+2/2022 has particularly limited ranking.
- **Limitation:** AUROC/AP do not prove inadequacy for every policy class. AP also
  changes with prevalence, and related models are not independent replications.
- **Consequence:** prioritize local separability and composition together with
  decision transport, without selecting a new predictor from these reused years.

## F4 — Temporal calibration changes direction without a uniform ranking collapse

- **Observation:** annual procedures have different probability scales and biases.
- **Evidence:** G0_OFF mean-p minus onset frequency is **+11.1940/+7.8066 pp**
  in 2022 and **−12.2585/−7.5275 pp** in 2024 (T+1/T+2). T+1/2022 AUROC
  **0.8301** is higher than 2020 **0.8126**, 2021 **0.7754** and 2024 **0.7996**.
  T+1 Brier is 0.0823/0.0558/0.1038/0.1695 in chronological evaluation years.
  For the fixed 2022 procedure, selection/evaluation onset prevalence changes
  **6.15%→12.84%** at T+1 and **5.78%→9.67%** at T+2; mean scores change
  **20.52%→24.04%** and **16.25%→17.48%**.
- **Source:** `discrimination.csv`, `reliability.csv`, `selection_comparison.csv`;
  Chapter 4, Figure 3. [Historical EXP04 synthesis](../analisis-5.md) supplies context.
- **Interpretation:** calibration, prevalence, discrimination and contractual margin
  vary differently. Lower Brier or higher AP cannot alone certify warning usefulness.
- **Limitation:** annual retraining/calibration changes the procedure; the comparison
  does not isolate drift of one fixed model. Reliability tails lack support.
- **Consequence:** retain separate audits of risk calibration, ranking and alert
  performance; another calibrator is not automatically justified.

## F5 — DELTA establishes both infeasibility and incomplete temporal transport

- **Observation:** aligning threshold selection with the contract did not provide
  a complete feasible, stable policy.
- **Evidence:** the stored frontier has **0/510** feasible thresholds for T+1/2022
  and **0/259** for T+2/2024. Both complete P1 horizons are `NO_EVALUABLE`.
  Of six available policies satisfying historical C, only **3/6** retain C in
  evaluation. T+1 loses **19, 2 and 28** detections in evaluable 2020/2021/2024.
  In T+2/2022 Meta gains three detections and FAR falls **50.00%→44.12%**;
  Tolima also gains three but FAR rises **71.74%→73.33%**.
- **Source:** `feasibility.csv`, `transport.csv`; exact reconciliation of all 60
  [DELTA metric strata and published paired changes](../EXP-DELTA01/RESULTS.md).
- **Interpretation:** both development feasibility and future relative-margin
  compliance matter; lower absolute FAR need not preserve margin against CHANNEL.
- **Limitation:** no new policy is tested here. Two missing mandatory policies
  prohibit complete or department-pooled P1 improvement claims.
- **Consequence:** do not automatically recommend EXP-DELTA02 or relaxed constraints.

## F6 — Municipal estimates have insufficient support for stable local policies

- **Observation:** pooling hides very small yearly event and alert counts.
- **Evidence:** of **300/298** observed municipality-years (T+1/T+2), **105/129**
  have zero onsets; **273/294** have fewer than three. Across four years,
  **43/76** T+1 and **64/76** T+2 municipalities still have fewer than five onsets.
  **142/162** municipality-years have no G0_OFF alerts, making FAR undefined.
  Among defined annual rates, median 95% Wilson reference widths for both
  sensitivity and FAR are **79.35 pp** in each horizon.
- **Source:** `municipal.csv`, `municipal_year.csv`, `support.csv`; Chapter 5,
  Figures 5/8. Codes and individual municipal rows remain private.
- **Interpretation:** extreme 0%/100% municipal rates frequently carry little information.
- **Limitation:** binomial intervals assume independent observations, while municipal
  months are dependent. No temporally validated transmission profile is available.
- **Consequence:** geographic heterogeneity motivates a question, not selectable
  municipal thresholds or validated transmission groups. Profile analysis is blocked.

## F7 — Boundary conditions occur in errors and in additional detections

- **Observation:** nearness to target-month P75 is not specific to false alerts.
- **Evidence:** T+1 G0-only false alerts are near P75 in **107/118 (90.68%)**
  cases; additional true detections in **62/71 (87.32%)**. Exact equality occurs
  in **82/118** and **46/71**. For T+2, near-boundary counts are **74/92**
  and **28/33**. P75=0 occurs in **20/118** false versus **11/71** true
  additional T+1 alerts. T+2 has **284** eligible rows whose target-minus-one
  month is already in excess, including **40** G0_OFF alerts, **31** correct
  for excess but false for onset.
- **Source:** `boundary.csv`, `origin_zones.csv`, `prior_states.csv`; Chapter 6,
  Figure 7. [EXP02 conclusions](../EXP02_label_stability/CONCLUSIONS.md) provide
  separate evidence of H5/H9 label sensitivity: 87/912 changed onset labels in 2024.
- **Interpretation:** small-count boundaries describe a shared difficult context;
  they do not identify mislabeled cases or validate a filter.
- **Limitation:** ±1 case is descriptive; overlapping descriptors cannot be summed.
  EXP02's full-month population differs from the benchmark eligible population.
- **Consequence:** preserve H5 and avoid new epidemiological adjudications or
  removing boundary alerts on the basis of this EDA.

## F8 — Errors concentrate, but neither model nor CHANNEL uniformly dominates

- **Observation:** a territorial concentration exists alongside complementary detections.
- **Evidence:** the seven municipalities with most observed G0_OFF false excess
  alerts account for **51/179 (28.49%)** at T+1 and **40/130 (30.77%)** at T+2,
  over **20.08/221.08** and **19.17/201.83** eligible municipality-years.
  Errors occur in **56/76** and **48/76** municipalities. G0_OFF detects **71/33**
  onsets CHANNEL misses, but CHANNEL detects **19/17** G0_OFF misses (T+1/T+2).
- **Source:** `support.csv`, `overlap.csv`; Chapters 3/5.
- **Interpretation:** errors are unevenly distributed, while comparator successes
  overlap only partially. Aggregate detection gains conceal gains and losses.
- **Limitation:** these top-seven sets are selected retrospectively by errors,
  differ by horizon and have unequal exposure. They are not prospective groups.
- **Consequence:** retain paired gains/losses and exposure in future protocols;
  no municipal exclusion, profile selection or ensemble is inferred.
