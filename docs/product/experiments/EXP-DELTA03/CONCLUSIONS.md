# EXP-DELTA03 — retrospective scientific conclusions

The primary result is **NOT_SUPPORTED**. FULL_COMMON does not meet the frozen
academic acceptance conditions at either horizon and provides no incremental
detection advantage over the frozen learned controls. Execution succeeded
technically; that does not imply scientific acceptance or authorize promotion.
[PHASE3.md](PHASE3.md) owns all execution identities, metric/support tables and
artifact-verification evidence. These conclusions use the frozen regional
2020–2022 development cohort; 2024 is reported separately.

## Question and hypotheses

The question was whether climatic, environmental, territorial and demographic
blocks add incremental H5 onset prediction at T+1/T+2 when national pooled
XGBoost is applied to the same Meta/Tolima cohorts under the frozen selection
budget. H1 proposed extra detections over existing learned controls at a verified
common budget; H2 proposed consistent utility loss when a material block is
removed; H3 proposed surface-water benefit on genuine coverage only.

H1 is not supported by observed detections: FULL_COMMON detects 40/210 and 17/158
in development; R0/G0_OFF/G0_ON/G1 detect 77/91/97/88 at T+1 and 63/36/43/42 at T+2.
Full comparator role/budget equivalence is not established, so these are immutable
descriptive controls, not a formal equal-capacity superiority test. Independently,
the controlling academic comparison fails: FULL_COMMON detects fewer onsets than
CHANNEL (52/210 and 25/158), and its excess-FAR exceeds CHANNEL by 35.99/28.78 pp,
well beyond the five-point limit. Beating zero-alert PERSISTENCE satisfies only B.

H2 has no consistent cross-horizon/period support. H3 shows no observed increment
on the admitted water cohort. Neither result establishes causal irrelevance of
environmental variables or a universally optimal feature set.

## Primary utility and calibration

Sensitivity is 19.05%/10.76%, precision 12.16%/5.28%, and 170/141 eligible onsets are
missed at T+1/T+2. AP 0.1346/0.0921, secondary AUROC 0.5759/0.5361 and Brier
0.0962/0.0762 do not overturn failed alert utility. False-onset rates are
1.576/1.823 per eligible municipality-year (1.268/1.459 per monitored year).
Selection B=1 was respected in every cell; it did not transport as an evaluation
cap. This is evidence against assuming that selected budgets remain stable.

Mean probability overestimates development onset prevalence by 0.0647/0.0346;
ECE is 0.0692/0.0449. In stress2024 the signed bias reverses to −0.1334/−0.0637,
with ECE 0.1334/0.0655. Intercept calibration on an earlier role does not establish
later calibration. This observation does not authorize recalibration on evaluation.
Higher stress AP accompanies different prevalence and support; it is not a clean
between-period model improvement. Anticipation of 1/2 months follows label geometry,
without evidence of actual data availability or operational response time.

## Ablations and history

| Block or sensitivity | Development evidence | Scientific disposition |
| --- | --- | --- |
| History-only vs FULL_COMMON | 47 vs 40 detections at T+1,24 vs 17 at T+2;69/116 fewer false-onset alerts | Simpler history-only is descriptively favorable on these pooled counts, but sensitivity intervals cross zero at both horizons and period effects vary; no replacement champion |
| Thermal/humidity removed | +2/−2 detections at T+1/T+2 | No consistent benefit from inclusion or removal |
| Rainfall/hydrology removed | +2/+8 detections; +3/+71 false-onset alerts | More detections can cost more alerts; no stable net block utility |
| NDVI removed | +2/+5 detections; +19/+20 false-onset alerts | No consistent incremental inclusion benefit; tradeoff remains |
| Terrain removed | +2/0 detections; −12/+9 false-onset alerts | Horizon-dependent, no consistent increment |
| Demography removed | −13/+14 detections; +22/+181 false-onset alerts | Opposing horizon effects; T+2 detection gain carries substantial load |
| Land cover removed | +3/+2 detections; −19/+9 false-onset alerts | Small unstable differences, no established consistent benefit |

The intervals are paired descriptive uncertainty under the predeclared block
resampling, not independent IID tests. Removing demography at T+2 has a positive
saved sensitivity interval [1.74,16.55] pp while its false-onset rate difference
spans [0,2.280] per eligible year. Removing rainfall at T+2 has sensitivity
interval [0,14.91]pp and a positive burden interval [0.033,0.819]. Endpoint zero is
not strictly positive evidence. No block shows a consistent advantage across
both horizons and periods, and multiple contrasts were not multiplicity-adjusted.
The 78 saved annual contrasts preserve gained/lost onsets and per-metric absolute/
relative changes; pooled direction alone cannot justify deleting a feature block.

## Meta and Tolima

Meta's development sensitivity is 26.26% at T+1 but8.70% at T+2; Tolima's is
12.61%/12.36%. The apparent T+1 advantage in Meta disappears at T+2. Tolima has
development excess-FAR92.59%/90.86% and lower AP 0.0898/0.0728; Meta has
81.43%/88.44% and AP 0.2102/0.1314. Department support and prevalence differ;
the pooled result cannot be represented as uniform regional utility.

National sensitivity is only 8.40%/6.04% in development, with AP 0.1364/0.0888.
These are secondary national views of a regionally selected policy, including
Meta/Tolima. They are neither an independent replication nor evidence that
national training produced national alert utility. Frozen learned national
comparator scores are absent, so that comparison remains non-evaluable.

## Transfer excluding Meta/Tolima

The correct paired reference is TRANSFER_REFERENCE, not FULL_COMMON. Excluding
Meta/Tolima from all learned roles yields65 vs 42 detections and 342 vs 309 false-
onset alerts at T+1; at T+2,26 vs 20 detections and 224 vs 339 false-onset alerts.
The saved sensitivity intervals cross zero. This changes training, calibration,
selection and reference transformations together, with different historical
coverage outside the region; it is not a causal effect of training population size.
The T+2 point tradeoff merits a separately predeclared investigation, not promotion
from this consumed retrospective comparison.

## Climate: CHIRPS and ERA5

FULL_ERA5_PRECIPITATION must be compared with ERA5_REFERENCE on the genuine shared
cohort. It detects 42 vs 43 onsets at T+1 and 13 vs 16 at T+2, with 273 vs 285 and
299 vs 354 false-onset alerts. Lower load accompanies fewer detections; this does
not establish ERA5 superiority or justify replacing CHIRPS. The climate and
hydrology ablations likewise show utility/load tradeoffs rather than a stable
cross-horizon gain. Reference/support differences prevent a direct attribution
from unmatched FULL_COMMON totals.

## Surface water

FULL_PLUS_SURFACE_WATER and WATER_REFERENCE have identical saved development
outputs/metrics, with zero paired differences and [0,0] intervals. There is no
observed increment in this frozen configuration. Genuine source coverage ends
in 2021; only lag-supported124-row views per horizon remain in 2022. Four2024
descriptors are unavailable, not failed models and not zero-effect observations.
The result cannot be extrapolated to later water coverage or universal lack of
predictive information. No imputation of later water data is warranted.

## Separate consumed 2024 stress

FULL_COMMON detects 15/103 and 8/61 versus CHANNEL42/103 and 21/61. Its excess-FAR
61.54%/62.22% exceeds CHANNEL40.85%/46.99%; A/C fail again. Regional Brier rises
to 0.1892/0.1291. Meta detects 7/47 and 3/27; Tolima8/56 and 5/34. National detects
153/1461 and 47/818. These are distinct retrospective support/prevalence regimes,
not development additions or independent confirmation. All18 stress uncertainty
sets lack the required two temporal blocks and remain non-evaluable. No stress
interval or definitive between-year effect is inferred.

## Limits, revised decisions and next experiment

Consolidated snapshots do not establish historical releases, operational E(T),
covariate vintage or available-at-origin labels. H5 onsets are experimental and
not externally epidemiologically validated. National pooled training includes
regional history; monitored and eligible exposures differ. Coverage1.0 refers
to admitted view retention, not complete real surveillance. Only three development
blocks support the descriptive intervals. Transmission-profile mapping and frozen
learned national comparators remain unavailable. None is silently substituted.
2025 is already consumed and remains excluded; it is not an untouched confirmation set.

Retain the frozen outputs and negative result. Do not promote FULL_COMMON, treat
history-only/transfer as a new champion, remove blocks automatically, or retune
thresholds/calibration against these evaluation outcomes. G5 remains NOT_APPROVED,
champion not_selected, operational_PIT=false, with no deployment authorization.
Technical verification and this documentary closure do not constitute Mauricio's
independent acceptance of a scientific model or permission to merge PR79.

A later human-approved experiment could compare history-only and the existing
frozen controls under an explicitly verified common role/capacity contract, then
test calibration/budget transport and regional heterogeneity on new, predeclared
temporal evidence with release/vintage auditing. Transfer and genuine later-water
coverage need separate hypotheses and support rules. No such experiment, HPO,
new execution or additional phase is started here.
