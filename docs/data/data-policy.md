# Data Policy

## Current Source Strategy

Current epidemiological and climate CSV snapshots are supplied locally for read-only Stage 2 analysis. Kaggle/local/Colab is the intended large-data strategy; exact upstream versions and reproducible retrieval of these snapshots are not yet established. The Stage 2 provenance register records those limits. Supplied DIVIPOLA reference snapshots have human-provided DANE provenance bound to local hashes.

## Git Data Boundaries

Must not be committed to GitHub:

- Large raw datasets
- Large interim/processed datasets
- Sensitive personal health records

Allowed in repository:

- Small synthetic fixtures for tests
- Tiny non-sensitive examples required for CI
- Metadata/configuration for reproducible data workflows

## Intended Lifecycle (not yet an implemented pipeline)

Kaggle -> reproducible download -> local/Colab workspace -> processing pipeline -> training/evaluation

## Deferred Infrastructure

DVC + S3 may be introduced only when justified by demonstrated traceability or collaboration needs.
