# Stage 4 delivery 1 — shared model-training pipeline and simple references

This first bounded Stage 4 delivery implements a shared execution pipeline on top of current Stage 3 temporal artifacts. It runs two references only:

- Persistence: deterministic binary alert derived from current endemic-zone state.
- Train prevalence: constant probability estimated from `Y_train` per window/horizon.

This delivery does **not** train XGBoost, LightGBM or GAM. It does not close G4, and it does not retroactively close G2/G3.

## Scope and inputs

- Stage 3 source contract: [training_preparation_contract_v1.json](../stage-3/training_preparation_contract_v1.json)
- Stage 4 contract: [model_engineering_contract_v1.json](model_engineering_contract_v1.json)
- Notebook orchestrator: [05_baseline_models.ipynb](../../../notebooks/05_baseline_models.ipynb)
- Pipeline modules: [scripts/model_training](../../../scripts/model_training)

The pipeline verifies Stage 3 temporal artifacts from manifests and hash checks before loading any window. It never selects folders by alphabetical order or "latest" naming.

## Reference behavior

1. Persistence
- Formula: `predict_excess_t_plus_h = 1 if zona_canal_t == EXCESO else 0`.
- Unknown/missing state rows are marked non-evaluable.
- Outputs are deterministic alerts, not calibrated probabilities.

2. Train prevalence
- Formula: `mean(Y_train)` for each cutoff-horizon window.
- Probability is constant on the corresponding validation rows.
- Event metrics for this reference remain non-evaluable unless a threshold policy is declared in a future delivery.

Planned future reference not in this delivery: Poisson baseline.

## Metrics in this delivery

Primary metrics:
- `average_precision`
- `onset_sensitivity` (detected/total)
- `false_alarm_ratio` (incorrect alerts / emitted alerts)
- `brier` (probabilistic outputs only)

Event definitions are explicit in the contract:
- onset definition
- anticipation semantics
- evaluable population
- unknown-period treatment

Cases with empty denominators or insufficient classes are reported as non-evaluable. They are not imputed as zero.

## Commands

```bash
.venv/bin/python -m scripts.model_training.execution --execute
.venv/bin/python -m scripts.model_training.execution --verify
.venv/bin/python -m scripts.model_training.notebook_execution --execute
.venv/bin/python -m scripts.model_training.notebook_execution --verify
```

Artifacts are written under `artifacts/model_training/` (gitignored), with immutable identity directories and byte-verified reuse.
