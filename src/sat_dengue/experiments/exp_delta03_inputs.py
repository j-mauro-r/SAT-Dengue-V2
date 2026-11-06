"""Pure materialization of verified shared-base views and separately bound outcome joins."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03 import KEYS, seasonal_anomaly, temporal_roles
from sat_dengue.data.exp_delta03_retrospective import static_features, view_projection


def role_inputs(
    prepared: dict[str, Any], plan: dict[str, Any], outcomes: pd.DataFrame
) -> dict[str, Any]:
    base, membership = prepared["base"], prepared["memberships"]
    labels = prepared["labels"]
    if outcomes.duplicated(KEYS + ["horizon"]).any():
        raise ValueError("Duplicate outcome-comparator join key")
    keys = pd.MultiIndex.from_frame(base[KEYS])
    if keys.has_duplicates:
        raise ValueError("Duplicate shared-base key")
    metadata = prepared["metadata"]
    cells = {}
    for cell in plan["cells"]:
        x = view_projection(base, cell, metadata["feature_contract"])
        parts = {}
        for role in ("train", "calibration", "selection", "evaluation"):
            flag = "primary" if cell["reference"] == "transfer_reference" else cell["reference"]
            rows = membership.loc[
                membership.horizon.eq(cell["horizon"])
                & membership.year.eq(cell["year"])
                & membership.role.eq(role)
                & membership[flag]
            ].copy()
            rows = rows.sort_values(KEYS).reset_index(drop=True)
            index = keys.get_indexer(pd.MultiIndex.from_frame(rows[KEYS]))
            if (index < 0).any():
                raise ValueError("A declared role key was lost")
            rows = rows.merge(
                labels[KEYS + ["horizon", "truth", "target_month"]],
                on=KEYS + ["horizon"],
                validate="many_to_one",
                how="left",
                suffixes=("", "_label"),
            )
            if not rows.truth.eq(rows.truth_label).all():
                raise ValueError("Labels/cohort correspondence changed")
            rows = rows.drop(columns="truth_label")
            rows = rows.merge(outcomes, on=KEYS + ["horizon"], validate="one_to_one", how="left")
            if rows.target_excess.isna().any() or not rows.truth.eq(rows.onset_truth).all():
                raise ValueError("Required distinct excess/onset source join unavailable")
            parts[role] = {"rows": rows, "X": x.iloc[index].reset_index(drop=True)}
        cells[cell["id"]] = parts
    return cells


def generated_outcomes(sources: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """A generated-only companion with actual H5 target excess, comparator and episode identity."""
    from sat_dengue.data.exp_delta03 import h5_labels

    native = sources["historical_panel"].rename(
        columns={"municipality_code": KEYS[0], "year_month": KEYS[1]}
    )
    regional = sources["baseline"].rename(
        columns={"municipality_code": KEYS[0], "year_month": KEYS[1]}
    )
    history = pd.concat(
        [regional.loc[regional.periodo_mes.lt("2011-06")], native], ignore_index=True
    )
    history = history.sort_values(KEYS).reset_index(drop=True)
    state = h5_labels(history, history.dengue_notifications_count)
    state["origin_count"] = history.dengue_notifications_count
    episodes = []
    for code, group in state.groupby(KEYS[0], sort=False):
        serial = 0
        previous = False
        for row in group.itertuples():
            excess = bool(pd.notna(row.excess) and row.excess == 1)
            if excess and not previous:
                serial += 1
            episodes.append(f"generated_{code}_{serial}" if excess else None)
            previous = excess
    state["episode_id"] = episodes
    lookup = state.set_index(KEYS)
    records = []
    for horizon in sources["contract"]["horizons"]:
        future = pd.MultiIndex.from_arrays(
            [
                state.divipola_municipio,
                (pd.PeriodIndex(state.periodo_mes, freq="M") + horizon).astype(str),
            ]
        )
        row = state[KEYS].copy()
        row["horizon"] = horizon
        row["onset_truth"] = state[f"onset_T{horizon}"]
        row["origin_count"] = state.origin_count
        row["origin_excess"] = state.excess
        row["target_excess"] = lookup.excess.reindex(future).to_numpy()
        row["target_p75"] = lookup.p75.reindex(future).to_numpy()
        row["episode_id"] = lookup.episode_id.reindex(future).to_numpy()
        records.append(row)
    return pd.concat(records, ignore_index=True), history


def generated_national_annex(
    sources: dict[str, Any],
    prepared: dict[str, Any],
    plan: dict[str, Any],
    outcomes: pd.DataFrame,
    history: pd.DataFrame,
) -> dict[str, Any]:
    """Additional generated evaluation only; never relabel the original regional cohort."""
    full = sources["frame"]
    ordinary, manifest = static_features(full, history, sources["contract"])
    native = sources["historical_panel"].rename(
        columns={"municipality_code": KEYS[0], "year_month": KEYS[1]}
    )
    base = native[KEYS].merge(full, on=KEYS, validate="one_to_one")
    base = base.sort_values(KEYS).reset_index(drop=True)
    values = base[KEYS].merge(ordinary, on=KEYS, validate="one_to_one")
    members = prepared["memberships"]
    result = {}
    base_keys = pd.MultiIndex.from_frame(base[KEYS])
    for cell in plan["cells"]:
        if cell["reference"] == "transfer":
            continue
        flag = "primary" if cell["reference"] == "transfer_reference" else cell["reference"]
        train = members.loc[
            members.horizon.eq(cell["horizon"])
            & members.year.eq(cell["year"])
            & members.role.eq("train")
            & members[flag],
            KEYS,
        ]
        train_mask = pd.Series(base_keys.isin(pd.MultiIndex.from_frame(train)), index=base.index)
        anomaly = seasonal_anomaly(
            base,
            values.ndvi_medio__lag1,
            train_mask,
            national_reference=cell["reference"] == "transfer_reference",
        )
        physical = f"ndvi_anomaly__h{cell['horizon']}_y{cell['year']}_{cell['reference']}"
        projected = values.copy()
        projected[physical] = anomaly
        x = view_projection(projected, cell, manifest)
        outcome = base[KEYS].merge(
            outcomes.loc[outcomes.horizon.eq(cell["horizon"])], on=KEYS, validate="one_to_one"
        )
        eligible = native.set_index(KEYS)[f"g1_no_climate_t{cell['horizon']}"]
        mask = eligible.reindex(base_keys).to_numpy() & temporal_roles(
            base, cell["year"], cell["horizon"]
        ).eq("evaluation")
        if cell["reference"] == "water":
            mask &= values.fraccion_agua_superficial_pct_area_observada__lag1.notna()
        if cell["reference"] == "era5":
            rain = [
                f["name"]
                for f in manifest
                if f["block"] == "ERA5_PRECIPITATION"
                or str(f["source"]).startswith(("precipitacion_chirps", "racha_seca_chirps"))
            ]
            mask &= values[rain].notna().all(axis=1)
        rows = base.loc[mask, KEYS + ["divipola_departamento"]].merge(
            outcome, on=KEYS, validate="one_to_one"
        )
        rows["truth"] = rows.onset_truth
        rows["target_month"] = (
            pd.PeriodIndex(rows.periodo_mes, freq="M") + cell["horizon"]
        ).astype(str)
        rows = rows.sort_values(KEYS).reset_index(drop=True)
        positions = base_keys.get_indexer(pd.MultiIndex.from_frame(rows[KEYS]))
        result[cell["id"]] = {"rows": rows, "X": x.iloc[positions].reset_index(drop=True)}
    return result


def validate_national_annex(
    cell: dict[str, Any], part: dict[str, Any], expected: dict[str, Any], original: pd.DataFrame
) -> None:
    """Additional evaluation has its own full identity plus unchanged regional correspondence."""
    from sat_dengue.data.exp_delta03_retrospective import row_hash, values_hash

    rows, x = part["rows"], part["X"]
    validate_bound_outcomes(rows)
    if rows.empty or rows.duplicated(KEYS).any() or not rows.index.equals(x.index):
        raise ValueError("Invalid national annex alignment")
    if not rows[KEYS].equals(rows[KEYS].sort_values(KEYS).reset_index(drop=True)):
        raise ValueError("National annex rows must have canonical feature alignment")
    if list(x) != cell["columns"] or any(not pd.api.types.is_numeric_dtype(t) for t in x.dtypes):
        raise ValueError("National annex predictor schema changed")
    if np.isinf(x.to_numpy(dtype=float)).any():
        raise ValueError("Infinite national annex predictor")
    if not temporal_roles(rows, cell["year"], cell["horizon"]).eq("evaluation").all():
        raise ValueError("National annex is outside frozen evaluation period")
    if not rows.horizon.eq(cell["horizon"]).all() or not rows.truth.isin([0, 1]).all():
        raise ValueError("National annex horizon/outcome changed")
    if not rows.target_month.eq(
        (pd.PeriodIndex(rows.periodo_mes, freq="M") + cell["horizon"]).astype(str)
    ).all():
        raise ValueError("National annex target month differs")
    if not rows.divipola_departamento.eq(rows.divipola_municipio.str[:2]).all():
        raise ValueError("National annex geography mismatch")
    actual = {
        "rows": len(rows),
        "key_label_sha256": row_hash(rows, KEYS + ["truth"]),
        "X_sha256": values_hash(x),
    }
    if actual != expected:
        raise ValueError("Full national evaluation cohort identity changed")
    regional = rows.divipola_departamento.isin(["50", "73"])
    regional_identity = cell["roles"]["evaluation"]
    if (
        row_hash(rows.loc[regional], KEYS + ["truth"]) != regional_identity["key_label_sha256"]
        or values_hash(x.loc[regional]) != regional_identity["X_sha256"]
    ):
        raise ValueError("National annex changed frozen regional correspondence")
    columns = KEYS + [
        "horizon",
        "target_month",
        "truth",
        "onset_truth",
        "target_excess",
        "episode_id",
        "origin_count",
        "origin_excess",
        "target_p75",
    ]
    left = rows.loc[regional, columns].sort_values(KEYS).reset_index(drop=True)
    right = original[columns].sort_values(KEYS).reset_index(drop=True)
    for values in [left, right]:
        for column in [
            "horizon",
            "truth",
            "onset_truth",
            "target_excess",
            "origin_count",
            "origin_excess",
            "target_p75",
        ]:
            values[column] = values[column].astype(float)
        values["episode_id"] = values.episode_id.astype("string")
    if not left.equals(right):
        raise ValueError("National annex changed frozen regional outcome/comparator correspondence")


def validate_calendar(rows: pd.DataFrame) -> None:
    keys = KEYS + ["horizon"]
    if rows.empty or rows.duplicated(keys).any() or rows[keys].isna().any().any():
        raise ValueError("Invalid monitored calendar grain")
    if (
        not rows.horizon.isin([1, 2]).all()
        or not rows.divipola_departamento.eq(rows.divipola_municipio.str[:2]).all()
    ):
        raise ValueError("Invalid monitored calendar horizon/geography")
    target = (pd.PeriodIndex(rows.periodo_mes, freq="M") + rows.horizon.to_numpy()).astype(str)
    if not rows.target_month.eq(target).all():
        raise ValueError("Monitored calendar target mismatch")
    for column in ["coverage_water", "coverage_era5"]:
        if not rows[column].isin([True, False]).all():
            raise ValueError("Invalid monitored calendar coverage flag")


def validate_bound_outcomes(rows: pd.DataFrame) -> None:
    """Onset truth cannot substitute excess, episodes or origin-safe comparator inputs."""
    for column in ["truth", "onset_truth", "target_excess", "origin_excess"]:
        if not rows[column].isin([0, 1]).all():
            raise ValueError("Invalid bound binary onset/excess outcome")
    if (
        not rows.truth.eq(rows.onset_truth).all()
        or (rows.truth.eq(1) & rows.target_excess.ne(1)).any()
    ):
        raise ValueError("Bound onset/excess outcome correspondence changed")
    if rows.loc[rows.target_excess.eq(1), "episode_id"].isna().any():
        raise ValueError("Missing excess episode identity")
    for column in ["origin_count", "target_p75"]:
        if (
            not pd.api.types.is_numeric_dtype(rows[column])
            or not np.isfinite(rows[column]).all()
            or rows[column].lt(0).any()
        ):
            raise ValueError("Invalid bound comparator input")
