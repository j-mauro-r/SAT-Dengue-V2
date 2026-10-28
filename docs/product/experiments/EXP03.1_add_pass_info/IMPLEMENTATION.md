# EXP03.1 implementation traceability

| Requirement | Owner | Tests / evidence | Artifact |
| --- | --- | --- | --- |
| Exact H5 historical zones and T−1…T−12 windows | `exp03_1_features.py` | `test_exp03_1_features.py` | row-level audit/provenance |
| Six nonredundant predictors and audit reconstruction | `exp03_1_features.py` | formula/reconstruction tests | feature and audit tables |
| Paired twelve-state cohort | `exp03_1_features.py` | paired-cohort tests | exclusion/coverage ledger |
| M00/M01/M02, Q1/Q2/Q3 and derived counts | `exp03_1_contract.py` | contract tests | frozen matrix |
| Fail-closed V09 reuse/refit | `exp03_1_engine.py` | hash-drift tests | reuse decision receipt |
| Metrics and persistence diagnosis | `exp03_1_evaluation.py` | integration tests | aggregate tables |
| Safe reporting/tracking | `exp03_1_reporting.py`, `tracking/exp03_1.py` | privacy/no-write tests | protected native + aggregate projection |
| Real-science denial | `exp03_1_preflight.py` | preflight integration tests | blocked receipt |

EXP03 functions are reused only as immutable references or pure helpers. EXP00–EXP03 protocols, matrices, bundles, and conclusions are not modified.

