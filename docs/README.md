# SAT-Dengue V2 — Documentation Map

[Current status, next work and stage gates](roadmap/master-plan.md) are maintained only in the master plan. This index assigns documentation ownership; dated reports are evidence, not additional policies.

## Authority

Human-approved decisions and ADRs → governance → contracts → active requirements → architecture/methodology → DWP execution records → implementation → validation evidence. Historical evidence is dated; it must not override a later explicit human decision.

## References by responsibility

| Topic | Authoritative reference |
|---|---|
| Agent entry and commands | [AGENTS](../AGENTS.md) |
| Governance and handoff | [AI Developer First](governance/ai-developer-first.md) |
| DWP installation and planning policy | [DWP adoption](governance/dwp.md) |
| Evidence interpretation and dated audit history | [Validation operations](operations/validation-and-evidence.md) |
| Harness audit and document consolidation (2026-10-20) | [Audit record](operations/harness-documentation-audit-2026-10-20.md) |
| Historical Stage 2 PR preservation/recovery | [Dated reconciliation record](operations/stage2-pr-reconciliation.md) |
| Source-linked historical outbreak context | [Outbreak event register](research/colombia-dengue-outbreak-events.md) |
| Validation commands | [Testing guide](TESTING_GUIDE.md) |
| Product direction | [Product definition](product/product-definition.md) |
| Stage 1 requirements | [Business question](product/stage-1/PROD-01-business-question.md), [users](product/stage-1/PROD-02-users.md), [supported decisions](product/stage-1/PROD-03-supported-decisions.md), [dashboard story](product/stage-1/PROD-04-dashboard-master-user-story.md) |
| Stage 1 workflow and draft contracts | [New period](product/stage-1/PROD-05-new-period-flow.md), [UI information](product/stage-1/PROD-06-ui-information.md), [prediction draft](product/stage-1/PROD-07-draft-prediction-contract.md), [input draft](product/stage-1/PROD-08-draft-input-contract.md) |
| Stage 2 scientific decisions and current data/model status | [Active decision register](product/traking-concluciones.md) |
| Stage 2 chapter-1 candidate datasets | [Candidate construction record](product/stage-2/CH1-dataset-construction-candidate.md) |
| Stage 2 canonical definitions of all 69 epidemiological fields | [Active field dictionary and priority matrix](product/stage-2/DATA-01-Priority%20Field%20Matrix.md) |
| Retired experimental EDA and lineage reports | [Historical archive — DEPRECATED](archive/experimental-eda/README.md) |
| Implemented training preparation pipeline | [Preparation contract and technical validation](product/stage-3/README.md) |
| Stage 4 shared references and XGBoost candidate | [Model engineering deliveries](product/stage-4/README.md) |
| Data boundaries | [Data policy](data/data-policy.md) |
| Security | [Security policy](SECURITY.md) |
| Engineering and performance | [Engineering standards](standards/engineering-standards.md) |
| Scientific rigor | [ML standards](standards/ml-scientific-standards.md) |
| Architecture | [System overview](architecture/system-overview.md) |
| Methodology and scientific controls | [ML standards](standards/ml-scientific-standards.md) |
| Contract maturity and approval | [Master plan gates](roadmap/master-plan.md), [change governance](governance/ai-developer-first.md#contract-change-governance) |
| Foundation decisions | [ADR 0001](decisions/adr-0001-foundation-boundaries.md) |

Redundant compatibility summaries, the superseded Stage 2 brief, and separate methodology/contract-lifecycle summaries were consolidated into the references above. Stage 1 documents retain distinct requirement/contract ownership; they are not duplicate implementation specifications.
