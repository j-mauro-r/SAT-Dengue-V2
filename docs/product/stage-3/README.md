# Training preparation — deterministic and temporal pipeline

Notebook [04](../../../notebooks/04_training_preparation_pipeline.ipynb) is the code-only configuration, execution and bounded review entry point. The [modules](../../../scripts/training_preparation/__init__.py) reuse existing notebook 03 products without running consolidation or EDA. Run from the repository root or `notebooks/` using the repository Python environment. The CLI resolves the repository by its markers rather than a personal absolute path:

```bash
.venv/bin/python -m scripts.training_preparation.development
.venv/bin/python -m scripts.training_preparation.development --verify
```

The [preparation contract](training_preparation_contract_v1.json) remains separate from the [canonical 69-field dictionary](../stage-2/DATA-01-Priority%20Field%20Matrix.md). Its input schema mirrors the existing 51-column construction contract. It defines input roles and the development output roles without redefining scientific source concepts. The [milestone 1 evidence](milestone-1-validation.md) remains historical evidence for that implementation; notebook 04 now integrates the complete preparation pipeline. [Milestone 2 evidence](milestone-2-validation.md) records the current results.

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

Execution checkpoint: local `.dwp/plans/PLAN_018_training_data_preparation/`, same branch and phase plan. All three implementation milestones are integrated; final review/closure is recorded in the same plan. Fitted preprocessing is isolated by horizon and training window. The reserved block begins 2025-01 and never guides feature selection. No predictor training has run.

## Temporal preparation and inference interface (milestone 3)

The [milestone 3 evidence](milestone-3-validation.md) records the completed temporal construction. Install the notebook tooling only when executing or verifying saved notebook outputs (`pip install -e '.[dev,notebook]'` in the repository environment). No estimator library is needed:

```bash
.venv/bin/python -m scripts.training_preparation.temporal
.venv/bin/python -m scripts.training_preparation.temporal --verify
.venv/bin/python -m scripts.training_preparation.notebook_execution --execute
.venv/bin/python -m scripts.training_preparation.notebook_execution --verify
```

`temporal` calls the same input and deterministic feature modules, then consumes their verified immutable tables. It reuses `select_supervised_rows`, `independent_select_supervised_rows` and the existing temporal audit, without rerunning experimental EDA. The configured policy remains evaluable targets in 2012-01 through 2024-12, reserved targets from 2025-01 excluded, and fit cutoffs 2018-12, 2020-12, 2022-12 and 2024-06. Training Y must be observable by the cutoff. Validation requires origin >= cutoff and target in the six configured months after it. T+1 therefore covers all six target months; T+2 covers the last five because the first configured target would require a pre-fit origin. Actual origin/target ranges are stored separately from configured bounds. Each later origin is a successive prediction using information at that origin; these rows are not a multi-month forecast issued once at the initial cutoff.

X/Y and key/index CSVs are separate for each of eight horizon/cutoff combinations. The only key explicitly introduced into raw model X is `municipality_code` as the user-authorized categorical representation; `year_month`, target history/evaluability and all other controls stay outside X. Thus deterministic `features.csv` retains 28 candidates while raw model X has 29 columns. This is a representation step, not a new demographic variable or result-driven selection.

`PreparerSpec` configures `native`, `onehot` or `ordinal` categories; numeric scaling is independently `none` or `standard`. The two persisted default profiles are `native` without scaling (29 columns) and `onehot_standard` (114 columns). They are generic future-estimator options, not a claim that every estimator accepts the same dtype, scaling or missing-value policy. No predictor or Y-based encoding is fitted.

The four known zone categories are EXITO, SEGURIDAD, ALERTA and EXCESO. Missing categories use `__MISSING__`, distinct from SEGURIDAD; unknown zones error. Municipality vocabularies are learned from X_train only; unseen values use a saved `__UNKNOWN__` category or error by configuration. No validation categories extend the training vocabulary. Standard scaling uses training means and population standard deviations; constant columns use scale 1. Default numeric missingness policy is error because eligible inputs are complete. Optional `preserve` keeps numeric NaN without imputation; scaling an entirely missing training column fails explicitly. Earlier insufficient-history rows remain visible in the deterministic bundle and are never manufactured into eligible examples.

Each window/horizon/profile stores safe JSON state: names/order of raw and transformed columns, category vocabularies/order, numeric parameters, configuration, exact training-X fingerprint and Python/pandas/NumPy versions. Validation and inference call `transform_predictors` with that state and never refit it. Strict input-column order and version checks prevent silently changed inference representation. No pickle deserialization or external model code is involved.

Temporal bundles live in `data/processed/training_preparation/temporal/<identity>/`, with raw X, Y, original feature-row indices, transformed matrices, preparer JSON and a manifest of hashes/selection support. They are separate from original data and deterministic feature bundles. New identities are required after any input/configuration/code/runtime change. The existing atomic immutable publication/reuse policy applies. Verify before loading:

```python
from scripts.training_preparation.contract import PreparationConfig
from scripts.training_preparation.development import resolve_root
from scripts.training_preparation.temporal import build_temporal, load_prepared_window
from scripts.training_preparation.preprocessing import transform_predictors

result = build_temporal(PreparationConfig(resolve_root()), verify_only=True)
X_train, y_train, train_index, state = load_prepared_window(
    result.bundle, "2024-06_t1", "native", "train"
)
X_validation, y_validation, validation_index, _ = load_prepared_window(
    result.bundle, "2024-06_t1", "native", "validation"
)
# Future inference: transform_predictors(new_raw_X_in_saved_order, state)
# Fit a future estimator only in a separately authorized modeling task.
```

Notebook 04 executes all modules in six code cells and displays bounded aggregate evidence. Its code-only identity excludes execution counts/outputs to avoid a circular artifact hash. `notebook_execution --execute` launches a new kernel using the repository interpreter over local IPC, keeps Jupyter/IPython writes in `tmp/`, saves outputs atomically, verifies displayed identities against regenerated current artifacts, and publishes an immutable receipt under `data/interim/training_preparation/notebook_execution/<receipt-identity>/`. The receipt binds saved notebook bytes, code identity, artifact manifest and runtime package versions. `--verify` requires that exact saved state and current artifacts; editing code, data, configuration or stale outputs causes failure. No individual case records or final-block outcome statistics are displayed.

This technically completes preparation; independent review and final DWP closure evidence are recorded in [the final validation report](milestone-3-validation.md). It does not approve G2/G3, historical operational availability or predictive performance. Future model adapters must explicitly choose the matching representation and honor the saved categories, versions and ordered schema.
