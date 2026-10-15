# Contract Lifecycle (Product and Engineering)

## Ordering Principle

Product Definition -> Dashboard functional requirements -> draft information contracts -> Data Understanding -> Data/target freeze -> Data Engineering -> Modeling -> QA/champion selection -> final product contracts -> API -> Dashboard -> E2E/deployment.

## Contract Types

- Product contracts: user-visible behavior and workflow semantics.
- Data contracts: input requirements, validation rules, and schema stability.
- Model contracts: output semantics, confidence/probability interpretation, and traceability.
- API contracts: request/response and error behavior, frozen after product/dashboard alignment.

## Change Governance

Material contract changes require:

- explicit rationale,
- durable documentation update,
- validation impact analysis,
- human approval.
