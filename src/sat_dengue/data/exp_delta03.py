"""Pure EXP-DELTA03 key, availability, label and block transformations; never fit models."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

KEYS = ["divipola_municipio", "periodo_mes"]


def normalize(frame: pd.DataFrame) -> pd.DataFrame:
    """Reject ambiguous identities and gaps, preserving string codes and explicit missingness."""
    if frame.empty or frame.columns.duplicated().any() or not set(KEYS) <= set(frame):
        raise ValueError("Empty or invalid schema")
    result = frame.copy()
    for name, width in [("divipola_municipio", 5), ("divipola_departamento", 2)]:
        if name not in result or not result[name].map(lambda x: isinstance(x, str)).all():
            raise ValueError("DIVIPOLA must be text")
        if not result[name].str.fullmatch(r"\d{" + str(width) + "}").all():
            raise ValueError("Invalid DIVIPOLA width")
    if not result.divipola_departamento.eq(result.divipola_municipio.str[:2]).all():
        raise ValueError("Contradictory department code")
    for code, name in [
        ("divipola_municipio", "municipio"),
        ("divipola_departamento", "departamento"),
    ]:
        if name in result and result[name].dtype == object:
            if result.groupby(code)[name].nunique(dropna=True).gt(1).any():
                raise ValueError("Contradictory identifier descriptions")
    raw = result.periodo_mes.astype(str)
    if not raw.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])(-01)?").all():
        raise ValueError("Expected canonical month or month-start date")
    result["periodo_mes"] = raw.str[:7]
    if result.duplicated(KEYS).any():
        raise ValueError("Duplicate normalized municipality-month")
    result = result.sort_values(KEYS, kind="stable").reset_index(drop=True)
    period = pd.PeriodIndex(result.periodo_mes, freq="M")
    result["year"] = period.year
    result["month"] = period.month
    for original, derived in [("anio", "year"), ("mes", "month")]:
        if original in result and not pd.to_numeric(result[original]).eq(result[derived]).all():
            raise ValueError("Contradictory source calendar")
    delta = pd.Series(period.asi8).groupby(result.divipola_municipio).diff().dropna()
    if not delta.eq(1).all():
        raise ValueError("Monthly discontinuity")
    result["is_meta"] = result.divipola_departamento.eq("50")
    result["is_tolima"] = result.divipola_departamento.eq("73")
    return result


def lagged(frame: pd.DataFrame, source: str, lag: int) -> pd.Series:
    """Exact-calendar lag; no bridging of gaps or municipal boundaries."""
    if lag < 1:
        raise ValueError("Only strictly historical lags are allowed")
    lookup = frame.set_index(KEYS)[source]
    keys = pd.MultiIndex.from_arrays(
        [frame.divipola_municipio, (pd.PeriodIndex(frame.periodo_mes, freq="M") - lag).astype(str)]
    )
    return pd.Series(lookup.reindex(keys).to_numpy(), index=frame.index, dtype="float64")


def historical_window(frame: pd.DataFrame, source: str, operator: str) -> pd.Series:
    """Require all three observed months T-3:T-1; never shorten windows or fill zeros."""
    window = pd.concat([lagged(frame, source, lag) for lag in (3, 2, 1)], axis=1)
    if operator not in {"mean", "sum", "max"}:
        raise ValueError("Unknown temporal operator")
    value = getattr(window, operator)(axis=1)
    return value.where(window.notna().all(axis=1))


def available_mask(
    frame: pd.DataFrame, source: str, lag: int, evidence: list[dict[str, Any]]
) -> pd.Series:
    """Use explicit release/vintage intervals; unknown evidence means ineligible, not guessed."""
    origins = pd.PeriodIndex(frame.periodo_mes, freq="M")
    observed = (origins - lag).astype(str)
    allowed = pd.Series(False, index=frame.index)
    for item in evidence:
        if item.get("source") != source:
            continue
        if (
            item.get("source_sha256") != frame.attrs.get("source_sha256")
            or item.get("vintage") != frame.attrs.get("field_vintages", {}).get(source)
            or not item.get("source_sha256")
        ):
            continue  # An old release cannot admit a revised value from another snapshot.
        if not {"source", "event_month", "available_at", "vintage", "evidence_id"} <= set(item):
            raise ValueError("Incomplete release evidence")
        release = pd.Timestamp(item["available_at"])
        cutoff = origins.to_timestamp(how="end")
        allowed |= (observed == item["event_month"]) & (cutoff >= release)
    return allowed


def h5_labels(frame: pd.DataFrame, counts: pd.Series) -> pd.DataFrame:
    """Construct conditional H5 labels; caller must separately admit count semantics/parity."""
    if len(frame) != len(counts):
        raise ValueError("Counts must align to keys")
    values = frame[KEYS].copy()
    values["count"] = counts.to_numpy()
    if (counts.dropna() < 0).any() or (counts.dropna() % 1 != 0).any():
        raise ValueError("Invalid notification count")
    lookup = values.set_index(KEYS)["count"]
    history = []
    for years in range(1, 6):
        idx = pd.MultiIndex.from_arrays(
            [
                frame.divipola_municipio,
                (pd.PeriodIndex(frame.periodo_mes, freq="M") - years * 12).astype(str),
            ]
        )
        history.append(pd.Series(lookup.reindex(idx).to_numpy(), index=frame.index))
    hist = pd.concat(history, axis=1)
    p75 = hist.quantile(0.75, axis=1, interpolation="linear").where(hist.notna().all(axis=1))
    excess = counts.gt(p75).astype("Int64").where(counts.notna() & p75.notna())
    states = frame[KEYS].copy()
    states["excess"] = excess
    result = states.copy()
    result["p75"] = p75
    lookup_state = states.set_index(KEYS).excess
    periods = pd.PeriodIndex(frame.periodo_mes, freq="M")

    def future(offset: int) -> pd.Series:
        idx = pd.MultiIndex.from_arrays([frame.divipola_municipio, (periods + offset).astype(str)])
        return pd.Series(lookup_state.reindex(idx).to_numpy(), index=frame.index, dtype="Int64")

    for h in (1, 2):
        preceding = future(h - 1)
        target = future(h)
        onset = (
            (preceding.eq(0) & target.eq(1))
            .astype("Int64")
            .where(preceding.notna() & target.notna())
        )
        result[f"onset_T{h}"] = onset
        result[f"eligible_T{h}"] = (
            excess.eq(0) & onset.notna() & ((periods + h).year < 2025)
        ).fillna(False)
    return result


def temporal_roles(frame: pd.DataFrame, year: int, horizon: int) -> pd.Series:
    """Target-year roles plus origin embargo at every role boundary; 2025 never develops."""
    if year not in (2020, 2021, 2022, 2024) or horizon not in (1, 2):
        raise ValueError("Unsupported temporal cell")
    origin = pd.PeriodIndex(frame.periodo_mes, freq="M")
    target = origin + horizon
    role = pd.Series("unused", index=frame.index)
    role.loc[
        (target.year <= year - 4) & (target.asi8 >= pd.Period("2011-06", freq="M").ordinal)
    ] = "train"
    for offset, name in [
        (-3, "calibration"),
        (-2, "embargo"),
        (-1, "selection"),
        (0, "evaluation"),
    ]:
        start_year = year + offset
        mask = (target.year == start_year) & (
            origin.asi8 >= pd.Period(f"{start_year - 1}-12", freq="M").ordinal
        )
        role.loc[mask] = name
    role.loc[(origin.year >= 2025) | (target.year >= 2025)] = "excluded_2025"
    return role


def prepare_features(
    frame: pd.DataFrame, contract: dict[str, Any]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """One base with closed feature provenance and explicit per-row release guards."""
    output = frame[KEYS].copy()
    manifest: list[dict[str, Any]] = []
    evidence = contract["availability_evidence"]

    def add(source: str, block: str, operator: str, lag: int = 1) -> None:
        if source not in frame:
            raise ValueError("Feature source missing")
        name = f"{source}__{operator}"
        values = (
            lagged(frame, source, lag)
            if operator.startswith("lag")
            else historical_window(frame, source, operator)
        )
        offsets = [lag] if operator.startswith("lag") else [1, 2, 3]
        mask = pd.Series(True, index=frame.index)
        for offset in offsets:
            mask &= available_mask(frame, source, offset, evidence)
        output[name] = values.where(mask)
        manifest.append(
            {
                "name": name,
                "source": source,
                "block": block,
                "transformation": operator,
                "event_lags": offsets,
                "available_at_guard": True,
                "dtype": "float64",
                "decision": "conditional",
                "eligible_rows": int((mask & values.notna()).sum()),
                "reason": "requires documented historical release/vintage evidence",
            }
        )

    month = frame.month.to_numpy()
    for name, values in [
        ("month_sin", np.sin(2 * np.pi * month / 12)),
        ("month_cos", np.cos(2 * np.pi * month / 12)),
    ]:
        output[name] = values
        manifest.append(
            {
                "name": name,
                "source": "periodo_mes",
                "block": "CALENDAR",
                "transformation": name,
                "event_lags": [0],
                "available_at_guard": True,
                "dtype": "float64",
                "decision": "included",
                "eligible_rows": len(frame),
                "reason": "known origin calendar",
            }
        )
    for block in ["THERMAL_HUMIDITY", "RAINFALL_HYDROLOGY", "NDVI"]:
        spec = contract["blocks"][block]
        for source in spec["sources"]:
            add(source, block, "lag1")
        for operation in ["mean3", "sum3", "max3"]:
            for source in spec.get(operation, []):
                add(source, block, operation[:-1])
    add("oni_3m_c", "ENSO", "lag2", 2)
    # Delta uses ONLY historical NDVI; both operands must pass release guards.
    add("ndvi_medio", "NDVI", "lag2", 2)
    output["ndvi_change"] = output["ndvi_medio__lag1"] - output.pop("ndvi_medio__lag2")
    manifest.pop()
    manifest.append(
        {
            "name": "ndvi_change",
            "source": "ndvi_medio",
            "block": "NDVI",
            "transformation": "lag1-lag2",
            "event_lags": [1, 2],
            "available_at_guard": True,
            "dtype": "float64",
            "decision": "conditional",
            "eligible_rows": int(output.ndvi_change.notna().sum()),
            "reason": "both original observations require release evidence",
        }
    )
    for source in ["precipitacion_total_mm", "precipitacion_max_diaria_mm", "racha_seca_max_dias"]:
        add(source, "ERA5_PRECIPITATION", "lag1")
    add("precipitacion_total_mm", "ERA5_PRECIPITATION", "sum")
    add("racha_seca_max_dias", "ERA5_PRECIPITATION", "max")
    add("fraccion_agua_superficial_pct_area_observada", "SURFACE_WATER", "lag1")
    water = "fraccion_agua_superficial_pct_area_observada__lag1"
    observed = lagged(frame, "area_observada_m2", 1)
    output[water] = output[water].where(observed.gt(0) & frame.year.le(2021))
    # Annual/static source snapshots require admitted historical versions.
    for block in ["TERRAIN", "DEMOGRAPHY"]:
        for source in contract["blocks"][block]["sources"]:
            name = source + "__asof"
            val = asof_observations(
                frame, source, pd.DataFrame(contract.get("versioned_observations", []))
            )
            if source in contract["blocks"][block].get("log1p", []):
                val = np.log1p(val.where(val.ge(0)))
            output[name] = val
            manifest.append(
                {
                    "name": name,
                    "source": source,
                    "block": block,
                    "transformation": "asof_last_verified_vintage",
                    "event_lags": [0],
                    "available_at_guard": True,
                    "dtype": "float64",
                    "decision": "conditional",
                    "eligible_rows": int(output[name].notna().sum()),
                    "reason": "source year is not a publication date",
                }
            )
    for source in [
        "dengue_notifications_count",
        "dengue_grave_notifications_count",
        "total_notifications_count",
    ]:
        for lag in contract["history_lags"]:
            name = f"{source}_lag{lag}"
            output[name] = np.nan
            manifest.append(
                {
                    "name": name,
                    "source": None,
                    "block": "HISTORY",
                    "transformation": f"lag{lag}",
                    "event_lags": [lag],
                    "available_at_guard": True,
                    "dtype": "float64",
                    "decision": "unresolved",
                    "eligible_rows": 0,
                    "reason": (
                        "210/220 source mapping and missing-observation equivalence not authorized"
                    ),
                }
            )
    output["ndvi_anomaly"] = np.nan
    manifest.append(
        {
            "name": "ndvi_anomaly",
            "source": "ndvi_medio",
            "block": "NDVI",
            "transformation": "training-only seasonal reference per horizon/year; seasonal_anomaly",
            "event_lags": [1],
            "available_at_guard": True,
            "dtype": "float64",
            "decision": "conditional",
            "eligible_rows": 0,
            "reason": "requires admitted cell-specific training references and release evidence",
        }
    )
    for name, columns in contract["blocks"]["LAND_COVER"]["aggregates"].items():
        output["land_" + name] = np.nan
        manifest.append(
            {
                "name": "land_" + name,
                "source": "+".join(columns),
                "block": "LAND_COVER",
                "transformation": (
                    "annual sum then last verified released vintage; mosaic remains separate"
                ),
                "event_lags": [],
                "available_at_guard": True,
                "dtype": "float64",
                "decision": "unresolved",
                "eligible_rows": 0,
                "reason": (
                    "annual vintages and final compositional vector unresolved; audit-"
                    "only aggregate"
                ),
            }
        )
    for item in manifest:
        item["eligible_rows"] = int(output[item["name"]].notna().sum())
    return output, manifest


def seasonal_anomaly(
    frame: pd.DataFrame,
    values: pd.Series,
    training: pd.Series,
    *,
    national_reference: bool = False,
    exclude_targets: bool = False,
) -> pd.Series:
    """Training-only municipal or national month reference; no held-out target fitting."""
    if exclude_targets and not national_reference:
        raise ValueError("Transport requires the same national-reference operator in both arms")
    mask = training.copy()
    if exclude_targets:
        mask &= ~frame.divipola_departamento.isin(["50", "73"])
    groups = ["month"] if national_reference else ["divipola_municipio", "month"]
    reference = frame[groups].copy()
    reference["value"] = values.to_numpy()
    means = reference.loc[mask].groupby(groups).value.mean()
    idx = reference["month"] if national_reference else pd.MultiIndex.from_frame(reference[groups])
    return values - pd.Series(means.reindex(idx).to_numpy(), index=frame.index)


def land_cover(frame: pd.DataFrame, contract: dict[str, Any]) -> pd.DataFrame:
    """Audit-only five-part composition preserves unresolved mixed mosaic separately."""
    return pd.DataFrame(
        {
            name: frame[columns].sum(axis=1, min_count=len(columns))
            for name, columns in contract["blocks"]["LAND_COVER"]["aggregates"].items()
        },
        index=frame.index,
    )


def block_views(manifest: list[dict[str, Any]], variants: list[str]) -> dict[str, list[str]]:
    """Deterministic selectors exclude identifiers/labels and all removed descendants."""

    def select(exclude: set[str], water: bool = False, era5: bool = False) -> list[str]:
        return [
            v["name"]
            for v in manifest
            if v["block"] not in exclude
            and (water or v["block"] != "SURFACE_WATER")
            and (era5 or v["block"] != "ERA5_PRECIPITATION")
            and not (
                era5 and str(v["source"]).startswith(("precipitacion_chirps", "racha_seca_chirps"))
            )
        ]

    views = {}
    for variant in variants:
        if variant == "HISTORY":
            views[variant] = select(set(v["block"] for v in manifest) - {"HISTORY", "CALENDAR"})
        else:
            removed = (
                {variant.removeprefix("FULL_MINUS_")}
                if variant.startswith("FULL_MINUS_")
                else set()
            )
            views[variant] = select(
                removed, variant == "FULL_PLUS_SURFACE_WATER", variant == "FULL_ERA5_PRECIPITATION"
            )
    return views


def geographic_mask(frame: pd.DataFrame, variant: str, role: str) -> pd.Series:
    """Whole-procedure geographic holdout; target histories are never learned samples."""
    target = frame.divipola_departamento.isin(["50", "73"])
    if role == "evaluation":
        return target
    if variant == "TRANSFER_EXCLUDE_META_TOLIMA":
        return ~target
    return pd.Series(True, index=frame.index)


def asof_observations(frame: pd.DataFrame, source: str, observations: pd.DataFrame) -> pd.Series:
    """Last released explicit vintage, never today's value substituted for an older release."""
    result = pd.Series(np.nan, index=frame.index, dtype="float64")
    required = {
        "source",
        "divipola_municipio",
        "event_month",
        "available_at",
        "vintage",
        "value",
        "source_sha256",
        "evidence_id",
    }
    if observations.empty:
        return result
    if not required <= set(observations) or observations[list(required)].isna().any().any():
        raise ValueError("Incomplete versioned observation")
    if observations.duplicated(["source", "divipola_municipio", "event_month", "vintage"]).any():
        raise ValueError("Ambiguous observation vintage")
    for code, origins in frame.groupby("divipola_municipio", sort=True):
        candidates = observations.loc[
            observations.source.eq(source) & observations.divipola_municipio.eq(code)
        ].copy()
        if candidates.empty:
            continue
        candidates["release"] = pd.to_datetime(candidates.available_at)
        candidates = candidates.sort_values(["event_month", "release", "vintage"])
        for idx, row in origins.iterrows():
            cutoff = pd.Period(row.periodo_mes, freq="M").end_time
            allowed = candidates.loc[
                candidates.event_month.le(row.periodo_mes) & candidates.release.le(cutoff)
            ]
            if not allowed.empty:
                result.loc[idx] = float(allowed.iloc[-1]["value"])
    return result


def history_from_mapping(frame: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Explicit admitted mappings only; never infer 210/220 addition or absent-observation zeros."""
    expected = {
        "dengue_notifications_count",
        "dengue_grave_notifications_count",
        "total_notifications_count",
    }
    if set(mapping) != expected or any(v not in frame for v in mapping.values()):
        raise ValueError("Exact authorized count mapping required")
    result = frame[KEYS].copy()
    for name, source in mapping.items():
        for lag in (1, 2, 3, 12):
            result[f"{name}_lag{lag}"] = lagged(frame, source, lag)
    return result


def comparison_masks(
    frame: pd.DataFrame,
    labels: pd.DataFrame,
    features: pd.DataFrame,
    year: int,
    horizon: int,
    *,
    labels_admitted: bool,
) -> dict[str, dict[str, pd.Series]]:
    """Executable paired populations by temporal role; unresolved labels yield no final rows."""
    roles = temporal_roles(frame, year, horizon)
    eligible = labels[f"eligible_T{horizon}"].copy() & labels_admitted
    result = {}
    for role in ["train", "calibration", "embargo", "selection", "evaluation"]:
        base = eligible & roles.eq(role) & geographic_mask(frame, "FULL_COMMON", role)
        target = (pd.PeriodIndex(frame.periodo_mes, freq="M") + horizon).year
        water = (
            base
            & features["fraccion_agua_superficial_pct_area_observada__lag1"].notna()
            & (target <= 2021)
        )
        rain = [
            c
            for c in features
            if c.startswith(
                (
                    "precipitacion_chirps",
                    "racha_seca_chirps",
                    "precipitacion_total_mm__",
                    "precipitacion_max_diaria_mm__",
                    "racha_seca_max_dias__",
                )
            )
        ]
        era5 = base & features[rain].notna().all(axis=1)
        transfer = (
            eligible & roles.eq(role) & geographic_mask(frame, "TRANSFER_EXCLUDE_META_TOLIMA", role)
        )
        result[role] = {
            "FULL_COMMON": base,
            "WATER_REFERENCE": water,
            "FULL_PLUS_SURFACE_WATER": water.copy(),
            "ERA5_REFERENCE": era5,
            "FULL_ERA5_PRECIPITATION": era5.copy(),
            "TRANSFER_EXCLUDE_META_TOLIMA": transfer,
        }
    return result
