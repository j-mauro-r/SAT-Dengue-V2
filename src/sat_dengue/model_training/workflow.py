"""Separate deterministic synthetic fitting from frozen component inference."""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.configuration import canonical_bytes, resolve_configuration
from sat_dengue.metrics import evaluate_metrics
from sat_dengue.training_preparation.features import DERIVED_COLUMNS
from sat_dengue.training_preparation.serialization import bytes_record, json_bytes, serialize_table

from .candidate_families import restore_model
from .candidate_preparation import _project
from .candidate_selection import select_and_fit
from .contract import ModelTrainingError
from .loading import WindowDataset
from .reference_workflow import (
    _build_window_outputs as _build_window_outputs,
)
from .reference_workflow import (
    _enforce_window_rules as _enforce_window_rules,
)
from .reference_workflow import (
    _window_base as _window_base,
)
from .reference_workflow import (
    diagnostic_scores as diagnostic_scores,
)
from .reference_workflow import (
    probability_frame as probability_frame,
)
from .references import persistence_reference

CONTRACT_SEMANTIC_SHA = "31a20af5c2130f7a2e43116f6a0a9b4e10bd0e150c08b9d3c848a48c9cc3b196"
FAMILIES = ("xgboost", "lightgbm", "gam")


def training_contract(resolved: dict[str, Any], mode: str) -> dict[str, Any]:
    body = {k: v for k, v in resolved.items() if k != "configuration_sha256"}
    contract = resolved["authorities"]["model_engineering_contract_v1"]["document"]
    if (
        hashlib.sha256(canonical_bytes(body)).hexdigest() != resolved["configuration_sha256"]
        or hashlib.sha256(canonical_bytes(contract)).hexdigest() != CONTRACT_SEMANTIC_SHA
        or resolved["operational"]["profile"] != "training_" + mode
        or resolved["operational"]["tracking"] not in ("disabled", "enabled")
    ):
        raise ModelTrainingError("Unapproved training configuration/profile or scientific identity")
    return contract


def resolve_replay_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any], sources: dict[str, Any]
) -> dict[str, Any]:
    result = resolve_configuration(inputs, parameters)
    result["training"] = {"source_provenance": sources["provenance"], "mode": "replay"}
    body = {k: v for k, v in result.items() if k != "configuration_sha256"}
    result["configuration_sha256"] = hashlib.sha256(canonical_bytes(body)).hexdigest()
    training_contract(result, "replay")
    return result


def resolve_synthetic_configuration(
    inputs: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    result = resolve_configuration(inputs, parameters)
    training_contract(result, "synthetic")
    return result


def synthetic_cases(resolved: dict[str, Any]) -> dict[str, Any]:
    """Generate the complete fixture internally; no external data or path is accepted."""
    training_contract(resolved, "synthetic")
    prep = resolved["authorities"]["training_preparation_contract_v1"]["document"]
    columns = ["municipality_code", *prep["roles"]["predictors"], *DERIVED_COLUMNS]

    def part(start: str, end: str) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
        keys = pd.MultiIndex.from_product(
            [["50001", "73001"], pd.period_range(start, end, freq="M").astype(str)],
            names=["municipality_code", "year_month"],
        ).to_frame(index=False)
        periods = pd.PeriodIndex(keys.year_month, freq="M")
        X = pd.DataFrame(
            {
                n: np.sin(np.arange(len(keys)) / (i + 2)) + periods.month
                for i, n in enumerate(columns)
            }
        )
        X["municipality_code"] = keys.municipality_code.astype("string")
        X["zona_canal_t"] = pd.Series(
            np.where(periods.month % 2, "EXCESO", "SEGURIDAD"), dtype="string"
        )
        X["zona_canal_lag_1"] = "ALERTA"
        keys["target_period_t1"] = (periods + 1).astype(str)
        y = pd.Series((periods.month % 3 == 0).astype(int), dtype="Int64")
        return X[columns], y, keys

    X, y, keys = part("2012-01", "2018-11")
    validation, labels, index = part("2018-12", "2019-05")
    return {
        "train_X": X,
        "train_y": y,
        "train_keys": keys,
        "validation_X": validation,
        "validation_y": labels,
        "validation_keys": index,
        "fixture": "training-synthetic-v1",
    }


def fit_synthetic(cases: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    """Fit only the internally generated deterministic fixture using approved parameters."""
    contract = training_contract(resolved, "synthetic")
    expected = synthetic_cases(resolved)
    if set(cases) != set(expected):
        raise ModelTrainingError("Only the internal synthetic fixture may be fitted")
    for name, value in expected.items():
        if isinstance(value, (pd.DataFrame, pd.Series)):
            if not value.equals(cases[name]):
                raise ModelTrainingError("Foreign/changed synthetic training input")
        elif value != cases[name]:
            raise ModelTrainingError("Unknown synthetic profile")
    result: dict[str, Any] = {
        "tables": {},
        "payloads": {},
        "mode": "synthetic",
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "synthetic_model_fits": 0,
    }
    for family in FAMILIES:
        settings = contract[family + "_candidate"]
        selection = select_and_fit(
            cases["train_X"],
            cases["train_y"],
            cases["train_keys"],
            cutoff="2018-12",
            horizon=1,
            settings=settings,
            policy=contract["selection_policy"],
            family=family,
        )
        fitted = selection.fitted
        result["payloads"][family + "_search.json"] = json_bytes(selection.evidence)
        native = fitted.model_bytes()
        restored = restore_model(family, native, fitted.preparer)
        prediction = fitted.predict(cases["validation_X"])
        np.testing.assert_array_equal(prediction, restored.predict(cases["validation_X"]))
        result["payloads"][family + "_model.json"] = native
        result["payloads"][family + "_preparer.json"] = json_bytes(fitted.preparer)
        result["tables"][family + "_predictions.csv"] = cases["validation_keys"].assign(
            prediction_probability=prediction, y=cases["validation_y"]
        )
        result["synthetic_model_fits"] += selection.evidence["fit_count"]
    return result


def validate_window(dataset: WindowDataset, columns: list[str]) -> None:
    for split in ("train", "validation"):
        X, y, keys = (getattr(dataset, split + "_" + role) for role in ("X", "y", "index"))
        if (
            list(X) != columns
            or not X.index.equals(y.index)
            or not X.index.equals(keys.index)
            or len(X) != len(keys)
            or len(X) != len(y)
            or keys.duplicated(["municipality_code", "year_month"]).any()
            or not X.municipality_code.astype(str).equals(keys.municipality_code.astype(str))
        ):
            raise ModelTrainingError("Predictor schema or X/Y/key alignment mismatch")
        targets = keys[dataset.target_column]
        expected = (pd.PeriodIndex(keys.year_month, freq="M") + dataset.horizon).astype(str)
        consumer = (
            dataset.cutoff
            if split == "train"
            else str(pd.Period(dataset.cutoff, freq="M") + 6 - dataset.horizon)
        )
        label_cutoff = (
            dataset.cutoff if split == "train" else str(pd.Period(dataset.cutoff, freq="M") + 6)
        )
        if (
            (keys.year_month > consumer).any()
            or (targets > label_cutoff).any()
            or (targets >= "2025-01").any()
            or list(targets.astype(str)) != list(expected)
            or (split == "validation" and (keys.year_month < dataset.cutoff).any())
        ):
            raise ModelTrainingError("Future origin/label or reserved training boundary")


def equal_window_means(metrics: pd.DataFrame, windows: list[str]) -> pd.DataFrame:
    """Retain equal window weights and explicit non-evaluability for incomplete support."""
    rows = []
    for (h, reference, metric), frame in metrics.groupby(
        ["horizon", "reference", "metric"], dropna=False
    ):
        expected = {w for w in windows if w.endswith(f"_t{h}")}
        if frame.window_id.duplicated().any() or set(frame.window_id) != expected:
            rows.append(
                dict(
                    horizon=h,
                    reference=reference,
                    metric=metric,
                    value=None,
                    windows=int(frame.value.notna().sum()),
                    evaluable=False,
                )
            )
            continue
        value = frame["value"].mean() if frame["value"].notna().all() else None
        rows.append(
            dict(
                horizon=h,
                reference=reference,
                metric=metric,
                value=value,
                windows=int(frame.value.notna().sum()),
                evaluable=value is not None,
            )
        )
    return pd.DataFrame(rows)


def replay_components(sources: dict[str, Any], resolved: dict[str, Any]) -> dict[str, Any]:
    """Inference-only graph: no fitting/search/threshold/calibration entrypoint is called."""
    contract = training_contract(resolved, "replay")
    prep = resolved["authorities"]["training_preparation_contract_v1"]["document"]
    columns = ["municipality_code", *prep["roles"]["predictors"], *DERIVED_COLUMNS]
    if set(sources["development"]) != set(contract["windows"]):
        raise ModelTrainingError("Missing or unknown eligible cohort")
    predictions: list[pd.DataFrame] = []
    metric_rows: list[dict[str, Any]] = []
    reference_predictions: list[pd.DataFrame] = []
    reference_metrics: list[dict[str, Any]] = []
    expected_experiments = {
        "xgboost",
        "lightgbm",
        "gam",
        "xgboost_without_climate",
        "xgboost_without_zones",
    }
    if set(sources["components"]) != expected_experiments:
        raise ModelTrainingError("Unknown/missing family or selected experiment")
    for window in contract["windows"]:
        case = sources["development"][window]
        dataset, context = case["dataset"], case["context"]
        validate_window(dataset, columns)
        refs, scored, _ = _build_window_outputs(dataset, contract["references"], context)
        reference_predictions.append(refs)
        reference_metrics.extend(scored)
        for experiment, entry in sources["components"].items():
            saved = entry["windows"][window]
            state = saved["preparer"]
            removed = (
                contract["ablations"].get(experiment.removeprefix("xgboost_"), [])
                if experiment.startswith("xgboost_")
                else []
            )
            if state["fit_X_fingerprint"] != bytes_record(
                serialize_table(_project(dataset.train_X, removed))
            ):
                raise ModelTrainingError("Saved preparer training cohort identity changed")
            fitted = restore_model(entry["family"], saved["model"], state)
            probability = fitted.predict(dataset.validation_X)
            roundtrip = restore_model(entry["family"], fitted.model_bytes(), state)
            np.testing.assert_array_equal(probability, roundtrip.predict(dataset.validation_X))
            frame = probability_frame(probability, experiment)
            predicted = pd.concat([_window_base(dataset), frame], axis=1)
            original = (
                entry["predictions"]
                .loc[entry["predictions"].window_id.eq(window)]
                .reset_index(drop=True)
            )
            for key in ("municipality_code", "origin_period", "target_period", "feature_row"):
                if predicted[key].astype(str).tolist() != original[key].astype(str).tolist():
                    raise ModelTrainingError("Saved prediction cohort identity/alignment mismatch")
            np.testing.assert_array_equal(
                probability.to_numpy(), original.prediction_probability.to_numpy()
            )
            predictions.append(predicted)
            scored = evaluate_metrics(
                experiment,
                dataset.validation_y[dataset.y_column],
                frame,
                dataset.validation_index,
                target_column=dataset.target_column,
                threshold_policy_declared=False,
                event_context=context,
            )
            metric_rows.extend(
                dict(r, window_id=window, cutoff=dataset.cutoff, horizon=dataset.horizon)
                for r in scored
            )
    tables = {
        "development_predictions.csv": pd.concat(predictions, ignore_index=True),
        "development_metrics.csv": pd.DataFrame(metric_rows),
        "reference_predictions.csv": pd.concat(reference_predictions, ignore_index=True)
        .sort_values(["window_id", "reference", "municipality_code", "target_period"])
        .reset_index(drop=True),
        "reference_metrics.csv": pd.DataFrame(reference_metrics)
        .sort_values(["window_id", "reference", "metric"])
        .reset_index(drop=True),
    }
    means_input = pd.concat(
        [tables["reference_metrics.csv"], tables["development_metrics.csv"]], ignore_index=True
    )
    tables["horizon_means.csv"] = equal_window_means(means_input, contract["windows"])
    raw, persistence = [], []
    for h, case in sources["frozen"]["cohorts"].items():
        X, keys = case["X"], case["keys"]
        if list(X) != columns or len(X) != len(keys) or not X.index.equals(keys.index):
            raise ModelTrainingError("Frozen replay X/key schema mismatch")
        if not X.municipality_code.astype(str).equals(keys.municipality_code.astype(str)):
            raise ModelTrainingError("Frozen replay municipality alignment mismatch")
        p = persistence_reference(X, horizon=h)
        persistence.append(pd.concat([keys, p.drop(columns=["horizon"]).assign(horizon=h)], axis=1))
        for family in FAMILIES:
            component = sources["frozen"]["components"][f"{family}_t{h}"]
            fitted = restore_model(family, component["model"], component["preparer"])
            probability = fitted.predict(X)
            saved = sources["frozen"]["predictions"]
            saved = saved.loc[saved.candidate.eq(family) & saved.horizon.eq(h)].reset_index(
                drop=True
            )
            np.testing.assert_array_equal(
                probability.to_numpy(), saved.probability_raw.to_numpy(dtype=float)
            )
            for key in ("municipality_code", "year_month", "target_period"):
                if keys[key].astype(str).tolist() != saved[key].astype(str).tolist():
                    raise ModelTrainingError("Frozen prediction key mismatch")
            raw.append(keys.assign(candidate=family, horizon=h, probability_raw=probability))
    tables["frozen_raw_predictions.csv"] = pd.concat(raw, ignore_index=True)
    tables["frozen_persistence.csv"] = pd.concat(persistence, ignore_index=True)
    return {
        "tables": tables,
        "payloads": {},
        "mode": "replay",
        "real_model_fits": 0,
        "real_preparer_refits": 0,
        "synthetic_model_fits": 0,
        "components_replayed": 46,
    }
