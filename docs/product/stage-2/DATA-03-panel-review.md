# DATA-03 — Independent-source monthly panel review

Stage 2 remains open. This bounded review implements the three-step request recorded in PLAN_006_stage2_panel_review. The user has no further evidence of reporting interruptions or incomplete downloads.

## Reproduction

Use the existing project environment:

```sh
.venv/bin/python scripts/stage2_panel_review.py --phase panel
```

Outputs are aggregate local evidence under `data/interim/stage2_panel_review/`; raw/reference files and PLAN_004/005 outputs remain unchanged. `input_hashes.json` binds the supplied files and previous results. Current catalog membership is not proof of historical territorial continuity.

## Panel meaning

Each row is one catalog municipality and calendar month in the union of source date ranges. Dengue, severe dengue and climate are joined independently to that grid. Codes absent from the supplied 76-municipality catalog are quarantined, never assigned by name. Missing onset cannot enter a monthly count and remains in reconciliation.

`*_recorded_count` measures source rows, including a numerical zero when no rows were found; that zero is not a certified absence of disease. Nullable `dengue_count`/`severe_count` remain missing when no retained records exist. States distinguish records present, no records/reporting unknown, and records removed by a scenario. No month is assigned a confirmed-zero status because no completeness evidence was supplied.

Climate retains daily coverage counts and expected calendar days; incomplete months are visible without imputation. The 2007–2025 common source window is flagged for descriptive comparisons, not automatically approved for operational training. January 2020 remains absent.

## Validation

The panel gate checks municipal membership, unique keys, exhaustive source reconciliation, severe/climate equality across scenarios, unknown states and January 2020. Synthetic tests exercise a month with climate/severe records and no dengue, complete scenario removal, unknown codes and date parsing. Later plan tasks add sensitivity and availability evidence before the review closes.

## Step 1 results

The 76-municipality grid includes 17,936 rows per scenario (2006-06 through 2026-01). Source reconciliation retains 235,111 dengue rows, separates 383 unresolved municipal-code rows and seven missing-onset rows, and preserves all 4,598 geographically identified severe-dengue rows. The other 21 severe rows remain in unresolved-geography reconciliation. Their separation is explicit; no patient deduplication or date replacement is applied. The former panel kept 4,501 severe rows including unresolved codes; comparisons must account for this changed territorial scope rather than subtracting totals blindly.

Evidence: `dengue_reconciliation.csv`, `severe_reconciliation.csv`, `municipality_catalog.csv`, `monthly_panel_s1.csv` through `monthly_panel_s3.csv`, `climate_gaps.csv`, and source hashes in the output directory.

## Step 2 protocol

Run `.venv/bin/python scripts/stage2_panel_review.py --phase analysis` after the panel phase. S1 retains all anomaly rows, S2 removes only cross-month anomalies, and S3 removes all anomalies; each is applied only to included valid-geography rows. Unresolved-geography anomalies remain in the separate audit, which explains differences from the original 8,556/7,772 scope.

The 2013 comparison reports each municipality-month and **all tied peak months**, not an arbitrary first maximum. A descriptive comparator asks whether retained 2013 records exceed the maximum of available same-calendar-month observations in 2007–2012, requiring at least three observed years. Missing historical months are not zero. This comparator is neither an endemic channel nor a target label; it only illustrates scenario sensitivity.

Annual references are re-read from the supplied Excel files and matched on unique within-year export identifiers. Genuine inverted pairs require unequal onset and notification dates. Annual file agreement cannot establish historical authenticity or the correct date.

The association rerun retains the previous variables and horizons, on the same eligible keys across scenarios. Unknown current/future dengue months are excluded, which creates a selected observed-positive sample and prevents population-wide interpretation. Climate requires complete daily coverage. Adjusted lead correlations include municipal effects, trend, annual seasonality and current dengue rank for other predictors; self-conditioning and contemporaneous adjusted rows are omitted. No p-values, significance claims or feature-selection recommendation are issued because the prior permutation design was not established for missing-coverage data.

Decision for this bounded study: preserve S1/S2/S3 as uncertainty scenarios. No option is approved as the true 2013 history or a production cleaning policy. Prefer repairing source lineage before any irreversible scientific selection; otherwise carry the scenarios into a later human decision.
