# EXP03.1 implementation traceability

| Requirement | Owner | Tests / evidence | Artifact |
| --- | --- | --- | --- |
| Exact H5 historical zones and T−1…T−12 windows | `exp03_1_features.py` | `test_exp03_1_features.py` | row-level audit/provenance |
| Six nonredundant predictors and audit reconstruction | `exp03_1_features.py` | formula/reconstruction tests | feature and audit tables |
| Paired twelve-state cohort | `exp03_1_features.py` | paired-cohort tests | exclusion/coverage ledger |
| M00/M01/M02, Q1/Q2/Q3 and derived counts | `exp03_1_contract.py` | contract tests | frozen matrix |
| Exact M00/V09 identity and fail-closed reuse/refit | `exp03_1_engine.py`, canonical EXP03 protocol loader | ordered-predictor, malformed-hash and hash-drift tests | reuse decision receipt |
| Metrics, contrast strata, exposure denominators and persistence diagnosis | `exp03_1_evaluation.py` | tie-invariant AP, grouped, paired and error-class tests | aggregate tables |
| Frozen delay diagnostic reuse | `exp03_1_evaluation.py`, immutable EXP03 diagnostic contract | zero-new-fit and strict-unavailability tests | conditional stress + unable-to-issue records |
| Safe reporting/tracking | `exp03_1_reporting.py`, `tracking/exp03_1.py` | privacy/no-write tests | protected native + aggregate projection |
| Real-science denial | `exp03_1_preflight.py` | preflight integration tests | blocked receipt |
| Complete source-free example | `exp03_1_demo.py` | integration generation test | ignored `tmp/exp03-1-synthetic-example` bundle, aggregate and marker |

## Authorized operational path

The EXP03.1-only command path is wired as a descriptor-only preflight, explicit
approval check, post-approval source admission through the unchanged EXP03
manifest verifier, shared-cohort 96-cell runner, local-only parent/child
tracking, and a real-only checksummed bundle. The run is refit-only today:
without an admitted identity-complete EXP03 V09 artifact, the engine fails
closed to refitting all 96 cells. The approval separately authorizes these
refits; it never approves G5 or selects a champion.

The global parameter validator accepts only the two EXP03.1 profiles when
bound to `experiment_id=EXP031` and enabled tracking. The existing EXP031
experiment-registry entry was verified and reused unchanged; unknown IDs still
fail registry resolution.

The bundle validator independently checks the frozen cell identities,
predictor lists, prediction/threshold/metric consistency, paired contrasts,
source admission lineage, execution counters and the 97-run MLflow identity.
Publication and local tracking are restricted to ignored repository `tmp/`;
no production or scientific MLflow store is configured by this path.

See [RUNBOOK.md](./RUNBOOK.md) for the exact future commands and manual
approval record. No preflight or scientific execution was performed while
implementing this path.

EXP03 functions are reused only as immutable references or pure helpers. EXP00–EXP03 protocols, matrices, bundles, and conclusions are not modified.
