# Phase 3 manual execution handoff

This is an operational consumer of the [Phase 2 implementation](PHASE2.md), not
an authorization. `execution=not_authorized`, `phase3_authorized=false` and
`training_authorized=false` remain mandatory in the protocol and training
contract. G5 remains `NOT_APPROVED`.

Before proposing a real execution, resolve the human scientific freeze and
separately approved national/excess/comparator/exposure annex. Pin every annex
table's repository-relative canonical path, SHA256 and byte size. National cells
also require full row count, key/label hash and feature-value hash. The original
Phase 1 bundle must remain byte-identical. Annex files belong under
`data/processed/exp_delta03-inputs`; their explicit schema is in the
[artifact catalogue](artifact-schemas.json).

Prepare the pinned modeling/tracking runtime using the repository's
[migration owner](../../../operations/kedro-migration.md). Choose the existing
permanent local tracking root explicitly; never infer it from a synthetic run.
Freeze a clean commit, protocol, training contract, catalogue, parameters,
publication/tracking roots, dependencies and derived model/calibrator caps.
Run `kedro run --pipeline=exp_delta03_preflight` with its matching profile and
tracking disabled. Preflight hashes real payload bytes and reads JSON metadata
only. It does not permit a fit or guarantee historical operational availability.

A distinct human-signed `exp-delta03-phase3-authorization-v1` JSON file under
`tmp/exp-delta03-phase3` must contain phase 3, `approved_by=Mauricio`, the exact execution fingerprint and its canonical SHA256, timezone-aware
issue/expiry timestamps, explicit resume permission, exact resource limits and
acknowledgements `retrospective_only`, `no_PIT_or_deployment`, `2025_excluded`,
`2024_stress_separate`, `manual_execution`. The fingerprint includes actual
runtime versions and code/configuration hashes. No template approval is valid.
The runtime validates that grant before parsing private input tables or writing
scientific outputs. Human approval must be recorded with the exact identity;
never manufacture or automatically renew it.

Only after Mauricio independently authorizes that identity may the matching
`exp_delta03` profile, tracking enabled, be run manually. The native protected
root is `data/processed/exp_delta03`. The execution reserves one identity, rejects
symlinks and unsafe paths, enforces derived adjustment caps and checks a
cooperative wall deadline. Incomplete adjustments without verified checkpoints
require inspection. Completed checkpoints and publications are reused without
refitting; changed bytes fail closed. The wall deadline does not forcibly kill
an in-progress native fit; completion cannot be reported after a detected expiry.

Review the native receipt and aggregate tracking links after the manual run.
Any scientific results remain retrospective consolidated evidence. Keep 2024
separate, exclude 2025, preserve non-evaluable cases, and obtain separate human
decisions for interpretation, G5, merge and deployment.
