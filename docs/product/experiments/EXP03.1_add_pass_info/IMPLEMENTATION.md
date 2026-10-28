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

EXP03 functions are reused only as immutable references or pure helpers. EXP00–EXP03 protocols, matrices, bundles, and conclusions are not modified.
