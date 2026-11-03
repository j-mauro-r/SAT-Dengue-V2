# EDA-EXP02 — Phase B findings

**Executed 2026-11-03.** Six findings from the new
[notebook](../../../../notebooks/eda_epidemiological_signals.ipynb); publication
identities and reproduction are in the [README](README.md#phase-b--authorized-exploratory-execution).
All numerical findings use the frozen benchmark, not newly trained predictions.
T+1/T+2 are separate; 2020/2021/2022/2024 are consumed retrospective years.
No intervals, p-values, causal effects or incremental performance are claimed.

## B1 — Complete episode history on the frozen evaluation population

- **Observation:** completed local history is available on 2,653/2,653 T+1 rows
  and 2,422/2,422 T+2 rows, including all 313/219 onsets. The analysis retains
  76 municipalities, 29 Meta and 47 Tolima. T+2 includes 129 continuations and
  2,074 no-excess outcomes; T+1 has 2,340 no-excess outcomes.
- **Evidence and denominator:** `cohort.csv`, `history_support.csv`,
  `censoring.csv`; 1,326 fully observed completed H5 episodes in the regional
  history through 2024-12, not 1,326 evaluation onsets or independent subjects.
- **Method:** verify exact publication hashes, one-to-one arm pairing and
  municipality/month joins; scan contiguous H5 states from the first observable
  channel month, 2011-06. Completion requires a known start and clearance before T.
- **Interpretation:** source/history availability does not exclude benchmark
  observations in this bounded analysis.
- **Limitations:** original benchmark selection remains; early history is
  left-censored and active boundary runs are not completed. Covered notification
  zeros do not prove active negative surveillance. No historical reporting vintages.
- **Scientific consequence:** O2 is evaluable on the original cohort without
  imputing recency. This does not certify all regional months or operational use.

## B2 — Shorter completed-episode recency accompanies onsets

- **Observation:** median end-recency is 5 months among onsets in both horizons,
  versus 8 among no-excess months. T+2 continuations also have median 5 months.
  The fixed 1–3-month band has 90/528 onsets (17.05%) at T+1 and 67/484 (13.84%)
  at T+2, versus 12/219 (5.48%) and 9/191 (4.71%) at ≥25 months.
- **Evidence and denominator:** `outcome_distributions.csv`, `recency_bands.csv`;
  all 2,653/2,422 original observations. No unknown-history evaluation rows.
- **Method:** empirical distributions, type-7 quantiles and fixed-band contingency
  fractions. Primary recency uses the last excess month of the latest episode
  whose clearance was observed through T−1; minimum observed recency is two months.
- **Interpretation:** there is a descriptive association with recent local episode
  history. Similar continuation recency prevents treating it as onset-specific.
- **Limitations:** no-excess-at-T selection, episodic clustering, shared waves,
  territory and existing predictors can explain the marginal pattern. H5 runs
  may fragment around a threshold and are not independently adjudicated outbreaks.
- **Scientific consequence:** an exploratory representation is observable, but
  these fractions are neither calibrated risks nor new alert thresholds.

## B3 — Weak association, with territorial and temporal heterogeneity

- **Observation:** pooled Spearman recency/onset correlations are −0.126/−0.097
  at T+1/T+2. Seven of eight year/department directions are negative per horizon;
  Meta 2021 is positive (+0.042/+0.033). Within-calendar-cell rank centering gives
  pooled −0.098/−0.092 and negative directions in all 16 year/department cells.
  Pooled departmental raw correlations are −0.058/−0.056 in Meta and
  −0.165/−0.119 in Tolima (T+1/T+2).
- **Evidence and denominator:** `associations.csv`, `temporal.csv`,
  `history_support.csv`. Each horizon has eight year/department cells; smallest
  onset denominator is 24 at T+1 and 17 at T+2. All satisfy the aggregate support
  rule n≥30 and ≥5 per outcome class.
- **Method:** Spearman; subtract year×department×origin-calendar-month means from
  each variable's ranks, then correlate the centered ranks on identical rows.
- **Interpretation:** calendar-cell mean differences do not fully explain the
  association, but its magnitude is weak and Meta's raw pattern is less consistent.
- **Limitations:** centering is descriptive, not causal adjustment or independent
  confirmation. Cells share municipalities, months, histories and regional shocks;
  pooled Spearman is not a weighted average of stratum correlations.
- **Scientific consequence:** retain all directions and territories. Do not infer
  stable incremental usefulness from aligned centered signs.

## B4 — Distinct ordering representation, substantial overlap and sparse conditional support

- **Observation:** 1,712/2,653 T+1 rows and 1,531/2,422 T+2 rows belong to groups
  with equal six EXP03.1 summaries but multiple recencies (391/1,277 and 355/1,191
  groups). Correlations with recent six-month excess count are −0.694/−0.692;
  with dengue lags 1/2/3/12, absolute correlations range from 0.121 to 0.264.
  Start/end recency correlation is 0.852/0.850.
- **Evidence and denominator:** `representation_variation.csv`,
  `redundancy_correlations.csv`, `conditional_redundancy.csv`. Exact six-summary
  × year × department matching leaves 81/68 groups with both outcomes and variable
  recency: 367/303 rows, including 94/81 onsets. **Zero matching groups** meet the
  predeclared n≥30 and ≥5 per-class support rule.
- **Method:** reuse EXP03.1's historical-zone implementation; group by its six
  predictors and count distinct recencies. Supplement with rank correlations
  after centering within the exact six-summary/year/department groups:
  −0.038/−0.071. Singletons contribute no centered variation.
- **Interpretation:** recency is not identical to the semestral summary vector,
  but much of its association overlaps existing excess memory. Start-recency
  equals end-recency + completed duration −1 and is not a separate opportunity.
- **Limitations:** equal summaries are not equality of all existing inputs;
  correlation cannot establish non-redundant predictive information. Conditional
  cells are sparse; the rank audit does not estimate an ablation gain.
- **Scientific consequence:** retain one primary representation. Evidence for
  incremental usefulness is insufficient; no automatic feature adoption follows.

## B5 — Missed onsets do not show a selective recency separation

- **Observation:** G0_OFF misses 167/313 T+1 and 157/219 T+2 onsets. Missed/detected
  recency medians are 6/5 months at T+1 and 5/5.5 at T+2. All four frozen models
  miss 125/313 and 112/219 onsets, with median recency 6 in both horizons.
- **Evidence and denominator:** `missed_distributions.csv`, `missed_strata.csv`;
  exact original R0/G0_OFF/G0_ON/G1_OFF intersection. G0 detected groups contain
  146/62 onsets. Original EDA multiplicity counts reconcile; shared-miss groups
  are subsets of G0 misses, not additional samples.
- **Method:** descriptive quantiles/ECDFs using frozen decisions; no score changes,
  retrospective neighbor selection or event-based filtering.
- **Interpretation:** distributions overlap, and the missed-versus-detected median
  direction changes between horizons. No distinctive shared-error rescue is shown.
- **Limitations:** small annual/territorial missed subsets, repeated histories and
  no paired predictive intervention; signal presence on an error is not its remedy.
- **Scientific consequence:** do not propose a recency cutoff or claim recovery
  of the shared omissions from this EDA.

## B6 — Official geography exists, but historical admission is unresolved

- **Observation:** the official DANE MGN integrated 2018 service responds and its
  regional query returns exactly 76/76 benchmark DIVIPOLA codes, all VERSION 2018.
  **Zero geometries and zero neighbor edges are admitted** for this analysis.
- **Evidence and denominator:** pinned `source_admission` publication, service/layer
  metadata and the successful regional attribute query. The
  [official MGN announcement](https://www.dane.gov.co/index.php/actualidad-dane/5454-el-dane-actualizo-el-marco-geoestadistico-nacional-a-2018)
  is dated 2022-02-07; the
  [official service](https://geoportal.dane.gov.co/mparcgis/rest/services/MGN2018/Serv_CapaMunicipiosInt_2018/MapServer)
  identifies integrated version 2018. Access date: 2026-11-03.
- **Method:** inspect local source inventory, retrieve official service/layer
  metadata, validate full five-digit DIVIPOLA through a regional attribute query,
  and assess version/chronology against the canonical contract. The initial
  geoportal query returned HTTP 500; the portalgis query succeeded, so access
  failure is not the final blocker. No unofficial geometry substitute is used.
- **Interpretation:** code membership is verified; polygon/topology equivalence
  over the study years and the full outside-neighbor crosswalk are not. Layer
  metadata has no timeInfo/valid-time boundary history. National historical
  territory applicability remains explicitly `UNVERIFIED`.
- **Limitations:** this bounded attempt does not prove that suitable historical
  official geometry cannot be obtained. A release after 2020/2021 also does not,
  by itself, prove all retrospective geometry unusable; the unresolved historical
  correspondence is decisive, including for later benchmark years.
- **Scientific consequence:** O1 `NOT_EVALUABLE`, blocked by historical geography
  admission. Its association, self-exclusion and spatial coverage checks are
  blocked/not applicable. No spatial null result or departmental proxy is reported.
