# EXP-DELTA02-R1 — recent neighboring epidemiological activity

Status: `PROTOCOL_FROZEN`; no R1 feature, fit, prediction, or result exists yet.

This independent revision tests one controlled intervention: append the mean of
MGN 2018 neighbors' general-dengue notifications at T−1 to the inherited
G0_OFF XGBoost procedure, then evaluate the unchanged academic T+1 cohort and
comparators. The [protocol](PROTOCOL.md) and machine-readable
[configuration](protocol.json) were frozen before implementation or training;
[sources.json](sources.json) pins every private input and preserved dependency.

## Lineage and preservation

PR #76 remains open. R1 branches independently from updated `main` and imports
commit `b3c982f` as an explicit dependency. The original
[EXP-DELTA02](../EXP-DELTA02/README.md) `NOT_EVALUABLE` result is preserved in
full. Its cross-vintage uncertainty is not erased: R1 records Mauricio's new
methodological decision to use MGN 2018 as one fixed retrospective approximation.

## Planned execution

The maintained R1 entrypoint will verify the exact source bundle before fitting,
construct only `neighbor_dengue_mean_lag1`, train one candidate, perform the
paired T+1 evaluation, and write one immutable private publication. No dataset
download or geography research is part of reproduction.

```bash
PYTHONPATH=tmp/exp-delta02/vendor KEDRO_DISABLE_TELEMETRY=yes \
  .venv/bin/python scripts/run_exp_delta02_r1.py --publish
```

This command is intentionally unavailable until the feature/candidate tasks
implement and validate the entrypoint. The testing map owns proportional gates.
Final aggregate evidence will be published in `RESULTS.md` and
`CONCLUSIONS.md`; neither file is created before real execution.

## Boundaries

The evidence is retrospective and exploratory. Consolidated notifications do
not prove historical delivery at origin T, MGN 2018 is not asserted to encode
every historical boundary, and the consumed periods cannot provide independent
confirmation. This revision cannot select a champion, change G5, start T+2 or
EXP-DELTA03, or authorize merge/deployment.
