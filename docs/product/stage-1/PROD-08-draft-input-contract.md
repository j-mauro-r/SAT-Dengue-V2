# PROD-08 — Draft Input Contract

## Status and Purpose

**Document status: CLOSSED — Phase F.**  
**Human Gate: APPROVED.**  
**Contract maturity: DRAFT PRODUCT/DATA CONTRACT — NOT FROZEN.**

This document defines the initial product-facing input expectations for loading a new monthly departmental period. It intentionally does not freeze the final schema, exact variable list, file format, or detailed operational validation rules.

The final Input Contract will be frozen only after Stage 2 Data Understanding, target definition, operational availability analysis, and later product-contract reconciliation.

Related sources:

- [PROD-05](PROD-05-new-period-flow.md): upload, validation, inference, result, and persistence flow.
- [PROD-06](PROD-06-ui-information.md): information required by the interface.
- [PROD-07](PROD-07-draft-prediction-contract.md): conceptual output semantics.
- [Contract lifecycle](../../contracts/contract-lifecycle.md): staged contract maturity.

## Approved Product Direction

The expected operational loading unit is one departmental file for either Tolima or Meta containing information for multiple municipalities for a new monthly period.

The file provides information available at the close of the latest period T so SAT-Dengue can perform predictive inference for T+1 and T+2.

The exact input variables are **not frozen**. They depend on:

- final model requirements;
- operational data availability at inference time;
- what is supplied through the departmental monthly file;
- what SAT-Dengue can derive from historical/reference data;
- information required by the dashboard and prediction contract.

No field should be required merely because it existed in SAT-Dengue V1.

## Input Responsibility Model

The draft contract distinguishes four categories.

### A. User-supplied monthly data

The departmental file contains the minimum operational information required for the new reference period T.

Potential examples to evaluate later include:

- municipality identifier;
- reference year/month;
- observed dengue information for the closed period;
- other epidemiological values demonstrated to be available at that cutoff.

These are examples, not approved mandatory columns.

### B. System reference data

SAT-Dengue should centrally control reference information when feasible, such as:

- municipality master data;
- department-municipality association;
- stable territorial identifiers;
- static or slowly changing reference metadata.

### C. System-derived data

SAT-Dengue should generate reproducible derived information internally when it can do so reliably, including, when later approved:

- temporal features;
- lags;
- rolling windows;
- target periods;
- endemic-channel values;
- current-state indicators;
- other model features derived from accepted historical/input data.

The user should not be required to calculate internal feature-engineering values such as lags or rolling windows when SAT-Dengue can derive them reproducibly.

### D. System-obtained external data

SAT-Dengue may obtain data from controlled external sources when operational timing and reproducibility support that design.

Possible examples include climatic/environmental variables.

**OPEN DECISION:** final responsibility split between user-supplied monthly fields and system-obtained external data.

## Conceptual Input Envelope

This is an information model, not a frozen CSV/Excel/JSON schema:

```text
MonthlyDepartmentInput
├── department identity
├── reference period T
└── municipality records[]
    ├── municipality identity
    └── user-supplied monthly observations
```

The final inference dataset may contain additional historical, derived, reference, or externally obtained features that are not expected to appear in the user-uploaded file.

## Candidate Field Classes

| Field class | Example business meaning | Expected responsibility | Maturity |
|---|---|---|---|
| Department identity | Tolima or Meta | USER or SYSTEM context | Required concept; encoding TO BE FROZEN. |
| Reference period | Closed month/year T | USER-supplied or inferred under approved rule | Required concept; format TO BE FROZEN. |
| Municipality identity | Stable municipality code/name | USER + REFERENCE DATA reconciliation | Required concept; identifier TO BE FROZEN. |
| Observed dengue measure(s) | Epidemiological information available for municipality at T | Likely USER/SOURCE input | Exact case/event definition TO BE FROZEN. |
| Historical context | Prior periods needed by model | SYSTEM history | Should not require repeated full-history upload unless later justified. |
| Derived temporal/model features | Lags, rolling windows, target periods, approved derived indicators | SYSTEM | Exact rules TO BE FROZEN later. |
| Endemic-channel inputs/results | Historical/context information required by the approved method | SYSTEM/DATA pipeline | Exact method TO BE FROZEN in Stage 2. |
| Climatic/environmental values | Operationally available external/context variables | EXTERNAL/SYSTEM or USER if later justified | Responsibility and variables OPEN DECISION. |
| Population/reference denominators | Stable or period-specific denominators if later required | REFERENCE/EXTERNAL | Only if scientifically required. |

## Core Validation Areas

Before inference, the input must be validated across four product-level areas:

### 1. File structure

The file must be readable and contain the required conceptual information in an accepted structure.

Exact format, encoding, column names, data types, and sheet/tab rules are **TO BE FROZEN IN LATER STAGE**.

### 2. Municipality and period

The system must be able to reconcile each record with the active Tolima or Meta context and a valid reference period T.

The input must not silently mix a municipality from another department or use future information beyond the approved inference cutoff.

### 3. Required data

The data required for the final model and approved product context must be present or obtainable through controlled system sources.

Missing required observations must not be silently converted to zero or to a low-risk prediction.

### 4. Eligibility for inference

A structurally valid record may still be unavailable for prediction if it does not satisfy later-approved scientific or data-quality eligibility rules.

Eligibility rules belong to Stage 2 and later contracts.

## Department and Municipality Coverage

The operational file is departmental and may contain multiple municipalities.

The geographic product scope includes municipalities in Tolima or Meta, but valid predictive coverage may be narrower according to later eligibility, history, and data-quality rules.

**OPEN DECISION:** whether every municipality in the active department must appear in each monthly file or whether missing municipalities are allowed and represented as unavailable.

## Temporal Rules

The input represents one intended reference period T and must use only information that was available by the approved cutoff for that period.

The exact date representation, source publication lags, and cutoff rules are **TO BE FROZEN IN LATER STAGE**.

Historical corrections, backfills, resubmission workflows, and detailed partial-processing policies are outside this Stage 1 contract.

A repeated period must not silently overwrite previously persisted data or results.

## Error Semantics

At Stage 1, the product only needs to distinguish:

- **blocking input problem:** inference must not start because the file or required data cannot be safely interpreted;
- **unavailable municipality prediction:** the file may be structurally valid, but that municipality cannot produce a valid prediction under later-approved eligibility rules;
- **warning:** the input remains processable, but the user should be informed of a non-blocking condition.

Detailed error codes, transport semantics, dependency failures, and support diagnostics belong to later implementation/API contracts.

## Invalid Values Must Not Become Predictions

The system must not silently:

- coerce unknown municipalities into valid ones;
- replace missing required observations with zero unless an approved data rule explicitly defines zero as correct;
- use future information to complete the current period;
- infer a low-risk result from missing data;
- accept conflicting duplicate records by arbitrary row order.

Any imputation or correction affecting scientific inputs must be governed by later data-engineering rules and reproducible evidence.

## Draft Input Invariants

1. One processing attempt belongs to one department context.
2. The input represents one intended reference period T.
3. Every municipality record must be reconcilable to a controlled municipality identity before inference.
4. User-supplied data must reflect information available by the approved cutoff.
5. Blocking input problems prevent inference.
6. Missing or invalid input must not be translated into low risk.
7. Derived features should be generated by SAT-Dengue when reproducible rather than manually calculated by the user.
8. The model feature vector is not equivalent to the user-upload schema.
9. A repeated period must not silently overwrite persisted data or results.

## Open Decisions and Later Freeze

- **OPEN DECISION:** exact fields required in the departmental monthly file.
- **OPEN DECISION:** which climatic/environmental variables, if any, are user-supplied versus system-obtained.
- **OPEN DECISION:** whether all municipalities must be present in each departmental file.
- **TO BE FROZEN IN LATER STAGE:** final case/event definitions and units.
- **TO BE FROZEN IN LATER STAGE:** accepted file format, encoding, exact column names, and data types.
- **TO BE FROZEN IN LATER STAGE:** operational availability cutoff for each data source.
- **TO BE FROZEN IN LATER STAGE:** final data schema, feature derivation rules, validation details, and model compatibility rules.

This document is explicitly a **DRAFT** and must not be used as a frozen ingestion or API implementation contract.
