# EXP03.1 execution runbook

Status: READY_FOR_AUTHORIZATION

This runbook is the exact operational preparation for a future real EXP03.1 execution after Mauricio authorizes it. It does not authorize the real scientific run by itself.

## 1) Prepare and verify the environment

From the repository root:

```bash
cd /Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2
python --version
python -m pip install -e '.[dev,modeling,tracking]'
python -m pytest tests/contracts/test_exp03_1_contract.py tests/unit/test_exp03_1_features.py tests/integration/test_exp03_1_integration.py -q
python -m sat_dengue.experiments.exp03_1_contract --check
```

Validated behavior:
- Python: 3.12.11
- Dependencies: kedro==1.7.0, mlflow==3.17.2, pandas==3.0.6, numpy==2.5.4, PyYAML==6.0.3
- Local MLflow store: `tmp/kedro-migration/replay-mlflow`
- MLflow UI store: `sqlite:////Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/tmp/kedro-migration/replay-mlflow/tracking.sqlite`
- Artifact root: `file:///Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/tmp/kedro-migration/replay-mlflow/artifacts`

## 2) Execute preflight

The repository's current guardrail path is a source-free validation preflight and expects the exact guarded parameters:

```bash
cd /Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2
python - <<'PY'
from sat_dengue.experiments.exp03_1_preflight import preflight
receipt = preflight({"profile": "exp03_1", "tracking": "disabled", "experiment_id": "EXP031"})
print(receipt)
PY
```

Expected result:
- `status` = `blocked_pending_separate_scientific_authorization`
- `execution_ready` = `False`
- `G5` = `NOT_APPROVED`
- `champion` = `not_selected`

This is the current repository state. The real scientific execution remains denied until a separate, explicit human authorization path is introduced and Mauricio approves it.

## 3) Execute EXP03.1 once (authorized future run only)

The repository does not currently contain an authorized real-science execution path. The guardrail is intentionally fail-closed. Once human authorization is granted, the operational command must be the exact Kedro pipeline registration exposed by the repo:

```bash
cd /Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2
export KEDRO_DISABLE_TELEMETRY=yes
export SAT_DENGUE_TRACKING_ROOT=tmp/kedro-migration/replay-mlflow
kedro run --pipeline=exp03_1 --params=profile=exp03_1,tracking=enabled,experiment_id=EXP031
```

Important:
- This command is intentionally blocked by the current implementation unless the project adds the separate authorization path.
- The current repo state enforces `tracking == "disabled"` for this experiment and refuses real execution.
- No real scientific execution was performed in this review.

## 4) Validate bundle, manifest and MLflow correspondence

After an authorized real execution, validate the bundle and its MLflow lineage with the repository's protected, source-free bundle logic:

```bash
cd /Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2
python -m sat_dengue.experiments.exp03_1_demo --output tmp/exp03-1-synthetic-example
python - <<'PY'
from pathlib import Path
import json
from sat_dengue.experiments.exp03_1_reporting import validate_bundle
from sat_dengue.tracking.exp03_1 import aggregate_projection
bundle_path = Path('tmp/exp03-1-synthetic-example/bundle.json')
raw = json.loads(bundle_path.read_text())
validate_bundle(raw)
aggregate = aggregate_projection(raw)
print({'experiment_id': aggregate['experiment_id'], 'protocol_sha256': aggregate['protocol_sha256'], 'evidence_type': aggregate['evidence_type']})
PY
```

This validates the canonical protocol hash and ensures the bundle remains source-free and non-authorized. For a real authorized run, the same validation step should be applied to the resulting bundle and the associated MLflow run metadata under the same protocol hash.

## 5) Start MLflow UI using the correct store

```bash
cd /Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2
mlflow ui --backend-store-uri sqlite:////Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/tmp/kedro-migration/replay-mlflow/tracking.sqlite --default-artifact-root file:///Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/tmp/kedro-migration/replay-mlflow/artifacts
```

Then open:

```text
http://127.0.0.1:5000
```

## How to locate the execution

In the MLflow UI:
1. Open the experiment named `sat-dengue-bounded-v1`.
2. Filter by `tags.experiment_id = 'EXP031'` or `tags.experiment_id = 'EXP03.1'`.
3. Find the parent run for the protocol hash `46f287468ace7cee7c67220b871cf85a7a9c0670a131d80838d3baf147da0075`.
4. If a real execution is authorized later, inspect the parent run and then the child runs for family/horizon/window lineage.

## Canonical protocol and experiment identity

- Scientific ID: `EXP03.1`
- Technical ID: `EXP031`
- Python/pipeline ID: `exp03_1`
- Protocol SHA-256: `46f287468ace7cee7c67220b871cf85a7a9c0670a131d80838d3baf147da0075`
- MLflow experiment name: `sat-dengue-bounded-v1`
- G5: `NOT_APPROVED`
- Champion: `not_selected`
