# Security and Data Boundaries

## Security Baseline

- Never commit credentials, keys, or secret tokens.
- Never expose secrets in logs, reports, screenshots, or PR text.
- Keep sensitive values in secure environment mechanisms when runtime services are introduced.

## Repository-Level Safety

- Run secret-pattern scans before merge.
- Keep `.dwp/` runtime state untracked except approved tracked files.
- Use least-privilege decisions for automation and CI.

## Data Boundaries

Authoritative source: `docs/data/data-policy.md`

- Large datasets are external (Kaggle/local/Colab).
- Sensitive health data must be treated as restricted by default.
- Tiny synthetic fixtures are the preferred repository test data.

## Vulnerability and Incident Handling

- Record material security decisions in versioned docs/ADRs.
- Escalate suspected vulnerabilities through private channels before disclosure.

## Bounded local MLflow tracking

Tracking is explicitly disabled by default. Enabled execution requires the optional
`tracking` extra and `SAT_DENGUE_TRACKING_ROOT=tmp/<store>`; remote, absolute,
traversing, symlinked or non-ignored stores fail closed. SQLite metadata and the
local artifact store stay ignored. No server, registry, promotion or autologging
is enabled. Domain functions import neither MLflow nor Kedro.

The tracker disables MLflow SDK usage telemetry before importing the optional
dependency and keeps that opt-out active for the process. This also prevents
project tracking calls from emitting SDK events when MLflow was already imported.
A normal-process regression removes pytest/CI opt-outs, blocks network egress and
checks that a fresh import creates no SDK installation-identifier file.

Only approved aggregate metrics, zero real-adjustment counters, contract/input/code/
environment hashes, version tokens, operational profiles and verified relative
engineering pointers may be logged. Raw rows, X/Y, epidemiological records, personal
identifiers, credentials, full environment variables, absolute private paths, native
model/preparer bytes and full bundles are excluded. The optional `satlocal:` artifact
repository accepts only generated schema-validated JSON lineage receipts and rejects
directory uploads. Its logical URI prevents MLflow's normal file-URI expansion from
persisting private checkout paths, including in its automatic Default experiment.

Native scientific publications remain authoritative. Tracking rehashes full bundle
membership and payloads after publication, checks configuration and scientific
status, then records success. Errors/aborts are explicit FAILED/KILLED states;
enabled tracking never falls back silently. An interrupted process can leave RUNNING
metadata, which cannot certify success. Exact verified duplicate publication logging
is marked KILLED and references the prior successful parent. Concurrent writers to
the same logical replay require a single orchestrator; this adapter is sequential.


Composed replay retains these exclusions. Only its additional pipeline identity hash
is projected to MLflow, after the atomic final receipt and complete stage lineage
are verified. Replay/checkpoint storage must be ignored relative repository-local
`tmp/`, without traversal or symlinks. Missing ancestry or changed source, contract,
configuration, manifest, membership or payload identity cannot certify reuse. Final
receipts point to immutable stage outputs; they do not duplicate private bundles.
