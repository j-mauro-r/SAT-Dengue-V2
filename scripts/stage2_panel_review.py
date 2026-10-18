"""Bounded Stage 2 review: independent source joins, explicit observation states.

Raw/reference and previous outputs are read-only. Outputs contain aggregates only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/interim/stage2_panel_review"
PREVIOUS = ROOT / "data/interim/stage2_monthly_sensitivity_associations"
KEY = ["mun_full", "year_month"]
CLIMATE = [
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
EPI_COLS = [
    "CONSECUTIVE",
    "COD_EVE",
    "ANO",
    "COD_DPTO_R",
    "COD_MUN_R",
    "INI_SIN",
    "FEC_NOT",
    "FEC_CON",
    "FEC_AJU",
    "FEC_ARC_XL",
    "TIP_CAS",
    "AJUSTE",
    "confirmados",
    "PAC_HOS",
    "CON_FIN",
    "SEXO",
    "EDAD",
    "UNI_MED",
]
FEATURES = [
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
    *CLIMATE,
]


def save_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def protected_inputs() -> list[Path]:
    paths = list((ROOT / "data/raw").glob("*.csv"))
    paths += list((ROOT / "data/sources").glob("Divipola-*.md"))
    paths += list((ROOT / "data/sources").glob("Dengue_Datos_20*.xlsx"))
    for folder in [PREVIOUS, ROOT / "data/interim/stage2_dengue_date_investigation"]:
        paths += [p for p in folder.rglob("*") if p.is_file()]
    return sorted(set(paths))


def record_inputs() -> None:
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in protected_inputs()}
    manifest = OUT / "input_hashes.json"
    if manifest.exists():
        assert json.loads(manifest.read_text()) == hashes, "Protected inputs changed"
    else:
        save_json("input_hashes.json", hashes)


def parse_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(
        series.fillna("").astype(str).str.strip().str.split().str[0],
        format="%d/%m/%Y",
        errors="coerce",
    )


def code(series: pd.Series, width: int) -> pd.Series:
    # Reject malformed values instead of extracting a misleading digit substring.
    s = series.fillna("").astype(str).str.strip()
    return s.where(s.str.fullmatch(r"\d{1," + str(width) + "}"), "").str.zfill(width)


def catalog() -> pd.DataFrame:
    payload = json.loads((ROOT / "data/sources/Divipola-municipios.md").read_text())
    c = pd.DataFrame(payload["resultado"])
    c = c[c.CODIGO_DEPARTAMENTO.isin(["50", "73"])].copy()
    c = c.rename(columns={"CODIGO_DPTO_MPIO": "mun_full", "NOMBRE_MUNICIPIO": "municipality_name"})
    assert len(c) == 76 and c.mun_full.nunique() == 76
    c["department_name"] = c.CODIGO_DEPARTAMENTO.map({"50": "Meta", "73": "Tolima"})
    return c[["mun_full", "municipality_name", "department_name"]].sort_values("mun_full")


def read_epi(filename: str) -> pd.DataFrame:
    parts = []
    for chunk in pd.read_csv(
        ROOT / "data/raw" / filename, usecols=EPI_COLS, dtype=str, chunksize=200_000
    ):
        chunk["dept_code"] = code(chunk.COD_DPTO_R, 2)
        parts.append(chunk[chunk.dept_code.isin(["50", "73"])].copy())
    d = pd.concat(parts, ignore_index=True)
    d["mun_full"] = d.dept_code + code(d.COD_MUN_R, 3)
    for field in ["INI_SIN", "FEC_NOT", "FEC_CON", "FEC_AJU", "FEC_ARC_XL"]:
        d[field + "_dt"] = parse_date(d[field])
    d["year_month"] = d.INI_SIN_dt.dt.to_period("M").astype(str)
    d["anomaly"] = d.INI_SIN_dt.gt(d.FEC_NOT_dt)
    d["same_month"] = d.INI_SIN_dt.dt.to_period("M").eq(d.FEC_NOT_dt.dt.to_period("M"))
    return d


def partition_epi(d: pd.DataFrame, c: pd.DataFrame, event: str) -> pd.DataFrame:
    d = d.copy()
    d["geography_valid"] = d.mun_full.isin(c.mun_full)
    d["onset_valid"] = d.INI_SIN_dt.notna()
    d["event_valid"] = d.COD_EVE.eq(event)
    # Exclusive disposition; separate flags preserve overlapping quality issues.
    d["disposition"] = np.select(
        [~d.event_valid, ~d.geography_valid, ~d.onset_valid],
        ["unexpected_event", "unresolved_municipality", "missing_or_invalid_onset"],
        default="included",
    )
    return d


def aggregate_dengue(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    mappings = {
        "confirmed_prop": ("confirmados", "1"),
        "hospitalized_prop": ("PAC_HOS", "1"),
        "death_prop": ("CON_FIN", "2"),
        "female_prop": ("SEXO", "F"),
        "tipcas_probable_prop": ("TIP_CAS", "2"),
        "tipcas_lab_prop": ("TIP_CAS", "3"),
    }
    for name, (field, value) in mappings.items():
        s = d[field].fillna("").str.strip()
        d[name] = s.eq(value).astype(float).where(s.ne(""))
    unit = pd.to_numeric(d.UNI_MED, errors="coerce")
    divisor = unit.map({1: 1, 2: 12, 3: 365, 4: 8760, 5: 525600})
    d["mean_age_years"] = pd.to_numeric(d.EDAD, errors="coerce") / divisor
    d["median_delay_days"] = (d.FEC_NOT_dt - d.INI_SIN_dt).dt.days
    agg = {name: (name, "mean") for name in mappings}
    agg.update(
        {
            "mean_age_years": ("mean_age_years", "mean"),
            "median_delay_days": ("median_delay_days", "median"),
            "dengue_recorded_count": ("COD_EVE", "size"),
            "anomaly_count": ("anomaly", "sum"),
        }
    )
    return d.groupby(KEY).agg(**agg).reset_index()


def monthly_climate(c: pd.DataFrame) -> pd.DataFrame:
    parts = []
    cols = ["date", "dpto_ccdgo", "mpio_cdpmp", *CLIMATE]
    for chunk in pd.read_csv(
        ROOT / "data/raw/google_earth_engine.csv", usecols=cols, dtype=str, chunksize=250_000
    ):
        chunk["mun_full"] = code(chunk.mpio_cdpmp, 5)
        parts.append(chunk[chunk.mun_full.isin(c.mun_full)].copy())
    d = pd.concat(parts, ignore_index=True)
    d["date_dt"] = pd.to_datetime(d.date, errors="coerce")
    assert d.date_dt.notna().all(), "Unparseable climate date"
    assert not d.duplicated(["mun_full", "date_dt"]).any(), "Duplicate climate municipality-day"
    assert code(d.dpto_ccdgo, 2).eq(d.mun_full.str[:2]).all()
    d["year_month"] = d.date_dt.dt.to_period("M").astype(str)
    for col in CLIMATE:
        d[col] = pd.to_numeric(d[col], errors="coerce")
    g = d.groupby(KEY)
    means = g[CLIMATE].mean()
    counts = g[CLIMATE].count().add_suffix("_valid_days")
    result = means.join(counts).join(g.date_dt.nunique().rename("climate_days")).reset_index()
    save_json(
        "climate_source_summary.json",
        {"rows": len(d), "min": str(d.date_dt.min()), "max": str(d.date_dt.max())},
    )
    return result


def join_panel(
    grid: pd.DataFrame,
    dengue: pd.DataFrame,
    severe: pd.DataFrame,
    climate: pd.DataFrame,
    baseline: pd.DataFrame,
    scenario: str,
) -> pd.DataFrame:
    p = grid.merge(dengue, on=KEY, how="left", validate="one_to_one")
    p = p.merge(severe, on=KEY, how="left", validate="one_to_one")
    p = p.merge(climate, on=KEY, how="left", validate="one_to_one")
    p = p.merge(
        baseline[KEY + ["dengue_recorded_count"]].rename(
            columns={"dengue_recorded_count": "dengue_s1_recorded_count"}
        ),
        on=KEY,
        how="left",
        validate="one_to_one",
    )
    for col in [
        "dengue_recorded_count",
        "severe_recorded_count",
        "dengue_s1_recorded_count",
        "anomaly_count",
        "climate_days",
        *[v + "_valid_days" for v in CLIMATE],
    ]:
        p[col] = p[col].fillna(0).astype(int)
    p["scenario"] = scenario
    p["scenario_removed_count"] = p.dengue_s1_recorded_count - p.dengue_recorded_count
    p["dengue_observation_state"] = np.select(
        [p.dengue_recorded_count.gt(0), p.dengue_s1_recorded_count.gt(0)],
        ["records_present", "all_records_removed_by_scenario"],
        default="no_records_reporting_unknown",
    )
    p["severe_observation_state"] = np.where(
        p.severe_recorded_count.gt(0), "records_present", "no_records_reporting_unknown"
    )
    # These columns are nullable: observed rows are not proof of unique clinical cases.
    p["dengue_count"] = p.dengue_recorded_count.where(p.dengue_recorded_count.gt(0))
    p["severe_count"] = p.severe_recorded_count.where(p.severe_recorded_count.gt(0))
    p["expected_climate_days"] = pd.PeriodIndex(p.year_month, freq="M").days_in_month
    p["climate_state"] = np.select(
        [p.climate_days.eq(0), p.climate_days.eq(p.expected_climate_days)],
        ["missing", "complete"],
        default="partial",
    )
    p["common_source_window"] = p.year_month.between("2007-01", "2025-12")
    p["reporting_completeness"] = "unknown"
    p["operational_asof_eligible"] = False
    return p.sort_values(KEY).reset_index(drop=True)


def source_audits(d: pd.DataFrame, label: str) -> None:
    # Local aggregate evidence only: no row identifiers or individual dates exported.
    disposition = (
        d.groupby(["disposition", "geography_valid", "onset_valid", "event_valid"], dropna=False)
        .size()
        .rename("records")
        .reset_index()
    )
    disposition.to_csv(OUT / f"{label}_reconciliation.csv", index=False)
    exceptions = (
        d[d.disposition.ne("included")]
        .groupby(["disposition", "mun_full", "ANO"], dropna=False)
        .size()
        .rename("records")
        .reset_index()
    )
    exceptions.to_csv(OUT / f"{label}_exceptions.csv", index=False)
    quality = []
    for field in ["TIP_CAS", "AJUSTE", "confirmados", "COD_EVE"]:
        for value, count in d[field].fillna("MISSING").value_counts().items():
            quality.append({"field": field, "value": value, "records": int(count)})
    pd.DataFrame(quality).to_csv(OUT / f"{label}_classification_counts.csv", index=False)
    identities = []
    for fields in [["CONSECUTIVE"], ["ANO", "CONSECUTIVE"], ["COD_EVE", "ANO", "CONSECUTIVE"]]:
        complete = d[fields].notna().all(axis=1) & d[fields].ne("").all(axis=1)
        identities.append(
            {
                "candidate_key": "+".join(fields),
                "complete_rows": int(complete.sum()),
                "rows_in_repeated_keys": int(d.loc[complete].duplicated(fields, keep=False).sum()),
                "interpretation": "not_patient_identity_no_automatic_deduplication",
            }
        )
    pd.DataFrame(identities).to_csv(OUT / f"{label}_identity_audit.csv", index=False)
    timing = []
    valid = d.INI_SIN_dt.notna()
    cutoff = d.INI_SIN_dt.dt.to_period("M").dt.to_timestamp(how="end")
    for field in ["FEC_NOT", "FEC_CON", "FEC_AJU", "FEC_ARC_XL"]:
        s = d[field + "_dt"]
        timing.append(
            {
                "field": field,
                "onset_comparable_rows": int(valid.sum()),
                "date_available_rows": int((valid & s.notna()).sum()),
                "date_missing_rows": int((valid & s.isna()).sum()),
                "after_onset_month_end": int((valid & s.gt(cutoff)).sum()),
                "cutoff": "hypothetical_onset_month_end_not_operational_approval",
            }
        )
    pd.DataFrame(timing).to_csv(OUT / f"{label}_availability_audit.csv", index=False)


def build_panels() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    record_inputs()
    c = catalog()
    c.to_csv(OUT / "municipality_catalog.csv", index=False)
    d = partition_epi(read_epi("dengue.csv"), c, "210")
    g = partition_epi(read_epi("dengue_grave.csv"), c, "220")
    source_audits(d, "dengue")
    source_audits(g, "severe")
    card = {
        "scope_records": len(d),
        "comparable_dates": int((d.INI_SIN_dt.notna() & d.FEC_NOT_dt.notna()).sum()),
        "anomalies": int(d.anomaly.sum()),
        "same_month": int((d.anomaly & d.same_month).sum()),
        "different_month": int((d.anomaly & ~d.same_month).sum()),
    }
    assert [card[k] for k in ["anomalies", "same_month", "different_month"]] == [8556, 784, 7772]
    save_json("anomaly_cardinality.json", card)
    d[d.anomaly].groupby(["disposition", "mun_full", "year_month", "same_month"]).size().rename(
        "records"
    ).reset_index().to_csv(OUT / "anomaly_distribution.csv", index=False)
    dv, gv = d[d.disposition.eq("included")], g[g.disposition.eq("included")]
    climate = monthly_climate(c)
    climate.to_csv(OUT / "climate_monthly.csv", index=False)
    severe = gv.groupby(KEY).size().rename("severe_recorded_count").reset_index()
    severe.to_csv(OUT / "severe_monthly.csv", index=False)
    start = min(dv.year_month.min(), gv.year_month.min(), climate.year_month.min())
    end = max(dv.year_month.max(), gv.year_month.max(), climate.year_month.max())
    grid = (
        pd.MultiIndex.from_product(
            [c.mun_full, pd.period_range(start, end, freq="M").astype(str)], names=KEY
        )
        .to_frame(index=False)
        .merge(c, on="mun_full")
    )
    baseline = aggregate_dengue(dv)
    inputs = {"s1": dv, "s2": dv[~dv.anomaly | dv.same_month], "s3": dv[~dv.anomaly]}
    for name, rows in inputs.items():
        p = join_panel(grid, aggregate_dengue(rows), severe, climate, baseline, name.upper())
        assert p.dengue_recorded_count.sum() == len(rows)
        assert p.severe_recorded_count.sum() == len(gv)
        p.to_csv(OUT / f"monthly_panel_{name}.csv", index=False)
    p.loc[
        p.climate_state.ne("complete"),
        KEY + ["climate_days", "expected_climate_days", "climate_state"],
    ].to_csv(OUT / "climate_gaps.csv", index=False)
    save_json(
        "metadata.json",
        {
            "created_utc": pd.Timestamp.now("UTC").isoformat(),
            "commit_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            "script_sha256": sha256(Path(__file__)),
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "municipalities": len(c),
            "start_month": start,
            "end_month": end,
            "dengue_scope": len(d),
            "dengue_included": len(dv),
            "severe_scope": len(g),
            "severe_included": len(gv),
            "reporting_completeness_evidence": "unavailable_confirmed_by_user",
            "source_strategy": "supplied_snapshot_read_only_no_network",
        },
    )
    validate_panels()
    print(json.dumps(json.loads((OUT / "metadata.json").read_text()), indent=2))


def panels() -> dict[str, pd.DataFrame]:
    return {
        s: pd.read_csv(OUT / f"monthly_panel_{s.lower()}.csv", dtype={"mun_full": str})
        for s in ["S1", "S2", "S3"]
    }


def validate_panels() -> None:
    ps = panels()
    c = catalog()
    baseline = ps["S1"]
    metadata = json.loads((OUT / "metadata.json").read_text())
    invariant_cols = [
        *KEY,
        "severe_recorded_count",
        "severe_count",
        "severe_observation_state",
        *CLIMATE,
        "climate_days",
        "climate_state",
    ]
    for p in ps.values():
        assert not p.duplicated(KEY).any()
        assert set(p.mun_full) == set(c.mun_full)
        pd.testing.assert_frame_equal(p[invariant_cols], baseline[invariant_cols])
        assert p.severe_recorded_count.sum() == metadata["severe_included"]
        assert p.loc[p.dengue_recorded_count.eq(0), "dengue_count"].isna().all()
        assert p.loc[p.severe_recorded_count.eq(0), "severe_count"].isna().all()
        assert p.reporting_completeness.eq("unknown").all()
        assert not p.operational_asof_eligible.any()
        assert p.loc[p.year_month.eq("2020-01"), "climate_days"].eq(0).all()
    for label in ["dengue", "severe"]:
        r = pd.read_csv(OUT / f"{label}_reconciliation.csv")
        assert r.records.sum() == metadata[f"{label}_scope"]
        assert r.loc[r.disposition.eq("included"), "records"].sum() == metadata[f"{label}_included"]
    for s in ["S2", "S3"]:
        assert (ps[s].dengue_recorded_count <= baseline.dengue_recorded_count).all()
        assert (
            ps[s]
            .loc[~ps[s].year_month.str.startswith("2013"), "scenario_removed_count"]
            .eq(0)
            .all()
        )
    print(
        "PASS: panel keys, source conservation, invariant support, unknown states and January 2020"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=["panel", "analysis", "rules", "validate"], required=True
    )
    args = parser.parse_args()
    if args.phase == "panel":
        build_panels()
    elif args.phase == "validate":
        validate_panels()
        record_inputs()
    else:
        raise NotImplementedError(f"Phase {args.phase} is not implemented yet")


if __name__ == "__main__":
    main()
