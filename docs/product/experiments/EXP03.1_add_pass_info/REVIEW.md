# EXP03.1 independent review

Disposition: READY_FOR_AUTHORIZATION

This review does not constitute scientific approval or a human authorization to run the real experiment. It confirms that the infrastructure, protocol freeze, and guardrails are in place and that the only pending action is explicit human authorization for the real execution.

## Registry and branch status

- Branch: `main`
- Exact commit: `1d777b0101ce3f923f043700013befaddeca7a5b`
- Tree status at review: clean, no uncommitted changes in the repository state after validation.
- Python: `3.12.11`
- Official environment installed from the repository manifests: `python -m pip install -e '.[dev,modeling,tracking]'`.
- Active protocol: `EXP03.1` / `EXP031`
- Canonical protocol SHA-256: `46f287468ace7cee7c67220b871cf85a7a9c0670a131d80838d3baf147da0075`
- G5: `NOT_APPROVED`
- Champion: `not_selected`
- Execution mode: `infrastructure_only_real_execution_not_authorized`

## Scientific review

The frozen protocol in [docs/product/experiments/EXP03.1_add_pass_info/protocol.json](../../../docs/product/experiments/EXP03.1_add_pass_info/protocol.json) and the canonical matrix in [docs/product/experiments/EXP03.1_add_pass_info/ablation-matrix.frozen.yml](../../../docs/product/experiments/EXP03.1_add_pass_info/ablation-matrix.frozen.yml) are internally consistent with the scientific objective and guardrails.

Confirmed points:

- Hypothesis, objective and variants are aligned: `M00` is the EXP03 V09 reference, `M01` adds recent channel memory and `M02` adds recent + change features.
- The pairwise contrasts `Q1=M01-M00`, `Q2=M02-M01`, `Q3=M02-M00` match the protocol and the canonical matrix.
- The feature contract is frozen and consistent with the intended historical reconstruction: six predictors only, recent windows `T−1…T−6` and prior windows `T−7…T−12`, no leakage across gap boundaries, strict greater-than `EXCESS` comparison, epidemic years included.
- The protocol explicitly rejects 2025 and keeps `stress_2024` as stress-only, not development, which is compatible with the design.
- M00/M01/M02 share rows, labels, family, horizon, cut and exposure denominators; the budget is a common false-alert cap of 1.0 false onset alert per monitored municipality-year.
- The code in [src/sat_dengue/experiments/exp03_1_contract.py](../../../src/sat_dengue/experiments/exp03_1_contract.py), [src/sat_dengue/experiments/exp03_1_engine.py](../../../src/sat_dengue/experiments/exp03_1_engine.py), and [src/sat_dengue/experiments/exp03_1_preflight.py](../../../src/sat_dengue/experiments/exp03_1_preflight.py) enforces a fail-closed, source-free validation surface and blocks real scientific execution unless a separate, explicit human authorization path is introduced.

No unresolved scientific defect was identified in the frozen design. The hard boundary is not a protocol bug; it is the deliberate prohibition of real execution and MLflow writes while the repository remains in infrastructure-only mode.

## Technical review

- Unit, contract and integration tests are passing for the source-free surface.
- Bundles are validated within the repository-local `tmp/` area and reject any accidental write to the protected permanent MLflow store.
- MLflow tracking remains controlled for synthetic data only; no permanent scientific tracking entry is created in the current repository state.
- The environment is ready to support a single authorized execution under the same protocol, with the permanent scientific store and real data admission left intentionally outside scope of this review.

## Final disposition

READY_FOR_AUTHORIZATION

This means the infrastructure, protocol freeze, reproducibility checks, synthetic validations, tracking protections, and operational runbook are prepared. It does not mean the real experiment is approved or that Mauricio has authorized a scientific run.
