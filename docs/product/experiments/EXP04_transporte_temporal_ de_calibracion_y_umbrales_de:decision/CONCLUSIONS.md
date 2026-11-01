# EXP04 — Scientific conclusions

**Scientific execution: completed; authorized bundle state: `VERIFIED`. Evidence: `DESCRIPTIVE_ONLY`.** No candidate met the joint development requirements for false-alert burden and sensitivity. Moving windows lowered burden, but lost too much detection; their different probability calibration did not change their alert decisions. No A+B+C composition was selected, so its transport to 2024 is `NOT_EVALUABLE`.

G5: NOT_APPROVED

champion: not_selected

## Evidence and interpretation

All empirical figures below come exclusively from the authorized bundle (`tmp/exp04-scientific-20261031-v1/result.json`), identified by its manifest (`tmp/exp04-scientific-20261031-v1/manifest.json`); both paths are relative to the repository root. These are local, unversioned scientific artifacts in temporary storage, not portable repository links or synthetic technical-validation outputs. The bundle identity below preserves the reported provenance; passing the Markdown link check does not verify the scientific bundle or establish its availability in a clean checkout:

- Bundle ID: `bbf1069c3855fb202f34f961a06fac1c203e48e73f6b97adce1e96662b3c4873`.
- Recorded execution: **282 cells, 72 calibrator fits, 72 threshold selections, 0 predictor fits, 0 MLflow writes**. This report reads existing results; it does not rerun or revalidate the experiment.
- Interpretation follows [DESING.md](DESING.md), the EXP04 entry in [experimentos.md](../experimentos.md), and the [frozen scientific protocol](scientific-protocol.json), whose recorded identity is `3f53615740281522f7efb2f124e810366c738acd11611a0905dbf9c27e1a599d`. The earlier [technical protocol](protocol.json) describes implementation boundaries; its pre-execution status is not the scientific outcome.

`A0` denotes the saved frozen reference within EXP04, not a new analysis of an earlier experiment. A1/A2/A3 use moving windows of 12/24/36 months, respectively, with the reference sigmoid method and C0 selector. B compares reference/sigmoid/isotonic; C compares reference/budget sensitivity/worst-block budget. T+1 has one onset objective; T+2 onset is primary and `excess_control` is reported separately.

**Development means 2020–2022 only.** The frozen eligibility rule requires FA_rate ≤1 in every evaluable development year and pooled sensitivity loss no worse than **−2 percentage points** against its paired control. Territorial deterioration limits interpretation to partial evidence without approval. **2024 is retrospective descriptive stress**, excluded from selection and pooled development summaries. It is never independent confirmation.

FA_rate is FP divided by common eligible observable municipality-month exposure/12, not FP/76 and not FAR. Sensitivity is TP/positives; precision is TP/(TP+FP); FAR is FP/(TP+FP), while FPR is FP/negatives. Alerts count positive municipality-month decisions, not unique episodes or intervention costs. Pooled rates use summed counts/exposure; pooled Brier is weighted by evaluation rows. Annual ranges are max−min within development only. Percentages and percentage-point changes are rounded to one decimal, FA_rate to three decimals, and Brier/ECE to four; no rounded value is used for eligibility.

Source locators: `cells` keyed by `(objective, family, horizon, cut, arm)` supply `metrics`, `strata`, `support` and `threshold`; `frozen[family/T+h].A.candidates` supplies recorded development eligibility; `contrasts` supplies paired effects; `execution_counters` supplies execution counts. Derived summaries below use only those stored metrics. The bundle's `transport.range` mixes development with stress, so it is not used as a development-only statistic.

## Support and evaluability

| Objective | Year | Rows | Onsets | Negatives | Municipalities | Months | Exposure | Prevalence % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | 661 | 69 | 592 | 76 | 12 | 55.083 | 10.4 |
| T+1 | 2021 | 846 | 52 | 794 | 76 | 12 | 70.500 | 6.1 |
| T+1 | 2022 | 693 | 89 | 604 | 76 | 12 | 57.750 | 12.8 |
| T+1 | 2024 stress | 453 | 103 | 350 | 72 | 12 | 37.750 | 22.7 |
| T+2 | 2020 | 588 | 51 | 537 | 76 | 11 | 49.000 | 8.7 |
| T+2 | 2021 | 779 | 45 | 734 | 76 | 11 | 64.917 | 5.8 |
| T+2 | 2022 | 641 | 62 | 579 | 76 | 11 | 53.417 | 9.7 |
| T+2 | 2024 stress | 414 | 61 | 353 | 70 | 11 | 34.500 | 14.7 |

Support is common across the compared onset arms and families within each horizon/cut. Development includes 29 Meta and 47 Tolima municipalities; stress retains 29 Meta municipalities and 43/41 Tolima municipalities in T+1/T+2. T+2 has 11 observed evaluation months per cut; T+1 has 12. Coverage is 1.0 with zero abstentions and zero excluded onsets **within the admitted cohort**, not evidence of complete territorial or real-time surveillance coverage. Do not add rows across families or overlapping calibration windows as independent observations.

Across cuts/families/horizons, calibration support is A1: 344–814 rows (45–130 positives), A2: 974–1,454 (102–220), A3: 1,787–2,221 (189–284). Selection has 128–355 rows in T+1 and 103–287 in T+2. Both predeclared selection blocks contain both classes, with minima of 8/6 positives in T+1/T+2. These are observed support facts, not evidence that the dependent B/C arms ran.

| Cells / arms | Evaluable | NOT_EVALUABLE | Scientific meaning |
| --- | --- | --- | --- |
| Onset A0–A3 | 96 | 0 | 24 cells per arm; development and stress |
| A4 | 0 | 24 | expanding_origin_undefined |
| B0–B2 | 0 | 72 | no_eligible_development_policy |
| C0–C2 | 0 | 72 | no_eligible_development_policy |
| D | 0 | 6 | no_eligible_development_composition; 2024 only |
| Separate T+2 excess A0 | 12 | 0 | Frozen controls; no onset-policy selection |
| Total | 108 | 174 | 282 recorded cells, not 282 independent experiments |

A4 lacks a defined expanding OOF origin. B/C/D are unavailable because **every A candidate failed development eligibility**, not because isotonic or C2 empirically failed. There is no fallback and no selected window, calibrator or selector in any of the six family/horizon chains. Transmission-profile comparisons and 2025 remain `NOT_EVALUABLE`. Missing numerical outcomes are `UNAVAILABLE`.

## A — Moving calibration windows: lower burden, excessive detection loss

The following development totals compare A0 → moving windows. A1, A2 and A3 have identical alert decisions, TP, FP, precision, sensitivity and average precision within each family/horizon/cut. They differ in probabilities and numerical thresholds, so one operating-result column represents all three without treating them as independent replications.

| Family | Horizon | Onsets | TP | FP | Alerts | Sensitivity % | Δ pp | Precision % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GAM | T+1 | 210 | 69 → 48 | 192 → 102 | 261 → 150 | 32.9 → 22.9 | -10.0 | 26.4 → 32.0 |
| LightGBM | T+1 | 210 | 95 → 63 | 189 → 105 | 284 → 168 | 45.2 → 30.0 | -15.2 | 33.5 → 37.5 |
| XGBoost | T+1 | 210 | 77 → 53 | 155 → 91 | 232 → 144 | 36.7 → 25.2 | -11.4 | 33.2 → 36.8 |
| GAM | T+2 | 158 | 33 → 24 | 215 → 151 | 248 → 175 | 20.9 → 15.2 | -5.7 | 13.3 → 13.7 |
| LightGBM | T+2 | 158 | 67 → 47 | 246 → 164 | 313 → 211 | 42.4 → 29.7 | -12.7 | 21.4 → 22.3 |
| XGBoost | T+2 | 158 | 63 → 48 | 202 → 151 | 265 → 199 | 39.9 → 30.4 | -9.5 | 23.8 → 24.1 |

All six pooled sensitivity losses exceed the frozen margin: **−5.7 to −15.2 pp**. Thus no candidate qualifies, including every T+1 candidate that respects the annual aggregate burden budget. Fewer false alerts are accompanied by more missed onsets; improved precision cannot compensate under the frozen joint criterion.

| Family | Horizon | A0 FA_rate: 2020, 2021, 2022 | Moving FA_rate: 2020, 2021, 2022 | Development range A0 → moving | Pooled FA_rate A0 → moving |
| --- | --- | --- | --- | --- | --- |
| GAM | T+1 | 1.652, 0.624, 0.987 | 0.472, 0.270, 0.987 | 1.028 → 0.718 | 1.047 → 0.556 |
| LightGBM | T+1 | 1.271, 0.624, 1.299 | 0.290, 0.624, 0.779 | 0.675 → 0.489 | 1.031 → 0.573 |
| XGBoost | T+1 | 1.343, 0.496, 0.797 | 0.254, 0.496, 0.727 | 0.847 → 0.473 | 0.845 → 0.496 |
| GAM | T+2 | 1.224, 0.555, 2.228 | 0.265, 0.385, 2.115 | 1.673 → 1.850 | 1.285 → 0.902 |
| LightGBM | T+2 | 1.551, 0.832, 2.172 | 0.408, 0.431, 2.172 | 1.340 → 1.763 | 1.470 → 0.980 |
| XGBoost | T+2 | 1.531, 0.508, 1.760 | 0.490, 0.508, 1.760 | 1.251 → 1.270 | 1.207 → 0.902 |

The moving-window development FA_rate range narrows for every T+1 family, but **widens for every T+2 family**. T+2 in 2022 remains above budget at 2.115/2.172/1.760 for GAM/LightGBM/XGBoost. All pooled moving rates are below one, demonstrating why pooled burden alone would hide failure of annual transport.

For timing, T+2 moving selection → evaluation FA_rate in 2022 is GAM **0.962 → 2.115**, LightGBM **0.878 → 2.172**, XGBoost **0.920 → 1.760**. The frozen selection budget does not bind future realized burden. A0 preserves its historical thresholds and is not reselected to meet the current common-exposure budget.

### Probability calibration improves in development without improving the operating frontier

Pooled development Brier (lower is better):

| Family | Horizon | A0 | A1: 12 months | A2: 24 months | A3: 36 months |
| --- | --- | --- | --- | --- | --- |
| GAM | T+1 | 0.1007 | 0.0974 | 0.0892 | 0.0840 |
| LightGBM | T+1 | 0.0941 | 0.0882 | 0.0811 | 0.0773 |
| XGBoost | T+1 | 0.0961 | 0.0905 | 0.0832 | 0.0790 |
| GAM | T+2 | 0.0808 | 0.0781 | 0.0754 | 0.0731 |
| LightGBM | T+2 | 0.0793 | 0.0756 | 0.0724 | 0.0699 |
| XGBoost | T+2 | 0.0797 | 0.0762 | 0.0730 | 0.0705 |

A3 has the lowest pooled development Brier in all six family/horizon combinations. This supports a **descriptive probability-quality advantage** for the longer moving history, not preservation of detection. The advantage is not uniform at every cut: GAM T+2 in 2022 has Brier 0.087282 for A2 versus 0.087307 for A3.

Short windows also do not improve calibration in every year. For GAM T+1 in 2021, A0 → A1 worsens Brier **0.0611 → 0.0802** and ECE **0.0664 → 0.1544**. Conversely, GAM T+2 in 2020 improves ECE **0.1450 → 0.0007** with A3 while detection falls **11/51 → 3/51**. Low ECE can coexist with poor alert utility. The stored reliability bins and score distributions support calibration assessment; no new curve fitting is required.

The invariant average precision and identical moving-window alert decisions are consistent with the frozen design's monotone-calibration warning: changing probability scale can improve Brier without improving ranking or the achieved detection–burden tradeoff. This is an interpretation of observed equality, not a causal proof. Numerical thresholds vary across methods/windows and cuts and cannot themselves rank transportability: GAM T+1 A1 thresholds are **0.3533, 0.2667, 0.0736** in development; T+2 GAM stress stores a null threshold for its zero-alert decision.

### Territorial stability

Pooled development department comparisons are A0 → moving for operating metrics; the Brier comparison uses A0 → A3. These summaries retain the same department support across paired arms.

| Family | Horizon | Department | TP A0 → moving / onsets | FA_rate | Precision % | Brier A0 → A3 |
| --- | --- | --- | --- | --- | --- | --- |
| GAM | T+1 | Meta | 35 → 25 / 99 | 1.023 → 0.519 | 33.7 → 41.7 | 0.1273 → 0.1007 |
| GAM | T+1 | Tolima | 34 → 23 / 111 | 1.061 → 0.578 | 21.7 → 25.6 | 0.0852 → 0.0742 |
| LightGBM | T+1 | Meta | 46 → 31 / 99 | 1.023 → 0.623 | 40.0 → 42.5 | 0.1178 → 0.0929 |
| LightGBM | T+1 | Tolima | 49 → 32 / 111 | 1.035 → 0.543 | 29.0 → 33.7 | 0.0802 → 0.0682 |
| XGBoost | T+1 | Meta | 32 → 23 / 99 | 0.801 → 0.504 | 37.2 → 40.4 | 0.1203 → 0.0944 |
| XGBoost | T+1 | Tolima | 45 → 30 / 111 | 0.871 → 0.492 | 30.8 → 34.5 | 0.0820 → 0.0701 |
| GAM | T+2 | Meta | 16 → 13 / 69 | 1.299 → 0.893 | 16.7 → 19.1 | 0.0972 → 0.0843 |
| GAM | T+2 | Tolima | 17 → 11 / 89 | 1.277 → 0.908 | 11.2 → 10.3 | 0.0712 → 0.0666 |
| LightGBM | T+2 | Meta | 29 → 25 / 69 | 1.413 → 0.991 | 25.0 → 29.1 | 0.0954 → 0.0808 |
| LightGBM | T+2 | Tolima | 38 → 22 / 89 | 1.504 → 0.974 | 19.3 → 17.6 | 0.0699 → 0.0636 |
| XGBoost | T+2 | Meta | 25 → 20 / 69 | 1.218 → 0.958 | 25.0 → 25.3 | 0.0959 → 0.0817 |
| XGBoost | T+2 | Tolima | 38 → 28 / 89 | 1.201 → 0.870 | 23.0 → 23.3 | 0.0702 → 0.0640 |

Both departments lose pooled sensitivity in every family/horizon. Global improvements therefore do not meet the territorial guardrail. Loss is uneven: LightGBM T+2 loses **4/69** detections in Meta and **16/89** in Tolima; its pooled Tolima precision also decreases. A pooled burden below one does not establish territorial annual stability.

Annual department detail below uses **A1** (A2/A3 share its decisions). Each entry is **TP/positives; FP; precision %; FA_rate; Brier**. It exposes changing support, burden and calibration by year without averaging away failures.

| Horizon | Year | Department | GAM | LightGBM | XGBoost |
| --- | --- | --- | --- | --- | --- |
| T+1 | 2020 | Meta | 3/26; 6; 33.3; 0.256; 0.0921 | 3/26; 4; 42.9; 0.171; 0.0819 | 4/26; 3; 57.1; 0.128; 0.0827 |
| T+1 | 2020 | Tolima | 8/43; 20; 28.6; 0.632; 0.1089 | 9/43; 12; 42.9; 0.379; 0.1022 | 6/43; 11; 35.3; 0.347; 0.1044 |
| T+1 | 2021 | Meta | 3/24; 7; 30.0; 0.264; 0.0876 | 7/24; 17; 29.2; 0.642; 0.0758 | 4/24; 15; 21.1; 0.566; 0.0783 |
| T+1 | 2021 | Tolima | 3/28; 12; 20.0; 0.273; 0.0757 | 8/28; 27; 22.9; 0.614; 0.0621 | 9/28; 20; 31.0; 0.455; 0.0651 |
| T+1 | 2022 | Meta | 19/49; 22; 46.3; 1.257; 0.2035 | 21/49; 21; 50.0; 1.200; 0.1920 | 15/49; 16; 48.4; 0.914; 0.1965 |
| T+1 | 2022 | Tolima | 12/40; 35; 25.5; 0.870; 0.0753 | 15/40; 24; 38.5; 0.596; 0.0724 | 15/40; 26; 36.6; 0.646; 0.0736 |
| T+1 | 2024 stress | Meta | 6/47; 4; 60.0; 0.223; 0.1534 | 16/47; 6; 72.7; 0.335; 0.1349 | 7/47; 4; 63.6; 0.223; 0.1448 |
| T+1 | 2024 stress | Tolima | 6/56; 12; 33.3; 0.605; 0.1764 | 11/56; 14; 44.0; 0.706; 0.1608 | 8/56; 12; 40.0; 0.605; 0.1670 |
| T+2 | 2020 | Meta | 0/17; 5; 0.0; 0.236; 0.0686 | 2/17; 4; 33.3; 0.189; 0.0655 | 2/17; 5; 28.6; 0.236; 0.0664 |
| T+2 | 2020 | Tolima | 3/34; 8; 27.3; 0.287; 0.0931 | 5/34; 16; 23.8; 0.575; 0.0907 | 8/34; 19; 29.6; 0.683; 0.0911 |
| T+2 | 2021 | Meta | 1/20; 9; 10.0; 0.371; 0.0733 | 4/20; 12; 25.0; 0.495; 0.0699 | 4/20; 12; 25.0; 0.495; 0.0707 |
| T+2 | 2021 | Tolima | 1/25; 16; 5.9; 0.393; 0.0615 | 6/25; 16; 27.3; 0.393; 0.0578 | 8/25; 21; 27.6; 0.516; 0.0587 |
| T+2 | 2022 | Meta | 12/32; 41; 22.6; 2.536; 0.1494 | 19/32; 45; 29.7; 2.784; 0.1476 | 14/32; 42; 25.0; 2.598; 0.1483 |
| T+2 | 2022 | Tolima | 7/30; 72; 8.9; 1.933; 0.0627 | 11/30; 71; 13.4; 1.906; 0.0621 | 12/30; 52; 18.8; 1.396; 0.0623 |
| T+2 | 2024 stress | Meta | 0/27; 0; UNAVAILABLE; 0.000; 0.1145 | 4/27; 18; 18.2; 1.059; 0.1135 | 1/27; 9; 10.0; 0.529; 0.1135 |
| T+2 | 2024 stress | Tolima | 0/34; 0; UNAVAILABLE; 0.000; 0.1359 | 12/34; 25; 32.4; 1.429; 0.1331 | 8/34; 15; 34.8; 0.857; 0.1342 |

In 2022, T+1 aggregate compliance hides Meta FA_rate **1.257** for GAM and **1.200** for LightGBM. Every T+2 moving family exceeds one in both departments that year. Municipal macro sensitivity also declines in affected cuts: LightGBM T+1 in 2020 falls **0.5142 → 0.1773** (A0 → moving), alongside global sensitivity **0.5072 → 0.1739**. This is not merely a change in weighting of large municipalities. Profiles remain `NOT_EVALUABLE`; no unsupported profile explanation is inferred.

## B and C — No empirical method or selector comparison

B0/B1/B2 and C0/C1/C2 have no evaluable cells after A fails. Accordingly:

- **B:** Platt versus isotonic superiority is `UNAVAILABLE`; isotonic was not empirically rejected for lack of classes. The protocol's reference method is already sigmoid, but `B0_B1_identity` is an empty list, so there is no executed B0/B1 identity contrast to claim.
- **C:** C1 versus C0 and C2 versus C0 effects are `UNAVAILABLE`. Positive/negative support in both chronological blocks does not bypass the missing eligible upstream policy. C0 used inside phase A must not be mistaken for an evaluated standalone phase-C arm.

The recorded 72 fits and threshold selections belong to A1–A3; they do not imply that every planned method or decision policy was evaluated.

## D — 2024 descriptive stress, with no selected composition

Every D cell is `NOT_EVALUABLE`: no eligible development A+B+C composition exists. The following are **already-recorded A-factor stress results**, not results of D and not a second opportunity to choose a policy. Operating figures again represent all moving windows; Brier lists A0/A1/A2/A3.

| Family | Horizon | TP A0 → moving / onsets | FP | Alerts | Sensitivity % | Precision % | FA_rate | Brier A0 / A1 / A2 / A3 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GAM | T+1 | 50 → 12 / 103 | 96 → 16 | 146 → 28 | 48.5 → 11.7 | 34.2 → 42.9 | 2.543 → 0.424 | 0.1831 / 0.1655 / 0.1662 / 0.1700 |
| LightGBM | T+1 | 71 → 27 / 103 | 96 → 20 | 167 → 47 | 68.9 → 26.2 | 42.5 → 57.4 | 2.543 → 0.530 | 0.1704 / 0.1485 / 0.1473 / 0.1510 |
| XGBoost | T+1 | 65 → 15 / 103 | 76 → 16 | 141 → 31 | 63.1 → 14.6 | 46.1 → 48.4 | 2.013 → 0.424 | 0.1759 / 0.1565 / 0.1573 / 0.1623 |
| GAM | T+2 | 22 → 0 / 61 | 85 → 0 | 107 → 0 | 36.1 → 0.0 | 20.6 → UNAVAILABLE | 2.464 → 0.000 | 0.1311 / 0.1253 / 0.1267 / 0.1283 |
| LightGBM | T+2 | 27 → 16 / 61 | 78 → 43 | 105 → 59 | 44.3 → 26.2 | 25.7 → 27.1 | 2.261 → 1.246 | 0.1303 / 0.1234 / 0.1230 / 0.1242 |
| XGBoost | T+2 | 23 → 9 / 61 | 54 → 24 | 77 → 33 | 37.7 → 14.8 | 29.9 → 27.3 | 1.565 → 0.696 | 0.1306 / 0.1240 / 0.1242 / 0.1255 |

T+1 stress burden falls below one for all moving families, but detection falls sharply; precision improves while many more onsets are missed. GAM T+2 emits **zero alerts**, missing **all 61 onsets**: precision is `UNAVAILABLE` because its denominator is zero, not zero precision or a successful policy. LightGBM T+2 retains the most moving-window detections within this descriptive stress comparison (**16/61**) but breaches budget (**1.246**); XGBoost respects burden (**0.696**) while detecting **9/61**. These contrasts do not authorize family selection.

The longer-window Brier pattern reverses in stress: A1 beats A3 in all six combinations, while LightGBM's minimum Brier is A2 in both horizons. A3's mean predicted probabilities understate observed stress prevalence: T+1 means are **0.1600/0.1774/0.1554** versus prevalence **0.2274**, and T+2 means are **0.0894/0.0945/0.0916** versus **0.1473** (GAM/LightGBM/XGBoost). Better development calibration does not establish transport to a different prevalence regime. This is descriptive distribution shift, with no causal attribution or confirmatory reuse of 2024.

## Separate T+2 excess controls

Only the frozen A0 excess control is evaluated. The counts and calibration below concern **monthly excess**, with different labels and positive support from onset. Its FA_rate is descriptive; the onset budget is not a criterion for selecting an excess policy.

| Year | Family | TP/positives | FP | Alerts | Sensitivity % | Precision % | FA_rate | Brier | ECE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | GAM | 8/72 | 29 | 37 | 11.1 | 21.6 | 0.592 | 0.1912 | 0.2935 |
| 2020 | LightGBM | 27/72 | 54 | 81 | 37.5 | 33.3 | 1.102 | 0.1760 | 0.2841 |
| 2020 | XGBoost | 17/72 | 22 | 39 | 23.6 | 43.6 | 0.449 | 0.1826 | 0.2923 |
| 2021 | GAM | 5/56 | 20 | 25 | 8.9 | 20.0 | 0.308 | 0.0770 | 0.1033 |
| 2021 | LightGBM | 12/56 | 38 | 50 | 21.4 | 24.0 | 0.585 | 0.0676 | 0.0628 |
| 2021 | XGBoost | 7/56 | 38 | 45 | 12.5 | 15.6 | 0.585 | 0.0710 | 0.0801 |
| 2022 | GAM | 41/101 | 91 | 132 | 40.6 | 31.1 | 1.704 | 0.1437 | 0.1064 |
| 2022 | LightGBM | 44/101 | 71 | 115 | 43.6 | 38.3 | 1.329 | 0.1424 | 0.1054 |
| 2022 | XGBoost | 36/101 | 56 | 92 | 35.6 | 39.1 | 1.048 | 0.1431 | 0.1059 |
| 2024 stress | GAM | 38/119 | 53 | 91 | 31.9 | 41.8 | 1.536 | 0.2165 | 0.1428 |
| 2024 stress | LightGBM | 57/119 | 58 | 115 | 47.9 | 49.6 | 1.681 | 0.2094 | 0.1742 |
| 2024 stress | XGBoost | 49/119 | 59 | 108 | 41.2 | 45.4 | 1.710 | 0.2130 | 0.1624 |

Excess controls share the T+2 row/exposure support reported above, but have 72/56/101/119 positives in 2020/2021/2022/2024. Department detail is **TP/positives; FP; precision %; FA_rate; Brier**, preserving the objective separation:

| Year | Department | GAM | LightGBM | XGBoost |
| --- | --- | --- | --- | --- |
| 2020 | Meta | 0/24; 13; 0.0; 0.614; 0.1882 | 4/24; 16; 20.0; 0.756; 0.1688 | 4/24; 6; 40.0; 0.283; 0.1751 |
| 2020 | Tolima | 8/48; 16; 33.3; 0.575; 0.1934 | 23/48; 38; 37.7; 1.365; 0.1814 | 13/48; 16; 44.8; 0.575; 0.1882 |
| 2021 | Meta | 3/23; 11; 21.4; 0.454; 0.0819 | 2/23; 16; 11.1; 0.660; 0.0741 | 1/23; 15; 6.2; 0.619; 0.0767 |
| 2021 | Tolima | 2/33; 9; 18.2; 0.221; 0.0741 | 10/33; 22; 31.2; 0.541; 0.0637 | 6/33; 23; 20.7; 0.566; 0.0676 |
| 2022 | Meta | 25/54; 38; 39.7; 2.351; 0.2516 | 23/54; 31; 42.6; 1.918; 0.2491 | 19/54; 26; 42.2; 1.608; 0.2507 |
| 2022 | Tolima | 16/47; 53; 23.2; 1.423; 0.0969 | 21/47; 40; 34.4; 1.074; 0.0961 | 17/47; 30; 36.2; 0.805; 0.0964 |
| 2024 stress | Meta | 19/53; 16; 54.3; 0.941; 0.2045 | 26/53; 21; 55.3; 1.235; 0.1994 | 24/53; 24; 50.0; 1.412; 0.2024 |
| 2024 stress | Tolima | 19/66; 37; 33.9; 2.114; 0.2282 | 31/66; 37; 45.6; 2.114; 0.2191 | 25/66; 35; 41.7; 2.000; 0.2233 |

These controls document objective-specific instability; they provide no evidence about an unexecuted moving-window excess intervention. Onset error classes also differ by horizon: T+1 false alerts are all `no_excess`; T+2 includes continuation errors. For example, moving LightGBM T+2 in 2022 partitions its false alerts into **18 continuation** and **98 no-excess** cases; those continuation decisions must not be counted as detected onsets.

## Hypothesis dispositions

| Hypothesis | Scientific disposition | Reason |
| --- | --- | --- |
| H1: joint transport of burden and detection | NOT SUPPORTED by observed development candidates; prescribed D contrast NOT_EVALUABLE | Every A1–A3 candidate fails sensitivity eligibility; T+2 also fails annual burden. No composition exists. |
| H1a: recent moving window better than expanding | NOT_EVALUABLE as stated; partial evidence for moving versus A0 burden/calibration, not joint success | A4 has no OOF origin. A1–A3 reduce burden versus A0 but lose detection; A3 improves pooled development Brier. This is not a moving-versus-expanding result. |
| H1b: calibration method improvement | NOT_EVALUABLE | No B0/B1/B2 evaluation; neither sigmoid superiority nor isotonic failure is established. |
| H1c: robust threshold selection improves transport | NOT_EVALUABLE | No standalone C contrasts; C2 cannot be credited or rejected from phase-A results. |

The bundle itself labels all four hypothesis summaries `DESCRIPTIVE_ONLY`; the dispositions above are this report's interpretation of the frozen criteria, not replacements for the stored classifications. No hypothesis receives an unqualified supported verdict. Partial support concerns specific burden or probability-calibration findings only. Failure of these observed candidates does not establish equivalence or impossibility of every future transport policy.

## Limits and recommended scientific decisions

- **No transport winner:** retain the frozen reference and the unselected state. A3 is the strongest **development probability-calibration configuration** among the tested moving windows; A1–A3 tie on operating decisions. None is a jointly transportable policy. XGBoost T+1 has the smallest pooled moving burden here, but still loses material sensitivity; this is not a family or champion selection.
- **Prioritize the decision frontier in future work:** distinguish loss of ranking/detection from probability-scale correction, and require annual and territorial burden alongside sensitivity. The observed monotone-window equality and T+2 2022 budget drift motivate a future controlled selector investigation. B/C remain open scientific questions; their missing outcomes must not be filled by dropping eligibility after seeing results. Any revised sequential design or margin requires a new authorized protocol.
- **Territorial calibration remains a question for EXP05:** department differences motivate testing it, without proving it will repair the loss. Preserve the frozen predictor/reference and define support and shrinkage rules before a later experiment; do not promote A3 merely for its Brier advantage. This report does not authorize execution.
- **Independent future evidence is required:** development years overlap historically and were used for policy eligibility; they are not independent replications. 2024 is a known stress period, with lower monitored exposure and higher observed prevalence, and cannot choose a window or confirm a claim. A later mature, genuinely unused and authorized period is needed for confirmation; 2025 remains `NOT_EVALUABLE` here.
- **Uncertainty is `UNAVAILABLE`:** the bundle has no approved block-resampling protocol, confidence intervals or p-values. Observed margins are descriptive checks, not a statistical noninferiority result. No significance, causal mechanism, epidemiological effectiveness or real-time lead-time claim follows.
- **Retrospective availability:** consolidated symptom-onset data do not reconstruct what notifications were available at issuance. EXP06 owns that future availability question. Workload here is alert-month burden, not measured staff time, cost or health benefit; those outcomes are `UNAVAILABLE`.
- **Incomplete questions remain visible:** expanding calibration, method and robust-selector effects, composition D, transmission profiles and 2025 have no evaluable evidence in this bundle. No cross-experiment comparison or baseline promotion is made.

## Findings, conclusions and insights

EXP04 demonstrates that **reducing false alerts and improving probability calibration can coexist with a material loss of onset detection**. Longer moving history improves pooled development Brier, but leaves the moving-window alert frontier unchanged and does not preserve that calibration advantage in 2024. T+1 moves within the aggregate annual burden budget by sacrificing sensitivity; T+2 additionally retains severe annual and territorial burden failures. A quiet system, especially the zero-alert GAM stress outcome, is not successful transport.

The scientific outcome is therefore **no eligible calibration-window policy and no selected composition**, with method and robust-threshold hypotheses still unevaluated. Future experiments should address the joint detection–burden frontier and territorial support under a new frozen design, preserving 2024's descriptive role and the current decision boundaries.

G5: NOT_APPROVED

champion: not_selected
