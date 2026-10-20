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
- MLflow is a planned experiment-tracking option, not an installed prerequisite for preparation or the first baseline. Establish the run record needed by the modeling task before adding infrastructure.

## Notebook and Module Policy

- Notebooks configure, execute and expose bounded review outputs. Maintained transformation logic belongs in reusable, tested Python modules.
- The current implementation uses `scripts/training_preparation/`; no `src/` migration is required just to satisfy a directory convention. Package runtime components when their deployment needs justify it.
- Notebooks 03/04 remain code-only under the current human instruction. Do not add Markdown cells until requested.
- Reuse preparation for model fitting and inference instead of copying it into a new training notebook. Validate saved outputs against current code/data identities.
