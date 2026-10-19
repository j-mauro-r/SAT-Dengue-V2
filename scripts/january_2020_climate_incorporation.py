"""Safely incorporate recovered January 2020 climate rows into raw source.

This script supports two modes:
- precheck: baseline identity, disk space, backup, candidate validation, overlap analysis.
- apply: precheck plus conditional append via same-filesystem temp file and atomic replace.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "date",
    "year",
    "month",
    "day_of_year",
    "dpto_ccdgo",
    "dpto_cnmbr",
    "mpio_ccdgo",
    "mpio_cdpmp",
    "mpio_cnmbr",
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
VARIABLE_COLUMNS = REQUIRED_COLUMNS[9:]
KEY_COLUMNS = ["date", "mpio_cdpmp"]


@dataclass
class Paths:
    root: Path
    raw_path: Path
    candidate_path: Path
    catalog_path: Path
    prior_audit_dir: Path
    evidence_dir: Path
    backup_dir: Path
    dengue_path: Path
    severe_path: Path


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_code(raw: str, width: int) -> str:
    value = str(raw or "").strip()
    return value.zfill(width)


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    out = {column: str(row.get(column, "") or "").strip() for column in REQUIRED_COLUMNS}
    out["dpto_ccdgo"] = normalize_code(out["dpto_ccdgo"], 2)
    out["mpio_ccdgo"] = normalize_code(out["mpio_ccdgo"], 3)
    out["mpio_cdpmp"] = normalize_code(out["mpio_cdpmp"], 5)
    return out


def canonical_signature(row: dict[str, str]) -> tuple[str, ...]:
    norm = normalize_row(row)
    values = [norm[column] for column in REQUIRED_COLUMNS[:9]]
    for column in VARIABLE_COLUMNS:
        value = norm[column]
        try:
            number = float(value)
        except ValueError:
            values.append(f"invalid:{value}")
            continue
        if not math.isfinite(number):
            values.append("nonfinite")
            continue
        values.append(f"{number:.15g}")
    return tuple(values)


def ensure_required_header(path: Path) -> list[str]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        header = next(reader)
    if header != REQUIRED_COLUMNS:
        raise ValueError(f"Unexpected schema in {path}: {header}")
    return header


def load_catalog_codes(catalog_path: Path, expected_count: int | None = 76) -> list[str]:
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))
    codes = sorted(
        {
            str(row.get("CODIGO_DPTO_MPIO", "")).strip()
            for row in payload.get("resultado", [])
            if str(row.get("CODIGO_DEPARTAMENTO", "")).strip() in {"50", "73"}
        }
    )
    if expected_count is not None and len(codes) != expected_count:
        raise ValueError(f"Expected {expected_count} catalog municipality codes, got {len(codes)}")
    return codes


def validate_candidate(
    candidate_path: Path,
    catalog_codes: list[str],
    require_full_grid: bool,
) -> tuple[pd.DataFrame, dict[str, object]]:
    ensure_required_header(candidate_path)
    candidate = pd.read_csv(candidate_path, dtype=str)
    for column, width in [("dpto_ccdgo", 2), ("mpio_ccdgo", 3), ("mpio_cdpmp", 5)]:
        candidate[column] = candidate[column].fillna("").astype(str).str.strip().str.zfill(width)
    for column in ["date", "year", "month", "day_of_year", "dpto_cnmbr", "mpio_cnmbr"]:
        candidate[column] = candidate[column].fillna("").astype(str).str.strip()

    parsed = pd.to_datetime(candidate["date"], format="%Y-%m-%d", errors="coerce")
    if parsed.isna().any():
        raise ValueError("Candidate has invalid date values")
    if not parsed.dt.year.astype(str).eq(candidate["year"]).all():
        raise ValueError("Candidate year values do not match date")
    if not parsed.dt.month.astype(str).str.zfill(2).eq(candidate["month"].str.zfill(2)).all():
        raise ValueError("Candidate month values do not match date")
    if not parsed.dt.dayofyear.astype(str).eq(candidate["day_of_year"]).all():
        raise ValueError("Candidate day_of_year values do not match date")

    if not candidate["mpio_cdpmp"].str[:2].eq(candidate["dpto_ccdgo"]).all():
        raise ValueError("Candidate dpto_ccdgo mismatch with mpio_cdpmp")
    if not candidate["mpio_cdpmp"].str[2:].eq(candidate["mpio_ccdgo"]).all():
        raise ValueError("Candidate mpio_ccdgo mismatch with mpio_cdpmp")

    if candidate[KEY_COLUMNS].duplicated().any():
        raise ValueError("Candidate has duplicate date+mpio_cdpmp keys")

    for column in VARIABLE_COLUMNS:
        numbers = pd.to_numeric(candidate[column], errors="coerce")
        if numbers.isna().any() or not pd.Series(numbers).map(math.isfinite).all():
            raise ValueError(f"Candidate has invalid numeric values in {column}")

    key_set = set(map(tuple, candidate[KEY_COLUMNS].to_numpy()))
    expected_dates = [d.strftime("%Y-%m-%d") for d in pd.date_range("2020-01-01", "2020-01-31")]
    expected_key_set = {(date, code) for date in expected_dates for code in catalog_codes}
    if require_full_grid and key_set != expected_key_set:
        raise ValueError("Candidate key coverage is not the required 76x31 grid")

    report = {
        "generated_utc": now_utc(),
        "candidate_relpath": str(candidate_path),
        "candidate_sha256": file_sha256(candidate_path),
        "candidate_rows": int(len(candidate)),
        "candidate_unique_keys": int(len(key_set)),
        "candidate_dates": int(candidate["date"].nunique()),
        "candidate_municipalities": int(candidate["mpio_cdpmp"].nunique()),
        "candidate_schema_valid": True,
        "candidate_numeric_finite": True,
        "catalog_municipalities_expected": len(catalog_codes),
        "required_full_grid": require_full_grid,
    }
    return candidate, report


def raw_identity(raw_path: Path) -> dict[str, object]:
    stat = raw_path.stat()
    return {
        "raw_relpath": str(raw_path),
        "raw_bytes": stat.st_size,
        "raw_mtime_ns": stat.st_mtime_ns,
        "raw_mtime_iso_utc": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        "raw_sha256": file_sha256(raw_path),
    }


def baseline_identity(paths: Paths) -> dict[str, object]:
    baseline = raw_identity(paths.raw_path)
    prior_identity = json.loads((paths.prior_audit_dir / "source_identity.json").read_text())
    prior_audit = json.loads((paths.prior_audit_dir / "january_raw_audit.json").read_text())
    changed = {
        "sha256_changed": baseline["raw_sha256"] != prior_identity["sha256"],
        "bytes_changed": baseline["raw_bytes"] != prior_identity["bytes"],
        "mtime_changed": baseline["raw_mtime_ns"] != prior_identity["mtime_ns"],
    }
    return {
        "generated_utc": now_utc(),
        **baseline,
        "prior_audit_sha256": prior_identity["sha256"],
        "prior_audit_bytes": prior_identity["bytes"],
        "prior_january_rows_global": prior_audit["january"]["global"]["rows"],
        "prior_january_rows_tolima_meta": prior_audit["january"]["tolima_meta"]["rows"],
        "changed_vs_prior": changed,
        "investigation_needed_before_modification": any(changed.values()),
    }


def disk_space_check(paths: Paths) -> dict[str, object]:
    usage = shutil.disk_usage(paths.raw_path.parent)
    required = paths.raw_path.stat().st_size * 3 + paths.candidate_path.stat().st_size
    return {
        "generated_utc": now_utc(),
        "filesystem": str(paths.raw_path.parent),
        "free_bytes": usage.free,
        "required_bytes_estimate": required,
        "enough_space": usage.free >= required,
        "assumptions": "raw + backup + temp_updated + candidate_margin",
    }


def create_or_reuse_backup(paths: Paths, source_sha: str, source_size: int) -> dict[str, object]:
    metadata_path = paths.evidence_dir / "backup_metadata.json"
    if metadata_path.exists():
        existing = json.loads(metadata_path.read_text())
        backup_path = paths.root / existing["backup_relpath"]
        if backup_path.exists():
            if file_sha256(backup_path) == source_sha and backup_path.stat().st_size == source_size:
                existing["generated_utc"] = now_utc()
                existing["reused_existing"] = True
                metadata_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n")
                return existing

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    for _ in range(5):
        name = f"google_earth_engine.pre_incorp_jan2020.{stamp}.{uuid.uuid4().hex[:8]}.csv"
        backup_path = paths.backup_dir / name
        if not backup_path.exists():
            break
    else:
        raise RuntimeError("Unable to allocate unique backup filename")

    shutil.copy2(paths.raw_path, backup_path)
    backup_sha = file_sha256(backup_path)
    check_ignore = subprocess.run(
        ["git", "check-ignore", str(backup_path)],
        capture_output=True,
        text=True,
        cwd=paths.root,
    )
    in_git_repo = (paths.root / ".git").exists()
    git_ignored = check_ignore.returncode == 0
    git_ignore_mode = "checked"
    if not in_git_repo and check_ignore.returncode not in (0, 1):
        # Unit tests use synthetic non-git temp workspaces.
        git_ignored = True
        git_ignore_mode = "not_checked_non_git_workspace"
    meta = {
        "generated_utc": now_utc(),
        "created": True,
        "reused_existing": False,
        "backup_relpath": str(backup_path.relative_to(paths.root)),
        "backup_bytes": backup_path.stat().st_size,
        "backup_sha256": backup_sha,
        "source_bytes": source_size,
        "source_sha256": source_sha,
        "matches_source": backup_sha == source_sha and backup_path.stat().st_size == source_size,
        "git_ignored": git_ignored,
        "git_ignore_mode": git_ignore_mode,
        "git_check_ignore_stdout": check_ignore.stdout.strip(),
        "git_check_ignore_stderr": check_ignore.stderr.strip(),
        "overwrite_protection": "unique timestamp+uuid filename; creation fails if path exists",
    }
    metadata_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    if not meta["matches_source"]:
        raise RuntimeError("Backup content differs from source")
    if not meta["git_ignored"]:
        raise RuntimeError("Backup path is not gitignored")
    return meta


def analyze_overlap(
    raw_path: Path,
    candidate: pd.DataFrame,
) -> tuple[dict[str, object], set[tuple[str, str]]]:
    candidate_by_key = {
        (row["date"], row["mpio_cdpmp"]): normalize_row(row)
        for row in candidate.to_dict(orient="records")
    }
    candidate_signatures = {key: canonical_signature(row) for key, row in candidate_by_key.items()}
    observed_signatures: dict[tuple[str, str], set[tuple[str, ...]]] = {}
    overlap_rows = 0

    with raw_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(f"Raw schema mismatch: {reader.fieldnames}")
        for row in reader:
            key = (
                str(row.get("date", "")).strip(),
                normalize_code(row.get("mpio_cdpmp", ""), 5),
            )
            if key not in candidate_by_key:
                continue
            overlap_rows += 1
            observed_signatures.setdefault(key, set()).add(canonical_signature(row))

    conflict_keys = []
    exact_keys = set()
    for key, sigs in observed_signatures.items():
        expected = candidate_signatures[key]
        if sigs == {expected}:
            exact_keys.add(key)
            continue
        conflict_keys.append({"date": key[0], "mpio_cdpmp": key[1], "variants": len(sigs)})

    candidate_keys = set(candidate_by_key)
    missing_keys = sorted(candidate_keys - set(observed_signatures))
    if conflict_keys:
        status = "conflict"
    elif len(missing_keys) == 0:
        status = "already_integrated_identically"
    elif len(exact_keys) > 0:
        status = "partial_incorporation"
    else:
        status = "partial_or_absent"

    report = {
        "generated_utc": now_utc(),
        "candidate_rows": len(candidate),
        "candidate_unique_keys": len(candidate_keys),
        "raw_overlap_rows": overlap_rows,
        "raw_keys_with_exact_match": len(exact_keys),
        "raw_missing_keys": len(missing_keys),
        "conflict_key_count": len(conflict_keys),
        "conflict_keys_sample": conflict_keys[:20],
        "status": status,
    }
    return report, set(missing_keys)


def has_trailing_newline(path: Path) -> bool:
    if path.stat().st_size == 0:
        return True
    with path.open("rb") as stream:
        stream.seek(-1, os.SEEK_END)
        last = stream.read(1)
    return last == b"\n"


def copy_and_append(
    raw_path: Path,
    raw_header: list[str],
    rows_to_add: list[dict[str, str]],
) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="wb",
        delete=False,
        dir=raw_path.parent,
        prefix="google_earth_engine.tmp.",
        suffix=".csv",
    ) as temp_stream:
        temp_path = Path(temp_stream.name)
        with raw_path.open("rb") as source:
            shutil.copyfileobj(source, temp_stream, length=8 * 1024 * 1024)

    with temp_path.open("a", encoding="utf-8", newline="") as out_stream:
        if rows_to_add and not has_trailing_newline(raw_path):
            out_stream.write("\n")
        writer = csv.DictWriter(out_stream, fieldnames=raw_header, lineterminator="\n")
        for row in rows_to_add:
            writer.writerow({column: row.get(column, "") for column in raw_header})

    return temp_path


def prefix_matches(source: Path, candidate: Path, prefix_bytes: int) -> bool:
    left = source.open("rb")
    right = candidate.open("rb")
    with left, right:
        remaining = prefix_bytes
        chunk = 8 * 1024 * 1024
        while remaining > 0:
            block_size = min(chunk, remaining)
            left_block = left.read(block_size)
            right_block = right.read(block_size)
            if left_block != right_block:
                return False
            remaining -= len(left_block)
            if len(left_block) == 0:
                return remaining == 0
    return True


def count_rows(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        next(reader)
        return sum(1 for _ in reader)


def january_tolima_meta_coverage(path: Path, catalog_codes: list[str]) -> tuple[int, int]:
    expected = {
        (d.strftime("%Y-%m-%d"), code)
        for d in pd.date_range("2020-01-01", "2020-01-31")
        for code in catalog_codes
    }
    present = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            day = str(row.get("date", "")).strip()
            code = normalize_code(row.get("mpio_cdpmp", ""), 5)
            key = (day, code)
            if key in expected:
                present.add(key)
    return len(present), len(expected - present)


def has_successful_prior_integration(evidence_dir: Path) -> bool:
    result_path = evidence_dir / "integration_result.json"
    if not result_path.exists():
        return False
    try:
        result = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return str(result.get("status", "")) in {"applied", "already_integrated"}


def run_precheck(
    paths: Paths,
    require_full_grid: bool = True,
    allow_changed_identity_after_success: bool = False,
) -> dict[str, object]:
    paths.evidence_dir.mkdir(parents=True, exist_ok=True)
    paths.backup_dir.mkdir(parents=True, exist_ok=True)

    baseline = baseline_identity(paths)
    (paths.evidence_dir / "baseline_identity.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    prior_success = has_successful_prior_integration(paths.evidence_dir)
    if baseline["investigation_needed_before_modification"] and not (
        allow_changed_identity_after_success and prior_success
    ):
        raise RuntimeError("Raw source differs from prior audit identity")

    space = disk_space_check(paths)
    (paths.evidence_dir / "disk_space_check.json").write_text(
        json.dumps(space, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not space["enough_space"]:
        raise RuntimeError("Insufficient free space for safe update")

    catalog_codes = load_catalog_codes(
        paths.catalog_path,
        expected_count=76 if require_full_grid else None,
    )
    candidate, candidate_report = validate_candidate(
        paths.candidate_path,
        catalog_codes,
        require_full_grid=require_full_grid,
    )
    (paths.evidence_dir / "candidate_validation.json").write_text(
        json.dumps(candidate_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    backup = create_or_reuse_backup(
        paths,
        source_sha=baseline["raw_sha256"],
        source_size=baseline["raw_bytes"],
    )

    overlap, missing_keys = analyze_overlap(paths.raw_path, candidate)
    (paths.evidence_dir / "overlap_analysis.json").write_text(
        json.dumps(overlap, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "baseline": baseline,
        "space": space,
        "candidate": candidate,
        "candidate_report": candidate_report,
        "catalog_codes": catalog_codes,
        "backup": backup,
        "overlap": overlap,
        "missing_keys": missing_keys,
    }


def apply_update(
    paths: Paths,
    fail_before_replace: bool,
    require_full_grid: bool = True,
) -> dict[str, object]:
    pre = run_precheck(
        paths,
        require_full_grid=require_full_grid,
        allow_changed_identity_after_success=True,
    )
    baseline = pre["baseline"]
    overlap = pre["overlap"]
    candidate: pd.DataFrame = pre["candidate"]
    missing_keys: set[tuple[str, str]] = pre["missing_keys"]

    dengue_before = file_sha256(paths.dengue_path)
    severe_before = file_sha256(paths.severe_path)

    if overlap["status"] == "conflict":
        raise RuntimeError("Conflicting values detected on overlapping date+mpio keys")

    if overlap["status"] == "already_integrated_identically":
        present_keys, missing = january_tolima_meta_coverage(paths.raw_path, pre["catalog_codes"])
        result = {
            "generated_utc": now_utc(),
            "status": "already_integrated",
            "added_rows": 0,
            "preservation_check_passed": True,
            "atomic_replace_completed": False,
            "raw_changed_during_process": False,
            "raw_sha256_before": baseline["raw_sha256"],
            "raw_sha256_after": baseline["raw_sha256"],
            "january_rows_tolima_meta_after": present_keys,
            "january_missing_municipality_days_after": missing,
            "dengue_csv_unchanged": file_sha256(paths.dengue_path) == dengue_before,
            "dengue_grave_csv_unchanged": file_sha256(paths.severe_path) == severe_before,
        }
        (paths.evidence_dir / "integration_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result

    raw_header = ensure_required_header(paths.raw_path)
    candidate_by_key = {
        (row["date"], row["mpio_cdpmp"]): normalize_row(row)
        for row in candidate.to_dict(orient="records")
    }
    rows_to_add = [candidate_by_key[key] for key in sorted(missing_keys)]

    temp_path: Path | None = None
    source_size = paths.raw_path.stat().st_size
    source_rows = count_rows(paths.raw_path)
    try:
        temp_path = copy_and_append(paths.raw_path, raw_header, rows_to_add)
        if not prefix_matches(paths.raw_path, temp_path, source_size):
            raise RuntimeError("Existing source prefix changed in temporary output")

        temp_rows = count_rows(temp_path)
        expected_rows = source_rows + len(rows_to_add)
        if temp_rows != expected_rows:
            raise RuntimeError(
                f"Unexpected temporary row count: got {temp_rows}, expected {expected_rows}"
            )

        if fail_before_replace:
            raise RuntimeError("Failpoint before replace (simulated)")

        check_identity = raw_identity(paths.raw_path)
        raw_changed = (
            check_identity["raw_sha256"] != baseline["raw_sha256"]
            or check_identity["raw_bytes"] != baseline["raw_bytes"]
            or check_identity["raw_mtime_ns"] != baseline["raw_mtime_ns"]
        )
        if raw_changed:
            raise RuntimeError("Raw source changed during process; aborting replace")

        os.replace(temp_path, paths.raw_path)
        temp_path = None

        after = raw_identity(paths.raw_path)
        present_keys, missing = january_tolima_meta_coverage(paths.raw_path, pre["catalog_codes"])
        result = {
            "generated_utc": now_utc(),
            "status": "applied",
            "added_rows": len(rows_to_add),
            "preservation_check_passed": True,
            "atomic_replace_completed": True,
            "raw_changed_during_process": False,
            "raw_sha256_before": baseline["raw_sha256"],
            "raw_sha256_after": after["raw_sha256"],
            "raw_bytes_before": baseline["raw_bytes"],
            "raw_bytes_after": after["raw_bytes"],
            "source_rows_before": source_rows,
            "source_rows_after": count_rows(paths.raw_path),
            "expected_rows_after": expected_rows,
            "january_rows_tolima_meta_after": present_keys,
            "january_missing_municipality_days_after": missing,
            "dengue_csv_unchanged": file_sha256(paths.dengue_path) == dengue_before,
            "dengue_grave_csv_unchanged": file_sha256(paths.severe_path) == severe_before,
        }
        (paths.evidence_dir / "integration_result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return result
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def write_post_summary(paths: Paths) -> dict[str, object]:
    catalog_codes = load_catalog_codes(paths.catalog_path)
    present, missing = january_tolima_meta_coverage(paths.raw_path, catalog_codes)
    post = {
        "generated_utc": now_utc(),
        "raw_sha256_after": file_sha256(paths.raw_path),
        "january_rows_tolima_meta_after": present,
        "january_missing_municipalities_after": int(missing / 31),
        "january_missing_municipality_days_after": missing,
    }
    (paths.evidence_dir / "post_update_summary.json").write_text(
        json.dumps(post, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return post


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["precheck", "apply"], required=True)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root",
    )
    parser.add_argument(
        "--raw-path",
        type=Path,
        default=Path("data/raw/google_earth_engine.csv"),
    )
    parser.add_argument(
        "--candidate-path",
        type=Path,
        default=Path(
            "data/interim/stage2_january_climate_recovery/climate_2020_01_candidate_tolima_meta.csv"
        ),
    )
    parser.add_argument(
        "--catalog-path",
        type=Path,
        default=Path("data/sources/Divipola-municipios.md"),
    )
    parser.add_argument(
        "--prior-audit-dir",
        type=Path,
        default=Path("data/interim/stage2_january_2020_climate_audit"),
    )
    parser.add_argument(
        "--evidence-dir",
        type=Path,
        default=Path("data/interim/stage2_january_2020_incorporation"),
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("data/interim/stage2_january_2020_incorporation/backups"),
    )
    parser.add_argument("--fail-before-replace", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    paths = Paths(
        root=root,
        raw_path=(root / args.raw_path).resolve(),
        candidate_path=(root / args.candidate_path).resolve(),
        catalog_path=(root / args.catalog_path).resolve(),
        prior_audit_dir=(root / args.prior_audit_dir).resolve(),
        evidence_dir=(root / args.evidence_dir).resolve(),
        backup_dir=(root / args.backup_dir).resolve(),
        dengue_path=(root / "data/raw/dengue.csv").resolve(),
        severe_path=(root / "data/raw/dengue_grave.csv").resolve(),
    )

    if args.mode == "precheck":
        pre = run_precheck(paths, require_full_grid=True)
        print(
            json.dumps(
                {
                    "status": "precheck_ok",
                    "overlap_status": pre["overlap"]["status"],
                    "backup_relpath": pre["backup"]["backup_relpath"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    result = apply_update(
        paths,
        fail_before_replace=args.fail_before_replace,
        require_full_grid=True,
    )
    post = write_post_summary(paths)
    print(
        json.dumps(
            {
                "status": result["status"],
                "added_rows": result["added_rows"],
                "raw_sha256_after": result["raw_sha256_after"],
                "january_rows_tolima_meta_after": post["january_rows_tolima_meta_after"],
                "january_missing_municipality_days_after": post[
                    "january_missing_municipality_days_after"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
