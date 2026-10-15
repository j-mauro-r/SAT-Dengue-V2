# PROD-08 — Draft Input Contract

## Status and Purpose

**Document status: DRAFT — Phase F.**
**Human Gate: UNAPPROVED.**
**Contract maturity: DRAFT PRODUCT/DATA CONTRACT — NOT FROZEN.**

This document defines the initial product-facing input expectations for loading a new monthly departmental period. It intentionally does not freeze the final schema, exact variable list, file format, or data-quality thresholds.

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
- what the user can realistically supply;
- what SAT-Dengue can derive from historical/reference data;
- information required by the dashboard and prediction contract.

No field should be required merely because it existed in SAT-Dengue V1.

## Input Responsibility Model

A useful Input Contract must distinguish four categories.

### A. User-supplied monthly fields

Information that the departmental user or their operational process can realistically include in the monthly file.

Potential examples to evaluate later include:

- municipality identifier;
- reference year/month;
- observed dengue information for the closed period;
- other epidemiological values demonstrably available at that cutoff.

These are examples, not approved mandatory columns.

### B. System reference data

Information SAT-Dengue should preferably control centrally instead of asking the user to repeat it in every upload, when feasible:

- municipality master data;
- department-municipality association;
- stable territorial identifiers;
- static or slowly changing reference metadata.

### C. System-derived fields

Information that can be generated reproducibly from accepted source data and prior periods:

- temporal features;
- lags;
- rolling windows;
- target periods;
- endemic-channel values;
- current-state indicators;
- other approved derived features.

The final rules belong to later data/feature contracts.

### D. System-obtained external fields

Information SAT-Dengue may retrieve or prepare from controlled external sources rather than requiring the user to upload it, if operational timing and reproducibility support that design.

Possible examples include climatic/environmental variables.

**OPEN DECISION:** which variables, if any, must be supplied by the user versus obtained automatically by SAT-Dengue.

## Conceptual Input Envelope

This is an information model, not a frozen CSV/Excel/JSON schema:

```text
MonthlyDepartmentInput
├── department identity
├── reference period T
├── file/source metadata
└── municipality records[]
    ├── municipality identity
    ├── user-supplied observations
    └── optional/source-specific information
```

The final inference dataset may contain many additional derived or externally obtained features that are not expected to appear in the user-uploaded file.

## Candidate Field Classes

| Field class | Example business meaning | Expected responsibility | Maturity |
|---|---|---|---|
| Department identity | Tolima or Meta | USER or SYSTEM context | Required concept; encoding TO BE FROZEN. |
| Reference period | Closed month/year T | USER-supplied or inferred under approved rule | Required concept; format TO BE FROZEN. |
| Municipality identity | Stable municipality code/name | USER + REFERENCE DATA reconciliation | Required concept; identifier TO BE FROZEN. |
| Observed dengue measure(s) | Epidemiological information available for municipality at T | Likely USER/SOURCE input | Exact case/event definition TO BE FROZEN. |
| Historical context | Prior periods needed by model | SYSTEM history | Must not require repeated full-history upload unless justified later. |
| Endemic-channel inputs | Historical values required to compute approved channel | SYSTEM/DATA pipeline | Exact method TO BE FROZEN in Stage 2. |
| Climatic/environmental values | Operationally available climate context/features | USER or EXTERNAL/SYSTEM | Responsibility and variables OPEN DECISION. |
| Population/reference denominators | Stable or period-specific denominators if later required | REFERENCE/EXTERNAL | Only if scientifically required. |
| Source/version metadata | Origin or version of loaded data where needed for traceability | SYSTEM and/or USER | Exact fields TO BE FROZEN. |

## User-Supplied Data Principle

The user should supply only information that:

1. is operationally available at the end of period T;
2. can reasonably be produced by the departmental workflow;
3. is necessary and cannot be obtained more reliably by SAT-Dengue elsewhere;
4. has a clear definition the user can follow;
5. can be validated before inference.

The contract should avoid exposing internal model feature engineering as an upload burden. For example, if the model needs lags or rolling windows that SAT-Dengue can derive from retained history, the user should not normally be required to calculate those values manually.

## Department and Municipality Coverage

The operational file is departmental and may contain multiple municipalities.

The geographic product scope includes municipalities in Tolima or Meta, but valid predictive coverage may be narrower according to later eligibility, history, and data-quality rules.

The input contract must therefore support explicit identification of:

- municipalities present in the file;
- municipalities expected for the department;
- municipalities missing from the file;
- municipalities present but ineligible for inference;
- unknown or mismatched municipalities.

**OPEN DECISION:** whether every departmental municipality must appear in each file or whether missing municipalities are allowed with explicit availability status.

## Temporal Rules

At minimum, the input must support a single reference period T representing the latest closed period being processed.

The final contract must prevent mixing unavailable future information into that cutoff.

Later validation must define:

- accepted date/month representation;
- whether every row must share the same reference period;
- handling of late corrections/revisions;
- whether backfilling older periods is allowed;
- whether periods must be processed sequentially;
- operational publication lag for each source.

These are **TO BE FROZEN IN LATER STAGE**.

## Draft Validation Categories

Validation should be layered so the user can understand why processing cannot continue.

### 1. File-level validation

Examples:

- file unreadable;
- unsupported format;
- empty file;
- wrong department context;
- missing period information;
- invalid encoding/structure.

### 2. Schema-level validation

Examples:

- required conceptual field missing;
- duplicate/conflicting column meaning;
- wrong data type;
- unrecognized municipality identifier field.

Exact field names and types are not frozen.

### 3. Municipality-record validation

Examples:

- unknown municipality;
- municipality does not belong to active department;
- duplicate municipality-period row;
- required observation missing;
- impossible or invalid value under later domain rules.

### 4. Temporal validation

Examples:

- mixed reference periods in the same file when not allowed;
- future period relative to allowed processing cutoff;
- period incompatible with retained history;
- late/revised period requiring a governed reprocessing policy.

### 5. Eligibility/readiness validation

Examples:

- insufficient historical window;
- missing required external/system-derived data;
- contract/model incompatibility;
- no municipality ready for inference.

Eligibility is not the same as file validity. A structurally valid file can still contain municipalities that cannot produce a valid prediction.

## Draft Error Semantics

The product should distinguish errors by effect, not just technical cause.

### BLOCKING ERROR

The run must not start because the input cannot be safely or consistently interpreted.

Examples may include unreadable file, invalid department, missing reference period, or schema incompatibility.

### RECORD ERROR

A municipality record is invalid or incomplete.

Whether other municipalities may continue is an **OPEN DECISION** tied to whole-file versus partial processing policy in PROD-05.

### WARNING

The input is interpretable and processing may continue, but the user should know about a non-blocking condition.

Warnings must not be used to bypass missing fields that are scientifically required by the final model.

### SYSTEM DEPENDENCY ERROR

User input may be valid, but SAT-Dengue cannot complete preparation because a required system/external dependency is unavailable or incompatible.

Exact error codes and API transport are **TO BE FROZEN IN LATER STAGE**.

## Invalid Values Must Not Become Predictions

The system must not silently:

- coerce unknown municipalities into valid ones;
- replace missing required observations with zero unless an approved data rule explicitly defines zero as correct;
- use a future value to fill a missing current value;
- infer a low-risk result from missing data;
- use retrospective data that would not have been operationally available at T without documenting the rule;
- accept conflicting duplicate records by arbitrary row order.

Any imputation or correction that affects scientific inputs must be governed by later data-engineering rules and reproducible evidence.

## Draft Input Invariants

1. One processing attempt belongs to one department context.
2. The input represents one intended reference period T unless later correction/backfill rules explicitly state otherwise.
3. Every municipality record must be reconcilable to a controlled municipality identity before inference.
4. User-supplied data must reflect information operationally available by the approved cutoff.
5. Blocking validation failures prevent inference.
6. Missing or invalid input must not be translated into low risk.
7. Derived features should be generated by the system when reproducible rather than manually calculated by the user without need.
8. The exact model feature vector is not equivalent to the user-upload schema.
9. The final contract must be versioned and traceable to the model/prediction contract that consumes it.

## Open Decisions and Later Freeze

- **OPEN DECISION:** exact fields the departmental user can and should supply.
- **OPEN DECISION:** which climatic/environmental variables are user-supplied versus system-obtained.
- **OPEN DECISION:** whether all municipalities must be present in each departmental file.
- **OPEN DECISION:** whole-file rejection versus partial processing for municipality-level errors.
- **OPEN DECISION:** policy for corrections, backfills, and same-period resubmission.
- **TO BE FROZEN IN LATER STAGE:** final case/event definitions and units.
- **TO BE FROZEN IN LATER STAGE:** accepted file format, encoding, size, sheet/tab conventions, and exact column names/types.
- **TO BE FROZEN IN LATER STAGE:** operational availability cutoff for each data source.
- **TO BE FROZEN IN LATER STAGE:** complete validation/error taxonomy.
- **TO BE FROZEN IN LATER STAGE:** final data schema, data contract versioning, feature derivation rules, and model compatibility rules.

This document is explicitly a **DRAFT** and must not be used as a frozen ingestion or API implementation contract.