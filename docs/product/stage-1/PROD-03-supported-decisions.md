# PROD-03 — Supported Decisions

## Status and Purpose

**Document status: DRAFT — Phase A, pending Mauricio's review.**
**Human Gate: UNAPPROVED.** Approved decisions below preserve Mauricio's direction; this document has not been approved.

This document owns how risk estimates support human decisions and the limits of that support. [PROD-01](PROD-01-business-question.md) owns the business objective, horizons, geography, and source register; [PROD-02](PROD-02-users.md) owns users and role boundaries.

## Decision-Support Boundary — Approved Decision

SAT-Dengue V2 supports departmental surveillance officials in early identification of dengue excess/outbreak-onset risk at T+1 and T+2. It does not decide, authorize, schedule, or execute health interventions automatically.

The dashboard must show a traffic-light alert level plus complementary information. An alert is information for human interpretation; no color mandates an intervention. The absence of an alert does not establish the absence of risk.

## Supported Human Decisions

The action families below are approved possibilities from Mauricio's request. The decision questions and use descriptions are **DRAFT** wording for review. They are neither clinical guidance nor a prescribed response protocol.

| Human decision question — DRAFT | Possible downstream action — approved family | How the estimate may help — DRAFT |
|---|---|---|
| Does the signal warrant a closer epidemiological assessment? | Deeper epidemiological investigation | Focus human review on the relevant municipality, period, and available surveillance context. |
| Should surveillance attention be intensified? | Intensified surveillance | Help officials assess where and when additional follow-up may be justified. |
| Should preventive activity be considered ahead of a potential peak? | Preventive campaigns | Provide advance risk information for authority-defined planning and coordination. |
| Should the health network prepare for a possible increase in demand? | Care-network preparation | Inform human assessment of readiness needs using both prediction horizons and local knowledge. |
| Is another response appropriate under the authority's responsibilities? | Other authority-defined actions | Supply supporting risk information while leaving action selection and approval to the competent authority. |

No one-to-one mapping between alert level and action is approved. Timing, intensity, feasibility, resource allocation, and institutional authorization remain human decisions.

## Interpretation — DRAFT

- Consider T+1 and T+2 separately, with their reference and target periods; neither is a guarantee that an outbreak will occur.
- Read predictive risk alongside the observed epidemiological situation. Distinguishing a potential new onset from continuation matters to the business question; the formal target and interpretation rules remain subject to later freeze.
- Assess data availability and uncertainty before interpreting the signal. Missing or unsuitable information must not be equated with a low-risk estimate; the precise product behavior is an open decision.
- Use the two horizons as advance information. Their allocation to specific departmental planning cycles has not been approved.

The intended result is to help prevent or mitigate a peak where possible and otherwise improve preparedness. Predictive performance alone would not demonstrate that an intervention caused that result.

## Assumptions and Open Questions

- **ASSUMPTION — pending validation:** authorities have feasible follow-up options within the available lead time. The product does not establish staffing, budgets, or response capacity.
- **OPEN DECISION:** which specific decisions and response protocols will Tolima and Meta validate as useful, and who is responsible for each?
- **OPEN DECISION:** how should users handle conflicting horizons, uncertain estimates, stale inputs, or unavailable predictions?
- **OPEN DECISION:** what false-alarm/missed-event tradeoff is acceptable to the authorities? The proposal motivates attention to missed events but does not establish approved departmental costs or automatic action thresholds.
- **TO BE FROZEN IN LATER STAGE:** alert thresholds, color semantics, probability interpretation, and onset/continuation rules, following the [contract lifecycle](../../contracts/contract-lifecycle.md) and [master plan](../../roadmap/master-plan.md).
- **OPEN DECISION:** how will practical decision-support usefulness and preparedness benefits be evaluated? No operational benefit or V2 performance is claimed as demonstrated.

## Review Boundary

This decision map defines no dashboard layout, upload procedure, input/output schema, model choice, API behavior, or automated response mechanism. These remain governed by the staged product and contract workflow.

V1 demonstrates historical design lessons only; its thresholds, municipalities, results, and response interpretations are not adopted as V2 decisions. Mauricio's approval of PROD-01..03 remains pending, and progression to PROD-04 requires explicit approval.
