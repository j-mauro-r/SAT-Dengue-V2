# PROD-07 — Draft Prediction Contract

## Status and Purpose

**Document status: DRAFT — Phase E.**
**Human Gate: UNAPPROVED.**
**Contract maturity: DRAFT PRODUCT/MODEL CONTRACT — NOT FROZEN.**

This document defines the initial business semantics of prediction output required by SAT-Dengue V2. It is intentionally incomplete and must not be treated as the final API, storage, or model schema.

The final Prediction Contract will be frozen only in Stage 6, after Data & Target Freeze, model evaluation, calibration, threshold selection, and Champion approval.

Related product sources:

- [PROD-03](PROD-03-supported-decisions.md): supported human decision.
- [PROD-04](PROD-04-dashboard-master-user-story.md): dashboard behavior.
- [PROD-06](PROD-06-ui-information.md): UI information requirements.
- [Contract lifecycle](../../contracts/contract-lifecycle.md): contract maturity and freeze order.

## Approved Business Semantics

A valid prediction represents a **predictive risk estimate** for dengue excess/outbreak-related risk at a future horizon. It is not certainty and does not autonomously prescribe a public-health action.

Each completed run is expected to provide municipality-level results for two distinct horizons:

- **T+1:** the month immediately following reference period T.
- **T+2:** the second month following reference period T.

The output must preserve the distinction between:

- observed/current state at T;
- predicted future risk at T+1;
- predicted future risk at T+2.

The product must not describe prediction generation as “performing a regression.”

## Conceptual Output Envelope

The following is a conceptual information structure, not a frozen JSON schema:

```text
PredictionRun
├── run identity and provenance
├── department
├── reference period T
├── generation metadata
├── model identity
└── municipality results[]
    ├── municipality identity
    ├── current observed state/context
    ├── T+1 prediction
    │   ├── target period
    │   ├── probability / risk score
    │   ├── applicable threshold
    │   ├── alert category
    │   ├── availability state
    │   └── event interpretation, when valid
    ├── T+2 prediction
    │   ├── target period
    │   ├── probability / risk score
    │   ├── applicable threshold
    │   ├── alert category
    │   ├── availability state
    │   └── event interpretation, when valid
    ├── epidemiological context
    └── explanation/context, when scientifically valid
```

Names, nesting, data types, required/optional fields, enums, precision, serialization, and API transport are **TO BE FROZEN IN LATER STAGE**.

## Draft Field Semantics

| Conceptual field | Business meaning | Maturity |
|---|---|---|
| `run_id` | Unique identity of the persisted prediction run for audit/retrieval. | DRAFT; format not frozen. |
| `run_origin` | Distinguishes operational user-triggered processing from historical/model-training results when those are surfaced. | DRAFT product requirement from PROD-04. |
| `department` | Tolima or Meta context to which the run belongs. | Approved geography; encoding not frozen. |
| `reference_period` | Latest loaded/available period T used as the operational cutoff for the run. | Approved concept; representation not frozen. |
| `generated_at` | Date/time when the prediction run was produced. | Approved traceability concept. |
| `model_name` | Model identity used to produce the run. | DRAFT field; final naming governed later. |
| `model_version` | Version/identifier of the model artifact. | Approved traceability need; representation not frozen. |
| `municipality_id` | Stable municipality identity. | Required concept; exact code field TO BE FROZEN. |
| `municipality_name` | Human-readable municipality name. | Required UI concept. |
| `current_state` | Observed epidemiological state at T under the later approved epidemiological definition. | TO BE FROZEN in Stage 2. |
| `current_cases` | Observed case count/context at T when part of the approved product definition. | DRAFT; case definition and aggregation TO BE FROZEN. |
| `horizon` | Identifies T+1 versus T+2. | Approved semantics. |
| `target_period` | Actual future month/year represented by the horizon. | Approved semantics. |
| `risk_probability` | Model-produced or approved calibrated probability/risk score for the target event at that horizon. | DRAFT; calibration semantics TO BE FROZEN. |
| `threshold` | Operational predictive threshold applicable to that horizon/model version. | DRAFT; value and selection policy TO BE FROZEN after evaluation. |
| `alert_category` | User-facing risk/traffic-light category derived under approved semantics. | Required product output; exact categories/colors TO BE FROZEN. |
| `availability_state` | Indicates whether a valid prediction exists or why it does not. | Required product concept; enum TO BE FROZEN. |
| `event_type` | Onset, continuation, or no outbreak predicted when scientifically valid. | DRAFT; depends on Stage 2 target/current-state definition. |
| `explanation` | Scientifically valid factors/attributions associated with the prediction. | OPTIONAL DRAFT; method TO BE FROZEN after model evaluation. |
| `climate_context` | Relevant climatic context where operationally timely and scientifically useful. | OPTIONAL DRAFT; exact variables TO BE FROZEN. |
| `endemic_context` | Approved observed/channel information for contextual interpretation. | DRAFT; method and fields TO BE FROZEN in Stage 2. |

## Horizon Semantics

T+1 and T+2 are independent prediction outputs tied to the same reference period T. The product must not assume that:

- T+2 probability must be greater than or less than T+1;
- both horizons share the same threshold;
- both horizons have the same calibration method;
- a missing T+2 result implies low risk;
- a predicted excess automatically means a new outbreak onset.

Each horizon must identify its actual target period.

## Probability / Risk Score Semantics

A probability or risk score shown to the user must originate from the approved model/calibration pipeline. The UI must not recompute it.

**TO BE FROZEN IN LATER STAGE:**

- whether the product exposes a calibrated probability in `[0,1]`, percentage form, or both;
- calibration method;
- precision/rounding;
- uncertainty representation;
- minimum evidence required before probability is considered operationally interpretable.

No probability value is approved in Stage 1.

## Threshold Semantics

The prediction threshold is distinct from epidemiological/endemic-channel case thresholds.

A predictive threshold may differ by:

- horizon;
- model version;
- later approved calibration/decision policy.

The final threshold must be evidence-backed and selected without using unavailable future information.

**TO BE FROZEN IN LATER STAGE:** numeric values, selection rule, stability/recalibration policy, and whether exact threshold values are always user-visible.

## Traffic-Light / Alert Semantics

The dashboard must show an alert level using both color and text. Color alone is insufficient.

At this stage, only the existence of a traffic-light-style alert is approved. The exact number of levels, labels, colors, and probability boundaries are not approved.

A valid final design must also represent conditions that are not risk levels, such as:

- unavailable prediction;
- insufficient data;
- municipality ineligible under later rules;
- processing/contract inconsistency.

These states must not be represented as green/low risk.

## Current State and Event Interpretation

`current_state` belongs to observed epidemiological context at reference period T.

`event_type` may eventually distinguish:

- `ONSET` — predicted future excess when current state is not already in the later-defined excess/boutbreak state;
- `CONTINUATION` — predicted future excess while current state is already in that state;
- `NO_OUTBREAK_PREDICTED` — later-approved interpretation when future prediction is below the relevant rule.

These labels are **DRAFT SEMANTICS ONLY**. They cannot be frozen before Stage 2 formally defines excess, outbreak onset, continuation, and current state.

## Explanation Semantics

Explanation is supporting information, not a causal claim.

If the final model supports valid explainability, the contract may expose:

- top contributing variables/features;
- contribution direction/sign where meaningful;
- explanation method/version;
- scope of explanation (local versus global).

The product must not state that a feature “caused” the predicted dengue risk merely because an attribution method assigns it importance.

**TO BE FROZEN IN LATER STAGE:** whether explanations are mandatory, method used, number of factors, units, and user-facing wording.

## Traceability Requirements

A displayed prediction must be traceable to at least:

- reference period;
- department and municipality;
- target period/horizon;
- model identity/version;
- generation time;
- run identity;
- origin of the run where historical/model-training results are exposed.

Later engineering contracts should additionally preserve contract/data/model versions and checksums where needed for reproducibility, but exact technical provenance fields are not frozen here.

## Availability and Missing Results

The contract must distinguish a valid low-risk prediction from absence of a valid prediction.

A municipality/horizon may be unavailable because of later-defined reasons such as:

- insufficient history;
- missing required data;
- failed validation;
- ineligible municipality;
- inference failure;
- model/contract incompatibility.

The exact reason taxonomy is **TO BE FROZEN IN LATER STAGE**.

## Draft Invariants

1. Every valid prediction belongs to one municipality, one reference period, and one horizon.
2. Every valid horizon result identifies its actual target period.
3. Observed state at T and future prediction must remain semantically separate.
4. A missing prediction cannot be represented as probability `0`, threshold failure, or green/low risk.
5. Alert category, probability, and threshold shown together must come from the same approved model/run context.
6. The UI must not invent or recalculate scientific values absent from the contract.
7. Historical/model-training results must retain their true periods and be visibly distinguishable from current operational runs.
8. No field in this draft implies autonomous intervention or guaranteed outbreak prevention.

## Open Decisions and Later Freeze

- **OPEN DECISION:** exact traffic-light categories and human-readable labels.
- **OPEN DECISION:** whether exact threshold values are always visible to the primary user.
- **TO BE FROZEN IN LATER STAGE:** formal target/excess/onset/continuation semantics.
- **TO BE FROZEN IN LATER STAGE:** probability calibration and threshold-selection method.
- **TO BE FROZEN IN LATER STAGE:** uncertainty representation.
- **TO BE FROZEN IN LATER STAGE:** final availability/error enums.
- **TO BE FROZEN IN LATER STAGE:** explainability method and fields.
- **TO BE FROZEN IN LATER STAGE:** exact schema, types, endpoint representation, versioning, and compatibility rules.

This document is explicitly a **DRAFT** and must not be used as a frozen implementation contract.