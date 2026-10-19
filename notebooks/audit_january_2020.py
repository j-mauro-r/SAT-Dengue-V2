"""Read-only January 2020 climate-source audit before filters or joins.

The script scans the raw CSV in streaming mode and writes compact evidence
artifacts under data/interim/stage2_january_2020_climate_audit by default.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

VARIABLES = [
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
EXPECTED_JANUARY = {f"2020-01-{day:02d}" for day in range(1, 32)}
PROVENANCE_SHA_2026_10_16 = "4287197dc1ce14fc442c3717ccc665e87970d1893d2b7d2c06e247647011f634"
ISO_DATETIME_RE = r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?([+-]\d{2}:?\d{2}|Z)?"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_digits(raw: str, width: int) -> str:
    value = (raw or "").strip()
    return value.zfill(width) if value.isdigit() and 1 <= len(value) <= width else ""


def date_format_bucket(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return "empty"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return "iso_yyyy_mm_dd"
    if re.fullmatch(ISO_DATETIME_RE, value):
        return "iso_datetime"
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        return "dmy_slash"
    return "other"


def parse_strict_iso_date(raw: str) -> str | None:
    value = (raw or "").strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def load_tolima_meta_catalog(catalog_path: Path) -> dict[str, dict[str, str]]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    result = {}
    for item in payload.get("resultado", []):
        dept = str(item.get("CODIGO_DEPARTAMENTO", "")).strip()
        mun = str(item.get("CODIGO_DPTO_MPIO", "")).strip()
        name = str(item.get("NOMBRE_MUNICIPIO", "")).strip()
        if dept in {"50", "73"} and mun.isdigit() and len(mun) == 5:
            result[mun] = {
                "department_code": dept,
                "department_name": "Meta" if dept == "50" else "Tolima",
                "municipality_name": name,
            }
    if len(result) != 76:
        raise SystemExit(f"Expected 76 Tolima/Meta municipalities, got {len(result)}")
    return result


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/interim/stage2_january_2020_climate_audit"),
        help="Directory where compact evidence artifacts are written.",
    )
    parser.add_argument(
        "--catalog-path",
        type=Path,
        default=Path("data/sources/Divipola-municipios.md"),
        help="DIVIPOLA municipalities JSON payload used as approved catalog source.",
    )
    parser.add_argument(
        "--print-report",
        action="store_true",
        help="Print January raw report JSON to stdout after writing artifacts.",
    )
    args = parser.parse_args()

    csv_path = args.csv_path.resolve()
    out_dir = args.out_dir.resolve()
    catalog_path = args.catalog_path.resolve()

    start_stats = csv_path.stat()
    source_sha = sha256(csv_path)
    catalog = load_tolima_meta_catalog(catalog_path)

    required_cols = ["date", "mpio_cdpmp", "dpto_ccdgo", *VARIABLES]

    total_rows = 0
    unique_dates = set()
    format_counts = Counter()
    invalid_date_rows = 0
    invalid_date_examples = Counter()

    january_distinct_dates = set()
    january_rows_by_date = Counter()
    january_rows_by_department = Counter()
    january_keys = Counter()
    january_municipality_days = defaultdict(set)

    january_rows_with_empty_municipality = 0
    january_rows_with_any_empty_variable = 0
    january_rows_with_all_variables_empty = 0
    january_rows_with_any_zero_value = 0

    variable_stats = {
        var: {
            "rows_empty": 0,
            "rows_nonempty": 0,
            "rows_finite": 0,
            "rows_invalid_numeric": 0,
            "rows_zero": 0,
        }
        for var in VARIABLES
    }

    daily_summary = {
        day: {
            "rows": 0,
            "municipalities": set(),
            "rows_with_any_empty_variable": 0,
            "rows_with_any_zero_variable": 0,
            "finite_counts": Counter(),
            "zero_counts": Counter(),
        }
        for day in EXPECTED_JANUARY
    }

    subset_rows = 0
    subset_rows_by_date = Counter()
    subset_days_by_municipality = defaultdict(set)
    subset_var_valid_days = defaultdict(lambda: defaultdict(set))
    subset_var_empty_rows = defaultdict(lambda: Counter())

    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        missing = sorted(set(required_cols) - set(reader.fieldnames or []))
        if missing:
            raise SystemExit(f"Missing required columns: {missing}; header={reader.fieldnames}")

        for row in reader:
            total_rows += 1
            raw_date = (row.get("date") or "").strip()
            format_counts[date_format_bucket(raw_date)] += 1

            iso_day = parse_strict_iso_date(raw_date)
            if iso_day is None:
                invalid_date_rows += 1
                invalid_date_examples[raw_date] += 1
                continue

            unique_dates.add(iso_day)
            if iso_day not in EXPECTED_JANUARY:
                continue

            january_distinct_dates.add(iso_day)
            january_rows_by_date[iso_day] += 1

            municipality = normalize_digits(row.get("mpio_cdpmp", ""), 5)
            department = normalize_digits(row.get("dpto_ccdgo", ""), 2)
            january_rows_by_department[department] += 1
            if not municipality:
                january_rows_with_empty_municipality += 1

            january_keys[(municipality, iso_day)] += 1
            january_municipality_days[municipality].add(iso_day)
            daily_summary[iso_day]["rows"] += 1
            daily_summary[iso_day]["municipalities"].add(municipality)

            any_empty = False
            all_empty = True
            any_zero = False
            for variable in VARIABLES:
                raw_value = (row.get(variable) or "").strip()
                if raw_value == "":
                    variable_stats[variable]["rows_empty"] += 1
                    any_empty = True
                    continue

                all_empty = False
                variable_stats[variable]["rows_nonempty"] += 1
                try:
                    number = float(raw_value)
                except ValueError:
                    variable_stats[variable]["rows_invalid_numeric"] += 1
                    continue

                if math.isfinite(number):
                    variable_stats[variable]["rows_finite"] += 1
                    daily_summary[iso_day]["finite_counts"][variable] += 1
                    if number == 0.0:
                        variable_stats[variable]["rows_zero"] += 1
                        daily_summary[iso_day]["zero_counts"][variable] += 1
                        any_zero = True
                else:
                    variable_stats[variable]["rows_invalid_numeric"] += 1

            if any_empty:
                january_rows_with_any_empty_variable += 1
                daily_summary[iso_day]["rows_with_any_empty_variable"] += 1
            if all_empty:
                january_rows_with_all_variables_empty += 1
            if any_zero:
                january_rows_with_any_zero_value += 1
                daily_summary[iso_day]["rows_with_any_zero_variable"] += 1

            if municipality in catalog:
                subset_rows += 1
                subset_rows_by_date[iso_day] += 1
                subset_days_by_municipality[municipality].add(iso_day)
                for variable in VARIABLES:
                    raw_value = (row.get(variable) or "").strip()
                    if raw_value == "":
                        subset_var_empty_rows[municipality][variable] += 1
                        continue
                    try:
                        number = float(raw_value)
                    except ValueError:
                        continue
                    if math.isfinite(number):
                        subset_var_valid_days[municipality][variable].add(iso_day)

    end_stats = csv_path.stat()
    if end_stats.st_size != start_stats.st_size or end_stats.st_mtime_ns != start_stats.st_mtime_ns:
        raise SystemExit("Source changed during audit. Re-run against a stable file.")

    out_dir.mkdir(parents=True, exist_ok=True)
    source_identity = {
        "generated_utc": datetime.now(UTC).isoformat(),
        "file_path": str(csv_path),
        "file_relpath": "data/raw/google_earth_engine.csv",
        "bytes": start_stats.st_size,
        "mtime_ns": start_stats.st_mtime_ns,
        "mtime_iso_utc": datetime.fromtimestamp(start_stats.st_mtime, tz=UTC).isoformat(),
        "sha256": source_sha,
        "source_provenance_reference_sha256_2026_10_16": PROVENANCE_SHA_2026_10_16,
        "matches_source_provenance_2026_10_16": source_sha == PROVENANCE_SHA_2026_10_16,
    }

    january_duplicate_key_rows = [
        {
            "municipality_code": municipality,
            "date": day,
            "rows": rows,
        }
        for (municipality, day), rows in sorted(january_keys.items())
        if rows > 1
    ]

    coverage_rows = []
    for municipality, meta in sorted(catalog.items()):
        present_days = subset_days_by_municipality.get(municipality, set())
        row = {
            "mun_full": municipality,
            "department_code": meta["department_code"],
            "department_name": meta["department_name"],
            "municipality_name": meta["municipality_name"],
            "days_present": len(present_days),
            "missing_days": len(EXPECTED_JANUARY - present_days),
            "present_in_january": len(present_days) > 0,
        }
        for variable in VARIABLES:
            row[variable + "_valid_days"] = len(subset_var_valid_days[municipality][variable])
            row[variable + "_empty_rows"] = subset_var_empty_rows[municipality][variable]
        coverage_rows.append(row)

    daily_rows = []
    for day in sorted(EXPECTED_JANUARY):
        record = daily_summary[day]
        row = {
            "date": day,
            "rows": record["rows"],
            "municipalities": len(record["municipalities"] - {""}),
            "rows_with_any_empty_variable": record["rows_with_any_empty_variable"],
            "rows_with_any_zero_variable": record["rows_with_any_zero_variable"],
        }
        for variable in VARIABLES:
            row[variable + "_finite_rows"] = record["finite_counts"][variable]
            row[variable + "_zero_rows"] = record["zero_counts"][variable]
        daily_rows.append(row)

    missing_entirely = sorted(
        [mun for mun in catalog if len(subset_days_by_municipality[mun]) == 0]
    )
    excess_duplicate_rows = int(sum(row["rows"] - 1 for row in january_duplicate_key_rows))
    municipalities_present = int(sum(1 for mun in catalog if subset_days_by_municipality[mun]))
    january_report = {
        "audit_scope": "Original CSV; no geographic filters, joins, imputations or data mutation",
        "date_parser_policy": {
            "accepted": "strict ISO YYYY-MM-DD only",
            "rejected_examples_recorded": True,
            "silent_ambiguity_conversion": False,
        },
        "rows": {
            "total_rows": total_rows,
            "invalid_date_rows": invalid_date_rows,
            "invalid_date_examples_top10": [
                {"raw_date": raw, "rows": count}
                for raw, count in invalid_date_examples.most_common(10)
            ],
            "date_format_counts": dict(sorted(format_counts.items())),
            "unique_dates_global": len(unique_dates),
        },
        "january": {
            "global": {
                "distinct_dates": len(january_distinct_dates),
                "missing_dates": sorted(EXPECTED_JANUARY - january_distinct_dates),
                "rows": int(sum(january_rows_by_date.values())),
                "rows_by_date": dict(sorted(january_rows_by_date.items())),
            },
            "national": {
                "rows": int(sum(january_rows_by_date.values())),
                "departments_present": len({k for k in january_rows_by_department if k}),
                "departments_rows": dict(sorted(january_rows_by_department.items())),
                "municipalities_present": len({k for k in january_municipality_days if k}),
                "rows_with_empty_municipality_code": january_rows_with_empty_municipality,
                "duplicate_municipality_date_keys": len(january_duplicate_key_rows),
                "excess_duplicate_rows": excess_duplicate_rows,
                "rows_with_any_empty_climate_field": january_rows_with_any_empty_variable,
                "rows_with_all_climate_fields_empty": january_rows_with_all_variables_empty,
                "rows_with_any_zero_climate_value": january_rows_with_any_zero_value,
            },
            "tolima_meta": {
                "expected_catalog_municipalities": len(catalog),
                "municipalities_present": municipalities_present,
                "missing_entirely_in_january": len(missing_entirely),
                "missing_entirely_codes": missing_entirely,
                "rows": subset_rows,
                "rows_by_date": dict(sorted(subset_rows_by_date.items())),
            },
        },
        "climate_variables": variable_stats,
        "distinctions": {
            "missing_dates": "dates absent from source after strict parsing",
            "empty_values": "rows present but one or more climate variable cells empty",
            "valid_zeros": "finite numeric zeros in present rows",
        },
        "limitations": [
            "Global presence of 31 dates does not prove complete municipality-by-day coverage.",
            "Finite numeric values do not certify physical plausibility "
            "or upstream extraction correctness.",
            "Historical CHIRPS/ERA5 availability does not prove this "
            "CSV contains all expected rows.",
        ],
    }

    (out_dir / "source_identity.json").write_text(
        json.dumps(source_identity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out_dir / "january_raw_audit.json").write_text(
        json.dumps(january_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_csv(
        out_dir / "january_catalog_coverage.csv",
        coverage_rows,
        [
            "mun_full",
            "department_code",
            "department_name",
            "municipality_name",
            "days_present",
            "missing_days",
            "present_in_january",
            *[v + "_valid_days" for v in VARIABLES],
            *[v + "_empty_rows" for v in VARIABLES],
        ],
    )
    write_csv(
        out_dir / "january_daily_coverage.csv",
        daily_rows,
        [
            "date",
            "rows",
            "municipalities",
            "rows_with_any_empty_variable",
            "rows_with_any_zero_variable",
            *[v + "_finite_rows" for v in VARIABLES],
            *[v + "_zero_rows" for v in VARIABLES],
        ],
    )
    write_csv(
        out_dir / "january_duplicates.csv",
        january_duplicate_key_rows,
        ["municipality_code", "date", "rows"],
    )

    if args.print_report:
        print(json.dumps(january_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
