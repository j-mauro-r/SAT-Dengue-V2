from __future__ import annotations

import argparse
import csv
import hashlib
import json
import uuid
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = ROOT / "data/interim/stage2_manifest_traceability"
PANEL_DIR = ROOT / "data/interim/stage2_panel_review"
INCORP_DIR = ROOT / "data/interim/stage2_january_2020_incorporation"
AUDIT_DIR = ROOT / "data/interim/stage2_january_2020_climate_audit"

MANIFEST_PATH = PANEL_DIR / "input_hashes.json"
MANIFEST_HISTORY_DIR = PANEL_DIR / "input_hashes_history"
MANIFEST_TRANSITION_LOG = PANEL_DIR / "input_hashes_transitions.jsonl"

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


@dataclass
class ManifestTransitionContext:
    authorized: bool
    reason: str | None
    authorized_plan: str | None
    evidence_paths: list[str]
    backup_reference: str | None


def now_utc() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": sha256(path),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _path_ref(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _manifest_digest(payload: dict[str, str]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _archive_manifest_snapshot(manifest_path: Path, history_dir: Path) -> Path:
    old_payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_digest = _manifest_digest(old_payload)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"input_hashes.{stamp}.{old_digest[:12]}.{uuid.uuid4().hex[:8]}.json"
    history_dir.mkdir(parents=True, exist_ok=True)
    archive_path = history_dir / name
    if archive_path.exists():
        raise RuntimeError(f"Refusing to overwrite manifest archive: {archive_path}")
    archive_path.write_text(
        json.dumps(
            {
                "archived_utc": now_utc(),
                "archive_kind": "historical_manifest_snapshot",
                "source_path": _path_ref(manifest_path),
                "source_manifest_sha256": old_digest,
                "manifest": old_payload,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return archive_path


def apply_manifest_transition(
    *,
    manifest_path: Path,
    new_hashes: dict[str, str],
    history_dir: Path,
    transition_log_path: Path,
    context: ManifestTransitionContext,
) -> dict[str, Any]:
    if manifest_path.exists():
        current = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        current = None

    if current == new_hashes:
        return {
            "status": "unchanged",
            "manifest_path": _path_ref(manifest_path),
            "manifest_sha256": _manifest_digest(new_hashes),
            "authorized": context.authorized,
        }

    if not context.authorized:
        raise AssertionError(
            "Protected inputs changed. Transition refused: missing explicit authorization"
        )

    if not context.reason or not context.authorized_plan:
        raise AssertionError("Transition refused: missing reason or authorized plan reference")
    if not context.evidence_paths:
        raise AssertionError("Transition refused: missing supporting evidence paths")

    archive_relpath = None
    old_digest = None
    if current is not None:
        archive = _archive_manifest_snapshot(manifest_path, history_dir)
        archive_relpath = _path_ref(archive)
        old_digest = _manifest_digest(current)

    new_digest = _manifest_digest(new_hashes)
    manifest_path.write_text(
        json.dumps(new_hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    transition_log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp_utc": now_utc(),
        "event": "authorized_manifest_transition",
        "manifest_path": _path_ref(manifest_path),
        "old_manifest_sha256": old_digest,
        "new_manifest_sha256": new_digest,
        "archived_old_manifest": archive_relpath,
        "authorized_plan": context.authorized_plan,
        "reason": context.reason,
        "evidence_paths": context.evidence_paths,
        "backup_reference": context.backup_reference,
    }
    with transition_log_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {
        "status": "transition_applied",
        "manifest_path": _path_ref(manifest_path),
        "old_manifest_sha256": old_digest,
        "new_manifest_sha256": new_digest,
        "archived_old_manifest": archive_relpath,
        "transition_log_path": _path_ref(transition_log_path),
    }


def _normalize_code(raw: str, width: int) -> str:
    return str(raw or "").strip().zfill(width)


def _canonical_row(row: dict[str, str]) -> tuple[str, ...]:
    values = []
    for col in REQUIRED_COLUMNS:
        value = str(row.get(col, "") or "").strip()
        if col == "dpto_ccdgo":
            value = _normalize_code(value, 2)
        elif col == "mpio_ccdgo":
            value = _normalize_code(value, 3)
        elif col == "mpio_cdpmp":
            value = _normalize_code(value, 5)
        values.append(value)
    return tuple(values)


def _tail_counter_from_updated(backup_path: Path, updated_path: Path) -> Counter[tuple[str, ...]]:
    backup_size = backup_path.stat().st_size
    with updated_path.open("rb") as stream:
        stream.seek(backup_size)
        tail = stream.read()

    if not tail:
        return Counter()

    if tail.startswith(b"\n"):
        tail = tail[1:]
    text = tail.decode("utf-8")
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        values = next(csv.reader([line]))
        if len(values) != len(REQUIRED_COLUMNS):
            raise AssertionError("Unexpected appended row width in updated climate file")
        rows.append(dict(zip(REQUIRED_COLUMNS, values, strict=True)))
    return Counter(_canonical_row(row) for row in rows)


def _candidate_counter(candidate_path: Path) -> Counter[tuple[str, ...]]:
    with candidate_path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != REQUIRED_COLUMNS:
            raise AssertionError("Candidate schema mismatch")
        return Counter(_canonical_row(row) for row in reader)


def _is_prefix_bytes(backup_path: Path, updated_path: Path) -> bool:
    size = backup_path.stat().st_size
    chunk = 8 * 1024 * 1024
    with backup_path.open("rb") as left, updated_path.open("rb") as right:
        remaining = size
        while remaining > 0:
            part = min(chunk, remaining)
            a = left.read(part)
            b = right.read(part)
            if a != b:
                return False
            remaining -= len(a)
            if not a:
                break
    return True


def _count_rows(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        next(reader)
        return sum(1 for _ in reader)


def search_manifest_evidence() -> dict[str, Any]:
    searched_locations = [
        "data/interim/stage2_panel_review/",
        "data/interim/stage2_january_2020_incorporation/",
        "data/interim/stage2_january_2020_climate_audit/",
        ".dwp/plans/PLAN_009_january_climate_recovery/",
        ".dwp/plans/PLAN_010_january_2020_climate_incorporation/",
        "tmp/",
    ]
    input_hashes_candidates = sorted(
        str(path.relative_to(ROOT)) for path in ROOT.rglob("*input_hashes*.json*")
    )
    plan_mentions = []
    for path in sorted(ROOT.glob(".dwp/plans/PLAN_0*/README.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "input_hashes" in text:
            plan_mentions.append(str(path.relative_to(ROOT)))
    return {
        "generated_utc": now_utc(),
        "searched_locations": searched_locations,
        "input_hashes_candidates": input_hashes_candidates,
        "plan_readme_mentions": plan_mentions,
        "historical_manifest_recovered": False,
        "notes": (
            "No authoritative copy of deleted historical input_hashes.json was found. "
            "A provenance-limited reconstruction is required."
        ),
    }


def build_reconstructed_manifest() -> dict[str, Any]:
    current_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    prior_identity = json.loads((AUDIT_DIR / "source_identity.json").read_text(encoding="utf-8"))
    baseline_identity = json.loads(
        (INCORP_DIR / "baseline_identity.json").read_text(encoding="utf-8")
    )
    backup_meta = json.loads((INCORP_DIR / "backup_metadata.json").read_text(encoding="utf-8"))

    reconstructed_entries = {}
    provenance = []

    for relpath in ["data/raw/dengue.csv", "data/raw/dengue_grave.csv"]:
        reconstructed_entries[relpath] = current_manifest.get(relpath)
        provenance.append(
            {
                "path": relpath,
                "hash": reconstructed_entries[relpath],
                "source": "current_manifest_plus_raw_readonly_invariant",
                "source_date": now_utc(),
                "limit": (
                    "No standalone historical manifest copy recovered; "
                    "value inferred under raw-read-only invariant."
                ),
            }
        )

    reconstructed_entries["data/raw/google_earth_engine.csv"] = prior_identity["sha256"]
    provenance.append(
        {
            "path": "data/raw/google_earth_engine.csv",
            "hash": prior_identity["sha256"],
            "source": "PLAN_008_audit_source_identity",
            "source_date": "2026-10-19",
            "limit": (
                "This reconstructs the pre-incorporation source hash only; "
                "not the full deleted historical manifest file."
            ),
        }
    )

    return {
        "generated_utc": now_utc(),
        "manifest_kind": "reconstructed_not_original",
        "includes_limits": True,
        "reconstructed_for": (
            "data/interim/stage2_panel_review/input_hashes.json historical traceability"
        ),
        "basis": {
            "current_manifest_path": str(MANIFEST_PATH.relative_to(ROOT)),
            "prior_source_identity_path": str(
                (AUDIT_DIR / "source_identity.json").relative_to(ROOT)
            ),
            "baseline_identity_path": str(
                (INCORP_DIR / "baseline_identity.json").relative_to(ROOT)
            ),
            "backup_metadata_path": str((INCORP_DIR / "backup_metadata.json").relative_to(ROOT)),
            "baseline_preincorp_climate_sha256": baseline_identity["raw_sha256"],
            "backup_source_sha256": backup_meta["source_sha256"],
            "backup_sha256": backup_meta["backup_sha256"],
        },
        "entries": reconstructed_entries,
        "provenance": provenance,
        "limitations": [
            "The deleted historical full-manifest file was not recovered.",
            "Only core raw-source entries were reconstructed with explicit provenance.",
            "Recomputing a hash today does not prove historical value without independent records.",
        ],
    }


def reconcile_historical_identities() -> dict[str, Any]:
    prior_identity = json.loads((AUDIT_DIR / "source_identity.json").read_text(encoding="utf-8"))
    baseline = json.loads((INCORP_DIR / "baseline_identity.json").read_text(encoding="utf-8"))
    backup_meta = json.loads((INCORP_DIR / "backup_metadata.json").read_text(encoding="utf-8"))
    first_apply = json.loads(
        (INCORP_DIR / "integration_result_first_apply.json").read_text(encoding="utf-8")
    )
    second_apply = json.loads(
        (INCORP_DIR / "integration_result_second_run.json").read_text(encoding="utf-8")
    )

    checks = {
        "prior_equals_baseline": prior_identity["sha256"] == baseline["raw_sha256"],
        "baseline_equals_backup_source": baseline["raw_sha256"] == backup_meta["source_sha256"],
        "backup_equals_backup_source": backup_meta["backup_sha256"] == backup_meta["source_sha256"],
        "first_apply_changed_hash": first_apply["raw_sha256_before"]
        != first_apply["raw_sha256_after"],
        "second_apply_idempotent": second_apply["raw_sha256_before"]
        == second_apply["raw_sha256_after"],
    }
    return {
        "generated_utc": now_utc(),
        "checks": checks,
        "all_passed": all(checks.values()),
        "records": {
            "prior_source_identity": str((AUDIT_DIR / "source_identity.json").relative_to(ROOT)),
            "baseline_identity": str((INCORP_DIR / "baseline_identity.json").relative_to(ROOT)),
            "backup_metadata": str((INCORP_DIR / "backup_metadata.json").relative_to(ROOT)),
            "integration_first_apply": str(
                (INCORP_DIR / "integration_result_first_apply.json").relative_to(ROOT)
            ),
            "integration_second_run": str(
                (INCORP_DIR / "integration_result_second_run.json").relative_to(ROOT)
            ),
        },
        "limit": (
            "Historical reconciliation proves linked identities across "
            "independent records, not full deleted-manifest recovery."
        ),
    }


def resolve_preintegration_backup() -> dict[str, Any]:
    prior_identity = json.loads((AUDIT_DIR / "source_identity.json").read_text(encoding="utf-8"))
    target_sha = prior_identity["sha256"]
    candidates = []
    selected_relpath = None

    for backup in sorted((INCORP_DIR / "backups").glob("google_earth_engine*.csv")):
        current_sha = sha256(backup)
        relpath = str(backup.relative_to(ROOT))
        matches_prior = current_sha == target_sha
        candidates.append(
            {"path": relpath, "sha256": current_sha, "matches_prior_source": matches_prior}
        )
        if matches_prior and selected_relpath is None:
            selected_relpath = relpath

    if selected_relpath is None:
        raise AssertionError("No backup file matches prior pre-integration climate source identity")

    return {
        "prior_source_sha256": target_sha,
        "selected_backup_relpath": selected_relpath,
        "candidates": candidates,
    }


def verify_authorized_append_only_change() -> dict[str, Any]:
    backup_meta = json.loads((INCORP_DIR / "backup_metadata.json").read_text(encoding="utf-8"))
    selected = resolve_preintegration_backup()
    candidate_validation = json.loads(
        (INCORP_DIR / "candidate_validation.json").read_text(encoding="utf-8")
    )
    backup_path = ROOT / selected["selected_backup_relpath"]
    updated_path = ROOT / "data/raw/google_earth_engine.csv"
    candidate_path = (
        ROOT
        / "data/interim/stage2_january_climate_recovery/climate_2020_01_candidate_tolima_meta.csv"
    )

    prefix_ok = _is_prefix_bytes(backup_path, updated_path)
    appended_counter = _tail_counter_from_updated(backup_path, updated_path)
    candidate_counter = _candidate_counter(candidate_path)

    backup_rows = _count_rows(backup_path)
    updated_rows = _count_rows(updated_path)
    added_rows = updated_rows - backup_rows

    delta_matches_candidate = appended_counter == candidate_counter
    unauthorized_modification_detected = not (prefix_ok and delta_matches_candidate)

    return {
        "generated_utc": now_utc(),
        "backup_path": str(backup_path.relative_to(ROOT)),
        "updated_path": str(updated_path.relative_to(ROOT)),
        "candidate_path": str(candidate_path.relative_to(ROOT)),
        "latest_backup_metadata_reference": backup_meta["backup_relpath"],
        "selected_preintegration_backup": selected,
        "backup_sha256": sha256(backup_path),
        "updated_sha256": sha256(updated_path),
        "candidate_sha256": sha256(candidate_path),
        "backup_rows": backup_rows,
        "updated_rows": updated_rows,
        "authorized_added_rows": added_rows,
        "candidate_rows": candidate_validation["candidate_rows"],
        "backup_is_exact_prefix_of_updated": prefix_ok,
        "appended_segment_matches_authorized_candidate": delta_matches_candidate,
        "unauthorized_modification_detected": unauthorized_modification_detected,
        "duplicate_preservation_claim": (
            "All pre-existing bytes are preserved when backup is an exact "
            "byte prefix of updated file. "
            "This includes any pre-existing duplicate rows and values."
        ),
        "expected_authorized_added_rows": 2356,
    }


def write_before_after_comparison(conservation: dict[str, Any]) -> dict[str, Any]:
    baseline = json.loads((INCORP_DIR / "baseline_identity.json").read_text(encoding="utf-8"))
    backup_meta = json.loads((INCORP_DIR / "backup_metadata.json").read_text(encoding="utf-8"))
    first_apply = json.loads(
        (INCORP_DIR / "integration_result_first_apply.json").read_text(encoding="utf-8")
    )
    return {
        "generated_utc": now_utc(),
        "change_reason": "Authorized January 2020 climate incorporation",
        "authorizing_plan": "PLAN_010_january_2020_climate_incorporation",
        "backup_reference": backup_meta["backup_relpath"],
        "before": {
            "path": baseline["raw_relpath"],
            "bytes": baseline["raw_bytes"],
            "sha256": baseline["raw_sha256"],
        },
        "after": {
            "path": baseline["raw_relpath"],
            "bytes": first_apply["raw_bytes_after"],
            "sha256": first_apply["raw_sha256_after"],
        },
        "delta": {
            "added_rows": conservation["authorized_added_rows"],
            "prefix_preserved": conservation["backup_is_exact_prefix_of_updated"],
            "delta_matches_candidate": conservation[
                "appended_segment_matches_authorized_candidate"
            ],
        },
    }


def current_source_hashes() -> dict[str, Any]:
    backup_meta = json.loads((INCORP_DIR / "backup_metadata.json").read_text(encoding="utf-8"))
    selected = resolve_preintegration_backup()
    backup_path = ROOT / selected["selected_backup_relpath"]
    source_paths = [
        ROOT / "data/raw/dengue.csv",
        ROOT / "data/raw/dengue_grave.csv",
        ROOT / "data/raw/google_earth_engine.csv",
        backup_path,
    ]
    return {
        "generated_utc": now_utc(),
        "files": [identity(path) for path in source_paths],
        "selected_preintegration_backup": selected,
        "latest_backup_metadata_reference": backup_meta["backup_relpath"],
    }


def run_traceability() -> None:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    search = search_manifest_evidence()
    reconstructed = build_reconstructed_manifest()
    reconciled = reconcile_historical_identities()
    conservation = verify_authorized_append_only_change()
    comparison = write_before_after_comparison(conservation)
    current = current_source_hashes()

    write_json(TRACE_DIR / "manifest_search_inventory.json", search)
    write_json(TRACE_DIR / "reconstructed_manifest_pre_jan2020.json", reconstructed)
    write_json(TRACE_DIR / "historical_identity_reconciliation.json", reconciled)
    write_json(TRACE_DIR / "conservation_verification.json", conservation)
    write_json(TRACE_DIR / "before_after_comparison.json", comparison)
    write_json(TRACE_DIR / "current_source_hashes.json", current)

    print(
        json.dumps(
            {
                "status": "ok",
                "historical_manifest_recovered": search["historical_manifest_recovered"],
                "authorized_added_rows": conservation["authorized_added_rows"],
                "prefix_preserved": conservation["backup_is_exact_prefix_of_updated"],
                "delta_matches_candidate": conservation[
                    "appended_segment_matches_authorized_candidate"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["run", "transition"], required=True)
    parser.add_argument("--authorized", action="store_true")
    parser.add_argument("--reason")
    parser.add_argument("--authorized-plan")
    parser.add_argument("--evidence-path", action="append", default=[])
    parser.add_argument("--backup-reference")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "run":
        run_traceability()
        return

    new_hashes = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in sorted((ROOT / "data/raw").glob("*.csv"))
    }
    result = apply_manifest_transition(
        manifest_path=MANIFEST_PATH,
        new_hashes=new_hashes,
        history_dir=MANIFEST_HISTORY_DIR,
        transition_log_path=MANIFEST_TRANSITION_LOG,
        context=ManifestTransitionContext(
            authorized=args.authorized,
            reason=args.reason,
            authorized_plan=args.authorized_plan,
            evidence_paths=args.evidence_path,
            backup_reference=args.backup_reference,
        ),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
