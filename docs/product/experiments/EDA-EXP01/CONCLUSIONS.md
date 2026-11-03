# EDA-EXP01 — conclusions and research priority

**Completed with limitations.** Existing results support several interacting
constraints, without establishing a unique causal explanation of SAT-Dengue's
limitations. [Eight quantified findings](FINDINGS.md) distinguish new descriptive
calculations from corroborated historical results. G5 remains `NOT_APPROVED`;
`champion: not_selected`.

## 1. Is discrimination insufficient?

There is useful signal and incomplete separation. G0_OFF annual onset AUROC is
0.775–0.830 at T+1 and 0.713–0.763 at T+2; true/false outcomes overlap within
each annual procedure. All four predictors jointly miss 32/89 and 29/62 onsets
in 2022. DELTA also found no admissible scalar-threshold policy in two required
historical cells. These facts justify investigating limited local separability,
especially T+2/2022, but do not prove that every policy or predictor would fail.
AP variation also reflects prevalence. No new model is selected.

## 2. What is known about calibration and temporal transport?

Calibration in the large changes sign: G0_OFF overpredicts 2022 onset frequency
by 11.19/7.81 pp and underpredicts 2024 by 12.26/7.53 pp. Annual model/calibrator
identities differ; this is not a clean fixed-model drift experiment. T+1/2022
has the highest AUROC despite failure of the academic margin. DELTA's fixed P1
selection policy transports C in only three of six available cells, with two
mandatory policies absent. Its complete primary comparison remains `NO_EVALUABLE`.
Neither a new calibration method nor a stricter threshold is automatically justified:
EXP04 and BETA03 already document detection costs under their separate protocols.

## 3. How much of the territorial difference relates to prevalence?

For pooled T+1 G0_OFF, the Tolima−Meta excess-FAR gap is 13.94 pp. A symmetric
three-factor accounting decomposition attributes +9.28 pp to prevalence, +3.98
to excess sensitivity and +0.68 to FPR. At a common 11.80% prevalence, FARs become
52.58%/57.27%, leaving 4.69 pp. The decomposition and standardization are different
accounting summaries, not interchangeable causal percentages.

At T+2 the observed +1.95 pp gap reverses to −4.28 pp at common excess prevalence.
Tolima's lower prevalence offsets its better pooled excess sensitivity/FPR.
Thus a general claim of inferior Tolima prediction is unsupported. Annual controls
and DELTA's differing departmental responses further limit pooled interpretations.

## 4. Do transmission profiles differ with sufficient support?

This cannot be established: the admitted sources have no temporally validated
transmission classification. Departments describe geography, not validated profiles.
Municipal rates vary, but 273/300 T+1 and 294/298 T+2 municipality-years have fewer
than three onsets. Median Wilson sensitivity/FAR reference widths are 79.35 pp
among defined rates, even before accounting for dependence. This is insufficient
support for selecting municipal thresholds. A future historically defined grouping
could be investigated only with its own source, temporal validity and support audit;
no grouping is constructed from these evaluation errors.

## 5. What do near-P75 errors reveal?

They expose shared ambiguity, not a validated correction rule. At T+1,
107/118 model-only false alerts and 62/71 model-only true detections are within
one case of target P75. P75=0 and equality also occur in both groups. EXP02's
documented H5/H9 sensitivity shows label identity can change substantially, but
does not establish H5 error or validate a different epidemiological target.
H5, boundary observations and all municipalities remain unchanged.

## 6. Which hypothesis should come next?

**Priority hypothesis:** limited local onset separation, together with changing
epidemiological composition, constrains transport of the academic alert margin
across periods. This has more support than a claim that a new global threshold,
calibrator or municipal policy alone will resolve the problem. The evidence does
not identify one intervention with a demonstrated expected gain.

The immediate decision is to define an independent evaluation opportunity and
adequate historically fixed strata before choosing an intervention. Any later
experiment needs separate human authorization and a predeclared protocol. These
consumed years cannot supply independent confirmation. No automatic EXP-DELTA02
recommendation or execution follows from this analysis.

| Priority / possible research line | Evidence | Main uncertainty | Potential improvement | Complexity / prerequisite |
| --- | --- | --- | --- | --- |
| 1. Joint audit of local ranking, composition and decision transport in independent periods | Annual score overlap, shared misses, calibration sign changes, 3/6 P1 transport, exact territorial decomposition | Cannot separate composition, procedure effects, reporting availability and H5 validity here | Could identify the component worth intervening on; gain unquantified | Moderate analytical complexity; requires independent period and temporal provenance |
| 2. Probability-calibration transport under a fixed predeclared decision criterion | Large calibration gaps; EXP04's calibration/detection trade-off | Recalibration may lose detections without improving margin | Plausible conditional benefit; no established joint improvement | Moderate; freeze objective and independent evaluation before any fitting |
| 3. Additional discriminative information, particularly T+2 | Lower T+2 AUROC and shared missed onsets; EXP03 information effects are conditional | Unknown availability and incremental signal | Potentially useful, magnitude unknown | High; separate data/protocol approval, no evaluation-led feature search |
| 4. Policy by historically validated transmission profile | Departmental differences and prevalence accounting | No valid classification; sparse events and intervals | Speculative; pooled differences do not establish benefit | High support burden; historical grouping and independent evaluation required |
| 5. New global scalar threshold on the same scores | DELTA tested this family; two cells infeasible and T+1 detection losses | Alternative constraint/policy would change the scientific question | Unsupported as a general remedy | Low computation, high risk of recycling evaluation evidence |
| 6. Revise H5 or filter small-P75 alerts | EXP02 sensitivity; boundary features shared by errors/successes | No external outbreak truth; true detections may be removed | Unknown and unvalidated | High scientific complexity; external adjudication and separate approval required |

The ordering reflects evidential support and unmet prerequisites, not numerical
confidence scores or a forecast of improvement. No statistical superiority,
causal effect, prospective performance or sanitary efficacy is established.

## Limits of the decision

Only 2020/2021/2022/2024 frozen Meta–Tolima cohorts are analyzed: 2,653/313 and
2,422/219 observations/onsets. 2024 is consumed stress, and 2025 is excluded and
already consumed elsewhere. Historical consolidated data do not establish
availability at forecast origin. Different annual model identities, changing
eligibility and shared temporal shocks confound simple drift explanations.
Wilson intervals are descriptive binomial references; no defensible independent
temporal uncertainty is manufactured by resampling municipalities. Historical
EXP03/EXP04/BETA summaries are context, not additional paired replications.

The contribution of EDA-EXP01 is a more precise evidential diagnosis, particularly
prevalence accounting and municipal support, while preserving every prior result
and all scientific approval boundaries.
