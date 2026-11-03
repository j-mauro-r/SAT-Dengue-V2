# EXP-DELTA02 — frozen spatial admission and conditional experiment

Frozen 2026-11-03 before topology, neighbor-signal calculation or fitting.
Authority: Mauricio's explicit EXP-DELTA02 request. Base: updated `main` containing
merged PR #75; branch `experiment/EXP-DELTA02`. This bounded request is executed
directly, with this two-stage scientific contract rather than a new DWP lifecycle.

## Hypothesis and fixed scope

One scalar of recent neighboring municipalities' dengue notifications may improve
G0_OFF's T+1 onset detection under the [academic contract](../contrato.md).
Retain all 76 Meta/Tolima municipalities, H5, P75, non-excess at origin and known
outcomes. Future labels are outcomes only. No T+2, new EDA, alternative hypothesis,
new model family, champion selection or G5 approval is authorized.

## Stage 1: admission before any signal or fit

1. Pin the existing national canonical publication, regional inventory, benchmark
   and EDA-EXP02 admission receipt; verify their payload hashes. Never replace them.
2. Inspect official DANE municipal geometry, starting with MGN Integrado 2018;
   inspect official alternative vintages and documentation to resolve historical
   applicability. Capture raw responses, URLs, access date, schema and hashes.
3. Require unique five-character DIVIPOLA codes for the 76 targets and potential
   neighbors nationwide, including outside both departments. Code agreement and
   a release/vintage label alone do not establish valid-time correspondence.
4. Audit polygon validity, positive area, shared edges, point-only contacts,
   overlaps and changes in target-neighbor membership across available vintages.
   A neighbor must share a boundary of strictly positive length; point contact
   and self-contact are excluded. No correlation/outcome-based selection.
   No snapping, buffering, geometry repair, distance or departmental substitute
   is admitted to hide ambiguities. Cross-vintage differences require resolution
   against historical territorial evidence, not an assumption of stability.
5. Verify canonical municipality-month uniqueness, periods, notification-count
   coverage and zero semantics. Distinguish missing/unknown reporting from zero.
   Neighbor-specific coverage cannot pass until the graph passes admission.

`FEASIBLE` permits Stage 2; `FEASIBLE_WITH_LIMITATIONS` also permits Stage 2 only
when historical relations and absence of future information remain defensible.
Late publication is an operational-availability limitation, not by itself proof
of historical invalidity. Unresolved historical graph/topology ambiguity yields
`NOT_EVALUABLE`, closes the experiment, and prohibits signal construction and
training. A partial graph or an easier municipal subset cannot bypass that gate.

## Stage 2: conditional specification

The sole proposed feature is the arithmetic mean of general-dengue monthly
notifications across all admitted neighbors at exact T−1. Exclude the target;
divide by neighbor count. Require admissible observations for every neighbor;
retain missing otherwise, including zeros without demonstrated coverage. Never
fill unknown coverage with zero or silently change the neighbor denominator.
Counts measure notification volume, not population-standardized risk. No
correction is selected at this freeze; any material comparability correction
must be justified and recorded once before fitting, without evaluating variants.
The EDA's earlier log1p proposal is historical context, not this experiment's
feature definition. No feature is constructed during Stage 1.

Use BETA01's G0_OFF epidemiological predictors, categorical preprocessing,
XGBoost configuration (80 trees, depth 2, learning rate 0.05), global calibration,
embargos and deterministic policy-selection procedure. The only added predictor
is the spatial scalar. Preserve the unused adaptation-year gap; do not introduce
local adaptation. For target year Y: fit through Y−4, calibrate Y−3, retain Y−2
gap, select policy in Y−1 and evaluate Y. Exact inherited implementation and
input identities must be pinned before any conditional fit. No search or change
to the selection objective; academic metrics assess the resulting decisions.
CHANNEL, PERSISTENCE, R0 and original G0_OFF predictions stay frozen.

Use 2020/2021/2022/2024 only as a retrospective exploratory paired comparison;
these and 2025 are consumed. No independent period is claimed. Report original
and exactly matched cohorts, missing-feature coverage and all lost keys. Do not
compare unmatched denominators or remove difficult municipalities.

## Metrics and disposition

Report true/detected/missed onsets, sensitivity, alerts, false excess alerts,
FAR-excess, difference from CHANNEL in percentage points, false onset alerts,
FA per eligible municipality-year, paired gained/lost detections and false
alerts, and AP/Brier when probabilities are comparable. Retain pooled, annual,
departmental and year-by-department counts. FAR is undefined with no alerts.

A: candidate detects more onsets than CHANNEL. B: more than PERSISTENCE.
C: candidate FAR-excess ≤ CHANNEL FAR-excess + 0.05. Require all three jointly;
historical pooled controls (94/313, 47.49%; G0_OFF 146/313, 55.08%) reconcile
sources and never select a threshold. Report temporal/territorial harms even
with pooled compliance. Classify `EXPLORATORY_IMPROVEMENT`, `NOT_SUPPORTED` or
`NOT_EVALUABLE`; execution may be `COMPLETED_WITH_LIMITATIONS` alongside that
scientific disposition. No fictional candidate metrics after a Stage 1 stop.

## Evidence and validation

Keep private municipal rows and geography audit exports under identified ignored
`data/processed/exp_delta02/` publications using the existing atomic publisher.
Record source/code/protocol/package hashes, deterministic recomputation and
preservation checks. Commit aggregate findings and provenance only. Validate the
actual touched surface under the [testing guide](../../../TESTING_GUIDE.md),
including code integrity, exact keys, missingness and fail-closed admission.
Only if Stage 2 is admitted, add temporal-prefix/self-exclusion, cohort/label,
role, metric and deterministic model checks. Blocked checks are not passes.
Open the separate PR to `main` without merging; independent review and required
CI remain integration gates.
