# DATA-04 — Rules for the bounded retrospective review

Version: stage2-review-v1. These rules make PLAN_006 reproducible; they do not freeze the final Data Contract, target, training population or G2. Mauricio confirmed that no additional information is available about municipal reporting interruptions or incomplete downloads.

## What is counted

1. Keep dengue (event 210) and severe dengue (event 220) separate. Count supplied **notification rows**, not unique patients, episodes or confirmed incidence. Both probable and confirmed source classifications remain in this diagnostic population.
2. Attribute rows to municipality of residence using exact code membership in the supplied current DIVIPOLA catalog. Codes 50000/73000 remain in aggregate exceptions. The current catalog does not prove historical boundary stability.
3. Assign the original symptom-onset date, parsed as day/month/year. A missing/unparseable onset cannot be placed in a month and is reconciled separately. Never replace it with notification or exchange dates automatically.
4. Preserve all rows meeting those conditions. `CONSECUTIVE` alone is not a patient identifier: 762 dengue rows belong to repeated values across this departmental scope, whereas the observed year-plus-identifier candidate is unique. This is an export-key observation, not evidence that there are no repeated clinical episodes. No automatic deduplication or union of streams is justified.
5. Interpret TIP_CAS, AJUSTE, confirmation, hospitalization and vital status separately as documented in the [field matrix](DATA-01-Priority%20Field%20Matrix.md). `confirmados` is a supplied retrospective flag with unresolved generation/version semantics. AJUSTE 0/7 are not automatic discard codes. Future populations containing different states require a new review; the input-hash guard prevents unnoticed snapshot replacement.

## What missing information means

- `*_recorded_count` counts retained source rows. Its zero means that no retained rows were found, not that disease was absent.
- Nullable `dengue_count` and `severe_count` stay missing when no retained records exist. Reporting completeness remains unknown throughout.
- A month whose rows were removed by S2/S3 has an explicit scenario-removal state. This is different from a month without source records.
- No confirmed disease-zero month is certified. Such certification would require an explicit zero report or another reliable completeness source.
- Climate joins independently. Monthly values are means of the available daily variables, retaining their original units (daily rainfall mean is not monthly rainfall total). Expected versus observed days and variable-specific valid-day counts accompany them. No interpolation is performed. January 2020 remains missing for all 76 municipalities.

## Which months can participate

All 76 valid municipalities are represented in the audit grid. The shared descriptive window is January 2007–December 2025, 228 calendar months per municipality. Coverage is published by municipality; a municipal row in this inventory is not approval for forecasting.

For each association, both current and future dengue must have retained records, the feature must be available, and the same keys must be available under all three scenarios. Climate requires all expected days for that variable. This selected observed-positive sample supports bounded description only; it can exclude low-reporting periods and is not representative of all months. The number of usable pairs is reported for every result. No general predictive minimum-history threshold is approved here.

The 2013 historical comparator requires at least three observed same-calendar-month years from 2007–2012. It compares retained records to the prior observed maximum; it is neither an endemic channel nor an outbreak/target definition.

## What could have been known at the cutoff

Event time and information availability differ. The audit uses the end of each onset month as a **hypothetical** timing boundary, consistent with the product's monthly concept but without approving an exact production schedule or maturation delay.

| Field/source | What it establishes | What it cannot establish |
|---|---|---|
| INI_SIN | Recorded onset date | When the system first knew the event |
| FEC_NOT | Recorded notification date; a later date warns against use at the earlier cutoff | Full prior state or all subsequent revisions |
| FEC_AJU | Documented initial-entry/latest-adjustment meaning | Earlier versions of classifications and counts |
| FEC_ARC_XL | Export-generation timing | First availability of each field or row |
| confirmados / clinical outcomes | Consolidated export state | That the state existed at month end |
| Climate CSV | Retrospective daily measurements | Operational release time, historical product version or revision history |

In the full departmental onset-comparable scope (including unresolved municipal codes), 41,380/235,494 dengue rows and 811/4,619 severe rows have notification dates after onset-month end. The date in FEC_AJU is after that boundary for 107,326 dengue and 2,251 severe rows. These are timing warnings, not a reconstruction of all past records. `date_available_rows` in the audit means a **parseable date field**, not real-time availability.

With the available consolidated exports, historical as-of states cannot be reconstructed. No operational feature use or retrospective real-time performance claim is approved. A genuine operational evaluation needs versioned snapshots/revision records, publication timing for climate, a selected cutoff and a documented report-maturation policy. Those inputs are absent; asking Mauricio again does not supply them.

## Decisions and remaining evidence

Applied now: original onset, residence codes, exhaustive row reconciliation, independent source joins, explicit unknown reporting, separate source streams and S1/S2/S3 as uncertainty alternatives. These are bounded review rules.

Open: final case definition and episode identity; real reporting zeros/completeness; historical territory; January 2020 extraction provenance; true 2013 dates and final treatment; historic availability and maturation; prediction eligibility; endemic channel, Y and Data Contract. The plan can finish with these explicitly open; Stage 2 cannot be declared frozen from this review.

## Reproduce and inspect

```sh
.venv/bin/python scripts/stage2_panel_review.py --phase panel
.venv/bin/python scripts/stage2_panel_review.py --phase analysis
.venv/bin/python scripts/stage2_panel_review.py --phase rules
.venv/bin/python scripts/stage2_panel_review.py --phase validate
```

The three source snapshots and supplied references stay read-only. Local outputs live in `data/interim/stage2_panel_review/`: `retrospective_rules.json`, `municipality_coverage_eligibility.csv`, `availability_summary.csv`, classification/identity audits, `review_summary.json`, reconciliations, scenario comparisons and source hashes. No individual-level export is produced.
