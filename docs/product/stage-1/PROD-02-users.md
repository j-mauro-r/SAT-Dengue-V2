# PROD-02 — Users

## Status and Purpose

**Document status: DRAFT — Phase A, pending Mauricio's review.**
**Human Gate: UNAPPROVED.** Approved decisions below preserve Mauricio's direction; this document has not been approved.

This document owns the user definition and role boundaries. Business scope and source provenance live in [PROD-01](PROD-01-business-question.md); decision-support uses live in [PROD-03](PROD-03-supported-decisions.md).

## Primary User — Approved Decision

The primary user is an **official of a departmental Health Secretariat responsible for epidemiological surveillance**, within the approved Tolima and Meta product scope.

The user interprets predictive risk information alongside surveillance knowledge and exercises institutional judgment about follow-up. The user is not defined as a patient, an individual seeking a diagnosis, or an autonomous decision-making system.

## User Needs — DRAFT Interpretation

The following needs translate the approved direction into reviewable product language; they do not define screens or acceptance criteria:

- Understand the traffic-light alert and complementary information for the relevant municipality and T+1/T+2 horizon.
- Distinguish the observed epidemiological situation from an estimate about a future period, including possible onset versus continuation once their definitions are approved.
- Know the reference period and whether available information is sufficient and current enough to interpret the estimate.
- Use the estimate to assess whether further investigation, intensified surveillance, preventive activity, or care-network preparation should be considered.

Detailed dashboard behavior and information requirements remain for later Stage 1 documents. The existing [product baseline](../product-definition.md) remains the reference for planned capabilities.

## Roles and Responsibility Boundaries

| Role | Status | Boundary |
|---|---|---|
| Departmental epidemiological-surveillance official | APPROVED primary user | Interprets risk and supports human assessment within the authority's responsibilities. The system does not grant intervention or resource-allocation powers. |
| Person preparing/uploading the departmental file | OPEN DECISION | The expected file contains multiple municipalities from one department. Whether the primary user or a separate data-support role prepares and uploads it is undecided. |
| Municipal surveillance teams, vector-control teams, and care-network coordinators | DRAFT downstream stakeholders | They may participate in authority-defined follow-up. Direct dashboard access and separate product personas are not approved. |
| BIOMAC/research team and technical maintainers | DRAFT supporting stakeholders | Scientific advice and technical evaluation do not make them the approved primary operational users. |

Mauricio remains the product owner and approval authority under [repository governance](../../governance/ai-developer-first.md). Product approval and a health authority's operational decisions are separate responsibilities.

## Assumptions and Open Questions

- **ASSUMPTION — pending validation:** the primary user can interpret epidemiological surveillance context. Training needs, familiarity with predictive probabilities, and available time have not been validated.
- **OPEN DECISION:** which departmental offices and specific job functions will participate in initial review and eventual use?
- **OPEN DECISION:** who owns file preparation, upload, correction, and confirmation of the latest loaded period? This will inform the later new-period workflow.
- **OPEN DECISION:** which supporting stakeholders require direct access, and who is authorized to approve or coordinate each downstream action?
- **TO BE FROZEN IN LATER STAGE:** access permissions and technical role enforcement. This document defines no authentication or authorization implementation.

## Historical Boundary and Review

V1's Cali/Bucaramanga municipal users are historical context only; they do not replace the approved departmental primary user. The [source register](PROD-01-business-question.md#authority-and-source-register) records this distinction.

User wording, draft needs, and unresolved roles require Mauricio's review. This document does not approve G1, complete Stage 1, or authorize PROD-04.
