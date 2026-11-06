"""Generated role/calibration/policy tests, distinct from real scientific execution."""

import copy
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data.exp_delta03_retrospective import row_hash, values_hash
from sat_dengue.experiments.exp_delta03_contract import digest
from sat_dengue.experiments.exp_delta03_learning import (
    apply_policy,
    calibrate,
    calibrated,
    select_policy,
    validate_parts,
)


def parts_fixture():
    parts, role_ids = {}, {}
    for role, year in [
        ("train", 2016),
        ("calibration", 2017),
        ("selection", 2019),
        ("evaluation", 2020),
    ]:
        rows = pd.DataFrame(
            {
                "divipola_municipio": ["50001", "73001"] * 4,
                "divipola_departamento": ["50", "73"] * 4,
                "periodo_mes": [f"{year}-0{m}" for m in range(1, 9)],
                "truth": [0, 1] * 4,
            }
        )
        rows["target_month"] = (pd.PeriodIndex(rows.periodo_mes, freq="M") + 1).astype(str)
        x = pd.DataFrame({"signal": np.arange(8, dtype=float)})
        parts[role] = {"rows": rows, "X": x}
        role_ids[role] = {
            "key_sha256": row_hash(rows, ["divipola_municipio", "periodo_mes"]),
            "key_label_sha256": row_hash(rows, ["divipola_municipio", "periodo_mes", "truth"]),
            "X_sha256": values_hash(x),
        }
    return {
        "year": 2020,
        "horizon": 1,
        "reference": "primary",
        "columns": ["signal"],
        "roles": role_ids,
    }, parts


def test_exact_role_membership_and_mutation_guards():
    cell, parts = parts_fixture()
    validate_parts(cell, parts, 1)
    for mutation in ["future", "overlap", "truth", "columns", "territory"]:
        altered = copy.deepcopy(parts)
        if mutation == "future":
            altered["evaluation"]["rows"]["periodo_mes"] = "2025-01"
        if mutation == "overlap":
            altered["selection"] = altered["calibration"]
        if mutation == "truth":
            altered["evaluation"]["rows"]["truth"] = 1
        if mutation == "columns":
            altered["train"]["X"].columns = ["year"]
        if mutation == "territory":
            altered["calibration"]["rows"]["divipola_departamento"] = "05"
        with pytest.raises(ValueError):
            validate_parts(cell, altered, 1)
    cell["reference"] = "transfer"
    with pytest.raises(ValueError, match="held-out"):
        validate_parts(cell, parts, 1)


def test_scalar_calibration_has_separate_role_identity_and_support():
    scores = np.array([0.05, 0.1, 0.2, 0.3, 0.4, 0.5])
    truth = [0, 1, 0, 1, 0, 1]
    spec = {"method": "regularized_intercept", "penalty": 1, "minimum_per_class": 1}
    c = calibrate(
        scores,
        truth,
        role="calibration",
        model_sha256="model",
        cohort_sha256="cohort",
        specification=spec,
    )
    assert c["base_model_changed"] is False
    np.testing.assert_array_equal(
        calibrated(scores, c, model_sha256="model"),
        calibrated(scores, copy.deepcopy(c), model_sha256="model"),
    )
    with pytest.raises(ValueError, match="role"):
        calibrate(
            scores,
            truth,
            role="evaluation",
            model_sha256="model",
            cohort_sha256="cohort",
            specification=spec,
        )
    with pytest.raises(ValueError, match="support"):
        calibrate(
            scores,
            [0] * 6,
            role="calibration",
            model_sha256="model",
            cohort_sha256="cohort",
            specification=spec,
        )
    with pytest.raises(ValueError, match="identity"):
        calibrated(scores, c, model_sha256="another")


def test_whole_ties_budget_rounding_no_alert_and_zero_support():
    kwargs: dict[str, Any] = {
        "role": "selection",
        "cohort_sha256": "keys",
        "calibrator_sha256": "cal",
        "specification": {"B": 1},
    }
    policy = select_policy([0.8, 0.8, 0.2], [1, 0, 0], **kwargs)
    assert policy["false_alert_limit"] == 0 and policy["status"] == "NO_ALERT"
    assert not apply_policy([0.9, 0.8, 0.1], policy, calibrator_sha256="cal").any()
    unsupported = select_policy([0.1, 0.2], [0, 0], **kwargs)
    assert unsupported["status"].startswith("NO_EVALUABLE")
    with pytest.raises(ValueError, match="not evaluable"):
        apply_policy([0.1, 0.2], unsupported, calibrator_sha256="cal")
    with pytest.raises(ValueError, match="role"):
        select_policy([0.5], [1], **{**kwargs, "role": "evaluation"})
    p = select_policy([0.9, 0.9, 0.3, 0.1], [1, 1, 0, 0], **kwargs)
    assert p["detected"] == 2 and p["threshold"] == 0.9
    before = digest(p)
    evaluation = np.array([0, 1, 1, 1])
    evaluation[:] = 1 - evaluation
    assert digest(p) == before
