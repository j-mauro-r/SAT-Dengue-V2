"""Independent count cohorts, calendar roles and strict frozen-reference pairing."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.canonical.table import CLIMATE, PREDICTORS, predictor_matrix
from sat_dengue.configuration import validate_parameters
from sat_dengue.experiments.onset import KEYS, labels, validate_keys


def prepare(sources: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
    """Project X separately from exact future counts and epidemiological controls."""
    if validate_parameters(parameters) != {"profile": "exp_beta02", "tracking": "disabled"}:
        raise ValueError("Beta02 requires its own profile and disabled tracking")
    protocol = sources["protocol"]
    if protocol["predictors"] != PREDICTORS or protocol["climate_predictors"] != CLIMATE:
        raise ValueError("Beta02 predictor allowlist changed")
    table = (
        sources["table"]
        .loc[sources["table"].year_month.lt(protocol["reserved_target_start"])]
        .copy()
    )
    validate_keys(table)
    matrix = predictor_matrix(table, sources["columns"])
    states = table[KEYS].copy()
    states["excess"] = table.zona_canal_t.eq("EXCESO").astype("Int64")
    states.loc[table.zona_canal_t.isna(), "excess"] = pd.NA
    counts = table.set_index(KEYS).dengue_notifications_count.to_dict()
    cohorts = {}
    for horizon in protocol["horizons"]:
        outcomes = labels(states, horizon)
        count = pd.Series(
            [
                counts.get((m, t), np.nan)
                for m, t in outcomes[["municipality_code", "target_month"]].itertuples(
                    index=False, name=None
                )
            ],
            index=table.index,
            dtype="Float64",
        )
        common = outcomes.eligible_at_t & outcomes.onset_target.notna() & matrix.notna().all(axis=1)
        common &= count.notna() & outcomes.target_month.lt(protocol["reserved_target_start"])
        frame = table.loc[common, [*KEYS, "department_code", *PREDICTORS]].copy()
        frame["count_target"] = count.loc[common].astype(float)
        for name in ("target_month", "onset_target"):
            frame[name] = outcomes.loc[common, name]
        frame["target_year"] = frame.target_month.str[:4].astype(int)
        frame["zona_canal_t"] = frame.zona_canal_t.map(
            {"EXITO": 0, "SEGURIDAD": 1, "ALERTA": 2, "EXCESO": 3}
        )
        if (
            frame[PREDICTORS].isna().any().any()
            or frame.count_target.lt(0).any()
            or frame.count_target.mod(1).ne(0).any()
        ):
            raise ValueError("Invalid count cohort")
        cohorts[horizon] = frame.sort_values(KEYS).reset_index(drop=True)
    return {
        **sources,
        "cohorts": cohorts,
        "provenance": {**sources["provenance"], "operational": parameters},
    }


def role_parts(frame: pd.DataFrame, year: int, protocol: dict[str, Any]) -> dict[str, Any]:
    """Common global cutoffs; no target crosses into a later fitted role."""
    if year not in protocol["evaluation_years"] or year >= 2025:
        raise ValueError("Unapproved Beta02 evaluation year")
    periods = {
        "train": (protocol["training_start"], f"{year - 2}-12"),
        "selection": (f"{year - 1}-01", f"{year - 1}-12"),
        "evaluation": (f"{year}-01", f"{year}-12"),
    }
    parts, audit, previous = {}, {}, None
    for role, (start, end) in periods.items():
        if role != "evaluation" and end >= "2024-01":
            raise ValueError("Stress cannot fit or select")
        mask = frame.target_month.between(start, end)
        before = int(mask.sum())
        if previous is not None:
            mask &= frame.year_month.ge(previous)
        part = frame.loc[mask].copy()
        if part.empty:
            raise ValueError(f"Missing Beta02 support: {role}/{year}")
        parts[role] = part
        audit[role] = {
            "target_start": start,
            "target_end": end,
            "rows": len(part),
            "origin_start": str(part.year_month.min()),
            "origin_end": str(part.year_month.max()),
            "embargo_excluded": before - len(part),
        }
        previous = end
    return {"parts": parts, "audit": audit}


def paired(base: pd.DataFrame, reference: Any, horizon: int, year: int) -> pd.DataFrame | None:
    """Require complete identical keys and truths; never substitute an intersection."""
    if reference is None:
        return None
    old = (
        reference.loc[reference.horizon.eq(horizon) & reference.target_month.str[:4].eq(str(year))]
        .rename(columns={"origin_month": "year_month"})
        .sort_values(KEYS)
        .reset_index(drop=True)
    )
    current = base.sort_values(KEYS).reset_index(drop=True)
    if (
        old.duplicated(KEYS).any()
        or len(old) != len(current)
        or old[KEYS].to_records(index=False).tolist()
        != current[KEYS].to_records(index=False).tolist()
        or old.truth.astype(int).tolist() != current.onset_target.astype(int).tolist()
        or old.target_month.tolist() != current.target_month.tolist()
    ):
        return None
    if not np.isfinite(old.score).all() or not old.score.between(0, 1).all():
        raise ValueError("Invalid frozen reference probabilities")
    return old
