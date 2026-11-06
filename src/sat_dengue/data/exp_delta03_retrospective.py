"""Explicitly authorized consolidated-data preparation, never operational PIT or fitting."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03 import (
    KEYS,
    block_views,
    geographic_mask,
    h5_labels,
    historical_window,
    lagged,
    land_cover,
    seasonal_anomaly,
    temporal_roles,
)
from sat_dengue.data.exp_delta03_reconciliation import exact_parity

REGIME = "RETROSPECTIVE_CONSOLIDATED"
ROLES = ["train", "calibration", "embargo", "selection", "evaluation"]
REQUIRED_ROLES = ["train", "calibration", "selection", "evaluation"]


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def row_hash(frame: pd.DataFrame, columns: list[str]) -> str:
    rows = frame[columns].sort_values(KEYS).copy()
    if "truth" in rows:
        rows["truth"] = rows.truth.astype("Int64")
    return hashlib.sha256(rows.to_csv(index=False, lineterminator="\n").encode()).hexdigest()


def values_hash(frame: pd.DataFrame) -> str:
    """Stable numeric view identity; missing values stay missing, signed zeros agree."""
    array = frame.to_numpy(dtype="float64", copy=True)
    if np.isinf(array).any():
        raise ValueError("Infinite matrix value")
    array[np.isnan(array)] = np.nan
    array[array == 0] = 0.0
    body = canonical({"columns": list(frame), "shape": list(array.shape), "dtype": "<f8"})
    return hashlib.sha256(body + array.astype("<f8").tobytes(order="C")).hexdigest()


def annual_previous(frame: pd.DataFrame, source: str) -> pd.Series:
    """Exact previous observation year, not a released vintage or older-year fill."""
    if frame.groupby(["divipola_municipio", "year"])[source].nunique(dropna=False).gt(1).any():
        raise ValueError("Annual source changes within its observation year: " + source)
    lookup = frame.set_index(KEYS)[source]
    keys = pd.MultiIndex.from_arrays(
        [frame.divipola_municipio, (frame.year - 1).astype(str) + "-12"]
    )
    return pd.Series(lookup.reindex(keys).to_numpy(), index=frame.index, dtype="float64")


def static_features(
    frame: pd.DataFrame, history: pd.DataFrame, contract: dict[str, Any]
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Event-time causal values from admitted consolidated snapshots, with honest status."""
    result = frame[KEYS].copy()
    manifest: list[dict[str, Any]] = []

    def add(name: str, source: str, block: str, values: pd.Series, event: str) -> None:
        result[name] = values.to_numpy(dtype="float64", na_value=np.nan)
        manifest.append(
            {
                "name": name,
                "source": source,
                "block": block,
                "event_rule": event,
                "available_at_guard": False,
                "vintage_status": "RETROSPECTIVE_ONLY",
                "decision": "included_authorized_retrospective",
                "dtype": "float64",
            }
        )

    for name, values in [
        ("month_sin", np.sin(2 * np.pi * frame.month / 12)),
        ("month_cos", np.cos(2 * np.pi * frame.month / 12)),
    ]:
        add(name, "periodo_mes", "CALENDAR", values, "known origin month")
        manifest[-1]["vintage_status"] = "VERIFIED_POINT_IN_TIME"
        manifest[-1]["available_at_guard"] = True
    for block in ["THERMAL_HUMIDITY", "RAINFALL_HYDROLOGY", "NDVI"]:
        spec = contract["blocks"][block]
        for source in spec["sources"]:
            add(source + "__lag1", source, block, lagged(frame, source, 1), "T-1")
        for operation in ["mean3", "sum3", "max3"]:
            for source in spec.get(operation, []):
                operator = operation[:-1]
                add(
                    source + "__" + operator,
                    source,
                    block,
                    historical_window(frame, source, operator),
                    "all of T-3..T-1",
                )
    add(
        "oni_3m_c__lag2",
        "oni_3m_c",
        "ENSO",
        lagged(frame, "oni_3m_c", 2),
        "central T-2 observes T-3..T-1; no historical release claim",
    )
    add(
        "ndvi_change",
        "ndvi_medio",
        "NDVI",
        lagged(frame, "ndvi_medio", 1) - lagged(frame, "ndvi_medio", 2),
        "T-1 minus T-2",
    )
    for source in ["precipitacion_total_mm", "precipitacion_max_diaria_mm", "racha_seca_max_dias"]:
        add(source + "__lag1", source, "ERA5_PRECIPITATION", lagged(frame, source, 1), "T-1")
    for source, operator in [("precipitacion_total_mm", "sum"), ("racha_seca_max_dias", "max")]:
        add(
            source + "__" + operator,
            source,
            "ERA5_PRECIPITATION",
            historical_window(frame, source, operator),
            "all of T-3..T-1",
        )
    water_source = "fraccion_agua_superficial_pct_area_observada"
    water = lagged(frame, water_source, 1).where(lagged(frame, "area_observada_m2", 1).gt(0))
    observation = pd.PeriodIndex(frame.periodo_mes, freq="M") - 1
    water = water.where(observation <= pd.Period("2021-12", freq="M"))
    add(
        water_source + "__lag1",
        water_source,
        "SURFACE_WATER",
        water,
        "genuinely observed T-1 <=2021-12; no target-year proxy or later-year fill",
    )
    for source in contract["blocks"]["TERRAIN"]["sources"]:
        if frame.groupby("divipola_municipio")[source].nunique(dropna=False).gt(1).any():
            raise ValueError("Static terrain source changed")
        add(
            source + "__asof",
            source,
            "TERRAIN",
            frame[source],
            "fixed retrospective measurement/current geometry; not historical boundary proof",
        )
    for source in contract["blocks"]["DEMOGRAPHY"]["sources"]:
        values = annual_previous(frame, source)
        if source in contract["blocks"]["DEMOGRAPHY"].get("log1p", []):
            if values.dropna().lt(0).any():
                raise ValueError("Negative demographic log input")
            values = np.log1p(values)
        add(
            source + "__asof",
            source,
            "DEMOGRAPHY",
            values,
            "exact previous calendar observation year, consolidated vintage; no backfill",
        )
    history_lookup = history.set_index(KEYS)
    for source in contract["history_source_mapping"]:
        for offset in contract["history_lags"]:
            keys = pd.MultiIndex.from_arrays(
                [
                    frame.divipola_municipio,
                    (pd.PeriodIndex(frame.periodo_mes, freq="M") - offset).astype(str),
                ]
            )
            values = pd.Series(history_lookup[source].reindex(keys).to_numpy(), index=frame.index)
            add(
                f"{source}_lag{offset}",
                "historical:" + source,
                "HISTORY",
                values,
                f"authorized V2 source T-{offset}; no new-mart count substitution",
            )
    composition = land_cover(frame, contract)
    for group in contract["blocks"]["LAND_COVER"]["predictors"]:
        temporary = frame[KEYS + ["year"]].copy()
        temporary[group] = composition[group]
        add(
            "land_" + group,
            group,
            "LAND_COVER",
            annual_previous(temporary, group),
            "exact previous complete observation year; bare_other reference omitted",
        )
    manifest.append(
        {
            "name": "ndvi_anomaly",
            "source": "ndvi_medio",
            "block": "NDVI",
            "event_rule": "lag1 minus this cell/population training-only seasonal reference",
            "available_at_guard": False,
            "vintage_status": "RETROSPECTIVE_ONLY",
            "decision": "included_authorized_retrospective",
            "dtype": "float64",
        }
    )
    return result, manifest


def view_projection(
    base: pd.DataFrame, descriptor: dict[str, Any], feature_manifest: list[dict[str, Any]]
) -> pd.DataFrame:
    """Closed X-only projection; IDs, labels and another fold's reference cannot enter."""
    logical, physical = descriptor["columns"], descriptor["physical_columns"]
    if len(logical) != len(set(logical)) or len(logical) != len(physical):
        raise ValueError("Invalid predictor selector")
    for name, stored in zip(logical, physical, strict=True):
        if name in {
            *KEYS,
            "year",
            "month",
            "role",
            "truth",
            "horizon",
            "excess",
        } or name.startswith(
            (
                "onset_",
                "target_",
                "eligible_",
                "notificados_",
                "estado_cobertura_",
                "ndvi_anomaly__",
            )
        ):
            raise ValueError("Forbidden predictor")
        expected = (
            f"ndvi_anomaly__h{descriptor['horizon']}_y{descriptor['year']}_{descriptor['reference']}"
            if name == "ndvi_anomaly"
            else name
        )
        if stored != expected or stored in KEYS:
            raise ValueError("Cross-fold or undeclared physical predictor")
    variant = descriptor["variant"]
    references = {
        "WATER_REFERENCE": "water",
        "ERA5_REFERENCE": "era5",
        "TRANSFER_REFERENCE": "transfer_reference",
    }
    expected_reference = references.get(
        variant,
        {
            "FULL_PLUS_SURFACE_WATER": "water",
            "FULL_ERA5_PRECIPITATION": "era5",
            "TRANSFER_EXCLUDE_META_TOLIMA": "transfer",
        }.get(variant, "primary"),
    )
    if descriptor["reference"] != expected_reference:
        raise ValueError("Undeclared reference population")
    allowed = {
        "HISTORY",
        "FULL_COMMON",
        "FULL_PLUS_SURFACE_WATER",
        "FULL_ERA5_PRECIPITATION",
        "TRANSFER_EXCLUDE_META_TOLIMA",
        *references,
        *(
            "FULL_MINUS_" + b
            for b in [
                "THERMAL_HUMIDITY",
                "RAINFALL_HYDROLOGY",
                "NDVI",
                "TERRAIN",
                "LAND_COVER",
                "DEMOGRAPHY",
            ]
        ),
    }
    if variant not in allowed:
        raise ValueError("Undeclared ablation variant")
    selection = "FULL_COMMON" if variant in references else variant
    if logical != block_views(feature_manifest, [selection])[selection]:
        raise ValueError("Predictor selector violates declared variant contract")
    result = base[physical].copy()
    result.columns = logical
    return result


def prepare_retrospective(sources: dict[str, Any]) -> dict[str, Any]:
    """Build one shared base and verified logical views, with no estimator invocation."""
    contract = sources["contract"]
    approval = contract.get("retrospective_preparation", {})
    if (
        contract.get("preparation_regime") != REGIME
        or approval.get("status") != "APPROVED"
        or not sources.get("retrospective_verification", {}).get("verified")
    ):
        raise ValueError("Explicit verified retrospective preparation authorization required")
    if contract["blocks"]["LAND_COVER"]["predictors"] != [
        "natural_vegetation",
        "agriculture",
        "urban",
        "mosaic_unassigned",
    ]:
        raise ValueError("Unapproved MODIS predictive composition")
    native = sources["historical_panel"].copy()
    prior = sources["baseline"].loc[sources["baseline"].year_month.lt("2011-06")].copy()
    rename = {"municipality_code": "divipola_municipio", "year_month": "periodo_mes"}
    counts = [
        "dengue_notifications_count",
        "dengue_grave_notifications_count",
        "total_notifications_count",
    ]
    history = pd.concat(
        [
            prior[["municipality_code", "year_month", *counts]],
            native[["municipality_code", "year_month", *counts]],
        ],
        ignore_index=True,
    )
    history = history.rename(columns=rename).sort_values(KEYS).reset_index(drop=True)
    if (
        history.duplicated(KEYS).any()
        or not history.total_notifications_count.eq(
            history.dengue_notifications_count + history.dengue_grave_notifications_count
        ).all()
    ):
        raise ValueError("Historical count identity mismatch")
    outcomes = h5_labels(history, history.dengue_notifications_count)
    expected = native.rename(columns=rename)
    actual = outcomes.rename(columns={"p75": "p75_canal_t"})
    actual = actual.loc[actual.periodo_mes.ge("2011-06")]
    native_parity = exact_parity(expected, actual, KEYS, ["p75_canal_t", "onset_T1", "onset_T2"])
    if not native_parity["exact"]:
        raise ValueError("Historical national H5/onset parity failed")
    full_source = sources["frame"]
    base = expected[KEYS].merge(full_source, on=KEYS, how="left", validate="one_to_one")
    if len(base) != len(expected) or base.divipola_departamento.isna().any():
        raise ValueError("Historical cohort key absent from canonical source")
    base = base.sort_values(KEYS).reset_index(drop=True)
    label = base[KEYS].merge(outcomes, on=KEYS, how="left", validate="one_to_one")
    admitted = base[KEYS].merge(
        expected[KEYS + ["g1_no_climate_t1", "g1_no_climate_t2"]], on=KEYS, validate="one_to_one"
    )
    for h in contract["horizons"]:
        mask = admitted[f"g1_no_climate_t{h}"]
        if mask.isna().any() or not mask.isin([True, False]).all():
            raise ValueError("Unknown historical national cohort membership")
        if (mask & ~label[f"eligible_T{h}"]).any():
            raise ValueError("Historical eligibility contradicts reconstructed H5")
        label[f"eligible_T{h}"] = mask.astype(bool)
    full_features, manifest = static_features(full_source, history, contract)
    features = base[KEYS].merge(full_features, on=KEYS, how="left", validate="one_to_one")
    selectors = block_views(manifest, contract["variants"])
    memberships, views, reference_records, frozen_parity = [], [], [], []
    cell_masks: dict[tuple[int, int], dict[str, dict[str, pd.Series]]] = {}
    for h in contract["horizons"]:
        for year in contract["evaluation_years"]:
            role = temporal_roles(base, year, h)
            eligible = label[f"eligible_T{h}"]
            masks = {}
            rain = [
                m["name"]
                for m in manifest
                if m["block"] == "ERA5_PRECIPITATION"
                or str(m["source"]).startswith(("precipitacion_chirps", "racha_seca_chirps"))
            ]
            for name in ROLES:
                # Frozen V2 expands TRAINING only; calibration/selection/evaluation
                # retain the exact regional populations. Transfer is the explicit
                # whole-procedure territorial exception, evaluated on the same MT keys.
                target = base.divipola_departamento.isin(["50", "73"])
                primary_geo = pd.Series(True, index=base.index) if name == "train" else target
                primary = eligible & role.eq(name) & primary_geo
                masks[name] = {
                    "primary": primary,
                    "water": primary
                    & features["fraccion_agua_superficial_pct_area_observada__lag1"].notna(),
                    "era5": primary & features[rain].notna().all(axis=1),
                    "transfer_reference": primary.copy(),
                    "transfer": eligible
                    & role.eq(name)
                    & geographic_mask(base, "TRANSFER_EXCLUDE_META_TOLIMA", name),
                }
                union = primary | masks[name]["transfer"]
                rows = base.loc[union, KEYS + ["divipola_departamento"]].copy()
                rows["horizon"], rows["year"], rows["role"] = h, year, name
                rows["truth"] = label.loc[union, f"onset_T{h}"].astype("Int64")
                for population in ["primary", "water", "era5", "transfer"]:
                    rows[population] = masks[name][population].loc[union].to_numpy()
                memberships.append(rows)
            cell_masks[(h, year)] = masks
            for population in ["primary", "water", "era5", "transfer_reference", "transfer"]:
                supported = all(masks[r][population].any() for r in REQUIRED_ROLES)
                if not supported:
                    continue
                column = f"ndvi_anomaly__h{h}_y{year}_{population}"
                anomaly = seasonal_anomaly(
                    base,
                    features.ndvi_medio__lag1,
                    masks["train"][population],
                    national_reference=population in ["transfer", "transfer_reference"],
                    exclude_targets=population == "transfer",
                )
                features[column] = anomaly
                reference_records.append(
                    {
                        "horizon": h,
                        "year": year,
                        "population": population,
                        "training_rows": int(masks["train"][population].sum()),
                        "training_keys_sha256": row_hash(
                            base.loc[masks["train"][population]], KEYS
                        ),
                        "column": column,
                        "observed_training_month_support": {
                            str(month): int(count)
                            for month, count in base.loc[
                                masks["train"][population] & features.ndvi_medio__lag1.notna()
                            ]
                            .groupby("month")
                            .size()
                            .items()
                        },
                        "held_out_target_statistics": False,
                    }
                )
    membership = pd.concat(memberships, ignore_index=True)
    if membership.truth.isna().any() or not membership.truth.isin([0, 1]).all():
        raise ValueError("Unavailable outcome entered a cohort")
    for frozen in sources["frozen_cohorts"]:
        selected = membership.loc[
            membership.horizon.eq(frozen["horizon"])
            & membership.year.eq(frozen["year"])
            & membership.role.eq(frozen["role"])
            & membership.primary
        ]
        expected_frozen = frozen["frame"].rename(columns=rename)
        report = exact_parity(expected_frozen, selected, KEYS, ["truth"])
        frozen_parity.append(
            {
                "control": frozen["control"],
                "horizon": frozen["horizon"],
                "year": frozen["year"],
                "role": frozen["role"],
                **report,
            }
        )
    if len(frozen_parity) != 40 or not all(p["exact"] for p in frozen_parity):
        raise ValueError("Complete frozen selection/evaluation cohort parity failed")
    training_parity = []
    if len(sources["training_controls"]) != 8:
        raise ValueError("Incomplete frozen national training controls")
    for control in sources["training_controls"]:
        cell = membership.loc[
            membership.horizon.eq(control["horizon"])
            & membership.year.eq(control["year"])
            & membership.primary
        ]
        train = cell.loc[cell.role.eq("train"), KEYS].rename(
            columns={"divipola_municipio": "municipality_code", "periodo_mes": "year_month"}
        )
        digest = hashlib.sha256(
            train.to_csv(index=False, na_rep="", lineterminator="\n", float_format="%.17g").encode()
        ).hexdigest()
        if digest != control["audit"]["train_keys_sha256"]:
            raise ValueError("Frozen national training keys changed")
        for role in ROLES:
            regional = cell.loc[cell.role.eq(role) & cell.divipola_departamento.isin(["50", "73"])]
            old_role = "adaptation" if role == "embargo" else role
            if len(regional) != control["audit"]["regional_role_audit"][old_role]["rows"]:
                raise ValueError("Frozen regional role membership changed")
            expected_role = control["audit"]["regional_role_audit"][old_role]
            actual_bounds = {
                "origin_start": str(regional.periodo_mes.min()),
                "origin_end": str(regional.periodo_mes.max()),
                "municipalities": int(regional.divipola_municipio.nunique()),
            }
            if any(
                actual_bounds[k] != expected_role[k] for k in actual_bounds if k in expected_role
            ):
                raise ValueError("Frozen regional role boundaries changed")
        training_parity.append(
            {
                "horizon": control["horizon"],
                "year": control["year"],
                "train_keys_sha256": digest,
                "exact": True,
            }
        )
    # Physically retain only the union consumed by declared views, without changing any cohort.
    keys = pd.MultiIndex.from_frame(membership[KEYS].drop_duplicates())
    used = pd.MultiIndex.from_frame(features[KEYS]).isin(keys)
    features = features.loc[used].reset_index(drop=True)
    label = label.loc[used].reset_index(drop=True)
    labels = []
    for h in contract["horizons"]:
        required = membership.loc[membership.horizon.eq(h), KEYS].drop_duplicates()
        rows = required.merge(label[KEYS + [f"onset_T{h}"]], on=KEYS, validate="one_to_one")
        rows = rows.rename(columns={f"onset_T{h}": "truth"})
        rows["truth"] = rows.truth.astype("Int64")
        rows["horizon"] = h
        rows["target_month"] = (pd.PeriodIndex(rows.periodo_mes, freq="M") + h).astype(str)
        labels.append(rows)
    target_table = pd.concat(labels, ignore_index=True)
    if features.drop(columns=KEYS).isna().all().any() or target_table.truth.isna().any():
        raise ValueError("All-null predictor or unauthorized/missing target")
    base_keys = pd.MultiIndex.from_frame(features[KEYS])
    for (h, year), masks in cell_masks.items():
        variants = [(name, "primary") for name in contract["variants"]]
        variants += [
            ("WATER_REFERENCE", "water"),
            ("ERA5_REFERENCE", "era5"),
            ("TRANSFER_REFERENCE", "transfer_reference"),
        ]
        for variant, population in variants:
            population = {
                "FULL_PLUS_SURFACE_WATER": "water",
                "FULL_ERA5_PRECIPITATION": "era5",
                "TRANSFER_EXCLUDE_META_TOLIMA": "transfer",
            }.get(variant, population)
            columns = selectors.get(variant, selectors["FULL_COMMON"])
            descriptor = {
                "id": f"h{h}_y{year}_{variant}",
                "variant": variant,
                "horizon": h,
                "year": year,
                "reference": population,
                "columns": columns,
                "physical_columns": [
                    f"ndvi_anomaly__h{h}_y{year}_{population}" if c == "ndvi_anomaly" else c
                    for c in columns
                ],
                "availability_regime": REGIME,
                "operational_PIT": False,
                "evidence_type": "consumed_retrospective_stress"
                if year == 2024
                else "consumed_retrospective",
                "comparison_row_weight": 1,
                "base_file": "prepared_features.csv",
                "roles": {},
            }
            if not all(masks[r][population].any() for r in REQUIRED_ROLES):
                if population != "water":
                    raise ValueError("Required non-water comparison has no cohort support")
                descriptor.update(
                    status="UNAVAILABLE_GENUINE_SOURCE_COVERAGE",
                    reason=(
                        "No common genuine support in every required role; "
                        "no matrix or zero metrics"
                    ),
                    support_by_role={r: int(masks[r][population].sum()) for r in ROLES},
                )
                views.append(descriptor)
                continue
            projected = view_projection(features, descriptor, manifest)
            for role in ROLES:
                chosen = membership.loc[
                    membership.horizon.eq(h) & membership.year.eq(year) & membership.role.eq(role)
                ].copy()
                flag = "primary" if population == "transfer_reference" else population
                chosen = chosen.loc[chosen[flag]]
                positions = base_keys.get_indexer(pd.MultiIndex.from_frame(chosen[KEYS]))
                if (positions < 0).any():
                    raise ValueError("A declared cohort key was lost from physical base")
                x = projected.iloc[positions]
                if role == "train" and (x.empty or x.isna().all().any()):
                    raise ValueError("Empty training population or all-null predictor")
                descriptor["roles"][role] = {
                    "rows": len(chosen),
                    "onsets": int(chosen.truth.sum()),
                    "key_sha256": row_hash(chosen, KEYS),
                    "key_label_sha256": row_hash(chosen, KEYS + ["truth"]),
                    "X_sha256": values_hash(x),
                }
            descriptor["status"] = "MATERIALIZABLE_RETROSPECTIVE"
            views.append(descriptor)
    return {
        "base": features,
        "labels": target_table,
        "memberships": membership,
        "feature_manifest": manifest,
        "views": views,
        "references": reference_records,
        "historical_parity": {
            "national": native_parity,
            "frozen_cells": frozen_parity,
            "national_training_keys": training_parity,
        },
        "availability_regime": REGIME,
        "operational_PIT": False,
    }


def validate_materialized_tables(
    base: pd.DataFrame,
    labels: pd.DataFrame,
    membership: pd.DataFrame,
    views: list[dict[str, Any]],
    feature_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    """Recheck reopened stored tables and every logical view without fitting anything."""
    if (
        base.duplicated(KEYS).any()
        or labels.duplicated(KEYS + ["horizon"]).any()
        or membership.duplicated(KEYS + ["horizon", "year", "role"]).any()
    ):
        raise ValueError("Duplicate materialized key")
    if labels.truth.isna().any() or not labels.truth.isin([0, 1]).all():
        raise ValueError("Unavailable or nonbinary materialized label")
    target = pd.PeriodIndex(labels.periodo_mes, freq="M") + labels.horizon.to_numpy()
    if (target.year >= 2025).any():
        raise ValueError("Consumed 2025 entered final labels")
    joined = membership.merge(
        labels[KEYS + ["horizon", "truth"]],
        on=KEYS + ["horizon"],
        how="left",
        validate="many_to_one",
        suffixes=("", "_label"),
    )
    if joined.truth_label.isna().any() or not joined.truth.eq(joined.truth_label).all():
        raise ValueError("Role/label correspondence changed")
    if base.drop(columns=KEYS).isna().all().any():
        raise ValueError("All-null physical predictor")
    base_keys = pd.MultiIndex.from_frame(base[KEYS])
    lookup = {}
    for descriptor in views:
        lookup[(descriptor["horizon"], descriptor["year"], descriptor["variant"])] = descriptor
        if descriptor["status"] != "MATERIALIZABLE_RETROSPECTIVE":
            if descriptor["reference"] != "water":
                raise ValueError("Unexpected unavailable primary comparison")
            continue
        x = view_projection(base, descriptor, feature_manifest)
        for role, expected in descriptor["roles"].items():
            rows = membership.loc[
                membership.horizon.eq(descriptor["horizon"])
                & membership.year.eq(descriptor["year"])
                & membership.role.eq(role)
            ]
            population = descriptor["reference"]
            flag = "primary" if population == "transfer_reference" else population
            rows = rows.loc[rows[flag]]
            positions = base_keys.get_indexer(pd.MultiIndex.from_frame(rows[KEYS]))
            if (positions < 0).any():
                raise ValueError("Declared member missing from stored matrix")
            actual = {
                "rows": len(rows),
                "onsets": int(rows.truth.sum()),
                "key_sha256": row_hash(rows, KEYS),
                "key_label_sha256": row_hash(rows, KEYS + ["truth"]),
                "X_sha256": values_hash(x.iloc[positions]),
            }
            if actual != expected:
                raise ValueError("Reopened logical matrix identity changed")
            regional = rows.divipola_departamento.astype(str).str.zfill(2).isin(["50", "73"])
            if population == "transfer" and role != "evaluation" and regional.any():
                raise ValueError("Transfer learned a held-out territory")
            if population != "transfer" and role != "train" and not regional.all():
                raise ValueError("Frozen regional development/evaluation geography changed")
            if role == "evaluation" and not regional.all():
                raise ValueError("Nationwide evaluation is not authorized")
    for h in [1, 2]:
        for year in [2020, 2021, 2022, 2024]:
            for reference, variant in [
                ("WATER_REFERENCE", "FULL_PLUS_SURFACE_WATER"),
                ("ERA5_REFERENCE", "FULL_ERA5_PRECIPITATION"),
            ]:
                a, b = lookup[(h, year, reference)], lookup[(h, year, variant)]
                if a["status"] != b["status"]:
                    raise ValueError("Matched sensitivity availability differs")
                if a["status"] != "MATERIALIZABLE_RETROSPECTIVE":
                    continue
                for role in ROLES:
                    if a["roles"][role]["key_label_sha256"] != b["roles"][role]["key_label_sha256"]:
                        raise ValueError("Matched sensitivity population differs")
            a = lookup[(h, year, "TRANSFER_REFERENCE")]
            b = lookup[(h, year, "TRANSFER_EXCLUDE_META_TOLIMA")]
            if (
                a["roles"]["evaluation"]["key_label_sha256"]
                != b["roles"]["evaluation"]["key_label_sha256"]
            ):
                raise ValueError("Transfer evaluation population differs")
    return {
        "status": "PASS",
        "physical_base_rows": len(base),
        "labels": len(labels),
        "membership_rows": len(membership),
        "logical_views": sum(v["status"] == "MATERIALIZABLE_RETROSPECTIVE" for v in views),
        "unavailable_water_views": sum(
            v["status"] != "MATERIALIZABLE_RETROSPECTIVE" for v in views
        ),
        "operational_PIT": False,
        "fits": 0,
        "calibrations": 0,
        "mlflow_writes": 0,
    }
