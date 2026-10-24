# ML and Scientific Standards

## Methodology

CRISP-ML(Q) governs business/data understanding, data preparation, modeling, evaluation, deployment and monitoring. The [master plan](../roadmap/master-plan.md) maps those responsibilities to project stages and acceptance gates. Product direction is owned by the [product definition](../product/product-definition.md); do not maintain a second stage checklist here.

## Validation and Leakage Control

- Strict temporal validation is mandatory; training-only metrics cannot select the model.
- Keep X separate from future Y and target/evaluability controls. Fit learned transformations on each training window only; reuse their saved state for validation/inference.
- Respect origin, target and fit dates separately. Keep the configured final target block out of tuning and exploratory model comparison.
- Apply one comparison protocol across candidates. Evaluate calibration, false alarms and outbreak onsets as well as discrimination under the approved evaluation decisions.
- Retrospective consolidated data do not establish historical operational availability. Temporal ordering is necessary but does not prove real-time performance.

## Reproducibility and Traceability

- Bind data, configuration, transforming code and runtime identities to artifacts and experiment evidence.
- Current deterministic/temporal preparation is documented in [the implemented workflow](../product/stage-3/README.md). Scientific definitions remain in the [decision register](../product/traking-concluciones.md) and owning contracts.
- A passing test, completed DWP or successful notebook execution is not a human scientific gate approval.
- MLflow is optional, explicitly enabled local metadata tracking under the existing allowlist. It is not a prerequisite for preparation or tracking-disabled replay; native scientific artifacts remain authoritative.

## Notebook and Module Policy

- The maintained implementation lives under `src/sat_dengue`. Reusable scientific logic belongs in the tested package; Kedro is the active orchestrator and dataset adapters own verified I/O.
- Official execution uses registered Kedro pipelines, including `kedro run --pipeline=replay`. The [migration owner](../operations/kedro-migration.md#current-cleanup-and-execution--session-8) and [testing guide](../TESTING_GUIDE.md) own runtime, input and validation requirements.
- Notebooks 03–08 are retained exclusively as frozen historical identity evidence where required by provenance readers. They are not production entrypoints and do not orchestrate current preparation, fitting, calibration or evaluation. Do not execute or rewrite their cells; the original code-only restriction for notebooks 03/04 remains.
- Retained scripts are explicit tools or compatibility adapters with a current consumer, owner and verifiable retirement condition in the [disposition registry](../operations/repository-disposition.json). They do not create a second scientific implementation or a notebook execution route.
- Reuse the same preparation implementation for model fitting and inference across pipelines instead of duplicating logic. Validate saved outputs against current code/data identities.
