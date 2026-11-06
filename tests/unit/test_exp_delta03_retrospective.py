"""Generated retrospective matrices; real fits and private source loading are absent."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data.exp_delta03 import KEYS
from sat_dengue.data.exp_delta03_retrospective import (
    prepare_retrospective,
    validate_materialized_tables,
    view_projection,
)
from sat_dengue.datasets import exp_delta03 as adapter

ROOT = Path(__file__).resolve().parents[2]


def retrospective_fixture() -> dict[str, Any]:
    from sat_dengue.experiments.exp_delta03_synthetic import generated_preparation

    contract = json.loads((ROOT / adapter.CONTRACT).read_text())
    ledger = json.loads((ROOT / contract["retrospective_source_ledger"]["path"]).read_text())
    return generated_preparation(contract, ledger)


def descriptor(prepared: dict, variant="FULL_COMMON", year=2020, horizon=1) -> dict:
    return next(
        v
        for v in prepared["views"]
        if v["variant"] == variant and v["year"] == year and v["horizon"] == horizon
    )


def test_authorized_retrospective_has_closed_features_and_exact_frozen_cohorts():
    result = prepare_retrospective(retrospective_fixture())
    assert len(result["feature_manifest"]) == 54
    assert len(descriptor(result)["columns"]) == 48
    assert "land_mosaic_unassigned" in descriptor(result)["columns"]
    assert "land_bare_other" not in result["base"]
    assert result["base"].dengue_notifications_count_lag1.max() < 999
    assert len(result["historical_parity"]["frozen_cells"]) == 40
    assert len(result["historical_parity"]["national_training_keys"]) == 8
    check = validate_materialized_tables(
        result["base"],
        result["labels"],
        result["memberships"],
        result["views"],
        result["feature_manifest"],
    )
    assert check["logical_views"] == 108 and check["unavailable_water_views"] == 4
    assert not check["operational_PIT"] and check["fits"] == 0


def test_unapproved_regime_and_lost_frozen_key_fail_closed():
    sources = retrospective_fixture()
    sources["retrospective_verification"]["verified"] = False
    with pytest.raises(ValueError, match="authorization"):
        prepare_retrospective(sources)
    sources["retrospective_verification"]["verified"] = True
    sources["frozen_cohorts"][0]["frame"] = sources["frozen_cohorts"][0]["frame"].iloc[:-1]
    with pytest.raises(ValueError, match="cohort parity"):
        prepare_retrospective(sources)


def test_future_prefix_and_target_training_values_cannot_change_transfer_reference():
    sources = retrospective_fixture()
    original = prepare_retrospective(sources)
    changed = copy.deepcopy(sources)
    changed["frame"].loc[changed["frame"].year.eq(2025), "ndvi_medio"] = -0.8
    future = prepare_retrospective(changed)
    pd.testing.assert_frame_equal(original["base"], future["base"])
    changed = copy.deepcopy(sources)
    frame = changed["frame"]
    frame.loc[
        frame.year.between(2012, 2015) & frame.divipola_departamento.isin(["50", "73"]),
        "ndvi_medio",
    ] = 0.9
    heldout = prepare_retrospective(changed)
    for result in [original, heldout]:
        x = descriptor(result, "TRANSFER_EXCLUDE_META_TOLIMA")
        assert x["roles"]["evaluation"]["rows"] > 0
    assert (
        descriptor(original, "TRANSFER_EXCLUDE_META_TOLIMA")["roles"]["evaluation"]["X_sha256"]
        == descriptor(heldout, "TRANSFER_EXCLUDE_META_TOLIMA")["roles"]["evaluation"]["X_sha256"]
    )
    assert (
        descriptor(original)["roles"]["evaluation"]["X_sha256"]
        != descriptor(heldout)["roles"]["evaluation"]["X_sha256"]
    )


def test_annual_source_window_and_genuine_lagged_water_are_honest():
    result = prepare_retrospective(retrospective_fixture())
    base = result["base"].set_index(KEYS)
    assert base.loc[("50001", "2015-07"), "poblacion_total__asof"] == np.log1p(1000 + 2014)
    water = "fraccion_agua_superficial_pct_area_observada__lag1"
    assert pd.notna(base.loc[("50001", "2022-01"), water])
    assert pd.isna(base.loc[("50001", "2022-02"), water])
    assert descriptor(result, "FULL_PLUS_SURFACE_WATER", 2024)["status"].startswith("UNAVAILABLE")
    assert (
        descriptor(result, "FULL_PLUS_SURFACE_WATER", 2022)["status"]
        == "MATERIALIZABLE_RETROSPECTIVE"
    )


def test_cross_fold_and_identifier_selectors_are_rejected():
    result = prepare_retrospective(retrospective_fixture())
    view = copy.deepcopy(descriptor(result))
    position = view["columns"].index("ndvi_anomaly")
    view["physical_columns"][position] = "ndvi_anomaly__h1_y2024_primary"
    with pytest.raises(ValueError, match="Cross-fold"):
        view_projection(result["base"], view, result["feature_manifest"])
    view = copy.deepcopy(descriptor(result))
    view["columns"][0] = "truth"
    with pytest.raises(ValueError, match="Forbidden"):
        view_projection(result["base"], view, result["feature_manifest"])

    view = copy.deepcopy(descriptor(result))
    view["columns"][position] = view["physical_columns"][position] = (
        "ndvi_anomaly__h1_y2024_primary"
    )
    with pytest.raises(ValueError, match="Forbidden"):
        view_projection(result["base"], view, result["feature_manifest"])
    view = copy.deepcopy(descriptor(result, "FULL_MINUS_NDVI"))
    view["columns"].append("ndvi_medio__lag1")
    view["physical_columns"].append("ndvi_medio__lag1")
    with pytest.raises(ValueError, match="variant contract"):
        view_projection(result["base"], view, result["feature_manifest"])

    view = copy.deepcopy(descriptor(result))
    view["variant"] = "FULL_MINUS_ENSO"
    with pytest.raises(ValueError, match="Undeclared ablation"):
        view_projection(result["base"], view, result["feature_manifest"])


def test_actual_csv_roundtrip_and_member_corruption(tmp_path, monkeypatch):
    sources = retrospective_fixture()
    payloads = adapter.retrospective_payloads(sources, {"generated": True})
    receipt = adapter.publish(tmp_path, "tmp/exp-delta03-phase1/products", payloads)
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    result = adapter.load_retrospective_publication(receipt["path"], receipt["manifest_sha256"])
    assert result["validation"]["status"] == "PASS"
    path = tmp_path / receipt["path"] / "prepared_features.csv"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="member changed"):
        adapter.load_retrospective_publication(receipt["path"], receipt["manifest_sha256"])
