# PROD-05 — New Period Flow

## Status and Purpose

**Document status: CLOSED — Phase C. APPROVED TO MAURICIO**
**Human Gate: APPROVED.** 

This document defines the product workflow for processing a new monthly departmental period. It owns the user-visible sequence from file selection through validation, explicit predictive inference, result presentation, and persistence. It does not define implementation architecture, endpoint shapes, final schemas, model internals, retry/timeout behavior, cancellation, technical error taxonomies, or detailed partial-processing mechanics.

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
System validates file, municipality identities, required information, and period
    ↓
If invalid → explain the blocking problem; no inference
    ↓
If valid → user explicitly starts processing
    ↓
System performs predictive inference for eligible municipalities
    ↓
System produces T+1 and T+2 results
    ↓
System persists the completed result
    ↓
Dashboard presents the new result
```

The flow is a product contract. It does not prescribe synchronous versus asynchronous execution, queues, workers, storage engines, or a particular API design.

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

**TO BE FROZEN IN LATER STAGE:** accepted file format and exact period representation.

### 3. Validate Before Inference

Validation occurs before model execution. At product level it must determine whether:

- the file can be interpreted;
- the municipality and period information are valid for the active department;
- the required information is present;
- there is sufficient eligible information to proceed to inference.

A blocking validation failure prevents inference and must be explained to the user in understandable terms.

Detailed technical validation taxonomies belong to later data/API contracts.

### 4. Explicitly Start Processing

After successful validation, the user explicitly initiates processing through an action such as **Process new period**.

The user should not need to understand model internals to perform this action. Selecting the file or validating it is not equivalent to running inference.

### 5. Predictive Inference

The system uses historical information plus information available at the close of the newly loaded reference period to estimate dengue excess/outbreak-related risk for T+1 and T+2.

User-facing language should use predictive inference, risk estimation, or equivalent approved terminology.

The flow must preserve the distinction between:

- current observed epidemiological state at T;
- estimated future risk at T+1;
- estimated future risk at T+2.

No public-health intervention is executed automatically.

### 6. Processing Outcome

If processing succeeds, the resulting T+1/T+2 prediction becomes available to the dashboard.

If validation or processing fails, the user must receive a clear failure state and the previously persisted valid result must not be silently replaced or relabeled as the new result.

Technical retry, timeout, cancellation, detailed partial-completion behavior, and internal error codes are outside this Stage 1 document.

### 7. Persist Completed Results

A completed result must be persisted so that the dashboard can retrieve it later without rerunning inference.

At minimum, persistence must preserve enough product information to identify:

- department;
- reference period;
- municipality-level T+1/T+2 results;
- model version;
- prediction generation date/time.

Exact persistence technology, internal identifiers, provenance fields, input-version associations, and storage layout belong to later engineering contracts.

### 8. Display the New Result

After successful processing, the dashboard should load the newly completed result and expose the information defined by PROD-04 and PROD-06.

## Result Reuse and Refresh Rules

- Dashboard load is read-only.
- Dashboard refresh is read-only.
- Changing municipality is read-only.
- Changing T+1/T+2 view is read-only.
- Switching Tolima/Meta tabs is read-only.
- Only an explicit new-period processing action may initiate inference.
- A previously persisted result may be revisited without uploading the file again.

## Repeated Period Rule

A repeated period must not silently overwrite an existing persisted result.

The final replacement, versioning, or correction policy belongs to later contracts and implementation design.

## Error Communication Principles

Errors shown to the user must:

- explain what prevented progression;
- avoid exposing internal stack traces or technical secrets;
- avoid converting missing or invalid input into a low-risk prediction;
- preserve the previously valid persisted result when the new attempt fails.

## Acceptance Criteria — DRAFT

| ID | Given / When | Then |
|---|---|---|
| AC01 | The user selects a departmental file. | File selection alone does not start inference or replace persisted results. |
| AC02 | The selected file contains a blocking validation problem. | Inference does not start and the user receives an understandable validation outcome. |
| AC03 | Validation succeeds and the user explicitly starts processing. | The system performs predictive inference for eligible municipalities for T+1 and T+2. |
| AC04 | Processing completes successfully. | The new result is persisted and becomes available to the dashboard. |
| AC05 | Validation or processing fails. | The failure is visible and a previous valid persisted result is not silently replaced. |
| AC06 | The user refreshes or revisits the dashboard. | Existing persisted results are read without triggering new inference or training. |
| AC07 | A municipality has no valid prediction. | The UI shows an unavailable state rather than zero risk or a fabricated alert. |
| AC08 | The same period is submitted again. | The system does not silently overwrite the existing persisted result. |

## Later Freeze

- **TO BE FROZEN IN LATER STAGE:** exact validation rules.
- **TO BE FROZEN IN LATER STAGE:** final input schema and prediction schema.
- **TO BE FROZEN IN LATER STAGE:** replacement/versioning policy for repeated periods.
- **TO BE FROZEN IN LATER STAGE:** API endpoints, persistence mechanism, and implementation architecture.

This document does not approve Gate G1, Stage 1 completion, or any implementation detail beyond the product workflow defined above.
