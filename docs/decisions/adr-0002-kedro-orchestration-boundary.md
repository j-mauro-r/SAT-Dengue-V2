# ADR-0002: Kedro orchestration and immutable configuration

## Status and date

Accepted for the bounded foundation on 2026-10-22 under Mauricio's Session 2
instruction. This extends [ADR-0001](adr-0001-foundation-boundaries.md); its
historical decision and deferred DVC/S3 boundary remain unchanged.

## Context

Scientific Stages 2–5 currently run from preserved scripts and notebooks. Migrating
orchestration must preserve original data, component identities and accepted
scientific decisions. Installing a framework does not establish scientific parity.

## Decision

- Package only used orchestration modules under `src/sat_dengue`. The implemented
  `foundation` graph resolves and persists configuration; no scientific graph is
  registered yet. Domain migration remains a separately authorized task.
- Pure configuration resolution imports neither Kedro nor MLflow. Kedro assembles
  dependencies and validates merged YAML; dataset adapters own reading and atomic
  publication. Tracking remains disabled, with its separately pinned optional
  dependency verified but no adapter implemented before T-tracking.
- Existing scientific JSON documents, including `champion_decision_policy_v1.json`,
  supply every scientific value. Code pins their approved byte identities; YAML
  supplies only `foundation`/`disabled` operational settings. Unknown profiles,
  extra settings, authority/catalog replacement and changed documents fail closed.
  Approved future scientific revisions update the owning JSON and its identity;
  never add a competing YAML policy.
- Each foundation invocation produces a unique execution ID and an immutable JSON
  snapshot containing resolved operational values, scientific documents and their
  original hashes, Git revision/dirty status, source/config/constraints hashes,
  package versions and UTC creation time. Its content hash excludes only itself.
  Atomic no-replace publication creates read-only files under ignored
  `tmp/kedro-migration/runs/<run_id>/resolved.json`. Exact retries reuse identical
  bytes; conflicting bytes fail. This is engineering provenance, not a replacement
  for native scientific bundle identities or hashes.
- Future scientific pipelines must consume the verified resolved configuration
  and publish its snapshot before computation. This wiring and stage parity belong
  to their owning later tasks; foundation makes no E2E replay claim.
- `pyproject.toml` is the only dependency declaration authority. Existing pip
  entrypoints select its extras without duplicating versions. Export resolved pip
  constraints from an isolated install; the constraints identify their source
  metadata hash and are generated, never a second manually maintained list.
- Python 3.12.11 is the observed baseline; package support is bounded to 3.12.
  Kedro 1.7.0 / kedro-datasets 9.6.0 / optional MLflow 3.17.2 resolve together with
  the accepted LightGBM 4.7.0 pin. Preserve historical 4.6 and candidate 4.7 runtimes.
- Mauricio approved a narrow exception for the two changing dependency metadata
  files. Verify their original Git blobs against the original protected inventory
  and their current engineering hashes against the separate metadata ledger. All
  other 2,551 protected files remain unchanged at their original paths. Do not
  modify the original baseline or broaden this mapping.

## Bounded Session 3 extension

Mauricio subsequently authorized only Stage 2 data migration and its closed
two-script preservation mapping. The implemented `data` graph publishes and
consumes the resolved snapshot; the [migration record](../operations/kedro-migration.md#stage-2-execution--session-3)
owns its catalog, isolated outputs and exact original/current identities. The
foundation-specific descriptions above retain the scope of the original decision.
No scientific authority, tolerance or historical exception changes. Stage 3 and
tracking remain separately gated.

## Consequences

No scientific function, data location, cohort, metric, tolerance, target, feature
or decision changes. G5 remains NOT_APPROVED and champion not_selected; consumed
2025 cannot train, tune or select. The 13 historical source exceptions and their
17 KEEP / UNVERIFIED bundles remain closed and excluded from equivalence evidence.
Full historical reproducibility is not established. No generic model/persistence/
tracking interface is created until a real consumer needs it.

The wheel requires the repository's external configuration and authoritative JSON
files; it does not distribute data or claim to be a standalone scientific runner.
The generated constraints are observed on macOS arm64/Python 3.12.11; another
platform still requires resolver and native-runtime verification.

## Sources consulted on 2026-10-22

- [Kedro installation and Python support](https://docs.kedro.org/en/stable/getting-started/install/).
- [Kedro configuration](https://docs.kedro.org/en/stable/configure/configuration_basics/).
- [Kedro Data Catalog](https://docs.kedro.org/en/stable/catalog-data/introduction/).
- [Kedro 1.7.0 publisher metadata](https://pypi.org/project/kedro/1.7.0/).
- [kedro-datasets 9.6.0 publisher metadata](https://pypi.org/project/kedro-datasets/9.6.0/).
- [MLflow 3.17.2 publisher metadata](https://pypi.org/project/mlflow/3.17.2/).
- [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/).

Publisher metadata declares Python >=3.10 for all three distributions;
kedro-datasets requires Kedro >=1.0.0rc1,<2.0.0. MLflow permits NumPy <3,
pandas <4, scikit-learn <2 and SciPy <2. The repository's pinned versions satisfy
those bounds; clean installation and `pip check` supply observed compatibility,
not a claim that metadata alone proves scientific equivalence.
