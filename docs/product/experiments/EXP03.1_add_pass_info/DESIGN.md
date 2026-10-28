# EXP03.1 executable scientific design

Status: **implemented infrastructure; scientific execution pending and unauthorized**.

EXP03.1 asks whether an exact-calendar representation of the recent endemic-channel trajectory improves future-onset detection relative to complete EXP03 V09 at the same fixed false-alert budget. [The normalized human source](descripcion.md) owns intent; [protocol.json](protocol.json) and [the frozen matrix](ablation-matrix.frozen.yml) own executable identities.

## Feature contract

At origin T, reconstruct each historical channel zone as it was knowable at its own month, using five prior observations of the same calendar month, NumPy/type-7 P75, epidemic years included, and strict observed count `> P75` for EXCESS. Recent months are T−1…T−6 and prior months are T−7…T−12. Gaps are never crossed or compacted.

Predictors are exactly the three recent counts and three recent-minus-prior changes for SECURITY, WARNING, and EXCESS. SUCCESS is audit-reconstructed; prior counts, coverage, and exclusion reasons are audit-only. Primary rows require twelve known zones. Covered no-notification months are zero cases under DEC-120 but do not prove active reporting; uncovered or unreconstructable months remain unknown.

## Paired comparisons and temporal roles

M00/M01/M02 share rows, labels, family, horizon, cut, cohort, selection policy, and exposure denominators. Q1=M01−M00, Q2=M02−M01, Q3=M02−M00. T+1 uses onset only. T+2 uses onset as primary and excess controls for M00/M02. Development 2020–2022 remains overlapping retrospective OOF history; stress_2024 cannot select configuration; 2025 is rejected.

M00 is a V09 reference, not a champion. Reuse is fail-closed across every declared hash. Any cohort change forces refit on the intersection. Counts derive from one canonical matrix: refit path 72 onset + 24 excess = 96 fits; complete reuse path 36 reused M00 cells + 60 new fits; 24 terminal cells.

## Interpretation boundary

Reports retain adverse, null, and unknown outcomes; distinguish FAR from FPR; separate onset, continuation, no excess, and T+1-prior onset for T+2; and keep 2024 outside development intervals. Absence of significance is not equivalence. Delay is a frozen-model conditional predictor stress and separately records strict inability to issue when Y(T) is unavailable.

G5 remains `NOT_APPROVED`; champion remains `not_selected`. This implementation creates no scientific result.

