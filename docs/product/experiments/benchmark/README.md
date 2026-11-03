# Academic benchmark: frozen SAT-Dengue models against surveillance rules

Status: **BENCHMARK_COMPLETED_WITH_LIMITATIONS** — executed and published locally;
retrospective descriptive comparisons only. G5 `NOT_APPROVED`; `champion: not_selected`.

## Authority and scope

The [approved academic contract](../contrato.md) is authoritative. Mauricio explicitly
clarified CHANNEL before metrics: **general dengue cases known at T strictly greater
than the H5 P75 of the target calendar month**, including P75=0. The original advance
report is not required and its absence is not a blocker. The source contract was an
existing untracked file on `contrato_del_proyecto`; it was preserved byte-for-byte.
Starting HEAD: `9ea3b8b` (merged EXP-BETA01 V2). No branch creation or merge.

The [frozen protocol](protocol.json), SHA-256
`6eb69f14ab19c04d844fe0aaac1c298c6f77c8f718ce965329632b2510453e05`, was written and pinned
before benchmark metrics. No models were fitted, invoked for inference, calibrated,
or assigned newly selected thresholds. No scientific historical files were edited.

## Comparator reconstruction

- **CHANNEL:** `count(T) > P75_H5(T+h)`. The threshold uses five values from the same
  calendar month in the five years preceding the target year, type-7 percentiles;
  every history month must be no later than T. Equality means no alert. P75=0 with
  positive count(T) emits an alert. The recomputed threshold matches the identified
  canonical `p75_h5_t1`/`p75_h5_t2` for every included row.
- **PERSISTENCE:** existing `persistence_reference` projects `zona_canal_t == EXCESO`
  to either horizon. Since the common cohort requires non-excess at T, it emits zero
  alerts. Its FAR and precision are undefined. Beating it on this restricted cohort
  is a structural consequence of detecting any onset, not an independent strong baseline.
- **R0 / G0_OFF / G0_ON / G1_OFF:** consume original saved probabilities and alerts.
  Saved thresholds are checked against saved scores without searching or selecting.
  G0_OFF/R0 copies in V2 must agree exactly with V1 and the native M00 R0 publication.

Historical V1 inspection found a material distinction: `src/models/baseline.py`
uses `zona_objetivo == 2`; `src/features/build_features.py` assigns that zone at
count(T) >= P75 when P75>0, but not when P75=0. Its `src/evaluation/metrics.py`
names FP/(FP+TN) `tasa_falsas_alarmas`. This is **FPR**, not contractual FAR.
Those files were read in the sibling `proyecto-desarrollo-de-soluciones/microproyecto`
repository at HEAD `b63257c17f3064a0dcda6fcf4e7028fae4a43078`; their hashes are in
[protocol.json](protocol.json). They were not copied or changed. This benchmark
implements the explicit academic clarification with current H5; it does not claim
byte-identical reconstruction of that old V1 rule or reproduce its evaluation population.

## Common observations and metric definitions

All six arms retain exactly the BETA evaluation keys, labels, outcome months and
original embargo: **2,653 rows / 313 onsets at T+1; 2,422 / 219 at T+2**, Meta and
Tolima, target years 2020/2021/2022/2024. No intersections, removed observations or
missing comparator inputs. Each horizon's ordered keys and labels have hashes in
private `preflight.json`. T+1/T+2 are different cohorts; do not pool their sensitivities.

Onset is `Y(T+h-1)=0 AND Y(T+h)=1`, with Y defined by H5 and strict exceedance.
Future states are consulted only to verify outcomes, never to construct alerts.
A T+2 alert for an ongoing episode can be correct for excess and false for onset.

- Sensitivity: detected onsets / real onsets; missed = real minus detected.
- **FAR_excess:** alert with target non-excess / all emitted alerts.
- **FPR_excess:** alert with target non-excess / all target non-excess observations.
- Onset false alerts, onset precision and onset FPR are separate columns.
- Eligible municipality-year exposure = observed eligible rows / 12; onset false
  alert load uses this denominator, not all 76 municipalities times elapsed years.
- AP and Brier retain the original onset probabilities. Deterministic comparators
  have no probabilities; these columns are blank. AUROC is not added because AP and
  Brier already cover the requested secondary evaluation without introducing a ranking.
- CSV blanks mean undefined/not applicable, never zero. Year `all` and department
  `all` designate pooled strata; departments 50/73 are Meta/Tolima.

A model meets descriptively only when it detects **strictly more** onsets than each
comparator and its FAR exceeds CHANNEL's by at most **0.05 absolute**. The inclusive
boundary is evaluated using integer count cross-products. All conditions are per
horizon on pooled observations; annual and department results expose instability.
BETA's <=1 onset FA/eligible municipality-year and >=-2 pp sensitivity versus R0
remain separate complementary controls. None selects a champion.

## Reproduction and local publication

Implementation: [academic_benchmark.py](../../../../src/sat_dengue/experiments/academic_benchmark.py).
Use the existing environment with modeling dependencies; this route only reads
predictions and computes metrics. No new Kedro graph or tracking writes.

```bash
.venv/bin/python -m sat_dengue.experiments.academic_benchmark --preflight
.venv/bin/python -m sat_dengue.experiments.academic_benchmark --verify 6cfc7bcf565ebdf7ff11ab3ff79d6d91ce7d2f392958c76aa55d310ba27b6c48
```

The original execution used `--publish`. Do not repeat it as a replay command:
publication refuses replacement. `--verify` recomputes and compares every byte
against the explicit existing identity without writing data or running models.

Detailed private publication:
`data/processed/benchmark/6cfc7bcf565ebdf7ff11ab3ff79d6d91ce7d2f392958c76aa55d310ba27b6c48/`

Manifest SHA-256: `4ca5b8359c914fc080c80ebf538d7d11bf1c76aa783d9434c1832d478ff15f2f`.
Seven payload/manifest files contain 30,450 row-arm records, metrics, comparisons,
protocol, preflight and provenance. The row records preserve origin/target keys,
H5 onset and target excess, original probability/alert, threshold, model/policy/source
identities and both confusion classifications. They are ignored by Git and never
exported to `docs/`. The bundle preserves no duplicate full canonical dataset.

Public [metrics](METRICS_BY_STRATUM.csv) and [comparisons](PAIRED_COMPARISONS.csv) are
byte-identical copies of the private aggregate CSVs. There are 180 metric rows and
360 comparison rows: horizons x arms x pooled/annual x pooled/department. R0 self
comparisons are retained explicitly as zero reference checks, not independent evidence.
See [results](RESULTS.md) and [conclusions](CONCLUSIONS.md).

## Validation evidence

- PASS: 420 pinned source files, including native R0 replay payloads and the G0/G1
  bundles, verified before/after calculation and publication. H5 count/state/history,
  complete cohorts, copied predictions and frozen policy application verified.
- PASS: second execution via `--verify` reproduced all publication bytes.
- PASS: independent arithmetic from the 30,450 saved records reconciled all 180
  strata and 360 comparisons, including TP/FP/FN, FAR/FPR denominators, AP, Brier
  and the three academic conditions. No original scientific results were rewritten.
- PASS: nine focused engineering tests in
  [test_academic_benchmark.py](../../../../tests/unit/test_academic_benchmark.py):
  strict ties/P75=0, unavailable denominators, continuation-vs-onset errors,
  future-outcome mutation, missing history, altered labels/cohorts, strict boolean
  parsing, exact five-pp boundary, stratified count reconciliation and immutable
  publication/tamper rejection.
- PASS: 114 matching model strata agree with the published historical metric tables;
  V1's metric file has annual strata only, while V2 also stores pooled strata.
- PASS: scoped Ruff, format, mypy, Markdown links, diff/whitespace checks, public CSV
  privacy boundary and changed-file secret scan. Full CI suites and historical
  training tests were not rerun for this task.
- PASS: repository-only conformance (17 checks). The separate initial all-plan gate
  retains two inherited failures (PLAN_012 review evidence and legacy Stage 2 mixed
  lifecycle), not failures introduced by this benchmark.

The local publication is reproducibility evidence, not remote CI approval or
independent scientific review. Personal review and any later Git publication/merge
remain separate from the computed academic dispositions.
