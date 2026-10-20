from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts import stage2_manifest_traceability as trace


def _manifest(path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _rows(value_base: float) -> list[dict[str, str]]:
    return [
        {
            "date": "2020-01-01",
            "year": "2020",
            "month": "01",
            "day_of_year": "1",
            "dpto_ccdgo": "50",
            "dpto_cnmbr": "Meta",
            "mpio_ccdgo": "001",
            "mpio_cdpmp": "50001",
            "mpio_cnmbr": "Villavicencio",
            "rain_mm_day": f"{value_base:.1f}",
            "temp_mean_c": f"{value_base + 1:.1f}",
            "dewpoint_mean_c": f"{value_base + 2:.1f}",
            "soil_water_l1_mean": f"{value_base + 3:.1f}",
            "surface_runoff_mm_day": f"{value_base + 4:.1f}",
            "total_evaporation_mm_day_ecmwf": f"{value_base + 5:.1f}",
            "wind_u_mean_ms": f"{value_base + 6:.1f}",
            "wind_v_mean_ms": f"{value_base + 7:.1f}",
            "solar_radiation_mj_m2_day": f"{value_base + 8:.1f}",
        }
    ]


def _write_csv(path: Path, rows: list[dict[str, str]], include_header: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=trace.REQUIRED_COLUMNS, lineterminator="\n")
        if include_header:
            writer.writeheader()
        writer.writerows(rows)


def test_manifest_preservation_on_authorized_transition(tmp_path: Path) -> None:
    manifest = tmp_path / "input_hashes.json"
    history = tmp_path / "history"
    transitions = tmp_path / "transitions.jsonl"

    _manifest(manifest, {"data/raw/dengue.csv": "old"})
    result = trace.apply_manifest_transition(
        manifest_path=manifest,
        new_hashes={"data/raw/dengue.csv": "new"},
        history_dir=history,
        transition_log_path=transitions,
        context=trace.ManifestTransitionContext(
            authorized=True,
            reason="Authorized transition",
            authorized_plan="PLAN_011",
            evidence_paths=["data/interim/stage2_manifest_traceability/report.json"],
            backup_reference="data/interim/backups/google_earth_engine.pre.csv",
        ),
    )

    assert result["status"] == "transition_applied"
    assert len(list(history.glob("*.json"))) == 1
    saved = json.loads(manifest.read_text(encoding="utf-8"))
    assert saved["data/raw/dengue.csv"] == "new"


def test_unauthorized_change_detection_including_epi_files(tmp_path: Path) -> None:
    manifest = tmp_path / "input_hashes.json"
    _manifest(manifest, {"data/raw/dengue.csv": "old"})

    with pytest.raises(AssertionError):
        trace.apply_manifest_transition(
            manifest_path=manifest,
            new_hashes={"data/raw/dengue.csv": "tampered"},
            history_dir=tmp_path / "history",
            transition_log_path=tmp_path / "transitions.jsonl",
            context=trace.ManifestTransitionContext(
                authorized=False,
                reason=None,
                authorized_plan=None,
                evidence_paths=[],
                backup_reference=None,
            ),
        )


def test_backup_updated_candidate_exact_correspondence(tmp_path: Path) -> None:
    backup = tmp_path / "backup.csv"
    candidate = tmp_path / "candidate.csv"
    updated = tmp_path / "updated.csv"

    backup_rows = _rows(1.0) + _rows(1.0)
    candidate_rows = _rows(10.0)

    _write_csv(backup, backup_rows)
    _write_csv(candidate, candidate_rows)

    updated.write_bytes(backup.read_bytes())
    with updated.open("a", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=trace.REQUIRED_COLUMNS, lineterminator="\n")
        writer.writerows(candidate_rows)

    assert trace._is_prefix_bytes(backup, updated)
    assert trace._tail_counter_from_updated(backup, updated) == trace._candidate_counter(candidate)


def test_evidence_overwrite_protection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = tmp_path / "input_hashes.json"
    history = tmp_path / "history"
    _manifest(manifest, {"data/raw/dengue.csv": "old"})

    class _FixedUuid:
        hex = "12345678abcdef001122334455667788"

    class _FixedDateTime:
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 10, 18, 12, 0, 0, tzinfo=trace.UTC)

    monkeypatch.setattr(trace.uuid, "uuid4", lambda: _FixedUuid())
    monkeypatch.setattr(trace, "datetime", _FixedDateTime)

    first = trace._archive_manifest_snapshot(manifest, history)
    assert first.exists()
    with pytest.raises(RuntimeError):
        trace._archive_manifest_snapshot(manifest, history)


def test_transition_without_evidence_is_rejected(tmp_path: Path) -> None:
    manifest = tmp_path / "input_hashes.json"
    _manifest(manifest, {"data/raw/dengue.csv": "old"})

    with pytest.raises(AssertionError):
        trace.apply_manifest_transition(
            manifest_path=manifest,
            new_hashes={"data/raw/dengue.csv": "new"},
            history_dir=tmp_path / "history",
            transition_log_path=tmp_path / "transitions.jsonl",
            context=trace.ManifestTransitionContext(
                authorized=True,
                reason="Missing evidence path",
                authorized_plan="PLAN_011",
                evidence_paths=[],
                backup_reference=None,
            ),
        )
