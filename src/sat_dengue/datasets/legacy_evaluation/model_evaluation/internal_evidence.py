"""Minimal earlier internal predictions with persisted models and inference-only replay."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from scripts.model_training.candidate_families import fit_model, restore_model, simplicity
from scripts.model_training.contract import read_json
from scripts.model_training.persistence import bytes_record, json_bytes, serialize_table

from .availability import ROLES, preflight_window
from .contract import ModelEvaluationError


def internal_evidence(
    *,
    dataset: Any,
    calendar: dict[str, Any],
    support: dict[str, int],
    candidate: str,
    settings: dict[str, Any],
    policy: dict[str, Any],
    selector: Callable[..., Any],
    payloads: dict[str, bytes] | None = None,
    bundle: Path | None = None,
) -> tuple[dict[str, Any], pd.DataFrame, str, dict[str, Any], pd.DataFrame]:
    """Fit missing evidence once or replay saved models without any fitting.

    Args:
        dataset: Verified train-only inputs and separate external keys.
        calendar: Frozen feasible role calendar.
        support: Existing minimum support policy.
        candidate: Unchanged family name.
        settings: Existing family grid, seed and thread count.
        policy: Approved Stage4 selection policy.
        selector: Shared pure scoring/selection function, also used for decision verification.
        payloads: New-run payload sink; absent for saved-bundle replay.
        bundle: Existing verified bundle; when supplied no fit operation is reachable.

    Returns:
        Search metadata, all configuration HP rows plus selected development rows,
        selected configuration, parameters and score trace.
    """
    target, ycol = dataset.target_column, dataset.y_column
    window = dataset.window_id
    prefix = f"{candidate}_{window}"
    planned = preflight_window(dataset, calendar, support)
    truth = dataset.train_index.copy()
    truth[ycol] = dataset.train_y[ycol]
    truth["zona_canal_t"] = dataset.train_X.zona_canal_t
    hp = truth[truth[target].isin(calendar["hyperparameter_selection_targets"])]
    dev = truth[truth[target].isin(sum([calendar[f"{role}_targets"] for role in ROLES[1:]], []))]
    meta_name = f"{prefix}_internal_components.json"
    data_name = f"{prefix}_internal_predictions.csv"
    saved = read_json(bundle / meta_name) if bundle else None
    model_records = []
    frames = []
    candidates = []

    def model_prediction(
        cid: str, params: dict[str, Any], cutoff: str, rows: pd.DataFrame, *, role: str
    ) -> tuple[Any, pd.DataFrame]:
        """Fit or restore one component and predict only after its training labels exist."""
        train = truth[truth[target] <= cutoff]
        tag = f"{prefix}_{role}_{cid}"
        model_file, prep_file = f"{tag}_model.json", f"{tag}_preparer.json"
        record: dict[str, Any] = dict(
            model_artifact=model_file,
            preparer_artifact=prep_file,
            configuration_id=cid,
            role=role,
            fit_cutoff=cutoff,
            training_target_max=str(train[target].max()),
            training_keys=bytes_record(serialize_table(dataset.train_index.loc[train.index])),
            training_X=bytes_record(serialize_table(dataset.train_X.loc[train.index])),
            training_y=bytes_record(serialize_table(dataset.train_y.loc[train.index])),
            training_rows=len(train),
        )
        if record["training_target_max"] > str(rows.year_month.min()):
            raise ModelEvaluationError(
                "Internal model/preparer uses labels after prediction origin"
            )
        if bundle is not None:
            assert saved is not None
            if record not in saved["models"]:
                raise ModelEvaluationError("Saved internal training provenance differs")
            fitted = restore_model(
                candidate, (bundle / model_file).read_bytes(), read_json(bundle / prep_file)
            )
            if fitted.preparer["fit_X_fingerprint"] != record["training_X"]:
                raise ModelEvaluationError(
                    "Internal preparer was not fitted on declared training rows"
                )
        else:
            assert payloads is not None
            fitted = fit_model(
                candidate,
                dataset.train_X.loc[train.index],
                dataset.train_y.loc[train.index, ycol],
                params,
                seed=settings["seed"],
                threads=settings["threads"],
            )
            payloads[model_file] = fitted.model_bytes()
            payloads[prep_file] = json_bytes(fitted.preparer)
        result = rows.copy()
        result["prediction_probability"] = fitted.predict(dataset.train_X.loc[rows.index])
        result["configuration_id"] = cid
        result["fold"] = 0 if role == "hp" else 1
        result["model_artifact"] = model_file
        result["preparer_artifact"] = prep_file
        result["model_available_month"] = record["training_target_max"]
        result["configuration_available_month"] = (
            record["training_target_max"]
            if role == "hp"
            else planned["components"]["configuration_target_end"]
        )
        model_records.append(record)
        return fitted, result

    for number, params in enumerate(settings["configurations"]):
        cid = f"{candidate}_{number:02d}"
        model, rows = model_prediction(
            cid, params, calendar["hyperparameter_model_fit_cutoff"], hp, role="hp"
        )
        rows["split_role"] = "hyperparameter_selection"
        frames.append(rows)
        candidates.append(
            dict(
                id=cid,
                parameters=params,
                simplicity=simplicity(candidate, dataset.train_X.shape[1], params, model.preparer),
            )
        )
    hp_rows = pd.concat(frames, ignore_index=True)
    search = dict(candidates=candidates)
    selected_id, params, trace = selector(
        candidate=candidate,
        search=search,
        hp_rows=hp_rows,
        y_column=ycol,
        target_column=target,
        stage4_policy=policy,
        train_feature_count=dataset.train_X.shape[1],
    )
    _, dev_rows = model_prediction(
        selected_id, params, calendar["internal_model_fit_cutoff"], dev, role="internal"
    )
    for role in ROLES[1:]:
        dev_rows.loc[dev_rows[target].isin(calendar[f"{role}_targets"]), "split_role"] = role
    frame = pd.concat([hp_rows, dev_rows], ignore_index=True)
    frame["window_id"], frame["cutoff"], frame["horizon"] = window, dataset.cutoff, dataset.horizon
    metadata = dict(
        models=model_records,
        components=planned["components"],
        support=planned["support"],
        selected_id=selected_id,
        selected_parameters=params,
        model_fit_count=len(model_records),
    )
    if bundle is not None:
        if metadata != saved:
            raise ModelEvaluationError("Saved internal component metadata or selection differs")
        observed = pd.read_csv(
            bundle / data_name, dtype={"municipality_code": "string"}, float_precision="round_trip"
        )
        for column in frame:
            if column == "prediction_probability":
                if not np.array_equal(
                    frame[column].to_numpy(dtype=float), observed[column].to_numpy(dtype=float)
                ):
                    raise ModelEvaluationError("Internal saved model probabilities differ")
            elif frame[column].astype(str).tolist() != observed[column].astype(str).tolist():
                raise ModelEvaluationError(f"Internal persisted rows differ: {column}")
    else:
        assert payloads is not None
        payloads[meta_name] = json_bytes(metadata)
        payloads[data_name] = serialize_table(frame)
    search["components"] = planned["components"]
    return search, frame, selected_id, params, trace
