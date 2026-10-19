# Stage 2 Chapter 1 — Candidate Dataset Construction

## Purpose

This document records the bounded Chapter 1 implementation for Stage 2 Data Understanding:

- Candidate row-level consolidated dataset: `data/processed/dengue_y_dengue_grave.csv`
- Candidate municipality-month panel dataset: `data/processed/panel_mensual_dengue_clima.csv`

This chapter is limited to construction, reconciliation and validation of candidate datasets. It does not include new EDA, target construction, feature selection, model training, model evaluation, or Stage 2 gate closure.

## Scope and constraints

- Source inputs are read-only:
  - `data/raw/dengue.csv`
  - `data/raw/dengue_grave.csv`
  - `data/raw/google_earth_engine.csv`
  - `data/sources/Divipola-municipios.md`
- Epidemiological sources are vertically concatenated; no patient-level merge or deduplication is applied.
- Original 69 epidemiological columns are preserved exactly as supplied.
- Additional columns capture provenance, normalized helper keys and climate linkage status.
- Climate monthly aggregates are computed directly from daily climate source rows, never from repeated climate values in notification rows.

## Candidate construction contract

Candidate construction metadata is versioned in:

- `data/interim/stage2_consolidated_dataset_pipeline/candidate_construction_contract_v1.json`

Execution evidence is recorded in:

- `data/interim/stage2_consolidated_dataset_pipeline/execution_manifest.json`

The contract is explicitly a candidate construction contract and must not be interpreted as a final training contract.

## Implementation artifacts

- Pipeline module: `scripts/stage2_consolidated_dataset_pipeline.py`
- Notebook chapter: `notebooks/03_consolidated_dataset_pipeline.ipynb`
- Synthetic tests: `tests/unit/test_consolidated_dataset_pipeline.py`
- Plan validator: `.dwp/plans/PLAN_013_stage2_consolidated_datasets_ch1/validate_pipeline_outputs.py`

## Safety and publication behavior

- Outputs are written via temporary files and atomic replace.
- Existing outputs are backed up before replacement.
- Validation failures are blocking and must not silently produce published outputs.
- Manifest and contract updates are local evidence artifacts under `data/interim/`.

## Current status statement

The generated CSV files are candidate artifacts for downstream analysis only. No claim of final training readiness is made in this chapter.
