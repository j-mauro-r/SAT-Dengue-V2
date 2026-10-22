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

## Dashboard Delivery Direction

The approved first product slice is a **read-only E2E MVP** that retrieves persisted results through an API and presents them in the dashboard. It includes observed/endemic context, T+1/T+2 risk information, traceability, model-governance status, and historically scoped false-alert/onset evidence. The canonical functionality and acceptance criteria belong to [PROD-04](stage-1/PROD-04-dashboard-master-user-story.md); the information catalog belongs to [PROD-06](stage-1/PROD-06-ui-information.md).

A prototype must be reviewed before Stage 6 freezes the minimum read-only contracts. Monthly input/inference and expert decision/action feedback are later write-enabled iterations. User feedback will be stored separately from the epidemiological outcome observed later.

## Inference Trigger Policy

The read-only MVP does not upload data or trigger inference. Dashboard load, refresh, filtering, and navigation only retrieve persisted results. A later write-enabled iteration may add an explicit user-initiated monthly input/inference action under its frozen contract; passive dashboard actions must never trigger inference.
