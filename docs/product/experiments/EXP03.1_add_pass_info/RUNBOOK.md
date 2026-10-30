# EXP03.1 operational runbook

## Status boundary

This runbook describes a future command path only. Do not execute it until
Mauricio explicitly authorizes this reviewed revision. Execution authorization
does not approve G5, select a champion, or establish a scientific conclusion.
The local JSON approval is an auditable human action, not cryptographic
authentication. A clean reviewed Git revision is required.

All paths below are repository-local and under ignored `tmp/`. The tracking
store is separate from EXP03 and from any permanent scientific store:

```sh
export SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/exp03-1-mlflow
```

## 1. Structural preflight

This checks protocol, matrix, source inventory and local tracking-store
structure. It does not open or hash scientific source files.

```sh
KEDRO_DISABLE_TELEMETRY=yes \
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/exp03-1-mlflow \
python -m sat_dengue.experiments.exp03_1_preflight \
  --output tmp/kedro-migration/exp03-1-preflight/receipt.json
```

Review the emitted receipt. It must report `structural_pass`, zero initial
effect counters, `G5: NOT_APPROVED`, and `champion: not_selected`. Do not
authorize a dirty revision or a receipt whose source, protocol, matrix,
configuration, tracking root or Git revision is unexpected.

## 2. Human approval

After review, Mauricio must manually create
`tmp/kedro-migration/exp03-1-preflight/approval.json`. Copy each bound hash and
revision from the structural receipt. The approval JSON must contain exactly
these keys; replace each `<...>` value with the reviewed value:

```json
{
  "schema": "exp03-1-execution-approval-v1",
  "experiment_id": "EXP031",
  "authority": "Mauricio",
  "independent_reviewer": "<reviewer name other than Mauricio>",
  "preflight_sha256": "<canonical receipt SHA-256>",
  "protocol_sha256": "<receipt protocol_sha256>",
  "matrix_sha256": "<receipt matrix_sha256>",
  "source_descriptor_sha256": "<receipt source_descriptor_sha256>",
  "configuration_sha256": "<receipt configuration_sha256>",
  "data_version": "<receipt data_version>",
  "git_revision": "<receipt git_revision>",
  "real_execution_authorized": true,
  "m00_refit_authorized": true,
  "variant_refits_authorized": true,
  "retrospective_availability_acknowledged": true,
  "G5_approval": false,
  "champion_selection": false
}
```

Compute `preflight_sha256` from the saved receipt without reading scientific
inputs:

```sh
python -c 'import json; from sat_dengue.experiments.exp01 import digest; print(digest(json.load(open("tmp/kedro-migration/exp03-1-preflight/receipt.json"))))'
```

The approval path is explicit; missing, stale, altered or incomplete approval
is rejected before source admission.

## 3. Future authorized real execution

Run only after the human approval is in place and the reviewed revision is
clean:

```sh
SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/exp03-1-mlflow \
SAT_DENGUE_EXP03_1_APPROVAL=tmp/kedro-migration/exp03-1-preflight/approval.json \
KEDRO_DISABLE_TELEMETRY=yes \
kedro run --pipeline=exp03_1 \
  --params="profile=exp03_1,tracking=enabled,experiment_id=EXP031"
```

On success, the final JSON line reports `bundle_path` and `bundle_id`. The
run writes only to the local ignored tracking store and the protected real
bundle root `tmp/kedro-migration/exp03-1-runs/`. The result remains
`G5: NOT_APPROVED` and `champion: not_selected`.

## 4. Validate the real bundle and MLflow lineage

Use the exact `bundle_path` and `bundle_id` printed by the run:

```sh
python -m sat_dengue.experiments.exp03_1_validate \
  --bundle <bundle_path> \
  --bundle-id <bundle_id> \
  --tracking-root tmp/kedro-migration/exp03-1-mlflow
```

The validator is read-only. It rejects a missing or altered manifest, an
incomplete cell or contrast grid, mismatched source/protocol identities, and
missing, unfinished or incorrectly tagged parent/child runs.

## 5. Open local MLflow and find the run hierarchy

```sh
mlflow ui \
  --backend-store-uri sqlite:///tmp/kedro-migration/exp03-1-mlflow/tracking.sqlite \
  --host 127.0.0.1 \
  --port 5000
```

In the MLflow run search, locate the parent using the pinned protocol and
verified state:

```text
tags.experiment_id = 'EXP031' and tags.protocol_sha256 = '<protocol_sha256>' and tags.status = 'verified'
```

Use the parent run ID from the validated bundle to find its children:

```text
tags.mlflow.parentRunId = '<parent_run_id>'
```

Each child is keyed by `cell_id` and tagged with `objective`, `variant`,
`family`, `horizon` and `cut`. Only aggregate metrics and identity metadata are
logged; municipality-level prediction rows remain in the protected bundle,
not in MLflow.
