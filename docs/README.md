# SAT-Dengue-V2 Documentation Map

This index defines where authoritative knowledge lives in the repository.

## Authority Hierarchy

1. Human-approved decisions and ADRs
2. Governance policies
3. Product/data/model/API contracts
4. Active requirements and task contracts
5. Architecture and methodology docs
6. DWP plans for current work
7. Implementation diffs
8. Validation evidence

## Domain Index

### Governance

- `governance/ai-developer-first.md`: AI Developer First policy and operating boundaries.
- `governance/dwp.md`: DWP adoption and conformance evidence log.

### Product

- `product/product-definition.md`: product objective, scope, and dashboard functional baseline.
- [Stage 2 brief](product/stage-2/DATA-01-Data%20Understanding.md): scope, completed increments and review constraints.
- [Recognition report](product/stage-2/DATA-01-Initial%20Recognition%20Report.md): historical recognition and saved corrected EDA findings.
- [Canonical priority field matrix](product/stage-2/DATA-01-Priority%20Field%20Matrix.md): single field-definition reference; observed headers and pending aliases.
- [Source provenance](product/stage-2/DATA-01-Source%20Provenance.md): input fingerprints, saved-run metadata and reference lineage limits.
- [Methodological note](product/stage-2/nota-metodologica.md): approved residence/onset choices, literature context and open model decisions.

### Notebooks

- [Official Stage 2 notebook](../notebooks/01_stage2_residence_onset_eda.ipynb): bounded residence/onset EDA; saved outputs remain unchanged by documentary consolidation.

### Methodology

- `methodology/crisp-mlq-framework.md`: scientific lifecycle application.

### Data

- `data/data-policy.md`: data boundaries and lifecycle policy.

### Architecture

- `architecture/system-overview.md`: planned system structure and runtime flow.

### Contracts

- `contracts/contract-lifecycle.md`: contract ordering and freeze/change rules.

### Standards

- `standards/engineering-standards.md`: engineering/testing/Git/documentation standards.
- `standards/ml-scientific-standards.md`: ML, leakage, reproducibility, and notebook standards.

### Decisions

- `decisions/adr-0001-foundation-boundaries.md`: accepted foundation-level decisions.

### Operations

- `operations/validation-and-evidence.md`: evidence-state and validation operations.

### Roadmap

- `roadmap/master-plan.md`: single durable master plan for all Stages 0–10 and their gate evidence.

## Compatibility Entry Documents (Root docs/)

The files below are maintained as stable entry points and summaries:

- `PRODUCT_SPEC.md`
- `ARCHITECTURE.md`
- `STANDARDS.md`
- `TESTING_GUIDE.md`
- `DEVELOPMENT_COMMANDS.md`
- `SECURITY.md`
- `PERFORMANCE.md`
- `AI_AGENT_ONBOARDING.md`
- `AI_AGENT_COLLAB.md`
