"""Replay all saved development probabilities without fitting or selecting decisions."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.final_evaluation.parity import assert_table_parity
from sat_dengue.model_assessment.policy import require_development
from sat_dengue.model_training.candidate_families import restore_model

from .availability import preflight_window
from .calibration import _apply_saved_calibrator


def replay_development(development: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    """Verify every retained HP/internal/outer inference row and calibration representation."""
    tables = development["tables"]
    internals = {}
    model_count = 0
    row_count = 0
    calibrators = {(c["candidate"], c["window_id"]): c for c in development["calibrators"]}
    for label, saved in development["internals"].items():
        family, window = label.split("_", 1)
        d = development["windows"][window]
        target = d.target_column
        calendar = contract["window_role_calendar"][window]
        planned = preflight_window(d, calendar, contract["support_requirements"])
        meta = development["metadata"][label]
        if meta["components"] != planned["components"]:
            raise ValueError("Saved development temporal provenance changed")
        require_development(saved[target])
        current = saved.copy()
        for name, rows in saved.groupby("model_artifact", sort=False):
            record = next(x for x in meta["models"] if x["model_artifact"] == name)
            if str(record["training_target_max"]) > str(rows.year_month.min()):
                raise ValueError("Development labels unavailable at consuming origin")
            lookup = d.train_index.reset_index().set_index("feature_row")["index"]
            positions = lookup.reindex(rows.feature_row)
            if positions.isna().any():
                raise ValueError("Missing development prediction cohort")
            model = restore_model(
                family,
                development["models"][name],
                development["preparers"][record["preparer_artifact"]],
            )
            if model.preparer["fit_X_fingerprint"] != record["training_X"]:
                raise ValueError("Saved development preparer provenance changed")
            values = model.predict(d.train_X.loc[positions.to_numpy()])
            np.testing.assert_array_equal(
                values.to_numpy(dtype=float), rows.prediction_probability.to_numpy(dtype=float)
            )
            restored = restore_model(family, model.model_bytes(), model.preparer)
            np.testing.assert_array_equal(
                values.to_numpy(dtype=float),
                restored.predict(d.train_X.loc[positions.to_numpy()]).to_numpy(dtype=float),
            )
            current.loc[rows.index, "prediction_probability"] = values.to_numpy(dtype=float)
            model_count += 1
            row_count += len(rows)
        assert_table_parity(saved, current, exact_floats=True)
        internals[label] = current
    # Selected-development rows link to the full internal model replay above.
    saved = tables["development_predictions.csv"]
    current = saved.copy()
    for (family, window), rows in saved.groupby(["candidate", "window_id"], sort=False):
        internal = internals[f"{family}_{window}"]
        keys = ["municipality_code", "feature_row", "configuration_id"]
        joined = rows[keys].merge(
            internal[keys + ["prediction_probability"]], on=keys, how="left", validate="one_to_one"
        )
        if joined.prediction_probability.isna().any():
            raise ValueError("Missing selected development predictions")
        raw = pd.Series(joined.prediction_probability.to_numpy(), index=rows.index, dtype="Float64")
        sigmoid = _apply_saved_calibrator(raw, calibrators[family, window])
        current.loc[rows.index, "probability_raw"] = raw.to_numpy(dtype=float)
        current.loc[rows.index, "probability_sigmoid"] = sigmoid.to_numpy(dtype=float)
    assert_table_parity(saved, current, exact_floats=True, stage5_probabilities=True)
    posterior = tables["posterior_predictions.csv"].copy()
    for (family, window), rows in posterior.groupby(["candidate", "window_id"], sort=False):
        d = development["windows"][window]
        prefix = f"{family}_{window}_outer"
        model = restore_model(
            family,
            development["models"][prefix + "_model.json"],
            development["preparers"][prefix + "_preparer.json"],
        )
        keys = d.validation_index.reset_index(drop=True)
        expected = pd.DataFrame(
            {
                "municipality_code": keys.municipality_code,
                "origin_period": keys.year_month,
                "target_period": keys[d.target_column],
                "feature_row": keys.feature_row,
            }
        )
        assert_table_parity(
            expected, rows[list(expected)].reset_index(drop=True), exact_floats=True
        )
        raw = model.predict(d.validation_X).reset_index(drop=True).astype("Float64")
        c = calibrators[family, window]
        sigmoid = _apply_saved_calibrator(raw, c)
        selected = raw if c["calibration_choice"] == "original" else sigmoid
        threshold_rows = tables["threshold_selection.csv"]
        choice = threshold_rows[
            threshold_rows.candidate.eq(family) & threshold_rows.window_id.eq(window)
        ]
        if len(choice) != 1 or str(choice.calibration_choice.iloc[0]) != str(
            c["calibration_choice"]
        ):
            raise ValueError("Retained calibration/threshold decision changed")
        threshold = float(choice.selected_threshold.iloc[0])
        for col, values in [
            ("probability_raw", raw),
            ("probability_sigmoid", sigmoid),
            ("probability_selected", selected),
            ("prediction_label", selected.ge(threshold).astype("Int64")),
        ]:
            posterior.loc[rows.index, col] = values.to_numpy()
        if not rows.selected_threshold.eq(threshold).all():
            raise ValueError("Retained threshold changed")
        model_count += 1
        row_count += len(rows)
    assert_table_parity(
        tables["posterior_predictions.csv"], posterior, exact_floats=True, stage5_probabilities=True
    )
    return {
        "tables": {"development_predictions.csv": current, "posterior_predictions.csv": posterior},
        "models_replayed": model_count,
        "prediction_rows_replayed": row_count,
        "internal_prediction_rows": sum(map(len, internals.values())),
    }
