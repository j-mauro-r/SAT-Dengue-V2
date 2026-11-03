# EDA-EXP02 — Phase A conclusions

**Final state: `READY_WITH_LIMITATIONS`.** Phase A is complete as a bounded source
audit. Two conditional opportunities warrant Phase B **design**, with no
demonstrated predictive gain and no operationally validated candidate. Proceed
only after Mauricio authorizes that next scope; no Phase B or EXP-DELTA02 has
started. The [README](README.md) owns source IDs, exact private identities,
coverage definitions and audit limits; the
[CSV](SIGNAL_INVENTORY.csv) is the unique signal-level matrix.

## Main findings

1. **National calendar coverage exceeds observed notification presence.** In
   2011-06–2024-12, 1,103/1,122 territories have any general-dengue notifications,
   and 790 have severe-dengue records. All 1,122 are retained through the approved
   zero-by-absence calendar rule. Only 36 have notifications in every month;
   this does not establish whether other months reflect zero disease or reporting
   gaps. Meta–Tolima has 76/76 with some general-dengue notifications and 71 with
   severe notifications. Snapshot integrity does not prove extraction completeness.
2. **History is asymmetric.** The national canonical table has 182,886 rows and
   163 origins. H5 is available from 2011-06 for the original 76, but only from
   2016-06 for the other 1,046. Regional counts extend 2006-06–2026-01; nine-variable
   climate coverage extends 2007-01–2025-12. These extra dates are source inventory,
   not a new independent evaluation opportunity (I01/I11/I12).
3. **Climate availability and climate usefulness are different findings.**
   All nine variables are complete for 182,560 national rows/1,120 territories
   and all 12,388 regional rows in the common national window. EDA-EXP01 already
   had complete climate on its frozen 2,653/2,422 horizon cohorts. Its inconsistent
   associations, overlapping true/false alert climates and only 1/32 and 0/14
   near-P75 common cells with ≥3 observations per group support
   `INSUFFICIENT_EVIDENCE`, not another lag search (I02).
4. **Most readily suggested local features are already investigated or algebraic
   views of the same information.** The meaningful remaining local question is
   ordered episode history, not renaming count differences or six-month state
   frequencies as new information (I03/I04).
5. **Other municipalities' time-varying epidemiology is a distinct information
   source.** N makes its retrospective ingredients available. BETA01 V2 expanded
   training rows; it did not add neighbors' cases/onsets at each origin. Its
   negative national-transfer finding therefore neither tests nor endorses
   spatial-context features (I07).
6. **Official transmission stratification exists outside the admitted tables.**
   [MSPS/INS's 2022 methodology](https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/VS/ED/VSP/lineamiento-metodologico-estimacion-poblacion-arbovirosis-colombia-2020-2023.pdf)
   describes historical endemicity work and revised classification approaches;
   [INS 2023 Annex 4](https://www.ins.gov.co/BibliotecaDigital/lineamientos-nacionales-2023.pdf)
   identifies municipal lists. A dated, code-validated membership panel, its
   source lookback and release history have not been established for the 76.
   EDA-EXP01's finding of no historically validated classification **in its
   admitted sources** remains valid. Departments and error clusters cannot fill
   this gap. Profile-based analysis remains conditioned, not ready.
7. **Observation before T does not establish availability by T.** All empirical
   inputs retain `UNVERIFIED` operational timing. Local metadata can support a
   later reporting-delay investigation but cannot reconstruct immutable as-of
   histories. Calendar season is the only timing-verified signal in this inventory.

## Prior work that should not be repeated as a new discovery

| Signal or proposed remedy | Verified antecedent | Consequence |
| --- | --- | --- |
| Counts, short lags, three-month means, first differences, seasonality, current/lagged channel and observed/expected notification ratios (L01–L05, L07–L10, L14–L15) | EXP03 B/U/L/Z/R/F groups; current information contributes conditionally at T+1; historical thresholds help boosting under that protocol, but every primary disposition remains inconclusive | Preserve baseline knowledge. Do not claim these are absent or generally ineffective. |
| Six-month SECURITY/WARNING/EXCESS frequencies and recent-minus-prior-semester changes (L09–L10) | EXP03.1 Q1 partially supported; Q2/Q3 not supported. Repeated-cell totals: Q1 +5 onset detections with +58 false alerts; Q3 −10 detections with +30 false alerts | Do not repeat M01/M02 under a new name or treat repeated totals as unique events. |
| Climate T and predefined lags (C01–C10) | EXP03 conditional gains/load and adverse 2024 stress; BETA01 OFF/ON mixed trade-offs; EDA-EXP01 Chapter 7 insufficient evidence | Neither absence of all climate value nor a supported general climate upgrade follows. Do not repeat closed climate EDA. |
| Departmental residual adaptation or national pooling as a general remedy | BETA01 L1 not supported; BETA01 V2 G1 loses five/one detections and adds eight/21 false alerts at T+1/T+2 | Not new anticipatory inputs; do not restart these models. |
| Marginal count forecasts as direct onset-T+2 probabilities | BETA02 T+1 joint objective not supported; T+2 onset not evaluable from marginals | Distinguish counts, excess and onset; do not invent a joint probability. |
| Recalibration, moving windows or a new global scalar threshold on frozen scores | EXP04 detection cost; DELTA01 has no admissible P1 in two required cells and only 3/6 available policies transport the FAR margin | These change a procedure/policy, not available information. No automatic DELTA02. |
| Filter near-P75 cases or set municipal policies from evaluation errors | Benchmark diagnosis and EDA-EXP01 F6/F7: boundaries occur among errors and useful detections; sparse municipal onsets | Preserve H5 and all municipalities. No retrospective profile construction or boundary filter. |

Acceleration (L06) is **not independently evaluated** in the reviewed inventories,
but it is a deterministic second difference of already available short-lag counts.
Without a justified representation-specific question, it is not incremental
information and does not make the shortlist. Likewise, episode frequency over a
fixed window can overlap EXP03.1's state counts; only genuinely order-dependent
episode timing is retained as a conditional question.

## Available ingredients not yet represented in the reviewed feature sets

The national series can supply other municipalities' lagged notifications and
historically known H5 transitions, subject to its history limits. The existing
regional H5 sequence can in principle distinguish recency and ordering of past
completed episodes. No admitted feature inventory contains a verified neighbor
graph, neighbor signal or explicit time-since-completed-episode variable.

These are ingredient-level findings. **No neighbor, episode duration, inter-onset
interval, transmission profile, acceleration or new feature was calculated.**
Transformability does not establish useful event support, biological transmission
links, operational timing or predictive improvement.

## Two conditional opportunities for Phase B design

The order below reflects direct evidence and unmet prerequisites, not numerical
scores. These are the only shortlisted opportunities; subordinate CSV rows are
components or alternatives, not extra candidates.

### O1 — Recent epidemiological activity outside the focal municipality

**Inventory:** S01–S03; S05/S06 are geographical prerequisites; S04 is a later
ordering question. **Novelty:** new information relative to focal-municipality
inputs, rather than another national training expansion.

**Evidence and applicability:** N contains notifications for all 1,122 calendar
territories and historical H5 for all after 2016-06, including cross-department
context around Meta/Tolima. EDA-EXP01 documents shared missed onsets and incomplete
local separation, but does not establish a spatial mechanism. DANE provides an
official geometry source (E01). These facts justify testing the missing-information
question; proximity alone supplies no evidence of transmission linkage.

**Question for a separately authorized Phase B:** conditional on focal counts,
channel, season and territory, is already observed activity in a prespecified
geographic relation present *before* focal onset, with adequate support in both
departments and horizons? Distinguish first onset from continuation and common
seasonal/regional shocks. Do not choose neighbors or lag windows from observed
model errors or select the strongest pairwise correlation.

**Readiness and cost:** medium analytical complexity, with a real source-admission
dependency. Geographic adjacency means shared boundaries; distance requires a
specified metric and representative location. Neither measures human mobility or
epidemiological connectivity. S07/S08 lack an admitted input and are excluded from
this first opportunity. The climate scripts' simplified private assets are not a
validated neighbor graph. No matrix is built in Phase A.

**Conditions before analysis:** admit a pinned historically defensible geometry
and DIVIPOLA crosswalk; fix one relation/lag definition independently of outcomes;
audit matched neighbor/origin coverage and reporting-time evidence. Establish
eligible focal events and independent temporal support before association claims.
For pre-2016 external H5, leave unknowns unknown or restrict the design; never
borrow regional history for the other 1,046. If geography or as-of timing cannot
be established, stop the operational branch; any retrospective question must be
explicitly labeled. No expected gain is estimated.

### O2 — Recency and ordering of completed local H5 episodes

**Inventory:** L11; L12/L13 are alternative historical descriptors within this
single opportunity. **Novelty:** a new representation of existing information,
not a new dataset. Compare explicitly with EXP03 lags and EXP03.1 state frequencies.

**Evidence and applicability:** all 76 have a complete current H5 sequence in
2011-06–2024-12; R provides its underlying earlier counts. State frequencies
discard order: two sequences can have equal recent state counts and different
time since an earlier completed episode. That is a concrete distinction from
M01/M02, not evidence that recency predicts onset or proxies immunity.

**Question for Phase B design:** does a predeclared time-since-last-observed-onset
or completed-episode representation retain descriptive variation beyond existing
lags/state counts, on a common at-risk cohort, with enough distinct historical
events? Separate it from seasonal variation and continuing excess. Do not launch
a broad search over durations, interval definitions or cutoffs.

**Readiness and cost:** lower implementation complexity than O1, but substantial
support and censoring constraints. Before the first observable H5 transition,
recency is unknown/left-censored, not zero or an infinitely long quiet spell.
An episode active at T has unknown final duration; historical duration is usable
only after its end is observable by T. Inter-onset intervals require two prior
observed starts. No completed interval may cross a missing state or depend on a
future end. A short completed run remains a descriptive H5 episode, not verified
clinical transmission.

**Conditions before analysis:** freeze one ordering descriptor and its redundancy
comparison; audit contiguous historical state support and distinct past starts
without using evaluation errors. Set a scientifically justified support rule
before seeing associations. EDA-EXP01's 273/300 and 294/298 municipality-years with
fewer than three onsets warn against municipal-level effects or policies; complete
history alone does not overcome this. National extension would have a later
history origin and is secondary to the 76. Stop if the representation is
equivalent on admissible rows or adequate episode support is absent.

## External sources retained outside the shortlist

| Candidate | Potential contribution | Decisive gap / disposition |
| --- | --- | --- |
| Historically issued transmission profiles (T03; E03/E04) | Predefined territorial strata, with better provenance than error-derived groups | Obtain complete code membership, lookback, publication and validity dates first. The 2022 methodology/2023 edition cannot certify availability before 2020. Do not conflate endemicity, risk, current outbreak status and transmission intensity. |
| Population, historical incidence and urban/rural share (T01/T02/T04; E02) | Denominators and contextual composition absent from canonical predictors | Revised 2025 population series need earlier vintages. Total-resident incidence is not incidence in the population at risk. AREA describes case occurrence, not municipal residence urbanization. No rates were calculated. |
| Population density/elevation (T05/T06; E01/E02/E08) | Territorial context potentially distinct from municipal identity and observed climate | Need compatible geometry/year/units and a population-relevant summary. Mostly static context supplies no demonstrated month-specific onset signal. |
| ENSO (C11; E05) | Broad climate regime potentially different from local weather | ONI seasons overlap and historical values are revisable; assigning a centered season to T may use T+1. The five-season episode convention can require later observations. Release-vintage and lag rules are unresolved; national replication is not independent municipal evidence. |
| Entomological indices (C12; E06) | Directly surveyed vector/container context | A report is not a complete monthly panel. Sampling effort, locality, dates, access and regional coverage are unknown; surveillance may intensify after an outbreak. The source itself cautions against assuming standard larval indices predict outbreaks. |
| Surface water (C13; E07) | Observed water persistence beyond monthly rainfall/runoff | Pixel-to-municipality aggregation, clouds/no-data, revisions and release lag unresolved. Whole-history recurrence/occurrence would leak future years. Open-water detection is not household breeding-container surveillance. |

No third opportunity is forced. Biological plausibility, a long nominal history,
or a public download page is insufficient to prioritize these inputs.

## Recommendation and stop conditions

Continue to **bounded Phase B design only**, with O1/O2 as conditional options.
First resolve timing/source admission and predeclare support, censoring and
redundancy checks. If these prerequisites cannot be met, pause or conclude
`NO_CANDIDATES_SUPPORTED` for the affected follow-up; do not manufacture a third
candidate or relax the academic contract. `READY_WITH_LIMITATIONS` is appropriate
because concrete, distinct questions and existing ingredients were identified,
while adequate new-signal support and operational safety remain unproven.

Any later descriptive analysis of consumed 2020/2021/2022/2024 or previously used
2025 remains exploratory. No unused independent period is certified by this audit.
An eventual predictive experiment requires its own protocol, explicit authorization,
chronological roles, common cohorts, detection and false-alert burden assessed
together, and an independent evaluation opportunity. Phase A makes no causal,
superiority, prospective, immunity or sanitary-efficacy claim.

The existing experiment registry, scientific decisions, contracts, models,
datasets, publications and notebooks remain unchanged. Independent PR review,
GitHub CI and Mauricio's merge decision remain separate from this Phase A state.
