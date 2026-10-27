"""La comparación predictiva cambia solo Y; ninguna prueba ajusta modelos reales."""

import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sat_dengue.experiments.exp01 import synthetic_fit
from sat_dengue.experiments.exp02_labels import construct_variants
from sat_dengue.experiments.exp02_prediction import common_partitions, evaluate_predictive


def inputs():
    protocol = json.loads(
        Path("docs/product/experiments/EXP02_label_stability/protocol.json").read_text()
    )
    contract = json.loads(
        Path("docs/product/stage-3/training_preparation_contract_v1.json").read_text()
    )
    design = copy.deepcopy(protocol["design"])
    design["families"] = {"gam": design["families"]["gam"]}
    design["windows"] = [design["windows"][-1]]
    rng = np.random.default_rng(42)
    rows = []
    for municipality in ["50001", "50002", "50003", "73001", "73002", "73003"]:
        for month in pd.period_range("2000-01", "2024-12", freq="M"):
            row = {"municipality_code": municipality, "year_month": str(month)}
            row.update(
                {
                    c: float(rng.integers(0, 30))
                    for c in contract["roles"]["predictors"]
                    if c != "zona_canal_t"
                }
            )
            rows.append(row)
    return pd.DataFrame(rows), contract, design


def test_common_predictors_independent_fits_and_fixed_vs_changed_truth():
    panel, contract, design = inputs()
    variants = construct_variants(panel)
    calls = []

    def fit(family, X, y, parameters, seed):
        calls.append((X.copy(), y.copy()))
        return synthetic_fit(family, X, y, parameters, seed)

    result = evaluate_predictive(
        panel,
        contract,
        variants,
        design,
        fit=fit,
        calibrate=lambda p, y, s: lambda v: v,
        synthetic=True,
    )
    assert result["synthetic_interface_fits"] == 6
    assert result["real_model_fits"] == result["calibrator_fits"] == 0
    for start in [0, 3]:
        for i in [1, 2]:
            pd.testing.assert_frame_equal(calls[start][0], calls[start + i][0])
        assert not calls[start][1].equals(calls[start + 2][1])
    for horizon in [1, 2]:
        cells = [c for c in result["children"] if c["horizon"] == horizon]
        assert len({c["cohort_sha256"] for c in cells}) == 1
        assert all(c["status"] == "evaluable" for c in cells)
        for index in range(len(cells[0]["frontier"])):
            assert len({c["frontier"][index]["fixed_anchor"]["real_onsets"] for c in cells}) == 1
        assert all(c["frontier"][0]["paired_interval"]["interval"] is None for c in cells)
    assert result["predictions"]
    assert any(
        c["own_definition"]["brier"] != c["fixed_anchor"]["brier"]
        for c in result["children"]
        if c["history_years"] != 5
    )


def test_unsupported_roles_preserve_cells_without_any_fit():
    panel, contract, design = inputs()
    panel["dengue_notifications_count"] = 0

    def forbidden(*args, **kwargs):
        raise AssertionError("No debe invocarse un ajuste")

    result = evaluate_predictive(
        panel,
        contract,
        construct_variants(panel),
        design,
        fit=forbidden,
        calibrate=forbidden,
        synthetic=True,
    )
    assert len(result["children"]) == 6
    assert all(c["status"] == "not_evaluable" for c in result["children"])
    assert result["synthetic_interface_fits"] == 0


def test_target_calendar_keeps_late_2024_and_excludes_2025():
    panel, contract, design = inputs()
    variants = construct_variants(panel)
    for horizon in [1, 2]:
        parts, coverage = common_partitions(
            panel, contract, variants, design, horizon, design["windows"][0]
        )
        assert parts["evaluation"].target_month.max() == "2024-12"
        assert {"2024-11", "2024-12"} <= set(parts["evaluation"].target_month)
        assert all(frame.target_month.lt("2025-01").all() for frame in parts.values())
        assert all(
            frame.target_month.lt("2024-01").all()
            for role, frame in parts.items()
            if role != "evaluation"
        )
        if horizon == 2:
            assert coverage["evaluation"]["embargo_excluded_rows"] == 6
