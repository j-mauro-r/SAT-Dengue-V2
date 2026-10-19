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

## Baseline readiness and conservative eligibility policy

- Baseline preservation receipt and readiness checks are tracked through `scripts/validate_stage2_training_readiness.py` and plan-local evidence for bounded Stage 2 closeout work.
- Source-coverage support and model-eligibility are treated as separate concepts:
  - Source coverage support is backed by source notification-year metadata plus execution-manifest fingerprints.
  - Model eligibility is conservative and requires target periods inside backed coverage, outside the reserved final block, and with sufficient same-month history.
- Edge symptom periods outside backed coverage remain preserved in the candidate panel for traceability and diagnostics; they are not deleted or rewritten.
- Existing future-label columns (`y_t1`, `y_t2`, `p75_t1`, `p75_t2` and related status/evaluable fields) are preserved as historical outputs and must not be redefined by closeout tasks.
- Current endemic-channel candidate fields (`p25_canal_t`, `p50_canal_t`, `p75_canal_t`, `zona_canal_t`) are computed at reference month T per municipality using the same calendar month from the five prior years (type-7 percentiles at q=0.25/0.50/0.75).
- Current endemic-channel zone convention is explicit and deterministic: `EXITO` if `c < p25`, `SEGURIDAD` if `p25 <= c <= p50`, `ALERTA` if `p50 < c <= p75`, `EXCESO` if `c > p75`; missing current count or insufficient history yields null thresholds and null zone.
- Retrospective consolidated data remain a limitation: temporal ordering in this dataset does not certify historical operational as-of availability.

## Bounded descriptive scope notes

- Category/cardinality profiling in notebook Chapter 5 is intentionally partial: the profile uses the first 150,000 rows from `data/raw/dengue.csv` (general dengue stream only), so severe-dengue representativeness is out of scope in that chapter.
- The chapter-5 matrix remains a sampled diagnostic aid and does not claim exhaustive production-grade profiling for all 69 source columns.
- Correlation diagnostics in notebook Chapter 7 use global calendar-month mean centering as a descriptive adjustment only; results are not causal evidence and do not trigger automatic predictor removal.
