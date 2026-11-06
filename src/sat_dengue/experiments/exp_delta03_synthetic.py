"""Small generated-only preparation, shared by Phase1 regression and Phase2 E2E.

Only public contracts enter this builder; no filesystem, private rows, estimator
or tracking access. Its synthetic control sets do not claim private-source parity.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03 import KEYS, h5_labels, normalize, temporal_roles


def generated_preparation(contract: dict[str, Any], ledger: dict[str, Any]) -> dict[str, Any]:
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
        "vintage_ledger": ledger,
        "retrospective_verification": {"verified": True, "generated_only": True, "records": {}},
    }
