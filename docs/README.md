# SAT-Dengue V2 — Documentation Map

[Current status and stage gates](roadmap/master-plan.md) are maintained only in the master plan. **Stage 2 — Data Understanding is active; G2 is open.**

## Authority

Human-approved decisions and ADRs → governance → contracts → active requirements → architecture/methodology → DWP execution records → implementation → validation evidence. Historical evidence is dated; it must not override a later explicit human decision.

## References by responsibility

| Topic | Authoritative reference |
|---|---|
| Agent entry and commands | [AGENTS](../AGENTS.md) |
| Governance and handoff | [AI Developer First](governance/ai-developer-first.md) |
| DWP installation and planning policy | [DWP adoption](governance/dwp.md) |
| Current audit and validation evidence | [Validation operations](operations/validation-and-evidence.md) |
| Stage 2 PR preservation and reconciliation | [Reconciliation and recovery](operations/stage2-pr-reconciliation.md) |
| Source-linked historical outbreak context | [Outbreak event register](research/colombia-dengue-outbreak-events.md) |
| Validation commands | [Testing guide](TESTING_GUIDE.md) |
| Product direction | [Product definition](product/product-definition.md) |
| Stage 1 requirements | [Business question](product/stage-1/PROD-01-business-question.md), [users](product/stage-1/PROD-02-users.md), [supported decisions](product/stage-1/PROD-03-supported-decisions.md), [dashboard story](product/stage-1/PROD-04-dashboard-master-user-story.md) |
| Stage 1 workflow and draft contracts | [New period](product/stage-1/PROD-05-new-period-flow.md), [UI information](product/stage-1/PROD-06-ui-information.md), [prediction draft](product/stage-1/PROD-07-draft-prediction-contract.md), [input draft](product/stage-1/PROD-08-draft-input-contract.md) |
| Stage 2 scope, results and next decisions | [Recognition report](product/stage-2/DATA-01-Initial%20Recognition%20Report.md) |
| Stage 2 panel review and sensitivity | [Panel review](product/stage-2/DATA-03-panel-review.md) |
| Stage 2 bounded retrospective rules | [Use and availability rules](product/stage-2/DATA-04-retrospective-use-rules.md) |
| Stage 2 field definitions | [Canonical field matrix](product/stage-2/DATA-01-Priority%20Field%20Matrix.md) |
| Stage 2 source identities and lineage | [Source provenance](product/stage-2/DATA-01-Source%20Provenance.md) |
| Scientific decisions and literature | [Methodological note](product/stage-2/nota-metodologica.md) |
| Executable Stage 2 evidence | [Official notebook](../notebooks/01_stage2_residence_onset_eda.ipynb) |
| Data boundaries | [Data policy](data/data-policy.md) |
| Security | [Security policy](SECURITY.md) |
| Engineering and performance | [Engineering standards](standards/engineering-standards.md) |
| Scientific rigor | [ML standards](standards/ml-scientific-standards.md) |
| Architecture | [System overview](architecture/system-overview.md) |
| Methodology | [CRISP-ML(Q)](methodology/crisp-mlq-framework.md) |
| Contract maturity | [Contract lifecycle](contracts/contract-lifecycle.md) |
| Foundation decisions | [ADR 0001](decisions/adr-0001-foundation-boundaries.md) |

Redundant compatibility summaries and the superseded Stage 2 brief were consolidated into the references above. Stage 1 documents retain distinct requirement/contract ownership; they are not duplicate implementation specifications.
