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

- Dashboard functional scope was defined in Stage 1; final API contracts remain deferred until Stage 6 scientific/model evidence is available.
- Exact input schema is not frozen during the current Stage 2 analysis.
