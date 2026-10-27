"""Stage 4 reference-pipeline regressions without private datasets."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.datasets.legacy_training.events import build_event_context
from sat_dengue.datasets.legacy_training.loading import WindowDataset, _validate_alignment
from sat_dengue.datasets.legacy_training.persistence import publish_artifacts, verify_artifacts
from sat_dengue.datasets.legacy_training.pipeline import _enforce_window_rules
from sat_dengue.metrics import (
    average_precision_metric,
    brier_metric,
    evaluate_metrics,
    false_alarm_ratio_metric,
    onset_sensitivity_metric,
)
from sat_dengue.model_training.references import persistence_reference, train_prevalence_reference


def _index(target_column: str, targets: list[str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "municipality_code": pd.Series(["50001"] * len(targets), dtype="string"),
            "year_month": pd.Series(["2024-01"] * len(targets), dtype="string"),
            target_column: pd.Series(targets, dtype="string"),
            "feature_row": pd.Series(range(len(targets)), dtype="Int64"),
        }
    )


def test_alignment_requires_row_and_key_consistency() -> None:
    X = pd.DataFrame(
        {
            "municipality_code": ["50001", "50001"],
            "zona_canal_t": ["EXCESO", "ALERTA"],
        }
    )
    y = pd.DataFrame({"y_t1": pd.Series([1, 0], dtype="Int64")})
    index = _index("target_period_t1", ["2024-02", "2024-03"])
    development_X = X.copy(deep=True).reset_index(drop=True)
    _validate_alignment(
        X,
        y,
        index,
        y_column="y_t1",
        target_column="target_period_t1",
        development_X=development_X,
    )

    bad_X = X.iloc[[0]].reset_index(drop=True)
    with pytest.raises(ValueError, match="row counts"):
        _validate_alignment(
            bad_X,
            y,
            index,
            y_column="y_t1",
            target_column="target_period_t1",
            development_X=development_X,
        )

    permuted = X.iloc[[1, 0]].reset_index(drop=True)
    with pytest.raises(ValueError, match="feature_row linkage order"):
        _validate_alignment(
            permuted,
            y,
            index,
            y_column="y_t1",
            target_column="target_period_t1",
            development_X=development_X,
        )


class _Dataset:
    def __init__(self, target_column: str, targets: list[str]) -> None:
        self.window_id = "2024-06_t1"
        self.target_column = target_column
        self.train_index = _index(target_column, ["2024-06", "2024-07"])
        self.validation_index = _index(target_column, targets)


def test_future_targets_are_rejected_before_evaluation() -> None:
    ok = cast(WindowDataset, _Dataset("target_period_t1", ["2024-07", "2024-08"]))
    _enforce_window_rules(ok, reserved_start="2025-01")

    leaking = cast(WindowDataset, _Dataset("target_period_t1", ["2024-12", "2025-01"]))
    with pytest.raises(ValueError, match="reserved targets"):
        _enforce_window_rules(leaking, reserved_start="2025-01")

    train_leak = cast(WindowDataset, _Dataset("target_period_t1", ["2024-11", "2024-12"]))
    train_leak.train_index.loc[1, "target_period_t1"] = "2025-01"
    with pytest.raises(ValueError, match="reserved training targets"):
        _enforce_window_rules(train_leak, reserved_start="2025-01")


def test_train_prevalence_uses_train_only_and_is_constant() -> None:
    train_y = pd.Series([1, 0, 1, 1], dtype="Int64")
    predictions, prevalence = train_prevalence_reference(train_y, rows=3)
    assert prevalence == pytest.approx(0.75)
    assert predictions["prediction_probability"].tolist() == [0.75, 0.75, 0.75]
    assert predictions["prediction_label"].isna().all()


def test_persistence_reference_is_horizon_specific_and_deterministic() -> None:
    X = pd.DataFrame(
        {
            "zona_canal_t": pd.Series(["EXCESO", "ALERTA", pd.NA], dtype="string"),
            "municipality_code": pd.Series(["50001", "50001", "50001"], dtype="string"),
        }
    )
    t1 = persistence_reference(X, horizon=1)
    t2 = persistence_reference(X, horizon=2)
    assert t1["horizon"].tolist() == [1, 1, 1]
    assert t2["horizon"].tolist() == [2, 2, 2]
    assert t1["prediction_label"].tolist() == [1, 0, pd.NA]
    assert t1["prediction_kind"].eq("deterministic").all()


def test_metrics_with_empty_denominators_are_non_evaluable() -> None:
    y_all_zero = pd.Series([0, 0, 0], dtype="Int64")
    y_all_one = pd.Series([1, 1], dtype="Int64")
    scores = pd.Series([0.1, 0.2, 0.3], dtype="Float64")
    probs = pd.Series([pd.NA, pd.NA], dtype="Float64")
    labels = pd.Series([0, 0], dtype="Int64")
    index = _index("target_period_t1", ["2024-02", "2024-03"])

    ap = average_precision_metric(y_all_zero, scores)
    assert not ap["evaluable"]

    context = build_event_context(
        index,
        pd.DataFrame(
            {
                "municipality_code": index["municipality_code"],
                "target_period": index["target_period_t1"],
                "excess": y_all_one,
            }
        ),
        target_column="target_period_t1",
    )
    onset = onset_sensitivity_metric(
        y_all_one, labels, index, target_column="target_period_t1", event_context=context
    )
    assert not onset["evaluable"]

    far = false_alarm_ratio_metric(
        pd.Series([0, 0], dtype="Int64"),
        pd.Series([0, 0], dtype="Int64"),
    )
    assert not far["evaluable"]

    brier = brier_metric(y_all_one, probs)
    assert not brier["evaluable"]


def test_probabilistic_reference_needs_threshold_policy_for_event_metrics() -> None:
    y = pd.Series([0, 1, 1], dtype="Int64")
    index = _index("target_period_t1", ["2024-02", "2024-03", "2024-04"])
    predictions = pd.DataFrame(
        {
            "prediction_kind": ["probabilistic"] * 3,
            "prediction_score": pd.Series([0.2, 0.6, 0.6], dtype="Float64"),
            "prediction_probability": pd.Series([0.2, 0.6, 0.6], dtype="Float64"),
            "prediction_label": pd.Series([pd.NA, pd.NA, pd.NA], dtype="Int64"),
        }
    )
    metrics = evaluate_metrics(
        "train_prevalence",
        y,
        predictions,
        index,
        target_column="target_period_t1",
        threshold_policy_declared=False,
        event_context=build_event_context(
            index,
            pd.DataFrame(
                {
                    "municipality_code": index["municipality_code"],
                    "target_period": index["target_period_t1"],
                    "excess": y,
                }
            ),
            target_column="target_period_t1",
        ),
    )
    by_name = {row["metric"]: row for row in metrics}
    assert by_name["average_precision"]["evaluable"]
    assert by_name["brier"]["evaluable"]
    assert not by_name["onset_sensitivity"]["evaluable"]
    assert not by_name["false_alarm_ratio"]["evaluable"]


def test_empty_prediction_frame_returns_non_evaluable_metrics() -> None:
    y = pd.Series([], dtype="Int64")
    index = pd.DataFrame(
        {
            "municipality_code": pd.Series([], dtype="string"),
            "year_month": pd.Series([], dtype="string"),
            "target_period_t1": pd.Series([], dtype="string"),
            "feature_row": pd.Series([], dtype="Int64"),
        }
    )
    predictions = pd.DataFrame(
        {
            "prediction_kind": pd.Series([], dtype="string"),
            "prediction_score": pd.Series([], dtype="Float64"),
            "prediction_probability": pd.Series([], dtype="Float64"),
            "prediction_label": pd.Series([], dtype="Int64"),
        }
    )
    metrics = evaluate_metrics(
        "train_prevalence",
        y,
        predictions,
        index,
        target_column="target_period_t1",
        threshold_policy_declared=False,
        event_context=build_event_context(
            index,
            pd.DataFrame(
                {
                    "municipality_code": index["municipality_code"],
                    "target_period": index["target_period_t1"],
                    "excess": y,
                }
            ),
            target_column="target_period_t1",
        ),
    )
    assert len(metrics) == 4
    assert all(not row["evaluable"] for row in metrics)


def test_artifact_verification_detects_tampering(tmp_path: Path) -> None:
    payloads = {
        "predictions.csv": b"a,b\n1,2\n",
        "manifest.json": b"{}\n",
    }
    bundle = publish_artifacts(tmp_path, "a" * 64, payloads)
    verify_artifacts(bundle, payloads)

    (bundle / "predictions.csv").write_bytes(b"tampered\n")
    with pytest.raises(ValueError, match="stale|corrupted"):
        verify_artifacts(bundle, payloads)


def test_training_pipeline_routes_are_separate_and_safe() -> None:
    from sat_dengue.pipelines.training.pipeline import (
        create_replay_pipeline,
        create_synthetic_pipeline,
    )

    replay = create_replay_pipeline()
    synthetic = create_synthetic_pipeline()
    assert "training_sources" in replay.inputs()
    assert synthetic.inputs() == {"configuration_inputs", "parameters"}
    assert not any("fit" in n.name for n in replay.nodes)
    assert any("fit" in n.name for n in synthetic.nodes)


def test_training_domain_has_no_framework_or_filesystem_imports() -> None:
    import ast

    root = Path(__file__).resolve().parents[2]
    for path in (root / "src/sat_dengue/model_training").glob("*.py"):
        tree = ast.parse(path.read_text())
        names = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        names += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
        assert not {n.split(".")[0] for n in names} & {
            "pathlib",
            "os",
            "tempfile",
            "kedro",
            "mlflow",
        }, path


@pytest.mark.parametrize("name", ["fit", "_fit", "select_and_fit", "train"])
def test_training_replay_guard_rejects_fit_and_search_aliases(name: str) -> None:
    from sat_dengue.datasets.training_legacy import no_fitting

    namespace: dict = {}
    exec("def " + name + "():\n    return None", namespace)
    alias = namespace[name]
    with pytest.raises(AssertionError, match="Forbidden"):
        with no_fitting():
            alias()


def _synthetic_training_configuration() -> dict:
    from sat_dengue.datasets import ConfigurationInputsDataset
    from sat_dengue.model_training.workflow import resolve_synthetic_configuration

    return resolve_synthetic_configuration(
        ConfigurationInputsDataset().load(),
        {"profile": "training_synthetic", "tracking": "disabled"},
    )


@pytest.mark.parametrize("mutation", ["label", "control", "future", "order", "alignment"])
def test_training_rejects_predictor_or_temporal_leakage(mutation: str) -> None:
    from sat_dengue.model_training.workflow import synthetic_cases, validate_window

    cases = synthetic_cases(_synthetic_training_configuration())
    columns = list(cases["train_X"])
    for split in ("train", "validation"):
        cases[split + "_y"] = cases[split + "_y"].to_frame("y_t1")
        cases[split + "_keys"]["feature_row"] = range(len(cases[split + "_keys"]))
    if mutation in {"label", "control"}:
        cases["train_X"]["y_t1" if mutation == "label" else "y_evaluable_t1"] = 1
    elif mutation == "future":
        cases["train_keys"].loc[0, "target_period_t1"] = "2025-01"
    elif mutation == "order":
        cases["train_X"] = cases["train_X"][list(reversed(columns))]
    else:
        cases["validation_keys"].loc[0, "municipality_code"] = "99999"
    dataset = WindowDataset(
        "2018-12_t1",
        "2018-12",
        1,
        "target_period_t1",
        "y_t1",
        cases["train_X"],
        cases["train_y"],
        cases["train_keys"],
        cases["validation_X"],
        cases["validation_y"],
        cases["validation_keys"],
    )
    with pytest.raises(ValueError, match="schema|alignment|Future"):
        validate_window(dataset, columns)


def test_training_equal_window_weights_and_missing_support_are_explicit() -> None:
    from sat_dengue.model_training.workflow import equal_window_means

    windows = [f"{year}-12_t1" for year in (2018, 2020, 2022, 2023)]
    rows = pd.DataFrame(
        {
            "horizon": 1,
            "reference": "gam",
            "metric": "ap",
            "window_id": windows,
            "value": [0.1, 0.2, 0.3, 0.8],
            "rows": [10, 100, 1, 5],
        }
    )
    complete = equal_window_means(rows, windows).iloc[0]
    assert complete.value == pytest.approx(0.35) and complete.evaluable
    for bad in (rows.iloc[:-1], rows.assign(value=[0.1, None, 0.3, 0.8])):
        result = equal_window_means(bad, windows).iloc[0]
        assert pd.isna(result.value) and not result.evaluable and result.windows == 3


@pytest.mark.parametrize("mutation", ["payload", "manifest", "membership", "missing"])
def test_training_publication_is_immutable_and_detects_corruption(
    mutation: str, repo_tmp_path: Path
) -> None:
    import json

    from kedro.io import DatasetError

    from sat_dengue.datasets.training import TrainingBundleDataset, assemble_training_payloads

    resolved = _synthetic_training_configuration()
    result = {
        "mode": "synthetic",
        "tables": {"predictions.csv": pd.DataFrame({"p": [0.5]})},
        "payloads": {},
        "real_model_fits": 0,
        "real_preparer_refits": 0,
    }
    data = assemble_training_payloads(result, resolved)
    root = Path.cwd()
    directory = str(repo_tmp_path)
    dataset = TrainingBundleDataset(str(Path(directory).relative_to(root)))
    with pytest.raises(DatasetError, match="explicit"):
        dataset.load()
    dataset.save(data)
    saved = dataset.load()
    bundle = root / saved["path"]
    with pytest.raises(Exception, match="exists|Existing|already"):
        dataset.save(data)
    assert json.loads((bundle / "provenance.json").read_text()) == resolved
    name = "manifest.json" if mutation == "manifest" else "predictions.csv"
    path = bundle / name
    path.chmod(0o644)
    if mutation == "missing":
        path.unlink()
    elif mutation == "membership":
        (bundle / "extra.json").write_text("{}")
    else:
        path.write_bytes(b"changed")
    with pytest.raises(DatasetError, match="changed|missing|verified"):
        dataset.load()


@pytest.mark.parametrize("mutation", ["contract", "family", "selection", "root"])
def test_training_legacy_rejects_unknown_configuration_before_reading_models(mutation: str) -> None:
    from sat_dengue.datasets.legacy_training.contract import ModelTrainingConfig
    from sat_dengue.datasets.training_legacy import LegacyTrainingLoader

    config = ModelTrainingConfig(Path.cwd())
    family, ablation = "xgboost", None
    if mutation == "contract":
        config = ModelTrainingConfig(Path.cwd(), contract_path=Path("tmp/unapproved.json"))
    elif mutation == "root":
        config = ModelTrainingConfig(Path.cwd() / "tmp")
    elif mutation == "family":
        family = "unknown"
    else:
        ablation = "unknown"
    with pytest.raises(ValueError, match="Unknown legacy"):
        LegacyTrainingLoader.legacy_result(config, family=family, ablation=ablation)


def test_training_candidate_without_evaluable_windows_stays_non_evaluable() -> None:
    from sat_dengue.model_training.workflow import equal_window_means

    windows = [f"{year}-12_t1" for year in (2018, 2020, 2022, 2023)]
    metrics = pd.DataFrame(
        {
            "horizon": 1,
            "reference": "gam",
            "metric": "average_precision",
            "window_id": windows,
            "value": [None] * 4,
        }
    )
    result = equal_window_means(metrics, windows).iloc[0]
    assert result.windows == 0 and pd.isna(result.value) and not result.evaluable
