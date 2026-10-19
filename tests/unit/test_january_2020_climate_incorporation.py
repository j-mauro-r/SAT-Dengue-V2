from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "jan_incorp", ROOT / "scripts/january_2020_climate_incorporation.py"
)
assert spec and spec.loader
jan_incorp = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = jan_incorp
spec.loader.exec_module(jan_incorp)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8192), b""):
            digest.update(block)
    return digest.hexdigest()


def _row(date: str, code: str, base: float) -> dict[str, str]:
    day = pd.Timestamp(date).dayofyear
    return {
        "date": date,
        "year": date[:4],
        "month": date[5:7],
        "day_of_year": str(day),
        "dpto_ccdgo": code[:2],
        "dpto_cnmbr": f"DEP-{code[:2]}",
        "mpio_ccdgo": code[2:],
        "mpio_cdpmp": code,
        "mpio_cnmbr": f"MUN-{code}",
        "rain_mm_day": f"{base:.1f}",
        "temp_mean_c": f"{base + 1:.1f}",
        "dewpoint_mean_c": f"{base + 2:.1f}",
        "soil_water_l1_mean": f"{base + 3:.1f}",
        "surface_runoff_mm_day": f"{base + 4:.1f}",
        "total_evaporation_mm_day_ecmwf": f"{base + 5:.1f}",
        "wind_u_mean_ms": f"{base + 6:.1f}",
        "wind_v_mean_ms": f"{base + 7:.1f}",
        "solar_radiation_mj_m2_day": f"{base + 8:.1f}",
    }


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=jan_incorp.REQUIRED_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _build_paths(
    tmp_path: Path,
    raw_rows: list[dict[str, str]],
    candidate_rows: list[dict[str, str]],
    catalog_codes: list[str],
) -> Any:
    raw_path = tmp_path / "data/raw/google_earth_engine.csv"
    candidate_path = (
        tmp_path
        / "data/interim/stage2_january_climate_recovery/climate_2020_01_candidate_tolima_meta.csv"
    )
    prior_dir = tmp_path / "data/interim/stage2_january_2020_climate_audit"
    evidence_dir = tmp_path / "data/interim/stage2_january_2020_incorporation"
    sources_path = tmp_path / "data/sources/Divipola-municipios.md"
    dengue_path = tmp_path / "data/raw/dengue.csv"
    severe_path = tmp_path / "data/raw/dengue_grave.csv"

    _write_csv(raw_path, raw_rows)
    _write_csv(candidate_path, candidate_rows)
    dengue_path.write_text("id,value\n1,1\n", encoding="utf-8")
    severe_path.write_text("id,value\n1,1\n", encoding="utf-8")

    sources_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_payload = {
        "resultado": [
            {
                "CODIGO_DPTO_MPIO": code,
                "CODIGO_DEPARTAMENTO": code[:2],
            }
            for code in catalog_codes
        ]
    }
    sources_path.write_text(json.dumps(catalog_payload, ensure_ascii=False), encoding="utf-8")

    prior_dir.mkdir(parents=True, exist_ok=True)
    raw_stat = raw_path.stat()
    prior_identity = {
        "path": str(raw_path),
        "bytes": raw_stat.st_size,
        "mtime_ns": raw_stat.st_mtime_ns,
        "sha256": _sha256(raw_path),
    }
    (prior_dir / "source_identity.json").write_text(
        json.dumps(prior_identity, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (prior_dir / "january_raw_audit.json").write_text(
        json.dumps(
            {
                "january": {
                    "global": {"rows": 0},
                    "tolima_meta": {"rows": 0},
                }
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return jan_incorp.Paths(
        root=tmp_path,
        raw_path=raw_path,
        candidate_path=candidate_path,
        catalog_path=sources_path,
        prior_audit_dir=prior_dir,
        evidence_dir=evidence_dir,
        backup_dir=evidence_dir / "backups",
        dengue_path=dengue_path,
        severe_path=severe_path,
    )


def test_backup_identity_and_no_overwrite(tmp_path: Path) -> None:
    raw_rows = [_row("2019-12-30", "50001", 1.0)]
    candidate_rows = [_row("2020-01-01", "50001", 10.0)]
    paths = _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001"])

    pre = jan_incorp.run_precheck(paths, require_full_grid=False)
    backup_meta = pre["backup"]
    backup_path = tmp_path / backup_meta["backup_relpath"]

    assert backup_path.exists()
    assert _sha256(backup_path) == _sha256(paths.raw_path)
    assert backup_meta["matches_source"]

    reused = jan_incorp.create_or_reuse_backup(
        paths,
        source_sha=pre["baseline"]["raw_sha256"],
        source_size=pre["baseline"]["raw_bytes"],
    )
    assert reused["reused_existing"]
    assert reused["backup_relpath"] == backup_meta["backup_relpath"]


def test_preserve_existing_rows_with_duplicates_and_append_only_missing_keys(
    tmp_path: Path,
) -> None:
    duplicate = _row("2019-12-31", "50001", 2.0)
    raw_rows = [duplicate, duplicate, _row("2019-12-30", "50002", 3.0)]
    candidate_rows = [_row("2020-01-01", "50001", 10.0), _row("2020-01-01", "50002", 11.0)]
    paths = _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001", "50002"])

    before = _read_csv(paths.raw_path)
    result = jan_incorp.apply_update(paths, fail_before_replace=False, require_full_grid=False)
    after = _read_csv(paths.raw_path)

    assert result["status"] == "applied"
    assert result["added_rows"] == 2
    assert after[: len(before)] == before
    assert (
        sum(1 for row in after if row["date"] == "2019-12-31" and row["mpio_cdpmp"] == "50001") == 2
    )
    assert sum(1 for row in after if row["date"] == "2020-01-01") == 2


def test_reject_invalid_schema(tmp_path: Path) -> None:
    raw_rows = [_row("2019-12-30", "50001", 1.0)]
    candidate_rows = [_row("2020-01-01", "50001", 2.0)]
    _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001"])

    broken_path = tmp_path / "broken_candidate.csv"
    broken_columns = jan_incorp.REQUIRED_COLUMNS[:-1]
    with broken_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=broken_columns)
        writer.writeheader()
        writer.writerow({key: candidate_rows[0][key] for key in broken_columns})

    with pytest.raises(ValueError):
        jan_incorp.validate_candidate(broken_path, ["50001"], require_full_grid=False)


def test_reject_invalid_values(tmp_path: Path) -> None:
    raw_rows = [_row("2019-12-30", "50001", 1.0)]
    invalid = _row("2020-01-01", "50001", 2.0)
    invalid["temp_mean_c"] = "inf"
    paths = _build_paths(tmp_path, raw_rows, [invalid], catalog_codes=["50001"])

    with pytest.raises(ValueError):
        jan_incorp.validate_candidate(paths.candidate_path, ["50001"], require_full_grid=False)


def test_reject_conflicting_key_values(tmp_path: Path) -> None:
    raw_rows = [_row("2020-01-01", "50001", 1.0)]
    candidate_rows = [_row("2020-01-01", "50001", 9.0)]
    paths = _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001"])

    before_hash = _sha256(paths.raw_path)
    with pytest.raises(RuntimeError):
        jan_incorp.apply_update(paths, fail_before_replace=False, require_full_grid=False)
    assert _sha256(paths.raw_path) == before_hash


def test_second_run_is_idempotent(tmp_path: Path) -> None:
    raw_rows = [_row("2019-12-30", "50001", 1.0)]
    candidate_rows = [_row("2020-01-01", "50001", 10.0)]
    paths = _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001"])

    first = jan_incorp.apply_update(paths, fail_before_replace=False, require_full_grid=False)
    rows_after_first = len(_read_csv(paths.raw_path))
    second = jan_incorp.apply_update(paths, fail_before_replace=False, require_full_grid=False)
    rows_after_second = len(_read_csv(paths.raw_path))

    assert first["status"] == "applied"
    assert first["added_rows"] == 1
    assert second["status"] == "already_integrated"
    assert second["added_rows"] == 0
    assert rows_after_second == rows_after_first


def test_failpoint_before_replace_keeps_original_intact(tmp_path: Path) -> None:
    raw_rows = [_row("2019-12-30", "50001", 1.0)]
    candidate_rows = [_row("2020-01-01", "50001", 10.0)]
    paths = _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001"])

    before_hash = _sha256(paths.raw_path)
    with pytest.raises(RuntimeError, match="Failpoint before replace"):
        jan_incorp.apply_update(paths, fail_before_replace=True, require_full_grid=False)
    assert _sha256(paths.raw_path) == before_hash
    assert not list(paths.raw_path.parent.glob("google_earth_engine.tmp.*.csv"))


def test_apply_keeps_epidemiological_raw_files_unchanged(tmp_path: Path) -> None:
    raw_rows = [_row("2019-12-30", "50001", 1.0)]
    candidate_rows = [_row("2020-01-01", "50001", 10.0)]
    paths = _build_paths(tmp_path, raw_rows, candidate_rows, catalog_codes=["50001"])

    dengue_before = _sha256(paths.dengue_path)
    severe_before = _sha256(paths.severe_path)
    result = jan_incorp.apply_update(paths, fail_before_replace=False, require_full_grid=False)

    assert result["dengue_csv_unchanged"]
    assert result["dengue_grave_csv_unchanged"]
    assert _sha256(paths.dengue_path) == dengue_before
    assert _sha256(paths.severe_path) == severe_before
