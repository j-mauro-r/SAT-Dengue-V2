# EXP-DELTA02 — results

**Spatial feasibility: `NOT_EVALUABLE`; scientific disposition: `NOT_EVALUABLE`;
execution: `COMPLETED_WITH_LIMITATIONS`.** Stage 1 was executed on real sources.
Stage 2 was not admitted. No candidate feature or fitted/predicted output exists.
The [protocol](PROTOCOL.md) fixes the gate; [provenance](PROVENANCE.json) binds
source, code, runtime and publication identities. These are implementer findings,
not independent scientific approval.

## Official geography and topology

All national code fields are unique five-character DIVIPOLA strings. Every
snapshot includes the exact 76 regional targets. Edge counts below are distinct
undirected pairs with at least one target endpoint, including external neighbors;
point-only contacts are excluded. They are alternative source graphs, not models.

| Official archive | National territories | Valid polygons nationally | Target-related edge pairs | External neighbors | Point-only pairs |
| --- | ---: | ---: | ---: | ---: | ---: |
| MGN 2005 | 1,119 | 1,117 | 284 | 63 | 9 |
| MGN 2018 | 1,122 | 1,122 | 288 | 66 | 7 |
| MGN 2021 | 1,121 | 1,121 | 289 | 67 | 7 |

All targets and all national polygons screened by their bounding boxes are valid.
The two invalid 2005 polygons are outside that screened set. The 2005 graph has
16 directed positive-overlap observations with maximum area
7.922039662656244e-12 native degrees squared; these tiny numerical/topological
artifacts are disclosed, not used as the material stop or silently repaired.
The 2018/2021 target-related intersections have no positive-area overlap.
No self-edge is retained. There are 291 distinct positive-boundary pairs in the
union of all three graphs; the union is not admitted for feature construction.

| Transition | Removed positive-boundary pairs | Added positive-boundary pairs |
| --- | --- | --- |
| 2005 → 2018 | 41001–73067; 41357–73555 | 25372–50686; 25488–73352; 41016–73555; 41524–73555; 41801–73555; 73168–76834 |
| 2018 → 2021 | none | 41799–50370 |

**Nine relations differ, affecting six targets:** Uribe (50370), San Juanito
(50686), Ataco (73067), Chaparral (73168), Icononzo (73352), Planadas (73555).
For example, 41357–73555 shares 0.3873659170 native degrees of boundary in 2005
and none in 2018; 41801–73555 shares none in 2005 and 0.3945843669 in 2018.
These are not rounding-sized changes in the specified edge predicate. Lengths
are angular diagnostics within each source CRS, not physical distances.

The shape metadata contain edition/creation dates, rather than a relation-level
valid-time crosswalk: the 2018 XML even retains required-placeholder publication
and ground-date fields. They cannot resolve whether a difference is cartographic
correction, territorial change or another source discrepancy, or establish its
applicability to the canonical historical notifications. No dated resolution of
these nine relations was admitted. Vintage equality/code equality cannot fill
that gap. Selecting a single vintage or switching graphs at edition years would
assume the answer. This is the material historical-admission stop.

## Epidemiological coverage and timing

The pinned national CSV hash reconciles to
`66c58d862f397b7953f7b32cfb6399330acc86e0acab1b5e3a6e809ea4b392d0`.
All municipality-month keys are unique; counts are nonnegative integers. All
targets and the potential external neighbors from all three graphs are checked
against the national canonical table. Its historical applicability remains
`UNVERIFIED`; snapshot coverage does not certify territorial/reporting identity.

| Diagnostic population | Territories | Monthly rows | Period | Null general-dengue counts | Zeros, all flagged zero-from-absence |
| --- | ---: | ---: | --- | ---: | ---: |
| National | 1,122 | 182,886 | 2011-06–2024-12 | 0 | 106,946 |
| Original Meta + Tolima targets | 76 | 12,388 | 2011-06–2024-12 | 0 | 3,584 |
| Potential external neighbors, union of unadmitted graphs | 68 | 11,084 | 2011-06–2024-12 | 0 | 4,866 |

The calendar therefore contains all potential-neighbor codes and 163 months,
but zero-from-absence is not demonstrated absence of dengue or complete negative
reporting. The source's approved zero rule is preserved. No new missing-to-zero
conversion or epidemiological adjustment was made. External pre-2011-06 history
and publication/notification revision vintages are not established here.
T−1 is the only proposed source month; no signal is constructed and no future
outcome enters a spatial feature. Temporal-prefix tests on an actual feature
remain blocked, not passed by inspection of this proposed formula.

## Original T+1 controls — context only

The original cohort remains **2,653 observations, 76 municipalities, 313 onsets**.
The following are unchanged benchmark metrics read from its verified publication;
they are not new EXP-DELTA02 predictive results. There is no matched candidate
cohort, measured candidate coverage loss, paired decision change, AP/Brier
comparison or incremental false-alert cost. Those quantities are unavailable,
not zero. None of the six geographically affected municipalities is excluded.

| Frozen arm | Detected/onsets | Missed | Sensitivity | Alerts | False excess alerts | FAR-excess | FAR − CHANNEL (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CHANNEL | 94/313 | 219 | 30.03% | 179 | 85 | 47.49% | +0.00 |
| G0_OFF | 146/313 | 167 | 46.65% | 325 | 179 | 55.08% | +7.59 |
| PERSISTENCE | 0/313 | 313 | 0.00% | 0 | 0 | undefined | undefined |
| R0 | 142/313 | 171 | 45.37% | 373 | 231 | 61.93% | +14.44 |

At T+1 on this non-excess-at-T cohort, false onset alerts equal false excess
alerts. The CHANNEL-relative ceiling is exactly 85/179 + 0.05, approximately
**52.49%**; it is a reconciliation result, not a fitted threshold. R0 and G0_OFF
satisfy A and B and fail C. PERSISTENCE emits no alerts, so its FAR is undefined.
**Candidate A/B/C and their conjunction are not evaluable.**

### Annual and departmental context

Each model cell shows **detected onsets; FAR-excess**. These are the original
paired benchmark strata; no candidate value is imputed. All 60 T+1 comparator
strata, including annual totals and pooled department totals, are preserved in
the private result's `baseline_t1.csv` and the existing public
[benchmark table](../benchmark/METRICS_BY_STRATUM.csv).

| Target year | Department | Rows; true onsets | CHANNEL | R0 | G0_OFF |
| --- | --- | ---: | ---: | ---: | ---: |
| 2020 | Meta | 281; 26 | 7; 61.11% | 12; 63.64% | 12; 57.14% |
| 2020 | Tolima | 380; 43 | 11; 56.00% | 19; 73.61% | 20; 62.96% |
| 2021 | Meta | 318; 24 | 6; 33.33% | 4; 78.95% | 6; 66.67% |
| 2021 | Tolima | 528; 28 | 4; 69.23% | 9; 68.97% | 4; 78.95% |
| 2022 | Meta | 210; 49 | 13; 38.10% | 16; 52.94% | 30; 45.45% |
| 2022 | Tolima | 483; 40 | 11; 50.00% | 17; 62.22% | 19; 64.81% |
| 2024 | Meta | 215; 47 | 21; 44.74% | 34; 44.26% | 26; 33.33% |
| 2024 | Tolima | 238; 56 | 21; 36.36% | 31; 61.25% | 29; 50.00% |

All these years are consumed retrospective evidence. No temporal or territorial
benefit from spatial information is inferred from the controls.

## Validation record

- PASS: exact source-manifest/payload identities before and after execution;
  complete target/code/calendar coverage; polygon/point/edge/self-exclusion audit;
  frozen comparator controls; no source/publication replacement.
- PASS: alternate DE-9IM boundary-contact predicate independently recomputes
  all 288/289 target-related edge pairs in 2018/2021. This is an implementer
  arithmetic check, not an independent scientific review.
- PASS: synthetic edge, point-only, disjoint and invalid-polygon checks; three
  generated source-tampering cases (payload, manifest and unexpected file).
- PASS: the final result publication is byte-identical on repeated execution,
  with all six files reused unchanged. Provenance records the exact identity.
- PASS: all 420 upstream source records in the frozen benchmark manifest,
  including 120 model binaries, match their historical digests; no model is loaded
  or executed. The four direct source publications and new geography source bundle
  also pass before/after payload checks.
- PASS: five focused tests (three generated tampering cases, registered-directory
  boundary, script orchestration/tracking-import boundary); scoped Ruff/format,
  mypy, Markdown links, diff whitespace and changed-file security checks.
- PASS: repository-only conformance, 17 checks. Scoped-plan conformance: not
  applicable to this direct bounded task. All-plan conformance: FAIL on the two
  inherited records, 465 checks passed and 60 advisories. These are
  `PLAN_012_retire_experimental_eda`'s unresolved critical-review record and
  `PLAN_stage2_data_understanding_initial_recognition`'s mixed legacy lifecycle;
  neither was edited or waived. They are not current experimental code failures.
- Candidate-specific feature-prefix, fitted temporal roles, cohort/label pairing,
  A/B/C and prediction reproduction: BLOCKED / not executed at the geography gate.

No historical experiment, notebook or model was rerun. Required remote CI and
independent scientific review remain separate integration evidence. G5
`NOT_APPROVED`; `champion: not_selected`.
