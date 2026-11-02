# EXP-BETA01 V2 — Conclusions

**Scientific disposition: `NO_RESPALDADA`.** Technical execution:
`COMPLETED_WITH_LIMITATIONS`, with real native-model replay verified. Evidence is
retrospective, covers four reused years and does not establish superiority or
operational early-warning performance. [Complete results](RESULTS.md).

## Question answered

Does adding eligible Colombian municipalities to fixed XGBoost training improve
H5 onset detection in Meta/Tolima compared with the frozen regional G0 OFF?
Under the frozen V2 features, roles, calibration and alert policy, **no relevant
improvement was demonstrated**. National G1 loses five detections and adds eight
false alerts in T+1, and loses one detection while adding 21 false alerts in T+2.
G0's aggregate primary detection/load pair is therefore better in both horizons.
This is evidence about this controlled procedure, not proof that all possible
national transfer methods are ineffective.

## What improved, and why it is insufficient

G1 improves AP and Brier against G0 in both horizons. These are favorable
descriptive ranking/probability findings, but they do not rescue the adopted
sensitivity/load objective. Against R0, T+1 meets the aggregate budget and margin;
T+2 loses 11.42 pp sensitivity and fails. The annual/territorial checks fail in
20/24 overlapping annual strata. Aggregate budget compliance in both horizons
cannot substitute for those controls, and no average-based winner is selected.

## Attribution and limits

- Regional X, labels and all five role key sets match V1 exactly. Frozen G0 and
  native R0 predictions remain unchanged. G0_MATCHED was not needed or fitted.
- Only training is expanded; regional calibration/selection/evaluation and the
  original 80-tree, depth-2 XGBoost configuration are fixed. No climate, new
  feature, geographic covariate, search, L1 or new alert method was introduced.
- National H5 support starts in June 2016 outside the original 76 territories.
  2020 has only six/five additional origin months. The observed intervention is
  adding the available national rows, not an isolated causal estimate of the
  number of municipalities independent of recency, season and heterogeneity.
- 2024 is previously consumed stress; no independent confirmation or 2025
  evaluation was performed. H5 is a retrospective proxy, not clinical truth.
- Source extraction completeness, historical boundary/geometry equivalence,
  unresolved territorial notifications, retained possible duplicates and
  point-in-time availability limitations remain those of the national source.
- Native execution/reproduction passes do not erase inherited CI/preservation
  issues or authorize merge. They remain reported separately from V2 defects.

Statistical noninferiority: `UNAVAILABLE`. Superiority: `NOT_ESTABLISHED`.
**G5 `NOT_APPROVED`; `champion: not_selected`.**

## Continuity decision

Do not automatically advance to national L1, NB2 or BETA03 V2 on this evidence.
The present G1 is not an improved alerting base, so no downstream national
extension is recommended as the next automatic phase. Better AP/Brier can
inform a future narrowly defined question, but any adaptation, count forecast
or policy investigation needs a new human decision and protocol. Keep V1's
scientific knowledge and frozen artifacts intact; this negative national result
is a new, independently identified contribution.
