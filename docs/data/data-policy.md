# Data Policy

## Current Source Strategy

Primary large dataset is externally hosted in Kaggle and consumed through reproducible download and local/Colab processing workspaces.

## Git Data Boundaries

Must not be committed to GitHub:

- Large raw datasets
- Large interim/processed datasets
- Sensitive personal health records

Allowed in repository:

- Small synthetic fixtures for tests
- Tiny non-sensitive examples required for CI
- Metadata/configuration for reproducible data workflows

## Current Lifecycle (conceptual)

Kaggle -> reproducible download -> local/Colab workspace -> processing pipeline -> training/evaluation

## Deferred Infrastructure

DVC + S3 may be introduced only when justified by demonstrated traceability or collaboration needs.
