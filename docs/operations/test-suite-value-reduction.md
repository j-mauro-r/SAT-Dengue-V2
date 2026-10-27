# Test-suite value reduction audit

Base: `ba2870bafd6888bb0c2628a06461d6cb52c36cd0` (`origin/main`). Initial checkout was clean at `13f2b77`; no earlier branch was reset. Audit pin `93ebab3` contains unmerged admission changes, absent from this base. Scientific protocol/gates/budget are preserved from main.

Baseline static inventory: 57 modules, 573 test functions. Collection: 1315 selected /1327 total, 12 private deselections. Inventory and collection logs retained in ignored `tmp/suite-baseline-*`.

## Risk matrix

| Guarantee | Baseline owner | Resulting owner / evidence |
| --- | --- | --- |
| Target/horizon; five prior same calendar months | test_consolidated_dataset_pipeline; test_exp02_labels | Independent target/history and interpolation oracles |
| Anti-leakage and temporal availability | test_exp01_onset; test_exp03_causality | Actual orchestration capture; future inputs reach production boundary |
| Train/calibration/selection/evaluation separation | test_exp03_causality | Generated orchestration integration |
| Consumed 2025 | test_exp03_transport_validation | Shared validator rules + coherent-manifest bundle boundaries |
| Budget and authorization | test_exp01_runner; test_exp03; test_exp03_budget | Private IO and side-effect denial guards |
| Admission/source identity | test_exp03_input_integration; EXP02 integration | Full CI critical integration inventory; admission absent on main |
| Reproducibility/provenance | exp03_generated_result | Source/protocol/scope fingerprint invalidation and checksum |
| Exposure/abstentions/uncertainty | test_exp03_evaluation; test_exp03_causality | Retain meaningful distinct scenarios, track moved owners |
| Persistence/semantic tampering | test_exp03_reporting; test_exp03_transport_validation | Re-signed synthetic payload plus write/reload validation |
| Read-only API | test_read_only_api_http; test_dashboard_query_service | All mutating verbs, OpenAPI methods, invalid-query repository guard |
| Historical conservation | test_stage2_*; repository-disposition contracts | Explicit historical marker, no adapter removal or private evidence requirement |

## Boundaries

No scientific source, protocol, metric, budget, model role, gate or permanent tracking store changes are authorized. Historical-only missing artifacts are reported separately. Reduction occurs only after gates A/B; no test is removed without its risk destination.
