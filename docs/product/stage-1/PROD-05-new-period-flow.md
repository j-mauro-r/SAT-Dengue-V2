# PROD-05 — New Period Flow

## Status and Purpose

**Document status: DRAFT — Phase C.**
**Human Gate: UNAPPROVED.**

This document defines the product workflow for processing a new monthly departmental period. It owns the user-visible sequence from file selection through validation, inference, result presentation, and persistence semantics. It does not define implementation architecture, endpoint shapes, final schemas, model internals, or frozen validation rules.

Related sources of truth:

- [PROD-01](PROD-01-business-question.md): business question and geography.
- [PROD-02](PROD-02-users.md): primary user.
- [PROD-03](PROD-03-supported-decisions.md): supported human decision.
- [PROD-04](PROD-04-dashboard-master-user-story.md): dashboard experience and visible behaviors.
- [Product definition](../product-definition.md): current product baseline.
- [Contract lifecycle](../../contracts/contract-lifecycle.md): contract maturity and freeze order.

## Approved Product Direction

SAT-Dengue V2 processes a new period only after an explicit user action. Opening the dashboard, refreshing it, switching department, changing municipality, or changing horizon must remain read-only and must not trigger inference or training.

The expected loading unit is one departmental file for either Tolima or Meta containing information for multiple municipalities. The exact file format, columns, allowed omissions, and eligibility rules are not frozen in Stage 1.

## Product Flow

```text
User selects department
    ↓
User selects monthly departmental file
    ↓
System validates file and period
    ↓
If invalid → explain blocking errors; no inference
    ↓
If valid → user explicitly starts processing
    ↓
System performs predictive inference for eligible municipalities
    ↓
System produces T+1 and T+2 results
    ↓
System persists the completed run and its traceability
    ↓
Dashboard presents the new results
```

The flow is a product contract. It does not prescribe whether the implementation uses synchronous or asynchronous jobs, queues, workers, storage engines, or a particular API design.

## Step-by-Step User Experience

### 1. Select Department

The user works within either the Tolima or Meta context. A file must belong to the active department.

A file associated with another department must not be silently accepted into the active context.

**TO BE FROZEN IN LATER STAGE:** how department identity is encoded or inferred from the file.

### 2. Select the New Monthly File

Selecting a file only stages it for validation. It must not alter the currently displayed persisted prediction and must not start inference automatically.

The interface should show at minimum:

- selected file name;
- active department;
- detected or declared reference period when available;
- validation state.

**TO BE FROZEN IN LATER STAGE:** accepted file format, size limits, encoding, sheet/tab rules, and exact period representation.

### 3. Validate Before Inference

Validation occurs before model execution. Validation must distinguish at least:

- file cannot be read;
- structural/schema problem;
- invalid or missing period information;
- municipality identity problem;
- required information missing for one or more municipalities;
- duplicate/conflicting records;
- incompatible or unsupported data values;
- no municipality eligible for inference.

A blocking validation failure prevents inference.

A non-blocking issue may allow partial processing only if later product/data contracts explicitly authorize that behavior.

**OPEN DECISION:** whether a departmental file with some invalid municipalities is rejected entirely or can proceed for the valid subset.

### 4. Confirm and Start Processing

After successful validation, the user explicitly initiates processing through an action such as **Process new period**.

The product must make clear that processing may create a new persisted prediction run. The user should not need to understand the model implementation to execute this action.

**OPEN DECISION:** whether an explicit confirmation step is required after validation and before inference, or whether the processing action itself is sufficient confirmation.

### 5. Predictive Inference

The system uses historical information plus information available at the close of the newly loaded reference period to estimate dengue excess/outbreak-onset risk for T+1 and T+2.

The product must not describe this as a regression operation. User-facing language should use predictive inference, risk estimation, or equivalent approved terminology.

The flow must preserve the distinction between:

- current observed epidemiological state at T;
- estimated future risk at T+1;
- estimated future risk at T+2.

No public-health intervention is executed automatically.

### 6. Processing Outcome

The workflow must end in one of these product states:

- **COMPLETED:** a new valid run is available and can be displayed.
- **VALIDATION FAILED:** inference was not started because the input did not satisfy blocking requirements.
- **PROCESSING FAILED:** validation passed, but processing did not complete successfully.
- **NO ELIGIBLE PREDICTION:** the input was processed but no municipality/horizon produced a valid prediction under later eligibility rules.

These are product-level semantic states, not frozen API status codes.

**TO BE FROZEN IN LATER STAGE:** retry behavior, timeout behavior, cancellation, partial-completion policy, and technical error taxonomy.

### 7. Persist Completed Results

A completed run must be persisted so that the dashboard can retrieve it later without rerunning inference.

At minimum, persistence must preserve enough information to reconstruct:

- department;
- reference period;
- municipality-level T+1/T+2 results;
- model/version identity;
- generation time;
- run identity;
- origin of the run where relevant;
- the association with the uploaded period/input version.

Exact persistence technology and storage layout are implementation decisions for later stages.

### 8. Display the New Result

After successful processing, the dashboard should load the newly completed result and expose the information defined by PROD-04 and PROD-06.

If the new run fails, the previously persisted valid result must not be silently overwritten or relabeled as the new result.

## Result Reuse and Refresh Rules

- Dashboard load is read-only.
- Dashboard refresh is read-only.
- Changing municipality is read-only.
- Changing T+1/T+2 view is read-only.
- Switching Tolima/Meta tabs is read-only.
- Only an explicit new-period processing action may initiate inference.
- A previously persisted result may be revisited without uploading the file again.

## Duplicate or Repeated Period Handling

A repeated submission for the same department and reference period must not silently destroy prior traceability.

**OPEN DECISION:** final product policy for same-period reprocessing:

1. reject duplicate periods;
2. allow reprocessing and create a new immutable run version;
3. allow replacement under an explicitly governed correction workflow.

Until this is decided, no overwrite-in-place behavior is approved.

## Error Communication Principles

Errors shown to the user must:

- explain what prevented progression;
- identify whether the problem is file-wide or municipality-specific when known;
- avoid exposing internal stack traces or technical secrets;
- avoid converting missing/invalid input into a low-risk prediction;
- preserve the previously valid persisted result when the new attempt fails.

Exact error codes belong to the later Input/API contracts.

## Acceptance Criteria — DRAFT

| ID | Given / When | Then |
|---|---|---|
| AC01 | The user selects a departmental file. | File selection alone does not start inference or replace persisted results. |
| AC02 | The selected file contains a blocking validation problem. | Inference does not start and the user receives an understandable validation outcome. |
| AC03 | Validation succeeds and the user explicitly starts processing. | The system may perform inference for eligible municipalities for T+1 and T+2. |
| AC04 | Processing completes successfully. | A new traceable run is persisted and becomes available to the dashboard. |
| AC05 | Processing fails after validation. | The failure is visible and a previous valid persisted result is not silently replaced. |
| AC06 | The user refreshes or revisits the dashboard. | Existing persisted results are read without triggering new inference or training. |
| AC07 | A municipality has no valid prediction. | The UI shows an unavailable/ineligible state rather than zero risk or a fabricated alert. |
| AC08 | The same period is submitted again. | The system does not silently overwrite prior traceability; final reprocessing policy remains governed by the later contract. |

## Open Decisions and Later Freeze

- **OPEN DECISION:** whole-file rejection versus partial municipality processing.
- **OPEN DECISION:** same-period reprocessing/versioning policy.
- **OPEN DECISION:** whether a separate confirmation is required before inference.
- **TO BE FROZEN IN LATER STAGE:** exact validation rules and error taxonomy.
- **TO BE FROZEN IN LATER STAGE:** retry, timeout, cancellation, and partial-failure behavior.
- **TO BE FROZEN IN LATER STAGE:** final input schema, prediction schema, API endpoints, persistence mechanism, and implementation architecture.

This document does not approve PROD-06, PROD-07, PROD-08, Gate G1, or Stage 1 completion.