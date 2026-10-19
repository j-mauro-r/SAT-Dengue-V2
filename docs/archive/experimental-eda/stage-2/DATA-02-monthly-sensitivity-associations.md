> **DEPRECATED — experimental EDA retired on 2026-10-19 by Mauricio.** Historical evidence only; the [active decision register](../../../product/traking-concluciones.md) governs current scientific decisions. Instructions, pending reruns, results and dates below describe the historical experiment and are not current execution requirements.

# DATA-02 Monthly Sensitivity and Temporal Associations (Exploratory)

> Historical PLAN_005 results. The source joins and association interpretations below are superseded by the [PLAN_006 review](DATA-03-panel-review.md). Original outputs are preserved for audit. Its severe/climate joins lost support, unknown codes entered the panel, and missing reporting was filled with zeros. Do not use the historical candidate list as a validated selection.

## Scope
This report documents a reproducible exploratory study of monthly municipality-level dengue (210) and severe dengue (220) behavior in Tolima and Meta under three anomaly-handling scenarios for 2013 date inconsistencies.

The analysis is bounded to Stage 2 data understanding:
- No causal claims.
- No claim of demonstrated predictive utility.
- No final model training or champion selection.

## Inputs and Reproducibility
- Raw sources:
  - `data/raw/dengue.csv`
  - `data/raw/dengue_grave.csv`
  - `data/raw/google_earth_engine.csv`
- Reproducible pipeline script:
  - `scripts/stage2_monthly_sensitivity_analysis.py`
- Reproducible notebook:
  - `notebooks/02_stage2_monthly_sensitivity_associations.ipynb`
- Output directory:
  - `data/interim/stage2_monthly_sensitivity_associations/`

## Scenario Definitions (S1/S2/S3)
Scenario differences are applied only to the anomaly group `INI_SIN > FEC_NOT`:
- S1: keep all anomaly rows in onset month.
- S2: keep anomaly rows only when onset year-month equals notification year-month; drop the rest.
- S3: drop all anomaly rows.

All non-anomaly rows are treated identically across scenarios.

## Anomaly Reproduction
Reproduced in scope (Tolima/Meta residence):
- Total anomaly rows: 8556
- Same onset/notif year-month: 784
- Different onset/notif year-month: 7772

Reference match status: exact match.

Artifacts:
- `anomaly_cardinality_summary.csv`
- `anomaly_distribution_by_geo.csv`
- `anomaly_discrepancy_log.md`

## Monthly Sensitivity Findings
Scenario impact on retained dengue records:
- S2 vs S1: -7772 records (about -3.3% global impact in scope).
- S3 vs S1: -8556 records (about -3.6% global impact in scope).

Department-level relative impacts:
- Meta: S2 -3.04%, S3 -3.38%
- Tolima: S2 -3.52%, S3 -3.84%

Impacts are concentrated in specific municipality-month windows and alter some peak magnitudes and active-month continuity, with smaller peak-month timing shifts.

Artifacts:
- `monthly_panel_s1.csv`, `monthly_panel_s2.csv`, `monthly_panel_s3.csv`
- `sensitivity_summary_by_geo.csv`
- `sensitivity_peak_continuity_changes.csv`

## Column Inventory and Eligibility
The 69 dengue fields were inventoried and classified by analytical role:
- identifier
- date
- demographic/context category
- post-event or classification
- metadata/time index
- insufficient definition or other

Eligible-for-association fields are represented as monthly counts/proportions/summaries with explicit caveats and timing notes.

Artifact:
- `field_analytic_eligibility.csv`

## Temporal Associations (Exploratory)
Associations were estimated for pooled, department, and municipality strata with explicit direction:
- contemporaneous (`t` vs `t`)
- lead (`t` vs `t+1`)
- lead (`t` vs `t+2`)

Methods:
- raw Spearman associations
- controlled partial Spearman with trend/seasonality/autocorrelation controls
- circular-shift permutation p-values for selected pooled lead analyses
- BH q-values for multiplicity in grouped raw tests

Artifacts:
- `associations_raw.csv`
- `associations_controlled.csv`
- `associations_municipal.csv`
- `associations_stability_summary.csv`
- `associations_method_notes.md`

## Stability Summary Across Scenarios
From `associations_stability_summary.csv`:
- Rows evaluated: 112
- Stable across S1/S2/S3: 111
- Sensitive to 2013 treatment: 1

The single scenario-sensitive row is:
- controlled, `severe_count`, horizon `t+1`, with near-zero sign-switching values.

## Candidate Variables for Later Predictive Evaluation
Exploratory candidates for later strict temporal validation (not yet predictive proof):
- `dengue_count` (strong lead autocorrelation signal)
- `severe_count`
- `confirmed_prop`
- `temp_mean_c`

Lower-priority or unstable/marginal candidates should be re-checked under as-of reconstruction and final label design.

## Key Limitations
- Current sources are retrospective consolidated exports, not fully reconstructed as-of historical availability snapshots.
- Final Y-channel and final label design decisions remain open.
- No out-of-time model training/testing was performed in this study.

## Proposed Validation Path (Not Executed Here)
Suggested next bounded step before modeling decisions:
- expanding-window temporal validation, separated by T+1 and T+2,
- strict holdout isolation,
- feature selection only within allowed historical windows,
- explicit maturation policy for delayed variables.

## Final Interpretation Guardrail
All findings here are exploratory association evidence under transparent scenario stress tests. They do not establish causal influence or validated predictive utility in operational conditions.
