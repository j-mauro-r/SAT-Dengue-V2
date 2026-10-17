# Stage 2 Investigation - INI_SIN > FEC_NOT Date Inconsistency (2012-2014 References)

Updated: 2026-10-17. Scope: bounded Stage 2 Data Understanding diagnostics for dengue residence records in Meta and Tolima.

## 1. Objective

Investigate the 8,556 records in `data/raw/dengue.csv` where symptom onset (`INI_SIN`) is later than notification date (`FEC_NOT`), using newly supplied yearly SIVIGILA downloads (2012, 2013, 2014), without applying automatic correction.

## 2. Inputs and comparability boundaries

- Consolidated file: `data/raw/dengue.csv`.
- Companion control: `data/raw/dengue_grave.csv` (used only to confirm anomaly concentration is specific to dengue export).
- Yearly references detected by content coverage: 2012, 2013, 2014.
- Residence scope: Meta and Tolima municipalities.
- Date policy: use parsed date values with explicit handling for missing/unparseable rows; keep unresolved rows visible.

Inventory and provenance outputs are stored in:

- `data/interim/stage2_dengue_date_investigation/source_inventory.csv`
- `data/interim/stage2_dengue_date_investigation/source_inventory_metadata.json`

## 3. Method summary

1. Reproduced baseline anomaly counts in the consolidated dengue export at Meta/Tolima residence scope.
2. Profiled temporal comparability and data quality classes before source comparison.
3. Matched consolidated rows to yearly reference rows with a keyed, one-to-one constrained strategy.
4. Compared parsed date pairs and raw date-string stability by source year.
5. Evaluated sensitivity scenarios at municipality-month level:
   - A: keep current values.
   - B: swap only affected records.
   - C: exclude affected records.
   - D: use 2013 source reference where matched (fallback to A).
6. Embedded all outputs in the official notebook section and saved execution outputs.

## 4. Key observations (evidence)

### 4.1 Baseline reproduction

- Consolidated dengue, Meta+Tolima: 235,494 comparable records, 8,556 affected (3.6332%).
- By department:
  - Meta: 3,597 affected.
  - Tolima: 4,959 affected.
- Severe dengue control stream: 0 affected in 4,619 comparable records.

Evidence files:

- `data/interim/stage2_dengue_date_investigation/baseline_anomaly_summary.csv`
- `data/interim/stage2_dengue_date_investigation/baseline_anomaly_by_department.csv`
- `data/interim/stage2_dengue_date_investigation/dengue_grave_baseline_check.csv`

### 4.2 Yearly-reference comparison

- 2012 reference: 10,715 uniquely matched rows; 0 affected among comparable records.
- 2013 reference: 20,296 uniquely matched rows; 8,556 affected among comparable records (42.1623% in that 2013-only subset).
- 2014 reference: 15,216 uniquely matched rows; 0 affected among comparable records.
- Match diagnostics show right-only rows equal to 0 for all yearly references in the keyed comparison output.

Evidence files:

- `data/interim/stage2_dengue_date_investigation/comparison_match_outcomes.csv`
- `data/interim/stage2_dengue_date_investigation/temporal_comparability_summary.csv`

### 4.3 Date-pair consistency and swap signal

- For matched rows, raw `INI_SIN` and `FEC_NOT` strings are stable against yearly references in all three years.
- Exact parsed-date swaps (`INI_SIN` equal to source `FEC_NOT` and vice versa) appear in all yearly references (2012: 481, 2013: 66, 2014: 540), but this pattern alone is not causal proof for the 8,556 alerts.
- The affected alert concentration is specific to records aligned with 2013 reference coverage.

Evidence file:

- `data/interim/stage2_dengue_date_investigation/comparison_date_pairs.csv`

### 4.4 Sensitivity scenarios (municipality-month distribution)

- Scenario A (keep current): baseline volume preserved.
- Scenario B (swap affected only): preserves total volume, redistributes monthly peaks strongly (total absolute municipality-month delta 8,576).
- Scenario C (exclude affected): reduces covered records by 8,556 and suppresses peaks.
- Scenario D (2013 reference fallback): net-neutral against A in this bounded matched-coverage construction.

Evidence files:

- `data/interim/stage2_dengue_date_investigation/sensitivity_scenarios_municipio_mes.csv`
- `data/interim/stage2_dengue_date_investigation/sensitivity_top_months_shift.csv`
- `data/interim/stage2_dengue_date_investigation/sensitivity_scenario_notes.csv`

## 5. Interpretation boundaries

- This investigation is diagnostic only; it does not approve replacement, swap, exclusion, or imputation as production policy.
- Yearly files are treated as supplied references and may include post-hoc revisions.
- Match quality is controlled in this scope, but upstream extraction lineage for all files remains a separate provenance concern.
- Causal attribution (source-native issue vs transformation issue) remains partially unresolved and must be carried to review with uncertainty explicitly stated.

## 6. Notebook execution evidence

Official notebook section with saved outputs:

- `notebooks/01_stage2_residence_onset_eda.ipynb`

This notebook now includes a bounded section for this investigation and uses generated artifacts under `data/interim/stage2_dengue_date_investigation/`.

## 7. Current status for decision handoff

- Reproduction of the 8,556 alerts: confirmed.
- No automatic correction applied: confirmed.
- Evidence package for human review: complete for this bounded Stage 2 increment.
- Stage 2 / G2 closure decision: out of scope for this task.