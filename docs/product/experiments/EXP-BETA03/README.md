# EXP-BETA03 — frozen-score false-alert policy

Implementation is separate from historical predictors and publications. This is
Phase 4 of [DESING.md](../EXP-BETA/DESING.md), explicitly authorized on
`experiment/EXP-BETA02`, existing PR #67, without merge. Human review remains
pending. The [protocol](protocol.json) was committed at `8fc0a8e` before policy
evaluation; SHA-256 `0b8b5f22ef678039147fd55dafd7938d70de6333c85afe631a31c3e8386ee386`.
See [DEC-139](../../traking-concluciones.md#dec-139-freeze-exp-beta03-before-policy-evaluation).

## Entry checklist

| Phase | Mandatory component | Entry state | Verified evidence / remaining work |
|---|---|---|---|
| 1 | Identified canonical table and Kedro reader | IMPLEMENTADO_Y_VALIDADO | Real 17,936-row/70-column table, pinned Stage 2 dependencies, original contract and manifest readable |
| 2 | G0/L1, climate pairing, R0 comparison | IMPLEMENTADO_Y_VALIDADO | 20,300 saved-model scores replayed, 120 metric strata reconciled; native publication unchanged |
| 2 | National expansion / transmission profiles | NO_EVALUABLE | Only Meta/Tolima supplied; no validated time-safe profile |
| 3 | Fixed NB2, H5 risk, count and T1 onset comparison | IMPLEMENTADO_Y_VALIDADO | 10,150 native forecasts replayed; 48 count and 84 onset strata; no new fits during recheck |
| 3 | NB2 T2 onset | NO_EVALUABLE | Marginals do not identify a joint transition |
| 3 | DeepAR/GRU | CONDICIONAL_NO_JUSTIFICADO | No identified sequence-remediable limitation with independent support; four reused years cannot justify model escalation |
| 4 | R0 native development/evaluation sources | IMPLEMENTADO_Y_VALIDADO | Original native roles and zero-fit score reload pass for all 96 parent cells; mandatory eight M00/XGBoost/onset cells available |
| 4 | Global constrained policy, paired evaluation and publication | PENDIENTE | Implemented four-node graph; real scientific acceptance required before completion |
| 4 | Department policy | PENDIENTE | Execute only after predeclared development support/heterogeneity check |
| 4 | Additional FP-aware learning | CONDICIONAL_NO_JUSTIFICADO | One original six-month selection block per frozen predictor; no independent recurrence plus untouched policy block |

## Scientific boundary

R0 is selected by reference priority and verified native development support,
not by observed evaluation performance. Native artifacts preserve the original
train/calibration/selection/evaluation roles. The same model and calibrator
produce both selection and evaluation scores; no crossing of fitted vintages,
new fits, new calibration, OOF construction, or evaluation mining.

The mandatory global policy reuses `exp_beta01.thresholds` unchanged: maximize
detected onsets under `floor(eligible_rows/12 * 1)`, preserve whole score ties,
prefer fewer false alerts, then higher threshold, including no-alert fallback.
R0's original policy used broader monitored exposure. Its original threshold and
alerts remain intact, while all paired Beta metrics use the same scored eligible
municipality-month denominator. Therefore this is an explicitly different cap,
not a new algorithm or a claim that R0 had violated its historical contract.

Only development scores determine whether to evaluate one department arm.
Both departments need at least 24 rows and three examples of each class; their
global-policy development false-alert rates must differ by at least 0.5 per
eligible municipality-year. These fixed exploratory support rules are not new
acceptance margins. Shrink local thresholds toward global using 24 pseudo-rows;
keep the stricter of that blend and the feasible local threshold. Missing support
returns global; a null threshold means no alerts. No municipal free thresholds.
No arm is selected by evaluation performance.

High-confidence false positives (score >=0.8) and municipal repetition are
reported from development only. A single six-month block per fitted predictor
cannot demonstrate independent recurrence while leaving a separate policy block.
Calibration was fitted on its own scores, and evaluation cannot supply mining
examples. The learning component is conditionally unexecuted, not a negative
result for all asymmetric learning or hard-negative methods.

Direct H5 onset labels remain distinct from excess at T2. Exact canonical
origin/target/truth and frozen R0 probabilities must match, without intersection
rescue. Evaluation is restricted to 2020/2021/2022 and consumed 2024 stress.
There is no 2025, prospective confirmation, statistical noninferiority or
automatic champion. G5 remains NOT_APPROVED; champion remains not_selected.

## Kedro and integrity

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run \
  --pipeline=exp_beta03 --params=profile=exp_beta03,tracking=disabled
```

Four nodes separate verification/preparation, development selection, application
and metrics/publication. The explicit reader requires the pinned native R0
manifest, full replay package integrity and zero-fit native score reproduction,
plus the existing identified canonical source. No latest lookup or source rebuild.
Strict catalog/profile bindings reject scientific overrides and tracking.
Only the new `exp_beta03` graph is registered; `replay` and `__default__` are
unchanged. The existing atomic no-overwrite publisher writes under
`tmp/kedro-migration/exp-beta03-runs/<bundle_id>/`.

Every publication records predictions, metrics, paired comparisons, development
policies/support, role/key hashes, unchanged reference thresholds, protocol,
source/code/runtime provenance and a content-addressed manifest. Code and
aggregate reports are versioned; private rows and native publications stay local.
Reproduction should use an in-memory sink and compare every payload byte; an
existing immutable destination must reject a second publication.
