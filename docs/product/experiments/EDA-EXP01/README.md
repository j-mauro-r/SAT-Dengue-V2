# EDA-EXP01 — exploratory analysis of experimental results

**Scientifically closed:** main analysis `COMPLETED_WITH_LIMITATIONS`;
Chapter 7 climate extension `INSUFFICIENT_EVIDENCE`.
The seven-chapter [notebook](../../../../notebooks/eda_experimental_results.ipynb)
was executed on identified private artifacts. [Findings](FINDINGS.md) preserve
F1–F8 and C7.1–C7.5; the final
[scientific closure](CONCLUSIONS.md#scientific-closure--eda-exp01) consolidates
conclusions, lessons and hypothesis dispositions. Scientific closure does not
approve PR integration, model adoption or a new experiment.
G5 `NOT_APPROVED`; `champion: not_selected`.

The original question was whether the principal observed limitations concern
predictive separation, temporal calibration, alert policy or epidemiological
differences between municipalities. Chapter 7 separately asked whether existing
climate variables and predefined lags distinguish true detections from false
alerts, particularly near P75. Both questions are concluded within their stated
exploratory limits; the evidence does not identify a unique causal bottleneck.

## Chapter index

Chapters 1–6 are the preserved original analysis: integrity/comparability;
false-alert distribution; probability separability; temporal calibration;
territorial heterogeneity; epidemiological boundary and synthesis.
Chapter 7 appends four climate analyses: availability/distributions;
climate by frozen alert outcome; predefined calendar lags; near-P75 comparisons.
Its findings and conclusions are independent appendices in the existing documents.

## Scope and authority

The human EDA-EXP01 request authorizes read-only analysis of published results,
an independent `analysis/EDA-EXP01` branch from `main`, and a PR without merge.
Starting `main`: `ca22bc7`; EXP-DELTA01 PR #73 was already merged when checked.
The [academic contract](../contrato.md) controls events and denominators.
No inference, fitting, recalibration, threshold optimization, H5 change, new
Kedro pipeline or dashboard occurs. Historical sources remain untouched.

The original six-chapter acceptance covered exact cohort/metric reconciliation,
deterministic publication and eight figures. The separately authorized Chapter 7
added four climate analyses and four figures while preserving all 35 original
complete cells, original findings/conclusions and the original publication.
The final notebook contains seven chapters and 12 figures. This closure is a
documentation-only consolidation of that completed work; no DWP plan or stage
approval is inferred.

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
In Chapters 1–6 the canonical table supplies only the prior epidemiological state;
Chapter 7 also reads its existing climate aggregates and coverage metadata. No
labels, predictors or cohort are reconstructed. Missing/changed required inputs
fail closed.

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
# Execute the current extended notebook using the preservation wrapper below.
.venv/bin/python -m ruff check notebooks/eda_experimental_results.ipynb
.venv/bin/python -m ruff format --check notebooks/eda_experimental_results.ipynb
.venv/bin/python scripts/check_markdown_links.py
bash .agents/skills/deepworkplan/verify/conformance.sh --repo-only
```

The original Chapters 1–6 replay preserves aggregate outputs in the notebook,
writes eight figure previews under ignored `tmp/eda-exp01/figures/`, and reuses
21 derived tables plus settings/manifest under ignored `data/processed/eda_exp01/`.
Chapter 7 publishes its 12 new tables separately, as described below.
It does not duplicate historical predictions. Only aggregate notebook outputs
and narrative documents enter Git; municipality-origin keys, individual scores
and named municipal tables do not.

Original Chapters 1–6 publication identity:
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

## Chapter 7 sources and preservation replay

Chapter 7 reuses the identified regional canonical publication above for all nine
monthly climate variables and their valid-day metadata. The original EDA publication
is an immutable dependency, not a replacement target. Benchmark, diagnosis and
DELTA sources are unchanged. The only documentary climate antecedent is
[EXP03](../EXP03_feature_ablation/CONCLUSIONS.md). No external data are downloaded.

Original notebook identity before this extension:
SHA-256 `77d7d5b765150dbc3fc929ddc992a6f7848d7fd801f13406bfa1f9a8a619ec62`,
first **35 complete cells**, source revision
`80b1561b279c3ce7523ed6bc06aad5cedc146933`.
The original publication identity and manifest SHA-256 above remain unchanged.

The first publisher hashes the complete notebook file on disk. Appending cells
and running plain `nbconvert --execute` would therefore change that original
source identity. The preservation wrapper below executes all cells in a fresh
kernel while temporarily materializing the pinned original file for Chapters 1–6.
It restores the extended source at Chapter 7, verifies equal original sources,
outputs and execution counts, then preserves even original cell timing metadata.
A guarded execution path restores the extension if execution fails. Run with no
concurrent notebook editor or second writer. The pinned Git revision must exist
locally; a shallow checkout without it needs that history supplied before replay.

```bash
JUPYTER_RUNTIME_DIR="$PWD/tmp/eda-exp01/jupyter" IPYTHONDIR="$PWD/tmp/eda-exp01/ipython" .venv/bin/python - <<'PY'
from pathlib import Path
import hashlib
import json
import subprocess
import nbformat
from nbclient import NotebookClient

root = Path.cwd()
path = root / "notebooks/eda_experimental_results.ipynb"
revision = "80b1561b279c3ce7523ed6bc06aad5cedc146933"
original_bytes = subprocess.check_output([
    "git", "show", f"{revision}:notebooks/eda_experimental_results.ipynb"
])
assert hashlib.sha256(original_bytes).hexdigest() == (
    "77d7d5b765150dbc3fc929ddc992a6f7848d7fd801f13406bfa1f9a8a619ec62"
)
original = nbformat.reads(original_bytes.decode(), as_version=4)
extended_bytes = path.read_bytes()
extended = nbformat.reads(extended_bytes.decode(), as_version=4)
assert extended.cells[:35] == original.cells
bundle = root / (
    "data/processed/eda_exp01/"
    "3d0803788eab1bbc92f29410540b184ff11b07ab921b611b5fd5965ed05e356e"
)
before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir()}
assert before["manifest.json"] == (
    "6c3ff1a8a2c5a97b7306a28b30f0f8f305dbdbb87209025be8b16150dbbc8002"
)

def restore_extension(cell, cell_index, **kwargs):
    if cell_index == 35:
        path.write_bytes(extended_bytes)

path.write_bytes(original_bytes)
try:
    NotebookClient(
        extended, timeout=600, kernel_name="python3",
        resources={"metadata": {"path": str(root)}},
        on_cell_start=restore_extension,
    ).execute()
    for i in range(35):
        assert extended.cells[i].source == original.cells[i].source
        assert extended.cells[i].get("outputs", []) == original.cells[i].get("outputs", [])
        assert extended.cells[i].get("execution_count") == original.cells[i].get("execution_count")
    assert before == {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir()
    }
    extended.cells[:35] = original.cells
    nbformat.validate(extended)
    nbformat.write(extended, path)
except BaseException:
    path.write_bytes(extended_bytes)
    raise
print("PASS: full execution; 35 original cells and 23 original files unchanged")
print("Chapter 7 publication:", extended.cells[-1].outputs[0].text)
PY
```

The extension publishes only 12 new aggregate climate tables plus settings and
manifest, under a distinct identity in `data/processed/eda_exp01/`. No original
dataset, prediction file or Chapters 1–6 table is copied into it. Four new figures
are embedded in the notebook and previewed under ignored
`tmp/eda-exp01/chapter7/figures/`; all eight original embedded figures are unchanged.
Every joined climate month is at or before its origin; lags use exact calendar
keys, not positional shifts. Missing values are never imputed.

Chapter 7 publication:
`75a1b9e36a4d1792f3dbec72e0ac9013f0918f5115c66deb19832e26c977d2ce`.
Manifest SHA-256:
`5b15e3ef3904383e2774606ac56b8472f6d45b51eb0d6cf16503520b9bd86e20`.
Its source record binds the original publication, canonical climate data/metadata,
academic/diagnostic/DELTA identities, contract, EXP03 antecedent and Chapter 7 cells.
NumPy/pandas/SciPy and the original numerical environment are recorded.

Validation: full fresh-kernel preservation replay, all 35 original complete cells
and 23 original publication files unchanged; 192 raw and 192 season-centered rank
calculations independently reconciled; all 1,008 weighted quantiles checked using
integer replication, separate from the notebook's exact rational CDF calculation;
calendar-gap refusal checked without imputation. The four new PNG figures were
inspected directly. Repeated execution reuses identical derived bytes and cannot
overwrite the original. Receipts remain under ignored `tmp/eda-exp01/chapter7/`.
Full browser page inspection remains unverified; the available browser host was
unavailable in the original delivery. No current browser layout check is claimed.

To inspect the current saved presentation without execution:

```bash
.venv/bin/python -m jupyter nbconvert --to html --output-dir tmp/eda-exp01/chapter7 notebooks/eda_experimental_results.ipynb
```

## Scientific closure and PR integration

The documentation closure on 3 November 2026 reads saved notebook outputs,
published tables and quantitative owners only. It does not execute the notebook,
Kedro, model training or test suites, and changes no scientific evidence. Both
publication identities above remain authoritative; the findings record is intact.
Reproduction commands are retained for an explicitly authorized preservation
replay, not as standing instructions to refresh already consumed results.

[PR #74](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/74) remains the independent
integration vehicle on `analysis/EDA-EXP01`; no merge or integration approval is
part of scientific closure. The closure audit inspected analyzed head `a48ac6d`:
Repository Quality, Python Quality, base-wheel validation and CodeQL passed;
Unit Tests were still running. The preceding head's
[CI run](https://github.com/j-mauro-r/SAT-Dengue-V2/actions/runs/41672426715)
reported 831 passing tests and one existing architecture-test failure,
`test_data_domain_has_no_filesystem_or_framework_dependencies`, concerning a
disallowed `pathlib` import. That source/test is unchanged by this closure and
no unrelated repair is authorized here.

No independent review or approval was recorded on the PR when inspected.
Full CI approval and the independent review remain outstanding integration
evidence; consult the [live PR checks](https://github.com/j-mauro-r/SAT-Dengue-V2/pull/74/checks)
for subsequent results, including the documentation closure commit. These states
do not reopen the completed exploratory analysis or waive its limitations.
