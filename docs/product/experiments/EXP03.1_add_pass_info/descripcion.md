# EXP03.1 — Recent endemic-channel trajectory

EXP03.1 evaluates whether knowing how a municipality evolved over the previous year improves prediction of new episode onsets beyond the point-in-time information already used by EXP03 V09.

The experiment separates two non-overlapping periods: the recent semester (T−1 through T−6) and the preceding semester (T−7 through T−12). It represents the recent period with counts of SECURITY, WARNING, and EXCESS months. SUCCESS is reconstructed as six minus those counts and is not a redundant predictor. The trajectory block is the recent count minus the preceding count for the same three states; preceding counts remain audit values only.

Within officially covered periods, a month with no notification rows follows the approved project assumption and has zero cases; this does not prove active reporting. Outside coverage, or when a channel state cannot be reconstructed, the month remains unknown. Primary evaluation requires all twelve historical states to be known.

The three variants are the complete EXP03 V09 reference (M00), V09 plus recent channel memory (M01), and M01 plus semester-over-semester trajectory change (M02). M00 may reuse EXP03 artifacts only when every applicable cohort, label, ordered-predictor, preparation, family/configuration, temporal-protocol, budget, and code hash matches. Otherwise it is refitted on the common paired cohort.

The experiment retains EXP03's H5 channel semantics, families, T+1/T+2 horizons, temporal cuts, fixed configurations, and primary budget of one false onset alert per monitored municipality-year. It does not optimize hyperparameters or budget, choose a champion, approve G5, claim operational availability, evaluate 2025, or reinterpret EXP03.

The hypothesis is that recent state frequency and its change from the preceding semester add onset detection under the same false-alert budget. It is not supported when apparent gain comes mainly from continuations, increased alert load, calibration loss, or unstable year/territory/profile behavior. A favorable isolated result never selects a champion or approves G5.
