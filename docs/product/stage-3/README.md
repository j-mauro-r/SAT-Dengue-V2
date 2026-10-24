# Training preparation — Kedro execution and preserved scientific baseline

G2 and G3 are **APPROVED with documented limits** by Mauricio on 2026-10-21
([DEC-135](../traking-concluciones.md#dec-135)). Historical operational availability
remains unproven; retrospective preparation does not establish prospective model
performance. G5 remains `NOT_APPROVED`, champion `not_selected`, and 2025 cannot
train, fit preparers, tune or select.

## Current execution

The [preparation contract](training_preparation_contract_v1.json) is unchanged and
owns scientific roles, categories, features, windows and representation settings.
The [field dictionary](../stage-2/DATA-01-Priority%20Field%20Matrix.md) retains source
semantics. Domain calculations live in
[`src/sat_dengue/training_preparation`](../../../src/sat_dengue/training_preparation/__init__.py);
[the seven-node graph](../../../src/sat_dengue/pipelines/preparation/pipeline.py)
separates resolved configuration, cutoffs, deterministic features, eligibility,
partitions, saved-state replay and publication. Dataset adapters own filesystem I/O.

From the repository root, use the isolated migration environment:

```bash
export PATH="$PWD/tmp/kedro-migration/foundation/bin:$PATH"
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=preparation --params=profile=preparation
```

Catalog inputs `configuration_inputs`, `parameters`, `preparation_sources` and
`saved_preparers` identify the authoritative configuration, verified Stage 2
manifest/products, and the exact native preparers. No `latest` selection, notebook
execution, consolidation or model training is required. The catalog pins Stage 2
manifest SHA-256 `241aa320e2df20d1d4613c50c61d32b60f161a10d76931721131c93a544a213a`.
Original development identity is
`2ab12a21172a1cc49ff4fe713c1ff5199f1c7569354c300ed7cb2579ff0ffe24`;
original temporal identity is
`a41c1252e81090eec60db2b0bc0089aeee5c96bc645ea9766225eb45e7bc1d97`.
Changed native manifest bytes, membership or payloads fail closed.

Every run publishes its verified resolved configuration first, then a new isolated
engineering bundle under `tmp/kedro-migration/preparation-runs/<bundle-id>/`.
Atomic immutable publication refuses replacement. Outputs include `features.csv`,
`keys.csv`, `controls.csv`, separate train/validation raw X, Y, indices and controls
for each window, saved JSON states, transformed matrices, `schema.json`,
`provenance.json` and a hash manifest. Historical native bundles and their manifests
are preserved; source movement creates engineering identities, never repaired hashes.

## Preserved preparation behavior

The complete development cohort has 16,948 rows and 76 municipalities through
2024-12. Earlier history is retained before eligibility is evaluated. Features
contain two current counts, nine climate aggregates, current `zona_canal_t` and
16 deterministic candidates: `dengue_lag_1/2/3`, `grave_lag_1/2`,
`dengue_cambio_1m`, `dengue_media_3m`, `zona_canal_lag_1`, `lluvia_lag_1/2`,
`temperatura_lag_1/2`, `rocio_lag_1`, `escorrentia_lag_1`, `mes_sin`, `mes_cos`.
Calendar-keyed lookups, T/T−1/T−2 complete means, January-phased cycles, negative
changes, climate signs and missingness are unchanged. No imputation or feature
selection is introduced.

The deterministic table has 28 ordered columns. Raw X has 29, introducing only the
approved municipality category. Y, target metadata, temporal keys and controls
remain separate. Eligibility preserves 11,856 examples per horizon. Targets entering
2025 are masked in development controls, with their target dates and exclusion flags
retained. Reserved reference rows produce no development features or outcome summaries.

| Fit cutoff | Horizon | Train | Validation | Validation targets | Validation origins |
| --- | --- | ---: | ---: | --- | --- |
| 2018-12 | T+1 | 6,384 | 456 | 2019-01–2019-06 | 2018-12–2019-05 |
| 2018-12 | T+2 | 6,384 | 380 | 2019-02–2019-06 | 2018-12–2019-04 |
| 2020-12 | T+1 | 8,208 | 456 | 2021-01–2021-06 | 2020-12–2021-05 |
| 2020-12 | T+2 | 8,208 | 380 | 2021-02–2021-06 | 2020-12–2021-04 |
| 2022-12 | T+1 | 10,032 | 456 | 2023-01–2023-06 | 2022-12–2023-05 |
| 2022-12 | T+2 | 10,032 | 380 | 2023-02–2023-06 | 2022-12–2023-04 |
| 2024-06 | T+1 | 11,400 | 456 | 2024-07–2024-12 | 2024-06–2024-11 |
| 2024-06 | T+2 | 11,400 | 380 | 2024-08–2024-12 | 2024-06–2024-10 |

Training labels must be observable at the producer cutoff. Validation is sequential
at each origin, bounded by an explicit consumer cutoff and the six-month target
interval. T+2 has five effective months because its first configured target would
require an origin before the fit cutoff. There is no new test partition; the
reserved 2025 block remains excluded. Unknown windows, future labels/origins,
role/order/alignment changes and incompatible saved schemas are rejected.

Real execution replays all 16 saved preparers without fitting. `native` preserves
29 columns and saved pandas categories; `onehot_standard` preserves 114 columns and
training means/population standard deviations. Fixed zones are EXITO, SEGURIDAD,
ALERTA and EXCESO; missing and unknown tokens remain distinct. Saved municipality
vocabularies, category order, runtime versions, training-X hashes and output order
are checked. Synthetic tests alone exercise new train-only fits and validation
perturbation. No real preparer is refitted.

## Migration evidence and compatibility

The [migration record](../../operations/kedro-migration.md#stage-3-execution--session-4)
and [testing map](../../TESTING_GUIDE.md#kedro-stage-3-preparation-migration-session-4)
own current execution evidence and validation commands. The private gate compares
all 99 original development/temporal payloads byte for byte, complete cohorts,
categories, dtypes and matrices, with fitting denied at call level.

The eleven script facades are replaced by direct imports from their package owners.
The single legacy I/O boundary loads verified native temporal evidence without
rebuilding or fitting; scientific calculations stay in the pure preparation package.
The [original mapping](../../operations/kedro-preparation-identities.json) stays
closed; the [separate cleanup correspondence](../../operations/kedro-cleanup-identities.json)
checks original/pre-cleanup bytes and final absence. Use `kedro run --pipeline=replay`
for the composed workflow; old notebook/CLI commands are historical only.

Notebook [04](../../../notebooks/04_training_preparation_pipeline.ipynb) and
[milestone 1](milestone-1-validation.md), [milestone 2](milestone-2-validation.md),
[milestone 3](milestone-3-validation.md) remain unchanged historical evidence.
Notebook 04 is retained only as frozen source identity evidence, never as a production entrypoint.
Their earlier G2/G3 wording and bundle identities describe their dated execution;
DEC-135 owns present approval. Migration parity does not establish full historical
reproducibility or resolve the 13 closed source exceptions and 17 KEEP / UNVERIFIED
bundles. Current training, evaluation and optional tracking are documented in the migration owner; no new scientific adjustment is authorized.
