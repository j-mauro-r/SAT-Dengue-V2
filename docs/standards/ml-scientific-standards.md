# ML and Scientific Standards

## Validation and Leakage Control

- Strict temporal validation is mandatory.
- Anti-leakage checks are required in feature engineering and evaluation.
- No model selection based solely on training metrics.

## Reproducibility and Traceability

- Experiment setup must be reproducible.
- Model runs and evaluation evidence must be traceable.
- Common evaluation protocol must be applied across candidate models.
- MLflow is planned but not yet implemented in foundation stage.

## Notebook Policy

- Notebooks are valid for exploration, communication, and experimentation.
- Reusable production logic belongs in src/ modules.
- Deterministic notebook execution is preferred when feasible.
- Critical business/ML logic must not remain only in notebook cells.
