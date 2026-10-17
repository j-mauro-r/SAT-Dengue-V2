# PROD-07 — Draft Prediction Contract

## Status and Purpose

**Document status: CLOSED — Stage 1 product definition, confirmed by Mauricio after PR #7 merge.**
**Human Gate: APPROVED.**  
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

Each completed result is expected to provide municipality-level outputs for two distinct horizons:

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
PredictionResult
├── department
├── reference period T
├── generation date/time
├── model version
└── municipality results[]
    ├── municipality identity
    ├── current observed state/context
    ├── T+1 prediction
    │   ├── target period
    │   ├── probability / risk score
    │   ├── prediction/decision threshold
    │   ├── alert category
    │   └── availability
    ├── T+2 prediction
    │   ├── target period
    │   ├── probability / risk score
    │   ├── prediction/decision threshold
    │   ├── alert category
    │   └── availability
    ├── endemic/epidemiological context
    └── optional supporting information
```

Names, nesting, data types, required/optional fields, enums, precision, serialization, and API transport are **TO BE FROZEN IN LATER STAGE**.

## Draft Field Semantics

| Conceptual field | Business meaning | Maturity |
|---|---|---|
| `department` | Tolima or Meta context to which the result belongs. | Approved geography; encoding not frozen. |
| `reference_period` | Latest loaded/available period T used as the operational cutoff. | Approved concept; representation not frozen. |
| `generated_at` | Date/time when the prediction was produced. | Approved visible traceability concept. |
| `model_version` | Version/identifier of the model artifact. | Approved traceability need; representation not frozen. |
| `municipality_id` | Stable municipality identity. | Required concept; exact identifier TO BE FROZEN. |
| `municipality_name` | Human-readable municipality name. | Required UI concept. |
| `current_state` | Observed epidemiological state at T under the later approved epidemiological definition. | TO BE FROZEN in Stage 2. |
| `current_cases` | Observed case count/context at T when part of the approved product definition. | DRAFT; case definition and aggregation TO BE FROZEN. |
| `horizon` | Identifies T+1 versus T+2. | Approved semantics. |
| `target_period` | Actual future month/year represented by the horizon. | Approved semantics. |
| `risk_probability` | Model-produced or approved calibrated probability/risk score for the target event at that horizon. | DRAFT; calibration semantics TO BE FROZEN. |
| `threshold` | Prediction/decision threshold applicable to that horizon/model version. | DRAFT; value and selection policy TO BE FROZEN after evaluation. |
| `alert_category` | User-facing risk/traffic-light category derived under approved semantics. | Required product output; exact categories/colors TO BE FROZEN. |
| `availability` | Indicates whether a valid prediction exists. If unavailable, a user-understandable reason must be provided under the later contract. | Required product concept; detailed reasons TO BE FROZEN. |
| `event_type` | Onset, continuation, or no outbreak predicted when scientifically valid. | DRAFT; depends on Stage 2 target/current-state definition. |
| `endemic_context` | Approved observed/channel information for contextual interpretation. | DRAFT; method and fields TO BE FROZEN in Stage 2. |
| `supporting_information` | Optional explanation or climatic/context information, subject to later scientific validation. | OPTIONAL DRAFT. |

Internal run identifiers, run origin, checksums, contract versions, and other engineering provenance may be added later for reproducibility. They are not primary Stage 1 product semantics.

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
- uncertainty representation.

No probability value is approved in Stage 1.

## Prediction / Decision Threshold Semantics

The prediction/decision threshold is distinct from epidemiological/endemic-channel case thresholds.

A threshold may differ by horizon, model version, or later approved calibration/decision policy.

The final threshold must be evidence-backed and selected without using unavailable future information.

**TO BE FROZEN IN LATER STAGE:** numeric values, selection rule, recalibration policy, and whether exact threshold values are always user-visible.

## Traffic-Light / Alert Semantics

The dashboard must show an alert level using both color and text. Color alone is insufficient.

At this stage, only the existence of a traffic-light-style alert is approved. The exact number of levels, labels, colors, and probability boundaries are not approved.

Unavailable predictions must never be represented as green/low risk.

## Current State and Event Interpretation

`current_state` belongs to observed epidemiological context at reference period T.

A future excess prediction does not automatically mean outbreak onset. Event interpretation can be frozen only after Stage 2 formally defines excess, onset, continuation, and current state.

## Optional Supporting Information

Explanation and climatic/context information are optional supporting information, subject to later scientific validation. They must not be treated as causal evidence or as mandatory Stage 1 output semantics.

## Traceability Requirements

A displayed prediction must be traceable at product level to at least:

- department and municipality;
- reference period;
- target period/horizon;
- model version;
- generation date/time.

Additional technical provenance belongs to later engineering contracts.

## Availability and Missing Results

The contract must distinguish only two product-level conditions at this stage:

- **valid prediction**;
- **unavailable prediction**.

When unavailable, the final contract must provide a user-understandable reason. The exact reason taxonomy is **TO BE FROZEN IN LATER STAGE**.

## Draft Invariants

1. Every valid prediction belongs to one municipality, one reference period, and one horizon.
2. Every valid horizon result identifies its actual target period.
3. Observed state at T and future prediction remain semantically separate.
4. A missing prediction cannot be represented as probability `0`, threshold failure, or green/low risk.
5. Alert category, probability, and threshold shown together must come from the same approved model context.
6. The UI must not invent or recalculate scientific values absent from the contract.
7. T+1 and T+2 are independent outputs.
8. No field in this draft implies autonomous intervention or guaranteed outbreak prevention.

## Open Decisions and Later Freeze

- **OPEN DECISION:** exact traffic-light categories and human-readable labels.
- **OPEN DECISION:** whether exact prediction/decision threshold values are always visible to the primary user.
- **TO BE FROZEN IN LATER STAGE:** formal target/excess/onset/continuation semantics.
- **TO BE FROZEN IN LATER STAGE:** probability calibration and threshold-selection method.
- **TO BE FROZEN IN LATER STAGE:** uncertainty representation.
- **TO BE FROZEN IN LATER STAGE:** detailed availability reasons.
- **TO BE FROZEN IN LATER STAGE:** optional supporting information semantics.
- **TO BE FROZEN IN LATER STAGE:** exact schema, types, endpoint representation, versioning, compatibility rules, and technical provenance.

This document is explicitly a **DRAFT** and must not be used as a frozen implementation contract.
