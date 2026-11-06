# Separate Phase 2 annex preparation

Mauricio approved this bounded preparation in [Phase 2 authority](PHASE2-AUTHORIZATION.md).
The [inventory](ANNEX-PREPARATION.json) is the single machine-readable record of
what exists and what remains pending. Status is `PREPARED_WITH_EXPLICIT_PENDING_INPUTS`;
`execution_ready=false`. It is a preparation record, not the executable
`exp-delta03-evaluation-annex-v1` consumed by the guarded real pipeline.

The protected content-addressed publication contains:

- `national-primary-cohorts.csv`: copied national eligibility keys and historical
  H5 onset labels for T+1/T+2 in 2020, 2021, 2022 and separate 2024 stress.
- `national-primary-monitored-calendar.csv`: independently selected observed
  calendar keys using historical target-evaluability flags, without conditioning
  on primary eligibility. Coverage-specific monitoring still needs admission.
- `preparation.json` and `manifest.json`: aggregate slice counts, identities,
  source availability, pending inputs and zero scientific-activity counters.

Only cohort columns of the historical national table and Phase 1 membership
were parsed. No feature or frozen-score rows were parsed. Existing source
manifests and payload bytes were hash-verified, including historical excess and
frozen comparator sources. Protected tables stay ignored; public evidence
contains aggregates and hashes. The original Phase 1 publication and PLAN054/055
remain byte-identical. Each national slice preserves exact original regional
key/label correspondence. National X/value correspondence is explicitly pending.

Eligible exposure equals eligible rows/12; independently observed monitored
exposure equals monitored calendar rows/12. The approved B=1 selection cap uses
only eligible selection exposure, floor rounding and whole-score ties. These
annex evaluation exposures do not change thresholds or learned roles.

Onset truth identifies a transition; excess truth identifies an H5 excess month.
An onset negative cannot stand in for an excess negative. Exact H5 excess,
episode and comparator-input joins remain pending. Existing regional R0/G0_OFF/
G0_ON/G1 scores and alert policies must be joined exactly, without refitting or
changing their original policies. Their budget equivalence must be demonstrated
or reported non-evaluable. National frozen learned comparator scores are absent;
no national comparator predictions are authorized by this preparation.

Before a Phase 3 proposal, complete per-cell national X/identities, water/ERA5
cohort and monitored-coverage restrictions, exact excess/episode joins, exact
regional frozen comparator joins, and the complete executable annex descriptor.
No new learned reference may be fitted on evaluation. The Phase 3 handoff also
requires a pinned runtime, clean commit, independent review and a distinct
identity-bound manual human grant. Missing inputs cannot be inferred or replaced
by generated controls.

All evidence is retrospective consolidated and descriptive. 2025 is excluded;
2024 remains a separate consumed stress stratum. No real fitting, calibration,
scientific prediction or permanent MLflow write occurred. No operational PIT,
causal, deployment, Phase 3, G5, champion or merge authorization follows.


The bounded Phase 2 record above remains preserved. PLAN_057 completes its
executable input connections under [Phase 3](PHASE3.md), with a separately pinned
annex in training-contract.json. That admission does not modify the original core
or retroactively make the Phase 2 preparation record an executable annex.
