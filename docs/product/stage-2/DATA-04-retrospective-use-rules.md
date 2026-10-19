# DATA-04 — Rules for the bounded retrospective review

Version: stage2-review-v1; baseline policy addendum 2026-10-18 (DEC-113). The existing machine-readable review outputs retain their original diagnostic version. These rules make PLAN_006 reproducible; they do not freeze the final Data Contract, target, training population or G2. Mauricio confirmed that no additional information is available about municipal reporting interruptions or incomplete downloads.

## What is counted

1. Keep dengue (event 210) and severe dengue (event 220) separate. Count supplied **notification rows**, not unique patients, episodes or confirmed incidence. Mauricio approved all supplied records for the baseline on 2026-10-18 (DEC-118): include probable and confirmed classifications without a confirmation-status filter. All source rows are preserved and reconciled; rows outside the study scope or without usable municipality/onset are accounted for separately rather than assigned invented keys.
2. Attribute rows to municipality of residence using exact code membership in the supplied current DIVIPOLA catalog. Codes 50000/73000 remain in aggregate exceptions. The current catalog does not prove historical boundary stability.
3. Assign the original symptom-onset date, parsed as day/month/year. A missing/unparseable onset cannot be placed in a month and is reconciled separately. Never replace it with notification or exchange dates automatically.
4. Preserve all rows meeting those conditions. `CONSECUTIVE` alone is not a patient identifier: 762 dengue rows belong to repeated values across this departmental scope, whereas the observed year-plus-identifier candidate is unique. This is an export-key observation, not evidence that there are no repeated clinical episodes. No automatic deduplication or union of streams is justified.
5. Interpret TIP_CAS, AJUSTE, confirmation, hospitalization and vital status separately as documented in the [field matrix](DATA-01-Priority%20Field%20Matrix.md). `confirmados` is a supplied retrospective flag with unresolved generation/version semantics. AJUSTE 0/7 are not automatic discard codes. Future populations containing different states require a new review; the input-hash guard prevents unnoticed snapshot replacement.

## Historical PLAN_006 missing-information policy (superseded for the baseline by DEC-120)

- `*_recorded_count` counts retained source rows. Its zero means that no retained rows were found, not that disease was absent.
- Nullable `dengue_count` and `severe_count` stay missing when no retained records exist. Reporting completeness remains unknown throughout.
- A month whose rows were removed by S2/S3 has an explicit scenario-removal state. This is different from a month without source records.
- No confirmed disease-zero month is certified. Such certification would require an explicit zero report or another reliable completeness source.
- Climate joins independently. Monthly values are means of the available daily variables, retaining their original units (daily rainfall mean is not monthly rainfall total). Expected versus observed days and variable-specific valid-day counts accompany them. No interpolation is performed. Historical audit evidence preserves that January 2020 was missing in the original local snapshot; after PLAN_010 controlled incorporation, January 2020 climate rows are now present for all 76 Tolima/Meta municipalities in the supplied local dataset.

## Approved baseline zero-count rule (2026-10-18)

Under DEC-120, municipality-months with no epidemiological source records within the supplied coverage are represented as zero counts for the baseline, separately for dengue and severe dengue. These are aggregate zero-case months under the approved reliance on supplied data, not fabricated patient records or independent proof of reporting completeness. Their provenance remains identifiable. A covered zero-case month is a valid value in the five-year same-month P75 reference; a genuinely unavailable historical observation is not. Do not infer municipal coverage from its first positive case. Months outside supplied coverage, unassignable case records, scenario removals and missing climate are distinct. January 2020 climate was not zero-filled; it was incorporated via recovered source rows in PLAN_010 with explicit backup and lineage artifacts. Previous generated PLAN_006 outputs retain the earlier policy and require regeneration before claims about the new zero-inclusive baseline/target population.

## Which months can participate (historical diagnostic support)

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

Applied now: original onset, residence codes, exhaustive row reconciliation, independent source joins, explicit unknown reporting, separate source streams and historical S1/S2/S3 sensitivity evidence. Mauricio subsequently selected S1 for the baseline: preserve the supplied 2013 records without anomaly-based deletion, date replacement or reassignment. Any replacement/removal experiments come after the baseline (DEC-113).

Resolved for the supplied baseline: all notification classifications are included (DEC-118), with no unsupported duplicate removal (DEC-114). Baseline assumptions now approved: all classifications, no unsupported deduplication, unchanged 2013 and covered no-case months as zero (DEC-113/114/118/120). Current Y configuration is approved under DEC-119/121. Remaining implementation/evidence: deterministic percentile/evaluability and consecutive-state rules, target sensitivity 5/7/9, baseline eligibility and Data Contract, plus upstream provenance verification of recovered January 2020 climate rows. Independent episode identity, completeness, true dates and historical availability remain documented limitations, not reopened baseline-selection questions. Operational re-execution is deferred to product work. Future-excess Y at T+1/T+2 and special attention to new onsets are already accepted in DEC-013/035/038. The plan can finish with these explicitly open; Stage 2 cannot be declared frozen from this review.

## Reproduce and inspect

```sh
.venv/bin/python scripts/stage2_panel_review.py --phase panel
.venv/bin/python scripts/stage2_panel_review.py --phase analysis
.venv/bin/python scripts/stage2_panel_review.py --phase rules
.venv/bin/python scripts/stage2_panel_review.py --phase validate
```

The three source snapshots and supplied references stay read-only. Local outputs live in `data/interim/stage2_panel_review/`: `retrospective_rules.json`, `municipality_coverage_eligibility.csv`, `availability_summary.csv`, classification/identity audits, `review_summary.json`, reconciliations, scenario comparisons and source hashes. No individual-level export is produced.

Post-incorporation rerun status (PLAN_011): the affected `stage2_panel_review` phases were re-executed in order (`panel`, `analysis`, `rules`, `validate`) after January 2020 climate incorporation. Reconciliation confirms unchanged epidemiological counts/rules and complete January climate coverage for the reviewed 76 municipalities. As expected, lag/window-sensitive association rows changed in support-linked statistics while keeping the same row membership keys. Historical outputs under `data/interim/stage2_monthly_sensitivity_associations/` remain preserved as historical reference and are not promoted as freshly recomputed post-incorporation evidence.


## Approved channel-method clarification (2026-10-18)

DEC-119 selects the INS median-and-percentile channel family, with excess strictly above P75, for the already approved monthly five-year same-month project configuration. The official [INS period-IV 2023 report, page 3](https://www.ins.gov.co/buscador-eventos/Informesdeevento/DENGUE%20PE%20IV%202023.pdf) documents weekly histories and distinguishes P75 from Bortman's upper confidence limit. Project-specific monthly/history choices remain explicit adaptations. That report does not provide a numerical sample-percentile interpolation convention. This subsequent method approval supersedes earlier method-selection uncertainty; target sensitivity and G2 remain unverified/open. The current-authority summary and DEC-121 in the [decision register](../traking-concluciones.md) now reconcile the complete approved PR #9 configuration and later zero-month decision with the preserved historical rules in this guide.
