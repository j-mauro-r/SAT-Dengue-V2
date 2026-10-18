from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

TARGET_DEPTS = {"50": "Meta", "73": "Tolima"}
CLIMATE_VARS = [
    "rain_mm_day",
    "temp_mean_c",
    "dewpoint_mean_c",
    "soil_water_l1_mean",
    "surface_runoff_mm_day",
    "total_evaporation_mm_day_ecmwf",
    "wind_u_mean_ms",
    "wind_v_mean_ms",
    "solar_radiation_mj_m2_day",
]

DENGUE_USECOLS = [
    "CONSECUTIVE",
    "COD_EVE",
    "FEC_NOT",
    "INI_SIN",
    "FEC_CON",
    "COD_DPTO_R",
    "COD_MUN_R",
    "Departamento_residencia",
    "Municipio_residencia",
    "TIP_CAS",
    "AJUSTE",
    "PAC_HOS",
    "CON_FIN",
    "confirmados",
    "Estado_final_de_caso",
    "nom_est_f_caso",
    "SEXO",
    "EDAD",
    "UNI_MED",
    "PER_ETN",
    "GRU_POB",
]

GRAVE_USECOLS = [
    "COD_EVE",
    "INI_SIN",
    "COD_DPTO_R",
    "COD_MUN_R",
    "Departamento_residencia",
    "Municipio_residencia",
]

CLIMATE_USECOLS = ["date", "dpto_ccdgo", "mpio_cdpmp", *CLIMATE_VARS]

ASSOCIATION_FEATURES = [
    "dengue_count",
    "severe_count",
    "confirmed_prop",
    "hospitalized_prop",
    "death_prop",
    "median_delay_days",
    "mean_age_years",
    "female_prop",
    "tipcas_probable_prop",
    "tipcas_lab_prop",
    *CLIMATE_VARS,
]

MUNICIPAL_FEATURES = [
    "severe_count",
    "confirmed_prop",
    "median_delay_days",
    "rain_mm_day",
    "temp_mean_c",
]

PERMUTATION_FEATURES = {
    "dengue_count",
    "severe_count",
    "confirmed_prop",
    "hospitalized_prop",
    "death_prop",
    "median_delay_days",
    "rain_mm_day",
    "temp_mean_c",
    "solar_radiation_mj_m2_day",
}

EXPECTED_ANOMALIES = {
    "total_anomalies": 8556,
    "same_year_month": 784,
    "different_year_month": 7772,
}


@dataclass
class Paths:
    repo_root: Path
    output_dir: Path
    dengue_path: Path
    grave_path: Path
    climate_path: Path


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "AGENTS.md").exists():
            return candidate
    raise FileNotFoundError("Could not resolve repository root from current location")


def resolve_paths() -> Paths:
    repo_root = find_repo_root(Path(__file__).parent)
    output_dir = repo_root / "data" / "interim" / "stage2_monthly_sensitivity_associations"
    return Paths(
        repo_root=repo_root,
        output_dir=output_dir,
        dengue_path=repo_root / "data" / "raw" / "dengue.csv",
        grave_path=repo_root / "data" / "raw" / "dengue_grave.csv",
        climate_path=repo_root / "data" / "raw" / "google_earth_engine.csv",
    )


def normalize_text(series: pd.Series) -> pd.Series:
    out = series.fillna("").astype(str)
    out = out.str.replace("\xa0", " ", regex=False).str.strip()
    return out


def parse_colombian_date(series: pd.Series) -> pd.Series:
    s = normalize_text(series)
    s = (
        s.str.replace("a. m.", "", regex=False)
        .str.replace("p. m.", "", regex=False)
        .str.replace("a. m", "", regex=False)
        .str.replace("p. m", "", regex=False)
        .str.replace("AM", "", regex=False)
        .str.replace("PM", "", regex=False)
        .str.strip()
    )
    token = s.str.split(" ").str[0]
    return pd.to_datetime(token, format="%d/%m/%Y", errors="coerce")


def normalize_dept_code(series: pd.Series) -> pd.Series:
    return normalize_text(series).str.extract(r"(\d+)", expand=False).fillna("").str.zfill(2)


def normalize_muni_code(series: pd.Series) -> pd.Series:
    return normalize_text(series).str.extract(r"(\d+)", expand=False).fillna("")


def to_age_years(age: pd.Series, unit: pd.Series) -> pd.Series:
    age_num = pd.to_numeric(age, errors="coerce")
    unit_num = pd.to_numeric(unit, errors="coerce")
    out = pd.Series(np.nan, index=age.index, dtype="float64")
    out.loc[unit_num.eq(1)] = age_num.loc[unit_num.eq(1)]
    out.loc[unit_num.eq(2)] = age_num.loc[unit_num.eq(2)] / 12.0
    out.loc[unit_num.eq(3)] = age_num.loc[unit_num.eq(3)] / 365.0
    out.loc[unit_num.eq(4)] = age_num.loc[unit_num.eq(4)] / (24.0 * 365.0)
    out.loc[unit_num.eq(5)] = age_num.loc[unit_num.eq(5)] / (60.0 * 24.0 * 365.0)
    return out


def bh_qvalues(pvals: pd.Series) -> pd.Series:
    p = pvals.astype(float).to_numpy()
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = np.empty(n, dtype=float)
    prev = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        val = ranked[i] * n / rank
        prev = min(prev, val)
        q[i] = prev
    out = np.empty(n, dtype=float)
    out[order] = np.clip(q, 0.0, 1.0)
    return pd.Series(out, index=pvals.index)


def spearman_corr(x: pd.Series, y: pd.Series) -> float:
    valid = x.notna() & y.notna()
    if valid.sum() < 8:
        return float("nan")
    xr = x.loc[valid].rank(method="average")
    yr = y.loc[valid].rank(method="average")
    return float(xr.corr(yr, method="pearson"))


def partial_spearman(x: pd.Series, y: pd.Series, controls: pd.DataFrame) -> float:
    valid = x.notna() & y.notna()
    for col in controls.columns:
        valid &= controls[col].notna()
    if valid.sum() < 20:
        return float("nan")

    xv = x.loc[valid].rank(method="average").to_numpy(dtype=float)
    yv = y.loc[valid].rank(method="average").to_numpy(dtype=float)
    cv = controls.loc[valid].to_numpy(dtype=float)
    ones = np.ones((cv.shape[0], 1), dtype=float)
    design = np.concatenate([ones, cv], axis=1)

    bx, *_ = np.linalg.lstsq(design, xv, rcond=None)
    by, *_ = np.linalg.lstsq(design, yv, rcond=None)
    rx = xv - design @ bx
    ry = yv - design @ by

    sx = np.std(rx)
    sy = np.std(ry)
    if sx == 0.0 or sy == 0.0:
        return float("nan")
    rx_c = rx - np.mean(rx)
    ry_c = ry - np.mean(ry)
    denom = np.sqrt(np.sum(rx_c**2) * np.sum(ry_c**2))
    if denom == 0.0:
        return float("nan")
    return float(np.sum(rx_c * ry_c) / denom)


def circular_shift_perm_pvalue(
    df: pd.DataFrame,
    feature_col: str,
    target_col: str,
    muni_col: str,
    observed_corr: float,
    n_perm: int = 80,
    seed: int = 42,
) -> float:
    if np.isnan(observed_corr):
        return float("nan")

    rng = np.random.default_rng(seed)
    work = df[[muni_col, "year_month", feature_col, target_col]].dropna().copy()
    if work.shape[0] < 40:
        return float("nan")

    grouped = {k: g.sort_values("year_month") for k, g in work.groupby(muni_col)}
    perm_corrs = []
    for _ in range(n_perm):
        shifted_parts = []
        for muni, g in grouped.items():
            n = g.shape[0]
            if n < 6:
                continue
            shift = int(rng.integers(1, n))
            shifted_target = np.roll(g[target_col].to_numpy(dtype=float), shift)
            part = g[[feature_col]].copy()
            part[target_col] = shifted_target
            shifted_parts.append(part)
        if not shifted_parts:
            continue
        shifted = pd.concat(shifted_parts, ignore_index=True)
        corr = spearman_corr(shifted[feature_col], shifted[target_col])
        if pd.notna(corr):
            perm_corrs.append(float(corr))
    if not perm_corrs:
        return float("nan")
    perm = np.asarray(perm_corrs)
    return float(np.mean(np.abs(perm) >= abs(observed_corr)))


def build_preflight(paths: Paths, sha: str) -> dict:
    protocol = {
        "created_utc": pd.Timestamp.now("UTC").isoformat(),
        "commit_sha": sha,
        "scope": "Tolima+Meta residence, municipality-month exploratory panel",
        "scenario_rules": {
            "S1": "Keep all anomaly rows (INI_SIN > FEC_NOT) in original onset month",
            "S2": "Keep anomaly rows only when onset and notification share same year-month; exclude other anomaly rows",
            "S3": "Exclude all anomaly rows",
        },
        "invariants": [
            "No modification under data/raw",
            "No automatic date replacement/swap/imputation",
            "Scenario deltas apply only to anomaly-group rows",
            "Dengue and severe dengue streams remain separate",
        ],
        "lag_direction": {
            "contemporaneous": "x_t vs y_t",
            "lead_t1": "x_t vs y_(t+1)",
            "lead_t2": "x_t vs y_(t+2)",
        },
        "interpretation_limits": [
            "Correlations are exploratory associations, not causal effects",
            "Associations do not prove predictive utility",
            "Y final labeling remains open and only bounded exploratory proxies are used",
        ],
    }
    return protocol


def monthly_aggregates(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
    work = df.copy()
    work["year_month"] = work["ini_dt"].dt.to_period("M").astype(str)
    work["age_years"] = to_age_years(work["EDAD"], work["UNI_MED"])
    work["delay_days"] = (work["fec_not_dt"] - work["ini_dt"]).dt.days

    work["is_female"] = normalize_text(work["SEXO"]).str.upper().eq("F")
    work["is_confirmed"] = pd.to_numeric(work["confirmados"], errors="coerce").eq(1)
    work["is_hospitalized"] = pd.to_numeric(work["PAC_HOS"], errors="coerce").eq(1)
    work["is_death"] = pd.to_numeric(work["CON_FIN"], errors="coerce").eq(2)
    work["is_tipcas_probable"] = pd.to_numeric(work["TIP_CAS"], errors="coerce").eq(2)
    work["is_tipcas_lab"] = pd.to_numeric(work["TIP_CAS"], errors="coerce").eq(3)

    grouped = (
        work.groupby(["dept_code", "mun_full", "year_month"], dropna=False)
        .agg(
            dengue_count=("CONSECUTIVE", "size"),
            confirmed_prop=("is_confirmed", "mean"),
            hospitalized_prop=("is_hospitalized", "mean"),
            death_prop=("is_death", "mean"),
            female_prop=("is_female", "mean"),
            mean_age_years=("age_years", "mean"),
            median_delay_days=("delay_days", "median"),
            tipcas_probable_prop=("is_tipcas_probable", "mean"),
            tipcas_lab_prop=("is_tipcas_lab", "mean"),
            anomaly_share=("is_anomaly", "mean"),
        )
        .reset_index()
    )
    grouped["scenario"] = scenario
    grouped["department_name"] = grouped["dept_code"].map(TARGET_DEPTS)
    return grouped


def build_field_inventory(fields: list[str]) -> pd.DataFrame:
    date_fields = {"FEC_NOT", "INI_SIN", "FEC_CON", "FEC_HOS", "FEC_DEF", "FECHA_NTO", "FEC_ARC_XL", "FEC_AJU"}
    id_fields = {
        "CONSECUTIVE",
        "COD_EVE",
        "COD_PRE",
        "COD_SUB",
        "COD_PAIS_O",
        "COD_DPTO_O",
        "COD_MUN_O",
        "COD_ASE",
        "COD_PAIS_R",
        "COD_DPTO_R",
        "COD_MUN_R",
        "COD_DPTO_N",
        "COD_MUN_N",
        "Nombre_upgd",
        "Pais_ocurrencia",
        "Departamento_ocurrencia",
        "Municipio_ocurrencia",
        "Pais_residencia",
        "Departamento_residencia",
        "Municipio_residencia",
        "Departamento_Notificacion",
        "Municipio_notificacion",
        "FM_FUERZA",
        "FM_UNIDAD",
        "FM_GRADO",
    }
    target_outcome_like = {
        "TIP_CAS",
        "AJUSTE",
        "confirmados",
        "Estado_final_de_caso",
        "nom_est_f_caso",
        "PAC_HOS",
        "CON_FIN",
        "CBMTE",
    }
    demographic = {
        "EDAD",
        "UNI_MED",
        "SEXO",
        "PER_ETN",
        "GRU_POB",
        "nom_grupo",
        "estrato",
        "AREA",
        "OCUPACION",
        "TIP_SS",
        "sem_ges",
        "GP_DISCAPA",
        "GP_DESPLAZ",
        "GP_MIGRANT",
        "GP_CARCELA",
        "GP_GESTAN",
        "GP_INDIGEN",
        "GP_POBICFB",
        "GP_MAD_COM",
        "GP_DESMOVI",
        "GP_PSIQUIA",
        "GP_VIC_VIO",
        "GP_OTROS",
    }
    metadata_fields = {"fuente", "Nombre_evento", "va_sispro", "ANO", "SEMANA"}

    monthly_candidate = {
        "PAC_HOS",
        "CON_FIN",
        "TIP_CAS",
        "AJUSTE",
        "confirmados",
        "SEXO",
        "EDAD",
        "UNI_MED",
        "PER_ETN",
        "GRU_POB",
        "FEC_NOT",
        "INI_SIN",
        "FEC_CON",
    }

    rows = []
    for field in fields:
        if field in date_fields:
            role = "date"
            representation = "monthly_delay_or_timing_summary"
        elif field in id_fields or field.startswith("COD_"):
            role = "identifier"
            representation = "not_aggregated_for_correlation"
        elif field in target_outcome_like:
            role = "post_event_or_classification"
            representation = "monthly_proportion_distribution"
        elif field in demographic:
            role = "demographic_or_context_category"
            representation = "monthly_proportion_or_summary"
        elif field in metadata_fields:
            role = "metadata_or_time_index"
            representation = "context_only_or_time_axis"
        else:
            role = "insufficient_definition_or_other"
            representation = "excluded_until_definition"

        eligible = field in monthly_candidate
        if role == "identifier":
            reason = "Identifier fields are keys/lineage fields; not continuous analytic magnitudes."
        elif role == "date":
            reason = "Used to derive monthly timing and delays; raw dates are preserved for traceability."
        elif not eligible:
            reason = "Excluded from current exploratory associations due role/availability ambiguity."
        else:
            reason = "Included as exploratory monthly representation with explicit denominator and timing caveats."

        availability = "retrospective_consolidated_export"
        if field in {"FEC_NOT", "FEC_CON", "FEC_AJU", "FEC_ARC_XL"}:
            availability = "administrative_timing_field_not_equal_to_real_time_availability"

        rows.append(
            {
                "field": field,
                "analytic_role": role,
                "monthly_representation": representation,
                "eligible_for_association": bool(eligible),
                "availability_timing_note": availability,
                "inclusion_exclusion_reason": reason,
            }
        )

    out = pd.DataFrame(rows)
    return out


def summarize_sensitivity(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_geo = (
        panel.groupby(["scenario", "department_name"], dropna=False)
        .agg(
            retained_records=("dengue_count", "sum"),
            baseline_records=("dengue_count_s1", "sum"),
            severe_records=("severe_count", "sum"),
            impacted_months=("scenario_delta_vs_s1", lambda s: int((s != 0).sum())),
        )
        .reset_index()
    )
    summary_geo["net_delta"] = summary_geo["retained_records"] - summary_geo["baseline_records"]
    summary_geo["relative_delta_pct"] = np.where(
        summary_geo["baseline_records"] > 0,
        100.0 * summary_geo["net_delta"] / summary_geo["baseline_records"],
        np.nan,
    )

    peak_rows = []
    for (scenario, mun), g in panel.groupby(["scenario", "mun_full"], dropna=False):
        g = g.sort_values("year_month")
        if g["dengue_count"].notna().sum() == 0:
            continue
        idx = g["dengue_count"].idxmax()
        peak_rows.append(
            {
                "scenario": scenario,
                "mun_full": mun,
                "department_name": g["department_name"].iloc[0],
                "peak_month": g.loc[idx, "year_month"],
                "peak_count": g.loc[idx, "dengue_count"],
                "active_months": int((g["dengue_count"] > 0).sum()),
            }
        )

    peaks = pd.DataFrame(peak_rows)
    baseline = peaks[peaks["scenario"] == "S1"][
        ["mun_full", "peak_month", "peak_count", "active_months"]
    ].rename(
        columns={
            "peak_month": "peak_month_s1",
            "peak_count": "peak_count_s1",
            "active_months": "active_months_s1",
        }
    )
    peak_cmp = peaks.merge(baseline, on="mun_full", how="left")
    peak_cmp["peak_count_delta"] = peak_cmp["peak_count"] - peak_cmp["peak_count_s1"]
    peak_cmp["active_months_delta"] = peak_cmp["active_months"] - peak_cmp["active_months_s1"]

    def month_offset(a: str, b: str) -> float:
        if pd.isna(a) or pd.isna(b):
            return np.nan
        pa = pd.Period(a, freq="M")
        pb = pd.Period(b, freq="M")
        return float(pa.ordinal - pb.ordinal)

    peak_cmp["peak_month_shift"] = [
        month_offset(a, b) for a, b in zip(peak_cmp["peak_month"], peak_cmp["peak_month_s1"])
    ]
    return summary_geo, peak_cmp


def add_time_controls(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    periods = pd.PeriodIndex(out["year_month"], freq="M")
    out["month_num"] = periods.month
    out["sin_month"] = np.sin(2.0 * np.pi * out["month_num"] / 12.0)
    out["cos_month"] = np.cos(2.0 * np.pi * out["month_num"] / 12.0)
    out["trend_idx"] = out.groupby("mun_full").cumcount().astype(float)
    out["log_dengue_t"] = np.log1p(out["dengue_count"].clip(lower=0))
    return out


def association_loop(panel: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    raw_rows = []
    controlled_rows = []
    municipal_rows = []

    scenarios = ["S1", "S2", "S3"]
    for scenario in scenarios:
        sc = panel[panel["scenario"] == scenario].copy()
        sc = add_time_controls(sc)
        sc = sc.sort_values(["mun_full", "year_month"])  # needed for shifts
        sc["dengue_tplus1"] = sc.groupby("mun_full")["dengue_count"].shift(-1)
        sc["dengue_tplus2"] = sc.groupby("mun_full")["dengue_count"].shift(-2)

        level_frames: list[tuple[str, pd.DataFrame]] = [("pooled", sc)]
        for dept in sorted(sc["department_name"].dropna().unique()):
            level_frames.append((f"department:{dept}", sc[sc["department_name"] == dept].copy()))

        for level, lf in level_frames:
            for horizon, target_col in [(0, "dengue_count"), (1, "dengue_tplus1"), (2, "dengue_tplus2")]:
                features = ASSOCIATION_FEATURES
                for feature in features:
                    if feature not in lf.columns:
                        continue
                    if horizon == 0 and feature == "dengue_count":
                        continue
                    x = lf[feature]
                    y = lf[target_col]
                    rho_raw = spearman_corr(x, y)
                    n_obs = int((x.notna() & y.notna()).sum())
                    if level == "pooled" and horizon in {1, 2} and feature in PERMUTATION_FEATURES:
                        p_perm = circular_shift_perm_pvalue(
                            lf,
                            feature,
                            target_col,
                            "mun_full",
                            rho_raw,
                            n_perm=80,
                        )
                    else:
                        p_perm = float("nan")
                    raw_rows.append(
                        {
                            "scenario": scenario,
                            "level": level,
                            "horizon": horizon,
                            "feature": feature,
                            "association_method": "spearman",
                            "rho": rho_raw,
                            "p_permutation": p_perm,
                            "n_obs": n_obs,
                            "target": target_col,
                        }
                    )

                    controls = lf[["trend_idx", "sin_month", "cos_month", "log_dengue_t"]]
                    rho_ctrl = partial_spearman(x, y, controls)
                    controlled_rows.append(
                        {
                            "scenario": scenario,
                            "level": level,
                            "horizon": horizon,
                            "feature": feature,
                            "association_method": "partial_spearman",
                            "rho": rho_ctrl,
                            "n_obs": n_obs,
                            "target": target_col,
                            "controls": "trend_idx+sin_month+cos_month+log_dengue_t",
                        }
                    )

        for horizon, target_col in [(1, "dengue_tplus1"), (2, "dengue_tplus2")]:
            for mun, mf in sc.groupby("mun_full", dropna=False):
                if mf.shape[0] < 24:
                    continue
                for feature in MUNICIPAL_FEATURES:
                    if feature not in mf.columns:
                        continue
                    rho = spearman_corr(mf[feature], mf[target_col])
                    n_obs = int((mf[feature].notna() & mf[target_col].notna()).sum())
                    municipal_rows.append(
                        {
                            "scenario": scenario,
                            "level": "municipality",
                            "mun_full": mun,
                            "department_name": mf["department_name"].iloc[0],
                            "horizon": horizon,
                            "feature": feature,
                            "rho": rho,
                            "n_obs": n_obs,
                            "target": target_col,
                        }
                    )

    raw = pd.DataFrame(raw_rows)
    controlled = pd.DataFrame(controlled_rows)
    municipal = pd.DataFrame(municipal_rows)

    if not raw.empty:
        raw["q_value_bh"] = np.nan
        for keys, g in raw.groupby(["scenario", "level", "horizon"], dropna=False):
            idx = g.index
            valid = raw.loc[idx, "p_permutation"].notna()
            if valid.any():
                raw.loc[idx[valid], "q_value_bh"] = bh_qvalues(raw.loc[idx[valid], "p_permutation"])

    return raw, controlled, municipal


def stability_summary(raw: pd.DataFrame, controlled: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()

    parts = []
    for label, src in [("raw", raw), ("controlled", controlled)]:
        pooled = src[src["level"] == "pooled"].copy()
        if pooled.empty:
            continue
        for (feature, horizon), g in pooled.groupby(["feature", "horizon"], dropna=False):
            rho_map = {row["scenario"]: row["rho"] for _, row in g.iterrows()}
            rhos = [rho_map.get(s) for s in ["S1", "S2", "S3"]]
            valid_rhos = [r for r in rhos if pd.notna(r)]
            if len(valid_rhos) < 2:
                continue
            max_abs_delta = float(np.nanmax(valid_rhos) - np.nanmin(valid_rhos))
            signs = np.sign(valid_rhos)
            sign_consistent = bool(np.all(signs == signs[0]))
            depends_2013 = bool((not sign_consistent) or (max_abs_delta >= 0.15))
            robust = bool(sign_consistent and max_abs_delta < 0.10)
            parts.append(
                {
                    "analysis_type": label,
                    "feature": feature,
                    "horizon": horizon,
                    "rho_s1": rho_map.get("S1"),
                    "rho_s2": rho_map.get("S2"),
                    "rho_s3": rho_map.get("S3"),
                    "max_abs_delta": max_abs_delta,
                    "sign_consistent": sign_consistent,
                    "depends_on_2013_treatment": depends_2013,
                    "stable_across_scenarios": robust,
                }
            )

    return pd.DataFrame(parts).sort_values(["analysis_type", "horizon", "feature"]).reset_index(drop=True)


def write_method_notes(path: Path) -> None:
    content = """# Association method notes

- Scope: exploratory municipality-month associations under S1/S2/S3.
- Directionality: contemporaneous (`t` vs `t`), lead-1 (`t` vs `t+1`), lead-2 (`t` vs `t+2`).
- Raw associations: Spearman correlation.
- Controlled associations: partial Spearman on ranked variables with controls `trend_idx`, `sin_month`, `cos_month`, `log_dengue_t`.
- Uncertainty for raw pooled associations: circular-shift permutation p-values (preserves within-municipality serial dependence).
- Multiplicity: Benjamini-Hochberg q-values within each scenario/level/horizon group.
- Heterogeneity: municipal-level correlations are exported separately and summarized for stability.
- Interpretation guardrail: associations are not causal effects and do not prove predictive utility.
"""
    path.write_text(content, encoding="utf-8")


def run() -> None:
    paths = resolve_paths()
    paths.output_dir.mkdir(parents=True, exist_ok=True)

    for source in [paths.dengue_path, paths.grave_path, paths.climate_path]:
        if not source.exists():
            raise FileNotFoundError(f"Missing required input file: {source}")

    import subprocess

    sha = (
        subprocess.check_output(["git", "-C", str(paths.repo_root), "rev-parse", "HEAD"], text=True)
        .strip()
    )

    preflight = build_preflight(paths, sha)
    (paths.output_dir / "preflight_protocol.json").write_text(
        json.dumps(preflight, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    dengue = pd.read_csv(paths.dengue_path, usecols=DENGUE_USECOLS, dtype=str, low_memory=False)
    grave = pd.read_csv(paths.grave_path, usecols=GRAVE_USECOLS, dtype=str, low_memory=False)
    climate = pd.read_csv(paths.climate_path, usecols=CLIMATE_USECOLS, dtype=str, low_memory=False)

    dengue_header = pd.read_csv(paths.dengue_path, nrows=0).columns.tolist()

    dengue["dept_code"] = normalize_dept_code(dengue["COD_DPTO_R"])
    dengue["mun_code"] = normalize_muni_code(dengue["COD_MUN_R"])
    dengue["mun_code_3"] = np.where(dengue["mun_code"].str.fullmatch(r"\d{1,3}"), dengue["mun_code"].str.zfill(3), "")
    dengue["mun_full"] = dengue["dept_code"] + dengue["mun_code_3"]
    dengue["ini_dt"] = parse_colombian_date(dengue["INI_SIN"])
    dengue["fec_not_dt"] = parse_colombian_date(dengue["FEC_NOT"])
    dengue["fec_con_dt"] = parse_colombian_date(dengue["FEC_CON"])

    grave["dept_code"] = normalize_dept_code(grave["COD_DPTO_R"])
    grave["mun_code"] = normalize_muni_code(grave["COD_MUN_R"])
    grave["mun_code_3"] = np.where(grave["mun_code"].str.fullmatch(r"\d{1,3}"), grave["mun_code"].str.zfill(3), "")
    grave["mun_full"] = grave["dept_code"] + grave["mun_code_3"]
    grave["ini_dt"] = parse_colombian_date(grave["INI_SIN"])

    scope_dengue = dengue[dengue["dept_code"].isin(TARGET_DEPTS.keys())].copy()
    scope_grave = grave[grave["dept_code"].isin(TARGET_DEPTS.keys())].copy()

    scope_dengue["valid_mun"] = scope_dengue["mun_code_3"].ne("")
    scope_grave["valid_mun"] = scope_grave["mun_code_3"].ne("")

    scope_dengue["comparable_dates"] = scope_dengue["ini_dt"].notna() & scope_dengue["fec_not_dt"].notna()
    scope_dengue["is_anomaly"] = scope_dengue["comparable_dates"] & (scope_dengue["ini_dt"] > scope_dengue["fec_not_dt"])
    scope_dengue["same_year_month"] = (
        scope_dengue["is_anomaly"]
        & (scope_dengue["ini_dt"].dt.to_period("M") == scope_dengue["fec_not_dt"].dt.to_period("M"))
    )

    anomaly_total = int(scope_dengue["is_anomaly"].sum())
    anomaly_same = int(scope_dengue["same_year_month"].sum())
    anomaly_diff = int(anomaly_total - anomaly_same)

    anomaly_cardinality = pd.DataFrame(
        [
            {"metric": "total_scope_records", "value": int(scope_dengue.shape[0])},
            {"metric": "comparable_records", "value": int(scope_dengue["comparable_dates"].sum())},
            {"metric": "total_anomalies", "value": anomaly_total},
            {"metric": "same_year_month", "value": anomaly_same},
            {"metric": "different_year_month", "value": anomaly_diff},
            {
                "metric": "reference_total_anomalies",
                "value": EXPECTED_ANOMALIES["total_anomalies"],
            },
            {
                "metric": "reference_same_year_month",
                "value": EXPECTED_ANOMALIES["same_year_month"],
            },
            {
                "metric": "reference_different_year_month",
                "value": EXPECTED_ANOMALIES["different_year_month"],
            },
            {
                "metric": "matches_reference",
                "value": int(
                    anomaly_total == EXPECTED_ANOMALIES["total_anomalies"]
                    and anomaly_same == EXPECTED_ANOMALIES["same_year_month"]
                    and anomaly_diff == EXPECTED_ANOMALIES["different_year_month"]
                ),
            },
        ]
    )
    anomaly_cardinality.to_csv(paths.output_dir / "anomaly_cardinality_summary.csv", index=False)

    anomaly_geo = (
        scope_dengue[scope_dengue["is_anomaly"]]
        .groupby(["dept_code", "mun_full", "Departamento_residencia", "Municipio_residencia"], dropna=False)
        .agg(
            anomaly_records=("CONSECUTIVE", "size"),
            same_year_month_records=("same_year_month", "sum"),
        )
        .reset_index()
    )
    anomaly_geo["different_year_month_records"] = (
        anomaly_geo["anomaly_records"] - anomaly_geo["same_year_month_records"]
    )
    anomaly_geo["department_name"] = anomaly_geo["dept_code"].map(TARGET_DEPTS)
    anomaly_geo.sort_values(["dept_code", "anomaly_records"], ascending=[True, False]).to_csv(
        paths.output_dir / "anomaly_distribution_by_geo.csv", index=False
    )

    discrepancy_status = "MATCHED"
    discrepancy_note = "Reference cardinalities reproduced exactly."
    if not (
        anomaly_total == EXPECTED_ANOMALIES["total_anomalies"]
        and anomaly_same == EXPECTED_ANOMALIES["same_year_month"]
        and anomaly_diff == EXPECTED_ANOMALIES["different_year_month"]
    ):
        discrepancy_status = "DISCREPANCY"
        discrepancy_note = (
            "Observed cardinalities differ from reference values. Downstream interpretation should stay provisional "
            "until discrepancy is explained."
        )

    (paths.output_dir / "anomaly_discrepancy_log.md").write_text(
        "\n".join(
            [
                "# Anomaly cardinality discrepancy log",
                "",
                f"- Status: {discrepancy_status}",
                f"- Observed totals: total={anomaly_total}, same_ym={anomaly_same}, diff_ym={anomaly_diff}",
                (
                    "- Reference totals: "
                    f"total={EXPECTED_ANOMALIES['total_anomalies']}, "
                    f"same_ym={EXPECTED_ANOMALIES['same_year_month']}, "
                    f"diff_ym={EXPECTED_ANOMALIES['different_year_month']}"
                ),
                f"- Note: {discrepancy_note}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    dengue_valid = scope_dengue[scope_dengue["valid_mun"] & scope_dengue["ini_dt"].notna()].copy()
    dengue_valid["department_name"] = dengue_valid["dept_code"].map(TARGET_DEPTS)

    grave_valid = scope_grave[scope_grave["valid_mun"] & scope_grave["ini_dt"].notna()].copy()
    grave_valid["department_name"] = grave_valid["dept_code"].map(TARGET_DEPTS)

    non_anomaly = dengue_valid[~dengue_valid["is_anomaly"]].copy()
    anomaly = dengue_valid[dengue_valid["is_anomaly"]].copy()
    anomaly_same_df = anomaly[anomaly["same_year_month"]].copy()

    s1_df = pd.concat([non_anomaly, anomaly], ignore_index=True)
    s2_df = pd.concat([non_anomaly, anomaly_same_df], ignore_index=True)
    s3_df = non_anomaly.copy()

    s1 = monthly_aggregates(s1_df, "S1")
    s2 = monthly_aggregates(s2_df, "S2")
    s3 = monthly_aggregates(s3_df, "S3")

    severe_monthly = (
        grave_valid.assign(year_month=grave_valid["ini_dt"].dt.to_period("M").astype(str))
        .groupby(["dept_code", "mun_full", "year_month"], dropna=False)
        .agg(severe_count=("COD_EVE", "size"))
        .reset_index()
    )

    climate["dept_code"] = normalize_dept_code(climate["dpto_ccdgo"])
    climate["mun_full"] = normalize_text(climate["mpio_cdpmp"]).str.extract(r"(\d+)", expand=False).fillna("").str.zfill(5)
    climate["date_dt"] = pd.to_datetime(normalize_text(climate["date"]), errors="coerce")
    climate_scope = climate[climate["dept_code"].isin(TARGET_DEPTS.keys()) & climate["mun_full"].str.fullmatch(r"\d{5}")].copy()
    climate_scope["year_month"] = climate_scope["date_dt"].dt.to_period("M").astype(str)
    for col in CLIMATE_VARS:
        climate_scope[col] = pd.to_numeric(climate_scope[col], errors="coerce")
    climate_monthly = (
        climate_scope.groupby(["dept_code", "mun_full", "year_month"], dropna=False)[CLIMATE_VARS]
        .mean()
        .reset_index()
    )

    def attach_support(df: pd.DataFrame) -> pd.DataFrame:
        out = df.merge(severe_monthly, on=["dept_code", "mun_full", "year_month"], how="left")
        out["severe_count"] = out["severe_count"].fillna(0).astype(int)
        out = out.merge(climate_monthly, on=["dept_code", "mun_full", "year_month"], how="left")
        return out

    s1 = attach_support(s1)
    s2 = attach_support(s2)
    s3 = attach_support(s3)

    muni_universe = sorted(set(s1["mun_full"]).union(set(s2["mun_full"])).union(set(s3["mun_full"])).union(set(severe_monthly["mun_full"])))
    start_month = min(s1["year_month"].min(), s2["year_month"].min(), s3["year_month"].min())
    end_month = max(s1["year_month"].max(), s2["year_month"].max(), s3["year_month"].max())
    months = pd.period_range(start_month, end_month, freq="M").astype(str)

    base_index = pd.MultiIndex.from_product([muni_universe, months], names=["mun_full", "year_month"])
    base_panel = pd.DataFrame(index=base_index).reset_index()
    base_panel["dept_code"] = base_panel["mun_full"].str[:2]
    base_panel = base_panel[base_panel["dept_code"].isin(TARGET_DEPTS.keys())].copy()
    base_panel["department_name"] = base_panel["dept_code"].map(TARGET_DEPTS)

    def reindex_panel(df: pd.DataFrame, scenario: str) -> pd.DataFrame:
        keep_cols = [
            "dept_code",
            "mun_full",
            "year_month",
            "department_name",
            "dengue_count",
            "confirmed_prop",
            "hospitalized_prop",
            "death_prop",
            "female_prop",
            "mean_age_years",
            "median_delay_days",
            "tipcas_probable_prop",
            "tipcas_lab_prop",
            "anomaly_share",
            "severe_count",
            *CLIMATE_VARS,
        ]
        w = df[keep_cols].copy()
        merged = base_panel.merge(w, on=["dept_code", "mun_full", "year_month", "department_name"], how="left")
        merged["scenario"] = scenario
        merged["dengue_count"] = merged["dengue_count"].fillna(0).astype(int)
        merged["had_records_before_fill"] = merged["confirmed_prop"].notna()
        return merged

    p1 = reindex_panel(s1, "S1")
    p2 = reindex_panel(s2, "S2")
    p3 = reindex_panel(s3, "S3")

    observed_window = (
        p1[p1["dengue_count"] > 0]
        .groupby("mun_full")["year_month"]
        .agg(first_month="min", last_month="max")
        .reset_index()
    )

    def add_window_flags(df: pd.DataFrame) -> pd.DataFrame:
        out = df.merge(observed_window, on="mun_full", how="left")
        ym = pd.PeriodIndex(out["year_month"], freq="M")
        first = pd.PeriodIndex(out["first_month"].fillna(out["year_month"]), freq="M")
        last = pd.PeriodIndex(out["last_month"].fillna(out["year_month"]), freq="M")
        out["in_s1_observed_window"] = (ym >= first) & (ym <= last)
        return out

    p1 = add_window_flags(p1)
    p2 = add_window_flags(p2)
    p3 = add_window_flags(p3)

    merged = p1.rename(columns={"dengue_count": "dengue_count_s1"})[
        ["dept_code", "mun_full", "year_month", "department_name", "dengue_count_s1", "in_s1_observed_window"]
    ]
    merged = merged.merge(
        p2.rename(columns={"dengue_count": "dengue_count_s2"})[
            ["dept_code", "mun_full", "year_month", "dengue_count_s2"]
        ],
        on=["dept_code", "mun_full", "year_month"],
        how="left",
    )
    merged = merged.merge(
        p3.rename(columns={"dengue_count": "dengue_count_s3"})[
            ["dept_code", "mun_full", "year_month", "dengue_count_s3"]
        ],
        on=["dept_code", "mun_full", "year_month"],
        how="left",
    )

    merged["dengue_count_s2"] = merged["dengue_count_s2"].fillna(0).astype(int)
    merged["dengue_count_s3"] = merged["dengue_count_s3"].fillna(0).astype(int)

    p1 = p1.merge(merged[["mun_full", "year_month", "dengue_count_s1", "dengue_count_s2", "dengue_count_s3"]], on=["mun_full", "year_month"], how="left")
    p2 = p2.merge(merged[["mun_full", "year_month", "dengue_count_s1", "dengue_count_s2", "dengue_count_s3"]], on=["mun_full", "year_month"], how="left")
    p3 = p3.merge(merged[["mun_full", "year_month", "dengue_count_s1", "dengue_count_s2", "dengue_count_s3"]], on=["mun_full", "year_month"], how="left")

    p1["scenario_delta_vs_s1"] = p1["dengue_count"] - p1["dengue_count_s1"]
    p2["scenario_delta_vs_s1"] = p2["dengue_count"] - p2["dengue_count_s1"]
    p3["scenario_delta_vs_s1"] = p3["dengue_count"] - p3["dengue_count_s1"]

    baseline_panel = p1.copy()

    key_validation = pd.DataFrame(
        [
            {
                "check": "unique_key_baseline",
                "state": "PASS" if not baseline_panel.duplicated(["mun_full", "year_month"]).any() else "FAIL",
                "detail": "mun_full+year_month uniqueness on baseline panel",
            },
            {
                "check": "scenario_cardinality_alignment",
                "state": "PASS" if p1.shape[0] == p2.shape[0] == p3.shape[0] else "FAIL",
                "detail": "S1/S2/S3 panels share same municipality-month cardinality",
            },
            {
                "check": "s2_only_removes_anomaly_rows",
                "state": "PASS" if int((p2["dengue_count"] > p1["dengue_count"]).sum()) == 0 else "FAIL",
                "detail": "S2 should not create additional records versus S1",
            },
            {
                "check": "s3_only_removes_anomaly_rows",
                "state": "PASS" if int((p3["dengue_count"] > p1["dengue_count"]).sum()) == 0 else "FAIL",
                "detail": "S3 should not create additional records versus S1",
            },
        ]
    )

    field_inventory = build_field_inventory(dengue_header)

    scenario_panel = pd.concat([p1, p2, p3], ignore_index=True)
    summary_geo, peak_changes = summarize_sensitivity(scenario_panel)

    raw_assoc, controlled_assoc, municipal_assoc = association_loop(scenario_panel)
    stability = stability_summary(raw_assoc, controlled_assoc)

    baseline_panel.to_csv(paths.output_dir / "monthly_panel_baseline.csv", index=False)
    p1.to_csv(paths.output_dir / "monthly_panel_s1.csv", index=False)
    p2.to_csv(paths.output_dir / "monthly_panel_s2.csv", index=False)
    p3.to_csv(paths.output_dir / "monthly_panel_s3.csv", index=False)
    summary_geo.to_csv(paths.output_dir / "sensitivity_summary_by_geo.csv", index=False)
    peak_changes.to_csv(paths.output_dir / "sensitivity_peak_continuity_changes.csv", index=False)

    field_inventory.to_csv(paths.output_dir / "field_analytic_eligibility.csv", index=False)
    key_validation.to_csv(paths.output_dir / "panel_key_validation.csv", index=False)

    raw_assoc.to_csv(paths.output_dir / "associations_raw.csv", index=False)
    controlled_assoc.to_csv(paths.output_dir / "associations_controlled.csv", index=False)
    municipal_assoc.to_csv(paths.output_dir / "associations_municipal.csv", index=False)
    stability.to_csv(paths.output_dir / "associations_stability_summary.csv", index=False)
    write_method_notes(paths.output_dir / "associations_method_notes.md")

    metadata = {
        "created_utc": pd.Timestamp.now("UTC").isoformat(),
        "commit_sha": sha,
        "output_dir": str(paths.output_dir.relative_to(paths.repo_root)),
        "expected_anomalies": EXPECTED_ANOMALIES,
        "observed_anomalies": {
            "total_anomalies": anomaly_total,
            "same_year_month": anomaly_same,
            "different_year_month": anomaly_diff,
        },
        "scenario_rows": {
            "S1": int(p1.shape[0]),
            "S2": int(p2.shape[0]),
            "S3": int(p3.shape[0]),
        },
        "associations_rows": {
            "raw": int(raw_assoc.shape[0]),
            "controlled": int(controlled_assoc.shape[0]),
            "municipal": int(municipal_assoc.shape[0]),
            "stability": int(stability.shape[0]),
        },
    }
    (paths.output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    print("Outputs written to", paths.output_dir)
    print("Anomaly totals:", metadata["observed_anomalies"])


if __name__ == "__main__":
    run()
