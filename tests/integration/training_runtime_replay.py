"""Current domain adapters in each frozen runtime: all 46 models, no fits or writes."""

from __future__ import annotations

import importlib.metadata
import json
import os
import sys
from pathlib import Path
from types import FrameType
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from migration_support import fingerprint

from sat_dengue.model_training.candidate_families import restore_model


def deny_fitting(frame: FrameType, event: str, arg: Any) -> None:
    name = frame.f_code.co_name
    if event == "call" and (
        name.startswith(("fit", "_fit"))
        or name in {"train", "select_and_fit", "select_threshold", "_select_threshold"}
    ):
        raise AssertionError("Forbidden fitting/search in current adapter replay: " + name)


def deny_writes(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and isinstance(args[0], (str, bytes)):
        flags = args[2]
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            raise AssertionError("Runtime replay must not write")


def main() -> None:
    root, descriptor_path, version = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    assert importlib.metadata.version("lightgbm") == version
    descriptor = json.loads(descriptor_path.read_text())
    for relative, expected in descriptor["files"].items():
        assert fingerprint(root / relative) == expected, relative
    sys.setprofile(deny_fitting)
    sys.addaudithook(deny_writes)
    counts = {"development": 0, "frozen": 0}
    for case in descriptor["cases"]:
        X = pd.read_csv(root / case["X"], float_precision="round_trip")
        original = pd.read_csv(root / case["predictions"], float_precision="round_trip")
        if case["kind"] == "development":
            original = original.loc[original.window_id.eq(case["window"])].reset_index(drop=True)
            column = "prediction_probability"
        else:
            original = original.loc[
                original.candidate.eq(case["family"]) & original.horizon.eq(case["horizon"])
            ].reset_index(drop=True)
            column = "probability_raw"
        state = json.loads((root / case["preparer"]).read_text())
        fitted = restore_model(case["family"], (root / case["model"]).read_bytes(), state)
        predicted = fitted.predict(X)
        np.testing.assert_array_equal(predicted.to_numpy(), original[column].to_numpy())
        restored = restore_model(case["family"], fitted.model_bytes(), state)
        np.testing.assert_array_equal(predicted.to_numpy(), restored.predict(X).to_numpy())
        counts[case["kind"]] += len(predicted)
    assert len(descriptor["cases"]) == 46 and counts == {"development": 16720, "frozen": 5472}
    print(
        json.dumps(
            {
                "status": "PASS",
                "version": version,
                "components": 46,
                "predictions": counts,
                "real_model_fits": 0,
                "real_preparer_refits": 0,
                "model_roundtrip_tolerance": 0,
                "probability_tolerance": 0,
                "source_descriptor": fingerprint(descriptor_path),
            }
        )
    )


if __name__ == "__main__":
    main()
