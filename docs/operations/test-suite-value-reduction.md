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

## Concurrent main integration

During validation main advanced from the initial `ba2870b` base to
`9c7c1edaa490e39f7daa6386b9a4a6f5b2185ef7` (#38, three-phase EXP03 admission).
That commit was merged without overwriting either history. The only conflict,
TESTING_GUIDE.md, retained both the operational-admission section and the new
public selection. The critical CI inventory now explicitly requires admission.
All own scientific-source/configuration/product-protocol/dependency deltas against
this current main remain empty. Updated admission/guards:69PASS; classifier29PASS.


## Exact scenario disposition

| Previous node | Retained node |
| --- | --- |
| `tests/unit/test_model_training.py::test_training_synthetic_graph_fits_every_authorized_family` | `tests/integration/test_full_model_training.py::test_training_synthetic_graph_fits_every_authorized_family` |
| `tests/unit/test_training_preparation.py::test_preparation_synthetic_complete_kedro_graph` | `tests/integration/test_full_training_preparation.py::test_preparation_synthetic_complete_kedro_graph` |
| `tests/unit/test_training_preparation.py::test_preparation_replay_rejects_misalignment_and_boundaries` | `tests/integration/test_full_training_preparation.py::test_preparation_replay_rejects_misalignment_and_boundaries` |
| `tests/unit/test_training_preparation.py::test_preparation_atomic_persistence_and_identity_refusal` | `tests/integration/test_full_training_preparation.py::test_preparation_atomic_persistence_and_identity_refusal` |
| `tests/unit/test_training_preparation.py::test_preparation_native_bundle_rejects_identity_drift` | `tests/integration/test_full_training_preparation.py::test_preparation_native_bundle_rejects_identity_drift` |
| `tests/unit/test_final_evaluation.py::test_native_roundtrip_reuse_verify_no_fallback_and_budget` | `tests/integration/test_full_final_evaluation.py::test_native_roundtrip_reuse_verify_no_fallback_and_budget` |
| `tests/unit/test_final_evaluation.py::test_evaluation_synthetic_graph_is_source_free_atomic_and_repeatable` | `tests/integration/test_full_final_evaluation.py::test_evaluation_synthetic_graph_is_source_free_atomic_and_repeatable` |
| `tests/unit/test_final_evaluation.py::test_evaluation_rejects_foreign_synthetic_inputs_before_inference` | `tests/integration/test_full_final_evaluation.py::test_evaluation_rejects_foreign_synthetic_inputs_before_inference` |
| `tests/unit/test_final_evaluation.py::test_evaluation_publication_is_atomic_read_only_and_never_overwrites` | `tests/integration/test_full_final_evaluation.py::test_evaluation_publication_is_atomic_read_only_and_never_overwrites` |
| `tests/unit/test_final_evaluation.py::test_evaluation_rejects_missing_predictions_before_alerting` | `tests/integration/test_full_final_evaluation.py::test_evaluation_rejects_missing_predictions_before_alerting` |
| `tests/unit/test_final_evaluation.py::test_evaluation_rejects_semantic_snapshot_override_even_with_recomputed_hash` | `tests/integration/test_full_final_evaluation.py::test_evaluation_rejects_semantic_snapshot_override_even_with_recomputed_hash` |
| `tests/unit/test_final_evaluation.py::test_evaluation_rejects_decision_metric_policy_inconsistency` | `tests/integration/test_full_final_evaluation.py::test_evaluation_rejects_decision_metric_policy_inconsistency` |
| `tests/unit/test_kedro_data.py::test_data_synthetic_graph_publishes_counts_labels_and_exclusions` | `tests/integration/test_full_kedro_data.py::test_data_synthetic_graph_publishes_counts_labels_and_exclusions` |
| `tests/unit/test_xgboost_candidate.py::test_native_model_and_preparer_roundtrip` | `tests/integration/test_full_xgboost_candidate.py::test_native_model_and_preparer_roundtrip` |
| `tests/unit/test_xgboost_candidate.py::test_pipeline_external_perturbation_cannot_change_fitting` | `tests/integration/test_full_xgboost_candidate.py::test_pipeline_external_perturbation_cannot_change_fitting` |

All 15 test bodies and decorators (33 parameterized cases) and the preparation setup fixture were AST-identical in the mechanical relocation commit. Normalized collection for those five surfaces remained 162: 129 units and 33 integrations.

| Absorbed surface | Equivalent retained protection |
| --- | --- |
| Unknown-only EXP01 eligibility test | `test_operational_eligibility_depends_only_on_observed_current_state` now parametrizes 0/1/NA; future-label effects reach the labels boundary for both horizons |
| Tautological evaluation-copy comparison | `tests/integration/test_exp03_causal_flow.py::test_evaluation_label_mutation_cannot_change_fit_inputs_or_selection_policy` captures actual fit/calibration/selection/evaluation and detects selector poison |
| `test_exp03_causality.py` feature/zero/coverage/reconstruction/profile scenarios | Same test names in `test_exp03_revision.py`; shared source-free fixture in `exp03_causal_fixture.py` |
| `test_exp03_causality.py` interval/exposure/no-onset scenarios | Same test names in `test_exp03_evaluation.py`; no assertion removed |
| Duplicate HTTP municipal inventory | Exact persisted fixture equality in HTTP; territorial completeness remains in `test_read_only_api_contract.py` |
| Duplicate service repeated-query/no-write check | `test_repeated_http_queries_are_identical_and_do_not_modify_files` reaches the same service/repository, additionally rejects write modes at both Python open APIs |
| Preparation/training identical AST import loops | `test_repository_bootstrap.py::test_training_domains_have_no_framework_or_filesystem_imports[domain]` preserves both domains and forbidden sets; data-specific calls/import restrictions remain separate |
| Transport 44 mutations ×4record classes ×2bundle boundaries, plus alias/stress cases: 367 cases | 44 direct invalid-rule cases +4class checks +3alias checks +4stress checks =55 units; actual-producer valid bundle + invalid write/reload =3 integration cases; total58 |
| Full EXP03 generated estimator probe / benchmark / producer-shaped bundle boundaries | `test_exp03_generated_engine.py`, `test_exp03_benchmark.py`, `test_exp03_transport_bundle.py` under integration; bodies/decorators preserved |

Transport rule equivalence: every original invalid field/value remains in `MUTATIONS`, tested directly against the shared validator. Each annual/common/pooled/unavailable class independently proves valid admission and label/counter rejection. Alias normalization and year-only rejection cover all three periods. Native tamper fixtures regenerate JSON, CSV, annual summary, hashes and bundle identity before semantic rejection. No test-module imports remain in those shared fixtures.

## Historical evidence boundary

`historical_artifact` identifies frozen-output/notebook acceptance; existing skip conditions and reasons are unchanged and visible under CI `-v` / repository `-ra`. Three monthly-report tests remain skipped when their artifacts are absent. The notebook is tracked historical code-only identity evidence; its recovery version and owner remain in `repository-disposition.json` (`861b36966cec26d1d2b36edee4d6ada6d5bc0930:...`). Missing monthly snapshots cannot supply verified hashes or new provenance here; their acceptance remains UNVERIFIED, not synthetic PASS. No historical adapter or artifact was removed. Training-readiness tests use generated notebook/manifests and stay ordinary unit regressions; they do not require frozen private outputs.

## Review and measurement

An independent same-backend advisory review found one consumed-contract cache-key omission; it was fixed and independently rechecked. No remaining correctness findings. This is not cross-vendor/formal orchestra review, scientific approval or merge approval. Five in-memory oracle mutation probes reject nearest/lower percentiles and consistently shifted target/history; orchestration poison is detected by its real-flow assertions. No deliberate production mutation was committed.

Initial base static inventory:57 modules /573 functions, collection1315selected /1327total. After main advanced, isolated `9c7c1ed` baseline:58 modules /582 functions and1341selected /1353total. Final branch:66 modules /592 functions,1064selected /1076total. Both current-main and final collections deselect the same12private cases; skipif decorators remain4 on each side. No full execution timing comparison with baseline is claimed. Literal `pytest.skip` and `xfail` additions:zero. Existing conditional historical skips are retained. A full pre-change timing was not run; no same-environment whole-suite speedup is claimed. Mechanical surface timing53.61s, transport+reporting+benchmark gate18.30s; these are separate scopes, not before/after performance comparisons.

Parametrization declarations: 126 before /133 after. These counts do not replace behavioral equivalence. The late classifier regression also rejects baseline rename handling in two in-memory probes.

## Executed quality and boundaries

Scoped Ruff/format/mypy and the whole source/test quality selection PASS; the
classifier script is checked explicitly too. Markdown links, diff whitespace and
changed-file secret/generated-artifact scans PASS. Canonical EXP03 identity stays
`18ce612581d710245294f3966187178e697df1972d45b460f54be7cc2f4d1611`
(408cells/102terminal). The initial and concurrent-main interrupted gates remain
recorded as interrupted, never PASS. Final complete public gate: **PASS — 1061 passed, 3 expected historical skips,
12 private deselections, 540 existing dependency/framework warnings;1173.91seconds.**
The command exactly matches CI and the guide. DWP observed gate sequence5 also
passed Ruff, format, mypy, Markdown links and diff checks.

Actual wheel build, source-byte comparison, fresh base-only installation, optional
root absence, pip check and foundation bootstrap PASS. The official installed API
wheel probe PASS outside the source tree. An initial probe placed the temporary
installation inside the checkout and correctly failed its isolation assertion;
rerunning the unmodified official script with its normal external temporary root
passed. No optional modeling/tracking package entered the base environment.

No adapter was retired and no private evidence was read or made a public
requirement. Real experiment execution/approval and permanent MLflow remain
outside this work. Budget, gates, targets, methods and consumed2025 state match
current main.

The first completed post-main gate failed its old filename-substring CI contract
(1059 passed /1failed /3skipped). That contract now parses actual public pytest
selection, requires unit/contracts/integration roots, verifies the E2E and
disposition files are selected and rejects exclusion flags. All scientific,
private-evidence and historical-notebook assertions remain. Focused disposition
and classifier54PASS, with two in-memory exclusions rejected. The final complete
gate above includes both this correction and the late rename regression; no
failure was waived. The classifier uses `--no-renames` so both old and new risk
paths survive a scientific-source rename into documentation.

Whole source/test quality:253formatted files, mypy251source/test files; the
classifier script and disposition tests also pass their scoped checks. Independent
same-backend review rechecked the main merge, cache fix, rename fix and semantic
CI contract and reported no unresolved correctness findings.
