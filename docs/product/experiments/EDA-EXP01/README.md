# EDA-EXP01 — exploratory analysis of experimental results

**Status: `COMPLETED_WITH_LIMITATIONS`.** The six-chapter
[notebook](../../../../notebooks/eda_experimental_results.ipynb) executed on real
private artifacts. [Findings](FINDINGS.md) quantify the evidence;
[conclusions](CONCLUSIONS.md) prioritize the remaining research question.
This is exploratory reuse of consumed observations, not a predictive experiment
or independent validation. G5 `NOT_APPROVED`; `champion: not_selected`.

## Scope and authority

The human EDA-EXP01 request authorizes read-only analysis of published results,
an independent `analysis/EDA-EXP01` branch from `main`, and a PR without merge.
Starting `main`: `ca22bc7`; EXP-DELTA01 PR #73 was already merged when checked.
The [academic contract](../contrato.md) controls events and denominators.
No inference, fitting, recalibration, threshold optimization, H5 change, new
Kedro pipeline or dashboard occurs. Historical sources remain untouched.

Acceptance is a fully executed six-chapter notebook, exact cohort/metric
reconciliation, deterministic derived publication, at most eight useful figures,
source preservation and conclusions with explicit uncertainty. The bounded
request is implemented directly; no DWP plan or stage approval is inferred.

## Identified inputs

Every path below is repository-relative private storage, not a GitHub download.
The notebook selects explicit identities, never the newest directory.

| Source | Publication identity | Manifest SHA-256 |
| --- | --- | --- |
| Academic benchmark, `data/processed/benchmark/` | `6cfc7bcf565ebdf7ff11ab3ff79d6d91ce7d2f392958c76aa55d310ba27b6c48` | `4ca5b8359c914fc080c80ebf538d7d11bf1c76aa783d9434c1832d478ff15f2f` |
| Benchmark diagnosis, `data/processed/benchmark/diagnostico/` | `874ef99634db44e0e71a3aba9b7195f8762ff5f9327ef0394d27ce77fc8e116c` | Pinned by the diagnosis identity; payload and canonical manifest identity checked |
| DELTA results, `data/processed/exp_delta01/` | `d5c482b64e0d44e5012b20d24baa73d14f829ca4857bb2e2e53870ab3a82a284` | `a6f67b769cc52365da097ffa1b2709452252f0b7e9a5e6a6644c70a7f1cb0a92` |
| DELTA selection freeze, `data/processed/exp_delta01/selection_freezes/` | `e99f60fed004de212b4310d1114ad60e51b097a48ea7e251d2fbc41b8935d2b0` | `592a166956fdf536ea247eae6d99f3d01e6674ea8b030f2ef91ab34e7b6ddbad` |
| Recovered scores, `data/processed/exp_delta01/recovered_selection/` | `b2e8256c9c37f8ecdb5f895ccd6d936cfb11f3896adc654ecab3c386bf57acc1` | Pinned by DELTA provenance; canonical identity and payloads checked |
| Regional canonical table, `data/processed/canonical_model_table_v1/` | `ddf4d3be23f7ce2cd874bbdc73fdf0f7b9ae5e6f7055b2761ec23bd31fc15c98` | `037445487086f7123ee2bf4b97b9af06b96716e2f24e9ff5160177c59da261d8` |

The benchmark contains frozen G0_OFF, G0_ON, G1_OFF and R0 probabilities and
decisions plus CHANNEL/PERSISTENCE. All 506 recorded inputs, including parent
artifact records and documentary context, are hashed before/after analysis.
The canonical table supplies only the prior epidemiological state; no labels,
predictors or cohort are reconstructed. Missing/changed required inputs fail closed.

[Analyses 1](../analisis-1.md), [2](../analisis-2.md), [3](../analisis-3.md),
[4](../analisis-4.md), [5](../analisis-5.md), [6](../analisis-6.md) and
[7](../analisis-7.md), and EXP02/EXP03/EXP03.1/EXP04/BETA conclusions supply
historical interpretation only. Their distinct protocol populations are never
pooled with benchmark metrics. EXP02's label-sensitivity counts are attributed
to its published conclusions, not newly adjudicated here.

## Reproduce

Use the existing project `.venv` with modeling/notebook extras and Matplotlib.
Execution needs the exact private publications and their recorded parent files;
a data-free checkout cannot reproduce the real-data results. Run from the root:

```bash
JUPYTER_RUNTIME_DIR="$PWD/tmp/eda-exp01/jupyter" IPYTHONDIR="$PWD/tmp/eda-exp01/ipython" .venv/bin/python -m jupyter nbconvert --execute --to notebook --inplace notebooks/eda_experimental_results.ipynb --ExecutePreprocessor.timeout=600
.venv/bin/python -m ruff check notebooks/eda_experimental_results.ipynb
.venv/bin/python -m ruff format --check notebooks/eda_experimental_results.ipynb
.venv/bin/python scripts/check_markdown_links.py
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
```

Execution preserves aggregate outputs in the notebook, writes eight figure
previews under ignored `tmp/eda-exp01/figures/`, and atomically publishes 21 derived
tables plus settings/manifest under ignored `data/processed/eda_exp01/`.
It does not duplicate historical predictions. Only aggregate notebook outputs
and narrative documents enter Git; municipality-origin keys, individual scores
and named municipal tables do not.

Final derived identity:
`3d0803788eab1bbc92f29410540b184ff11b07ab921b611b5fd5965ed05e356e`.
Manifest SHA-256:
`6c3ff1a8a2c5a97b7306a28b30f0f8f305dbdbb87209025be8b16150dbbc8002`.
Its manifest binds every input, notebook source cells and numerical package
versions. A changed environment/source creates a new identity; reuse requires
identical bytes and cannot overwrite prior results.

## Methods and limits

- Exact municipality-origin pairing; horizons remain separate. All 180 benchmark
  and 60 DELTA metric strata reconcile, including AP/Brier and unavailable P1.
- Counts, exposure, contingency tables, annual score histograms, real-class
  quantiles/ECDFs, saved-threshold margins, AP/AUROC/Brier and supported reliability
  bins. Score distributions and ranking interpretations remain within annual
  model/horizon cells. Pooled AP is recomputed only for published-metric parity;
  it is not interpreted as ranking by a single fixed predictor.
- Excess-FAR decomposition uses excess prevalence/sensitivity/FPR. Common-prevalence
  standardization uses the horizon's pooled prevalence. Three-factor Shapley
  contributions average all six substitution orders and sum to the observed gap.
  These are accounting descriptions, not causal effects or candidate policies.
- Reliability bins are fixed at width 0.1 and shown only with ≥30 rows and ≥5 of
  each outcome. Other bins remain in the private table. No calibrator is fitted.
- Municipal 95% Wilson intervals expose sparse denominators. Their independent
  Bernoulli assumption is not established for repeated months, so they are reference
  intervals, not calibrated uncertainty for temporal transport or superiority.
  Jeffreys intervals, cluster bootstrap and count regressions add no necessary
  evidence to the supported descriptive question; none is run automatically.
- Four reused years, changing eligibility, annual model identities and shared
  temporal shocks prevent causal attribution or independent confirmation.
  Transmission-profile analysis is **blocked**: the admitted contract contains no
  temporally validated classification. Departments are geographic controls only.

## Validation evidence

PASS: fresh-kernel top-to-bottom execution; exact six-arm pairing on 5,075 keys;
P0 equality and P0/P1 score/label identity; 180/60-stratum reconciliation;
diagnostic overlap/boundary reconciliation; source hashes unchanged; notebook
format and scoped Ruff checks. Eight figure PNGs were visually inspected, with
legends moved out of plotted data where needed, and all eight are embedded in the
saved notebook. A second fresh-kernel run reproduced every derived payload and
manifest byte. Markdown links, the two focused directory/historical-boundary
contract checks and repo-only conformance pass. The disposition inventory also
registers four inherited benchmark/DELTA directories whose absence failed the
first directory check; their contents and historical identity mappings are unchanged.
No extensive test infrastructure was added.

A separate arithmetic check uses CSV counts and the subset-weighted Shapley
formula to verify both G0_OFF decompositions, and the Mann–Whitney rank identity
to verify all 32 annual model AUROCs. Principal support/boundary claims reconcile.
Receipts remain in ignored `tmp/eda-exp01/`; these checks are arithmetic validation,
not independent scientific confirmation or an independent reviewer decision.

The HTML preview rendered successfully under `tmp/eda-exp01/`; full notebook-page
visual inspection is `UNVERIFIED` because the browser host was unavailable.
Figures were inspected directly as PNGs; this does not claim a browser layout check.
Remote CI and independent review remain separate PR integration evidence.

Repository-only, scoped-plan and all-plan DWP states are distinct: repo-only is
checked for this change; scoped-plan is not applicable; the initial all-plan gate
retains inherited PLAN_012 unresolved-review and legacy Stage 2 lifecycle findings.
Those historical findings neither pass silently nor become EDA code failures.
