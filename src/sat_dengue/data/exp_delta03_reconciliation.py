"""Read-only scientific reconciliation calculations; no source or model admission."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.consolidation import normalize_code_series, parse_epi_date_series


def residence_onset_counts(raw: pd.DataFrame) -> pd.DataFrame:
    """Reproduce V2's residence/INI_SIN aggregation before its declared calendar join.

    Records are notifications, not unique patients or confirmed cases. Stream/event
    identity and immutable source admission are the caller's responsibility.
    """
    dept = normalize_code_series(raw.COD_DPTO_R, 2)
    mun = normalize_code_series(raw.COD_MUN_R, 3)
    code = (dept + mun).where(dept.ne("") & mun.ne(""), "")
    month = parse_epi_date_series(raw.INI_SIN).dt.strftime("%Y-%m").fillna("")
    return grouped_counts(code, month)


def grouped_counts(code: pd.Series, month: pd.Series) -> pd.DataFrame:
    """Aggregate supplied keys without filling absent municipality-months."""
    if not code.index.equals(month.index):
        raise ValueError("Unaligned notification keys")
    keys = pd.DataFrame({"municipality_code": code, "year_month": month})
    keys = keys.loc[code.ne("") & month.ne("")]
    return keys.groupby(["municipality_code", "year_month"]).size().rename("count").reset_index()


def observed_event_union(counts: dict[str, dict[tuple[str, str], int]]) -> pd.DataFrame:
    """Derive the entire observed key universe independently of any published fact.

    An absent event contributes zero only where the other stream has an observed
    record. No completely unobserved municipality-month is invented or admitted.
    """
    if set(counts) != {"210", "220"}:
        raise ValueError("Expected the two separate notification streams")
    if any(v <= 0 for stream in counts.values() for v in stream.values()):
        raise ValueError("Observed aggregate counts must be positive")
    keys = sorted(set(counts["210"]) | set(counts["220"]))
    return pd.DataFrame(
        [(*key, counts["210"].get(key, 0), counts["220"].get(key, 0)) for key in keys],
        columns=["municipality_code", "year_month", "notificados_210", "notificados_220"],
    )


def exact_parity(
    expected: pd.DataFrame, actual: pd.DataFrame, keys: list[str], values: list[str]
) -> dict[str, Any]:
    """Compare full key sets and values, retaining unmatched keys and null semantics."""
    if expected[keys].isna().any().any() or actual[keys].isna().any().any():
        raise ValueError("Missing reconciliation key")
    if expected.duplicated(keys).any() or actual.duplicated(keys).any():
        raise ValueError("Duplicate reconciliation key")
    joined = expected[keys + values].merge(
        actual[keys + values],
        on=keys,
        how="outer",
        suffixes=("_expected", "_actual"),
        indicator=True,
    )
    both = joined._merge.eq("both")
    mismatches = {}
    for column in values:
        a, b = joined[f"{column}_expected"], joined[f"{column}_actual"]
        same = a.eq(b).fillna(False) | (a.isna() & b.isna())
        mismatches[column] = int((both & ~same).sum())
    missing = int(joined._merge.eq("left_only").sum())
    extra = int(joined._merge.eq("right_only").sum())
    return {
        "expected_rows": len(expected),
        "actual_rows": len(actual),
        "common_keys": int(both.sum()),
        "expected_only": missing,
        "actual_only": extra,
        "value_mismatches": mismatches,
        "exact": not (missing or extra or any(mismatches.values())),
        "semantic_equivalence_inferred": False,
    }


def composition_audit(frame: pd.DataFrame, groups: pd.DataFrame) -> dict[str, Any]:
    """Audit annual compositional closure without choosing a predictive encoding."""
    if not frame.index.equals(groups.index) or groups.shape[1] != 5:
        raise ValueError("Expected aligned five-part audit composition")
    annual = pd.concat([frame[["divipola_municipio", "anio"]], groups], axis=1)
    keys = ["divipola_municipio", "anio"]
    if (annual.groupby(keys)[list(groups)].nunique(dropna=False) > 1).any().any():
        raise ValueError("MODIS values change within a municipality-year")
    annual = annual.drop_duplicates(keys)
    complete = annual[list(groups)].dropna()
    values = complete.to_numpy(dtype=float)
    total = complete.sum(axis=1)
    return {
        "annual_rows": len(annual),
        "complete_annual_rows": len(complete),
        "monthly_rows_not_independent_annual_observations": True,
        "parts": list(groups),
        "sum_min": None if complete.empty else float(total.min()),
        "sum_max": None if complete.empty else float(total.max()),
        "closure_tolerance_pct": 1e-4,
        "closure_failures": int(total.sub(100).abs().gt(1e-4).sum()),
        "bound_tolerance_pct": 1e-4,
        "negative_or_above_100_beyond_tolerance": int(
            ((values < -1e-4) | (values > 100 + 1e-4)).sum()
        ),
        "strict_boundary_roundoff_values": int(((values < 0) | (values > 100)).sum()),
        "zero_annual_values": {c: int(complete[c].eq(0).sum()) for c in groups},
        "centered_rank_tolerance": 1e-7,
        "centered_rank": 0
        if complete.empty
        else int(np.linalg.matrix_rank(values - values.mean(axis=0), tol=1e-7)),
        "coverage_by_year": [
            {
                "year": int(y),
                "municipalities": len(g),
                "complete": int(g[list(groups)].notna().all(axis=1).sum()),
            }
            for y, g in annual.groupby("anio", sort=True)
        ],
        "primary_disposition": "EXCLUDED_UNVERIFIED_VINTAGE",
        "mosaic": "separate audit part; no redistribution",
        "predictive_encoding_selected": False,
    }
