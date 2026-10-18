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
