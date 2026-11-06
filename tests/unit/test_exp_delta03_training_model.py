"""All estimator fits in this file use small generated fixtures."""

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.model_training.exp_delta03_adapter import fit_native, reload_native

ROOT = Path(__file__).resolve().parents[2]


def fixture():
    parameters = json.loads(
        (ROOT / "docs/product/experiments/EXP-DELTA03/training-contract.json").read_text()
    )["model"]
    x = pd.DataFrame(
        {"signal": np.tile([0.0, 1.0, 2.0, np.nan], 8), "other": np.arange(32, dtype=float)}
    )
    y = pd.Series(np.tile([0, 1, 1, 0], 8))
    return x, y, parameters


def test_native_serialization_reload_probabilities_and_repeat_identity():
    x, y, p = fixture()
    m = fit_native(x, y, p, cohort_sha256="a" * 64)
    restored = reload_native(m.serialize(), m.metadata)
    np.testing.assert_array_equal(m.predict(x), restored.predict(x))
    repeated = fit_native(x, y, p, cohort_sha256="a" * 64)
    assert repeated.serialize() == m.serialize()
    assert m.metadata["parameters"] == p and m.metadata["family"] == "xgboost"
    with pytest.raises(ValueError, match="column order"):
        m.predict(x[["other", "signal"]])
    with pytest.raises(ValueError, match="identity"):
        reload_native(m.serialize() + b"changed", m.metadata)
    altered = copy.deepcopy(m.metadata)
    altered["parameters"]["max_depth"] = 9
    with pytest.raises(ValueError, match="parameter identity"):
        reload_native(m.serialize(), altered)


def test_invalid_training_classes_alignment_null_columns_and_threads_rejected():
    x, y, p = fixture()
    with pytest.raises(ValueError, match="classes"):
        fit_native(x, y * 0, p, cohort_sha256="a" * 64)
    y.index = y.index + 1
    with pytest.raises(ValueError, match="Misaligned"):
        fit_native(x, y, p, cohort_sha256="a" * 64)
    y.index = x.index
    x["other"] = np.nan
    with pytest.raises(ValueError, match="All-null"):
        fit_native(x, y, p, cohort_sha256="a" * 64)
    x, y, p = fixture()
    p["n_jobs"] = 2
    with pytest.raises(ValueError, match="single-thread"):
        fit_native(x, y, p, cohort_sha256="a" * 64)
