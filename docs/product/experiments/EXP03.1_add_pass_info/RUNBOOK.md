# EXP03.1 replay persistence runbook

Status: `EXP031_REPLAY_COMPARISON_NORMALIZATION_FIXED_NOT_REEXECUTED`.
The completed replay is preserved; this correction did not repeat science.
G5: `NOT_APPROVED`; champion: `not_selected`. EXP04 remains
outside this repair; no additional 12/24/36-month OOF history is generated.

## Comparison normalization correction (2026-10-31)

The stored `REPLAY_MISMATCH` arose from equal-valued NumPy versus Python float
types in `cells/<integer>/threshold` before serialization. Canonical JSON restores
both as Python floats; comparison of the persisted bundles is exact. This is no
demonstrated scientific discrepancy. Future publication compares the canonical
serialization round-trip without changing scientific contents or bundle format.

The validator still verifies package schema/protocol, integrity, hashes, native
reloads and MLflow lineage. It corrects only stored `REPLAY_MISMATCH` evidence
with a nonempty list containing exclusively `cells/<integer>/threshold` paths,
an exact recalculated `EXACT_OBSERVABLE_REPLAY` with no differences, and otherwise
unchanged comparison metadata. Thresholds, alerts, ranking, ties, bins, discrete
metrics and retained selection must match exactly; numeric tolerance alone cannot
qualify. The result reports `stored_comparison_status: REPLAY_MISMATCH`,
`comparison_correction: canonical_numeric_type_normalization_v1`, and
`replay.status: EXACT_OBSERVABLE_REPLAY`. Other differences remain failures.

The existing bundle, companion, manifests and produced artifacts remain immutable.
No experiment, Kedro pipeline, model training, private-data read or permanent MLflow
write was performed for this correction. Only rerun the read-only validator below
with the preserved tracking root and original bundle path; do not repeat preflight
or scientific execution. Validation of this existing bundle was not run during
implementation.

```sh
python -m sat_dengue.experiments.exp03_1_validate \
  --bundle tmp/kedro-migration/exp03-1-runs/4fd644502e8fb2bb18155060bba68aedd7fc295cf66e16401b91c44af72781de \
  --bundle-id 732a9d7743b4c54d9252adf7095f2c4e2775cd4d6472446d2bd2e41a476927f4 \
  --tracking-root "$SAT_DENGUE_TRACKING_ROOT" \
  --original-bundle "$SAT_DENGUE_EXP03_1_ORIGINAL_BUNDLE"
```

## Repair and unchanged science

The runner retains the existing fitted predictor, its train-only preparer and
sigmoid calibrator. It captures the three existing raw prediction results,
calibrated scores, labels, ordered inputs and source row indices for training,
calibration, selection and evaluation, pre-eligibility role membership, cohort
ledger, temporal windows and threshold-selection result. Calibration-role
calibrated scores require only applying the already fitted sigmoid; no additional
prediction or fitting call is introduced by capture. Native reload validation
performs inference on saved inputs, never fitting.

The 96-cell matrix (including 36 M00), M00/M01/M02, predictor order, H5 labels,
cohorts, cuts, horizons, objectives, transformations, families, parameters, seeds,
calibration, threshold selection, false-alert budget, alert rules and metrics are
unchanged. The frozen scientific protocol and matrix are unchanged. The new
execution protocol is `exp03-1-replay-persistence-v1`, bound to a new approval.

The original bundle and its tracking are immutable:

- Bundle ID: `afcb8b4a6cb512c1247fc52c5d9786a3f0d245663981a29f8f23ac76873a3e04`.
- Bundle SHA-256: `5b3f20a266c5e6aae7d2727a00a2213ea9cc3bc691bac5f02267a3e44edc5619`.
- MLflow parent: `a37877c20dbd4b1382567e79e8d89e7b`.
- 96 cells, 60,207 final prediction keys, 36 M00 cells.

## New artifacts and equivalence contract

Each new cell uses existing `FrozenCell` / `save_cell` / `load_cell` storage:
`model.native`, `state.json`, `checksums.json`. State includes the preparer,
calibrator, threshold, scientific identity and role records, with complete float
precision, pandas dtypes, feature order and source index order. Source/event
month audit tables are retained when supplied by the existing frames. Missing
availability and label-maturity dates remain explicitly unknown; they are never
inferred from target dates.

A new publication uses `exp03-1-real-manifest-v2` and includes `replay/manifest.json`
and `replay/<cell_id>/...`. The companion inventory hashes every native/state
artifact and records the original reference, new bundle hash, observed environment,
persistence counters, per-role reload results and original/replay comparison.
Historical v1 bundles with just `bundle.json` and `manifest.json` remain readable.
All artifacts stay in protected repository `tmp/`, rejecting external paths,
symlinks and existing destinations. Partial capture directories are not published
as successful evidence and must be retained for diagnosis. No original artifact
is removed or overwritten.

Equivalence requires exact cell identities, prediction keys and order, labels,
error classes, cohort hashes, predictor order, source hashes, exposure,
thresholds (including null), discrete metric counts/supports, TP/FP/FN/TN, alert
bits, ranking, reliability-bin membership and score-tie groups. Whole-tie rules
remain frozen in the scientific protocol. Probabilities, continuous metrics and
paired score deltas first use exact equality, then `atol=1e-12, rtol=0`. Numeric
tolerance never excuses a discrete, ranking, bin, tie or selection change.

Results distinguish `EXACT_OBSERVABLE_REPLAY`, `NUMERICALLY_COMPATIBLE_REPLAY`,
`REPLAY_MISMATCH` and `NOT_COMPARABLE`. Historical models, preparers, calibrators,
intermediate scores, selection tie groups/details, role membership and observed
environment are absent: their comparison is always `NOT_COMPARABLE`, even when
all retained observables match. Reload checks establish the replay's internal
reproducibility, not identity with absent historical state. A mismatch is
published as evidence and validation exits unsuccessfully; it never replaces M00.
EXP04 must separately assess its temporal and OOF requirements.

## Future metadata preparation and preflight

**Do not execute these commands under the implementation-only authorization.**
Use a clean reviewed commit, a new output path and a new tracking root. Replace
`<original_execution_directory>` with the preserved original directory, not its
bundle ID unless that is its actual directory name. No other placeholders are
needed through preflight.

```sh
export SAT_DENGUE_EXP03_1_ORIGINAL_BUNDLE=tmp/kedro-migration/exp03-1-runs/<original_execution_directory>
export SAT_DENGUE_EXP03_1_REPLAY_SOURCES=tmp/kedro-migration/exp03-1-replay-preflight/source-identities.json
export SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/exp03-1-replay-mlflow
```

Prepare the metadata inventory from the verified original result bundle. This
reads the historical result, **not the eight scientific input files**; do not
substitute unverified current input hashes. The preflight itself reads only this
metadata inventory, code/configuration and local tracking metadata. It does not
open scientific sources or the original predictions, fit, reserve or write MLflow.

```sh
python - <<'PY'
import os
from pathlib import Path
from sat_dengue.configuration import canonical_bytes
from sat_dengue.experiments.exp03_1_validate import read_original
original = read_original(Path(os.environ['SAT_DENGUE_EXP03_1_ORIGINAL_BUNDLE']))
files = original['bundle']['provenance']['source_admission']['files']
assert len(files) == 8
path = Path(os.environ['SAT_DENGUE_EXP03_1_REPLAY_SOURCES'])
path.parent.mkdir(parents=True, exist_ok=True)
with path.open('xb') as stream:
    stream.write(canonical_bytes(files))
PY
KEDRO_DISABLE_TELEMETRY=yes python -m sat_dengue.experiments.exp03_1_preflight \
  --output tmp/kedro-migration/exp03-1-replay-preflight/receipt.json
```

Review `exp03-1-replay-preflight-v1`: the original reference, eight authorized
source hashes, clean commit/code identity, environment hash, Python, platform,
architecture, installed numerical-library versions, native thread pools and thread
configuration. Unverified source content remains pending until authorized
admission. Counter values and MLflow writes must all be zero. Missing source
inventory/linkage cannot authorize execution. Importing numerical backends here
only observes their loaded runtime; it never trains a model.

## New replay-only authorization

Mauricio and the independent reviewer must approve this replay and its exact
receipt; the historical approval and `SAT_DENGUE_EXP03_1_APPROVAL` do not authorize
it. Manually create a new local approval JSON with exactly:

- `schema`: `exp03-1-replay-approval-v1`; `experiment_id`: `EXP031`;
  `authority`: `Mauricio`; `independent_reviewer`: reviewed name other than Mauricio.
- `preflight_sha256`: canonical `digest(receipt)`.
- Exact copies of receipt fields `protocol_sha256`, `matrix_sha256`,
  `source_descriptor_sha256`, `configuration_sha256`, `data_version`, `git_revision`,
  `replay_protocol`, `original`, `original_bundle_path`, `authorized_source_files`,
  `environment_sha256`.
- `real_execution_authorized`, `replay_only_authorized`, `m00_refit_authorized`,
  `variant_refits_authorized`, `retrospective_availability_acknowledged`: all `true`.
- `G5_approval`, `champion_selection`: both `false`.

Do not generate this approval as part of the repair. Its future path is:
`tmp/kedro-migration/exp03-1-replay-preflight/approval.json`.

## Future authorized replay and read-only validation

Only after the new approval is present, run:

```sh
SAT_DENGUE_EXP03_1_REPLAY_APPROVAL=tmp/kedro-migration/exp03-1-replay-preflight/approval.json \
KEDRO_DISABLE_TELEMETRY=yes kedro run --pipeline=exp03_1 \
  --params="profile=exp03_1,tracking=enabled,experiment_id=EXP031"
```

The existing admission verifies the eight source contents against the newly
approved inventory and original before fitting. A new reservation, bundle and
MLflow parent/children are required. Reusing the original tracking root is
rejected. The companion automatically compares against the pinned original;
never interpret completion alone as equivalence. The final output supplies the
new `bundle_path` and `bundle_id` for this exact validation command:

```sh
python -m sat_dengue.experiments.exp03_1_validate \
  --bundle <new_bundle_path> --bundle-id <new_bundle_id> \
  --tracking-root "$SAT_DENGUE_TRACKING_ROOT" \
  --original-bundle "$SAT_DENGUE_EXP03_1_ORIGINAL_BUNDLE"
```

Validation rechecks hashes, native reloads and saved comparison against the
original, plus existing MLflow lineage. Historical bundles remain valid with the
original three arguments; their replay status is `NOT_COMPARABLE`. Preserve both
bundles, native states, receipts, approvals, tracking, comparison and original
scientific evidence regardless of outcome. Neither result approves G5 or selects
a champion.
