# PROD-01 — Business Question

## Status and Purpose

**Document status: CLOSED — Stage 1 product definition, confirmed by Mauricio after PR #7 merge.**
**Human Gate: APPROVED for Stage 1 scope.** The [master plan](../../roadmap/master-plan.md) records closure and the separate historical G0 evidence gap.

This document owns the business question, intended value, and Phase A source register. [PROD-02](PROD-02-users.md) owns users; [PROD-03](PROD-03-supported-decisions.md) owns supported human decisions. The [product definition](../product-definition.md) remains the existing scientific and dashboard baseline.

## Business Question

Can officials responsible for epidemiological surveillance in the departmental Health Secretariats of Tolima and Meta use predictive risk estimates for T+1 and T+2 to identify dengue excess/outbreak-onset risk early enough to inform preventive action and health-system preparation before a potential peak?

This asks whether predictive inference adds useful advance information to observed epidemiological surveillance. It does not assert that V2 already predicts reliably or prevents outbreaks.

## Approved Decisions

- Product geography: the departments of **Tolima and Meta**.
- Operational objective: support early identification of risk of dengue excess/outbreak onset at **T+1 and T+2**. Under the current monthly [product baseline](../product-definition.md), T is the latest loaded reference period; the horizons are the following one and two months.
- Inference uses historical data plus information available at the close of the latest loaded period. Future information unavailable at that cutoff must not be treated as an inference input.
- Describe the operation as **predictive inference** or **risk estimation**.
- Expected loading unit: one departmental file containing multiple municipalities for Tolima or Meta. This is product direction, not a frozen schema or a requirement that every municipality be included.
- The dashboard must communicate a traffic-light alert level together with complementary information.
- SAT-Dengue V2 supports human decisions and does not automate health decisions.
- Desired outcome: ideally prevent or mitigate a peak; otherwise improve health-system preparedness. This is an intended benefit, not a demonstrated causal effect or performance guarantee.

## Assumptions and Open Questions

- **ASSUMPTION — pending validation:** the information available at each cutoff will be sufficiently timely and complete to support useful advance estimates. Historical records may be revised; retrospective availability must not be confused with operational availability.
- **TO BE FROZEN IN LATER STAGE — municipal coverage within Tolima and Meta**: the geographic scope is defined at the departmental level and includes all municipalities in Tolima and all municipalities in Meta. Each department will be evaluated separately and will have its own dedicated dashboard tab. The specific eligibility, data-quality, coverage, and minimum-history criteria required for a municipality to produce a valid prediction will be frozen during Stage 2 Data & Target Freeze.
- **TO BE FROZEN IN LATER STAGE:** the epidemiological definition of excess, onset versus continuation, target construction, and temporal availability rules belong to Stage 2 Data & Target Freeze. A predicted excess must not automatically be called a new onset.
- **TO BE FROZEN IN LATER STAGE:** exact input variables, file format, historical-window requirements, validation rules, and prediction fields. The Input Contract is not frozen; final product contracts belong to Stage 6.
- **OPEN DECISION:** acceptable false-alarm/missed-event tradeoffs and evidence needed for operational usefulness. The proposal's scientific evaluation criteria are source context, not a newly approved operational acceptance threshold.
- **TO BE FROZEN IN LATER STAGE:** traffic-light semantics, thresholds, and handling of uncertain or unavailable estimates. No numeric cutoff or color-to-action rule is approved here.

## Authority and Source Register

Repository references were inspected on `main` at `a4863057780dbeb32f7c180a71092df7895eb22b`. Uploaded materials below were inspected read-only; they are identified by original filename and section because they are not versioned in this repository. They are not copied into the PR.

| Source | Use and boundary |
|---|---|
| Mauricio's explicit Phase A request and authorization to draft in this session | Authority for the approved decisions recorded here and in PROD-02/03. Stage 1 closure was subsequently confirmed by Mauricio. |
| `Formato-propuesta_Proyecto-de-grado-Mauricio.pdf`, pp. 1–3, 6–8 | Scientific purpose, anticipation of onset, municipal context, decision-support value, and evaluation concerns. National research framing does not expand approved V2 geography. |
| `Sesion_1_con_Experto_Notas.docx`, sections 2–5 and 9 | BIOMAC context: anticipation, temporal availability, justified geographic selection, and need to define excess. Suggested municipality counts and models are not adopted as V2 decisions. |
| `Reporte_Entrega3_final-2.docx`, sections 1, 2.3, 3, and 4 | V1 historical reference: decision support and distinction between onset and continuation; limited onset evidence does not establish V2 performance. Cali/Bucaramanga, 39 features, thresholds, and Champion are not V2 requirements. |
| `prueba-dashboard.md`, sections 1–2 and 9–13 | Historical dashboard/inference separation. Its V1 upload restrictions and implementation details do not override V2's expected departmental upload. |
| [Master plan](../../roadmap/master-plan.md), [product definition](../product-definition.md), and [system overview](../../architecture/system-overview.md) | Current V2 planning/configuration: stage ordering, monthly horizons, existing dashboard baseline, and deferred input schema. |
| [AI Developer First](../../governance/ai-developer-first.md), [contract lifecycle](../../contracts/contract-lifecycle.md), and [CRISP-ML(Q)](../../methodology/crisp-mlq-framework.md) | Human authority, evidence states, staged contract maturity, and current methodology. |

### Source Reconciliation

- The proposal names CRISP-DM; V2's [accepted foundation ADR](../../decisions/adr-0001-foundation-boundaries.md) and current methodology establish **CRISP-ML(Q)** for V2. No methodological change is made here.
- BIOMAC's preliminary geographic suggestions and V1's municipal pilot are context; Mauricio's approved Tolima/Meta departmental scope governs this draft.
- `AI-DEVELOPER-FIRST-FRAMEWORK.md` concerns MauroCFO and is not adopted as SAT-Dengue V2 policy. `Avance entrega 3 microproyecto.pdf` concerns PulmoIA and is not a dengue authority.

## Review Boundary

Only PROD-01, PROD-02, and PROD-03 are drafted in Phase A. No PROD-04 or later document, DWP plan, functional implementation, contract freeze, or stage completion is authorized by this document. Mauricio must explicitly approve these three documents before progression to PROD-04.