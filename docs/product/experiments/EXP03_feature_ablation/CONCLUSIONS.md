# EXP03 conclusions — implementation validation, scientific results pending

The revised software implements the information-value questions in
[alcance.md](alcance.md). Engineering acceptance and independent review are
recorded in [IMPLEMENTATION.md](IMPLEMENTATION.md) and [REVIEW.md](REVIEW.md).
The frozen-source generated gate passed 170 checks plus scoped Python/documentation
quality; 25 public disposition contracts passed separately. Final presentation-only
refinements passed 19 focused checks without new estimator fits.
No scientific experiment was executed for this delivery.

- Scientific contribution, burden trade-offs and stability: **NOT_EVALUATED**.
- Numeric `B_primary=1.0`: **HUMAN_APPROVED_BEFORE_EXECUTION**.
- Scientific execution authorization: **PENDING**.
- Real 2024 stress and consumed-2025 benchmark: **PENDING**.
- Data coverage/maturity/publication-availability verification: **PENDING**.
- G5: `NOT_APPROVED`; champion: `not_selected`.

Synthetic probabilities, native estimator fits, plots and benchmark tables
exercise software only. They are never EXP03 findings. No private scientific
inputs, permanent MLflow writes, real scientific reservation or approval record
are part of this implementation task.

## Questions the authorized results must answer

1. What information helped exact-onset detection, by how much, and at what
   realized false-alert burden under the fixed selection-budget policy?
2. For which horizon, family, year, department and historical notification profile
   did the effect appear, with what support and paired uncertainty?
3. Did it repeat across development years, and what disappeared under the
   prespecified stale-input stress? What could not be issued without known Y(T)?
4. Do T+2 excess controls differ in common-onset alert utility and continuation
   burden? Probability metrics remain labelled by their different targets.
5. How do the same frozen terminal artifacts transport to 2024 and consumed 2025?

Lead with a decision table and link every numerical conclusion to native
contrast/cell/count/exposure evidence. Separate confirmed findings,
interpretations, limitations and future hypotheses. A null, adverse or
inconclusive result is informative. A non-significant difference is not
equivalence; unknown subgroup support never becomes pass. No automatic champion,
clinical usefulness margin or claim of real-time availability follows.

Development uses overlapping 2020–2022 OOF cuts, with paired municipality/year
resampling of counts and exposure. These are conditional retrospective intervals,
not independent replications. Stress 2024 and consumed 2025 stay outside those
intervals and candidate decisions; their pooled summary is descriptive only.
Actual issuance lead is unavailable without publication evidence.

## Version boundary

The current [protocol](protocol.json) and [matrix](ablation-matrix.frozen.yml)
encode 16 unique sets, four primary and twelve secondary ablations, 384 onset
cells and 24 T+2 excess controls: 408 maximum fits and 102 terminal cells.
The prior hash `c2f445e767b36dfac5acebca865775d793a93c2a75dc05d829bce82257b57396`
is retained as legacy provenance in Git and the revised protocol. Its reported
94 generated tests do not certify this expanded scope or authorize its execution.
EXP00/EXP01 consolidated scientific conclusions and identities remain preserved.
