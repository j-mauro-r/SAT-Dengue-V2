"""Generated retrospective matrices; real fits and private source loading are absent."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data.exp_delta03 import KEYS, h5_labels, normalize, temporal_roles
from sat_dengue.data.exp_delta03_retrospective import (
    prepare_retrospective,
    validate_materialized_tables,
    view_projection,
)
from sat_dengue.datasets import exp_delta03 as adapter

ROOT = Path(__file__).resolve().parents[2]


def retrospective_fixture() -> dict[str, Any]:
    contract = json.loads((ROOT / adapter.CONTRACT).read_text())
    rows = []
    for code in ["05001", "50001", "73001"]:
        for period in pd.period_range("2007-01", "2025-12", freq="M"):
            row: dict[str, Any] = {c: 0.5 for c in contract["ordered_columns"]}
            row.update(
                divipola_municipio=code,
                divipola_departamento=code[:2],
                periodo_mes=str(period) + "-01",
                anio=period.year,
                mes=period.month,
                notificados_210=999,
                notificados_220=999,
                ndvi_disponible=True,
                ndvi_medio=0.4 + (period.year - 2007) / 1000,
                ndvi_desviacion=0.01,
                altitud_media_m=100,
                pendiente_media_grados=3,
                poblacion_total=1000 + period.year,
                densidad_poblacional_hab_km2=10,
                porcentaje_urbanizacion=50,
                porcentaje_0_4=5,
                porcentaje_65_mas=10,
                fraccion_agua_superficial_pct_area_observada=0.1 if period.year <= 2021 else np.nan,
                area_observada_m2=100 if period.year <= 2021 else np.nan,
            )
            for name in contract["blocks"]["LAND_COVER"]["sources"]:
                row[name] = 10.0 if period.year <= 2024 else np.nan
            rows.append(row)
    source = normalize(pd.DataFrame(rows, columns=contract["ordered_columns"]))
    history_rows = []
    for code in ["05001", "50001", "73001"]:
        for period in pd.period_range("2006-06", "2024-12", freq="M"):
            count = period.year - 2000 if period.month == 11 else 1
            history_rows.append(
                {
                    "municipality_code": code,
                    "year_month": str(period),
                    "dengue_notifications_count": count,
                    "dengue_grave_notifications_count": 1,
                    "total_notifications_count": count + 1,
                }
            )
    full = pd.DataFrame(history_rows)
    regional = full.loc[full.municipality_code.str.startswith(("50", "73"))].copy()
    native = full.loc[full.year_month.ge("2011-06")].copy()
    union = pd.concat([regional.loc[regional.year_month.lt("2011-06")], native])
    union = union.rename(columns={"municipality_code": KEYS[0], "year_month": KEYS[1]})
    union = union.sort_values(KEYS).reset_index(drop=True)
    union["divipola_departamento"] = union.divipola_municipio.str[:2]
    states = h5_labels(union, union.dengue_notifications_count)
    native = native.merge(
        states.rename(
            columns={KEYS[0]: "municipality_code", KEYS[1]: "year_month", "p75": "p75_canal_t"}
        ),
        on=["municipality_code", "year_month"],
        validate="one_to_one",
    )
    for h in [1, 2]:
        native[f"g1_no_climate_t{h}"] = native[f"eligible_T{h}"]
    base = source.loc[source.periodo_mes.between("2011-06", "2024-12")].reset_index(drop=True)
    aligned = base[KEYS].merge(
        native.rename(columns={"municipality_code": KEYS[0], "year_month": KEYS[1]}),
        on=KEYS,
        validate="one_to_one",
    )
    frozen, training = [], []
    for h in [1, 2]:
        for year in [2020, 2021, 2022, 2024]:
            roles = temporal_roles(base, year, h)
            eligible = aligned[f"eligible_T{h}"]
            regional_mask = base.divipola_departamento.isin(["50", "73"])
            audit: dict[str, Any] = {}
            for role in ["train", "calibration", "embargo", "selection", "evaluation"]:
                mask = eligible & roles.eq(role) & regional_mask
                audit["adaptation" if role == "embargo" else role] = {"rows": int(mask.sum())}
            train = base.loc[eligible & roles.eq("train"), KEYS].rename(
                columns={KEYS[0]: "municipality_code", KEYS[1]: "year_month"}
            )
            audit["train_keys_sha256"] = hashlib.sha256(
                train.to_csv(
                    index=False, na_rep="", lineterminator="\n", float_format="%.17g"
                ).encode()
            ).hexdigest()
            training.append(
                {
                    "horizon": h,
                    "year": year,
                    "audit": {
                        "train_keys_sha256": audit.pop("train_keys_sha256"),
                        "regional_role_audit": audit,
                    },
                }
            )
            for control, role in [
                ("G0", "selection"),
                ("G0", "evaluation"),
                ("G1", "calibration"),
                ("G1", "selection"),
                ("G1", "evaluation"),
            ]:
                mask = eligible & roles.eq(role) & regional_mask
                frame = base.loc[mask, KEYS].rename(
                    columns={KEYS[0]: "municipality_code", KEYS[1]: "year_month"}
                )
                frame["truth"] = aligned.loc[mask, f"onset_T{h}"].to_numpy()
                frozen.append(
                    {"horizon": h, "year": year, "role": role, "control": control, "frame": frame}
                )
    dictionary = [
        {
            "nombre_variable": name,
            "fuente_producto": "generated",
            "tipo_dato": "decimal",
            "unidad": "generated",
            "cobertura_temporal": "generated",
        }
        for name in contract["ordered_columns"]
    ]
    return {
        "contract": contract,
        "frame": source,
        "baseline": regional,
        "historical_panel": native,
        "frozen_cohorts": frozen,
        "training_controls": training,
        "dictionary": dictionary,
        "receipt": {"sha256": "generated_only", "rows": len(source)},
        "vintage_ledger": json.loads(
            (ROOT / contract["retrospective_source_ledger"]["path"]).read_text()
        ),
        "retrospective_verification": {"verified": True, "generated_only": True, "records": {}},
    }


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
