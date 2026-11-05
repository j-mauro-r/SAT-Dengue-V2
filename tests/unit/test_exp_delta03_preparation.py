"""Generated-only contracts for admission, temporal availability and deterministic no-fit views."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
import pytest

from sat_dengue.data.exp_delta03 import (
    available_mask,
    block_views,
    h5_labels,
    historical_window,
    lagged,
    land_cover,
    normalize,
    prepare_features,
    seasonal_anomaly,
    temporal_roles,
)
from sat_dengue.data.exp_delta03_quality import profile
from sat_dengue.datasets.exp_delta03 import admit, publish

ROOT = Path(__file__).resolve().parents[2]


def fixture() -> tuple[pd.DataFrame, dict, list[dict[str, str]]]:
    contract = json.loads(
        (ROOT / "docs/product/experiments/EXP-DELTA03/phase1-contract.json").read_text()
    )
    rows = []
    for code in ["05001", "50001", "73001"]:
        for i, month in enumerate(pd.period_range("2007-01", "2014-12", freq="M")):
            row: dict[str, Any] = {name: float(i % 10) for name in contract["ordered_columns"]}
            row["ndvi_disponible"] = True
            row.update(
                divipola_municipio=code,
                divipola_departamento=code[:2],
                periodo_mes=str(month) + "-01",
                anio=month.year,
                mes=month.month,
            )
            rows.append(row)
    frame = pd.DataFrame(rows, columns=contract["ordered_columns"])
    dictionary = [
        {
            "nombre_variable": name,
            "fuente_producto": "generated",
            "tipo_dato": "decimal"
            if name not in ["divipola_municipio", "divipola_departamento", "periodo_mes"]
            else "texto",
            "unidad": "unit",
            "cobertura_temporal": "generated",
        }
        for name in frame
    ]
    contract["source"].update(
        expected_rows=len(frame),
        expected_columns=len(frame.columns),
        expected_municipalities=3,
        expected_months=96,
        coverage=["2007-01", "2014-12"],
    )
    return frame, contract, dictionary


def saved(tmp_path: Path) -> tuple[Path, dict]:
    frame, c, _ = fixture()
    p = tmp_path / c["source"]["path"]
    p.parent.mkdir(parents=True)
    frame.to_csv(p, index=False)
    c["source"]["expected_bytes"] = p.stat().st_size
    c["source"]["expected_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p, c


def test_admission_identity_and_repeat_preservation(tmp_path: Path) -> None:
    p, c = saved(tmp_path)
    before = p.read_bytes()
    result = admit(tmp_path, c)
    assert result["receipt"]["rows"] == 288
    assert set(result["frame"].divipola_municipio) == {"05001", "50001", "73001"}
    assert admit(tmp_path, c)["receipt"] == result["receipt"] and p.read_bytes() == before


@pytest.mark.parametrize(
    "kind",
    ["hash", "bytes", "schema", "municipalities", "period", "external", "symlink", "duplicate"],
)
def test_admission_rejects_substitution(tmp_path: Path, kind: str) -> None:
    p, c = saved(tmp_path)
    if kind == "hash":
        c["source"]["expected_sha256"] = "0" * 64
    elif kind == "bytes":
        c["source"]["expected_bytes"] += 1
    elif kind == "schema":
        c["ordered_columns"].reverse()
    elif kind == "municipalities":
        c["source"]["expected_municipalities"] = 4
    elif kind == "period":
        c["source"]["coverage"] = ["2008-01", "2014-12"]
    elif kind == "symlink":
        other = tmp_path / "actual.csv"
        p.rename(other)
        p.symlink_to(other)
    elif kind == "duplicate":
        f = pd.read_csv(p, dtype={"divipola_municipio": str, "divipola_departamento": str})
        f = pd.concat([f.iloc[:-1], f.iloc[[0]]])
        f.to_csv(p, index=False)
        c["source"]["expected_bytes"] = p.stat().st_size
        c["source"]["expected_sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    with pytest.raises(ValueError):
        admit(tmp_path, c, relative="/outside.csv" if kind == "external" else None)


@pytest.mark.parametrize(
    "kind", ["integer_code", "department", "gap", "day", "calendar", "normalization_collision"]
)
def test_normalization_strict_codes_calendar_and_order(kind: str) -> None:
    f, _, _ = fixture()
    if kind == "integer_code":
        f["divipola_municipio"] = 50001
    elif kind == "department":
        f.loc[0, "divipola_departamento"] = "73"
    elif kind == "gap":
        f = f.drop(index=1)
    elif kind == "day":
        f.loc[0, "periodo_mes"] = "2007-01-02"
    elif kind == "calendar":
        f.loc[0, "anio"] = 2008
    else:
        f.loc[1, "periodo_mes"] = "2007-01"
    with pytest.raises(ValueError):
        normalize(f)


def test_eda_complete_classification_missingness_redundancy_no_drop() -> None:
    f, c, d = fixture()
    f.loc[0, "ndvi_medio"] = np.nan
    normal = normalize(f.sample(frac=1, random_state=3))
    r = profile(normal, d, c)
    assert len(r["inventory"]) == 142
    assert next(x for x in r["inventory"] if x["original_name"] == "ndvi_medio")["missing"] == 1
    assert r["redundancy"] and r["missingness"] and len(f.columns) == 142
    assert (
        next(
            x
            for x in r["inventory"]
            if x["original_name"] == "fraccion_mosaico_cultivo_natural_modis_pct"
        )["decision"]
        == "unresolved"
    )


def test_temporal_lags_windows_never_bridge_or_use_future() -> None:
    f, _, _ = fixture()
    f = normalize(f)
    before = historical_window(f, "temp_media_c", "mean")
    changed = f.copy()
    changed.loc[changed.periodo_mes.gt("2010-01"), "temp_media_c"] = 999
    pd.testing.assert_series_equal(
        before[f.periodo_mes.le("2010-01")],
        historical_window(changed, "temp_media_c", "mean")[f.periodo_mes.le("2010-01")],
    )
    assert lagged(f, "temp_media_c", 1).iloc[96] != lagged(f, "temp_media_c", 1).iloc[96]
    assert (
        historical_window(f.drop(index=1), "temp_media_c", "sum").iloc[1]
        != historical_window(f.drop(index=1), "temp_media_c", "sum").iloc[1]
    )
    with pytest.raises(ValueError):
        lagged(f, "temp_media_c", 0)


def test_availability_centered_oni_and_unknown_vintages() -> None:
    f, c, _ = fixture()
    f = normalize(f)
    assert not available_mask(f, "oni_3m_c", 2, []).any()
    evidence = [
        {
            "source": "oni_3m_c",
            "event_month": "2007-01",
            "available_at": "2007-03-01",
            "vintage": "generated",
            "evidence_id": "generated-proof",
        }
    ]
    f.attrs.update(source_sha256="generated-snapshot", field_vintages={"oni_3m_c": "generated"})
    evidence[0]["source_sha256"] = "generated-snapshot"
    mask = available_mask(f, "oni_3m_c", 2, evidence)
    assert set(f.loc[mask, "periodo_mes"]) == {"2007-03"}
    features, manifest = prepare_features(f, c)
    assert features.oni_3m_c__lag2.isna().all()
    assert all(v["name"] not in ["year", "periodo_mes", "divipola_municipio"] for v in manifest)


def test_h5_label_definition_and_unknown_history() -> None:
    f, _, _ = fixture()
    f = normalize(f)
    counts = pd.Series(1.0, index=f.index)
    counts.loc[f.periodo_mes.eq("2013-02")] = 10
    labels = h5_labels(f, counts)
    origin = f.periodo_mes.eq("2013-01")
    assert labels.loc[origin, "onset_T1"].eq(1).all()
    assert labels.loc[f.periodo_mes.eq("2012-12"), "onset_T2"].eq(1).all()
    assert labels.loc[f.year.lt(2012), "p75"].isna().all()
    missing = counts.copy()
    missing.iloc[0] = np.nan
    assert pd.isna(h5_labels(f, missing).loc[60, "p75"])


def test_cohort_roles_exclude_future_target_and_embargo_origins() -> None:
    f = pd.DataFrame({"periodo_mes": ["2019-12", "2020-01", "2024-12", "2025-01"]})
    assert temporal_roles(f, 2020, 1).tolist() == [
        "evaluation",
        "evaluation",
        "excluded_2025",
        "excluded_2025",
    ]


def test_blocks_no_identifier_leak_and_mosaic_separate() -> None:
    f, c, _ = fixture()
    f = normalize(f)
    _, manifest = prepare_features(f, c)
    views = block_views(manifest, c["variants"])
    assert len(views) == 11
    for name in views["FULL_MINUS_NDVI"]:
        assert next(v["block"] for v in manifest if v["name"] == name) != "NDVI"
    assert not set(views["FULL_COMMON"]) & set(["periodo_mes", "divipola_municipio", "onset_T1"])
    lc = land_cover(f, c)
    assert "mosaic_unassigned" in lc
    assert lc.agriculture.eq(f.fraccion_cultivo_modis_pct).all()


def test_training_only_seasonal_reference() -> None:
    f, _, _ = fixture()
    f = normalize(f)
    values = lagged(f, "ndvi_medio", 1)
    train = f.year.lt(2010)
    a = seasonal_anomaly(f, values, train)
    other = values.copy()
    other.loc[~train] = 999
    b = seasonal_anomaly(f, other, train)
    pd.testing.assert_series_equal(a[train], b[train])


def test_atomic_publication_reuse_tamper_and_paths(tmp_path: Path) -> None:
    payload = {"receipt.json": b"{}\n"}
    first = publish(tmp_path, "tmp/exp-delta03-phase1/products", payload)
    assert publish(tmp_path, "tmp/exp-delta03-phase1/products", payload) == first
    (tmp_path / first["path"] / "receipt.json").write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        publish(tmp_path, "tmp/exp-delta03-phase1/products", payload)
    for root in ["/tmp/elsewhere", "tmp/exp-delta03-phase1/../../escape"]:
        with pytest.raises(ValueError):
            publish(tmp_path, root, payload)


def test_revised_snapshot_cannot_borrow_old_release() -> None:
    f, _, _ = fixture()
    f = normalize(f)
    f.attrs.update(source_sha256="revised", field_vintages={"oni_3m_c": "revision2"})
    record = {
        "source": "oni_3m_c",
        "event_month": "2007-01",
        "available_at": "2007-02-28",
        "vintage": "revision1",
        "source_sha256": "old",
        "evidence_id": "old-release",
    }
    assert not available_mask(f, "oni_3m_c", 2, [record]).any()


def test_asof_selects_actual_prior_released_value_not_current_revision() -> None:
    from sat_dengue.data.exp_delta03 import asof_observations

    origins = pd.DataFrame(
        {"divipola_municipio": ["05001", "05001"], "periodo_mes": ["2020-01", "2020-06"]}
    )
    observations = pd.DataFrame(
        [
            {
                "source": "poblacion_total",
                "divipola_municipio": "05001",
                "event_month": "2019-01",
                "available_at": "2019-12-01",
                "vintage": "v1",
                "value": 100,
                "source_sha256": "old",
                "evidence_id": "proof1",
            },
            {
                "source": "poblacion_total",
                "divipola_municipio": "05001",
                "event_month": "2020-01",
                "available_at": "2020-05-01",
                "vintage": "v2",
                "value": 200,
                "source_sha256": "new",
                "evidence_id": "proof2",
            },
        ]
    )
    assert asof_observations(origins, "poblacion_total", observations).tolist() == [100.0, 200.0]


def test_pair_masks_are_role_specific_identical_and_transfer_holds_out_targets() -> None:
    from sat_dengue.data.exp_delta03 import comparison_masks

    f, _, _ = fixture()
    f = normalize(f)
    # Shift generated calendar into retrospective cells; no actual source is used.
    f["periodo_mes"] = (pd.PeriodIndex(f.periodo_mes, freq="M") + 12 * 8).astype(str)
    labels = pd.DataFrame({"eligible_T1": True, "eligible_T2": True}, index=f.index)
    features = pd.DataFrame(
        {
            "fraccion_agua_superficial_pct_area_observada__lag1": 1.0,
            "precipitacion_chirps_total_mm__lag1": 1.0,
            "precipitacion_total_mm__lag1": 1.0,
        },
        index=f.index,
    )
    masks = comparison_masks(f, labels, features, 2020, 1, labels_admitted=True)
    for role, pair in masks.items():
        pd.testing.assert_series_equal(pair["WATER_REFERENCE"], pair["FULL_PLUS_SURFACE_WATER"])
        pd.testing.assert_series_equal(pair["ERA5_REFERENCE"], pair["FULL_ERA5_PRECIPITATION"])
        selected = f.loc[pair["TRANSFER_EXCLUDE_META_TOLIMA"], "divipola_departamento"]
        assert (
            selected.isin(["50", "73"]) if role == "evaluation" else ~selected.isin(["50", "73"])
        ).all()
    denied = comparison_masks(f, labels, features, 2020, 1, labels_admitted=False)
    assert not any(v.any() for pair in denied.values() for v in pair.values())


def test_transport_anomaly_uses_training_national_reference_without_target_fit() -> None:
    f, _, _ = fixture()
    f = normalize(f)
    training = f.year.lt(2010)
    values = pd.Series(np.arange(len(f), dtype=float), index=f.index)
    target = f.divipola_departamento.isin(["50", "73"])
    before = seasonal_anomaly(f, values, training, national_reference=True, exclude_targets=True)
    changed = values.copy()
    changed.loc[target & training] += 1000
    after = seasonal_anomaly(f, changed, training, national_reference=True, exclude_targets=True)
    pd.testing.assert_series_equal(before[~training], after[~training])
    assert before[~training].notna().all()
