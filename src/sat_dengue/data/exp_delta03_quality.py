"""Reproducible source profiling, independent of filesystem and training frameworks."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]


def profile(
    frame: pd.DataFrame, dictionary: list[dict[str, str]], contract: dict[str, Any]
) -> dict[str, Any]:
    """Describe every source field; correlation never automatically changes eligibility."""
    meta = {v["nombre_variable"]: v for v in dictionary}
    blocks = {s: b for b, spec in contract["blocks"].items() for s in spec["sources"]}
    identifiers = {
        "divipola_municipio",
        "divipola_departamento",
        "departamento",
        "municipio",
        "periodo_mes",
    }
    target_prefixes = (
        "notificados_",
        "retenidos_",
        "hospitalizados_",
        "fallecidos_",
        "incidencia_",
        "registros_fecha_",
    )
    inventory = []
    numeric = {}
    quality = []
    missingness = []
    original = [v["nombre_variable"] for v in dictionary]
    missing = frame[original].isna() | frame[original].astype(str).eq("")
    for name in original:
        info = meta[name]
        series = frame[name]
        nonnull = series.dropna()
        n = int(missing[name].sum())
        decision = "descriptive_only"
        reason = "Source/QC metadata; no predictor role"
        if name in identifiers:
            decision = "identifier"
            reason = "Keys and names never enter X"
        elif name.startswith(target_prefixes):
            decision = "target_or_future"
            reason = "Contemporaneous epidemiology forbidden; history mapping unresolved"
        elif name in blocks:
            decision = "conditional"
            reason = "Historical release/vintage proof required"
        if name == "transpiracion_vegetacion_total_mm_signo_era5":
            decision = "excluded"
            reason = "Known source-band identity contradiction"
        if name in {
            "ndvi_mediana",
            "altitud_mediana_m",
            "pendiente_mediana_grados",
            "nino34_anomalia_c",
        }:
            decision = "excluded"
            reason = "Design excludes redundant representation"
        if name == "fraccion_mosaico_cultivo_natural_modis_pct":
            decision = "unresolved"
            reason = "Mixed composition retained separately; no scientific allocation"
        values = pd.to_numeric(series, errors="coerce").astype(float)
        invalid = int((series.notna() & values.isna()).sum())
        if info["tipo_dato"] in {"entero", "decimal"}:
            if invalid:
                quality.append(
                    {"variable": name, "issue": "metadata_type_contradiction", "rows": invalid}
                )
            if invalid == 0:
                numeric[name] = values
                finite = values.dropna()
                if not np.isfinite(finite).all():
                    quality.append(
                        {
                            "variable": name,
                            "issue": "nonfinite",
                            "rows": int((~np.isfinite(finite)).sum()),
                        }
                    )
                bad = pd.Series(False, index=frame.index)
                if (
                    name.startswith(("porcentaje_", "fraccion_"))
                    or name == "humedad_relativa_media_pct"
                ):
                    bad |= values.lt(0) | values.gt(100)
                if name in {"ndvi_medio", "ndvi_mediana"}:
                    bad |= values.lt(-1) | values.gt(1)
                if name == "pendiente_media_grados":
                    bad |= values.lt(0) | values.gt(90)
                if name in {
                    "vpd_medio_kpa",
                    "viento_medio_ms",
                    "precipitacion_chirps_total_mm",
                    "precipitacion_total_mm",
                    "area_agua_superficial_m2",
                    "area_observada_m2",
                    "poblacion_total",
                }:
                    bad |= values.lt(0)
                if bad.any():
                    quality.append(
                        {"variable": name, "issue": "physical_domain", "rows": int(bad.sum())}
                    )
                if len(finite):
                    q1, q3 = finite.quantile([0.25, 0.75])
                    iqr = q3 - q1
                    quality.append(
                        {
                            "variable": name,
                            "issue": "IQR_outlier_diagnostic_not_exclusion",
                            "rows": int((finite.lt(q1 - 3 * iqr) | finite.gt(q3 + 3 * iqr)).sum()),
                            "q01": float(finite.quantile(0.01)),
                            "q99": float(finite.quantile(0.99)),
                        }
                    )
        common = float(nonnull.value_counts(normalize=True).max()) if len(nonnull) else None
        inventory.append(
            {
                "original_name": name,
                "canonical_name": name,
                "source": info["fuente_producto"],
                "type": info["tipo_dato"],
                "unit": info["unidad"],
                "temporal_coverage": info["cobertura_temporal"],
                "missing": n,
                "missing_fraction": n / len(frame),
                "distinct_nonnull": int(nonnull.nunique()),
                "near_constant": common is not None
                and common >= contract["near_constant_fraction"],
                "dominant_fraction": common,
                "transformation": (
                    "see transformation manifest; original field is not an automatic predictor"
                ),
                "availability_window": "UNVERIFIED" if name in blocks else "not a predictor",
                "block": blocks.get(name),
                "leakage_risk": "high"
                if decision in {"target_or_future", "conditional", "unresolved"}
                else "controlled_by_exclusion",
                "decision": decision,
                "reason": reason,
            }
        )
    for group in ["year", "divipola_departamento", "divipola_municipio"]:
        counts = missing.groupby(frame[group], sort=True).sum()
        sizes = frame.groupby(group, sort=True).size()
        for key, row in counts.iterrows():
            missingness.append(
                {
                    "dimension": group,
                    "value": str(key),
                    "rows": int(sizes.loc[key]),
                    "missing": {name: int(v) for name, v in row.items()},
                }
            )
    numbers = pd.DataFrame(numeric)
    redundancy: list[dict[str, Any]] = []
    hashes = {
        name: pd.util.hash_pandas_object(frame[name], index=False).to_numpy().tobytes()
        for name in original
    }
    names = original
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            if hashes[left] == hashes[right] and frame[left].equals(frame[right]):
                redundancy.append(
                    {
                        "left": left,
                        "right": right,
                        "kind": "exact",
                        "recommendation": "review; no automatic removal",
                    }
                )
    if len(numbers.columns) > 1:
        corr = numbers.corr(min_periods=24)
        for i, left in enumerate(corr):
            for right in corr.columns[i + 1 :]:
                value = corr.loc[left, right]
                if pd.notna(value) and abs(value) >= contract["high_correlation_abs"]:
                    redundancy.append(
                        {
                            "left": left,
                            "right": right,
                            "kind": "high_correlation",
                            "r": float(value),
                            "support": int((numbers[left].notna() & numbers[right].notna()).sum()),
                            "recommendation": "review; no automatic removal",
                        }
                    )
    rainfall = []
    for left, right in [
        ("precipitacion_chirps_total_mm", "precipitacion_total_mm"),
        ("precipitacion_chirps_max_diaria_mm", "precipitacion_max_diaria_mm"),
    ]:
        if left in numbers and right in numbers:
            diff = numbers[left] - numbers[right]
            rainfall.append(
                {
                    "left": left,
                    "right": right,
                    "paired_rows": int(diff.notna().sum()),
                    "mean_difference": float(diff.mean()) if diff.notna().any() else None,
                    "different_spatial_statistics": True,
                }
            )
    coverage = []
    for code, part in frame.groupby("divipola_departamento", sort=True):
        coverage.append(
            {
                "department": str(code),
                "municipalities": int(part.divipola_municipio.nunique()),
                "rows": len(part),
                "period_start": part.periodo_mes.min(),
                "period_end": part.periodo_mes.max(),
            }
        )
    return {
        "inventory": inventory,
        "missingness": missingness,
        "quality": quality,
        "redundancy": redundancy,
        "rainfall_comparison": rainfall,
        "geographic_coverage": coverage,
        "summary": {
            "rows": len(frame),
            "source_columns": len(dictionary),
            "municipalities": int(frame.divipola_municipio.nunique()),
            "period_start": frame.periodo_mes.min(),
            "period_end": frame.periodo_mes.max(),
            "water_states": frame.estado_cobertura_agua_superficial.value_counts(dropna=False)
            .astype(int)
            .to_dict()
            if "estado_cobertura_agua_superficial" in frame
            else {},
            "availability": "UNVERIFIED; field coverage does not establish historical publication",
            "schema_changes": (
                "single pinned snapshot; change history unavailable; compare "
                "dictionary contradictions in quality report"
            ),
        },
    }
