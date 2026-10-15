# Product Definition — SAT-Dengue V2

## Problem and Purpose

SAT-Dengue V2 aims to support earlier epidemiological decision-making by anticipating dengue outbreak risk before onset, instead of only describing outbreaks already in progress.

## Scientific Objective

Evaluate whether epidemiological, temporal, and climatic signals can anticipate excess dengue risk with approximately:

- T+1 month
- T+2 months

## Candidate Modeling Families

- XGBoost
- LightGBM
- GAM

## Reference/Baseline Approaches

- Endemic channel
- Epidemiological persistence
- Poisson (when methodologically applicable)

Final model selection is evidence-driven and must use the same evaluation protocol across candidates.

## Future Dashboard Functional Scope (minimum)

- Municipality selection
- Current epidemiological state
- Endemic-channel visualization
- Observed cases and relevant thresholds
- T+1 prediction
- T+2 prediction
- Calibrated probability
- Operational threshold
- Outbreak interpretation:
  - onset
  - continuation
  - no outbreak predicted
- Relevant climatic context
- Explainability information (when scientifically valid)
- Model/run traceability
- Prediction history

## Inference Trigger Policy

A user-initiated action must upload/input new monthly data and trigger inference. Dashboard load/refresh must not auto-trigger inference.
