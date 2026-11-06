"""Bounded cohort/exposure annex preparation; no features, scores or learning access."""

from __future__ import annotations

from typing import Any

import pandas as pd  # type: ignore[import-untyped]

from sat_dengue.data.exp_delta03 import KEYS, temporal_roles
from sat_dengue.data.exp_delta03_retrospective import row_hash


def prepare_cohorts(
    national: pd.DataFrame, memberships: pd.DataFrame, plan: dict[str, Any]
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    """Copy frozen national eligibility/onset keys; independently count observed exposure.

    Coverage-restricted water/ERA5 national cohorts and national X are deliberately
    pending. This preparation is not the executable evaluation-annex-v1 contract.
    """
    if national.empty or national.duplicated(KEYS).any():
        raise ValueError("Invalid national source keys")
    if not national.divipola_departamento.eq(national.divipola_municipio.str[:2]).all():
        raise ValueError("National source geography mismatch")
    cohorts, calendars, summaries = [], [], []
    primary = [c for c in plan["cells"] if c["variant"] == "FULL_COMMON"]
    if not primary:
        raise ValueError("Missing primary cells")
    for cell in primary:
        h, year = cell["horizon"], cell["year"]
        eligible, evaluable = national[f"g1_no_climate_t{h}"], national[f"y_evaluable_t{h}"]
        for flag in [eligible, evaluable]:
            if not flag.isin([True, False]).all():
                raise ValueError("Unknown eligibility/calendar flag")
        period = temporal_roles(national, year, h).eq("evaluation")
        # The observed ledger is independent of the eligible flag.
        monitored = national.loc[period & evaluable, KEYS + ["divipola_departamento"]].copy()
        chosen = national.loc[period & eligible, KEYS + ["divipola_departamento", f"onset_T{h}"]]
        chosen = chosen.rename(columns={f"onset_T{h}": "truth"}).copy()
        if not chosen.truth.isin([0, 1]).all():
            raise ValueError("Missing frozen onset label")
        if (
            not pd.MultiIndex.from_frame(chosen[KEYS])
            .isin(pd.MultiIndex.from_frame(monitored[KEYS]))
            .all()
        ):
            raise ValueError("Eligible cohort is outside observed calendar")
        chosen = chosen.sort_values(KEYS).reset_index(drop=True)
        monitored = monitored.sort_values(KEYS).reset_index(drop=True)
        original = memberships.loc[
            memberships.horizon.eq(h)
            & memberships.year.eq(year)
            & memberships.role.eq("evaluation")
            & memberships.primary
        ]
        regional = chosen.loc[chosen.divipola_departamento.isin(["50", "73"])]
        expected = cell["roles"]["evaluation"]["key_label_sha256"]
        if (
            row_hash(regional, KEYS + ["truth"]) != expected
            or row_hash(original, KEYS + ["truth"]) != expected
        ):
            raise ValueError("Annex changed original regional keys/labels")
        summaries.append(
            {
                "horizon": h,
                "year": year,
                "stratum": "stress2024" if year == 2024 else "development",
                "eligible_rows": len(chosen),
                "eligible_municipality_years": len(chosen) / 12,
                "monitored_rows": len(monitored),
                "monitored_municipality_years": len(monitored) / 12,
                "municipalities": int(chosen.divipola_municipio.nunique()),
                "key_label_sha256": row_hash(chosen, KEYS + ["truth"]),
                "monitored_keys_sha256": row_hash(monitored, KEYS),
                "regional_key_label_sha256": expected,
                "regional_correspondence": "EXACT",
            }
        )
        for rows in [chosen, monitored]:
            rows["horizon"], rows["year"] = h, year
            rows["target_month"] = (pd.PeriodIndex(rows.periodo_mes, freq="M") + h).astype(str)
        cohorts.append(chosen)
        calendars.append(monitored)
    return pd.concat(cohorts, ignore_index=True), pd.concat(calendars, ignore_index=True), summaries
