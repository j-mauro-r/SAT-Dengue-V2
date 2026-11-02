# EXP-BETA02 — probabilistic monthly dengue counts

Status: **COMPLETED_WITH_LIMITATIONS**, locally executed on 2026-11-02. See
[RESULTS.md](RESULTS.md) for the fixed negative/mixed findings, exact publication,
32 real fits including reproduction, native-state checks and remaining limits.
This is the separately authorized Phase 3 of [the Beta design](../EXP-BETA/DESING.md).

## Entry gate and frozen scope

The compatibility repair is integrated in main `68d166a`. Its Git tree is exactly
`1102da7d996fda6f905a97e6f8899e1010bdc875`, the tree approved by all PR #66 checks
and [768 passing public tests](https://github.com/j-mauro-r/SAT-Dengue-V2/actions/runs/41441049931).
The new merge-commit CI was still running at entry; the passed evidence is for
the identical tree, not falsely attributed to that pending run.

**Gate: READY_WITH_LIMITATIONS.** Actual read-only acceptance loaded the pinned
canonical table (17,936 rows, 70 columns, 76 municipalities), Stage 2 dependencies
and 5,075 frozen R0 rows. Original identities and permissions of 437 inventoried
files remain unchanged. Count preflight checked 16,221 eligible future counts,
64,884 origin-safe H5 thresholds and exact keys/truths for all eight R0 cohorts.
These are data/contract checks, not predictive performance. Data availability
is established locally; Git publication does not provision private inputs in Cloud.

The requested standalone `DESING_Beta01.md` is absent; the checked-in linked
design owns the implemented scope. [DEC-138](../../traking-concluciones.md#dec-138-freeze-the-bounded-exp-beta02-count-forecasting-protocol)
and [protocol.json](protocol.json) were committed before any Beta02 fit.
Protocol SHA-256: `6a7697f0011680e59b697422b35a3f928fbe5a8a9dc6e74431548ad2581baef1`.

## Model and interpretation

One pooled log-link NB2 regression is fitted for each horizon, year and fixed
climate OFF/ON condition: 16 unique models, no search. Its variance is
`mu + alpha * mu^2`. Mean coefficients and a single dispersion are estimated by
penalized training-only likelihood, with fixed ridge penalty and optimizer bounds.
Learned centers/scales, coefficients, dispersion and convergence diagnostics are
saved as JSON. No neural candidate is justified by this bounded baseline; it is
explicitly `NO_EVALUABLE` rather than added to force a complete result.

The fixed canonical allowlist keeps nine climate aggregates in their original
units/signs, and OFF removes exactly those columns. Count/threshold variables
receive log1p, then training-only standardization. Counts represent notifications,
not population-standardized incidence. Forecasts are conditional on the shared
observed non-excess-at-T cohort; they are not forecasts for all municipality-months.

For target evaluation year Y, training targets end Y-2, selection uses Y-1, and
evaluation uses Y. Origins are embargoed at the preceding role's target end.
T+2 evaluation therefore excludes January across those boundaries. All territories
share cutoffs. Only 2020/2021/2022 and consumed retrospective stress 2024 are
evaluated; no 2025 target, fit, policy or evaluation is permitted.

The SciPy distribution uses `r=1/alpha`, `p=r/(r+mu)`. Strict H5 exceedance is
`nbinom.sf(floor(P75), r, p)` using the origin-safe target-month threshold.
T+1 excess equals onset on this cohort. Direct T+2 marginal excess does not
identify the joint non-excess-to-excess transition, so T+2 onset score and alert
are missing with `NO_EVALUABLE`, never replaced by future observed state or an
independence product. References: [SciPy NB distribution](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nbinom.html),
[NB2 log-link definition](https://www.statsmodels.org/stable/generated/statsmodels.genmod.families.family.NegativeBinomial.html).
Statsmodels is a methodological reference, not an added dependency.

R0 is the primary frozen comparator, paired only for complete identical origin,
target and truth records. Beta01 saved G0/L1 probabilities are optional secondary
context. Historical fitting windows differ; comparisons concern procedures, not
isolated causal effects of count modeling. Count MAE/RMSE, log score and discrete
90% predictive coverage/width are separate from onset sensitivity, detections,
false alerts, precision, AP and Brier. There is no R0 count forecast to compare.
Predictive intervals condition on fitted parameters; they do not quantify all
parameter, data-quality or temporal uncertainty.

The past-only whole-tie threshold selector is reused unchanged. The predeclared
joint load/margin checks apply to R0-comparable T+1 strata by year and department.
Four reused years cannot establish statistical noninferiority or superiority;
those remain UNAVAILABLE/NOT_ESTABLISHED. No champion or G5 approval is selected.

## Independent Kedro execution

```sh
KEDRO_DISABLE_TELEMETRY=yes .venv/bin/kedro run \
  --pipeline=exp_beta02 --params=profile=exp_beta02,tracking=disabled
```

Six nodes separate preparation, count fitting, forecast, H5 risk, policy and
evaluation. Strict catalog/profile bindings reject scientific overrides and
tracking. The existing canonical/R0 reader and atomic no-overwrite publisher are
reused without modification. The new source verifies its own protocol and the
optional explicit Beta01 publication; no latest search or automatic rebuild.
Sources, used code and runtime identities accompany every publication under
`tmp/kedro-migration/exp-beta02-runs/<bundle_id>/`. Native models, count forecasts,
event predictions, separate metric tables, policies, comparison audit and
conclusions are hashed and immutable. Historical graphs and inputs are untouched.

## Validation and known inherited limitation

Eight new generated-only cases validate NB likelihood/gradient, predictive law,
strict H5 tails, unavailable T+2 onset, exact target joins, chronology, strict
pairing, label-perturbation isolation, reproducibility, native graph/persistence,
tamper/no-overwrite, protocol/profile guards and nonconvergence without retries.
The mapped focused batch passes 63 tests (25 inherited framework warnings).
Scoped Ruff, formatting and mypy pass; base bootstrap still rejects optional
modeling/tracking imports during registration.

The separately supplied old private migration inventory still rejects the
already-changed decision register, as it did before this experiment. Its baseline,
cleanup mapping and expected historical hashes were not weakened or rewritten.
That private historical discrepancy is reported separately from passing public
checks and from current source/data preservation.
