# Architecture

## Current Architecture (Foundation)

The repository currently implements a harness-first architecture:

- `AGENTS.md` is the operational entry point for coding agents.
- `docs/` is the durable knowledge layer.
- `.agents/` contains reusable skills, commands, and personas.
- `.dwp/` is the plan-state workspace for Deep Work Plan execution.
- `tmp/` is isolated scratch space for disposable artifacts.

There is no application runtime or source module tree yet.

## Planned Technical Layers

When implementation starts, architecture is expected to include:

1. Data layer: ingestion, schema normalization, and quality checks.
2. Analytics/ML layer: feature engineering, model training/evaluation, and tracking.
3. Delivery layer: service/API and/or visualization surfaces.
4. Operations layer: CI/CD, environment governance, and release controls.

## Decision Flow

- Product intent and constraints are captured first in docs.
- Work is decomposed into DWP plans with explicit gates.
- Execution evidence is captured per task before completion.
