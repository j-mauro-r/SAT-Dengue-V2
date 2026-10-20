# Training preparation — milestone 1

Notebook [04](../../../notebooks/04_training_preparation_pipeline.ipynb) is the code-only configuration, execution and aggregate review entry point. It imports the [reusable modules](../../../scripts/training_preparation/__init__.py); no notebook 03 execution or consolidation import is needed. Run with the repository Python environment from the root or `notebooks/`. For command-line validation:

```bash
.venv/bin/python -m scripts.training_preparation.audit
```

Inputs must already exist. Missing, stale, schema-incompatible or fingerprint-incompatible products fail without repairs. The reader preserves missing values, approved count zeros and empty trace strings. No input is written, no rows are dropped and no training matrix is persisted. Full-file SHA-256 verification includes the consolidated companion, panel, construction contract and trace files; only the monthly panel is loaded into memory. Manifest and preparation-contract fingerprints are also recorded and rechecked after reading. An optional `--baseline` JSON maps repository-relative paths to SHA-256/byte records for before/after preservation checks.

The [preparation contract](training_preparation_contract_v1.json) is separate from the [canonical 69-field dictionary](../stage-2/DATA-01-Priority%20Field%20Matrix.md). Its exact 51-column panel schema mirrors the existing construction contract; it does not redefine source concepts. Roles partition every field into two keys, candidate X, two Y columns and controls. The explicit candidate X allowlist includes current separate counts, existing monthly climate aggregates and `zona_canal_t`. All keys, labels, target periods, target percentiles, history/evaluability metadata, geography names/codes, current channel percentiles, day-coverage metadata and combined counts are excluded from X. These are preparation roles, not a finding that any candidate has predictive value. Candidate selection has not used reserved-block results.

Y and the current endemic zone retain general dengue. Severe dengue stays a separate possible predictor; combining counts to redefine Y is a later experiment. No label, percentile, zero policy or scientific source is recomputed. Historical operational availability remains **unproven**: inputs are retrospective consolidated data. This bounded scaffold does not close G2 or claim a frozen training contract.

The modules validate semantic dtypes/nullability, exact columns, unique keys, complete monthly support including endpoints, DIVIPOLA scope, manifest dimensions, categories, coverage flags, separate count reconciliation, complete-day climate aggregates, and horizon/evaluability metadata. Missing climate and non-evaluable labels remain missing; reports expose missingness rather than impute it. Existing upstream scientific and temporal checks remain enabled.

Milestone 2 must implement municipality-local dengue lags 1/2/3, severe dengue 1/2, rain and temperature 1/2, dewpoint and runoff 1, monthly dengue change, a past-only dengue mean, previous zone and cyclic calendar. Specify the rolling window and minimum observations before implementation; retain warm-up missingness and prove that changing future rows cannot change earlier features. This milestone has not run.

Milestone 3 must prepare horizon-aware temporal partitions using existing controls (`target_period_t1/t2` and the reserved block beginning 2025-01). Learned imputation, scaling, category encoding, feature selection, resampling and calibration belong inside each training fold if subsequently authorized. Deterministic shifts/calendar operations remain separate. No global imputation or final-block feature selection is permitted. This milestone has not run.

Execution checkpoint: local `.dwp/plans/PLAN_018_training_data_preparation/`. The phase remains incomplete; only milestone 1 is authorized by the current request. Independent final review remains a later plan task, not an earned milestone-1 claim.
