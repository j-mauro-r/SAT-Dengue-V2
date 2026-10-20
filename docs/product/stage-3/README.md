# Training preparation — milestones 1 and 2

Notebook [04](../../../notebooks/04_training_preparation_pipeline.ipynb) is the code-only configuration, execution and bounded review entry point. The [modules](../../../scripts/training_preparation/__init__.py) reuse existing notebook 03 products without running consolidation or EDA. Run from the repository root or `notebooks/` using the repository Python environment. The CLI resolves the repository by its markers rather than a personal absolute path:

```bash
.venv/bin/python -m scripts.training_preparation.development
.venv/bin/python -m scripts.training_preparation.development --verify
```

The [preparation contract](training_preparation_contract_v1.json) remains separate from the [canonical 69-field dictionary](../stage-2/DATA-01-Priority%20Field%20Matrix.md). Its input schema mirrors the existing 51-column construction contract. It defines input roles and the development output roles without redefining scientific source concepts. The [milestone 1 evidence](milestone-1-validation.md) remains historical evidence for that implementation; notebook 04 now executes milestone 2. [Milestone 2 evidence](milestone-2-validation.md) records the current results.

Input validation checks exact schema/types/nullability, unique keys, complete monthly support including endpoints, DIVIPOLA scope, categories, coverage, count reconciliation, complete-day climate aggregation, target calendars and evaluability. SHA-256/byte verification includes the consolidated companion, panel, construction contract and trace files. Inputs are never repaired or rewritten. The standalone input audit remains available as `python -m scripts.training_preparation.audit`; `--baseline <path>` additionally checks a pre-task fingerprint map.

Development construction filters reference months after 2024-12 before typed validation and profiling. Full-file fingerprints remain necessary for source identity; string CSV reading and notification-year metadata reading do not analyze reserved outcomes. Reserved reference rows stay separately in the original input and produce no features or outcome summaries. In controls at development reference months whose target enters 2025, Y, target percentiles, history/evaluability/status metadata are masked in the output view; the known target date and an exclusion flag remain. Original scientific values are unchanged. No reserved outcomes enter X, eligibility counts or feature summaries.

The development feature table retains two current counts, all nine climate aggregates with their signs/units, current `zona_canal_t`, and these sixteen derived candidates:

| Columns | Definition |
|---|---|
| `dengue_lag_1/2/3` | General-dengue count at exactly T−1/T−2/T−3 |
| `grave_lag_1/2` | Severe-dengue count at exactly T−1/T−2 |
| `dengue_cambio_1m` | General-dengue count T minus T−1; negatives valid |
| `dengue_media_3m` | Mean of T, T−1 and T−2, requiring all three observations |
| `zona_canal_lag_1` | Existing zone at exactly T−1 |
| `lluvia_lag_1/2` | Rainfall at exactly T−1/T−2 |
| `temperatura_lag_1/2` | Temperature at exactly T−1/T−2 |
| `rocio_lag_1`, `escorrentia_lag_1` | Dewpoint and runoff at exactly T−1 |
| `mes_sin`, `mes_cos` | sin/cos of 2π(month−1)/12; January phase zero |

Lookups use `(municipality_code, calendar month)`, never global row position. Missing keys/history stay missing, not zero. The entire earlier history through 2024-12 is used before auditing supervised eligibility; no eligibility start truncates antecedents. No centered window, clipping, demographic variables, fitted imputation, scaling or statistical selection is applied. Input Y, zones and scientific percentiles are not recomputed. Candidate status is not demonstrated predictive utility.

Eligibility reuses the existing standalone readiness validator's notification-year-backed five-year policy and independent supervised selector through a small runtime adapter. Only ANO year metadata is read from the consolidated companion. Eligible target months must be within the policy interval and before the reserved block; these masks remain controls, not predictors. This is an audit of available examples, not the milestone 3 train/validation/test split. Features retain all development history regardless of label eligibility or missing predictors.

Outputs live under `data/processed/training_preparation/development/<identity>/` (gitignored): `features.csv` contains only 28 candidate columns, `keys.csv` contains two keys, and `controls.csv` repeats the keys alongside non-predictor metadata and horizon eligibility/exclusion flags. All tables use identical key-sorted row order. `manifest.json` records roles, row alignment, coverage, missingness, eligibility reconciliation and output hashes. No individual source case records are published.

Identity covers exact input/configuration bytes, all preparation Python modules, the existing eligibility script, notebook 04, project metadata and Python/pandas/NumPy versions. A data, configuration, code or runtime change creates a new directory. There is no unconditional cache reuse or replacement: default `reuse_identical` recomputes every output and requires the exact same files/bytes; contract policy `error` refuses existing output. Corrupted bundles fail and are never silently repaired. Publication holds an exclusive output lock, writes/fsyncs staged files on the same filesystem, then atomically renames the complete directory. `--verify` requires an existing matching bundle and performs no artifact writes. Keep prior identities as provenance; no `latest` pointer can silently select stale code.

The existing decisions still govern: general dengue defines Y and the current endemic zone; severe dengue remains separate. Combining counts for a new Y is a later experiment. Historical operational availability remains **unproven** because inputs are retrospectively consolidated. G2 and the scientific training contract remain open.

Execution checkpoint: local `.dwp/plans/PLAN_018_training_data_preparation/`, same branch and phase plan. Only milestones 1/2 are implemented. Milestone 3 must isolate horizon-aware temporal folds before any learned imputation, scaling, encoding, selection, resampling or calibration. The reserved block begins 2025-01; it must not guide feature selection. No model training or phase Final Review has run.
