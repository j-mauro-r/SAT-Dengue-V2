"""DEPRECATED: experimental EDA retired on 2026-10-19.

Retained at this path for historical reproduction and regression imports.
See docs/archive/experimental-eda/README.md and the active decision register.
Do not treat its outputs as current scientific acceptance or a required rerun.

Bounded Stage 2 review: independent source joins, explicit observation states.

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

try:
    from stage2_manifest_traceability import (
        MANIFEST_HISTORY_DIR,
        MANIFEST_PATH,
        MANIFEST_TRANSITION_LOG,
        ManifestTransitionContext,
        apply_manifest_transition,
    )
except ModuleNotFoundError:
    from scripts.stage2_manifest_traceability import (
        MANIFEST_HISTORY_DIR,
        MANIFEST_PATH,
        MANIFEST_TRANSITION_LOG,
        ManifestTransitionContext,
        apply_manifest_transition,
    )

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


def record_inputs(
    *,
    authorize_transition: bool = False,
    transition_reason: str | None = None,
    authorized_plan: str | None = None,
    transition_evidence_paths: list[str] | None = None,
    transition_backup_reference: str | None = None,
) -> None:
    hashes = {str(p.relative_to(ROOT)): sha256(p) for p in protected_inputs()}
    if MANIFEST_PATH.exists():
        apply_manifest_transition(
            manifest_path=MANIFEST_PATH,
            new_hashes=hashes,
            history_dir=MANIFEST_HISTORY_DIR,
            transition_log_path=MANIFEST_TRANSITION_LOG,
            context=ManifestTransitionContext(
                authorized=authorize_transition,
                reason=transition_reason,
                authorized_plan=authorized_plan,
                evidence_paths=transition_evidence_paths or [],
                backup_reference=transition_backup_reference,
            ),
        )
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


def build_panels(args: argparse.Namespace) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    record_inputs(
        authorize_transition=args.authorize_hash_transition,
        transition_reason=args.transition_reason,
        authorized_plan=args.authorized_plan,
        transition_evidence_paths=args.transition_evidence_path,
        transition_backup_reference=args.transition_backup_reference,
    )
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


def assert_climate_days_conservation(panel: pd.DataFrame, climate_monthly: pd.DataFrame) -> None:
    source = climate_monthly[KEY + ["climate_days"]].copy()
    source["climate_days"] = source["climate_days"].astype(int)
    source_idx = source.set_index(KEY)["climate_days"]

    current = panel[KEY + ["climate_days"]].copy()
    current_idx = current.set_index(KEY)["climate_days"].astype(int)

    present = current_idx.index.intersection(source_idx.index)
    missing = current_idx.index.difference(source_idx.index)

    if len(present):
        pd.testing.assert_series_equal(
            current_idx.loc[present].sort_index(),
            source_idx.loc[present].sort_index(),
            check_names=False,
        )
    if len(missing):
        assert current_idx.loc[missing].eq(0).all()


def validate_panels() -> None:
    ps = panels()
    c = catalog()
    baseline = ps["S1"]
    climate_monthly = pd.read_csv(OUT / "climate_monthly.csv", dtype={"mun_full": str})
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
        assert_climate_days_conservation(p, climate_monthly)
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
    print("PASS: panel keys, source conservation, invariant support, unknown states")


def date_pair_metrics(matched: pd.DataFrame) -> dict[str, int]:
    columns = ["ini_current", "not_current", "ini_reference", "not_reference"]
    valid = matched[columns].notna().all(axis=1)
    m = matched.loc[valid]
    inverted = m.ini_current.eq(m.not_reference) & m.not_current.eq(m.ini_reference)
    equal = m.ini_current.eq(m.not_current)
    return {
        "matched_rows": len(matched),
        "comparable_pairs": len(m),
        "identical_both_fields": int(
            (m.ini_current.eq(m.ini_reference) & m.not_current.eq(m.not_reference)).sum()
        ),
        "naive_inverted_pairs": int(inverted.sum()),
        "equal_date_inverted_pairs": int((inverted & equal).sum()),
        "genuine_non_equal_inverted_pairs": int((inverted & ~equal).sum()),
        "current_anomalies": int(m.ini_current.gt(m.not_current).sum()),
        "reference_anomalies": int(m.ini_reference.gt(m.not_reference).sum()),
    }


def annual_reference_audit() -> None:
    d = read_epi("dengue.csv")
    result = []
    for year in [2012, 2013, 2014]:
        path = ROOT / f"data/sources/Dengue_Datos_{year}_210.xlsx"
        r = pd.read_excel(
            path,
            usecols=["CONSECUTIVE", "COD_DPTO_R", "COD_MUN_R", "INI_SIN", "FEC_NOT"],
            dtype=str,
        )
        r = r[code(r.COD_DPTO_R, 2).isin(["50", "73"])].copy()
        current = d[d.ANO.eq(str(year))].copy()
        r["ini_reference"], r["not_reference"] = parse_date(r.INI_SIN), parse_date(r.FEC_NOT)
        current["ini_current"], current["not_current"] = current.INI_SIN_dt, current.FEC_NOT_dt
        # Within-year export-key matching only; never assert patient identity.
        key = "CONSECUTIVE"
        ru = r[r[key].notna() & ~r.duplicated(key, keep=False)]
        cu = current[current[key].notna() & ~current.duplicated(key, keep=False)]
        m = cu.merge(ru, on=key, suffixes=("_current", "_reference"), validate="one_to_one")
        metrics = date_pair_metrics(m)
        metrics.update(
            {
                "source_year": year,
                "reference_scope_rows": len(r),
                "current_year_rows": len(current),
                "reference_ambiguous_key_rows": len(r) - len(ru),
                "current_ambiguous_key_rows": len(current) - len(cu),
                "reference_unmatched_unique_rows": len(ru) - len(m),
                "same_raw_onset": int(
                    m.INI_SIN_current.fillna("").eq(m.INI_SIN_reference.fillna("")).sum()
                ),
                "same_raw_notification": int(
                    m.FEC_NOT_current.fillna("").eq(m.FEC_NOT_reference.fillna("")).sum()
                ),
            }
        )
        result.append(metrics)
        print(
            "Annual reference:",
            year,
            metrics["matched_rows"],
            "matched;",
            metrics["genuine_non_equal_inverted_pairs"],
            "genuine inverted pairs",
            flush=True,
        )
    pd.DataFrame(result).to_csv(OUT / "annual_reference_date_audit.csv", index=False)


def rho(x: pd.Series, y: pd.Series) -> float:
    valid = x.notna() & y.notna()
    if valid.sum() < 8 or x[valid].nunique() < 2 or y[valid].nunique() < 2:
        return float("nan")
    return float(x[valid].rank().corr(y[valid].rank()))


def adjusted_rho(frame: pd.DataFrame, feature: str) -> float:
    """Rank association adjusted within municipality; no self-conditioning."""
    if len(frame) < 20 or frame[feature].nunique() < 2 or frame.target.nunique() < 2:
        return float("nan")
    x, y = frame[feature].rank(), frame.target.rank()
    periods = pd.PeriodIndex(frame.year_month, freq="M")
    controls = pd.DataFrame(
        {
            "trend": periods.asi8.astype(float),
            "sin_month": np.sin(2 * np.pi * periods.month / 12),
            "cos_month": np.cos(2 * np.pi * periods.month / 12),
        },
        index=frame.index,
    )
    if feature != "dengue_count":
        controls["current_dengue_rank"] = frame.dengue_count.rank()
    # Demeaning is equivalent to municipality fixed effects in least squares.
    group = frame.mun_full
    x = x - x.groupby(group).transform("mean")
    y = y - y.groupby(group).transform("mean")
    controls = controls - controls.groupby(group).transform("mean")
    design = controls.to_numpy(dtype=float)
    rx = x.to_numpy() - design @ np.linalg.lstsq(design, x, rcond=None)[0]
    ry = y.to_numpy() - design @ np.linalg.lstsq(design, y, rcond=None)[0]
    if np.std(rx) < 1e-12 or np.std(ry) < 1e-12:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def common_support(frames: dict[str, pd.DataFrame], feature: str) -> pd.Series:
    valid = pd.Series(True, index=frames["S1"].index)
    for f in frames.values():
        valid &= f.common_source_window & f.target_window.fillna(False).astype(bool)
        valid &= f[feature].notna() & f.target.notna() & f.dengue_count.notna()
        if feature in CLIMATE:
            valid &= f[feature + "_valid_days"].eq(f.expected_climate_days)
    return valid


def repeat_associations(ps: dict[str, pd.DataFrame]) -> None:
    raw, adjusted, municipal = [], [], []
    muni_features = [
        "severe_count",
        "confirmed_prop",
        "median_delay_days",
        "rain_mm_day",
        "temp_mean_c",
    ]
    for horizon in [0, 1, 2]:
        frames = {}
        for name, p in ps.items():
            f = p.copy()
            f["target"] = f.groupby("mun_full").dengue_count.shift(-horizon)
            f["target_window"] = f.groupby("mun_full").common_source_window.shift(-horizon)
            frames[name] = f
        for feature in FEATURES:
            if feature == "dengue_count" and horizon == 0:
                continue
            valid = common_support(frames, feature)
            for scenario, f in frames.items():
                data = f.loc[valid].copy()
                for level, group in [
                    ("pooled", data),
                    *[(f"department:{dept}", g) for dept, g in data.groupby("department_name")],
                ]:
                    base = {
                        "scenario": scenario,
                        "level": level,
                        "feature": feature,
                        "horizon": horizon,
                        "n_obs": len(group),
                        "support": "same_keys_all_scenarios_observed_positive_dengue_pairs",
                        "inference": "descriptive_only_no_validated_p_values",
                    }
                    raw.append({**base, "rho": rho(group[feature], group.target)})
                    if horizon:
                        adjusted.append(
                            {
                                **base,
                                "rho": adjusted_rho(group, feature),
                                "controls": "municipality+trend+sin+cos"
                                + ("+current_dengue_rank" if feature != "dengue_count" else ""),
                            }
                        )
                if horizon and feature in muni_features:
                    for mun, group in data.groupby("mun_full"):
                        municipal.append(
                            {
                                "scenario": scenario,
                                "mun_full": mun,
                                "feature": feature,
                                "horizon": horizon,
                                "n_obs": len(group),
                                "rho": rho(group[feature], group.target),
                            }
                        )
    raw_df, adj_df = pd.DataFrame(raw), pd.DataFrame(adjusted)
    raw_df.to_csv(OUT / "associations_raw.csv", index=False)
    adj_df.to_csv(OUT / "associations_controlled.csv", index=False)
    pd.DataFrame(municipal).to_csv(OUT / "associations_municipal.csv", index=False)
    stability = []
    for label, df in [("raw", raw_df), ("controlled", adj_df)]:
        for keys, group in df.groupby(["level", "feature", "horizon"]):
            values = group.set_index("scenario").rho.reindex(["S1", "S2", "S3"])
            complete = values.notna().all()
            signs_same = bool(complete and (np.sign(values) == np.sign(values.iloc[0])).all())
            delta = float(values.max() - values.min()) if complete else np.nan
            stability.append(
                {
                    "analysis_type": label,
                    "level": keys[0],
                    "feature": keys[1],
                    "horizon": keys[2],
                    "complete_three_scenarios": complete,
                    "max_rho_difference": delta,
                    "sign_consistent": signs_same,
                    "descriptive_stability": bool(complete and signs_same and delta < 0.10),
                }
            )
    pd.DataFrame(stability).to_csv(OUT / "associations_stability_summary.csv", index=False)
    for label, df in [("raw", raw_df), ("controlled", adj_df)]:
        old = pd.read_csv(PREVIOUS / f"associations_{label}.csv")
        old = old[["scenario", "level", "feature", "horizon", "rho", "n_obs"]]
        df.merge(
            old, on=["scenario", "level", "feature", "horizon"], suffixes=("_review", "_previous")
        ).to_csv(OUT / f"associations_{label}_comparison.csv", index=False)
    (OUT / "associations_method_notes.md").write_text(
        "# Bounded association rerun\n\n"
        "Source window: 2007-01 through 2025-12, restricted at both ends of each lead. "
        "Unknown reporting months never become disease zeros. The support is the intersection "
        "of observed current/future dengue and available feature values across S1/S2/S3; "
        "severe without records stays unknown and climate requires complete daily coverage. "
        "This is a selected positive-record sample, not the entire municipal population. "
        "Counts are notification rows, not deduplicated cases. "
        "Missingness/selection can bias associations.\n\n"
        "Raw Spearman repeats t, t+1 and t+2. Adjusted ranked lead associations remove municipal "
        "fixed effects, a linear calendar trend and one annual sine/cosine pair; current dengue "
        "rank is added only for other features. Contemporaneous adjusted results and adjusting "
        "dengue on itself are omitted as uninterpretable. These simple controls do not establish "
        "complete removal of serial dependence, nonlinear seasonality or confounding.\n\n"
        "P-values and BH are not reissued: the previous 80-shift test could return zero and "
        "compressed time across missing months. "
        "A valid inferential design has not been established "
        "for this missing-coverage panel. Correlations are descriptive, not significance, causal "
        "or predictive evidence. Comparisons to PLAN_005 change both sample and controls and "
        "must not attribute differences to a single fix. No feature ranking is approved.\n"
    )


def sensitivity_tables(ps: dict[str, pd.DataFrame]) -> None:
    base = ps["S1"]
    summary, monthly, peaks = [], [], []
    for scenario, p in ps.items():
        for dept, g in p.groupby("department_name"):
            b = base[base.department_name.eq(dept)]
            y = g[g.year_month.str.startswith("2013")]
            by = b[b.year_month.str.startswith("2013")]
            summary.append(
                {
                    "scenario": scenario,
                    "department_name": dept,
                    "retained_records": int(g.dengue_recorded_count.sum()),
                    "removed_records": int(g.scenario_removed_count.sum()),
                    "baseline_records": int(b.dengue_recorded_count.sum()),
                    "baseline_2013": int(by.dengue_recorded_count.sum()),
                    "retained_2013": int(y.dengue_recorded_count.sum()),
                    "severe_records": int(g.severe_recorded_count.sum()),
                }
            )
        y = p[p.year_month.str.startswith("2013")].copy()
        y["removed_pct_of_s1"] = (
            100 * y.scenario_removed_count / y.dengue_s1_recorded_count.replace(0, np.nan)
        )
        monthly.append(
            y[
                KEY
                + [
                    "municipality_name",
                    "department_name",
                    "scenario",
                    "dengue_recorded_count",
                    "dengue_s1_recorded_count",
                    "scenario_removed_count",
                    "removed_pct_of_s1",
                ]
            ]
        )
        for mun, g in y.groupby("mun_full"):
            maximum = int(g.dengue_recorded_count.max())
            peaks.append(
                {
                    "scenario": scenario,
                    "mun_full": mun,
                    "peak_recorded_count_2013": maximum,
                    "peak_months_2013": "|".join(
                        g.loc[g.dengue_recorded_count.eq(maximum), "year_month"]
                    )
                    if maximum > 0
                    else "",
                    "months_with_retained_records_2013": int(g.dengue_recorded_count.gt(0).sum()),
                }
            )
    pd.DataFrame(summary).to_csv(OUT / "sensitivity_summary_by_geo.csv", index=False)
    pd.concat(monthly).to_csv(OUT / "sensitivity_2013_municipality_month.csv", index=False)
    pd.DataFrame(peaks).to_csv(OUT / "sensitivity_2013_peaks.csv", index=False)
    # Descriptive comparator, fixed across scenarios, using only 2007–2012 history.
    hist = base[
        base.year_month.between("2007-01", "2012-12") & base.dengue_recorded_count.gt(0)
    ].copy()
    hist["calendar_month"] = hist.year_month.str[5:]
    reference = (
        hist.groupby(["mun_full", "calendar_month"])
        .agg(
            prior_observed_years=("year_month", "size"),
            prior_max_recorded=("dengue_recorded_count", "max"),
        )
        .reset_index()
    )
    flags = []
    for p in ps.values():
        y = p[p.year_month.str.startswith("2013")].copy()
        y["calendar_month"] = y.year_month.str[5:]
        y = y.merge(reference, on=["mun_full", "calendar_month"], how="left")
        eligible = y.prior_observed_years.ge(3) & y.dengue_s1_recorded_count.gt(0)
        y["above_prior_observed_max"] = (
            y.dengue_recorded_count.gt(y.prior_max_recorded).astype("boolean").where(eligible)
        )
        y["comparison_status"] = np.where(
            eligible,
            "descriptive_only_not_endemic_channel",
            "insufficient_observed_history_or_no_baseline_records",
        )
        flags.append(
            y[
                KEY
                + [
                    "scenario",
                    "dengue_recorded_count",
                    "prior_observed_years",
                    "prior_max_recorded",
                    "above_prior_observed_max",
                    "comparison_status",
                ]
            ]
        )
    pd.concat(flags).to_csv(OUT / "descriptive_2013_exceptional_months.csv", index=False)


def validate_sensitivity() -> None:
    ps = panels()
    a = pd.read_csv(OUT / "anomaly_distribution.csv", dtype={"mun_full": str})
    included = a[a.disposition.eq("included")]
    for scenario in ["S2", "S3"]:
        expected = included if scenario == "S3" else included[~included.same_month]
        assert ps[scenario].scenario_removed_count.sum() == expected.records.sum()
    summary = pd.read_csv(OUT / "sensitivity_summary_by_geo.csv")
    assert summary.groupby("department_name").severe_records.nunique().eq(1).all()
    for label in ["raw", "controlled"]:
        df = pd.read_csv(OUT / f"associations_{label}.csv")
        assert df.groupby(["level", "feature", "horizon"]).n_obs.nunique().eq(1).all()
        if label == "controlled":
            assert df.horizon.gt(0).all()
            assert (
                ~df.loc[df.feature.eq("dengue_count"), "controls"]
                .str.contains("current_dengue")
                .any()
            )
    annual = pd.read_csv(OUT / "annual_reference_date_audit.csv")
    assert set(annual.source_year) == {2012, 2013, 2014}
    assert annual.matched_rows.gt(0).all()
    assert annual.matched_rows.eq(annual.reference_scope_rows).all()
    assert annual.comparable_pairs.gt(0).all()
    assert annual.reference_unmatched_unique_rows.eq(0).all()
    assert annual.genuine_non_equal_inverted_pairs.eq(0).all()
    assert annual.naive_inverted_pairs.eq(annual.equal_date_inverted_pairs).all()
    print("PASS: local scenario losses, fixed support, adjusted controls and equal-date audit")


def run_analysis() -> None:
    validate_panels()
    ps = panels()
    sensitivity_tables(ps)
    annual_reference_audit()
    repeat_associations(ps)
    validate_sensitivity()


def eligibility_table(p: pd.DataFrame) -> pd.DataFrame:
    d = p[p.common_source_window].copy()
    for horizon in [1, 2]:
        future = d.groupby("mun_full").dengue_count.shift(-horizon)
        d[f"observed_pair_t{horizon}"] = d.dengue_count.notna() & future.notna()
    d["observed_dengue"] = d.dengue_count.notna()
    d["observed_severe"] = d.severe_count.notna()
    d["complete_climate"] = d.climate_state.eq("complete")
    for col in CLIMATE:
        d["complete_climate"] &= d[col + "_valid_days"].eq(d.expected_climate_days)
    result = (
        d.groupby(["mun_full", "municipality_name", "department_name"])
        .agg(
            calendar_months=("year_month", "size"),
            dengue_observed_months=("observed_dengue", "sum"),
            severe_observed_months=("observed_severe", "sum"),
            climate_complete_months=("complete_climate", "sum"),
            observed_pairs_t1=("observed_pair_t1", "sum"),
            observed_pairs_t2=("observed_pair_t2", "sum"),
        )
        .reset_index()
    )
    result["dengue_no_records_months"] = result.calendar_months - result.dengue_observed_months
    result["reporting_completeness"] = "unknown"
    result["operational_eligible"] = False
    result["reason"] = "no_asof_snapshots_or_reporting_completeness_evidence"
    return result


def retrospective_rules() -> dict:
    return {
        "version": "stage2-review-v1",
        "status": "bounded_retrospective_rules_not_final_data_contract",
        "authority": "User-authorized three-step review; no extra reporting-completeness knowledge",
        "population": (
            "source notification rows by residence; not unique patients or confirmed incidence"
        ),
        "streams": {"dengue": "COD_EVE=210", "severe": "COD_EVE=220", "combine": False},
        "municipality": (
            "exact membership in supplied current DIVIPOLA catalog; historical changes unverified"
        ),
        "onset": "INI_SIN parsed day/month/year; no substitute or date swap",
        "missing_onset": "exclude from monthly placement; retain aggregate reconciliation",
        "unknown_geography": "quarantine with aggregate counts; no inferred assignment",
        "case_inclusion": (
            "all provided stream rows meeting geography and onset rules; no confirmed-only filter"
        ),
        "classification": (
            "TIP_CAS initial, AJUSTE adjustment, confirmados supplied "
            "retrospective flag; no inferred clinical severity equivalence"
        ),
        "duplicates": (
            "retain rows; audit CONSECUTIVE and year/event composite keys; no "
            "patient-level deduplication authority"
        ),
        "zero_policy": "recorded_count=0 means no retained rows; no certified disease zeros",
        "absence": "unknown_reporting; scenario removal is a separate state",
        "climate": (
            "independent monthly daily-variable means plus observed and expected "
            "day counts; no imputation; complete months for correlations"
        ),
        "scenario_policy": "S1/S2/S3 retained as uncertainty alternatives; production choice open",
        "retrospective_window": ["2007-01", "2025-12"],
        "association_support": (
            "same keys across scenarios, observed current/future dengue, "
            "available feature; selected sample only"
        ),
        "cutoff_audit": (
            "hypothetical month end for timing counts; exact operational schedule "
            "and maturation policy open"
        ),
        "timing_semantics": {
            "INI_SIN": "event date",
            "FEC_NOT": "notification date, not full availability proof",
            "FEC_AJU": "entry/latest adjustment, not version history",
            "FEC_ARC_XL": "export generation, not first record availability",
        },
        "historical_availability_reconstructed": False,
        "operational_feature_use_approved": False,
        "G2_closed": False,
        "open_decisions": [
            "final case population and episode identity",
            "historical territorial applicability",
            "reporting completeness and true zeros",
            "January 2020 climate lineage",
            "2013 source lineage and cleaning policy",
            "historical versioned availability",
            "operational cutoff and maturation",
            "prediction eligibility minimum history",
            "endemic channel, target Y and Data Contract",
        ],
    }


def write_rules() -> None:
    ps = panels()
    save_json("retrospective_rules.json", retrospective_rules())
    eligibility_table(ps["S1"]).to_csv(OUT / "municipality_coverage_eligibility.csv", index=False)
    frames = []
    for label in ["dengue", "severe"]:
        a = pd.read_csv(OUT / f"{label}_availability_audit.csv")
        a.insert(0, "stream", label)
        a["after_month_end_pct"] = 100 * a.after_onset_month_end / a.onset_comparable_rows
        a["asof_interpretation"] = "timing_warning_only_not_reconstructed_historical_availability"
        frames.append(a)
    pd.concat(frames).to_csv(OUT / "availability_summary.csv", index=False)
    b = ps["S1"]
    old = pd.read_csv(PREVIOUS / "monthly_panel_s1.csv", dtype={"mun_full": str})
    joined = b.merge(
        old[KEY + ["severe_count", "temp_mean_c"]], on=KEY, suffixes=("_review", "_previous")
    )
    summary = {
        "panel_rows": len(b),
        "municipalities": b.mun_full.nunique(),
        "included_dengue": int(b.dengue_recorded_count.sum()),
        "included_severe": int(b.severe_recorded_count.sum()),
        "recovered_identified_severe_records": int(
            joined.loc[joined.severe_count_previous.isna(), "severe_recorded_count"].sum()
        ),
        "recovered_temperature_cells": int(
            (joined.temp_mean_c_previous.isna() & joined.temp_mean_c_review.notna()).sum()
        ),
        "scenario_totals": {s: int(p.dengue_recorded_count.sum()) for s, p in ps.items()},
        "certified_zero_months": 0,
        "operational_eligible_months": 0,
        "population_warning": "notification rows; retrospective; no operational proof",
    }
    save_json("review_summary.json", summary)
    validate_rules()
    print(json.dumps(summary, indent=2))


def validate_rules() -> None:
    r = json.loads((OUT / "retrospective_rules.json").read_text())
    assert not r["historical_availability_reconstructed"]
    assert not r["operational_feature_use_approved"] and not r["G2_closed"]
    assert not r["streams"]["combine"]
    c = pd.read_csv(OUT / "municipality_coverage_eligibility.csv", dtype={"mun_full": str})
    assert set(c.mun_full) == set(catalog().mun_full)
    assert len(c) == 76 and c.calendar_months.eq(228).all()
    assert not c.operational_eligible.any()
    assert (c.dengue_observed_months + c.dengue_no_records_months).eq(c.calendar_months).all()
    a = pd.read_csv(OUT / "availability_summary.csv")
    assert len(a) == 8
    assert a.after_onset_month_end.le(a.date_available_rows).all()
    assert (a.date_available_rows + a.date_missing_rows).eq(a.onset_comparable_rows).all()
    assert (ROOT / "docs/product/stage-2/DATA-04-retrospective-use-rules.md").exists()
    print("PASS: retrospective rules, availability denominators and no operational approval")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--phase", choices=["panel", "analysis", "rules", "validate"], required=True
    )
    parser.add_argument("--authorize-hash-transition", action="store_true")
    parser.add_argument("--transition-reason")
    parser.add_argument("--authorized-plan")
    parser.add_argument("--transition-evidence-path", action="append", default=[])
    parser.add_argument("--transition-backup-reference")
    args = parser.parse_args()
    if args.phase == "panel":
        build_panels(args)
    elif args.phase == "analysis":
        run_analysis()
    elif args.phase == "rules":
        write_rules()
    elif args.phase == "validate":
        validate_panels()
        validate_sensitivity()
        validate_rules()
        record_inputs(
            authorize_transition=args.authorize_hash_transition,
            transition_reason=args.transition_reason,
            authorized_plan=args.authorized_plan,
            transition_evidence_paths=args.transition_evidence_path,
            transition_backup_reference=args.transition_backup_reference,
        )
    else:
        raise NotImplementedError(f"Phase {args.phase} is not implemented yet")


if __name__ == "__main__":
    main()
