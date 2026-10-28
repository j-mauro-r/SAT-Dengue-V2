# EXP03.1 validation evidence

Status: PASS for the source-free technical validation surface.

The following validations were run without any scientific data read, model fit, tracking write, or real execution.

## Executed checks

1. Contract, unit and integration tests
   - Command: `python -m pytest tests/contracts/test_exp03_1_contract.py tests/unit/test_exp03_1_features.py tests/integration/test_exp03_1_integration.py -q`
   - Result: PASS, 26 passed in 0.51s

2. Canonical protocol + matrix verification
   - Command: `python -m sat_dengue.experiments.exp03_1_contract --check`
   - Result: PASS

3. Synthetic bundle generation
   - Command: `python -m sat_dengue.experiments.exp03_1_demo --output tmp/exp03-1-synthetic-example`
   - Result: PASS
   - Generated bundle SHA-256: `8b64af888b31b2edf6dfe3f867371d8c28fb46a0de476ca1b66be240b80adb72`

4. Ruff lint
   - Command: `python -m ruff check src/sat_dengue/experiments/exp03_1_*.py src/sat_dengue/tracking/exp03_1.py tests/contracts/test_exp03_1_contract.py tests/unit/test_exp03_1_features.py tests/integration/test_exp03_1_integration.py`
   - Result: PASS

5. Ruff format
   - Command: `python -m ruff format --check src/sat_dengue/experiments/exp03_1_*.py src/sat_dengue/tracking/exp03_1.py tests/contracts/test_exp03_1_contract.py tests/unit/test_exp03_1_features.py tests/integration/test_exp03_1_integration.py`
   - Result: PASS

6. Mypy
   - Command: `python -m mypy src/sat_dengue/experiments/exp03_1_*.py src/sat_dengue/tracking/exp03_1.py tests/contracts/test_exp03_1_contract.py tests/unit/test_exp03_1_features.py tests/integration/test_exp03_1_integration.py`
   - Result: PASS, no issues found

## Environment verification

- Python: `3.12.11`
- Dependencies: installed via the repository’s official extra set `python -m pip install -e '.[dev,modeling,tracking]'`
- MLflow UI was started against the local protected store: `mlflow ui --backend-store-uri sqlite:////Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/tmp/kedro-migration/replay-mlflow/tracking.sqlite --default-artifact-root file:///Users/mauriciorodriguez/Projects/AI-Masters/SAT-Dengue-V2/tmp/kedro-migration/replay-mlflow/artifacts`
- Local MLflow URL: `http://127.0.0.1:5000`

## Findings

- No technical defects were identified that prevent faithful protocol execution.
- The validation surface confirms that only a human-authorized real execution may proceed.
- No real scientific results, model fits, or permanent MLflow writes were produced in this review.
