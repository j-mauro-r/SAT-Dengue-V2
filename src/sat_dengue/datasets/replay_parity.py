"""Complete persisted real-stage comparisons; no sampling or new tolerances."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.datasets.stage2 import local_path
from sat_dengue.final_evaluation.parity import assert_table_parity


def read(folder: Path, name: str) -> Any:
    return pd.read_csv(folder / name, float_precision="round_trip")


def training_parity(record: dict[str, Any]) -> None:
    from .training_legacy import SUITE, LegacyTrainingLoader

    sources = LegacyTrainingLoader().load()
    folder = local_path(record["path"])
    predictions = read(folder, "development_predictions.csv")
    metrics = read(folder, "development_metrics.csv")
    for experiment, entry in sources["components"].items():
        assert_table_parity(
            entry["predictions"],
            predictions.loc[predictions.reference.eq(experiment)].reset_index(drop=True),
            exact_floats=True,
        )
        assert_table_parity(
            entry["metrics"], metrics.loc[metrics.reference.eq(experiment)].reset_index(drop=True)
        )
    for name in ("reference_predictions", "reference_metrics"):
        assert_table_parity(
            sources[name], read(folder, name + ".csv"), exact_floats=name.endswith("predictions")
        )
    means = read(local_path(SUITE), "horizon_means.csv")
    assert_table_parity(means, read(folder, "horizon_means.csv")[list(means)])
    frozen = sources["frozen"]["predictions"]
    persistence = read(folder, "frozen_persistence.csv")
    assert_table_parity(
        frozen.loc[frozen.candidate.eq("persistence"), list(persistence)].reset_index(drop=True),
        persistence,
        exact_floats=True,
    )
    raw = read(folder, "frozen_raw_predictions.csv")
    for family in ("xgboost", "lightgbm", "gam"):
        for h in (1, 2):
            actual = raw.loc[raw.candidate.eq(family) & raw.horizon.eq(h)].reset_index(drop=True)
            expected = frozen.loc[
                frozen.candidate.eq(family) & frozen.horizon.eq(h), list(actual)
            ].reset_index(drop=True)
            assert_table_parity(expected, actual, exact_floats=True)
    if len(raw) != 5472 or len(persistence) != 1824 or len(predictions) != 16720:
        raise ValueError("Incomplete training replay cohorts")


def evaluation_parity(record: dict[str, Any]) -> None:
    from sat_dengue.final_evaluation.identities import ASSESSMENT, STAGE5

    from .evaluation_legacy import FrozenEvaluationLoader

    folder = local_path(record["path"])
    sources = FrozenEvaluationLoader().load()
    for name, expected in sources["reference"].items():
        assert_table_parity(expected, read(folder, name), exact_floats=name == "predictions.csv")
    for origin, names in (
        (STAGE5, ["development_predictions.csv", "posterior_predictions.csv"]),
        (ASSESSMENT, list(sources["development"]["assessment"])),
    ):
        for name in names:
            assert_table_parity(
                read(local_path(origin), name),
                read(folder, "development_" + name),
                exact_floats=origin == STAGE5,
                stage5_probabilities=origin == STAGE5,
            )
    audit = json.loads((folder / "audit.json").read_text())
    if (
        len(audit["decisions"]) != 6
        or {r["result"] for r in audit["decisions"]} != {"does_not_meet"}
        or audit["G5"] != "NOT_APPROVED"
        or audit["champion"] != "not_selected"
    ):
        raise ValueError("Frozen scientific decision parity failed")
