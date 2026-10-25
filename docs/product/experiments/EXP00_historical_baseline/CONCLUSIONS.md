# EXP00 — Historical pre-Kedro baseline conclusions

## Status

- Historical scientific conclusion: **complete**.
- Guarded Kedro reproducibility verification: **passed** on 2026-10-25.
- Formal MLflow registration with conceptual experiment tags: **pending**.
- G5: **NOT_APPROVED**.
- Champion: **not_selected**.

## Result

The retained XGBoost, LightGBM and GAM procedures for T+1 and T+2 improved
onset detection over persistence, but all six candidate/horizon procedures
exceeded the predeclared false-alert constraint. Every candidate decision remains
`does_not_meet`. This is the scientific comparison baseline for future work, not
an approved operational model.

## Reproducibility evidence

The protected Kedro E2E and migration-parity suites completed with **78 passed,
0 failed and 8 non-blocking warnings** in 1,492.84 seconds. They verified saved
component replay, complete lineage and preservation, deterministic restart and
zero real fitting or refitting.

Command:

```bash
python -m pytest \
  tests/integration/test_kedro_e2e.py \
  tests/integration/test_migration_parity.py \
  --require-migration-evidence -q
```

## Interpretation and limitations

- The 2025 comparison block is consumed and remains replay-only.
- Replay verifies reproducibility; it does not provide new independent evidence.
- The data are retrospectively consolidated and do not prove historical
  operational availability.
- No candidate is authorized for deployment or online inference.

## Pending formal-registration work

The conceptual-tag implementation is authorized and covered by synthetic tests.
The formal replay remains pending by explicit user instruction; no formal run ID
has been assigned. `mlflow_registration: pending` remains the registry state.

1. Run the documented formal command in the [registry guide](../README.md).
2. Verify the returned parent/children, protocol hash, bundle and zero real-adjustment counters.
3. Record the actual MLflow run ID, bundle ID, commit and registration date here.

Before the first formal registration, PLAN_032 removes the mutable registration
status and obsolete implementation note from the protocol, as explicitly authorized
by the user. The registry contains the updated canonical hash and remains pending.
After first formal execution, the protocol is immutable: add the actual run ID,
date and conclusion here, and update `mlflow_registration` in the registry only.
Scientific content, conceptual tags and historical results are unchanged.
