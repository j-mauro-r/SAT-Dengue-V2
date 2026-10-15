# System Overview (Planned)

## Product Components

1. ML predictive system
2. API
3. End-user dashboard

## High-Level Runtime Flow (target)

Data ingestion/preparation -> feature generation -> champion model inference -> result persistence -> API exposure -> dashboard consumption

## User-Initiated Inference Flow (target)

User uploads new period input -> validation -> backend/API -> inference pipeline -> champion model -> persisted result -> dashboard visualization

## Architecture Decisions Deferred

- Exact API contracts are deferred until dashboard functional scope is stabilized.
- Exact input column schema is intentionally not frozen in foundation stage.
